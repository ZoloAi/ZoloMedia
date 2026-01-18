# zDialog Subsystem Guide

## Overview

**zDialog** is zOS's **Interactive Form/Dialog Subsystem**. It handles form rendering, data collection, auto-validation against zSchema, and submission processing with mode-agnostic support for both Terminal and Bifrost (GUI) environments.

### Start Here: First Tutorials
- **Display primitives first.** Run the new micro-step demos in `Demos/Layer_1/zDisplay_Demo/output/Level_1_Primitives/` (write_raw, write_line, write_block) to see how raw text flows through zDisplay before adding form-specific rendering.
- These three scripts mirror the zConfig/zComm tutorial style—quick, copy/paste-ready steps—and form the entry point for this guide before you move into zDialog-specific YAML forms.

### Executive Summary
zDialog enables developers to create interactive forms declaratively using YAML, with automatic validation against data schemas and intelligent placeholder injection. Forms work seamlessly in both command-line (Terminal) and web-based (Bifrost) modes. The subsystem handles complex workflows like multi-field data collection, nested placeholder resolution, and submission routing—all while maintaining zOS's pure declarative paradigm.

**Key Value**: Define forms once in YAML, get automatic validation, mode-agnostic rendering, and seamless submission handling across Terminal and GUI environments.

---

## Architecture

### 5-Tier Pattern

```
Tier 5: Package Root (__init__.py)                    [88 lines]
         ↓ Exposes: zDialog class, handle_zDialog function
Tier 4: Facade (zDialog.py)                           [637 lines]
         ↓ Main API: handle(zHorizontal, context)
Tier 3: Package Aggregator (dialog_modules/__init__.py)
         ↓ Exposes: create_dialog_context, inject_placeholders, handle_submit
Tier 2: Submit Handler (dialog_submit.py)             [465 lines]
         ↓ Dict-based submission via zDispatch
Tier 1: Foundation (dialog_context.py)                [350 lines]
         ↓ Context creation + 5 placeholder types
```

**Total**: ~1,540 lines across 5 files

### Architecture Position
- **Layer 1** subsystem (initializes after zConfig, zComm, zDisplay, zParser, zLoader, zFunc)
- **Initialization Order**: Position 8
- **Dependencies**: zDisplay (rendering), zData (validation), zDispatch (submission), zComm (WebSocket)

---

## Key Features

### 1. Auto-Validation (v1.5.4+)
- Automatically validates form data against zSchema models
- Uses `DataValidator` from zData subsystem
- Triggers when model starts with `@` (e.g., `@.zSchema.users`)
- Displays validation errors in both Terminal and Bifrost modes
- Prevents onSubmit execution on validation failure

### 2. Mode-Agnostic Rendering
- **Terminal Mode**: Interactive input prompts via zDisplay
- **Bifrost Mode**: Pre-provided data from WebSocket context
- Single codebase works in both environments
- Automatic mode detection via `SESSION_KEY_ZMODE`

### 3. WebSocket Support (Bifrost)
- Accepts pre-provided form data from WebSocket context
- Broadcasts validation errors via `comm.websocket.broadcast()`
- Real-time form validation in GUI applications
- Event format: `{"event": "validation_error", "table": ..., "errors": ...}`

### 4. Placeholder Injection (5 Types)
- **Full zConv**: `"zConv"` → Returns entire form data dict
- **Dot Notation**: `"zConv.username"` → Returns field value
- **Bracket Single**: `"zConv['email']"` → Returns field value
- **Bracket Double**: `"zConv[\"email\"]"` → Returns field value
- **Embedded**: `"WHERE id = zConv.user_id"` → Replaces within string

### 5. Pure Declarative Paradigm (v1.5.4+)
- **Dict-based submissions only** via zDispatch
- String-based submissions removed for architectural purity
- All forms defined in YAML with structured dicts
- Enables IDE validation, autocomplete, and static analysis

### 6. Smart Formatting
- **Numeric values**: No quotes (`WHERE id = 123`)
- **String values**: With quotes (`WHERE name = 'Alice'`)
- **Recursive resolution**: Deep nested dict/list placeholder injection
- **Regex matching**: Finds all `zConv.*` occurrences in strings

---

## Public API

### Main Entry Point

**zDialog.handle(zHorizontal, context=None)**

```python
# Initialize (done by zOS.py)
dialog = zDialog(zcli_instance)

# Define form
form_spec = {
    "zDialog": {
        "model": "@.zSchema.users",
        "fields": [
            {"name": "username", "type": "text"},
            {"name": "email", "type": "text"}
        ],
        "onSubmit": {
            "zCRUD": {
                "action": "create",
                "data": "zConv"  # Injects entire form data
            }
        }
    }
}

# Handle dialog (renders, collects, validates, submits)
result = dialog.handle(form_spec)
```

**Parameters**:
- `zHorizontal` (Dict): Dialog specification with model, fields, onSubmit
- `context` (Dict, optional): Execution context (WebSocket data, etc.)

**Returns**:
- `None`: Validation failed (onSubmit not executed)
- `Any`: Result from onSubmit execution (if provided)
- `Dict`: Collected form data (zConv) if no onSubmit

**Workflow**:
1. Parse zHorizontal → Extract model, fields, onSubmit
2. Create dialog context → `create_dialog_context()`
3. Collect form data → Terminal (zDisplay.zDialog) or Bifrost (pre-provided)
4. Auto-validate → Against zSchema if model starts with `@`
5. Execute onSubmit → Via handle_submit() if provided
6. Return result or zConv

### Backward Compatibility

**handle_zDialog(zHorizontal, walker=None, zcli=None, context=None)**

Legacy function for older code. Wraps zDialog class for single-call operations.

```python
# Legacy approach
result = handle_zDialog(form_spec, zcli=zcli_instance)

# Modern approach (preferred)
result = zcli.zdialog.handle(form_spec)
```

---

## Usage Examples

### Example 1: Terminal Mode with Auto-Validation

```yaml
# zUI.user_registration.yaml
zVaF:
  register:
    zDialog:
      model: "@.zSchema.users"
      fields:
        - name: username
          type: text
        - name: email
          type: text
        - name: password
          type: password
      onSubmit:
        zCRUD:
          action: create
          data: zConv  # Injects {"username": ..., "email": ..., "password": ...}
```

**Flow**:
1. Renders form in Terminal
2. Collects username, email, password
3. Auto-validates against `@.zSchema.users`
4. On success: Creates user record via zCRUD
5. On failure: Displays validation errors, returns None

### Example 2: Bifrost Mode with Pre-Provided Data

```python
# WebSocket sends form data
context = {
    "websocket_data": {
        "data": {"username": "alice", "email": "alice@example.com"}
    }
}

# Handle dialog (skips rendering, uses pre-provided data)
result = zcli.zdialog.handle(form_spec, context=context)
# Auto-validates, broadcasts errors via WebSocket if needed
```

### Example 3: Data Collection Only (No onSubmit)

```yaml
zVaF:
  collect_info:
    zDialog:
      model: "@.zSchema.users"
      fields:
        - name: username
          type: text
        - name: age
          type: number
      # No onSubmit - just collect and validate
```

**Returns**: `{"username": "testuser", "age": 25}` (after validation)

### Example 4: Complex Placeholder Injection

```yaml
zVaF:
  create_order:
    zDialog:
      model: "@.zSchema.orders"
      fields:
        - name: customer_id
          type: number
        - name: product_id
          type: number
        - name: quantity
          type: number
      onSubmit:
        zData:
          query: "INSERT INTO orders (customer_id, product_id, quantity, total) VALUES (zConv.customer_id, zConv.product_id, zConv.quantity, zConv.quantity * 10)"
          # Embedded placeholders with smart formatting:
          # - customer_id: 123 (numeric, no quotes)
          # - product_id: 456 (numeric, no quotes)
          # - quantity: 5 (numeric, no quotes)
```

---

## Placeholder Resolution Details

### Full zConv
```yaml
onSubmit:
  zCRUD:
    action: create
    data: zConv  # Entire form data: {"username": "alice", "email": "alice@example.com"}
```

### Dot Notation
```yaml
onSubmit:
  zFunc: "&user_service.create(zConv.username, zConv.email)"
  # Resolves to: create("alice", "alice@example.com")
```

### Embedded Placeholders
```yaml
onSubmit:
  zData:
    query: "SELECT * FROM users WHERE id = zConv.user_id AND status = zConv.status"
    # Numeric: WHERE id = 42 (no quotes)
    # String: AND status = 'active' (with quotes)
```

### Nested Structures
```yaml
onSubmit:
  zCRUD:
    action: create
    data:
      user:
        name: zConv.username
        email: zConv.email
      metadata:
        source: form
        timestamp: now()
  # Resolves to:
  # data:
  #   user:
  #     name: "alice"
  #     email: "alice@example.com"
  #   metadata:
  #     source: "form"
  #     timestamp: "now()"
```

---

## Auto-Validation Workflow

### When Validation Triggers

Auto-validation **only** triggers when:
- `model` field is present
- `model` is a string
- `model` starts with `@` (schema reference)

Example: `model: "@.zSchema.users"` → **Validation enabled**  
Example: `model: "users"` → **Validation skipped**

### Validation Process

1. **Load Schema**: `zcli.loader.handle(model)` → Load YAML schema
2. **Extract Table**: `"@.zSchema.users"` → Extract `"users"`
3. **Create Validator**: `DataValidator(schema_dict, logger)`
4. **Validate Data**: `validator.validate_insert(table_name, zConv)`
5. **On Success**: Proceed to onSubmit (if provided)
6. **On Failure**:
   - Display errors via `display_validation_errors()`
   - Broadcast errors via WebSocket (Bifrost mode)
   - Return `None` (prevents onSubmit execution)

### Validation Error Display

**Terminal Mode**:
```
[ERROR] Validation failed for table 'users':
  - username: Field is required
  - email: Invalid email format
```

**Bifrost Mode** (WebSocket broadcast):
```json
{
  "event": "validation_error",
  "table": "users",
  "errors": {
    "username": "Field is required",
    "email": "Invalid email format"
  },
  "fields": ["username", "email"]
}
```

---

## Integration Points

### With zDisplay
- **Form Rendering**: `display.zDialog(zContext, zcli, walker)`
- **Status Messages**: `display.zDeclare(message, color, indent, style)`
- **Validation Errors**: `display_validation_errors()` (from zData)

### With zData
- **Auto-Validation**: `DataValidator(schema_dict, logger)`
- **Validation Execution**: `validator.validate_insert(table_name, data)`
- **Error Display**: `display_validation_errors(table_name, errors, ops)`

### With zLoader
- **Schema Loading**: `loader.handle(model)` → Load YAML schema from zPath

### With zDispatch
- **Dict Submissions**: `handle_zDispatch(command, submit_dict, zcli, walker)`
- **Command Routing**: Routes zCRUD, zData, zFunc commands

### With zComm
- **WebSocket Broadcasting**: `comm.websocket.broadcast(event_dict)`
- **Real-time Validation**: Validation errors sent to GUI clients

### With zParser
- **zPath Resolution**: Resolves `@.zSchema.users` to file path
- **Expression Parsing**: Parses placeholder expressions

---

## Best Practices

### Form Design
1. **Use zSchema Models**: Always use `@.zSchema.*` for auto-validation
2. **Minimal Fields**: Only collect necessary data
3. **Clear Field Names**: Use descriptive, lowercase field names
4. **Type Hints**: Specify field types (text, number, password, etc.)

### Placeholder Usage
1. **Dot Notation First**: Use `zConv.field` for simple access
2. **Bracket for Special**: Use brackets only for fields with special characters
3. **Full zConv for CRUD**: Use `data: zConv` for create/update operations
4. **Embedded for SQL**: Use embedded placeholders in SQL queries

### Submission Handling
1. **Dict-based Only**: Use dict-based submissions (string-based removed)
2. **zCRUD for Database**: Use zCRUD for create/update/delete operations
3. **zData for Queries**: Use zData for custom SQL queries
4. **zFunc for Logic**: Use zFunc for custom business logic (via zDispatch)

### Error Handling
1. **Rely on Auto-Validation**: Let zDialog validate against zSchema
2. **Check Return Values**: `None` return means validation failed
3. **Handle Exceptions**: Wrap dialog calls in try-catch for robustness
4. **Log Validation Failures**: Log for auditing and debugging

### Security
1. **Schema Validation**: Always use zSchema for input validation
2. **No Direct SQL**: Use placeholder injection, not string concatenation
3. **Sanitize Inputs**: zDialog sanitizes via zData validation
4. **Audit Submissions**: Log all form submissions for security audits

---

## Common Patterns

### User Registration
```yaml
register_user:
  zDialog:
    model: "@.zSchema.users"
    fields:
      - {name: username, type: text}
      - {name: email, type: text}
      - {name: password, type: password}
    onSubmit:
      zCRUD:
        action: create
        data: zConv
```

### Data Update
```yaml
update_profile:
  zDialog:
    model: "@.zSchema.users"
    fields:
      - {name: email, type: text}
      - {name: age, type: number}
    onSubmit:
      zCRUD:
        action: update
        where: {id: zConv.user_id}
        data:
          email: zConv.email
          age: zConv.age
```

### Search Query
```yaml
search_users:
  zDialog:
    model: "@.zSchema.users"
    fields:
      - {name: search_term, type: text}
    onSubmit:
      zData:
        query: "SELECT * FROM users WHERE username LIKE '%zConv.search_term%' OR email LIKE '%zConv.search_term%'"
```

---

## Testing

### Test Suite
**Location**: `zTestRunner/zUI.zDialog_tests.yaml` + `zTestRunner/plugins/zdialog_tests.py`

**Coverage**: 85 tests across 9 categories
- A. Facade - Initialization & Main API (8 tests)
- B. Context Creation (10 tests)
- C. Placeholder Injection - 5 types (15 tests)
- D. Submission Handling - Dict-based (10 tests)
- E. Auto-Validation - zData Integration (12 tests)
- F. Mode Handling - Terminal vs. Bifrost (8 tests)
- G. WebSocket Support (6 tests)
- H. Error Handling (6 tests)
- I. Integration Tests (10 tests)

**Pass Rate**: 100% (85/85 tests passing)

### Run Tests
```bash
zolo ztests  # Select "zDialog"
```

---

## Migration from v1.4.0 to v1.5.4+

### Removed: String-Based Submissions
**Old (v1.4.0)**:
```yaml
onSubmit: "zFunc(@auth.register, zConv.username, zConv.email)"
```

**New (v1.5.4+)**:
```yaml
onSubmit:
  zDispatch:
    zFunc: "&auth.register(zConv.username, zConv.email)"
```

**Rationale**: Pure declarative paradigm, better IDE support, schema validation

### Added: Auto-Validation
**New Feature** (v1.5.4+):
- Forms automatically validate against zSchema models
- Validation errors displayed in both Terminal and Bifrost modes
- Prevents onSubmit execution on validation failure

### Added: WebSocket Support
**New Feature** (v1.5.0+):
- Pre-provided data from WebSocket context
- Real-time validation error broadcasting
- Seamless Bifrost (GUI) integration

### Updated: Display Methods
**Old**:
```python
walker.display.handle({"event": "sysmsg", "label": "zDialog", ...})
```

**New**:
```python
walker.display.zDeclare("zDialog", color="ZDIALOG", indent=1, style="single")
```

---

## Technical Debt

### zData Direct Imports
**Current** (documented as temporary):
```python
from zOS.subsystems.zData.zData_modules.shared.validator import DataValidator
from zOS.subsystems.zData.zData_modules.shared.operations.helpers import display_validation_errors
```

**Future** (when zData is refactored):
```python
validator = zcli.zdata.create_validator(schema_dict)
zcli.zdata.display_validation_errors(table_name, errors)
```

### ValidationOps Mock Class
**Current**: Mock class created inside `zDialog.handle()` method  
**Future**: Extract to module-level helper or integrate with refactored zData

**Note**: Both items documented in code with TODO comments, will be addressed when zData subsystem is modernized.

---

## Version History

- **v1.5.4+**: String-based submission removal + Industry-grade upgrade
  - REMOVED: String-based onSubmit (zFunc integration)
  - Enhanced: Comprehensive documentation (400+ lines)
  - Added: 100% type hint coverage
  - Added: 28 module-level constants
  - Added: Session key modernization (SESSION_KEY_ZMODE)
  - Documented: Technical debt (zData direct imports)
- **v1.5.2**: Auto-validation integration with zData
- **v1.5.0**: WebSocket support for Bifrost mode
- **v1.4.0**: Initial implementation

---

**Last Updated**: 2025-11-08  
**Version**: 1.5.4+  
**Status**: Production Ready ✅  
**Test Coverage**: 85 tests (100% pass rate)
