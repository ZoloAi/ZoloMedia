# Zolo Integration Guide for zKernel

> **Note**: This guide is for zKernel developers who want to use the `.zolo` parser.  
> **Status**: zlsp is now in monorepo structure. Package name is `zlsp`, not `zolo`.  
> **Updated**: January 2026 to reflect Phase 1-3 refactoring.

## Overview

The `zlsp` package provides a pure Python parser for `.zolo` files with an optional LSP server for editor support. This document explains how zKernel can integrate with zlsp's parser.

## Architecture (Current - Monorepo)

```
/ZoloMedia/zlsp/                   # Monorepo structure (pip install zlsp)
  ├── core/                        # Core implementation
  │   ├── parser/                  # Parser (public API)
  │   │   ├── parser.py            # load(), loads(), dump(), dumps(), tokenize()
  │   │   └── parser_modules/      # Modular implementation
  │   ├── providers/               # LSP providers
  │   └── server/                  # LSP server
  └── pyproject.toml               # Modern Python packaging

/zKernel/                          # zKernel framework
  └── L2_Core/g_zParser/
      └── parser_modules/
          └── parser_file.py       # Imports: from zlsp.core.parser import load, loads
```

## Integration Options

### Option 1: Use zlsp Parser (Recommended)

**zKernel imports from `zlsp` package:**

```python
# zKernel/L2_Core/g_zParser/parser_modules/parser_file.py

from zlsp.core.parser import load, loads
from zlsp.core.exceptions import ZoloParseError

def parse_file(file_path, logger):
    """Parse .zolo file using zlsp."""
    try:
        # Use zlsp parser
        data = load(file_path)
        return data
    except ZoloParseError as e:
        logger.error(f"Parse error: {e}")
        return None

def parse_string(content, logger, file_extension='.zolo'):
    """Parse string content using zlsp."""
    try:
        data = loads(content, file_extension=file_extension)
        return data
    except ZoloParseError as e:
        logger.error(f"Parse error: {e}")
        return None
```

**Benefits:**
- ✅ Clean separation of concerns
- ✅ zolo can be used by other frameworks
- ✅ zolo can be pip installed independently
- ✅ Version management via pip
- ✅ Easier testing (test zolo independently)

### Option 2: Vendored Copy (Not Recommended)

If zKernel needs a specific version, use pip with version pinning instead:

```bash
pip install zlsp==1.0.0  # Pin specific version
```

## For zKernel Developers

### Using zlsp Parser in zKernel

```python
# Simple usage
from zlsp.core.parser import load, loads, dump, dumps

# Load .zolo file (string-first)
data = load('config.zolo')

# Load .json file
data = load('config.json')

# Load from string
data = loads('port: 8080', file_extension='.zolo')

# Dump to .zolo file
dump({'port': 8080, 'host': 'localhost'}, 'output.zolo')
```

### Type Hint Processing (Automatic!)

Type hints are processed automatically by `load()` and `loads()`:

```python
# Type hints work automatically
data = loads('port(int): 8080')  # Returns {'port': 8080} (int, not string!)
```

### Exception Handling

```python
from zlsp.core.exceptions import ZoloParseError, ZoloDumpError

try:
    data = load('config.zolo')
except ZoloParseError as e:
    logger.error(f"Failed to parse: {e}")
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
```

## Installation

### For Development

```bash
# Install zlsp in editable mode from monorepo
cd /path/to/ZoloMedia/zlsp
pip install -e .
```

### For Production (when published)

```bash
# Install from PyPI or GitHub
pip install zlsp

# Or from GitHub monorepo
pip install git+https://github.com/ZoloAi/ZoloMedia.git#subdirectory=zlsp
```

### For zKernel

Add to `pyproject.toml` or `requirements.txt`:

```toml
# pyproject.toml
dependencies = [
    "zlsp>=1.0.0",
    # ... other deps
]
```

## Integration Status

### ✅ Phase 1-3: Refactoring (Done)
- Parser modularized (2,700 → 364 lines, +13 modules)
- Providers modularized (820 → 231 lines, +4 modules)
- 261 tests, 63% coverage
- Industry-grade architecture

### 🔜 Phase 4-5: Documentation & Testing (Current)
- Update documentation for modular structure
- Add integration tests
- Expand coverage strategically
- Test zKernel still works with standalone zolo

### Phase 3: Publish (Future)
- Publish `zolo` to PyPI
- Update zKernel dependencies to use `pip install zolo`
- Update documentation

### Phase 4: IDE Support (Future)
- VSCode extension references standalone zolo spec
- Syntax validation uses zolo parser
- Auto-completion based on zolo types

## Testing

### Test Standalone Zolo

```bash
cd /path/to/zolo-zcli/zolo
python -m pytest tests/ -v
```

### Test Integration with zKernel

```bash
cd /path/to/zolo-zcli
python -m pytest zTestRunner/ -v
```

## Publishing to PyPI

### Build Package

```bash
cd /path/to/zolo-zcli/zolo
python -m build
```

### Upload to PyPI

```bash
python -m twine upload dist/*
```

## Benefits of Standalone Architecture

1. **Framework Agnostic**: Any Python app can use zolo
2. **Version Management**: `pip install zolo==1.0.0`
3. **IDE Integration**: VSCode/PyCharm can validate .zolo files
4. **OS-Level Recognition**: .zolo becomes a recognized format
5. **Cleaner zKernel**: zKernel focuses on framework, zlsp on parsing
6. **Python → JavaScript**: Python parses, JavaScript consumes

## Next Steps

1. ✅ Create standalone `/zolo/` package
2. ⏳ Update zKernel to use `import zolo`
3. ⏳ Test integration
4. ⏳ Publish to PyPI (optional)
5. ⏳ Update VSCode extension to use zolo spec

---

**Version:** 1.0  
**Last Updated:** 2026-01-05
