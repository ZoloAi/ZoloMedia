# zlsp Core

**Language-agnostic LSP implementation for .zolo files**

This directory contains the core LSP server implementation that is shared by all language bindings and editor integrations.

## Architecture

```
core/
├── server/          # LSP protocol implementation
│   ├── lsp_server.py         # Main LSP server
│   ├── lsp_types.py          # LSP type definitions
│   └── semantic_tokenizer.py # Token encoding
│
├── parser/          # Zolo parser (single source of truth)
│   ├── parser.py             # Main parser logic
│   ├── type_hints.py         # Type hint processing
│   └── constants.py          # Parser constants
│
├── providers/       # LSP feature providers
│   ├── completion_provider.py   # Autocomplete
│   ├── hover_provider.py        # Hover information
│   └── diagnostics_engine.py    # Error detection
│
└── exceptions.py    # Core exceptions
```

## Design Principles

1. **Language-agnostic** - No language-specific code
2. **Single source of truth** - Parser drives everything
3. **Shared by all** - Used by Python, C++, Java, etc. bindings
4. **LSP-first** - Follows LSP spec exactly

## Usage

This core is not meant to be used directly. Instead, use:
- **Language bindings** in `../bindings/` for SDK access
- **Editor integrations** in `../editors/` for editor support

## Features

- ✅ Semantic token highlighting
- ✅ Real-time diagnostics (error detection)
- ✅ Hover information
- ✅ Code completion
- ✅ Type hint processing
- ✅ UTF-16 position handling

## Development

The core is pure Python but designed to be wrapped by other languages:
- Python → Direct import
- C++ → Python C API or JSON-RPC
- Java → JNI or JSON-RPC
- Rust → PyO3 or JSON-RPC
