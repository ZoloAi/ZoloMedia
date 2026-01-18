# zWizard Guide

> **Multi-step workflow orchestration that just works™**  
> Execute sequences of actions with automatic result passing, transactions, and error handling.

---

## What It Does

**zWizard** orchestrates multi-step workflows with automatic context management:

- ✅ **Sequential execution** - Steps run in order with shared context
- ✅ **Result passing (zHat)** - Use previous step results in later steps
- ✅ **Transaction management** - Automatic BEGIN/COMMIT/ROLLBACK for data operations
- ✅ **Error handling** - Graceful recovery with rollback on failure
- ✅ **Navigation control** - Built-in zBack, exit, stop signals

**Status:** ✅ Production-ready (45/45 tests passing, 100% coverage)

---

## Why It Matters

### For Developers
- Zero boilerplate - define workflows in YAML, execution is automatic
- Result interpolation - `zHat[0]`, `zHat[step_name]`, `zHat.step_name` all work
- Transaction safety - multi-step data operations are atomic (all-or-nothing)
- Modular architecture - 6 focused modules with custom exceptions

### For Executives
- **Simplifies complex operations** - Multi-step workflows defined declaratively
- **Data integrity** - Automatic rollback prevents partial updates
- **Production-ready** - 45 comprehensive tests covering all scenarios
- **Powers two modes** - Shell canvas workflows AND Walker UI navigation

---

## Architecture (Simple View)

```
zWizard (Core Loop Engine + 6 Modules)
│
├── zWizard.py         → Main orchestrator (execute_loop, handle)
│
└── zWizard_modules/
    ├── wizard_hat.py           → WizardHat (triple-access results container)
    ├── wizard_interpolation.py → zHat[0] string interpolation
    ├── wizard_transactions.py  → BEGIN/COMMIT/ROLLBACK lifecycle
    ├── wizardzRBAC.py          → Permission checking (future)
    ├── wizard_exceptions.py    → Custom exception hierarchy
    └── __init__.py             → Module exports

Used By: zShell (canvas mode), zWalker (UI navigation), zData (transactions)
```

**Test Coverage:** 45 tests across 7 categories (A-to-G) = 100% coverage

---

## How It Works

### 1. WizardHat (Triple-Access Results)
Every workflow execution returns a `WizardHat` object that stores all step results:

```python
# Execute workflow
result = zcli.wizard.handle(workflow)

# Three ways to access results:
result[0]              # Numeric: First step result
result["step1"]        # Key-based: Step name
result.step1           # Attribute: Dot notation

# All three return the same value!
```

### 2. Workflow Execution
Define workflows in YAML, execute with one call:

```yaml
# Simple 2-step workflow
step1:
  zData:
    model: @.myschema
    action: insert
    tables: [users]
    options: {name: "Alice"}

step2:
  zDisplay:
    event: text
    message: "Inserted user"
```

```python
# Execute
result = zcli.wizard.handle(workflow_dict)
# Returns: WizardHat with 2 results
```

### 3. Result Interpolation (zHat)
Use previous step results in later steps:

```yaml
step1:
  zData:
    action: insert
    options: {name: "Alice"}
  # Returns: {"id": 123}

step2:
  zDisplay:
    event: text
    message: "Created user ID: zHat[0]['id']"
  # Displays: "Created user ID: 123"

step3:
  zData:
    action: update
    where: "id = zHat[step1]['id']"
  # Uses result from step1 by name
```

**Interpolation Rules:**
- Only string values are interpolated (not integers, booleans, etc.)
- Supports numeric (`zHat[0]`) and key-based (`zHat[step_name]`) access
- Invalid indices return `"None"`

### 4. Transaction Management
Add `_transaction: true` for atomic multi-step operations:

```yaml
_transaction: true

step1:
  zData:
    model: $mydb  # $ prefix triggers transaction
    action: insert
    tables: [users]

step2:
  zData:
    model: $mydb  # Reuses same connection
    action: insert
    tables: [users]

# On success → COMMIT
# On error → ROLLBACK (automatic)
```

**Transaction Lifecycle:**
1. **First step with `$alias`** → BEGIN transaction, create connection
2. **Subsequent steps** → Reuse same connection (efficient!)
3. **Success** → COMMIT transaction
4. **Error** → ROLLBACK transaction (automatic)
5. **Finally** → Clear schema_cache (cleanup)

---

## Common Use Cases

### Use Case 1: Multi-Step Data Insert
```yaml
_transaction: true

create_user:
  zData:
    model: $users_db
    action: insert
    tables: [users]
    options: {name: "Alice", email: "alice@example.com"}

create_profile:
  zData:
    model: $users_db
    action: insert
    tables: [profiles]
    options: {user_id: "zHat[0]['id']", bio: "Developer"}

# If either step fails → both rolled back (atomic)
```

### Use Case 2: Shell Canvas Mode
```bash
# 1. Start canvas mode
$ wizard --start

# 2. Add commands (converted to YAML workflow)
$ data insert users --name "Alice"
$ data insert users --name "Bob"

# 3. Execute as transaction
$ wizard --run --transaction

# 4. Stop canvas
$ wizard --stop
```

### Use Case 3: Walker UI Navigation
```python
# zWizard powers Walker's menu system
wizard = zWizard(walker=walker_instance)

menu_items = {
    "option1": {"zDisplay": {...}, "zLink": ...},
    "option2": {"zFunc": {...}},
}

# Automatic navigation with callbacks
result = wizard.execute_loop(
    menu_items,
    navigation_callbacks={
        "on_back": handle_back,
        "on_error": handle_error
    }
)
```

---

## Meta Keys (Underscore Prefix)

Keys starting with `_` are **configuration**, not execution steps:

```yaml
_transaction: true    # Enable transaction mode
_config: {...}       # Workflow configuration (future)
_timeout: 30         # Execution timeout (future)

# Only non-underscore keys execute as steps
step1: {...}
step2: {...}
```

---

## Error Handling

### Automatic Rollback
```yaml
_transaction: true

step1:
  zData: {action: insert, ...}  # Success

step2:
  zData: {action: invalid, ...}  # Error!

# Result: step1 is ROLLED BACK automatically
```

### Custom Error Callbacks (Walker Mode)
```python
def handle_error(error, key):
    """Called when step fails."""
    logger.error(f"Step '{key}' failed: {error}")
    display.error(f"Error: {error}")
    return "error"  # Navigation signal

wizard.execute_loop(
    items,
    navigation_callbacks={"on_error": handle_error}
)
```

---

## Best Practices

### ✅ DO: Use Transactions for Multi-Step Data
```yaml
_transaction: true
step1: {zData: {action: insert, ...}}
step2: {zData: {action: insert, ...}}
# All-or-nothing (atomic)
```

### ✅ DO: Leverage zHat for Dependent Steps
```yaml
step1: {zData: {action: insert, ...}}
step2: {zData: {where: "id = zHat[0]['id']"}}  # Use previous result
```

### ✅ DO: Use Consistent Schema for Transactions
```yaml
_transaction: true
step1: {zData: {model: $mydb, ...}}
step2: {zData: {model: $mydb, ...}}  # Same connection reused
```

### ❌ DON'T: Mix Schemas in Transaction
```yaml
_transaction: true
step1: {zData: {model: $db1, ...}}
step2: {zData: {model: $db2, ...}}  # Different connections!
```

### ❌ DON'T: Forget $ Prefix for Transactions
```yaml
_transaction: true
step1: {zData: {model: mydb, ...}}  # Missing $, no transaction!
```

---

## Integration with Other Subsystems

### zShell Integration
- **Canvas mode** - Wizard workflow execution
- **Step executor** - `zShell/executor_commands/wizard_step_executor.py`
- **Command buffering** - Commands converted to YAML workflow

### zWalker Integration
- **Menu navigation** - `zWizard.execute_loop()` powers UI
- **Navigation callbacks** - `on_back`, `on_error`, `on_continue`
- **Dispatch routing** - Steps routed via `zDispatch.handle()`

### zData Integration
- **Transaction support** - Schema cache shared with zWizard
- **Connection reuse** - `$alias` triggers single connection mode
- **Automatic rollback** - Failed operations roll back entire workflow

### zDisplay Integration
- **Visual feedback** - Step execution progress
- **Error display** - Formatted error messages
- **Result display** - WizardHat contents

---

## Exception Hierarchy

```python
zWizardError (base)
├── WizardInitializationError   # Missing zcli/walker, no session
├── WizardExecutionError         # Step execution failed
└── WizardRBACError              # Permission denied (future)

# Example usage:
try:
    wizard = zWizard()
except WizardInitializationError as e:
    print(f"Setup failed: {e}")
```

---

## Performance

### Connection Reuse
```yaml
_transaction: true
step1: {zData: {model: $db, ...}}  # CREATE connection
step2: {zData: {model: $db, ...}}  # REUSE connection (fast!)
step3: {zData: {model: $db, ...}}  # REUSE connection (fast!)
# Only 1 connection for all 3 steps
```

### Schema Cache Lifecycle
```python
# Workflow start
schema_cache = {}  # Empty

# First step with $db
schema_cache["db"] = handler  # Connection created

# Subsequent steps
handler = schema_cache["db"]  # Reused (no overhead!)

# Workflow end
schema_cache.clear()  # Cleanup
```

---

## Troubleshooting

### Issue: Transaction Not Working
```yaml
# ❌ Problem: Missing _transaction flag
step1: {zData: {model: $db, ...}}

# ✅ Solution: Add flag
_transaction: true
step1: {zData: {model: $db, ...}}
```

### Issue: zHat Interpolation Not Working
```yaml
# ❌ Problem: Non-string value (won't interpolate)
options: {id: zHat[0]}

# ✅ Solution: Use string context
where: "id = zHat[0]"  # Will interpolate
```

### Issue: Connection Not Reused
```yaml
# ❌ Problem: Missing $ prefix
_transaction: true
step1: {zData: {model: mydb, ...}}  # No $!

# ✅ Solution: Add $ prefix
_transaction: true
step1: {zData: {model: $mydb, ...}}  # Triggers transaction
```

---

## API Reference

### Python API
```python
# Execute workflow (Shell mode)
result = zcli.wizard.handle(workflow_dict)
# Returns: WizardHat instance

# Execute loop (Walker mode)
result = wizard.execute_loop(
    items_dict,
    dispatch_fn=custom_fn,         # Optional custom dispatcher
    navigation_callbacks={...},    # Optional callbacks
    context={...},                 # Optional context
    start_key="step3"              # Optional resume point
)
```

### WizardHat API
```python
# Create
zHat = WizardHat()

# Add results
zHat.add("step1", "result1")
zHat.add("step2", {"id": 123})

# Access (3 ways)
zHat[0]         # Numeric
zHat["step1"]   # Key-based
zHat.step1      # Attribute

# Utilities
len(zHat)           # 2
"step1" in zHat     # True
0 in zHat           # True
```

---

## Testing

**Test Suite:** 45 comprehensive tests
- ✅ WizardHat triple-access (8 tests)
- ✅ Initialization (5 tests)
- ✅ Workflow execution (10 tests)
- ✅ Interpolation (6 tests)
- ✅ Transactions (6 tests)
- ✅ Helper methods (5 tests)
- ✅ Exception handling (5 tests)

**Run Tests:**
```bash
# Declarative tests (45 tests)
$ zolo ztests
> Select: zWizard_test

# Unit tests (34 tests)
$ python3 -m unittest zTestSuite.zWizard_Test
```

---

## Quick Reference

### Workflow Structure
```yaml
_transaction: true           # Meta: Enable transactions
_config: {...}              # Meta: Configuration (future)

step1:                      # Step name
  zData: {...}             # Step action

step2:
  zFunc: {...}

step3:
  zDisplay: {...}
```

### Transaction Pattern
```yaml
_transaction: true

step1: {zData: {model: $db, action: insert, ...}}
step2: {zData: {model: $db, action: update, ...}}

# Success → COMMIT
# Error → ROLLBACK (automatic)
```

### Result Interpolation
```yaml
step1:
  zData: {action: insert, ...}  # Returns: {"id": 123}

step2:
  zDisplay:
    message: "ID is zHat[0]['id']"  # Interpolated
```

---

## See Also

- **zShell** - Canvas mode workflow execution
- **zWalker** - UI navigation and menu orchestration
- **zData** - Data operations with transaction support
- **zLoader** - Schema loading and cache management
- **zDispatch** - Command routing and step execution
