# zCLI Import Centralization Rules

## Purpose
All Python standard library and third-party imports are centralized in `zCLI/__init__.py` to:
1. **Prevent namespace collisions** (e.g., `time` module vs `datetime.time` class)
2. **Ensure consistent versioning** across the codebase
3. **Simplify dependency management**
4. **Enable global import mocking** for testing

## Rules

### ✅ DO: Import from zCLI
```python
# In subsystem files
from zCLI import time, datetime, os, Path, json
```

### ❌ DON'T: Direct imports in subsystems
```python
# WRONG - bypass centralization
import time
from datetime import datetime
```

### Exception: Local-only imports
```python
# OK for subsystem-specific imports not in __all__
def some_function():
    from datetime import datetime  # Local scope, doesn't pollute global
    return datetime.now()
```

## Critical Collision Fix (Dec 2024)

### The Bug
```python
# zCLI/__init__.py (BROKEN)
import time                               # Line 223: time module
from datetime import datetime, date, time, timedelta  # Line 229: OVERWRITES time!
```

**Error**: `type object 'datetime.time' has no attribute 'time'`

**Cause**: The `time` import from `datetime` overwrote the `time` module, so `time.time()` tried to call `datetime.time.time()` which doesn't exist.

### The Fix
```python
# zCLI/__init__.py (FIXED)
import time                               # Line 223: time module
# NOTE: Do NOT import 'time' from datetime - it would overwrite the time module
from datetime import datetime, date, timedelta  # Line 229: time removed
```

**Result**: 
- `time` = time module (with `time()`, `sleep()`, etc.)
- `datetime` = datetime class (with `now()`, `strptime()`, etc.)
- `date` = date class
- `timedelta` = timedelta class

If you need the `datetime.time` **type** for type hints:
```python
from datetime import time as datetime_time  # Explicit alias
# Or use directly: datetime.time(12, 30)
```

## __all__ Export List

All imports in `zCLI/__init__.py` must be listed in `__all__`:

```python
__all__: List[str] = [
    # Core class
    "zCLI",
    
    # System modules
    "asyncio", "datetime", "date", "time", "timedelta", ...
    
    # Typing helpers
    "Any", "Callable", "Dict", "List", ...
]
```

## Verification
Run this to verify imports work correctly:
```bash
python3 -B -c "
from zCLI import time, datetime, date, timedelta
assert str(type(time)) == \"<class 'module'>\"
assert hasattr(time, 'time')
assert str(type(datetime)) == \"<class 'type'>\"
print('✅ All imports verified')
"
```

## Impact of Centralization

### Before (Decentralized)
```python
# 50 files each with:
import time
from datetime import datetime
import json
```
**Issues**: Version conflicts, namespace collisions, hard to mock

### After (Centralized)
```python
# 1 file (zCLI/__init__.py):
import time
from datetime import datetime, date, timedelta
import json

# 50 files with:
from zCLI import time, datetime, json
```
**Benefits**: Single source of truth, no collisions, easy mocking

## Common Pitfalls

### 1. Shadowing Built-ins
```python
# BAD
from datetime import time  # Shadows time module
from asyncio import open_connection as open  # Shadows open()
```

### 2. Circular Dependencies
```python
# If zCLI/__init__.py imports from subsystems:
from zCLI.subsystems.zData import zData  # Circular!
```
**Solution**: Only import external libraries in `__init__.py`, not internal modules.

### 3. Missing __all__ Export
```python
# Added to imports but forgot __all__
import new_module  # In imports
# Missing from __all__ → not accessible via `from zCLI import new_module`
```

## Maintenance Checklist

When adding new imports to `zCLI/__init__.py`:

- [ ] Check for namespace collisions (e.g., `time` vs `datetime.time`)
- [ ] Add to `__all__` export list
- [ ] Update `EXPORT_COUNT` (auto-calculated from `len(__all__)`)
- [ ] Verify with `python3 -B -c "from zCLI import new_module; print(new_module)"`
- [ ] Clear `__pycache__` after changes: `find . -name "*.pyc" -delete`
- [ ] Document breaking changes in this file

## Version History

- **v1.5.8** (Dec 24, 2024): Fixed `time` module collision with `datetime.time`
  - Removed `time` from `from datetime import ...`
  - Added documentation comment above datetime import
  - Verified plugin loading works correctly

