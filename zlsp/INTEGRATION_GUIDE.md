# Zolo Integration Guide for zKernel

## Overview

The `zolo` library is now a **standalone package** that can be used independently of zKernel. This document explains how zKernel integrates with the standalone `zolo` library.

## Architecture

```
/zolo/                          # Standalone library (pip installable)
  ├── __init__.py              # Public API
  ├── parser.py                # Core parsing
  ├── type_hints.py            # Type hint processing
  ├── constants.py             # Constants
  └── exceptions.py            # Exceptions

/zKernel/                          # zKernel framework
  └── L2_Core/g_zParser/
      └── parser_modules/
          └── parser_file.py   # Imports: import zolo (or from zolo import ...)
```

## Integration Options

### Option 1: Use Standalone Zolo (Recommended)

**zKernel imports from standalone `zolo` library:**

```python
# zKernel/L2_Core/g_zParser/parser_modules/parser_file.py

import zolo
from zolo.exceptions import ZoloParseError

def parse_yaml(raw_content, logger, file_extension=None):
    """Parse YAML/Zolo content."""
    try:
        # Use standalone zolo library
        string_first = (file_extension == '.zolo')
        parsed = yaml.safe_load(raw_content)
        
        # Import type hint processor from zolo
        from zolo.type_hints import process_type_hints
        parsed = process_type_hints(parsed, string_first=string_first)
        
        return parsed
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

### Option 2: Vendored Copy (If Needed)

If zKernel needs a specific version or modifications:

```
/zKernel/
  └── vendor/
      └── zolo/          # Vendored copy of zolo
```

## For zKernel Developers

### Using Zolo in zKernel

```python
# Simple usage
import zolo

# Load .zolo file (string-first)
data = zolo.load('config.zolo')

# Load .yaml file (native types)
data = zolo.load('config.yaml')

# Load from string
data = zolo.loads('port: 8080', file_extension='.zolo')
```

### Type Hint Processing

```python
from zolo.type_hints import process_type_hints

# After YAML parsing, apply type hints
parsed = yaml.safe_load(content)
parsed = process_type_hints(parsed, string_first=True)  # For .zolo
parsed = process_type_hints(parsed, string_first=False)  # For .yaml
```

### Exception Handling

```python
from zolo.exceptions import ZoloParseError, ZoloTypeError

try:
    data = zolo.load('config.zolo')
except ZoloParseError as e:
    logger.error(f"Failed to parse: {e}")
except ZoloTypeError as e:
    logger.error(f"Type conversion error: {e}")
```

## Installation

### For Development

```bash
# Install zolo in editable mode from local directory
pip install -e /path/to/zolo-zcli/zolo
```

### For Production

```bash
# Install from PyPI (when published)
pip install zolo
```

### For zKernel

Add to `pyproject.toml` or `requirements.txt`:

```toml
# pyproject.toml
dependencies = [
    "zolo>=1.0.0",
    # ... other deps
]
```

## Migration Path

### Phase 1: Extract (✅ Done)
- Create standalone `/zolo/` directory
- Move type hint logic to `zolo/type_hints.py`
- Create clean API in `zolo/parser.py`
- Add tests and examples

### Phase 2: Update zKernel (Current)
- Update `zKernel/L2_Core/g_zParser/parser_modules/parser_file.py`
- Replace internal logic with `import zolo`
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
5. **Cross-Language**: Easier to port to JS, Go, Rust, etc.
6. **Cleaner zKernel**: zKernel focuses on framework, zolo on parsing

## Next Steps

1. ✅ Create standalone `/zolo/` package
2. ⏳ Update zKernel to use `import zolo`
3. ⏳ Test integration
4. ⏳ Publish to PyPI (optional)
5. ⏳ Update VSCode extension to use zolo spec

---

**Version:** 1.0  
**Last Updated:** 2026-01-05
