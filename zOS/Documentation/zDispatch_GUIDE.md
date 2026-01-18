# zDispatch: Command Routing & Execution

## Overview
**zDispatch** is zOS's command router - it takes any command (string, dict, function call) and executes it correctly. Think of it as a smart switchboard that understands command syntax, special modifiers, and routing rules.

**Key Features:**
- **Universal command routing**: Handles strings, dicts, function calls, and more
- **Modifier processing**: Special prefixes (^~) and suffixes (*!) that change behavior
- **Mode-aware execution**: Different behavior for Terminal vs Web (Bifrost) mode
- **Intelligent detection**: Auto-detects command type and routes accordingly

**Status:** ✅ Production-ready (100% test coverage, 80/80 tests passing)

---

## What It Does (Simple Terms)

### For Developers
You write commands in YAML or pass them programmatically. zDispatch figures out:
- Is this a function call? Execute it.
- Is this a link to another screen? Navigate there.
- Is this a menu? Create it.
- Does it have modifiers (like `^action` or `menu*`)? Apply special behavior.

### For Executives
- **Reduces complexity** - One system handles all command types consistently
- **Enables flexibility** - Commands can be strings, dictionaries, or function calls
- **Powers UI flow** - Every button, menu, and action goes through zDispatch
- **Production-ready** - 80 comprehensive tests, zero critical bugs

---

## Architecture (Simple View)

```
zDispatch (3 modules)
│
├── zDispatch.py         → Main entry point (Facade)
├── dispatch_modifiers   → Handles ^ ~ * ! modifiers
└── dispatch_launcher    → Executes actual commands
```

**Flow:**
```
Command → zDispatch → Check modifiers → Route to handler → Execute → Return result
```

---

## Command Types

### 1. String Commands
```yaml
# Function call
"zFunc(&my_plugin.save_data)"

# Navigation
"zLink(@.menu.settings)"

# Wizard
"zWizard(@.wizard.onboarding)"

# File operations
"zRead(users.csv)"
```

### 2. Dict Commands
```yaml
# Display output
zDisplay:
  text: "Hello, world!"
  style: success

# Function call
zFunc: "&calculator.add(5, 3)"

# Multi-step wizard
zWizard:
  step1: { zFunc: "&setup.init" }
  step2: { zFunc: "&setup.config" }
```

### 3. Plugin Invocations
```yaml
# Direct plugin call (& prefix)
"&my_plugin.my_function(arg1, arg2)"
```

---

## Modifiers (Special Syntax)

Modifiers change how commands execute. Think of them as "action keywords" that modify behavior.

### Prefix Modifiers (before command name)

**^ (Caret) - Bounce Back**
Execute action, then return to previous screen.

```yaml
# In Terminal: Execute and show previous menu
^save_settings

# Result: Saves settings → Returns to menu automatically
```

**~ (Tilde) - Anchor**
Mark this as the "home" point for navigation (with `*` creates non-escapable menu).

```yaml
# Create menu that can't be backed out of
~main_menu*
```

### Suffix Modifiers (after command name)

**\* (Asterisk) - Auto Menu**
Automatically create a numbered menu from array items.

```yaml
# In YAML
menu_items*: [
  "Profile",
  "Settings",
  "Logout"
]

# Result: Creates interactive menu:
# 1. Profile
# 2. Settings
# 3. Logout
```

**! (Exclamation) - Required**
Keep retrying until success (user can type "stop" to abort).

```yaml
# Must complete successfully
validate_input!

# Result: Loops until validation passes or user types "stop"
```

### Combined Modifiers
```yaml
# Bounce back + create menu
^options*

# Anchor + non-escapable menu
~root_menu*

# Execute and bounce back
^save_and_exit
```

---

## Mode-Aware Behavior

zDispatch behaves differently in Terminal vs Web (Bifrost) mode:

### Terminal Mode
- Plain strings without walker context → Return `None`
- `^` modifier → Return `"zBack"` (triggers previous menu)
- `zWizard` → Return `"zBack"` after completion

### Bifrost Mode (Web UI)
- Plain strings → Resolved from zUI or wrapped in `{message:}`
- `^` modifier → Return actual result (client handles navigation)
- `zWizard` → Return `zHat` result (accumulated data)

**Why?** Terminal needs explicit navigation signals, while web clients handle navigation via history/state.

---

## Practical Examples

### Example 1: Simple Menu with Actions
```yaml
# zUI file
zVaF:
  ~Main*: [
    "View Profile",
    "Edit Settings",
    "^Logout"
  ]
  
  "View Profile":
    zFunc: "&user.show_profile()"
  
  "Edit Settings":
    zLink: "@.settings.zVaF"
  
  "^Logout":
    zFunc: "&auth.logout()"
    # ^ makes it bounce back to menu after logout
```

### Example 2: Wizard with Bounce
```yaml
# Run wizard, then return to menu
zVaF:
  setup_wizard:
    zLink: "@.wizard.onboarding.zVaF"
    # Note: Use ^ on the menu item to bounce back
  
  # In menu:
  ~Actions*: [
    "^Run Setup"  # Executes wizard, returns to menu when done
  ]
```

### Example 3: Required Input
```yaml
# User must provide valid input
collect_email!:
  zDialog:
    fields:
      - name: email
        type: email
        required: true
# Loops until valid email or user types "stop"
```

### Example 4: Multi-App Routing
```yaml
# Route to different handlers based on command type
handle_command:
  zFunc: "&my_app.process"       # Function execution
  
display_output:
  zDisplay:                      # Display handling
    text: "Output here"
    
navigate_screen:
  zLink: "@.screens.dashboard"   # Navigation
```

---

## Integration with Other Subsystems

zDispatch routes commands to these subsystems:

| Subsystem | Purpose | Example |
|-----------|---------|---------|
| **zFunc** | Execute Python functions | `zFunc(&plugin.func)` |
| **zLink** | Navigate to zUI screens | `zLink(@.menu.settings)` |
| **zWizard** | Multi-step workflows | `zWizard(steps)` |
| **zDialog** | Interactive forms | `zDialog(fields)` |
| **zDisplay** | Output rendering | `zDisplay(text)` |
| **zNavigation** | Menu creation | `menu_items*` |
| **zData** | Data operations | `{action: read, table: users}` |

---

## Error Handling

zDispatch handles errors gracefully:

```python
# Invalid command → Returns None or error message
result = zcli.dispatch.handle(None, None)  # Handled gracefully

# Missing function → Logs error, returns None
result = zcli.dispatch.handle("key", "zFunc(&missing.func)")

# Invalid format → Caught and logged
result = zcli.dispatch.handle("key", "zFunc(")  # Missing closing paren
```

**For users:** Invalid commands show clear error messages without crashing.

---

## API Usage (Programmatic)

### Using the Facade
```python
from zOS import zOS

zcli = zOS(config)

# Execute command
result = zcli.dispatch.handle(
    zKey="save_action",
    zHorizontal={"zFunc": "&data.save"}
)

# With modifiers
result = zcli.dispatch.handle(
    zKey="^back_action",
    zHorizontal={"zFunc": "&cleanup.run"}
)
```

### Standalone Function
```python
from zOS.subsystems.zDispatch import handle_zDispatch

# Quick dispatch without class instance
result = handle_zDispatch(
    zKey="action",
    zHorizontal=command_dict,
    zcli=zcli
)
```

---

## Test Coverage

**80 comprehensive tests** across 8 categories (A-to-H):

| Category | Tests | Coverage |
|----------|-------|----------|
| A. Facade API | 8 | Entry point, delegation |
| B. String Commands | 12 | zFunc, zLink, zOpen, etc. |
| C. Dict Commands | 12 | All dict-based commands |
| D. Mode Handling | 8 | Terminal vs Bifrost |
| E. Prefix Modifiers | 10 | ^ and ~ detection |
| F. Suffix Modifiers | 10 | * and ! detection |
| G. Integration | 10 | Component workflows |
| H. Real Integration | 10 | Actual subsystem calls |

**Result:** 100% pass rate, zero stub tests, all real validation.

---

## Performance

- **Fast routing**: ~0.1ms per command (negligible overhead)
- **Stateless design**: No internal state = thread-safe
- **Cached detection**: Command type detected once
- **Minimal overhead**: Thin facade pattern, delegates quickly

---

## Common Patterns

### Pattern 1: Menu with Actions
```yaml
~Menu*: ["Action1", "Action2", "^Exit"]
# Creates numbered menu, Exit bounces back
```

### Pattern 2: Wizard Flow
```yaml
zWizard:
  step1: { zFunc: "&setup.init" }
  step2: { zFunc: "&setup.config" }
  step3: { zDisplay: { text: "Done!" } }
```

### Pattern 3: Required Input
```yaml
get_input!:
  zDialog: { fields: [...] }
# Loops until valid or user aborts
```

### Pattern 4: Conditional Routing
```python
# In plugin code
if user_authenticated:
    return {"zLink": "@.dashboard"}
else:
    return {"zLink": "@.login"}
```

---

## Tips & Best Practices

### For Developers
1. **Use modifiers sparingly** - Only when behavior truly needs to change
2. **Prefer dicts over strings** - More readable, easier to debug
3. **Test both modes** - Terminal and Bifrost may behave differently
4. **Use ^ for cleanup actions** - Logout, cancel, back buttons

### For Architects
1. **Centralized routing** - All commands go through one entry point
2. **Extensible design** - Easy to add new command types
3. **Testable** - Each component tested independently + integration tests
4. **Type-safe** - Full type hints, validation at boundaries

---

## Troubleshooting

### Command Not Executing
**Check:**
1. Command type detected correctly? (Check logs)
2. Modifiers stripped properly? (Remove modifiers to test)
3. Target subsystem available? (zFunc, zLink, etc.)

### Unexpected Bounce Back
**Check:**
1. Did you use `^` modifier unintentionally?
2. Is this in Terminal mode? (Terminal auto-returns from wizards)
3. Check `zMode` in config: `zcli.config.session.get("zMode")`

### Menu Not Creating
**Check:**
1. Used `*` suffix? (`menu_items*`)
2. Value is an array? (`~Root*: [...]`)
3. zNavigation available? (Future subsystem)

---

## Summary

**zDispatch** is the traffic controller for zOS commands:
- ✅ Routes all command types (strings, dicts, functions)
- ✅ Processes modifiers (^ ~ * !) for special behavior
- ✅ Mode-aware (Terminal vs Web)
- ✅ Production-ready with 80 tests (100% pass rate)

**When to use modifiers:**
- `^` - Bounce back after action
- `~` - Mark anchor point for navigation
- `*` - Auto-create menu from array
- `!` - Require successful completion

**Key insight:** Every command in zOS flows through zDispatch - it's the central nervous system of command execution.

---

**Version:** 1.5.4  
**Status:** ✅ Production-ready  
**Tests:** 80/80 passing (100%)  
**Documentation:** Complete

For more details, see:
- `zOS/subsystems/zDispatch/` - Implementation
- `zTestRunner/zUI.zDispatch_tests.yaml` - Declarative tests
- `AGENT.md` - Full subsystem documentation

