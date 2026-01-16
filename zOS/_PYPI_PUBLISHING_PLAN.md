# zOS PyPI Publishing Plan

**Status**: 🔴 **ARCHITECTURAL AUDIT REQUIRED**  
**Current Version**: 1.0.0  
**Target**: PyPI Publication + zlsp Update (1.0.1 → 1.0.3)

**⚠️ CRITICAL FINDING**: zOS contains framework logic that belongs in zKernel, violating architectural separation. Must be resolved before publishing.

---

## 📑 Table of Contents

- **[Phase 0](#-critical-phase-0---architectural-audit--refactoring)** 🔴 BLOCKING - Framework logic cleanup
  - [0.1 Framework Exceptions](#01-framework-exceptions-in-errors-module-🔴-high-priority)
  - [0.2 Framework Uninstall Logic](#02-framework-uninstall-logic-in-installremovalpy-🟡-medium-priority)
  - [0.3 Framework CLI Command](#03-framework-cli-command-handle_zspark_command-🟡-medium-priority)
  - [0.4 Hardcoded Colors → .zolo](#04-hardcoded-colors--zconfigcolorszolo-🟢-low-priority-enhancement)
  - [0.5 Code Comments Cleanup](#05-code-comments--docstrings-cleanup-🟡-medium-priority)
  - [0.6 Invalid CLI Entry Point](#06-invalid-cli-entry-point-🔴-high-priority)
- **[Phase 1](#-phase-1-code-cleanup--organization)** - Code cleanup (1.1 ✅ Complete)
- **[Phase 2](#-phase-2-documentation--metadata)** - Documentation
- **[Phase 3](#-phase-3-testing--validation)** - Testing
- **[Phase 4](#-phase-4-pypi-publishing-zos)** - PyPI publish (zOS)
- **[Phase 5](#-phase-5-zlsp-update-101--103)** - zlsp update
- **[Phase 6](#-phase-6-post-publishing)** - Post-publish tasks
- **[Phase 7](#-phase-7-github-release-notes)** - GitHub releases

---

## ⚠️ **CRITICAL: Phase 0 - Architectural Audit & Refactoring**

**STATUS**: 🟡 **IN PROGRESS** (3/6 complete - 50%) - Must be resolved before publishing

**Progress**:
- ✅ **0.1** Framework Exceptions (P0) - **COMPLETE** (800 lines extracted)
- ✅ **0.2** Framework Uninstall (P1) - **COMPLETE** (268 lines extracted)
- ✅ **0.3** Framework CLI Command (P1) - **COMPLETE** (221 lines extracted)
- ⏸️ **0.4** Hardcoded Colors → .zolo (P3) - Pending
- ⏸️ **0.5** Code Comments Cleanup (P2) - Pending
- ⏸️ **0.6** Invalid Entry Point (P0) - Pending

### **Issue**: zKernel Framework Logic in zOS (OS Primitives Layer)

**Problem**: zOS contains framework-specific logic that belongs in zKernel, violating the architectural separation:
- **zOS** = OS primitives (standalone, no framework dependencies)
- **zKernel** = Framework (depends on zOS)

---

### **🚨 CRITICAL WORKFLOW NOTE:**

**DO NOT** touch `~/Projects/Zolo/zKernel` directly - keep it pristine!

**Instead:**
1. ✅ Extract zKernel logic from zOS → `ZoloMedia/@temp_zKernel/` (staging area)
2. ✅ Remove framework dependencies from zOS
3. ✅ Keep `@temp_zKernel` organized by module (errors/, cli/, install/)
4. ⏭️ Later: Merge `@temp_zKernel` when we COPY zKernel into monorepo (like we did with zOS)

**Directory Structure:**
```
ZoloMedia/
├── zOS/              (OS primitives - cleaned)
├── zlsp/             (Language server)
├── @temp_zKernel/    (Extracted framework logic - staging)
│   ├── errors/
│   │   ├── exceptions.py      (12+ framework exceptions)
│   │   ├── traceback.py       (zTraceback system)
│   │   └── validation.py      (validate_zkernel_instance)
│   ├── cli/
│   │   ├── zspark.py          (handle_zspark_command)
│   │   └── uninstall.py       (3 CLI handlers with zcli.display)
│   └── README.md              (Merge instructions for later)
```

This keeps `~/Projects/Zolo/zKernel` untouched while we clean up zOS architecture.

---

### **0.1 Framework Exceptions in `errors/` Module** ✅ **COMPLETE**

**Status**: ✅ **EXTRACTED** - Framework logic moved to `@temp_zKernel/errors/`

**Files extracted:**

#### **`errors/exceptions.py`** - Framework exceptions, NOT OS primitives:
```python
class zKernelException(Exception):  # Line 12
    def _register_with_traceback(self):
        from zKernel.zCLI import get_current_zcli  # Line 44 - HARD DEPENDENCY
```

**Contains 12+ framework-specific exceptions:**
- `SchemaNotFoundError` (line 62) - zSchema framework
- `FormModelNotFoundError` (line 103) - zUI framework  
- `DatabaseNotInitializedError` (line 153) - zData framework
- `TableNotFoundError` (line 183) - zData framework
- `zUIParseError` (line 204) - zUI framework
- `AuthenticationRequiredError` (line 232) - zAuth framework
- `PermissionDeniedError` (line 263) - zAuth framework
- `ConfigurationError` (line 285) - Framework config
- `PluginNotFoundError` (line 305) - Framework plugins
- `ValidationError` (line 330) - Framework validation
- Plus more...

#### **`errors/validation.py`** - Framework validation:
```python
def validate_zkernel_instance(zcli, subsystem_name, require_session=True):  # Line 4
    """Validate zKernel instance is properly initialized"""
```

#### **`errors/traceback.py`** - Framework traceback system:
```python
import zKernel  # Line 150 - HARD DEPENDENCY
traceback_cli = zKernel.zCLI({...})  # Line 160
```

**COMPLETED ACTIONS**:
1. ✅ **KEPT in zOS**: OS-level exceptions only (2 exceptions, 93 lines)
   - `zMachinePathError` - zConfig.machine.zolo path resolution
   - `UnsupportedOSError` - OS detection
   - Removed: 12+ framework exceptions (325 lines)
   
2. ✅ **EXTRACTED to @temp_zKernel**: All framework logic (800 lines total)
   - `@temp_zKernel/errors/exceptions.py` (355 lines) - zKernelException + 12 framework exceptions
   - `@temp_zKernel/errors/traceback.py` (331 lines) - zTraceback + Walker UI integration
   - `@temp_zKernel/errors/validation.py` (31 lines) - validate_zkernel_instance()
   - `@temp_zKernel/errors/__init__.py` (83 lines) - Package exports
   - Hard dependencies on `zKernel.zCLI` kept intact (will work when merged)

3. ✅ **UPDATED zOS**: Clean separation achieved
   - `zOS/errors/exceptions.py` - NOW: 93 lines (WAS: 418 lines) - 78% reduction
   - `zOS/errors/__init__.py` - NOW: 25 lines (WAS: 87 lines) - Exports only OS exceptions
   - `zOS/__init__.py` - Updated docstring, removed framework references
   - Deleted: `zOS/errors/traceback.py`, `zOS/errors/validation.py`

4. ✅ **DOCUMENTED in @temp_zKernel/README.md** (460 lines):
   - Comprehensive extraction summary (800 lines, 12+ exceptions, 3 classes)
   - Step-by-step merge instructions for when zKernel joins monorepo
   - File-by-file breakdown with line counts and descriptions
   - Verification tests and import examples
   - Workflow note: DO NOT touch `~/Projects/Zolo/zKernel` directly

**RESULT**:
- ✅ zOS has ZERO zKernel dependencies
- ✅ Clean architectural separation achieved
- ✅ Framework logic staged in @temp_zKernel for later merge
- ✅ All files ready to commit (5 created, 4 modified, 2 deleted)

---

### **0.2 Framework Uninstall Logic in `install/removal.py`** ✅ **COMPLETE**

**Status**: ✅ **EXTRACTED** - Framework CLI handlers moved to `@temp_zKernel/cli/uninstall.py`

**Functions extracted:**
```python
def cli_uninstall_complete(zcli):  # Line 194
    display = zcli.display  # Requires zDisplay framework
    paths = zcli.config.sys_paths  # Requires framework config
```

**Contains 3 CLI handlers:**
- `cli_uninstall_complete(zcli)` (line 194) - Uses `zcli.display`
- `cli_uninstall_package_only(zcli)` (line 258) - Uses `zcli.display`
- `cli_uninstall_data_only(zcli)` (line 299) - Uses `zcli.display`

**COMPLETED ACTIONS**:
1. ✅ **KEPT in zOS**: Pure OS functions (182 lines, no framework dependencies)
   - `get_optional_dependencies()` - Read pyproject.toml for optional dependencies
   - `remove_package()` - Run pip uninstall via subprocess
   - `remove_user_data()` - Remove directories with shutil
   - `remove_dependencies()` - Uninstall optional packages
   - All functions return results, no display dependencies

2. ✅ **EXTRACTED to @temp_zKernel**: CLI handlers with framework dependencies (268 lines)
   - `@temp_zKernel/cli/uninstall.py` (244 lines) - 3 CLI handlers + _confirm_action
   - `@temp_zKernel/cli/__init__.py` (24 lines) - Package exports
   - `cli_uninstall_complete(zcli)` - Complete uninstall (package + data + deps)
   - `cli_uninstall_package_only(zcli)` - Package-only (preserve data)
   - `cli_uninstall_data_only(zcli)` - Data-only (keep package)
   - `_confirm_action(display, ...)` - User confirmation with zDisplay
   - All handlers use `zcli.display` and `zcli.config.sys_paths`

3. ✅ **UPDATED zOS**: Removed framework handlers
   - `zOS/install/removal.py` - NOW: 182 lines (WAS: 345 lines) - 47% reduction
   - Deleted 163 lines of framework CLI handlers
   - Added note explaining extraction to @temp_zKernel
   - Kept only OS-level functions (no zDisplay, no zcli parameter)

**RESULT**:
- ✅ zOS/install/ has NO zDisplay dependencies
- ✅ zOS/install/ has NO zcli parameter requirements
- ✅ Framework CLI handlers staged in @temp_zKernel for later merge
- ✅ Clean separation: OS functions (zOS) vs. CLI handlers (zKernel)

---

### **0.3 Framework CLI Command: `handle_zspark_command`** ✅ **COMPLETE**

**Status**: ✅ **EXTRACTED** - zSpark bootstrapping command moved to `@temp_zKernel/cli/zspark.py`

**Code extracted:**
```python
from zKernel import zKernel  # HARD DEPENDENCY
zcli = zKernel(zspark_config)
```

**COMPLETED ACTIONS**:
1. ✅ **EXTRACTED to @temp_zKernel**: `handle_zspark_command()` (221 lines)
   - `@temp_zKernel/cli/zspark.py` (221 lines) - Full command + helpers
   - `handle_zspark_command(...)` - Main handler (initializes zKernel instance)
   - `_validate_zspark_file(...)` - File validation (18 lines)
   - `_parse_zspark_file(...)` - .zolo parsing with zlsp parser (45 lines)
   - `_configure_zspark(...)` - Configuration overrides (23 lines)
   - Hard dependency: `from zKernel import zKernel` (line 69)

2. ✅ **UPDATED zOS**: Removed framework CLI command
   - `zOS/cli/cli_commands.py` - NOW: 617 lines (WAS: 764 lines) - 19% reduction
   - Deleted 147 lines of zspark code (lines 83-229)
   - Added note explaining extraction to @temp_zKernel
   - `zOS/cli/__init__.py` - Commented out `handle_zspark_command` export
   - `zOS/cli/main.py` - Commented out zspark file detection (lines 88-95)
   - `zOS/cli/main.py` - Commented out zspark routing (line 126-127)
   - Added error message: "zSpark command no longer available in standalone zOS"

3. ✅ **DOCUMENTED in @temp_zKernel**: 
   - Added zspark section to README with detailed breakdown
   - Explained: zSpark bootstraps full zKernel framework
   - Updated summary statistics and changelog
   - Exported `handle_zspark_command` in `cli/__init__.py`

**RESULT**:
- ✅ zOS has NO zKernel imports (zero `from zKernel` statements)
- ✅ zSpark command extracted (framework bootstrapping, not OS primitive)
- ✅ zOS/cli reduced by 147 lines (764→617 lines)
- ✅ @temp_zKernel now contains 1,328 lines of framework logic

---

### **0.4 Hardcoded Colors → `zConfig.colors.zolo`** 🟢 LOW PRIORITY (Enhancement)

**File**: `formatting/colors.py`

**Current**: 119 lines of hardcoded Python color definitions
**Problem**: Colors should be user-configurable via `.zolo` files

**Example Current State**:
```python
class Colors:
    ZDATA = "\033[97;48;5;94m"  # Brown bg
    ZFUNC = "\033[97;41m"        # Red bg
    # ... 30+ more hardcoded colors
```

**Desired State**: `zConfig.colors.zolo`
```zolo
#> Zolo Color Configuration (Terminal-first design) <#

colors:
	subsystems:
		zData:    #> CRUD operations <#
			ansi: 97;48;5;94
			hex: #5C3A21
			semantic: brown_bg
		
		zFunc:    #> Function execution <#
			ansi: 97;41
			hex: #FF0000
			semantic: red_bg
		
		# ... etc
	
	standard:
		success: 92     #> Bright green <#
		error: 91       #> Bright red <#
		warning: 93     #> Bright yellow <#
	
	semantic:
		primary: 150    #> Light green (intention) <#
		secondary: 98   #> Medium purple (validation) <#
```

**SOLUTION**:
1. 📝 **CREATE**: `zConfig.colors.zolo` template
2. 🔧 **REFACTOR**: `formatting/colors.py` to:
   - Load from `~/.config/Zolo/zConfig.colors.zolo` (user override)
   - Fall back to bundled defaults if not found
   - Keep `Colors` class API for backward compatibility
3. 📦 **BUNDLE**: Default `zConfig.colors.zolo` in package data
4. 🎨 **zlsp**: Add syntax highlighting for `zConfig.colors.zolo`

**Benefits**:
- ✅ Users can customize colors without editing Python code
- ✅ Consistent with `.zolo`-first design philosophy
- ✅ zlsp can provide validation and auto-completion
- ✅ Colors become part of zMachine profile (portable)

---

### **0.5 Code Comments & Docstrings Cleanup** 🟡 MEDIUM PRIORITY

**Issue**: Many files have comments/docstrings referencing zKernel when they're in zOS:

**Files to update:**
- `formatting/colors.py` (line 10): "ANSI color codes for zKernel terminal output"
- `formatting/__init__.py` (line 3): "Terminal formatting utilities for zKernel"
- `logger/formats.py` (line 2): "Single source of truth for ALL zKernel logging formats"
- `logger/bootstrap.py` (line 6): "Buffers log messages before zKernel framework is initialized"
- `logger/console.py` (line 14): "contexts where full zKernel logger isn't available"
- `install/detection.py` (line 5): "detection for zKernel without any framework dependencies"
- `machine/config.py` (line 19): "Used by all Zolo products (zKernel, zLSP, etc.)" ← OK
- `paths.py` (line 6): "used by zKernel, zLSP, zTheme" ← OK

**SOLUTION**: Global find-replace:
```bash
# Replace in docstrings/comments only (not code logic)
sed -i '' 's/for zKernel/for Zolo applications/g' zOS/**/*.py
sed -i '' 's/zKernel framework/Zolo framework/g' zOS/**/*.py
```

---

### **0.6 Invalid CLI Entry Point** 🔴 HIGH PRIORITY

**File**: `pyproject.toml`

**Lines 74-76**:
```toml
[project.scripts]
zolo = "zOS.cli.main:main"
zTests = "zOS.cli.main:ztests_main"  # ❌ DOESN'T EXIST
```

**SOLUTION**: Remove invalid entry point (covered in Phase 1.4)

---

## **Phase 0 Summary: Action Items**

### **Before Publishing to PyPI**:

| Priority | Action | Source → Destination | Effort | Status |
|----------|--------|---------------------|--------|--------|
| 🔴 P0 | Extract framework exceptions | `zOS/errors/` → `@temp_zKernel/errors/` | 2h | ✅ **COMPLETE** |
| 🟡 P1 | Extract framework uninstall | `zOS/install/removal.py` → `@temp_zKernel/cli/uninstall.py` | 1h | ✅ **COMPLETE** |
| 🟡 P1 | Extract `handle_zspark_command` | `zOS/cli/cli_commands.py` → `@temp_zKernel/cli/zspark.py` | 30m | ✅ **COMPLETE** |
| 🔴 P0 | Remove `zTests` entry point | `zOS/pyproject.toml` | 1m | ⏸️ Pending |
| 🟡 P2 | Clean up comments/docstrings | `zOS/**/*.py` | 30m | ⏸️ Pending |
| 🟢 P3 | Create `zConfig.colors.zolo` | `zOS/formatting/colors.py` → `.zolo` config | 3h | ⏸️ Pending |

### **Extraction Workflow**:

```bash
# Step 1: Create staging area
mkdir -p @temp_zKernel/{errors,cli}

# Step 2: Extract framework logic
# - Copy framework code → @temp_zKernel
# - Remove from zOS
# - Update imports/exports

# Step 3: Document
# - Add @temp_zKernel/README.md with merge instructions
# - Note which files came from where

# Step 4: Later (when copying zKernel to monorepo)
# - Merge @temp_zKernel into zKernel/
# - Delete @temp_zKernel
```

### **⚠️ REMEMBER**: 
- **DO NOT** touch `~/Projects/Zolo/zKernel` directly
- Everything goes to `@temp_zKernel` staging area first
- Merge happens later when we COPY zKernel into monorepo (like we did with zOS)

### **Recommendation**:
1. **Option A (Minimal Publishing)**: 
   - ✅ Extract P0 items to `@temp_zKernel` (exceptions + entry point)
   - 📦 Publish as `zOS 1.0.0` with "⚠️ Some framework stubs remain for compatibility"
   - 🚀 Fast path to PyPI (3h work)
   - Result: zOS is ~80% clean, stubs remain for zspark/uninstall

2. **Option B (Clean Architecture)** ⭐ **RECOMMENDED**:
   - ✅ Extract P0 + P1 items to `@temp_zKernel` (exceptions + uninstall + zspark)
   - 📦 Publish as `zOS 1.0.0` with complete OS/framework separation
   - 🚀 Proper architecture (5h work)
   - Result: zOS is 100% pure OS primitives, zero framework dependencies

3. **Option C (Full Polish)**:
   - ✅ Extract everything + `.zolo`-first configs (P0 + P1 + P2 + P3)
   - 📦 Publish as `zOS 1.0.0` with complete architectural vision
   - 🚀 Production-ready with `.zolo` configs (10h work)
   - Result: zOS is pristine + colors are user-configurable

---

### **File Structure After Extraction** (Option B):

```
ZoloMedia/
├── zOS/                           ✅ CLEAN - Pure OS primitives
│   ├── cli/                       (open command, info banner)
│   ├── errors/                    (OS-level exceptions only)
│   ├── formatting/                (terminal colors - hardcoded for now)
│   ├── install/                   (OS-level install/remove functions)
│   ├── logger/                    (standalone logging)
│   ├── machine/                   (zConfig.machine.zolo detection)
│   └── utils/                     (file opening, paths)
│
├── @temp_zKernel/                 ⚡ EXTRACTED - Framework logic
│   ├── errors/
│   │   ├── exceptions.py          (zKernelException + 12 framework exceptions)
│   │   ├── traceback.py           (zTraceback interactive system)
│   │   └── validation.py          (validate_zkernel_instance)
│   ├── cli/
│   │   ├── zspark.py              (handle_zspark_command - framework bootstrap)
│   │   └── uninstall.py           (3 CLI handlers with zcli.display)
│   └── README.md                  (Merge instructions for later)
│
└── zlsp/                          ✅ UNCHANGED
```

**Later** (when zKernel joins monorepo):
- Merge `@temp_zKernel/` → `zKernel/`
- Delete `@temp_zKernel/`
- `~/Projects/Zolo/zKernel` remains untouched throughout

---

## 📋 **Phase 1: Code Cleanup & Organization**

### **1.1 Remove Build Artifacts** ✅ **COMPLETE**
- [x] Remove all `__pycache__` directories (0 remaining)
- [x] Remove `.pyc` files (0 remaining)
- [x] Remove `zOS.egg-info` directory
- [x] Remove `.DS_Store` files (macOS)
- [x] Add comprehensive `.gitignore` (87 lines)

**Completed Actions:**
```bash
cd zOS
find . -type d -name "__pycache__" | while read dir; do rm -rf "$dir"; done  ✅
find . -type f -name "*.pyc" -delete  ✅
find . -type f -name ".DS_Store" -delete  ✅
rm -rf zOS.egg-info/  ✅
```

**Added**: `.gitignore` covering Python build artifacts, virtual environments, IDE files, test artifacts, macOS/Windows files

**Commit**: `63beb82` - chore(zOS): Phase 1.1 - Remove build artifacts and add .gitignore

### **1.2 Fix Package Structure**
Current Issues:
- `pyproject.toml` line 44: `package-dir = {"zOS" = "."}` ← Flat structure
- `pyproject.toml` line 45: Manually listed packages (should use find)
- Missing `zOS.utils.open` in package list

**Fix:**
```toml
[tool.setuptools]
package-dir = {"zOS" = "."}
packages = [
    "zOS",
    "zOS.cli",
    "zOS.errors",
    "zOS.formatting",
    "zOS.install",
    "zOS.logger",
    "zOS.machine",
    "zOS.machine.detectors",
    "zOS.utils",
    "zOS.utils.open",
]
```

Or use automatic discovery:
```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["zOS*"]
exclude = ["tests*", "docs*"]
```

### **1.3 Update Dependencies**
Current in `pyproject.toml`:
```toml
dependencies = [
    "platformdirs>=3.0.0",
    "PyYAML>=6.0",
]
```

**Action**: ✅ Dependencies are correct (no zlsp dependency!)

### **1.4 Fix Entry Points**
Current:
```toml
[project.scripts]
zolo = "zOS.cli.main:main"
zTests = "zOS.cli.main:ztests_main"
```

**Issue**: `ztests_main` doesn't exist (zKernel feature)

**Fix:**
```toml
[project.scripts]
zolo = "zOS.cli.main:main"
```

---

## 📋 **Phase 2: Documentation & Metadata**

### **2.1 Update README.md**
Current README needs:
- [ ] Installation instructions (`pip install zOS`)
- [ ] Quick start examples
- [ ] Link to ZoloMedia monorepo
- [ ] Feature highlights (machine detection, zolo open, etc.)
- [ ] License information

### **2.2 Add CHANGELOG.md**
Create `CHANGELOG.md`:
```markdown
# Changelog

## [1.0.0] - 2026-01-17

### Added
- Initial release of zOS (Zolo Operating System)
- Machine detection and configuration generation
- `zolo` CLI with machine config display
- `zolo open` command for files and URLs
- Cross-platform support (macOS, Linux, Windows)
- Auto-generates `zConfig.machine.zolo` on first run
- Logger ecosystem with bootstrap support
- Error handling and formatting utilities
```

### **2.3 Add LICENSE File**
- [ ] Create `LICENSE` file (MIT)
- [ ] Ensure all source files have license headers

### **2.4 Update pyproject.toml Metadata**
```toml
[project]
name = "zOS"
version = "1.0.0"
description = "Operating System primitives for the Zolo ecosystem - machine detection, file opening, and CLI utilities"
authors = [
    {name = "Gal Nachshon", email = "gal@zolo.media"}
]
maintainers = [
    {name = "Gal Nachshon", email = "gal@zolo.media"}
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
keywords = [
    "zOS",
    "zolo",
    "operating-system",
    "machine-detection",
    "cli",
    "utilities",
    "cross-platform",
    "configuration",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Shells",
    "Topic :: Utilities",
    "Operating System :: OS Independent",
    "Operating System :: MacOS",
    "Operating System :: POSIX :: Linux",
    "Operating System :: Microsoft :: Windows",
    "Environment :: Console",
    "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/ZoloAi/ZoloMedia"
Documentation = "https://github.com/ZoloAi/ZoloMedia/tree/main/zOS"
Repository = "https://github.com/ZoloAi/ZoloMedia"
"Bug Tracker" = "https://github.com/ZoloAi/ZoloMedia/issues"
```

---

## 📋 **Phase 3: Testing & Validation**

### **3.1 Local Build Test**
```bash
cd zOS
python -m build
# Should create:
# - dist/zOS-1.0.0.tar.gz
# - dist/zOS-1.0.0-py3-none-any.whl
```

### **3.2 Local Install Test**
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows

# Install from wheel
pip install dist/zOS-1.0.0-py3-none-any.whl

# Test commands
zolo
zolo --version
zolo machine
zolo open --help

# Test import
python -c "from zOS.utils.open import open_file, open_url; print('Import OK')"

# Cleanup
deactivate
rm -rf test_env
```

### **3.3 Check Package Contents**
```bash
tar -tzf dist/zOS-1.0.0.tar.gz | head -50
# Verify all necessary files are included
```

---

## 📋 **Phase 4: PyPI Publishing (zOS)**

### **4.1 Test PyPI Upload (Recommended First)**
```bash
# Install twine if needed
pip install twine

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ zOS

# Verify it works
zolo --version
```

### **4.2 Production PyPI Upload**
```bash
# Upload to PyPI
python -m twine upload dist/*

# Test install from PyPI
pip install zOS

# Verify
zolo --version
```

---

## 📋 **Phase 5: zlsp Update (1.0.1 → 1.0.3)**

### **5.1 Verify zlsp Version**
```bash
cd zlsp
grep "__version__" core/version.py
# Should show: __version__ = "1.0.3"
```

### **5.2 Clean zlsp Build Artifacts**
```bash
cd zlsp
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name ".DS_Store" -delete
rm -rf dist/ build/ zlsp.egg-info/
```

### **5.3 Build zlsp**
```bash
cd zlsp
python -m build
# Creates:
# - dist/zlsp-1.0.3.tar.gz
# - dist/zlsp-1.0.3-py3-none-any.whl
```

### **5.4 Test zlsp Locally**
```bash
# Create test environment
python -m venv test_zlsp
source test_zlsp/bin/activate

# Install
pip install dist/zlsp-1.0.3-py3-none-any.whl

# Test
zlsp --version
zolo-lsp --help
python -c "from core.parser import ZoloParser; print('zlsp OK')"

# Cleanup
deactivate
rm -rf test_zlsp
```

### **5.5 Upload zlsp to PyPI**
```bash
cd zlsp
python -m twine upload dist/*
# This will update the existing zlsp package from 1.0.1 to 1.0.3
```

---

## 📋 **Phase 6: Post-Publishing**

### **6.1 Update Documentation**
- [ ] Update main README.md with PyPI install instructions
- [ ] Update zlsp README with version 1.0.3 notes
- [ ] Create release notes on GitHub

### **6.2 Test Installation**
```bash
# Fresh environment test
python -m venv fresh_test
source fresh_test/bin/activate

# Install both packages
pip install zlsp zOS

# Verify versions
pip list | grep -E "zlsp|zOS"
# Should show:
# zlsp    1.0.3
# zOS     1.0.0

# Test both
zolo --version
zlsp --version

# Cleanup
deactivate
rm -rf fresh_test
```

### **6.3 Tag Releases**
```bash
cd /Users/galnachshon/Projects/ZoloMedia

# Tag zOS release
git tag -a zOS-v1.0.0 -m "zOS v1.0.0: Initial PyPI release"

# Tag zlsp update
git tag -a zlsp-v1.0.3 -m "zlsp v1.0.3: PyPI update"

# Push tags
git push origin --tags
```

---

## 📋 **Phase 7: GitHub Release Notes**

### **7.1 Create zOS Release**
Create GitHub release with:
- Tag: `zOS-v1.0.0`
- Title: "zOS v1.0.0 - Initial Release"
- Body: Features, installation, usage examples
- Attach: `dist/zOS-1.0.0-py3-none-any.whl`

### **7.2 Create zlsp Release**
Create GitHub release with:
- Tag: `zlsp-v1.0.3`
- Title: "zlsp v1.0.3 - PyPI Update"
- Body: Changelog, bug fixes, improvements
- Attach: `dist/zlsp-1.0.3-py3-none-any.whl`

---

## ✅ **Checklist Summary**

### **Pre-Publishing (zOS)**
- [ ] Clean build artifacts
- [ ] Fix package discovery in pyproject.toml
- [ ] Remove invalid entry points (zTests)
- [ ] Add missing packages (zOS.utils.open, zOS.machine.detectors)
- [ ] Update README.md
- [ ] Add CHANGELOG.md
- [ ] Add LICENSE file
- [ ] Update metadata in pyproject.toml

### **Publishing (zOS)**
- [ ] Build package (`python -m build`)
- [ ] Test local install
- [ ] Upload to TestPyPI (optional but recommended)
- [ ] Upload to PyPI

### **zlsp Update**
- [ ] Verify version is 1.0.3
- [ ] Clean build artifacts
- [ ] Build package
- [ ] Test local install
- [ ] Upload to PyPI (updates from 1.0.1)

### **Post-Publishing**
- [ ] Test fresh install of both packages
- [ ] Create Git tags
- [ ] Create GitHub releases
- [ ] Update main README

---

## 🚨 **Common Issues & Solutions**

### **Issue 1: Package Not Found After Install**
**Cause**: Incorrect package structure in pyproject.toml  
**Fix**: Use `packages.find` instead of manual list

### **Issue 2: Module Import Errors**
**Cause**: Missing `__init__.py` files  
**Fix**: Ensure all directories have `__init__.py`

### **Issue 3: Version Mismatch**
**Cause**: Cached builds  
**Fix**: `rm -rf dist/ build/ *.egg-info/` before rebuilding

### **Issue 4: Twine Upload Fails**
**Cause**: Missing credentials or network issues  
**Fix**: Configure `~/.pypirc` or use `--repository` flag

---

## 📝 **Notes**

1. **zOS has NO dependency on zlsp** - They are independent packages ✅
2. **zlsp has NO dependency on zOS** - They are independent packages ✅
3. **Both can be installed separately** - Monorepo != single package
4. **Version numbers are independent** - zOS 1.0.0, zlsp 1.0.3

---

## 🎯 **Success Criteria**

✅ Users can `pip install zOS` and get working `zolo` CLI  
✅ Users can `pip install zlsp` and get v1.0.3 (updated from 1.0.1)  
✅ Both packages installable independently  
✅ Both packages work together in monorepo development  
✅ Clean, professional PyPI presence  

---

**Next Step**: Begin Phase 1 cleanup! 🚀
