import pathlib
from dataclasses import field
from typing import Optional, Iterable, List, Tuple, Any, Callable, Dict

import numpy as np
import pandas as pd
import polars as pl
import duckdb
import dagster as dg

from pydantic import BaseModel

from dxtrx.utils.jinja import Jinja2TemplateEngine
from dxtrx.utils.sql import format_sql_multistatement
from dxtrx.dagster.resources.sql import SQLBaseResource
from dxtrx.utils.types import DataFrameType, OutputType, DEFAULT_OUTPUT_TYPE
from dxtrx.utils.dataframe_conversion import convert_output, ensure_pandas


DEFAULT_DUCKDB_EXTENSIONS: List[str] = ["iceberg", "httpfs", "postgres"]  # we will LOAD 'iceberg' only if catalogs are provided


class DuckDBResource(SQLBaseResource):
    """
    DuckDB-only Dagster resource with:
      - Pinned connection
      - Jinja templating + multi-statement execution
      - Auto-reconnect retry
      - DataFrame uploads (fast: register + CTAS/INSERT)
      - Optional Iceberg REST catalog attach via `iceberg_catalogs` (no other S3/minio config here)

    ---- Iceberg REST catalogs ----
    Pass `iceberg_catalogs` as a list of dicts. Minimal fields:

      iceberg_catalogs=[
        {
          "name": "iceberg_catalog",            # required: catalog alias inside DuckDB
          "endpoint": "https://rest.example",   # required: REST endpoint
          # optional:
          "attach_path": "warehouse",           # first literal in ATTACH; defaults to 'warehouse'
          "secret": {                           # creates a DuckDB SECRET and uses it in ATTACH
             "token": "bearer_token_here"       # (simplest: direct bearer token)
             # Alternatively (advanced): provide CLIENT_ID/CLIENT_SECRET via 'attach_options'
          },
          "attach_options": {                   # extra key->value ATTACH options
            # e.g., "ENDPOINT_TYPE": "S3_TABLES"
            # e.g., "CLIENT_ID": "...", "CLIENT_SECRET": "..."
          }
        }
      ]

    Notes:
      * We LOAD the `iceberg` extension automatically if `iceberg_catalogs` is non-empty.
      * DuckDB parameter interpolation is not supported for ATTACH; we build statements safely
        with basic SQL literal escaping for strings.
    """

    # Config
    file_path: Optional[str] = None        # path to .duckdb, or ":memory:"
    base_dir: Optional[str] = None         # optional: resolve file_path relative to this base

    duckdb_extensions: List[str] = field(default_factory=lambda: DEFAULT_DUCKDB_EXTENSIONS)
    duckdb_install_extensions: bool = False  # kept for parity (not used here)
    extra_startup_sql: Optional[List[str]] = field(default_factory=list)

    # Attach Iceberg REST catalogs on connect
    iceberg_catalogs: Optional[List[Dict[str, Any]]] = field(default_factory=list)

    # Behavior
    strict_fail_on_disconnect: bool = False

    # Internals
    _conn: Optional[duckdb.DuckDBPyConnection] = None
    _logger: Any = None
    _template_engine: Jinja2TemplateEngine = None
    _resolved_file_path: Optional[str] = None

    def _validate_params(self):
        """
        Validates configuration parameters for the DuckDB resource.

        Parity with the SQLAlchemy resource's validation approach:
        - Ensure types are correct
        - Validate complex structures like iceberg_catalogs
        - Allow in-memory default when file_path is not provided
        """
        # file_path and base_dir can be None or str
        if self.file_path is not None and not isinstance(self.file_path, str):
            raise ValueError("'file_path' must be a string or None")
        if self.base_dir is not None and not isinstance(self.base_dir, str):
            raise ValueError("'base_dir' must be a string or None")

        # duckdb_extensions must be a list[str] (if provided)
        if self.duckdb_extensions is not None:
            if not isinstance(self.duckdb_extensions, list) or not all(isinstance(ext, str) for ext in self.duckdb_extensions):
                raise ValueError("'duckdb_extensions' must be a list of strings")

        # extra_startup_sql must be a list[str] (if provided)
        if self.extra_startup_sql is not None:
            if not isinstance(self.extra_startup_sql, list) or not all(isinstance(stmt, str) for stmt in self.extra_startup_sql):
                raise ValueError("'extra_startup_sql' must be a list of strings")

        # iceberg_catalogs: list[dict] with required keys 'name' and 'endpoint'
        if self.iceberg_catalogs is not None:
            if not isinstance(self.iceberg_catalogs, list):
                raise ValueError("'iceberg_catalogs' must be a list of dicts")
            for idx, cat in enumerate(self.iceberg_catalogs):
                if not isinstance(cat, dict):
                    raise ValueError(f"iceberg_catalogs[{idx}] must be a dict")
                name = cat.get("name")
                endpoint = cat.get("endpoint")
                if not name or not endpoint:
                    raise ValueError("Each iceberg catalog requires 'name' and 'endpoint'.")
                # Optional nested fields' type checks
                if "attach_options" in cat and not isinstance(cat["attach_options"], dict):
                    raise ValueError(f"iceberg_catalogs[{idx}].attach_options must be a dict")
                if "secret" in cat and not isinstance(cat["secret"], dict):
                    raise ValueError(f"iceberg_catalogs[{idx}].secret must be a dict")

        # Flags
        if not isinstance(self.strict_fail_on_disconnect, bool):
            raise ValueError("'strict_fail_on_disconnect' must be a boolean")

    # ------------- Lifecycle -------------

    def setup_for_execution(self, context: dg.InitResourceContext):
        self._logger = dg.get_dagster_logger("duckdb")
        self._template_engine = Jinja2TemplateEngine()

        # Validate provided configuration prior to applying defaults
        self._validate_params()

        # Compute resolved (non-mutating) file path
        candidate_path = self.file_path or ":memory:"
        if candidate_path != ":memory:":
            candidate_path = self._resolve_path(candidate_path, self.base_dir)
        self._resolved_file_path = candidate_path

        self._create_pinned_connection()

    def _resolve_path(self, path: str, base_dir: Optional[str]) -> str:
        p = pathlib.Path(path)
        if not p.is_absolute():
            base = pathlib.Path(base_dir) if base_dir else pathlib.Path.cwd()
            p = (base / p).resolve()
        return str(p)

    def renew_connection(self):
        """Manually recreate the pinned connection."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception as e:
                if self._logger:
                    self._logger.debug(f"Error closing existing DuckDB conn: {e}")
        self._create_pinned_connection()

    def _create_pinned_connection(self):
        # Use resolved path to avoid mutating pydantic fields on Pythonic resources
        file_path = self._resolved_file_path or self.file_path or ":memory:"
        self._conn = duckdb.connect(file_path)

        # Optional startup SQL (PRAGMAs, etc.)
        for stmt in self.extra_startup_sql or []:
            self._conn.execute(stmt)

        # Attach Iceberg catalogs if provided
        if self.iceberg_catalogs:
            # LOAD iceberg extension
            try:
                self._conn.execute("LOAD iceberg")
            except Exception as e:
                self._logger.error(f"Failed to LOAD iceberg extension: {e}")
                raise

            self._attach_iceberg_catalogs()

    # ------------- Helpers -------------

    def _with_auto_reconnect(self, op: Callable, *args, **kwargs):
        try:
            return op(*args, **kwargs)
        except duckdb.Error as e:
            if self.strict_fail_on_disconnect:
                raise
            # Best-effort reconnect then retry once
            if self._logger:
                self._logger.warning(f"DuckDB error encountered, attempting reconnect: {e}")
            self.renew_connection()
            return op(*args, **kwargs)

    @staticmethod
    def _sql_quote(value: str) -> str:
        """Basic SQL single-quote escaping for literals."""
        return "'" + value.replace("'", "''") + "'"

    @staticmethod
    def _ident_quote(ident: str) -> str:
        """Basic identifier quoting with double-quotes."""
        return '"' + ident.replace('"', '""') + '"'

    def _attach_iceberg_catalogs(self):
        """
        Create optional DuckDB SECRET (token) and ATTACH the REST catalog(s).
        See: https://duckdb.org/docs/stable/core_extensions/iceberg/iceberg_rest_catalogs.html
        """
        for cat in self.iceberg_catalogs or []:
            name = cat.get("name")
            endpoint = cat.get("endpoint")
            if not name or not endpoint:
                raise ValueError("Each iceberg catalog requires 'name' and 'endpoint'.")

            attach_path = cat.get("attach_path", "warehouse")
            attach_options = dict(cat.get("attach_options") or {})

            # Optional SECRET (token)
            secret_name = None
            secret_cfg = cat.get("secret") or {}
            token = secret_cfg.get("token")
            if token:
                secret_name = f"iceberg_secret_{name}"
                stmt = (
                    f"CREATE SECRET {self._ident_quote(secret_name)} ("
                    f"  TYPE ICEBERG, TOKEN {self._sql_quote(token)}"
                    f")"
                )
                # Best-effort idempotency: DROP if exists (DuckDB SECRET drop requires try/catch)
                try:
                    self._conn.execute(f"DROP SECRET {self._ident_quote(secret_name)}")
                except Exception:
                    pass
                self._conn.execute(stmt)

            # Build ATTACH ... AS <name> (TYPE iceberg, ENDPOINT ..., SECRET ...)
            opts_kv = {
                "TYPE": "iceberg",
                "ENDPOINT": endpoint,
            }
            if secret_name:
                opts_kv["SECRET"] = secret_name

            # Merge user-provided attach options (e.g., CLIENT_ID/CLIENT_SECRET, ENDPOINT_TYPE, etc.)
            for k, v in (attach_options.items()):
                opts_kv[k] = v

            # Convert to "KEY VALUE" pairs, quoting string values
            def _fmt_val(v: Any) -> str:
                if isinstance(v, str):
                    return self._sql_quote(v)
                elif isinstance(v, bool):
                    return "TRUE" if v else "FALSE"
                elif v is None:
                    return "NULL"
                else:
                    return str(v)

            opt_sql = ", ".join(f"{k} {_fmt_val(v)}" for k, v in opts_kv.items())

            attach_sql = (
                f"ATTACH {self._sql_quote(str(attach_path))} "
                f"AS {self._ident_quote(name)} "
                f"({opt_sql})"
            )

            # ATTACH cannot use parameter interpolation; execute the statement directly.
            self._conn.execute(attach_sql)

    def _resolve_full_context(self, run_context: dict) -> dict:
        return run_context

    def _resolve_query_or_query_file(
        self,
        query: Optional[str],
        query_file: Optional[str],
        context: dict,
        fail_if_multiquery: bool = False,
    ) -> List[str]:
        if query:
            template_string = query
        elif query_file:
            with open(query_file, "rt") as f:
                template_string = f.read()
        else:
            raise ValueError("Must provide either 'query' or 'query_file'")

        rendered = self._template_engine.render_string(
            template_string, self._resolve_full_context(context)
        )
        queries = format_sql_multistatement(rendered, read_dialect="duckdb", write_dialect="duckdb")

        if len(queries) == 0:
            raise ValueError("No actual queries found in the provided template string")
        if fail_if_multiquery and len(queries) > 1:
            raise ValueError("This operation is not supported for multistatement queries")
        return queries

    # ------------- Public API -------------

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Return the pinned DuckDB connection."""
        return self._conn

    def run_query(
        self,
        query: Optional[str] = None,
        query_file: Optional[str] = None,
        params: Optional[dict] = None,
        atomic: bool = False,
    ) -> bool:
        def _op():
            queries = self._resolve_query_or_query_file(query, query_file, params or {}, False)

            if atomic:
                self._conn.execute("BEGIN")

            try:
                for q in queries:
                    if params:
                        # For ordinary statements (NOT ATTACH), DuckDB supports parameters.
                        self._conn.execute(q, params)
                    else:
                        self._conn.execute(q)
                if atomic:
                    self._conn.execute("COMMIT")
            except Exception:
                if atomic:
                    self._conn.execute("ROLLBACK")
                raise

            return True

        return self._with_auto_reconnect(_op)

    def get_query_results(
        self,
        query: Optional[str] = None,
        query_file: Optional[str] = None,
        params: Optional[dict] = None,
    ) -> List[Tuple]:
        def _op():
            qs = self._resolve_query_or_query_file(query, query_file, params or {}, True)
            cur = self._conn.execute(qs[0], params or {})
            return cur.fetchall()

        return self._with_auto_reconnect(_op)

    def get_query_results_as_df(
        self,
        query: Optional[str] = None,
        query_file: Optional[str] = None,
        params: Optional[dict] = None,
        output_type: OutputType = DEFAULT_OUTPUT_TYPE,
    ) -> DataFrameType:
        def _op():
            qs = self._resolve_query_or_query_file(query, query_file, params or {}, True)
            cur = self._conn.execute(qs[0], params or {})
            try:
                # Prefer Arrow path if available
                at = cur.fetch_arrow_table()
                df = at.to_pandas()
            except Exception:
                df = cur.fetch_df()
            return df

        pandas_df = self._with_auto_reconnect(_op)
        return convert_output(pandas_df, output_type)

    def check_if_table_exists(self, table_name: str, schema: str = "main") -> bool:
        def _op():
            # Check both tables and views for parity
            q = """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = ? AND table_name = ?
            UNION ALL
            SELECT 1
            FROM information_schema.views
            WHERE table_schema = ? AND table_name = ?
            LIMIT 1
            """
            res = self._conn.execute(q, [schema, table_name, schema, table_name]).fetchall()
            return len(res) > 0

        return self._with_auto_reconnect(_op)

    def upload_df_to_table(
        self,
        df: DataFrameType,
        table_name: str,
        if_exists: str = "replace",
        schema: str = "main",
        json_columns: Optional[List[str]] = None,
        override_dtypes: Optional[dict] = None,
    ):
        json_columns = json_columns or []
        override_dtypes = override_dtypes or {}

        def _op():
            pandas_df = ensure_pandas(df).copy()

            # Apply dtype overrides
            for col, dtype in override_dtypes.items():
                if col in pandas_df.columns:
                    pandas_df[col] = pandas_df[col].astype(dtype)

            # Basic JSON handling: pre-serialize to text, cast on CTAS/INSERT if needed later.
            for col in json_columns:
                if col in pandas_df.columns:
                    pandas_df[col] = pandas_df[col].apply(
                        lambda x: None if x is None else (x if isinstance(x, str) else pd.io.json.dumps(x))
                    )

            # Temp view name (safe-ish)
            tmp_view = f"tmp_df_{abs(hash((table_name, len(pandas_df), tuple(pandas_df.columns))))}"

            # Register as view
            self._conn.register(tmp_view, pandas_df)

            fq_table = f'{self._ident_quote(schema)}.{self._ident_quote(table_name)}'

            if if_exists not in {"replace", "append", "fail"}:
                raise ValueError("if_exists must be one of: 'replace', 'append', 'fail'")

            # Ensure schema exists (DuckDB auto-creates main; CREATE SCHEMA IF NOT EXISTS is fine)
            self._conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self._ident_quote(schema)}")

            table_exists = self.check_if_table_exists(table_name, schema=schema)

            if if_exists == "fail" and table_exists:
                raise ValueError(f"Table {schema}.{table_name} already exists")

            if if_exists == "replace":
                if table_exists:
                    self._conn.execute(f"DROP TABLE {fq_table}")
                self._conn.execute(f"CREATE TABLE {fq_table} AS SELECT * FROM {self._ident_quote(tmp_view)}")
            elif if_exists == "append":
                if not table_exists:
                    self._conn.execute(f"CREATE TABLE {fq_table} AS SELECT * FROM {self._ident_quote(tmp_view)}")
                else:
                    self._conn.execute(f"INSERT INTO {fq_table} SELECT * FROM {self._ident_quote(tmp_view)}")

            # Unregister to free memory
            try:
                self._conn.unregister(tmp_view)
            except Exception:
                pass

        self._with_auto_reconnect(_op)

    def upload_iterable_to_table(
        self,
        iterable: Iterable,
        table_name: str,
        schema: str = "main",
        json_columns: Optional[List[str]] = None,
        override_dtypes: Optional[dict] = None,
    ):
        items = []
        for item in iterable:
            if isinstance(item, dict):
                items.append(item)
            elif isinstance(item, BaseModel):
                items.append(item.model_dump())
            else:
                raise ValueError(f"Item is not a dict nor BaseModel: {item}")

        if not items:
            return

        df = pd.DataFrame(items, columns=items[0].keys()).replace({None: np.nan})
        self.upload_df_to_table(
            df,
            table_name=table_name,
            schema=schema,
            json_columns=json_columns or [],
            override_dtypes=override_dtypes or {},
        )

    def upload_single_row_to_table(
        self,
        row: dict,
        table_name: str,
        schema: str = "main",
        json_columns: Optional[List[str]] = None,
        override_dtypes: Optional[dict] = None,
    ):
        self.upload_df_to_table(
            pd.DataFrame([row]),
            table_name=table_name,
            schema=schema,
            json_columns=json_columns or [],
            override_dtypes=override_dtypes or {},
        )
