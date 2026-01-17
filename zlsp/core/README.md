# zlsp Core

**Pure Python LSP implementation for .zolo files**

This directory contains the core LSP server implementation that powers editor integrations.

## Architecture

```
core/
├── server/          # LSP protocol implementation
│   ├── lsp_server.py         # Main LSP server
│   ├── lsp_types.py          # LSP type definitions
│   └── semantic_tokenizer.py # Token encoding
│
├── parser/          # Zolo parser (modular architecture)
│   ├── parser.py             # Public API
│   ├── constants.py          # Parser constants
│   └── parser_modules/       # Modular implementation
│       ├── line_parsers.py         # Core parsing
│       ├── token_emitter.py        # Token emission
│       ├── block_tracker.py        # Context tracking
│       ├── key_detector.py         # Key classification
│       ├── file_type_detector.py   # File type detection
│       ├── value_validators.py     # Value validation
│       ├── serializer.py           # .zolo serialization
│       ├── type_hints.py           # Type hint processing
│       └── escape_processors.py    # Escape sequence handling
│       └── ... (additional modules)
│
├── providers/       # LSP feature providers
│   ├── completion_provider.py   # Autocomplete
│   ├── hover_provider.py        # Hover information
│   ├── diagnostics_engine.py    # Diagnostics
│   └── provider_modules/        # Modular implementation
│       ├── documentation_registry.py  # Documentation source of truth
│       ├── completion_registry.py     # Context-aware completions
│       ├── hover_renderer.py          # Hover formatting
│       └── diagnostic_formatter.py    # Error formatting
│
├── cli.py           # CLI commands
├── exceptions.py    # Core exceptions
└── version.py       # Package version
```

## Design Principles

1. **Pure Python** - Clean, well-tested implementation
2. **Single source of truth** - Parser drives everything
3. **LSP-first** - Follows LSP spec exactly
4. **Modular** - Clear separation of concerns

## Usage

Import directly from core:
```python
from core.parser import loads, dumps
from core.exceptions import ZoloParseError
```

Or use **Editor integrations** in `../editors/` for LSP support

## Features

- Semantic token highlighting
- Real-time diagnostics (error detection)
- Hover information
- Code completion
- Type hint processing
- UTF-16 position handling

## Development

The core is pure Python:
- Direct imports for Python applications
- LSP server for editor integrations
- Well-documented API for extensions
