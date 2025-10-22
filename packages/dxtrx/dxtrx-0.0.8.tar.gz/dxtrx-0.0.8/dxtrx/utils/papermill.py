import sys
import os

from dagster import EnvVar

def is_papermill_like():
    return any("--HistoryManager.hist_file=:memory:" in arg for arg in sys.argv)

def pm_exit(reason: str = "Notebook skipped.", exit_code: int = 0):
    print(f"✅ {reason}")
    if is_papermill_like():
        sys.exit(exit_code)
    else:
        print("ℹ️ Not running under Papermill/Dagstermill — skipping sys.exit to avoid traceback.")
        
def _is_running_in_dagster():
    """Detect if we're currently running inside a Dagster job or asset context."""
    try:
        # Try to directly access an EnvVar - this will fail outside Dagster
        test_env_var = EnvVar("_DAGSTER_CONTEXT_TEST")
        _ = str(test_env_var)  # This will raise RuntimeError outside Dagster
        return True
    except RuntimeError as e:
        if "Attempted to directly retrieve environment variable" in str(e):
            return False
        # If it's a different RuntimeError, re-raise it
        raise
    except Exception:
        # Any other exception means we're probably not in Dagster
        return False

def _auto_init(resource):
    """
    Automatically initialize a resource when not running inside Dagster.
    
    When inside Dagster: return the resource as-is (Dagster will inject it)
    When outside Dagster: call setup_for_execution to make it immediately usable
    """
    if _is_running_in_dagster():
        return resource
    
    # Create a new instance with resolved EnvVar values
    resolved_kwargs = {}
    
    # Only get the actual model fields, not Pydantic metadata
    for field_name in resource.model_fields.keys():
        attr_value = getattr(resource, field_name)
        
        # If it's an EnvVar, resolve it to the actual environment variable value
        if isinstance(attr_value, EnvVar):
            resolved_kwargs[field_name] = attr_value.get_value()
        # If it's a regular value (not None), include it
        elif attr_value is not None:
            resolved_kwargs[field_name] = attr_value
    
    # Create a new instance of the same resource class with resolved values
    resource_class = type(resource)
    resolved_resource = resource_class(**resolved_kwargs)
    resolved_resource.setup_for_execution(context={})
    
    return resolved_resource