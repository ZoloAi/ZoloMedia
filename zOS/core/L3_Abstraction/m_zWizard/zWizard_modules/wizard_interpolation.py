# zCLI/subsystems/zWizard/zWizard_modules/wizard_interpolation.py

"""
Wizard Interpolation - zHat Template Variable Interpolation
===========================================================

Recursively interpolates zHat references in strings, dictionaries, and lists.
This enables declarative workflows where later steps can reference earlier
step results using template syntax.

Interpolation Syntax
--------------------
### Supported Formats
- **zHat[0]**: Numeric indexing (backward compatible)
- **zHat["step1"]** or **zHat['step1']**: String key with quotes
- **zHat[step1]**: String key without quotes (recommended for YAML)

### Key Features
- **Recursive Processing**: Works at any nesting level
- **Type Preservation**: Maintains original data structure types
- **Safe Fallback**: Returns "None" string for missing keys (with warning)
- **Flexible Keys**: Supports both numeric and string key access

Works at Any Nesting Level
--------------------------
- **Top-level strings**: `"zHat[0]"` → Interpolated directly
- **Nested in dicts**: `{zDisplay: {content: "zHat[fetch_files]"}}` → Recursively processed
- **Nested in lists**: `["zHat[0]", "zHat[1]"]` → Each element interpolated
- **Mixed structures**: `{items: ["zHat[step1]", {"id": "zHat[step2]"}]}`

Interpolation Examples
----------------------
### Simple String Interpolation
```python
zHat.add("greeting", "Hello")
result = interpolate_zhat("Message: zHat[greeting]", zHat, logger)
# Result: "Message: 'Hello'"
```

### Dictionary Interpolation
```python
zHat.add("user_id", 42)
zHat.add("username", "alice")
config = {
    "user": "zHat[username]",
    "id": "zHat[user_id]"
}
result = interpolate_zhat(config, zHat, logger)
# Result: {"user": "42", "id": "'alice'"}
```

### List Interpolation
```python
zHat.add("file1", "/path/to/file1")
zHat.add("file2", "/path/to/file2")
files = ["zHat[file1]", "zHat[file2]"]
result = interpolate_zhat(files, zHat, logger)
# Result: ["'/path/to/file1'", "'/path/to/file2'"]
```

### Nested Structure Interpolation
```yaml
step1:
  type: zFunc
  function: get_user_data
  
step2:
  type: zDisplay
  content:
    header: "User Details"
    data:
      - "Name: zHat[step1][name]"
      - "Email: zHat[step1][email]"
```

Error Handling
--------------
- **Missing Keys**: Logs warning and returns "None" string
- **Invalid Indices**: Returns "None" string for out-of-range indices
- **Type Safety**: Non-interpolatable types (int, bool, None) returned as-is

Constants Reference
-------------------
- ZHAT_PATTERN: Regex pattern for matching zHat references
- ZHAT_FALLBACK: Default value for missing keys
- LOG_MSG_KEY_NOT_FOUND: Warning message for missing keys
- STR_QUOTE_CHARS: Characters to strip from quoted keys

Dependencies
-----------
- **re**: Regular expression module for pattern matching
- **WizardHat**: Container with dual/triple access for step results

Layer: 2, Position: 2 (zWizard subsystem)
Week: 6.14
Version: v1.5.4 Phase 1 (Industry-Grade)
"""

from zOS import Any
from zOS import re

# Import constants from centralized file
from .wizard_constants import (
    _ZHAT_PATTERN,
    _ZHAT_FALLBACK,
    _LOG_MSG_KEY_NOT_FOUND,
    _STR_QUOTE_CHARS,
)

__all__ = ["interpolate_zhat"]


def interpolate_zhat(step_value: Any, zHat: Any, logger: Any) -> Any:
    """
    Recursively interpolate zHat references in strings (including nested structures).
    
    Supports:
    - zHat[0], zHat[1], ...              # Numeric indexing (backward compat)
    - zHat["step1"], zHat['step1']       # String key with quotes
    - zHat[step1]                        # String key without quotes
    
    Works at any nesting level:
    - Top-level strings: "zHat[0]"
    - Nested in dicts: {zDisplay: {content: "zHat[fetch_files]"}}
    - Nested in lists: ["zHat[0]", "zHat[1]"]
    
    Args:
        step_value: Value to interpolate (str, dict, list, or primitive)
        zHat: WizardHat instance with dual access
        logger: Logger instance for warnings
        
    Returns:
        Interpolated value (same type as input)
    """
    # Handle strings (base case - actual interpolation happens here)
    if isinstance(step_value, str):
        def repl(match: Any) -> str:
            key = match.group(1)
            
            # Handle numeric index (backward compatible)
            if key.isdigit():
                idx = int(key)
                return str(zHat[idx]) if idx < len(zHat) else _ZHAT_FALLBACK
            
            # Handle string key (remove quotes if present)
            key_clean = key.strip(_STR_QUOTE_CHARS)
            
            # Check if key exists in zHat
            if key_clean in zHat:
                return str(zHat[key_clean])
            
            # Key not found - return None
            logger.warning(_LOG_MSG_KEY_NOT_FOUND, key_clean)
            return _ZHAT_FALLBACK
        
        # Use constant pattern for regex substitution
        return re.sub(_ZHAT_PATTERN, repl, step_value)
    
    # Handle dicts (recursive case)
    elif isinstance(step_value, dict):
        # DON'T interpolate 'if' conditions - they are Python expressions to be evaluated
        # Interpolating them would replace zHat[0] with the current value before evaluation
        return {
            k: (v if k == 'if' else interpolate_zhat(v, zHat, logger))
            for k, v in step_value.items()
        }
    
    # Handle lists (recursive case)
    elif isinstance(step_value, list):
        return [interpolate_zhat(item, zHat, logger) for item in step_value]
    
    # Other types (int, bool, None, etc.) - return as-is
    else:
        return step_value


