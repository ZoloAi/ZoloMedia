# zParser: Universal Parsing & Path Resolution

**Version**: 1.5.4+ | **Status**: ✅ Production-Ready | **Tests**: 86/86 real tests (100% pass rate)

> **Parse anything, resolve any path, execute any plugin™**  
> Universal parsing engine for paths, commands, files, expressions, and plugins.

---

## What is zParser?

**zParser** is zOS's universal parsing and path resolution engine that provides:
- **Path Resolution** - Workspace (@.), absolute (~.), zMachine paths
- **Plugin Invocation** - &plugin.function() syntax with auto-discovery
- **Command Parsing** - 20+ command types (zFunc, zLink, zOpen, etc.)
- **File Parsing** - YAML, JSON, auto-format detection
- **Expression Evaluation** - zExpr, zRef, dotted paths
- **Function Paths** - Args, kwargs, nested calls

**Key Insight**: zParser is a **Facade** over 8 specialized modules, providing a single, simple API for all parsing needs.

---

## For Developers

### Quick Start (3 Lines)

```python
from zOS import zOS

z = zOS({"zWorkspace": ".", "zMode": "Terminal"})
resolved_path = z.parser.zPath_decoder("@.zUI.users")
```

**What you get**:
- ✅ Workspace-relative path resolution
- ✅ File type auto-detection (zUI, zSchema, zConfig)
- ✅ Extension handling (.yaml auto-added)
- ✅ Cross-platform compatibility

### Common Operations

```python
# Path resolution
path = z.parser.zPath_decoder("@.zUI.menu")  # Workspace-relative
path = z.parser.zPath_decoder("~./tmp/file")  # Absolute
path = z.parser.resolve_zmachine_path("zMachine.zConfig.app")  # User data dir

# Plugin invocation
result = z.parser.resolve_plugin_invocation("&plugin.function(arg1, arg2)")
is_plugin = z.parser.is_plugin_invocation("&plugin.func()")  # True

# Command parsing
cmd = z.parser.parse_command("zFunc(&plugin.hello())")
cmd = z.parser.parse_command("zLink(@.menu.settings)")

# File parsing
data = z.parser.parse_yaml("key: value\nlist: [1, 2, 3]")
data = z.parser.parse_json('{"key": "value", "num": 42}')
data = z.parser.parse_file_by_path("/path/to/file.yaml")  # Auto-detects format

# Expression evaluation
result = z.parser.zExpr_eval('{"key": "value"}')  # Dict
result = z.parser.zExpr_eval('[1, 2, 3]')  # List
result = z.parser.handle_zRef("zSession.user_id")  # Session reference

# Function path parsing
func_path, args, name = z.parser.parse_function_path("&plugin.func(a, b, key=val)")

# zVaFile parsing
data = z.parser.parse_zva_file("/path/to/file.yaml")
valid = z.parser.validate_zva_structure(data)
metadata = z.parser.extract_zva_metadata(data)
```

### Path Resolution Symbols

```python
# @ (workspace-relative)
z.parser.zPath_decoder("@.zUI.users")
# → {workspace}/zUI.users.yaml

# ~ (absolute)
z.parser.zPath_decoder("~./home/user/file")
# → /home/user/file.yaml

# zMachine (user data directory, cross-platform)
z.parser.resolve_zmachine_path("zMachine.zConfig.app")
# macOS:   ~/Library/Application Support/zolo-zcli/zConfig/app.yaml
# Linux:   ~/.local/share/zolo-zcli/zConfig/app.yaml
# Windows: %LOCALAPPDATA%\zolo-zcli\zConfig\app.yaml

# No symbol (relative to workspace)
z.parser.zPath_decoder("utils.helpers")
# → {workspace}/utils.helpers.py
```

---

## For Executives

### Why zParser Matters

**Problem**: Most CLI frameworks have fragmented parsing:
- ❌ Multiple parsers for different file types
- ❌ Hardcoded paths (not cross-platform)
- ❌ Manual plugin loading (no auto-discovery)
- ❌ No unified API (each subsystem reinvents the wheel)

**Solution**: zParser provides enterprise-grade parsing:
- ✅ **Unified API** - One system for all parsing needs
- ✅ **Cross-Platform Paths** - zMachine for user data (macOS, Linux, Windows)
- ✅ **Auto-Discovery** - Plugins load automatically
- ✅ **Multi-Format** - YAML, JSON, expressions, commands
- ✅ **Type Safety** - 100% type hints

### Business Value

| Feature | Benefit | Impact |
|---------|---------|--------|
| **Unified Parsing** | One API for all formats | Dev: Faster development, fewer bugs |
| **zMachine Paths** | Cross-platform user data | Support: Works on all OS without changes |
| **Plugin Auto-Discovery** | No manual imports | Dev: Cleaner code, easier plugins |
| **Multi-Format Support** | YAML, JSON, expressions | Flexibility: Use best format for each task |
| **Path Symbols (@, ~)** | Clear, explicit paths | Maintainability: Know where files are |

### Production Metrics

- **Test Coverage**: 86 comprehensive tests (100% real, zero stubs)
- **Module Count**: 8 specialized modules + 1 facade
- **API Complexity**: 29 public methods (comprehensive facade)
- **Integration Points**: zConfig, zLoader, zFunc, zData, zWizard
- **Pass Rate**: 100%

---

## Architecture (Developer View)

### Three-Tier Facade Pattern

```
zParser (Facade - Tier 3)
│
├── Tier 2: Specialized Parsers
│   ├── parser_commands    → Command string parsing (20+ types)
│   ├── parser_plugin      → Plugin invocation (&prefix, auto-discovery)
│   ├── parser_file        → File content parsing (YAML, JSON)
│   └── vafile/ package    → zVaFile parsing (UI, Schema, Config)
│
└── Tier 1: Core Utilities
    ├── parser_utils       → Expression evaluation, dotted paths
    └── parser_path        → Path resolution, file identification
```

**Public API (29 methods organized in 7 categories):**

**1. Path Resolution (5 methods)**:
- `zPath_decoder()` - Dotted path to file path
- `identify_zFile()` - File type detection
- `resolve_zmachine_path()` - User data directory
- `resolve_symbol_path()` - @ and ~ symbols
- `resolve_data_path()` - Data_Path from schemas

**2. Plugin Invocation (2 methods)**:
- `is_plugin_invocation()` - Detect & prefix
- `resolve_plugin_invocation()` - Execute plugin function

**3. Command Parsing (1 method)**:
- `parse_command()` - Recognize and parse commands

**4. File Parsing (6 methods)**:
- `parse_file_content()` - Parse with format hint
- `parse_yaml()` - YAML string → dict
- `parse_json()` - JSON string → dict
- `detect_format()` - Auto-detect YAML/JSON
- `parse_file_by_path()` - Load and parse file
- `parse_json_expr()` - JSON expression → object

**5. Expression Evaluation (4 methods)**:
- `zExpr_eval()` - Evaluate expressions
- `parse_dotted_path()` - Split dotted paths
- `handle_zRef()` - Resolve references
- `handle_zParser()` - Parser-specific handling

**6. zVaFile Parsing (7 methods)**:
- `parse_zva_file()` - Parse zVaFile
- `validate_zva_structure()` - Validate structure
- `extract_zva_metadata()` - Extract metadata
- `parse_ui_file()` - UI-specific parsing
- `parse_schema_file()` - Schema-specific parsing
- `parse_config_file()` - Config-specific parsing
- `validate_ui_structure()` - UI validation

**7. Function Path Parsing (1 method)**:
- `parse_function_path()` - Parse zFunc paths

---

## How It Works

### 1. Path Resolution Flow

```
User: "@.zUI.users"
    ↓
zPath_decoder()
    ↓
Symbol detection (@)
    ↓
Workspace resolution
    ↓
File type identification (zUI)
    ↓
Extension addition (.yaml)
    ↓
Result: {workspace}/zUI.users.yaml
```

**File Type Auto-Detection**:
- `zUI.*` → User interface files
- `zSchema.*` → Data schema files
- `zConfig.*` → Configuration files
- Other → Generic files

### 2. Plugin Invocation Flow

```
User: "&plugin.function(arg1, arg2)"
    ↓
is_plugin_invocation() → True
    ↓
resolve_plugin_invocation()
    ↓
Parse: plugin=plugin, func=function, args=[arg1, arg2]
    ↓
Auto-discovery (if not cached)
    ↓ Search paths:
    ↓ 1. @.zOS.utils/plugin.py
    ↓ 2. @.utils/plugin.py
    ↓ 3. @.plugins/plugin.py
    ↓
Load plugin
    ↓
Inject zcli instance
    ↓
Execute: plugin.function(zcli, context, arg1, arg2)
    ↓
Return result
```

**Plugin Syntax**:
```python
# Simple call
"&plugin.function()"

# With args
"&plugin.function(arg1, arg2)"

# With kwargs
"&plugin.function(key1=val1, key2=val2)"

# Mixed
"&plugin.function(arg1, key=value)"

# Nested
"&plugin.outer(&other.inner())"
```

### 3. File Parsing Flow

```
User: parse_file_by_path("data.yaml")
    ↓
Read file content
    ↓
detect_format() → ".yaml"
    ↓
parse_yaml(content)
    ↓
Result: Python dict
```

**Auto-Detection Logic**:
- Tries JSON first (faster, stricter)
- Falls back to YAML
- Returns format type

### 4. Expression Evaluation Flow

```
User: zExpr_eval('{"key": "value"}')
    ↓
Detect type (dict, list, string)
    ↓
parse_json_expr()
    ↓
Result: {"key": "value"}
```

**Supported Expressions**:
- Dicts: `'{"key": "value"}'`
- Lists: `'[1, 2, 3]'`
- Strings: `'"text"'`
- References: `"zSession.key"`

---

## Integration Points

### zConfig Integration
```python
# zParser uses zConfig for workspace resolution
workspace = z.config.sys_paths.workspace_dir
path = z.parser.zPath_decoder("@.file")  # Uses workspace
```

### zLoader Integration
```python
# zLoader uses zParser for path resolution
data = z.loader.handle("@.zUI.menu")  # zParser resolves path
```

### zFunc Integration
```python
# zFunc uses zParser for plugin invocation
result = z.func.handle("&plugin.function()")  # zParser resolves
```

### zData Integration
```python
# zData uses zParser for schema loading
schema = z.data.load_schema("@.zSchema.users")  # zParser resolves
```

### zWizard Integration
```yaml
# zWizard uses zParser for zFunc execution
zWizard:
  step1:
    zFunc: "&plugin.step_one()"  # zParser parses and executes
```

---

## Special Features

### 1. zMachine Paths (Cross-Platform)

```python
# New format (clean, recommended)
path = z.parser.resolve_zmachine_path("zMachine.zConfig.app")

# Legacy format (still supported)
path = z.parser.resolve_zmachine_path("~.zMachine.config.app")

# Results (platform-specific):
# macOS:   ~/Library/Application Support/zolo-zcli/zConfig/app.yaml
# Linux:   ~/.local/share/zolo-zcli/zConfig/app.yaml
# Windows: %LOCALAPPDATA%\zolo-zcli\zConfig\app.yaml
```

### 2. Plugin Auto-Discovery

```python
# Plugin not in cache? zParser searches:
result = z.parser.resolve_plugin_invocation("&my_plugin.func()")

# Search order:
# 1. {workspace}/zOS/utils/my_plugin.py
# 2. {workspace}/utils/my_plugin.py
# 3. {workspace}/plugins/my_plugin.py

# First match is cached for future calls
```

### 3. Multi-Format File Parsing

```python
# Auto-detect and parse (recommended)
data = z.parser.parse_file_by_path("file.yaml")

# Explicit format
data = z.parser.parse_yaml(yaml_content)
data = z.parser.parse_json(json_content)

# Format detection only
fmt = z.parser.detect_format(content)  # ".yaml" or ".json"
```

### 4. Function Path Parsing

```python
# Dict format
spec = {
    "zFunc_path": "/path/to/file.py",
    "zFunc_args": "arg1, arg2"
}
func_path, args, name = z.parser.parse_function_path(spec)

# String format (workspace)
spec = "zFunc(@utils.myfile.my_function, arg1, arg2)"
func_path, args, name = z.parser.parse_function_path(spec)

# String format (absolute)
spec = "zFunc(~./home/user/scripts/file.func)"
func_path, args, name = z.parser.parse_function_path(spec)
```

---

## Error Handling

### Graceful Degradation

```python
# Invalid path
result = z.parser.zPath_decoder("invalid")
# → Returns None or raises clear error

# Missing plugin
result = z.parser.resolve_plugin_invocation("&nonexistent.func()")
# → Logs warning, searches standard paths, raises if not found

# Malformed file
data = z.parser.parse_yaml("invalid: yaml: structure:")
# → Logs error, returns None

# Invalid command
result = z.parser.parse_command("unknown command")
# → Returns {"error": "Unknown command: unknown"}
```

### Known Issues
1. **Plugin Collision** - Multiple plugins with same name (uses first found)
2. **Format Ambiguity** - Files without extensions (use explicit parse methods)
3. **Path Ambiguity** - Relative paths (use @ symbol for clarity)

---

## Testing

### Test Coverage (A-to-I, 86 tests)

- **A. Facade** (6 tests) - Init, attributes, dependencies
- **B. Path Resolution** (10 tests) - zPath, symbols, zMachine
- **C. Plugin Invocation** (8 tests) - Detection, resolution, context
- **D. Command Parsing** (10 tests) - 20+ command types
- **E. File Parsing** (12 tests) - YAML, JSON, auto-detection
- **F. Expression Evaluation** (10 tests) - zExpr, zRef, dotted paths
- **G. Function Path Parsing** (8 tests) - Args, kwargs, nested
- **H. zVaFile Parsing** (12 tests) - UI, Schema, Config
- **I. Integration** (10 tests) - Multi-component workflows

**All 86 tests are real validations - zero stub tests.**

### Declarative Test Suite

```bash
zolo ztests  # Open test menu
# Select: zParser
# → Runs all 86 tests in zWizard pattern
# → Displays final results table
```

**Test Location:** `zTestRunner/zUI.zParser_tests.yaml`

---

## Best Practices

### Do's ✅

- Use `@` symbol for workspace-relative paths
- Use `zMachine` for user data (cross-platform)
- Use `parse_file_by_path()` for auto-format detection
- Use plugin auto-discovery (don't hardcode paths)
- Validate paths before use

### Don'ts ❌

- Don't use hardcoded absolute paths (use ~ symbol if needed)
- Don't manually detect file formats (use auto-detection)
- Don't skip error handling on parse operations
- Don't assume plugin locations (let auto-discovery find them)
- Don't mix path symbols (pick @, ~, or relative consistently)

---

## Migration Notes

### From Legacy Parsing

```python
# ❌ OLD (manual parsing)
import yaml
with open(file_path) as f:
    data = yaml.safe_load(f)

# ✅ NEW (unified parser)
data = z.parser.parse_file_by_path(file_path)
```

### From Hardcoded Paths

```python
# ❌ OLD (hardcoded, not portable)
data_path = "/Users/john/Library/Application Support/myapp/data"

# ✅ NEW (cross-platform)
data_path = z.parser.resolve_zmachine_path("zMachine.myapp.data")
```

### From Manual Plugin Loading

```python
# ❌ OLD (manual import)
import sys
sys.path.append("/path/to/plugins")
from my_plugin import my_function
result = my_function()

# ✅ NEW (auto-discovery)
result = z.parser.resolve_plugin_invocation("&my_plugin.my_function()")
```

---

## Common Patterns

### Path Resolution Pipeline

```yaml
# In zUI file
zData:
  model: "@.zSchema.users"  # zParser resolves to workspace/zSchema.users.yaml
  action: read
  table: users
```

### Plugin Workflow

```yaml
# In zWizard
zWizard:
  step1:
    zFunc: "&validators.check_email(zSession.email)"  # zParser resolves plugin
  step2:
    zFunc: "&database.save_user(zSession.user_data)"
```

### Multi-Format Data Loading

```python
# Let zParser handle format detection
config = z.parser.parse_file_by_path("config.yaml")
data = z.parser.parse_file_by_path("data.json")
schema = z.parser.parse_file_by_path("schema.unknown")  # Auto-detects
```

---

## Performance

### Metrics (Production)

- **Path Resolution**: < 0.1ms (cached symbols)
- **Plugin Invocation**: < 1ms (cached plugins)
- **File Parsing**: < 5ms for small files (< 100KB)
- **Format Detection**: < 0.1ms (JSON try-first)
- **Expression Eval**: < 0.5ms for simple expressions

### Optimization Tips

- Paths are resolved once and cached
- Plugins are discovered once per session
- File format detection is fast (JSON-first)
- Use explicit parse methods for known formats (faster)
- Plugin cache persists across calls

---

## Troubleshooting

### Path Not Resolved

**Issue**: `zPath_decoder()` returns None  
**Cause**: Invalid path syntax  
**Fix**: Use proper symbol (`@`, `~`) and dotted notation

### Plugin Not Found

**Issue**: Plugin invocation fails  
**Cause**: Plugin not in standard paths  
**Fix**: Place plugin in `utils/`, `plugins/`, or `zOS/utils/`

### File Parse Error

**Issue**: `parse_yaml()` returns None  
**Cause**: Malformed YAML syntax  
**Fix**: Validate YAML syntax (use online validator)

### Format Detection Wrong

**Issue**: JSON detected as YAML (or vice versa)  
**Cause**: Ambiguous content  
**Fix**: Use explicit parse method (`parse_json()` or `parse_yaml()`)

---

## Summary

**zParser provides everything you need for universal parsing:**

✅ **29 Public Methods** - Comprehensive facade API  
✅ **3-Tier Architecture** - Facade → Specialized → Utilities  
✅ **Cross-Platform Paths** - zMachine for user data  
✅ **Multi-Format Support** - YAML, JSON, expressions, commands  
✅ **Plugin Auto-Discovery** - No manual imports  
✅ **Path Symbols** - @, ~, zMachine for clarity  
✅ **Type Safety** - 100% type hints  
✅ **Production-Ready** - 86 comprehensive tests

**Bottom Line**: Parse anything, resolve any path, execute any plugin - with one unified API.

---

**Need Help?** Check `zTestRunner/zUI.zParser_tests.yaml` for 86 real-world examples.
