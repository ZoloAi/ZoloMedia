# zWalker Guide

> **YAML-Driven UI Orchestration**  
> Turn simple YAML files into interactive CLI applications with menus, wizards, and workflows.

---

## What It Does

**zWalker** is the orchestration engine that brings all zOS subsystems together into navigable UI experiences:

- ✅ **YAML-based menus** - Define interactive UIs without code
- ✅ **Breadcrumb navigation** - Automatic back/forward tracking
- ✅ **Multi-step wizards** - Chain actions into workflows
- ✅ **Cross-file linking** - Navigate between menu files
- ✅ **Full subsystem access** - Data, display, auth, functions, dialogs
- ✅ **Dual-mode support** - Works in Terminal and zBifrost (web)

**Status:** ✅ Production-ready (100% test coverage, 88/88 tests passing)

---

## Why It Matters

### For Developers
- **Zero boilerplate** - Write YAML, get interactive menus
- **Extends zWizard** - Inherits workflow capabilities
- **Declarative** - UI defined in data, not code
- **Type-safe** - Full integration with typed subsystems
- **Industry-grade** - 88 comprehensive tests, 12 test categories

### For Executives
- **Rapid prototyping** - Build CLIs in minutes, not days
- **Non-technical friendly** - Business analysts can define UI flows
- **Maintainable** - UI changes don't require code changes
- **Production-ready** - 88 tests ensure reliability
- **Web-ready** - Same YAML works in Terminal and browser (zBifrost)

---

## Architecture (Simple View)

```
zWalker (Layer 3 - Orchestrator)
│
├── Extends zWizard → Multi-step workflows
│
├── Integrates 11 Subsystems:
│   ├── zDisplay   → UI rendering
│   ├── zNavigation → Menus & breadcrumbs
│   ├── zDispatch  → Command routing
│   ├── zLoader    → YAML file loading
│   ├── zData      → Database operations
│   ├── zDialog    → Forms & input
│   ├── zFunc      → Plugin execution
│   ├── zAuth      → Authentication
│   ├── zOpen      → File/URL opening
│   ├── zShell     → REPL integration
│   └── zUtils     → Utilities
│
└── Core Features:
    ├── run()           → Main entry point
    ├── zBlock_loop()   → Menu navigation
    └── walker_dispatch() → Breadcrumb-aware dispatch
```

**Test Coverage:** 88 tests across 12 categories = 100% coverage

---

## How It Works

### 1. Define UI in YAML

Create a menu file (`zUI.my_app.yaml`):

```yaml
zVaF:
  ~Root*: ["View Data", "Add Record", "Settings", "stop"]
  
  "View Data":
    zData:
      action: read
      table: users
      limit: 10
  
  "Add Record":
    zWizard:
      collect_input:
        zDialog:
          model: "UserData"
          fields: ["name", "email"]
      save_data:
        zData:
          action: create
          table: users
          data:
            name: "zHat[name]"
            email: "zHat[email]"
  
  "Settings":
    ~Menu*: ["Change Theme", "View Config", "zBack"]
    
    "Change Theme":
      zDisplay:
        event: info
        content: "Theme settings..."
```

### 2. Run Your App

```python
from zOS import zOS

# Initialize
zcli = zOS()

# Configure walker
zcli.zspark_obj['zVaFile'] = '@.zUI.my_app'
zcli.zspark_obj['zBlock'] = 'zVaF'

# Run
result = zcli.walker.run()
```

### 3. Navigate Automatically

Walker handles:
- Menu display via `~Root*` and `~Menu*` anchors
- User selection and command dispatch
- Breadcrumb tracking (zCrumbs)
- Back navigation (`zBack`)
- Exit handling (`stop`)

---

## YAML Syntax Reference

### Menu Anchors

```yaml
~Root*: ["Option 1", "Option 2", "stop"]  # Root menu (required)
~Menu*: ["Sub Option", "zBack"]           # Sub-menu
```

### Navigation Types

**1. Direct Actions**
```yaml
"Option Name":
  zDisplay:
    event: success
    content: "Action executed!"
```

**2. Delta Links (Same File)**
```yaml
~Root*: ["Main", "$SubMenu", "stop"]

SubMenu:
  ~Root*: ["Options", "zBack"]
```

**3. Cross-File Delta Links**
```yaml
# In file_a.yaml
~Root*: ["$OtherFile.OtherBlock", "stop"]

# In file_b.yaml (OtherFile)
OtherBlock:
  ~Root*: ["Options", "zBack"]
```

**4. Multi-Step Wizards**
```yaml
"Workflow":
  zWizard:
    step1:
      zDialog:
        model: "Input"
    step2:
      zFunc: "&plugin.process()"
    step3:
      zDisplay:
        event: json
        data: "zHat"
```

### Reserved Keywords

- **`zBack`** - Return to previous menu
- **`stop`** - Exit walker
- **`zHat`** - Access wizard results
- **`~Root*`** - Root menu anchor
- **`~Menu*`** - Sub-menu anchor
- **`$`** - Delta link prefix

---

## Common Patterns

### Pattern 1: CRUD Menu

```yaml
ManageUsers:
  ~Root*: ["View All", "Add User", "Edit User", "Delete User", "zBack"]
  
  "View All":
    zData:
      action: read
      table: users
  
  "Add User":
    zWizard:
      collect:
        zDialog:
          model: "User"
          fields: ["name", "email"]
      save:
        zData:
          action: create
          table: users
          data: "zHat"
```

### Pattern 2: Plugin Menu

```yaml
PluginActions:
  ~Root*: ["Generate ID", "Hash Password", "zBack"]
  
  "Generate ID":
    zFunc: "&id_generator.composite_id('USER', 2024)"
  
  "Hash Password":
    zWizard:
      input:
        zDialog:
          model: "Password"
          fields: ["password"]
      hash:
        zFunc: "&security.hash_password(zHat[password])"
```

### Pattern 3: Nested Navigation

```yaml
MainMenu:
  ~Root*: ["Features", "Admin", "stop"]
  
  "Features":
    ~Menu*: ["Feature A", "Feature B", "zBack"]
    
    "Feature A":
      ~Menu*: ["Sub Feature 1", "Sub Feature 2", "zBack"]
      
      "Sub Feature 1":
        zDisplay:
          event: success
          content: "Deep navigation works!"
```

---

## API Reference

### Main Methods

#### `run()`
Execute walker with configured zVaFile and zBlock.

```python
zcli.zspark_obj['zVaFile'] = '@.zUI.my_menu'
zcli.zspark_obj['zBlock'] = 'zVaF'
result = zcli.walker.run()
```

#### `zBlock_loop(block_dict, keys=None, key=None)`
Navigate through a specific menu block.

```python
ui_data = zcli.loader.handle("@.zUI.my_menu")
result = zcli.walker.zBlock_loop(
    ui_data["MenuBlock"],
    zBlock_keys=["option1", "option2"],
    zKey="option1"
)
```

### Session Management

Walker automatically manages session state:

```python
# Walker sets:
zcli.session["zMode"] = "Walker"
zcli.session["zCrumbs"] = {}  # Breadcrumb tracking
zcli.session["zBlock"] = "current_block"

# Access breadcrumbs:
breadcrumbs = zcli.session["zCrumbs"]
# Example: {"MainMenu": ["Features"], "Features": ["Feature A"]}
```

### Navigation Callbacks

Walker provides built-in callbacks for navigation events:

```python
navigation_callbacks = {
    'on_back': handle_zback,    # Breadcrumb-aware back
    'on_stop': handle_stop,     # Clean exit
    'on_exit': handle_exit,     # Graceful return
    'on_error': handle_error    # Error handling
}
```

---

## Integration Examples

### With zData

```yaml
"Database Operations":
  zWizard:
    load_schema:
      zData:
        action: load
        schema: "@.schemas.users"
    query:
      zData:
        action: read
        table: users
        limit: 10
    display:
      zDisplay:
        event: table
        data: "zHat"
```

### With zAuth

```yaml
"Secure Section":
  zWizard:
    authenticate:
      zAuth:
        action: login
        provider: "local"
    check_role:
      zAuth:
        action: check_role
        role: "admin"
    show_admin:
      zDisplay:
        event: success
        content: "Admin access granted"
```

### With zShell

```yaml
"Enter Shell":
  zFunc: "@.zOS.subsystems.zShell.zShell.interactive()"

"Run Command":
  zShell:
    command: "ls -la"
```

---

## Testing

### Declarative Test Suite
**Location:** `zTestRunner/zUI.zWalker_tests.yaml`  
**Plugin:** `zTestRunner/plugins/zwalker_tests.py`  
**Total Tests:** 88 (100% passing)

### Test Categories (12)

| Category | Tests | Coverage |
|----------|-------|----------|
| A. Initialization & Core Setup | 5 | zWalker creation, zWizard inheritance, subsystems |
| B. Session Management | 8 | zMode, zBlock, zCrumbs, workspace tracking |
| C. Orchestration & Delegation | 10 | Pure orchestrator pattern, subsystem delegation |
| D. Dual-Mode Support | 8 | Terminal vs zBifrost, mode switching |
| E. Navigation Callbacks | 10 | on_back, on_exit, on_stop, on_error |
| F. Block Loop Execution | 10 | Menu display, breadcrumbs, dispatch |
| G. Integration - Display | 5 | zDeclare, colors, styles, mode-agnostic |
| H. Integration - Navigation | 5 | zCrumbs, zBack, zLink, breadcrumb stack |
| I. Integration - Dispatch | 5 | Command routing, modifiers, errors |
| J. Integration - Loader | 5 | VaFile loading, zPath resolution, cache |
| K. Error Handling | 10 | Missing files, invalid blocks, graceful recovery |
| L. Cross-Subsystem Integration | 7 | Full stack, plugins, data, auth, shell |

### Run Tests

```bash
# From zOS main menu
python main.py
# Select: zWalker

# Or direct via script
python main.py << 'EOF'
16
EOF
```

### Test Results

```
==========================================================================================
zWalker Comprehensive Test Suite - 88 Tests
==========================================================================================

A. Initialization & Core Setup (5 tests)
------------------------------------------------------------------------------------------
  [OK]  Init: Walker Initialization                        Walker initialized successfully
  [OK]  Extends: zWizard Inheritance                       Walker extends zWizard
  ...

[12 categories total]

==========================================================================================
SUMMARY: 88/88 passed (100.0%) | Errors: 0 | Warnings: 0
==========================================================================================
```

---

## Best Practices

### ✅ DO: Clear Menu Labels
```yaml
~Root*: ["Manage Users", "View Reports", "Settings", "stop"]
```

### ❌ DON'T: Vague Labels
```yaml
~Root*: ["opt1", "opt2", "opt3", "stop"]
```

---

### ✅ DO: Use Wizards for Multi-Step
```yaml
"Complete Workflow":
  zWizard:
    validate:
      zFunc: "&plugin.validate()"
    process:
      zData:
        action: create
    confirm:
      zDisplay:
        event: success
```

### ❌ DON'T: Chain Single Events
```yaml
"Complete Workflow":
  zData:  # Missing validation & confirmation
    action: create
```

---

### ✅ DO: Provide Back Navigation
```yaml
SubMenu:
  ~Root*: ["Option A", "Option B", "zBack"]
```

### ❌ DON'T: Create Dead Ends
```yaml
SubMenu:
  ~Root*: ["Option A", "Option B"]  # No way back!
```

---

### ✅ DO: Use Delta Links for Navigation
```yaml
~Root*: ["$Features.Root", "$Settings.Root", "stop"]
```

### ❌ DON'T: Duplicate Menu Definitions
```yaml
~Root*: ["Features", "Settings", "stop"]
# Then redefine Features menu everywhere
```

---

## Troubleshooting

### Issue: "zVaFile not found"
```python
# Solution: Use correct zPath
zcli.zspark_obj['zVaFile'] = '@.zUI.my_menu'  # Correct
zcli.zspark_obj['zVaFile'] = 'my_menu'        # Wrong
```

### Issue: "Root block not found"
```yaml
# Solution: Ensure ~Root* exists
zVaF:
  ~Root*: ["Options", "stop"]  # Required anchor
```

### Issue: Delta link not working
```yaml
# Solution: Match exact block name
~Root*: ["$Settings", "stop"]

Settings:  # Must match exactly (case-sensitive)
  ~Root*: ["Options", "zBack"]
```

### Issue: Breadcrumbs not tracking
```python
# Solution: Ensure navigation subsystem is available
if not hasattr(zcli, 'navigation'):
    raise RuntimeError("Navigation subsystem not initialized")
```

---

## Performance Tips

1. **Cache schemas** - Load once at start, reuse in wizards
2. **Limit queries** - Always specify `limit` in zData reads
3. **Plugin caching** - Use auto-discovery paths
4. **Shallow hierarchies** - Keep menu depth ≤ 5 levels

```python
# Clear caches when done
zcli.data.schema_cache.clear()
zcli.loader.cache.clear("plugin")
```

---

## Demo Files

### Comprehensive Demo
**File:** `@.zTestSuite.demos.zUI.walker_comprehensive`

Features:
- Data operations (SQLite)
- Wizard workflows
- Plugin integration
- Delta links
- Quick access functions

### Navigation Demo
**File:** `@.zTestSuite.demos.zUI.walker_navigation`

Features:
- Cross-file navigation
- Multiple blocks
- Complex workflows
- Analytics integration

---

## Summary

**zWalker** is the final orchestration layer that transforms YAML into interactive CLI applications:

- **Declarative** - Define UIs in YAML, not code
- **Navigable** - Automatic breadcrumbs and back navigation
- **Powerful** - Access to all 11 zOS subsystems
- **Flexible** - Works in Terminal and web (zBifrost)
- **Production-ready** - 88 tests, 100% coverage

**Use Cases:**
- Admin panels
- Data management tools
- Configuration wizards
- Interactive dashboards
- Multi-step workflows

**Test Coverage:** 88/88 tests passing (100%)  
**Status:** ✅ Production Ready  
**Version:** 1.5.4
