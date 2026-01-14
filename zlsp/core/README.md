# zlsp Core

**Language-agnostic LSP implementation for .zolo files**

This directory contains the core LSP server implementation that is shared by all language bindings and editor integrations.

## Architecture

```
core/
├── server/          # LSP protocol implementation
│   ├── lsp_server.py         # Main LSP server (367 lines)
│   ├── lsp_types.py          # LSP type definitions
│   └── semantic_tokenizer.py # Token encoding
│
├── parser/          # Zolo parser (modular architecture!)
│   ├── parser.py             # Public API (364 lines - thin orchestration)
│   ├── constants.py          # Parser constants
│   └── parser_modules/       # ⭐ Modular implementation (Phase 2)
│       ├── line_parsers.py         # Core parsing (843 lines)
│       ├── token_emitter.py        # Token emission (171 lines)
│       ├── block_tracker.py        # Context tracking (71 lines)
│       ├── key_detector.py         # Key classification (98 lines)
│       ├── file_type_detector.py   # File type detection (61 lines)
│       ├── value_validators.py     # Value validation (53 lines)
│       ├── serializer.py           # .zolo serialization (56 lines)
│       ├── type_hints.py           # Type hint processing (60 lines)
│       └── + 5 more utility modules
│
├── providers/       # LSP feature providers (thin wrappers!)
│   ├── completion_provider.py   # Autocomplete (62 lines - was 301!)
│   ├── hover_provider.py        # Hover info (55 lines - was 285!)
│   ├── diagnostics_engine.py    # Diagnostics (114 lines - was 234!)
│   └── provider_modules/         # ⭐ Modular implementation (Phase 3)
│       ├── documentation_registry.py  # SSOT for docs (263 lines, 98% cov)
│       ├── completion_registry.py     # Context-aware (321 lines, 100% cov)
│       ├── hover_renderer.py          # Hover formatting (266 lines, 88% cov)
│       └── diagnostic_formatter.py    # Error formatting (239 lines, 97% cov)
│
├── exceptions.py    # Core exceptions
└── version.py       # Package version
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
