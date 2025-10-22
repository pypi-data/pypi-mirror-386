import pandas as pd
import polars as pl

from .types import DataFrameType
from .dataframe_conversion import ensure_pandas

def safe_astype_datetime(series):
    """
    Safely converts a pandas Series to datetime64[ns], handling timezone-aware dtypes.
    
    Note: This function works only with pandas Series. For DataFrames, use the appropriate
    conversion functions first.
    
    Args:
        series: pandas Series to convert
        
    Returns:
        pandas Series converted to datetime64[ns]
    """
    if not isinstance(series, pd.Series):
        raise TypeError(f"Expected pandas Series, got {type(series)}")
        
    series = pd.to_datetime(series, errors="coerce").dt.tz_localize(None)
    
    if pd.api.types.is_datetime64tz_dtype(series):
        # Remove timezone first
        return series.astype("datetime64[ns]")
    elif pd.api.types.is_datetime64_any_dtype(series):
        return series.astype("datetime64[ns]")
    else:
        raise TypeError("Series is not datetime-like and cannot be safely converted to datetime64[ns]")


def safe_astype(series, dtype):
    """
    Safely converts a pandas Series to the specified dtype, with special handling for datetime conversions.
    
    Note: This function works only with pandas Series. For DataFrames, use the appropriate
    conversion functions first.
    
    Args:
        series: pandas Series to convert
        dtype: Target dtype as string or numpy/pandas dtype
        
    Returns:
        pandas Series converted to the specified dtype
    """
    if not isinstance(series, pd.Series):
        raise TypeError(f"Expected pandas Series, got {type(series)}")
        
    # Normalize string dtype to str
    dtype_str = str(dtype)

    if dtype_str in ["datetime64[ns]", "datetime64"]:
        return safe_astype_datetime(series)
    elif pd.api.types.is_datetime64tz_dtype(series) and dtype_str.startswith("datetime64"):
        return safe_astype_datetime(series)
    else:
        return series.astype(dtype)