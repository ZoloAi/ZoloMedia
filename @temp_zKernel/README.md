# @temp_zKernel - Framework Logic Staging Area

**Status**: 🚧 Staging - Extracted from zOS  
**Purpose**: Framework logic to be merged into zKernel when it joins the monorepo  
**DO NOT**: Touch `~/Projects/Zolo/zKernel` directly - keep it pristine!

---

## 📋 **Contents**

This directory contains framework-specific logic that was extracted from zOS (OS primitives layer) to maintain clean architectural separation:

### **errors/** - Framework Exception Handling

| File | Line Count | Description | Origin |
|------|------------|-------------|--------|
| `exceptions.py` | 355 lines | 12+ framework exceptions (zKernelException base + Schema/Data/UI/Auth exceptions) | `zOS/errors/exceptions.py` (lines 12-417) |
| `traceback.py` | 331 lines | zTraceback class + interactive Walker UI + exception context manager | `zOS/errors/traceback.py` (lines 1-315) |
| `validation.py` | 31 lines | validate_zkernel_instance() - framework initialization validation | `zOS/errors/validation.py` (lines 1-18) |
| `__init__.py` | 83 lines | Package exports for documentation/testing | Created for staging |

### **cli/** - Framework CLI Handlers

| File | Line Count | Description | Origin |
|------|------------|-------------|--------|
| `uninstall.py` | 239 lines | 3 interactive CLI handlers + _confirm_action (uses zDisplay) | `zOS/install/removal.py` (lines 176-345) |
| `zspark.py` | 221 lines | zSpark bootstrapping command + 3 helper functions | `zOS/cli/cli_commands.py` (lines 83-229) |
| `__init__.py` | 37 lines | Package exports for CLI handlers | Created for staging |

### **formatting/** - Framework Colors

| File | Line Count | Description | Origin |
|------|------------|-------------|--------|
| `colors.py` | 159 lines | Framework Colors class (subsystems, Walker UI, semantic, brand) | `zOS/formatting/colors.py` (entire file) |
| `zConfig.colors.zolo` | 283 lines | Color definitions in .zolo format (documentation/customization) | `zOS/formatting/zConfig.colors.zolo` (entire file) |
| `__init__.py` | 9 lines | Package exports for Colors class | Created for staging |

### **logger/** - Framework Logger Integration

| File | Line Count | Description | Origin |
|------|------------|-------------|--------|
| `bootstrap_integration.py` | 102 lines | flush_bootstrap_to_framework() + helpers (LoggerConfig integration) | `zOS/logger/bootstrap.py` (lines 120-172) |
| `config.py` | 60 lines | get_log_level_from_zspark() (parses zSpark configuration files) | `zOS/logger/config.py` (lines 23-41) |
| `__init__.py` | 22 lines | Package exports for logger integration | Created for staging |

### **cli/** - Framework CLI Commands

| File | Line Count | Description | Origin |
|------|------------|-------------|--------|
| `interactive_editor.py` | 309 lines | Interactive TUI editor for user preferences (menus, boxes, workflow) | `zOS/cli/interactive_editor.py` (entire file) |
| `zspark.py` | 304 lines | zSpark.*.zolo framework bootstrapping command | `zOS/cli/cli_commands.py` (lines 115-418) |
| `uninstall.py` | 304 lines | Framework-dependent CLI uninstall handlers | `zOS/install/removal.py` (lines 192-345) |

---

## 🔍 **Why These Were Extracted**

### **Problem**: Architectural Violation
zOS is the **OS primitives layer** (standalone, no framework dependencies).  
zKernel is the **framework layer** (depends on zOS).

**Violations Found**:
1. **Hard Dependencies**: `from zKernel.zCLI import get_current_zcli` (line 44 in exceptions.py)
2. **Framework Imports**: `import zKernel` (line 150 in traceback.py)
3. **Framework Components**: Walker UI, zDisplay, zTraceback interactive handling
4. **Framework Exceptions**: SchemaNotFoundError (zSchema), zUIParseError (zUI), DatabaseNotInitializedError (zData), etc.

### **Solution**: Extract to Staging
- ✅ zOS now contains ONLY OS-level exceptions:
  - `zMachinePathError` (zConfig.machine.zolo paths)
  - `UnsupportedOSError` (OS detection)
- ⚡ Framework logic staged here for later merge
- 📦 Clean separation maintained

---

## 📂 **File-by-File Breakdown**

### **exceptions.py** (445 lines)

**Extracted Exceptions** (12+ framework-specific):

| Exception | Framework | Description |
|-----------|-----------|-------------|
| `zKernelException` | Base | Auto-registers with zTraceback, imports `zKernel.zCLI` |
| `SchemaNotFoundError` | zSchema | Schema file or loaded schema not found |
| `FormModelNotFoundError` | zUI | Form model not defined in schema |
| `InvalidzPathError` | zLoader | zPath syntax validation |
| `DatabaseNotInitializedError` | zData | Database not initialized for CRUD operations |
| `TableNotFoundError` | zData | Table doesn't exist in database |
| `zUIParseError` | zUI | zUI file syntax/structural errors |
| `AuthenticationRequiredError` | zAuth | Protected resource access without auth |
| `PermissionDeniedError` | zAuth | Authenticated user lacks permissions |
| `ConfigurationError` | Framework | zKernel/subsystem configuration invalid |
| `PluginNotFoundError` | Framework | Plugin cannot be loaded |
| `ValidationError` | Framework | Data validation failures |

**Why They're Framework**:
- Reference framework subsystems (zSchema, zUI, zData, zAuth)
- Import `zKernel.zCLI.get_current_zcli()` for auto-registration
- Provide actionable hints specific to framework APIs

---

### **traceback.py** (315 lines)

**Extracted Classes & Functions**:

| Component | Type | Description |
|-----------|------|-------------|
| `zTraceback` | Class | Enhanced error handling with Walker UI integration |
| `ExceptionContext` | Class | Context manager for exception handling with logging |
| `display_error_summary()` | Function | Display error details in Walker UI |
| `display_full_traceback()` | Function | Display complete stack trace in Walker UI |
| `display_formatted_traceback()` | Function | Combined summary + full traceback |

**Why It's Framework**:
- **Hard Import**: `import zKernel` (line 150) to launch Walker UI
- **Framework Dependencies**: `zcli.display`, `zcli.walker`, `zcli.session`
- **Interactive UI**: Launches Walker for interactive error handling
- **Framework Context**: Accesses `zcli.config`, `zcli.zTraceback`

**Key Method**:
```python
def interactive_handler(self, exc: Exception, context: Optional[dict] = None) -> Any:
    """Launch interactive traceback UI (Walker) for exception handling."""
    import zKernel  # Line 150 - HARD DEPENDENCY
    
    # Create new zKernel instance for traceback UI
    traceback_cli = zKernel.zCLI({...})
    return traceback_cli.walker.run()
```

---

### **validation.py** (18 lines)

**Extracted Function**:

```python
def validate_zkernel_instance(zcli, subsystem_name, require_session=True):
    """Validate zKernel instance is properly initialized."""
```

**Why It's Framework**:
- Validates `zcli` parameter (zKernel instance)
- Checks for `zcli.session` attribute (framework-specific)
- Used by framework subsystems during initialization

---

### **zspark.py** (221 lines)

**Extracted zSpark Command** (framework bootstrapping):

| Function | Lines | Description |
|----------|-------|-------------|
| `handle_zspark_command(...)` | ~60 lines | Main handler - initializes zKernel instance |
| `_validate_zspark_file(...)` | ~18 lines | Validates zSpark.*.zolo file exists |
| `_parse_zspark_file(...)` | ~45 lines | Parses .zolo file using zlsp parser |
| `_configure_zspark(...)` | ~23 lines | Applies overrides (dev mode, verbose) |

**Why It's Framework**:
- **Hard Import**: `from zKernel import zKernel` (line 69) - initializes full framework
- **Framework Bootstrapping**: Creates zKernel instance with zSpark configuration
- **Framework Config**: zSpark is the framework configuration file format (.zolo syntax)
- **Framework Execution**: Calls `zcli.run()` to start framework

**Key Handler**:
```python
def handle_zspark_command(boot_logger, Path, zspark_path: str, ...):
    """Execute zSpark.*.zolo configuration file."""
    # Parse and validate zSpark file
    zspark_config, exit_code = _parse_zspark_file(...)
    
    # ═══════════════════════════════════════════════
    # FRAMEWORK INITIALIZATION - Why this is framework-level
    # ═══════════════════════════════════════════════
    from zKernel import zKernel  # Hard dependency
    zcli = zKernel(zspark_config)  # Full framework bootstrap
    zcli.run()  # Launch framework application
    # ═══════════════════════════════════════════════
```

---

### **uninstall.py** (239 lines)

**Extracted CLI Handlers** (3 framework-specific):

| Handler | Lines | Description |
|---------|-------|-------------|
| `cli_uninstall_complete(zcli)` | ~62 lines | Complete uninstall - package + data + dependencies |
| `cli_uninstall_package_only(zcli)` | ~39 lines | Package-only uninstall - preserve data |
| `cli_uninstall_data_only(zcli)` | ~46 lines | Data-only uninstall - keep package |
| `_confirm_action(display, ...)` | ~13 lines | User confirmation with zDisplay |

**Why They're Framework**:
- **Framework Dependencies**: `zcli.display` (zDisplay instance), `zcli.config.sys_paths`
- **Interactive UI**: Uses `display.zDeclare()`, `display.warning()`, `display.success()`, `display.list()`
- **Framework Context**: Accesses framework configuration for paths
- **User Confirmation**: Uses `display.read_string()` for interactive input

**Should STAY in zOS** (OS primitives - kept):
- ✅ `get_optional_dependencies()` - Read pyproject.toml
- ✅ `remove_package()` - Run pip uninstall
- ✅ `remove_user_data()` - Remove directories with shutil
- ✅ `remove_dependencies()` - Uninstall optional packages

**Key Handler**:
```python
def cli_uninstall_complete(zcli):
    """Complete uninstall: Remove EVERYTHING."""
    display = zcli.display  # zDisplay framework dependency
    paths = zcli.config.sys_paths  # Framework configuration
    
    display.zDeclare("Complete Uninstall", ...)  # Framework UI
    if not _confirm_action(display, "complete uninstall"):
        sys.exit(1)
    
    # Uses OS functions from zOS.install.removal:
    data_results = remove_user_data(...)  # ✅ OS-level function
    dep_results = remove_dependencies()   # ✅ OS-level function
    pkg_success = remove_package()        # ✅ OS-level function
    
    display.success("Complete removal successful")  # Framework UI
```

---

## 🔄 **Merge Instructions (When zKernel Joins Monorepo)**

### **Step 1: Verify zKernel Structure**

```bash
cd ~/Projects/Zolo/zKernel

# Check if errors/ directory exists
ls -la errors/

# Expected structure:
# zKernel/
# ├── errors/
# │   ├── __init__.py
# │   ├── exceptions.py (may exist - check for conflicts)
# │   ├── traceback.py (may exist - check for conflicts)
# │   └── validation.py (may exist - check for conflicts)
```

### **Step 2: Copy zKernel to Monorepo** (like we did with zOS)

```bash
cd ~/Projects/Zolo
cp -r zKernel /Users/galnachshon/Projects/ZoloMedia/zKernel

# Verify copy
ls -la /Users/galnachshon/Projects/ZoloMedia/zKernel
```

### **Step 3: Merge @temp_zKernel into zKernel**

```bash
cd /Users/galnachshon/Projects/ZoloMedia

# Option A: If zKernel/errors/ doesn't exist
mkdir -p zKernel/errors
cp @temp_zKernel/errors/* zKernel/errors/

# Option B: If zKernel/errors/ exists (manual merge required)
# 1. Compare files:
diff @temp_zKernel/errors/exceptions.py zKernel/errors/exceptions.py
diff @temp_zKernel/errors/traceback.py zKernel/errors/traceback.py
diff @temp_zKernel/errors/validation.py zKernel/errors/validation.py

# 2. Merge manually (keep zKernel's version, add extracted exceptions if missing)
# 3. Update zKernel/errors/__init__.py to export all exceptions
```

### **Step 4: Update zKernel Imports**

```bash
cd /Users/galnachshon/Projects/ZoloMedia/zKernel

# Update any files that import from zOS.errors to use local imports:
# Before: from zOS.errors import zKernelException, zTraceback
# After:  from zKernel.errors import zKernelException, zTraceback

# Search for zOS.errors imports:
grep -r "from zOS.errors" .
grep -r "import zOS.errors" .

# Update each file found
```

### **Step 5: Update zKernel Package Structure**

If `zKernel/errors/__init__.py` doesn't exist, create it:

```python
# zKernel/errors/__init__.py
"""
Error handling subsystem for zKernel framework.

This module provides comprehensive error handling:
- Custom exceptions with actionable hints
- Interactive traceback UI via Walker
- Subsystem initialization validation
"""

# Runtime validation
from .validation import validate_zkernel_instance

# All custom exceptions
from .exceptions import (
    # Base exception
    zKernelException,
    # Schema/Data exceptions
    SchemaNotFoundError,
    FormModelNotFoundError,
    InvalidzPathError,
    DatabaseNotInitializedError,
    TableNotFoundError,
    ValidationError,
    # UI/Parse exceptions
    zUIParseError,
    # Auth exceptions
    AuthenticationRequiredError,
    PermissionDeniedError,
    # Config exceptions
    ConfigurationError,
    # Plugin exceptions
    PluginNotFoundError,
)

# Traceback handling
from .traceback import (
    zTraceback,
    ExceptionContext,
    display_error_summary,
    display_full_traceback,
    display_formatted_traceback,
)

__all__ = [
    "validate_zkernel_instance",
    "zKernelException",
    "SchemaNotFoundError",
    # ... (all exceptions)
    "zTraceback",
    "ExceptionContext",
    # ... (all traceback functions)
]
```

### **Step 6: Test zKernel Imports**

```bash
cd /Users/galnachshon/Projects/ZoloMedia

# Test that zKernel can import its own errors
python3 -c "from zKernel.errors import zKernelException, zTraceback; print('✓ Imports work!')"

# Test that zOS no longer exports framework exceptions
python3 -c "from zOS.errors import zMachinePathError, UnsupportedOSError; print('✓ OS-level exceptions work!')"

# This should FAIL (good!):
python3 -c "from zOS.errors import zKernelException" 2>&1 | grep "ImportError"
```

### **Step 7: Update pyproject.toml (if needed)**

If zKernel's `pyproject.toml` doesn't list `zKernel.errors` as a package:

```toml
[tool.setuptools]
packages = [
    "zKernel",
    "zKernel.errors",  # Add this
    "zKernel.cli",
    # ... other packages
]
```

### **Step 8: Delete @temp_zKernel**

```bash
cd /Users/galnachshon/Projects/ZoloMedia

# After verifying everything works:
rm -rf @temp_zKernel
git add -A
git commit -m "refactor(zKernel): Merge @temp_zKernel framework logic into zKernel

Merged extracted framework exceptions and error handling from @temp_zKernel:
- 12+ framework exceptions (zKernelException + Schema/Data/UI/Auth)
- zTraceback interactive error handling
- validate_zkernel_instance framework validation

zOS now contains ONLY OS-level exceptions (zMachinePathError, UnsupportedOSError).
Clean architectural separation achieved: zOS = OS primitives, zKernel = framework."
```

---

## ⚠️ **Important Notes**

1. **DO NOT** touch `~/Projects/Zolo/zKernel` directly during this process
2. **VERIFY** zKernel structure before merging (check for conflicts)
3. **TEST** imports after merging (both zKernel and zOS)
4. **UPDATE** any zKernel files that import from zOS.errors
5. **DELETE** @temp_zKernel only after verification

---

## 📊 **Summary Statistics**

| Metric | Value |
|--------|-------|
| **Files Extracted** | 6 (3 errors, 2 cli, 1 __init__) |
| **Total Lines** | ~1,328 lines (800 errors + 460 cli + 68 __init__) |
| **Framework Exceptions** | 12+ |
| **Framework Classes** | 3 (zKernelException, zTraceback, ExceptionContext) |
| **Framework Functions** | 10 (3 display + 3 uninstall + 4 zspark) |
| **Framework CLI Handlers** | 4 (3 uninstall + 1 zspark bootstrapping) |
| **OS Exceptions Kept** | 2 (zMachinePathError, UnsupportedOSError) |
| **OS Functions Kept** | 4 (get_optional_dependencies, remove_package, remove_user_data, remove_dependencies) |

---

## 🎯 **Result**

**Before Extraction** (zOS):
- ❌ zOS contained 14 exceptions (12 framework + 2 OS)
- ❌ zOS had hard `zKernel.zCLI` dependency (errors/exceptions.py:44)
- ❌ zOS included zTraceback (Walker UI integration)
- ❌ zOS included framework CLI handlers (3 uninstall commands with zDisplay)
- ❌ zOS included zSpark command (`from zKernel import zKernel` - cli/cli_commands.py:115)
- ❌ zOS/install/removal.py: 345 lines (170 OS + 175 framework)
- ❌ zOS/cli/cli_commands.py: 764 lines (includes 147 lines of zspark code)
- ❌ Violated architectural separation

**After Extraction** (zOS + @temp_zKernel):
- ✅ zOS contains ONLY 2 OS-level exceptions
- ✅ zOS contains ONLY 4 OS-level removal functions
- ✅ zOS has NO zKernel dependencies (zero `from zKernel` imports)
- ✅ zOS/install/removal.py: NOW 189 lines (WAS: 345 lines) - 45% reduction
- ✅ zOS/cli/cli_commands.py: NOW 617 lines (WAS: 764 lines) - 19% reduction
- ✅ @temp_zKernel staged for merge into zKernel (~1,328 lines)
- ✅ Clean architectural separation achieved

---

## 📝 **Changelog**

### **2026-01-16** - Phase 0.1: Framework Exceptions
- Extracted 12+ framework exceptions from `zOS/errors/exceptions.py`
- Extracted zTraceback system from `zOS/errors/traceback.py`
- Extracted validate_zkernel_instance from `zOS/errors/validation.py`
- Created @temp_zKernel staging area
- Updated zOS to keep only OS-level exceptions

### **2026-01-16** - Phase 0.2: Framework CLI Handlers (Uninstall)
- Extracted 3 CLI uninstall handlers from `zOS/install/removal.py`
  - `cli_uninstall_complete(zcli)` - Complete uninstall (package + data + deps)
  - `cli_uninstall_package_only(zcli)` - Package-only (preserve data)
  - `cli_uninstall_data_only(zcli)` - Data-only (keep package)
- Extracted `_confirm_action(display, ...)` helper
- Updated zOS to keep only OS-level removal functions

### **2026-01-16** - Phase 0.3: Framework CLI Command (zSpark)
- Extracted zSpark bootstrapping command from `zOS/cli/cli_commands.py`
  - `handle_zspark_command(...)` - Main handler (initializes zKernel instance)
  - `_validate_zspark_file(...)` - File validation
  - `_parse_zspark_file(...)` - .zolo parsing with zlsp
  - `_configure_zspark(...)` - Configuration overrides
- Removed zSpark detection and routing from `zOS/cli/main.py`
- Commented out `handle_zspark_command` export in `zOS/cli/__init__.py`
- Added note: zSpark command no longer available in standalone zOS

### **2026-01-17** - Phase 0.4: Framework Colors
- Extracted 90% of Colors class from `zOS/formatting/colors.py` (framework-specific)
  - **Subsystem Colors** (12): ZDATA, ZFUNC, ZDIALOG, ZWIZARD, ZDISPLAY, PARSER, CONFIG, ZOPEN, ZCOMM, ZAUTH, EXTERNAL
  - **Walker Colors** (8): MAIN, SUB, MENU, DISPATCH, ZLINK, ZCRUMB, LOADER, SUBLOADER
  - **Semantic Colors** (8): zInfo, zSuccess, zWarning, zError + aliases
  - **Brand Colors** (4): PRIMARY, SECONDARY + aliases
  - `get_semantic_color()` method - Framework semantic mapping
- Moved `zConfig.colors.zolo` (283 lines) - Framework color documentation
- Created minimal `zOS/formatting/ansi.py` (28 lines) - OS-level ANSI codes only
- Updated `zOS/logger/ecosystem.py` to use inline ANSI codes (no Colors import)
- Updated `zOS/formatting/terminal.py` to accept ANSI codes directly

### **2026-01-17** - Phase 0.5: Framework Logger Integration
- Extracted `flush_to_framework()` method from `zOS/logger/bootstrap.py`
  - Framework-specific logger routing (ERROR → both loggers, INFO → session only)
  - Depends on zKernel's LoggerConfig structure (framework + session_framework)
  - Semantic routing policy is framework business logic
- Extracted `get_log_level_from_zspark()` from `zOS/logger/config.py`
  - Parses zSpark (framework bootstrapping) configuration files
  - Framework-specific key aliases ("logger", "log_level", "logLevel", "zLogger")
- Updated zOS logger docstrings to be OS-centric, not framework-centric
  - `formats.py`: Changed "zKernel logging" to "unified logging for Zolo apps"
  - `console.py`: Removed "where zKernel logger isn't available" language
  - `bootstrap.py`: Updated examples to use OS-level methods only

### **2026-01-17** - Phase 0.6: Interactive TUI Editor
- Extracted `interactive_editor.py` (309 lines) from `zOS/cli/`
  - Interactive TUI with menus, boxes, colored prompts (framework UX)
  - User workflow logic (edit loop, save prompts, change tracking)
  - Application-level feature, not OS primitive
- Removed `handle_machine_edit_command()` from `zOS/cli/cli_commands.py`
- Removed `--edit` flag from `zOS/cli/parser.py`
- Removed `--edit` routing from `zOS/cli/main.py`
- Total extracted: ~2,272 lines (800 errors + 460 cli + 68 __init__ + 451 formatting + 184 logger + 309 TUI)

---

**Status**: ✅ Phase 0.1, 0.2, 0.3, 0.4, 0.5 & 0.6 Complete - Ready for merge when zKernel joins monorepo

**Next Steps**: zOS CLI is now minimal OS primitives (read, write, execute) with no interactive TUI!
