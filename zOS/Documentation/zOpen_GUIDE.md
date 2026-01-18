# zOpen Guide

> **Open anything, anywhere™**  
> Files, URLs, and workspace resources with intelligent routing and graceful fallbacks.

---

## What It Does

**zOpen** handles all file and URL opening operations in zOS:

- ✅ **Opens files** - Routes by extension (.html→browser, .txt/.py→IDE)
- ✅ **Opens URLs** - http/https in your preferred or default browser
- ✅ **Resolves zPaths** - `@.folder.file.ext` (workspace) or `~.path.file` (absolute)
- ✅ **Executes hooks** - onSuccess/onFail callbacks via zFunc
- ✅ **Graceful fallbacks** - Displays content when browser/IDE fails
- ✅ **Interactive prompts** - Creates missing files via zDialog

**Status:** ✅ Production-ready (100% test coverage, 83/83 tests passing)

---

## Why It Matters

### For Developers
- Zero configuration - uses your preferred browser/IDE from zConfig
- Supports two input formats (string and dict with hooks)
- Type-safe with 100% type hint coverage
- Industry-grade: 3-tier modular architecture, 97 constants, comprehensive error handling

### For Executives
- **Reduces friction** - Developers open files/URLs without leaving zOS
- **Cross-platform** - Works on macOS, Linux, Windows
- **Production-ready** - 83 comprehensive tests covering all scenarios
- **Extensible** - Easy to add new file types (PDF, images, archives)

---

## Architecture (3-Tier)

```
zOpen (3 tiers, 6 files, 1,944 lines with docs)
│
├── Tier 1: Foundation Modules (open_modules/)
│   ├── open_paths.py    → zPath resolution (@ and ~)
│   ├── open_urls.py     → URL opening in browsers
│   └── open_files.py    → File opening by extension
│
├── Tier 2: zOpen.py     → Facade (routing + hooks)
│
└── Tier 3: __init__.py  → Package root
```

**Test Coverage:** 83 tests across 8 categories (A-H) = 100% coverage

---

## How It Works

### 1. Type Detection (Automatic)
zOpen automatically detects what you're opening:
- **URLs**: `http://`, `https://`, or `www.` → browser
- **zPaths**: `@` (workspace) or `~` (absolute) → resolve then route
- **Local files**: Everything else → route by extension

### 2. Extension Routing
```
.html, .htm               → Browser (file:// URL)
.txt, .md, .py, .js, etc. → IDE (from zConfig)
Other extensions          → Graceful fallback
```

### 3. Hook Execution (Optional)
```python
# Execute callback on success
zcli.open.handle({
    "zOpen": {
        "path": "@.docs.readme.md",
        "onSuccess": "log_success()"
    }
})

# Execute callback on failure
zcli.open.handle({
    "zOpen": {
        "path": "/missing/file.txt",
        "onFail": "handle_error()"
    }
})
```

---

## Quick Start

### Basic Usage

```python
from zOS import zOS

zcli = zOS()

# Open local file (auto-detects .py → IDE)
zcli.open.handle("zOpen(/path/to/script.py)")

# Open URL (auto-opens in browser)
zcli.open.handle("zOpen(https://github.com)")

# Open workspace file (@ = workspace-relative)
zcli.open.handle("zOpen(@.docs.readme.md)")
```

### zPath Syntax

```python
# Workspace-relative (@)
"@.folder.file.ext"       → {zWorkspace}/folder/file.ext
"@.src.main.py"           → {zWorkspace}/src/main.py

# Absolute (~)
"~.Users.name.file.txt"   → /Users/name/file.txt
"~.tmp.test.log"          → /tmp/test.log
```

### With Hooks

```python
# String format (no hooks)
zcli.open.handle("zOpen(/path/to/file.txt)")

# Dict format (with hooks)
zcli.open.handle({
    "zOpen": {
        "path": "/path/to/file.txt",
        "onSuccess": "zFunc(@handlers.success)",
        "onFail": "zFunc(@handlers.error)"
    }
})
```

---

## Common Scenarios

### Scenario 1: Open Project Files
```python
# Open README in IDE
zcli.open.handle("zOpen(@.README.md)")

# Open config in IDE
zcli.open.handle("zOpen(@.config.settings.yaml)")

# Open HTML docs in browser
zcli.open.handle("zOpen(@.docs.index.html)")
```

### Scenario 2: Open External URLs
```python
# HTTPS URL
zcli.open.handle("zOpen(https://docs.python.org)")

# HTTP URL
zcli.open.handle("zOpen(http://localhost:8000)")

# WWW prefix (auto-adds https://)
zcli.open.handle("zOpen(www.github.com)")
```

### Scenario 3: Handle Missing Files
```python
# If file doesn't exist:
# 1. zDialog prompts: "Create file or Cancel?"
# 2. If "Create file" → creates empty file + opens in IDE
# 3. If "Cancel" → returns "stop"

result = zcli.open.handle("zOpen(@.new.file.py)")
```

### Scenario 4: Automation with Hooks
```python
# Log all file opens
zcli.open.handle({
    "zOpen": {
        "path": "@.sensitive.data.csv",
        "onSuccess": "log_access('data.csv', 'opened')",
        "onFail": "alert_admin('access_denied')"
    }
})
```

---

## Configuration

### Browser Preference
Set in `zConfig.machine.yaml`:
```yaml
zMachine:
  browser: "chrome"  # Options: chrome, firefox, safari, arc, etc.
```

### IDE Preference
Set in `zConfig.machine.yaml`:
```yaml
zMachine:
  ide: "cursor"  # Options: cursor, code, nano, vim
```

### Workspace Path
Set in session (usually auto-detected):
```python
zcli.session["zSpace"] = "/path/to/workspace"
```

---

## API Reference

### Main Method

#### `handle(zHorizontal)`
Opens file or URL with optional hooks.

**Parameters:**
- `zHorizontal` (str | dict): Open specification

**String Format:**
```python
"zOpen(/path/to/file.txt)"
"zOpen(https://example.com)"
"zOpen(@.folder.file.ext)"
```

**Dict Format:**
```python
{
    "zOpen": {
        "path": "/path/to/file.txt",      # Required
        "onSuccess": "callback()",         # Optional
        "onFail": "error_handler()"        # Optional
    }
}
```

**Returns:**
- `"zBack"`: Operation successful
- `"stop"`: Operation failed
- Hook result if hook executed

---

## Error Handling

### Missing Files
```python
# Behavior:
# 1. zDialog prompts for action (if available)
# 2. User chooses "Create file" or "Cancel"
# 3. Returns "zBack" (created) or "stop" (cancelled)

result = zcli.open.handle("zOpen(/missing/file.txt)")
if result == "stop":
    print("File not created")
```

### Browser Failures
```python
# Behavior:
# 1. Attempts to open in preferred browser
# 2. Falls back to system default browser
# 3. If all fail → displays URL info in terminal
# 4. Returns "zBack" (displayed) or "stop" (total failure)

result = zcli.open.handle("zOpen(https://example.com)")
# Always attempts graceful fallback
```

### IDE Failures
```python
# Behavior:
# 1. Attempts to open in configured IDE
# 2. If IDE unavailable → prompts to select IDE (zDialog)
# 3. If all fail → displays file content in terminal
# 4. Returns "zBack" (displayed) or "stop" (unreadable file)

result = zcli.open.handle("zOpen(@.script.py)")
# Always attempts graceful fallback
```

### Invalid zPaths
```python
# Missing workspace context
zcli.session["zSpace"] = None
result = zcli.open.handle("zOpen(@.file.txt)")
# Returns: "stop" (no workspace to resolve)

# Invalid format (too few parts)
result = zcli.open.handle("zOpen(@.file)")
# Returns: "stop" (invalid zPath format)
```

---

## Integration Examples

### With zShell
```python
# Execute shell command: open @.docs.readme.md
def shell_open(zcli, args):
    path = args[0]
    return zcli.open.handle(f"zOpen({path})")
```

### With zDispatch
```python
# zDispatch automatically routes zOpen() commands
# Defined in dispatch_launcher.py (lines 424-428)
if zHorizontal.startswith("zOpen("):
    return self.zcli.open.handle(zHorizontal)
```

### With zFunc
```python
# Hook execution via zFunc
if result == "zBack" and on_success:
    return zcli.zfunc.handle(on_success)
```

### With zDialog
```python
# File creation prompt
if not os.path.exists(path):
    response = zcli.dialog.handle({
        "zDialog": {
            "fields": [{
                "name": "action",
                "type": "enum",
                "options": ["Create file", "Cancel"]
            }]
        }
    })
```

---

## Testing

### Run Tests
```bash
# Via declarative test suite
zolo ztests
# Select: zOpen

# Expected: 83/83 tests passing
```

### Test Categories (83 tests)
- **A. Facade** (8 tests) - Initialization, handle() method, constants
- **B. zPath Resolution** (10 tests) - @ and ~ path resolution
- **C. URL Opening** (12 tests) - http/https/www handling
- **D. File Opening** (15 tests) - Extension routing, IDE integration
- **E. Type Detection** (10 tests) - URL vs zPath vs file detection
- **F. Input Parsing** (10 tests) - String and dict format parsing
- **G. Hook Execution** (8 tests) - onSuccess/onFail callbacks
- **H. Error Handling** (10 tests) - All error scenarios and fallbacks

---

## Best Practices

### ✅ Do This
```python
# Use zPaths for workspace files
zcli.open.handle("zOpen(@.docs.api.md)")

# Configure browser/IDE in zConfig
# (in zConfig.machine.yaml)
zMachine:
  browser: "chrome"
  ide: "cursor"

# Use hooks for automation
zcli.open.handle({
    "zOpen": {
        "path": "@.config.yaml",
        "onSuccess": "log_access()"
    }
})

# Handle return codes
result = zcli.open.handle("zOpen(@.file.txt)")
if result == "stop":
    # Handle error
    pass
```

### ❌ Avoid This
```python
# Don't use absolute paths for workspace files
zcli.open.handle("zOpen(/full/path/to/workspace/docs/api.md)")
# Use: "zOpen(@.docs.api.md)" instead

# Don't ignore return codes
zcli.open.handle("zOpen(@.critical.file)")  # No error checking
# Always check: if result == "stop": ...

# Don't hardcode paths
zcli.open.handle("zOpen(/Users/me/project/file.py)")
# Use: "zOpen(@.file.py)" or "zOpen(~.Users.me.project.file.py)"
```

---

## File Type Support

### Currently Supported
| Extension | Handler | Behavior |
|-----------|---------|----------|
| `.html`, `.htm` | Browser | Opens in system browser (file:// URL) |
| `.txt`, `.md` | IDE | Opens in configured IDE |
| `.py`, `.js` | IDE | Opens in configured IDE |
| `.json`, `.yaml`, `.yml` | IDE | Opens in configured IDE |

### Adding New Types
To add support for new file types, update `open_files.py`:

```python
# In EXTENSIONS constants
EXTENSIONS_PDF = ('.pdf', '.doc', '.docx')
EXTENSIONS_IMAGES = ('.png', '.jpg', '.gif', '.svg')

# In open_file() routing
if ext in EXTENSIONS_PDF:
    return _open_document(path)

if ext in EXTENSIONS_IMAGES:
    return _open_image(path)
```

**Future Extensions** (documented in code):
- Documents: PDF, Word, Excel, PowerPoint
- Images: PNG, JPG, GIF, SVG (with Bifrost display)
- Archives: ZIP, TAR, GZ (with extraction options)
- Media: Audio (MP3, WAV), Video (MP4, AVI)

---

## Troubleshooting

### "No workspace set for relative path"
**Problem:** Using `@` paths without workspace context  
**Solution:** Ensure `zcli.session["zSpace"]` is set (usually auto-detected)

### "Failed to open with IDE"
**Problem:** Configured IDE not found on system  
**Solution:**
1. zDialog will prompt to select available IDE
2. Or manually set: `zcli.config.persistence.persist_machine("ide", "nano")`

### "Browser failed to open URL"
**Problem:** Browser not available or URL malformed  
**Solution:** zOpen automatically falls back to displaying URL info in terminal

### "File not found"
**Problem:** Opening non-existent file  
**Solution:** zDialog prompts to create file or cancel (if zDialog available)

---

## Summary

**zOpen** provides intelligent file and URL opening for zOS:

- ✅ **3-tier architecture** - Modular (paths, URLs, files) + facade + root
- ✅ **Type detection** - Automatically routes to appropriate handler
- ✅ **Extension routing** - .html→browser, .py→IDE
- ✅ **zPath resolution** - `@` workspace-relative, `~` absolute
- ✅ **Hook execution** - onSuccess/onFail callbacks via zFunc
- ✅ **Graceful fallbacks** - Content display when tools fail
- ✅ **Interactive prompts** - File creation via zDialog
- ✅ **Fully tested** - 83 comprehensive tests (100% coverage)

**Key Integration Points:**
- Uses **zConfig** for browser/IDE preferences and workspace path
- Uses **zDisplay** for status messages and fallback content display
- Uses **zDialog** for file creation and IDE selection prompts
- Uses **zFunc** for hook callback execution
- Integrates with **zDispatch** for command routing

Use **zOpen** whenever you need to open files or URLs in your zOS workflows!
