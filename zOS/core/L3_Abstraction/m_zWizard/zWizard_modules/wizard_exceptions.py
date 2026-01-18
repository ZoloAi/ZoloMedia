# zCLI/subsystems/zWizard/zWizard_modules/wizard_exceptions.py

"""
Wizard Exceptions - Custom Exception Classes for zWizard Subsystem
===================================================================

Provides a hierarchy of exception types for different zWizard failure modes,
enabling precise error handling and diagnostic messaging.

Exception Hierarchy
-------------------
```
zWizardError (base exception)
├── WizardInitializationError    - Raised during wizard setup/init
├── WizardExecutionError          - Raised during step execution
└── WizardRBACError               - Raised on access control violations
```

Design Philosophy
----------------
1. **Specific Types**: Each exception indicates a distinct failure category
2. **Inherits from Base**: All inherit from `zWizardError` for catch-all handling
3. **Descriptive Messages**: Exception messages should explain what failed and why
4. **Standard Exception**: Follows Python exception conventions

Exception Types
--------------
### zWizardError (Base Class)
- **Purpose**: Base for all wizard-related exceptions
- **When to Use**: Catch-all for any wizard error
- **When to Raise**: Never directly, use subclasses

### WizardInitializationError
- **Purpose**: Signals wizard setup/initialization failures
- **Common Causes**:
  - Missing required zcli or walker instance
  - Invalid configuration parameters
  - Missing dependencies (logger, session, display)
- **When to Raise**: During `__init__()` method
- **Example**:
  ```python
  if not zcli and not walker:
      raise WizardInitializationError(
          "zWizard requires either zcli or walker instance"
      )
  ```

### WizardExecutionError
- **Purpose**: Signals failures during wizard step execution
- **Common Causes**:
  - Step dispatch failure
  - Invalid step value or structure
  - Error in step processing (zDisplay, zData, etc.)
  - Transaction failures
- **When to Raise**: During `execute_loop()` or `handle()` methods
- **Example**:
  ```python
  try:
      result = dispatch_fn(key, value)
  except Exception as e:
      raise WizardExecutionError(
          f"Step '{key}' failed: {e}"
      ) from e
  ```

### WizardRBACError
- **Purpose**: Signals RBAC (access control) violations
- **Common Causes**:
  - User not authenticated (requires login)
  - Missing required role
  - Missing required permission
- **When to Raise**: During RBAC checks in `checkzRBAC_access()`
- **Note**: Currently, RBAC failures return "access_denied" rather than raising
- **Example**:
  ```python
  if not user.has_permission(required_permission):
      raise WizardRBACError(
          f"Permission required: {required_permission}"
      )
  ```

Usage Patterns
-------------
### Importing Exceptions
```python
from zOS.L3_Abstraction.m_zWizard.zWizard_modules.wizard_exceptions import (
    WizardInitializationError,
    WizardExecutionError,
    WizardRBACError,
    zWizardError  # For catch-all
)
```

### Raising Exceptions
```python
# Initialization check
if not self.display:
    raise WizardInitializationError("Display subsystem required")

# Execution failure
if result == "error":
    raise WizardExecutionError(f"Step '{key}' returned error")

# RBAC violation
if not authenticated:
    raise WizardRBACError("Authentication required")
```

### Catching Exceptions
```python
# Catch specific exception
try:
    wizard.execute_loop(items)
except WizardExecutionError as e:
    logger.error("Execution failed: %s", e)
    display_error_to_user(str(e))

# Catch any wizard exception
try:
    wizard.execute_loop(items)
except zWizardError as e:
    logger.error("Wizard error: %s", e)
    return "error"

# Catch with re-raise
try:
    wizard.execute_loop(items)
except Exception as e:
    raise WizardExecutionError(f"Unexpected error: {e}") from e
```

Error Message Best Practices
----------------------------
1. **Be Specific**: State what failed and where
   - Good: "Step 'fetch_users' failed: Connection timeout"
   - Bad: "Error occurred"

2. **Include Context**: Add relevant variable values
   - Good: "Missing required parameter 'user_id' in step 'update_profile'"
   - Bad: "Missing parameter"

3. **Suggest Solutions**: Help users fix the issue
   - Good: "zWizard requires either zcli or walker instance. Check initialization."
   - Bad: "Invalid init"

4. **Chain Exceptions**: Use `from e` to preserve stack trace
   ```python
   except Exception as e:
       raise WizardExecutionError("...") from e
   ```

Constants Reference
-------------------
- Common error messages defined as module constants (see below)

Dependencies
-----------
- **None**: Pure exception classes, no external dependencies

Layer: 2, Position: 2 (zWizard subsystem)
Week: 6.14
Version: v1.5.4 Phase 1 (Industry-Grade)
"""

# Import constants from centralized file
from .wizard_constants import (
    # Public constant
    ERR_MISSING_INSTANCE,
    # Internal constants
    _ERR_MISSING_DISPLAY,
    _ERR_MISSING_LOGGER,
    _ERR_INVALID_CONFIG,
    _ERR_STEP_FAILED,
    _ERR_DISPATCH_FAILED,
    _ERR_INVALID_STEP,
    _ERR_TRANSACTION_FAILED,
    _ERR_NOT_AUTHENTICATED,
    _ERR_MISSING_ROLE,
    _ERR_MISSING_PERMISSION,
    _ERR_ACCESS_DENIED,
)

__all__ = [
    # Exception Classes
    "zWizardError",
    "WizardInitializationError",
    "WizardExecutionError",
    "WizardRBACError",
    # Public Constants (re-export)
    "ERR_MISSING_INSTANCE",
]


class zWizardError(Exception):
    """
    Base exception for all zWizard subsystem errors.
    
    All wizard-related exceptions inherit from this class.
    Use this for catching any wizard error.
    """


class WizardInitializationError(zWizardError):
    """
    Raised when zWizard initialization fails.
    
    Common causes:
    - Missing required zcli or walker instance
    - Invalid configuration
    - Missing dependencies (logger, session, etc.)
    
    Example:
        >>> raise WizardInitializationError(
        ...     "zWizard requires a walker with a session"
        ... )
    """


class WizardExecutionError(zWizardError):
    """
    Raised when wizard step execution fails.
    
    Common causes:
    - Step dispatch failure
    - Invalid step value
    - Error in step processing
    
    Example:
        >>> raise WizardExecutionError(
        ...     f"Step '{step_key}' failed: {error}"
        ... )
    """


class WizardRBACError(zWizardError):
    """
    Raised when RBAC (Role-Based Access Control) check fails.
    
    Common causes:
    - User not authenticated
    - Missing required role
    - Missing required permission
    
    Example:
        >>> raise WizardRBACError(
        ...     "User lacks admin role required for this operation"
        ... )
    """


