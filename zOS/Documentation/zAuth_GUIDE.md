# zAuth: Three-Tier Authentication & Authorization

## Overview
**zAuth** provides enterprise-grade authentication and authorization for zOS with three-tier architecture, context-aware RBAC, and secure credential management.

**Key Features:**
- **Three-tier authentication**: zSession (internal), Application (external), Dual-Mode (both)
- **bcrypt password security**: Industry-standard hashing with 12 rounds
- **SQLite session persistence**: 7-day expiry with automatic cleanup
- **Context-aware RBAC**: Role and permission checks across all tiers
- **Multi-app support**: Simultaneous authentication for multiple applications

---

## Three-Tier Architecture

### Tier 1: zSession Authentication (Internal)
**For:** zOS/Zolo platform users (developers, admins, premium features)

```python
# Login as internal user
result = zcli.auth.login("dev@zolo.com", "password")

# Check authentication
if zcli.auth.is_authenticated():
    print("Logged in to zOS platform")
```

**Session Structure:**
```python
session["zAuth"]["zSession"] = {
    "authenticated": True,
    "username": "dev@zolo.com",
    "user_id": "123",
    "role": "developer"
}
```

### Tier 2: Application Authentication (External)
**For:** End-users of applications built with zOS (customers, employees, students)

```python
# Authenticate app user
result = zcli.auth.authenticate_app_user(
    app_name="my_store",
    token="customer_token_xyz",
    config={"auth_endpoint": "https://store.com/api/auth"}
)

# Get specific app user
store_user = zcli.auth.get_app_user("my_store")

# Switch between apps
zcli.auth.switch_app("admin_panel")
```

**Multi-App Session:**
```python
session["zAuth"]["applications"] = {
    "my_store": {"user_id": "c123", "role": "customer"},
    "admin_panel": {"user_id": "a456", "role": "admin"}
}
```

### Tier 3: Dual-Mode (Both Contexts)
**For:** Users with both zOS and application identities (store owners, app developers)

```python
# Login to both contexts
zcli.auth.login("owner@zolo.com", "password")           # zSession
zcli.auth.authenticate_app_user("my_store", token, config)  # Application

# System automatically detects dual-mode
# active_context = "dual"
# dual_mode = True

# Get current user (based on active context)
user = zcli.auth.get_active_user()

# RBAC uses OR logic in dual mode
if zcli.auth.has_role("admin"):
    # Returns True if EITHER zSession OR app user has admin role
    print("Admin access granted from either context")
```

---

## Password Security (bcrypt)

### Secure Hashing
```python
# Hash password with bcrypt (12 rounds, random salt)
hashed = zcli.auth.hash_password("user_password")
# Result: "$2b$12$randomsalt...hashedpassword"

# Verify password (timing-safe comparison)
is_valid = zcli.auth.verify_password("user_password", hashed)
# Returns: True (correct) or False (incorrect)
```

**Security Features:**
- **12 rounds** (2^12 = 4096 iterations) - slow by design
- **Random salts** - each hash is unique
- **Timing-safe** - prevents timing attacks
- **72-byte handling** - automatic truncation with logging

---

## Session Persistence (SQLite)

### Save and Load Sessions
```python
# Sessions automatically persist to SQLite database
# Location: Application Support/zolo-zcli/sessions.db

# Login with persistence (default: enabled)
result = zcli.auth.login("user@zolo.com", "password", persist=True)

# Session saved with:
# - User credentials (hashed)
# - Session token (random, secure)
# - Expiry date (7 days from login)

# Automatic session loading on next zOS start
# No re-login needed if session not expired

# Logout with cleanup
zcli.auth.logout(delete_persistent=True)
```

**Persistence Features:**
- **7-day expiry** - sessions auto-expire after 7 days
- **Automatic cleanup** - expired sessions removed on login
- **Secure tokens** - generated with `secrets.token_urlsafe()`
- **Multi-session** - supports concurrent sessions from different devices

---

## Context-Aware RBAC

### Role Checks
```python
# Check single role
if zcli.auth.has_role("admin"):
    print("User is admin")

# Check multiple roles (any match)
if zcli.auth.has_role(["admin", "moderator"]):
    print("User has admin OR moderator role")
```

### Context Behavior
**zSession context:**
```python
zcli.auth.set_active_context("zSession")
# Checks role in session["zAuth"]["zSession"]["role"]
```

**Application context:**
```python
zcli.auth.set_active_context("application")
# Checks role in session["zAuth"]["applications"][active_app]["role"]
```

**Dual-mode context (OR logic):**
```python
zcli.auth.set_active_context("dual")
# Returns True if EITHER zSession OR app user has the role
```

### Permission Checks
```python
# Check permission
if zcli.auth.has_permission("data.delete"):
    # Execute privileged operation
    pass

# Grant permission (requires admin)
zcli.auth.grant_permission(
    user_id="user_123",
    permission="data.write",
    granted_by="admin_456"
)

# Revoke permission
zcli.auth.revoke_permission("user_123", "data.write")
```

---

## Common Workflows

### 1. Simple zSession Login
```python
# Interactive login (prompts for credentials)
result = zcli.auth.login()

# Check result
if result["status"] == "success":
    creds = zcli.auth.get_credentials()
    print(f"Welcome, {creds['username']}!")
```

### 2. Multi-App Management
```python
# Authenticate multiple apps
zcli.auth.authenticate_app_user("store", "token1", config1)
zcli.auth.authenticate_app_user("forum", "token2", config2)

# Switch between apps
zcli.auth.switch_app("store")
store_user = zcli.auth.get_app_user("store")

zcli.auth.switch_app("forum")
forum_user = zcli.auth.get_app_user("forum")

# Logout specific app
zcli.auth.logout(context="application", app_name="forum")
```

### 3. Dual-Mode with RBAC
```python
# Login as developer (zSession)
zcli.auth.login("dev@zolo.com", "password")

# Authenticate as store owner (Application)
zcli.auth.authenticate_app_user("my_store", "owner_token", config)

# System detects dual-mode automatically
# Now RBAC checks BOTH contexts

# Returns True if EITHER developer OR store owner has admin role
if zcli.auth.has_role("admin"):
    print("Admin access from either context")

# Context-specific logout
zcli.auth.logout(context="zSession")      # Logout zOS only
zcli.auth.logout(context="application", app_name="my_store")  # Logout app only
zcli.auth.logout(context="all")            # Logout everything
```

---

## API Reference

### Authentication Methods

**`login(username, password, server_url=None, persist=True)`**
- Authenticate zSession user (internal)
- Returns: `{"status": "success"|"fail", "user": {...}}`

**`logout(context="zSession", app_name=None, delete_persistent=True)`**
- Logout from specified context
- Contexts: "zSession", "application", "dual", "all", "all_apps"

**`is_authenticated()`**
- Check if zSession is authenticated
- Returns: `bool`

**`get_credentials()`**
- Get zSession credentials
- Returns: `dict` or `None`

**`status()`**
- Get authentication status
- Returns: `{"status": "authenticated"|"not_authenticated", "user": {...}}`

### Application Methods

**`authenticate_app_user(app_name, token, config)`**
- Authenticate application user
- Returns: `{"status": "success"|"fail", "user": {...}}`

**`switch_app(app_name)`**
- Switch active application
- Returns: `bool`

**`get_app_user(app_name)`**
- Get application user data
- Returns: `dict` or `None`

### Context Methods

**`set_active_context(context)`**
- Set active authentication context
- Values: "zSession", "application", "dual"
- Returns: `bool`

**`get_active_user()`**
- Get user data from active context
- Returns: `dict` or `None`

### RBAC Methods

**`has_role(required_role)`**
- Check if user has role(s)
- Accepts: `str` or `List[str]`
- Returns: `bool`

**`has_permission(permission)`**
- Check if user has permission
- Returns: `bool`

**`grant_permission(user_id, permission, granted_by)`**
- Grant permission to user
- Returns: `bool`

**`revoke_permission(user_id, permission)`**
- Revoke permission from user
- Returns: `bool`

### Security Methods

**`hash_password(plain_password)`**
- Hash password with bcrypt
- Returns: `str` (hashed password)

**`verify_password(plain_password, hashed_password)`**
- Verify password against hash
- Returns: `bool`

---

## Session Constants

All session keys use zConfig constants for consistency:

```python
from zOS.subsystems.zConfig.zConfig_modules.config_session import (
    SESSION_KEY_ZAUTH,              # "zAuth"
    ZAUTH_KEY_ZSESSION,             # "zSession"
    ZAUTH_KEY_APPLICATIONS,         # "applications"
    ZAUTH_KEY_ACTIVE_CONTEXT,       # "active_context"
    ZAUTH_KEY_ACTIVE_APP,           # "active_app"
    ZAUTH_KEY_DUAL_MODE,            # "dual_mode"
    ZAUTH_KEY_ROLE,                 # "role"
    ZAUTH_KEY_USERNAME,             # "username"
    ZAUTH_KEY_AUTHENTICATED,        # "authenticated"
    CONTEXT_ZSESSION,               # "zSession"
    CONTEXT_APPLICATION,            # "application"
    CONTEXT_DUAL                    # "dual"
)
```

---

## Module Architecture

```
zAuth/
├── zAuth.py                        # Facade (orchestrates all modules)
└── zAuth_modules/
    ├── auth_password_security.py   # bcrypt hashing/verification
    ├── auth_session_persistence.py # SQLite session storage
    ├── auth_authentication.py      # Three-tier auth logic (CORE)
    └── authzRBAC.py               # Context-aware RBAC
```

**Facade Pattern:**
- `zAuth.py` provides unified API
- Delegates to specialized modules internally
- Clean separation of concerns

---

## Testing

### Run Tests
```bash
# Run zAuth comprehensive test suite
zolo ztests
# Select: "zAuth"

# Or directly via Python
python3 -c "
from zOS import zOS
test_cli = zOS({'zSpace': 'zTestRunner', 'zMode': 'Terminal'})
test_cli.zspark_obj['zVaFile'] = '@.zUI.zAuth_tests'
test_cli.walker.run()
"
```

### Test Coverage
**70 comprehensive tests** with **100% pass rate**:
- Facade API (5 tests)
- Password Security (6 tests) - real bcrypt operations
- Session Persistence (7 tests) - SQLite validation
- Tier 1 - zSession Auth (9 tests)
- Tier 2 - Application Auth (9 tests)
- Tier 3 - Dual-Mode Auth (7 tests)
- RBAC (9 tests) - context-aware role checks
- Context Management (6 tests)
- Integration Workflows (6 tests)
- Real Bcrypt Tests (3 tests) - actual hashing/verification
- Real SQLite Tests (3 tests) - persistence round-trip

---

## Best Practices

### 1. Check Authentication First
```python
if not zcli.auth.is_authenticated():
    result = zcli.auth.login()
    if result["status"] != "success":
        return {"error": "Authentication required"}

# Proceed with authenticated action
```

### 2. Use Context-Aware RBAC
```python
# Set appropriate context before RBAC checks
zcli.auth.set_active_context("zSession")

if zcli.auth.has_role("admin"):
    # Admin-only operations
    pass
```

### 3. Handle Multi-App Isolation
```python
# Apps are automatically isolated
# Switching apps changes active_app but preserves all app sessions

zcli.auth.switch_app("store")
# Now RBAC checks store user's role

zcli.auth.switch_app("admin_panel")
# Now RBAC checks admin_panel user's role
```

### 4. Secure Password Handling
```python
# ALWAYS hash passwords before storage
hashed = zcli.auth.hash_password(plain_password)

# NEVER store plain passwords
# NEVER compare passwords with ==
# Use verify_password() for timing-safe comparison
```

### 5. Clean Logout
```python
# On application exit or logout
zcli.auth.logout(context="all", delete_persistent=True)
```

---

## Integration with zOS Subsystems

### zConfig
Provides all session constants and structure.

### zDisplay
All authentication UI via `zDisplay.zEvents.zAuth` events:
- `login_prompt`, `login_success`, `login_failure`
- `logout_success`, `status_display`
- Dual-mode compatible (Terminal + Bifrost)

### zComm
Remote authentication uses `zComm.http_post()` for API calls.

### zData
Session persistence and permissions use declarative zData operations.

### zWizard
RBAC integration for menu access control:
- `require_auth`, `require_role`, `require_permission` directives

---

## Summary

**zAuth** provides enterprise-grade authentication with:
- **Three-tier architecture** for internal and external users
- **bcrypt security** with 12 rounds and random salts
- **SQLite persistence** with 7-day auto-expiry
- **Context-aware RBAC** with OR logic in dual-mode
- **Multi-app support** with isolated contexts
- **70 tests at 100%** ensuring production readiness

For display integration, see [zDisplay_GUIDE.md](zDisplay_GUIDE.md).  
For session constants, see [zConfig_GUIDE.md](zConfig_GUIDE.md).  
For remote API integration, see [zComm_GUIDE.md](zComm_GUIDE.md).
