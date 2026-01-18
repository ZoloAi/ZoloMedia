# zCLI/subsystems/zWizard/zWizard_modules/wizard_rbac.py

"""
Wizard RBAC - Role-Based Access Control for Wizard Steps
=========================================================

Enforces RBAC (Role-Based Access Control) at the zKey level during wizard and
walker execution. Each step can declare authentication and authorization
requirements via `zRBAC` metadata.

Core Responsibilities
--------------------
1. **Authentication Check**: Verify user is logged in (`require_auth`)
2. **Role Check**: Verify user has required role(s) (`require_role`)
3. **Permission Check**: Verify user has required permission(s) (`require_permission`)
4. **Access Denial**: Display user-friendly access denied messages
5. **Audit Logging**: Log all access denials for security audit

RBAC Architecture
----------------
### Four-Level Hierarchy
1. **Public Access**: No `zRBAC` metadata = accessible to all users
2. **Guest-Only Access**: `zGuest: true` = unauthenticated users only (login/register pages)
3. **Authenticated Access**: `require_auth: true` = logged-in users only
4. **Authorized Access**: `require_role` or `require_permission` = specific users

### Check Order (Short-Circuit)
1. No `zRBAC`? → Access granted (public)
2. No auth subsystem? → Access denied (fail-safe)
3. `require_auth` + not authenticated? → Access denied
4. `require_role` + no role? → Access denied
5. `require_permission` + no permission? → Access denied
6. All checks passed? → Access granted

RBAC Metadata Format
-------------------
### In zUI YAML Files
```yaml
^Admin_Feature:
  zRBAC:
    require_auth: true                    # Must be logged in
    require_role: "admin"                 # Must have "admin" role
    require_permission: "manage_users"    # Must have permission
  zDisplay:
    event: text
    content: "Admin-only feature"
```

### Metadata Fields
- **zGuest** (bool): Require guest (unauthenticated) - denies authenticated users
- **require_auth** (bool): Require authentication
- **require_role** (str | list): Require role(s) - ANY match grants access
- **require_permission** (str | list): Require permission(s) - ANY match grants access

### Multiple Roles/Permissions (OR Logic)
```yaml
zRBAC:
  require_role: ["admin", "moderator"]  # admin OR moderator
  require_permission: ["read", "write"] # read OR write
```

Access Denial Flow
-----------------
### User Experience (Terminal + Bifrost)
```
[ACCESS DENIED] ^Delete_User
  Reason: Role required: admin
  Tip: Check your role/permissions or log in
```

### Display Events Generated
1. Empty text line (spacing)
2. Error event with "ACCESS DENIED" header
3. Text event with denial reason
4. Text event with user tip
5. Empty text line (spacing)

### Logging
```
[RBAC] Access denied for '^Delete_User': Role required: admin
```

Usage Examples
-------------
### Example 1: Guest-Only Access (Login/Register Pages)
```yaml
^zLogin:
  zRBAC:
    zGuest: true  # Only show if NOT logged in
  zDialog:
    title: "User Login"
    fields: [email, password]
```

### Example 2: Authentication Only
```yaml
^Profile:
  zRBAC:
    require_auth: true
  zDisplay:
    event: text
    content: "Your profile: {{ session.username }}"
```

### Example 2: Role Requirement
```yaml
^Admin_Panel:
  zRBAC:
    require_role: "admin"  # Implies authentication
  zDisplay:
    event: text
    content: "Admin panel access"
```

### Example 3: Permission Requirement
```yaml
^Delete_User:
  zRBAC:
    require_permission: "users.delete"
  zData:
    operation: delete
    model: "users"
    where: {id: "{{ zHat.user_id }}"}
```

### Example 4: Multiple Requirements
```yaml
^Sensitive_Data:
  zRBAC:
    require_auth: true
    require_role: ["admin", "auditor"]
    require_permission: ["data.read", "data.export"]
  zDisplay:
    event: text
    content: "Sensitive data export"
```

Integration with zAuth
----------------------
### Authentication Methods
- `is_authenticated()`: Check if user is logged in
- `has_role(role)`: Check if user has specific role
- `has_permission(permission)`: Check if user has permission

### Context-Aware RBAC
- **zSession Mode**: Session-based authentication
- **Application Mode**: Application-level authentication
- **Dual Mode**: Hybrid authentication context

Error Handling
-------------
- **No auth subsystem**: Fail-safe to "access_denied"
- **Invalid RBAC metadata**: Treated as public (no restrictions)
- **Display unavailable**: Access still checked, message not shown
- **Logger unavailable**: Access still checked, not logged

Constants Reference
-------------------
- RBAC_ACCESS_GRANTED, RBAC_ACCESS_DENIED: Return values
- _RBAC_KEY: Dict key for RBAC metadata (zRBAC)
- _RBAC_REQUIRE_AUTH, _RBAC_REQUIRE_ROLE, _RBAC_REQUIRE_PERMISSION: RBAC fields
- LOG_MSG_*: Log messages for various scenarios
- _MSG_AUTH_REQUIRED, _MSG_ROLE_REQUIRED, _MSG_PERMISSION_REQUIRED: Display messages
- EVENT_*: Display event types

Dependencies
-----------
- **zAuth**: Authentication and authorization checks
- **zDisplay**: User-friendly access denial messages
- **Logger**: Security audit logging

Best Practices
-------------
1. **Principle of Least Privilege**: Only add RBAC when necessary
2. **Clear Denial Messages**: Use descriptive role/permission names
3. **Audit Trail**: Review RBAC logs regularly for security issues
4. **Graceful Degradation**: UI should work without auth (public features)
5. **Test Coverage**: Test with multiple user roles

Layer: 2, Position: 2 (zWizard subsystem)
Week: 6.14
Version: v1.5.4 Phase 1 (Industry-Grade, RBAC from Week 3.3)
"""

from zOS import Any, Optional

# Import constants from centralized file
from .wizard_constants import (
    # Public constants
    RBAC_ACCESS_GRANTED,
    RBAC_ACCESS_DENIED,
    RBAC_ACCESS_DENIED_ZGUEST,
    # Internal constants
    _RBAC_KEY,
    _RBAC_REQUIRE_AUTH,
    _RBAC_REQUIRE_ROLE,
    _RBAC_REQUIRE_PERMISSION,
    _RBAC_ZGUEST,
    _LOG_MSG_NO_AUTH_SUBSYSTEM,
    _LOG_MSG_ACCESS_GRANTED,
    _LOG_MSG_ACCESS_DENIED,
    _MSG_AUTH_REQUIRED,
    _MSG_ROLE_REQUIRED,
    _MSG_PERMISSION_REQUIRED,
    _MSG_ZGUEST_ONLY,
    _MSG_ZGUEST_REDIRECT,
    _MSG_ACCESS_DENIED_HEADER,
    _MSG_DENIAL_REASON,
    _MSG_DENIAL_TIP,
    _EVENT_TEXT,
    _EVENT_ERROR,
    _KEY_EVENT,
    _KEY_CONTENT,
    _KEY_INDENT,
    _KEY_BREAK_AFTER,
    _INDENT_LEVEL_0,
    _INDENT_LEVEL_1,
    _FORMAT_ONE_OF,
    _RBAC_ERROR_COLOR,
    _RBAC_INDENT_LEVEL,
)

__all__ = [
    # Public Functions
    "checkzRBAC_access",
    "display_access_denied",
    "display_access_denied_zguest",
    # Public Constants (re-export)
    "RBAC_ACCESS_GRANTED",
    "RBAC_ACCESS_DENIED",
    "RBAC_ACCESS_DENIED_ZGUEST",
]


def checkzRBAC_access(
    key: str,
    value: Any,
    zcli: Optional[Any],
    walker: Optional[Any],
    logger: Any,
    display: Optional[Any]
) -> str:
    """
    Check RBAC access for a zKey before execution (v1.5.4 Week 3.3).
    
    Args:
        key: zKey name (e.g., "^Delete User")
        value: zKey value (parsed item with potential zRBAC metadata)
        zcli: zCLI instance (if direct mode)
        walker: zWalker instance (if walker mode)
        logger: Logger instance
        display: Display instance
    
    Returns:
        str: "access_granted" or "access_denied"
    """
    # Extract RBAC metadata (if it exists)
    rbac = None
    if isinstance(value, dict):
        rbac = value.get(_RBAC_KEY)
    
    # No RBAC requirements = public access
    if not rbac:
        return RBAC_ACCESS_GRANTED
    
    # Get zCLI instance (from walker or direct)
    zcli_instance = walker.zcli if walker else zcli
    if not zcli_instance or not hasattr(zcli_instance, 'auth'):
        logger.warning(_LOG_MSG_NO_AUTH_SUBSYSTEM)
        return RBAC_ACCESS_DENIED
    
    # Check zGuest (guest-only access - user must NOT be authenticated)
    if rbac.get(_RBAC_ZGUEST):
        if zcli_instance.auth.is_authenticated():
            # User is authenticated but this is guest-only
            # This is a GOOD thing - user is logged in! Just redirect gracefully
            display_access_denied_zguest(key, _MSG_ZGUEST_ONLY, display, logger)
            return RBAC_ACCESS_DENIED_ZGUEST  # Special return code (no pause needed)
    
    # Check require_auth (must be authenticated)
    if rbac.get(_RBAC_REQUIRE_AUTH):
        if not zcli_instance.auth.is_authenticated():
            display_access_denied(key, _MSG_AUTH_REQUIRED, display, logger)
            return RBAC_ACCESS_DENIED
    
    # Check require_role (implies authentication)
    required_role = rbac.get(_RBAC_REQUIRE_ROLE)
    if required_role is not None:
        # Role requirement implies authentication
        if not zcli_instance.auth.is_authenticated():
            display_access_denied(key, _MSG_AUTH_REQUIRED, display, logger)
            return RBAC_ACCESS_DENIED
        
        if not zcli_instance.auth.has_role(required_role):
            role_str = required_role if isinstance(required_role, str) else (_FORMAT_ONE_OF % required_role)
            display_access_denied(key, _MSG_ROLE_REQUIRED % role_str, display, logger)
            return RBAC_ACCESS_DENIED
    
    # Check require_permission (implies authentication)
    required_permission = rbac.get(_RBAC_REQUIRE_PERMISSION)
    if required_permission:
        # Permission requirement implies authentication
        if not zcli_instance.auth.is_authenticated():
            display_access_denied(key, _MSG_AUTH_REQUIRED, display, logger)
            return RBAC_ACCESS_DENIED
        
        if not zcli_instance.auth.has_permission(required_permission):
            perm_str = required_permission if isinstance(required_permission, str) else (_FORMAT_ONE_OF % required_permission)
            display_access_denied(key, _MSG_PERMISSION_REQUIRED % perm_str, display, logger)
            return RBAC_ACCESS_DENIED
    
    # All checks passed
    logger.debug(_LOG_MSG_ACCESS_GRANTED, key)
    return RBAC_ACCESS_GRANTED


def display_access_denied(
    key: str,
    reason: str,
    display: Optional[Any],
    logger: Any
) -> None:
    """
    Display access denied message (Terminal + zBifrost compatible).
    
    Args:
        key: zKey name that was denied
        reason: Reason for denial
        display: Display instance
        logger: Logger instance
    """
    if display:
        # Display clear access denied message (no break to avoid input prompt in tests)
        display.handle({
            _KEY_EVENT: _EVENT_TEXT,
            _KEY_CONTENT: "",
            _KEY_INDENT: _INDENT_LEVEL_0,
            _KEY_BREAK_AFTER: False
        })
        display.handle({
            _KEY_EVENT: _EVENT_ERROR,
            _KEY_CONTENT: _MSG_ACCESS_DENIED_HEADER % key,
            _KEY_INDENT: _INDENT_LEVEL_1
        })
        display.handle({
            _KEY_EVENT: _EVENT_TEXT,
            _KEY_CONTENT: _MSG_DENIAL_REASON % reason,
            _KEY_INDENT: _INDENT_LEVEL_2,
            _KEY_BREAK_AFTER: False
        })
        display.handle({
            _KEY_EVENT: _EVENT_TEXT,
            _KEY_CONTENT: _MSG_DENIAL_TIP,
            _KEY_INDENT: _INDENT_LEVEL_2,
            _KEY_BREAK_AFTER: False
        })
        display.handle({
            _KEY_EVENT: _EVENT_TEXT,
            _KEY_CONTENT: "",
            _KEY_INDENT: _INDENT_LEVEL_0,
            _KEY_BREAK_AFTER: False
        })
    
    # Log the denial
    logger.warning(_LOG_MSG_ACCESS_DENIED, key, reason)


def display_access_denied_zguest(
    key: str,
    reason: str,
    display: Optional[Any],
    logger: Any
) -> None:
    """
    Display friendly redirect message for zGuest (guest-only) pages.
    
    This is NOT an error - it's a feature! User is logged in, which is good.
    We just redirect them away from login/register pages gracefully.
    
    Args:
        key: zKey name that was denied
        reason: Reason for denial
        display: Display instance
        logger: Logger instance
    """
    if display:
        # Display friendly redirect message (positive tone!)
        display.handle({
            _KEY_EVENT: _EVENT_TEXT,
            _KEY_CONTENT: "",
            _KEY_INDENT: _INDENT_LEVEL_0,
            _KEY_BREAK_AFTER: False
        })
        display.handle({
            _KEY_EVENT: _EVENT_TEXT,
            _KEY_CONTENT: "✓ " + _MSG_ZGUEST_ONLY,
            _KEY_INDENT: _INDENT_LEVEL_1,
            _KEY_BREAK_AFTER: False
        })
        display.handle({
            _KEY_EVENT: _EVENT_TEXT,
            _KEY_CONTENT: _MSG_ZGUEST_REDIRECT,
            _KEY_INDENT: _INDENT_LEVEL_1,
            _KEY_BREAK_AFTER: False
        })
        display.handle({
            _KEY_EVENT: _EVENT_TEXT,
            _KEY_CONTENT: "",
            _KEY_INDENT: _INDENT_LEVEL_0,
            _KEY_BREAK_AFTER: False
        })
    
    # Log as info (not a warning - this is expected behavior!)
    logger.info(_LOG_MSG_ACCESS_DENIED, key, reason)


