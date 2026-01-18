# zShell Guide

**Interactive Command Center & REPL for zOS**

---

## Overview

`zShell` is zOS's interactive shell subsystem providing a command-line interface (REPL) for executing commands, managing workflows, and interacting with all zOS subsystems. Think of it as your text-based control panel.

**Key Features:**
- **18+ Commands** - Terminal, data, config, auth, and more
- **Wizard Canvas Mode** - Multi-step workflow orchestration
- **Command History** - Persistent history with search
- **zPath Support** - Navigate using zOS path syntax
- **Mode-Agnostic** - Works in Terminal and Bifrost modes
- **Cross-Subsystem** - Direct access to all zOS features

---

## Quick Start

### Starting the Shell

```bash
# Direct entry point (recommended)
zShell

# Or from zOS menu
zolo
# Select "Enter zShell"
```

### First Commands

```bash
# Get help
> help

# Check your location
> where

# List files
> ls

# Execute a function
> func &my_plugin.my_function()

# Exit shell
> exit
```

---

## Command Reference

### Terminal Commands (6)

#### `where`
Shows current workspace and zPath location.

```bash
> where
Workspace: /Users/yourname/Projects/my_project
zPath: @.Projects.my_project
```

#### `cd` / `pwd`
Change directory and print working directory.

```bash
> cd @.zTestSuite.demos    # Change to demos folder
> cd ..                    # Go up one level
> cd ~                     # Go to home
> pwd                      # Show current directory
```

#### `ls`
List directory contents.

```bash
> ls                       # List current directory
> ls @.zTestSuite.demos    # List specific path
> ls -l                    # Detailed listing (if supported)
```

#### `help`
Show available commands and usage.

```bash
> help                     # Show all commands
> help data                # Help for specific command (if supported)
```

#### `shortcut`
Manage zVars (user variables) and file shortcuts.

```bash
# Create zVar
> shortcut myvar="test_value"

# List zVars
> shortcut

# Use zVar in commands
> echo $myvar

# Create file shortcut (interactive)
> shortcut cache
# Select from cached files
```

---

### zLoader Commands (3)

#### `load`
Load resources (schemas, configs, plugins).

```bash
# Load a schema
> load @.zTestSuite.demos.zSchema.sqlite_demo

# Load and cache with alias (deprecated pattern)
# Note: Use direct zPath instead
> load @.zSchema.myschema
```

#### `data`
Database operations (CRUD).

```bash
# Load schema and read data
> data --model @.zSchema.users read users

# Insert data
> data --model @.zSchema.users insert users --fields name,age --values "Alice",30

# Update data
> data --model @.zSchema.users update users --fields age --values 31 --where "name='Alice'"

# Delete data
> data --model @.zSchema.users delete users --where "age < 18"
```

**Usage Pattern:**
```bash
data [--model ZPATH] <action> <table> [options]
```

**Actions:** `read`, `insert`, `update`, `delete`, `list` (tables)

#### `plugin`
Plugin management.

```bash
# List loaded plugins
> plugin list

# Load plugin
> plugin load @.plugins.my_plugin

# Call plugin function (use func command instead)
> plugin exec my_plugin.my_function
```

---

### Integration Commands (10)

#### `auth`
Authentication commands.

```bash
# Check auth status
> auth status

# Login (prompts for credentials)
> auth login

# Logout
> auth logout
```

#### `comm`
Communication services status.

```bash
# Check service status
> comm status

# Additional comm operations available
> comm start
> comm stop
```

#### `config`
Configuration management.

```bash
# Get config value
> config get my_key

# Set config value
> config set my_key my_value

# List all config
> config list

# Remove config value
> config remove my_key
```

#### `func`
Function execution.

```bash
# Call a plugin function
> func &my_plugin.my_function()

# With arguments
> func &my_plugin.calculate(10, 20)

# With context injection
> func &my_plugin.process(zContext)
```

#### `open`
Open files and URLs.

```bash
# Open file
> open @.README.md

# Open URL
> open https://example.com

# Open with specific app (if supported)
> open myfile.pdf
```

#### `session`
Session information.

```bash
# Show session info
> session

# Display includes:
# - Current workspace
# - Loaded zVaFile
# - Active zVars
# - Session keys
```

---

### Advanced Commands (2)

#### `walker`
Navigate to zWalker menu mode.

```bash
> walker
# Launches Walker UI menu system
```

#### `wizard_step` / `wizard`
Wizard canvas mode for multi-step workflows.

```bash
# Start canvas mode
> wizard_step start

# Add steps
> wizard_step step1: config set key1 value1
> wizard_step step2: config set key2 value2

# Show buffer
> wizard_step show

# Run workflow
> wizard_step run

# Clear buffer
> wizard_step clear

# Stop canvas mode
> wizard_step stop
```

---

## Wizard Canvas Mode

### What is Wizard Canvas?

Wizard canvas mode lets you **build multi-step workflows** before executing them. All steps run together in a transaction - if one fails, all changes are rolled back.

### Basic Workflow

```bash
# 1. Start canvas mode
> wizard_step start
📝 Wizard Canvas Active

# 2. Add steps (won't execute yet)
> wizard_step step1: config set test_key test_value
> wizard_step step2: data --model $db insert users --fields name --values "Alice"

# 3. Review your workflow
> wizard_step show
Wizard Buffer (2 steps):
  step1: config set test_key test_value
  step2: data --model $db insert users --fields name --values "Alice"

# 4. Execute all steps
> wizard_step run
✅ Workflow executed (2 steps)

# 5. Exit canvas mode
> wizard_step stop
```

### YAML Format Support

```bash
> wizard_step start
> wizard_step zWizard:
> wizard_step   step1: config get my_key
> wizard_step   step2: config set my_key new_value
> wizard_step run
```

### Transaction Support

```bash
> wizard_step start
> wizard_step _transaction: true
> wizard_step step1: data insert users ...
> wizard_step step2: data insert posts ...
> wizard_step run
# Both inserts succeed or both are rolled back
```

---

## Common Patterns

### Pattern 1: Navigate and Explore

```bash
# Check location
> where

# List files
> ls

# Change directory
> cd @.zTestSuite.demos

# List again
> ls
```

### Pattern 2: Data Operations

```bash
# Load schema
> load @.zSchema.mydb

# Read data
> data --model @.zSchema.mydb read users

# Insert data
> data --model @.zSchema.mydb insert users --fields name,age --values "Bob",25

# Update data
> data --model @.zSchema.mydb update users --fields age --values 26 --where "name='Bob'"
```

### Pattern 3: Multi-Step Workflow

```bash
# Start wizard canvas
> wizard_step start

# Add multiple operations
> wizard_step step1: data insert users --model $db --fields name --values "Alice"
> wizard_step step2: data insert posts --model $db --fields author --values "Alice"

# Execute together
> wizard_step run

# Exit canvas
> wizard_step stop
```

### Pattern 4: Config Management

```bash
# Set multiple values
> config set db_host localhost
> config set db_port 5432
> config set db_name myapp

# Check values
> config list

# Use in other commands
> config get db_host
```

### Pattern 5: Function Calls

```bash
# Load plugin
> plugin load @.plugins.my_utils

# Call function
> func &my_utils.process_data()

# With arguments
> func &my_utils.calculate(10, 20)
```

---

## Best Practices

### 1. Use `where` and `ls` Frequently

```bash
# Always know where you are
> where
> ls

# Before running important commands
> where
> data delete users --model $db --where "age < 18"
```

### 2. Use Wizard Canvas for Critical Operations

```bash
# ✅ Good: Multi-step operations in wizard mode
> wizard_step start
> wizard_step _transaction: true
> wizard_step step1: data insert users ...
> wizard_step step2: data insert profiles ...
> wizard_step run

# ❌ Avoid: Running critical operations separately
> data insert users ...
> data insert profiles ...  # If this fails, user has no profile!
```

### 3. Use zVars for Repeated Values

```bash
# Create shortcuts for common paths
> shortcut db="@.zSchema.production_db"

# Use in commands
> data --model $db read users
> data --model $db insert users --fields name --values "Alice"
```

### 4. Check Before You Delete

```bash
# ✅ Good: Check what you're deleting first
> data --model $db read users --where "age < 18"
# Review results
> data --model $db delete users --where "age < 18"

# ❌ Avoid: Deleting without checking
> data --model $db delete users --where "age < 18"
```

### 5. Use Direct zPaths

```bash
# ✅ Good: Direct zPath (modern approach)
> data --model @.zSchema.users read users

# ⚠️ Deprecated: Load with alias
> load @.zSchema.users --as db
> data --model $db read users
```

---

## Special Features

### Command History

zShell automatically saves command history to `~/.zolo/.zcli_history` (if readline is available).

**Features:**
- Up/down arrows navigate history
- Persistent across sessions
- Automatic saving

### Dynamic Prompts

```bash
# Normal mode
>

# Wizard canvas mode
📝>

# With zPath display (if enabled)
@.Projects.myapp>
```

### Special Commands

```bash
# Exit shell
exit
quit
q

# Clear screen
clear
cls

# Show tips
tips

# Empty input (ignored)
<just press Enter>

# Comments (ignored)
# This is a comment
```

---

## Error Handling

### Command Not Found

```bash
> unknowncommand
❌ Unknown command: unknowncommand
Type 'help' for available commands
```

### Missing Arguments

```bash
> data read
❌ Missing required argument: table
Usage: data --model PATH read TABLE [options]
```

### Invalid Path

```bash
> cd @.nonexistent.path
❌ Directory not found: @.nonexistent.path
```

### Schema Not Loaded

```bash
> data --model @.wrong.path read users
❌ Schema not found: @.wrong.path
```

---

## Integration Points

### With zWalker (UI Mode)

```bash
# Launch shell from Walker menu
# Walker menu → "Enter zShell"

# Return to Walker
> walker
# Or
> exit
```

### With zData

```bash
# Direct integration - no separate loading needed
> data --model @.zSchema.users read users

# Wizard canvas supports transactions
> wizard_step start
> wizard_step _transaction: true
> wizard_step step1: data insert users ...
```

### With zAuth

```bash
# Check auth status
> auth status

# Login if required
> auth login

# Commands respect RBAC
> data delete users --where "id=1"
# Requires appropriate permissions
```

### With zConfig

```bash
# Set config values
> config set my_key my_value

# Use in session
> session
# Shows config values
```

### With zFunc

```bash
# Call any loaded plugin function
> func &my_plugin.my_function()

# Context injection works
> func &my_plugin.process(zContext)
```

---

## Testing

### Test Coverage

**100 tests** across 14 categories (100% pass rate):
- A. Initialization & Core Setup (5 tests)
- B. Command Routing - Terminal (6 tests)
- C. Command Routing - zLoader (3 tests)
- D. Command Routing - Integration (10 tests)
- E. Command Routing - Advanced (2 tests)
- F. Wizard Canvas Mode (10 tests)
- G. Special Commands (5 tests)
- H. Command Execution (10 tests)
- I. Shortcut System (10 tests)
- J. Data Operations (10 tests)
- K. Plugin Operations (8 tests)
- L. Session Management (7 tests)
- M. Error Handling (7 tests)
- N. Integration & Cross-Subsystem (7 tests)

**Run Tests:**
```bash
zTests
# Select "zShell"
```

**Test Files:**
- `zTestRunner/zUI.zShell_tests.yaml` (100 test steps)
- `zTestRunner/plugins/zshell_tests.py` (~1,500 lines)

---

## Architecture

### 6-Layer Hierarchy

```
┌─────────────────────────────────────────────────┐
│         LEVEL 6: Package Root (__init__.py)     │
│              └─→ Exports: zShell                │
├─────────────────────────────────────────────────┤
│         LEVEL 5: Facade (zShell.py)             │
│              └─→ 3-method API                   │
├─────────────────────────────────────────────────┤
│    LEVEL 4: Module Aggregator (shell_modules)  │
│         └─→ Exports: ShellRunner, Executor      │
├─────────────────────────────────────────────────┤
│    LEVEL 3: Core Modules (2,340 lines)         │
│         ├─→ ShellRunner (REPL loop)            │
│         ├─→ CommandExecutor (routing)          │
│         └─→ HelpSystem (help display)          │
├─────────────────────────────────────────────────┤
│    LEVEL 2: Command Registry (commands/)       │
│         └─→ 18 command executors               │
├─────────────────────────────────────────────────┤
│    LEVEL 1: Command Executors (18 files)       │
│         ├─→ Terminal (6): where, cd, ls, etc.  │
│         ├─→ zLoader (3): load, data, plugin    │
│         ├─→ Integration (10): auth, config...  │
│         └─→ Advanced (2): walker, wizard_step  │
└─────────────────────────────────────────────────┘
```

### Public API

```python
from zOS.subsystems.zShell import zShell

# Initialize shell
shell = zShell(zcli)

# Run REPL loop (interactive mode)
shell.run_shell()

# Execute single command (testing/non-interactive)
shell.execute_command("data read users --model @.zSchema.users")

# Show help
shell.show_help()
```

### Facade Pattern

zShell uses the **Facade pattern** to hide complexity:
- **Public API:** 3 simple methods
- **Internal:** 2,340 lines across 3 core modules
- **Commands:** 18 command executors with ~5,500 lines

**Benefits:**
- Simple to use (3 methods)
- Complex internally (full-featured)
- Easy to refactor (facade hides changes)

---

## Command Summary

### All Available Commands (18)

| Command | Category | Description |
|---------|----------|-------------|
| `where` | Terminal | Show current workspace |
| `cd` | Terminal | Change directory |
| `pwd` | Terminal | Print working directory |
| `ls` | Terminal | List directory contents |
| `help` | Terminal | Show command help |
| `shortcut` | Terminal | Manage zVars and file shortcuts |
| `load` | zLoader | Load resources |
| `data` | zLoader | Database operations (CRUD) |
| `plugin` | zLoader | Plugin management |
| `auth` | Integration | Authentication commands |
| `comm` | Integration | Communication services |
| `config` | Integration | Configuration management |
| `func` | Integration | Function execution |
| `open` | Integration | Open files and URLs |
| `session` | Integration | Session information |
| `walker` | Advanced | Navigate to Walker UI |
| `wizard_step` | Advanced | Wizard canvas mode |
| `wizard` | Advanced | Alias for wizard_step |

### Special Commands

- `exit`, `quit`, `q` - Exit shell
- `clear`, `cls` - Clear screen
- `tips` - Show quick tips
- `#` - Comment (ignored)
- Empty line - Ignored

---

## Troubleshooting

### Shell Won't Start

**Problem:** `zShell` command not found

**Solution:**
```bash
# Reinstall zOS
pip install --upgrade zolo-zcli

# Or check installation
which zShell
```

### Commands Not Working

**Problem:** Commands not recognized

**Solution:**
```bash
# Check available commands
> help

# Verify spelling
> hlep  ❌
> help  ✅
```

### Wizard Canvas Stuck

**Problem:** Can't exit wizard mode

**Solution:**
```bash
# Clear buffer and stop
> wizard_step clear
> wizard_step stop

# Or force exit
> exit
```

### Path Not Found

**Problem:** zPath not resolving

**Solution:**
```bash
# Check workspace
> where

# List available paths
> ls

# Use absolute paths if needed
> cd /Users/yourname/Projects
```

---

## Migration Notes

### From Old Shell Commands

**Old (deprecated):**
```bash
# Load with alias
> load @.zSchema.users --as db
> data --model $db read users
```

**New (recommended):**
```bash
# Direct zPath
> data --model @.zSchema.users read users
```

### From Manual Transactions

**Old (manual):**
```bash
> data --model $db begin
> data --model $db insert users ...
> data --model $db insert posts ...
> data --model $db commit
```

**New (wizard canvas):**
```bash
> wizard_step start
> wizard_step _transaction: true
> wizard_step step1: data insert users ...
> wizard_step step2: data insert posts ...
> wizard_step run
```

---

## FAQ

### Q: How do I exit the shell?
**A:** Type `exit`, `quit`, or `q` and press Enter.

### Q: Can I use regular bash commands?
**A:** No, zShell is not a bash replacement. It's designed for zOS operations. For bash commands, use your terminal.

### Q: How do I see my command history?
**A:** Use up/down arrows (if readline available) or check `~/.zolo/.zcli_history` file.

### Q: What's the difference between `wizard` and `wizard_step`?
**A:** They're aliases - both do the same thing.

### Q: Can I run Python code in the shell?
**A:** No, but you can call Python functions via `func` command:
```bash
> func &my_plugin.my_python_function()
```

### Q: How do I clear the screen?
**A:** Type `clear` or `cls` and press Enter.

---

## Quick Reference

### Essential Commands
```bash
where               # Show location
ls                  # List files
cd PATH             # Change directory
help                # Show help
data --model PATH   # Data operations
func &plugin.func() # Call function
wizard_step start   # Start workflow
exit                # Exit shell
```

### Workflow Pattern
```bash
1. where            # Know where you are
2. ls               # See what's available
3. load resource    # Load what you need
4. data/func/etc    # Do your work
5. exit             # Leave shell
```

---

## Support

- **Documentation:** `Documentation/zShell_GUIDE.md`
- **Tests:** `zTestRunner/zUI.zShell_tests.yaml` (100 tests)
- **Source:** `zOS/subsystems/zShell/`
- **Help:** Type `help` in the shell

---

**Version:** 1.5.4  
**Last Updated:** 2025-11-08  
**Status:** Production Ready  
**Total Commands:** 18+ (plus special commands)  
**Test Coverage:** 100 tests (100% pass rate)
