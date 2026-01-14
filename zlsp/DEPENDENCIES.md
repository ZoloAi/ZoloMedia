# zlsp Dependencies

**Last Updated**: January 14, 2026  
**Version**: 1.0.0  
**Status**: ✅ **MINIMAL DEPENDENCY SET**

---

## 📊 Dependency Summary

**Total Required**: 2 packages  
**Optional (themes)**: 1 package  
**Optional (dev)**: 5 packages  
**Python Standard Library**: Extensive use, zero external deps needed

---

## ✅ Required Dependencies

### 1. `pygls>=1.3.0`
**Purpose**: Language Server Protocol (LSP) framework  
**Used By**: `core/server/lsp_server.py`  
**Why Required**: Core LSP server implementation  
**License**: Apache 2.0  
**Size**: ~69 KB (wheel)

**What It Provides**:
- `LanguageServer` class - Main server implementation
- Request/response handling
- JSON-RPC transport layer
- LSP lifecycle management (initialize, shutdown, etc.)

**Import**:
```python
from pygls.lsp.server import LanguageServer
```

**Usage**:
- `ZoloLanguageServer` extends `LanguageServer`
- Handles LSP protocol communication
- Manages client connections

**Could We Remove It?**: ❌ No
- Would need to implement entire LSP protocol from scratch
- pygls is the de facto Python LSP library
- Well-maintained, stable, industry standard

---

### 2. `lsprotocol>=2023.0.0`
**Purpose**: LSP protocol type definitions  
**Used By**: `core/server/lsp_server.py`, `core/providers/*.py`  
**Why Required**: Type-safe LSP protocol structures  
**License**: MIT  
**Size**: ~76 KB (wheel)

**What It Provides**:
- `types.Position` - Line/character positions
- `types.Range` - Text ranges
- `types.Diagnostic` - Error/warning messages
- `types.SemanticTokensLegend` - Token type definitions
- `types.CompletionItem` - Code completion items
- `types.Hover` - Hover information
- And 100+ other LSP protocol types

**Import**:
```python
from lsprotocol import types as lsp_types
```

**Usage**:
- Creating diagnostics (errors/warnings)
- Returning semantic tokens
- Providing hover information
- Code completion items
- All LSP feature implementations

**Could We Remove It?**: ❌ No
- Required by `pygls` (dependency)
- Ensures LSP protocol compliance
- Prevents protocol mismatches
- Type safety for LSP operations

**Transitive Dependencies**:
- `attrs>=21.3.0` - Class decorators (used by lsprotocol)
- `cattrs!=23.2.1` - Serialization (used by lsprotocol)
- `typing-extensions>=4.14.0` - Type hints backport

---

## 🎨 Optional Dependencies: Themes

### 3. `pyyaml>=6.0` (Optional)
**Purpose**: YAML file parsing for theme definitions  
**Used By**: `themes/__init__.py`  
**Why Optional**: Themes are only needed for generating editor configs  
**License**: MIT  
**Size**: Varies by platform (~150-300 KB)

**What It Provides**:
- `yaml.safe_load()` - Parse YAML theme files
- YAML serialization/deserialization

**Import**:
```python
import yaml  # Lazy loaded
```

**Usage**:
- Loading `themes/zolo_default.yaml`
- Theme color palette management
- Editor config generation

**Could We Remove It?**: ⚠️ Partial
- **Already removed from core dependencies** ✅
- Now optional: `pip install zlsp[themes]`
- Lazy loading with graceful error messages
- Could replace with JSON themes in future
- YAML chosen for human readability

**When Is It NOT Needed**:
- Core parsing (`.zolo` files)
- LSP server operation
- Vim integration (uses pre-generated `.vim` files)
- All end-user functionality

**When IS It Needed**:
- Theme development
- Generating new editor configs
- Modifying color schemes

---

## 🛠️ Optional Dependencies: Development

### 4. `pytest>=7.0` (Optional - Dev Only)
**Purpose**: Test framework  
**Why Optional**: Only needed for development/testing  
**License**: MIT

**Usage**:
- Running 494 test cases
- Test discovery and execution
- Fixture management

---

### 5. `pytest-cov>=4.0` (Optional - Dev Only)
**Purpose**: Code coverage reporting  
**Why Optional**: Only needed for development/testing  
**License**: MIT

**Usage**:
- Measuring 80% code coverage
- Generating coverage reports
- Identifying untested code

---

### 6. `black>=23.0` (Optional - Dev Only)
**Purpose**: Code formatter  
**Why Optional**: Only needed for development  
**License**: MIT

**Usage**:
- Auto-formatting Python code
- Enforcing consistent style
- Pre-commit hooks

---

### 7. `mypy>=1.0` (Optional - Dev Only)
**Purpose**: Static type checker  
**Why Optional**: Only needed for development  
**License**: MIT

**Usage**:
- Type hint validation
- Catching type errors before runtime
- IDE integration

---

### 8. `ruff>=0.1.0` (Optional - Dev Only)
**Purpose**: Fast Python linter  
**Why Optional**: Only needed for development  
**License**: MIT

**Usage**:
- Code quality checks
- Import sorting
- Style enforcement
- Faster alternative to pylint/flake8

---

## 📦 Python Standard Library Usage

zlsp makes extensive use of the Python standard library, avoiding external dependencies:

### Core Modules Used
- `json` - JSON parsing/serialization
- `pathlib` - Path manipulation
- `typing` - Type hints
- `dataclasses` - Data structures
- `enum` - Enumerations
- `re` - Regular expressions
- `difflib` - Fuzzy matching (error suggestions)
- `argparse` - CLI argument parsing
- `logging` - Logging framework
- `sys` - System operations
- `os` - OS interface
- `io` - I/O operations
- `collections` - defaultdict
- `string` - String operations

**Why This Matters**:
- ✅ No external dependencies for core functionality
- ✅ Faster installation
- ✅ Fewer compatibility issues
- ✅ Smaller distribution size
- ✅ Better long-term stability

---

## 🎯 Dependency Philosophy

### Principles
1. **Minimal by Default**: Only 2 required packages
2. **Standard Library First**: Use Python stdlib whenever possible
3. **Optional When Reasonable**: Make features optional if they add dependencies
4. **Well-Maintained Only**: Only depend on actively maintained projects
5. **License Compatible**: All dependencies MIT/Apache compatible

### Decisions Made
- ✅ **Removed PyYAML from core** (Phase 6.2)
  - Made optional for themes
  - Lazy loading with helpful errors
- ✅ **No YAML for .zolo parsing** (Phase 2)
  - Custom pure-Python parser
  - Zero runtime dependencies
- ✅ **No regex libraries**
  - Python's `re` module sufficient
- ✅ **No serialization libraries**
  - Custom serializer for `.zolo` format
- ✅ **No validation libraries**
  - Custom validators for `.zolo` rules

---

## 📈 Dependency Graph

```
zlsp (base install)
├── pygls>=1.3.0
│   ├── lsprotocol>=2023.0.0
│   │   ├── attrs>=21.3.0
│   │   ├── cattrs!=23.2.1
│   │   │   └── typing-extensions>=4.14.0
│   │   └── typing-extensions>=4.14.0
│   └── Python 3.8+
└── lsprotocol>=2023.0.0 (shared)

zlsp[themes] (optional)
└── pyyaml>=6.0

zlsp[dev] (optional)
├── pytest>=7.0
├── pytest-cov>=4.0
├── black>=23.0
├── mypy>=1.0
└── ruff>=0.1.0
```

---

## 🔍 Dependency Audit Results

### Security
- ✅ All dependencies actively maintained
- ✅ No known security vulnerabilities
- ✅ Regular updates from maintainers
- ✅ MIT/Apache licenses (permissive)

### Compatibility
- ✅ Python 3.8+ support
- ✅ OS Independent (pure Python)
- ✅ No C extensions required (except PyYAML, which has fallback)

### Size
- **Base install**: ~145 KB (pygls + lsprotocol wheels)
- **With themes**: ~295-445 KB (adds PyYAML)
- **Compared to**: Similar LSP servers often have 5-10+ required dependencies

### Maintenance
- `pygls`: ✅ Active (last release: 2024)
- `lsprotocol`: ✅ Active (last release: 2025)
- `pyyaml`: ✅ Active (last release: 2024)

---

## 🚀 Installation Options

### Minimal Install (LSP + Parser)
```bash
pip install zlsp
```
**Size**: ~420 KB total (including transitive deps)  
**Includes**: Full LSP, parser, Vim integration

### With Theme Support
```bash
pip install zlsp[themes]
```
**Size**: ~570-720 KB total  
**Includes**: Everything + theme loading/generation

### Development Install
```bash
pip install zlsp[dev]
```
**Includes**: Everything + testing + linting + formatting

### Full Install
```bash
pip install zlsp[all]
```
**Includes**: All optional dependencies

---

## ✅ Dependency Audit Complete

**Status**: ✅ **MINIMAL, WELL-CHOSEN DEPENDENCIES**

**Summary**:
- 2 required packages (pygls, lsprotocol)
- 1 optional package for themes (pyyaml)
- 5 optional packages for development
- Heavy use of Python standard library
- No bloat, no unnecessary dependencies
- All dependencies actively maintained
- All licenses compatible (MIT/Apache)

**Recommendation**: No changes needed. Dependency set is optimal.

---

## 📝 Future Considerations

### Could Add (But Don't Need Yet)
- [ ] `rich` - Terminal formatting (for prettier CLI output)
- [ ] `click` - CLI framework (argparse is sufficient for now)
- [ ] `toml` - TOML support (not needed, .zolo is our format)

### Will NOT Add
- ❌ YAML libraries for parsing (custom parser is better)
- ❌ JSON schema validators (custom validation is sufficient)
- ❌ Heavy frameworks (keep it minimal)
- ❌ GUI libraries (terminal-first philosophy)

---

**Last Review**: January 14, 2026  
**Next Review**: v2.0.0 or when adding new features  
**Reviewer**: Automated audit + manual review
