# zLSP - Language Server Protocol for .zolo Files

**Language Server Protocol implementation for `.zolo` declarative configuration files**

## About

**zlsp** provides full LSP (Language Server Protocol) support for `.zolo` files with semantic highlighting, diagnostics, hover information, and code completion. Built on a pure LSP architecture where the parser is the single source of truth.

The `.zolo` format serves dual purposes: as a **generic replacement** for JSON, YAML, and TOML in any configuration context, ***and*** as the foundation for **ZoloMedia's zEcosystem**.

Browse to [**basic.zolo**](examples/basic.zolo) or [**advanced.zolo**](examples/advanced.zolo) for syntax and structure examples.

>**Note**: See [**zOS README**](../zOS/README.md) for the complete picture of zSpecial syntax and ecosystem integration.

## Requirements

- **Python 3.8+**
- **pygls 1.3.0+** (LSP framework)
- **lsprotocol 2023.0.0+** (LSP types)

For Vim:
- **Neovim 0.8+** (built-in LSP) OR
- **Vim 9+** with vim-lsp plugin

For VSCode/Cursor:
- **VSCode 1.50+** OR **Cursor** (any recent version)
- Both have built-in LSP support

## Installation

In Terminal run the following command:

```bash
pip install zlsp
```

Then install for your editor:

```bash
zlsp-install-all      # Install for all supported editors
zlsp-install-vim      # Automated Vim/Neovim integration
zlsp-install-vscode   # Automated VSCode integration
zlsp-install-cursor   # Automated Cursor integration
```

## Verify Installation

After installation, verify everything is working:

```bash
zlsp verify              # Quick health check
zlsp verify --verbose    # Detailed check with all components
```

This runs 5 essential checks:
- ✓ Python version compatibility
- ✓ Core dependencies (pygls, lsprotocol)
- ✓ Parser functionality
- ✓ LSP server availability
- ✓ Semantic tokenizer

If anything fails, you'll get clear error messages with suggested fixes. Exit code 0 means success, 1 means issues found.

> For installation troubleshoots see: [**INSTALLATION.md**](Documentation/INSTALLATION.md)
## Features

- **String-First Philosophy** - Values are strings by default with explicit type hints as needed
- **Pure LSP Architecture** - Parser is the source of truth, no grammar files
- **Editor Agnostic** - Works with Vim, VSCode, Cursor, and any LSP-compatible editor
- **Semantic Highlighting** - Context-aware syntax coloring
- **Real-Time Diagnostics** - Syntax errors and type validation
- **Code Completion** - Type hints and value suggestions
- **Hover Information** - Inline documentation and type information

## Why .zolo?

Configuration files consume significant space in LLM contexts.  
When you're working with AI assistants or processing configs at scale, every token counts.  
**The `.zolo` format is designed with this reality in mind.**

**Token Comparison** (measured from [**advanced.zolo**](examples/advanced.zolo) - 400 lines of real-world config):

| Format | Tokens | vs JSON | Why? |
|--------|--------|---------|------|
| **JSON** (baseline) | 7,358 | — | Industry standard, but verbose with `{}`, `[]`, `""` everywhere |
| YAML | 4,905 | 33% smaller | Clean syntax, but ambiguous (`yes` = `true`, bare strings behave unpredictably) |
| TOML | 5,813 | 21% smaller | Explicit types, but repetitive `[section.headers]` for nesting |
| **`.zolo`** | **4,542** | **38% smaller** | **String-first, explicit types, minimal syntax** |

**What does 38% token reduction mean?**

In practical terms, a typical application configuration that consumes **7,358 tokens in JSON** requires only **4,542 tokens in .zolo**.  
**That's 2,816 tokens saved** - enough space for several additional prompts or responses in an LLM conversation.

**Scale Amplifies Savings** - The more files you process, the more tokens you save (Impact Multiplier shows the growing benefit):

| Scale | JSON Tokens | .zolo Tokens | Tokens Saved | Impact Multiplier | Equivalent To |
|-------|-------------|--------------|--------------|-------------------|---------------|
| 1 file | 7,358 | 4,542 | 2,816 | 1x | ~4 LLM prompts |
| 10 files | 73,580 | 45,420 | 28,160 | 10x | ~40 prompts |
| 100 files | 735,800 | 454,200 | 281,600 | 100x | ~400 prompts |
| 1,000 files | 7,358,000 | 4,542,000 | 2,816,000 | 1,000x | ~4,000 prompts |

**What this means for you:**
- **Save 38% on AI API bills** - Every token you don't send is money saved
- **Fit more in AI conversations** - More room for your actual data and prompts
- **Faster load times** - Smaller files process quicker
- **Easier to read** - Less clutter, more clarity

**Why not just use YAML?**

YAML achieves similar token efficiency (33% reduction) but introduces ambiguity that causes production issues:
- `yes`, `no`, `on`, `off` auto-convert to booleans
- Bare strings like `true` or `false` become booleans unexpectedly
- The infamous "Norway problem" where country code `no` becomes `false`
- Implicit type conversions lead to bugs

>**Suggested reading:** [The yaml document from hell](https://ruudvanasseldonk.com/2023/01/11/the-yaml-document-from-hell) - A comprehensive breakdown of YAML's footguns and unexpected behaviors.

`.zolo` takes a different approach: **string-first with explicit types**. Only `true` and `false` are booleans, everything else is a string. This eliminates ambiguity while maintaining readability and token efficiency - a practical format for both humans and machines.

## String-First Philosophy

zLSP's core design: **values are strings by default**, with explicit type hints for conversion.

```zolo
# Strings (default)
name: Zolo
description: A declarative config format

# Explicit type conversion
version(float): 1.0
port(int): 8080
enabled(bool): true

# Force string (even if looks like number)
id(str): 12345

# Null values
empty(null):
```

**Why String-First?**
- Strings are the most common value type in declarative files, especially in the LLM era
- Optimized for the actual use case (text, paths, commands, descriptions)
- Side benefit: eliminates ambiguity (no `yes` = `true` confusion)
- Explicit type hints when you need other types


## Architecture

zLSP follows modern Language Server Protocol best practices:

```
Parser (parser.py)
    ↓
LSP Server (lsp_server.py)
    ↓
Editor Clients (vim-lsp, VSCode LSP)
```

**Key Principles:**
- Single source of truth (parser)
- Thin LSP wrapper
- No duplicate grammar files
- Editor-agnostic protocol

## Usage as Parser

```python
from zlsp.core.parser import load, loads, dump, dumps

# Load from file
data = load('config.zolo')

# Load from string
data = loads('''
name: Zolo
version(float): 1.0
enabled(bool): true
''')
# → {'name': 'Zolo', 'version': 1.0, 'enabled': True}

# Write to file
dump(data, 'output.zolo')

# Write to string
text = dumps(data)
```

## zLSP Advanced Features

zLSP server provides all the expected industry-grade features:

### Semantic Highlighting
- Keys, values, and comments colored by parser
- Context-aware for special file types (zConfig, zEnv, zSpark)
- Type hints highlighted

### Diagnostics
- Syntax errors (duplicate keys, invalid format)
- Type mismatches (e.g., `port(int): abc`)
- Real-time error reporting

### Hover Information
- Type hint documentation
- Value type detection
- Key descriptions

### Code Completion
- Type hints: `(int)`, `(float)`, `(bool)`, `(str)`, `(null)`
- Common values: `true`, `false`, `null`
- Context-aware suggestions

## Project Structure

```
zlsp/
├── core/              # Core LSP implementation
│   ├── server/        # LSP protocol handlers
│   ├── parser/        # Parser implementation
│   └── providers/     # Completion, hover, diagnostics
├── editors/           # Editor integrations
│   ├── vim/           # Vim/Neovim integration
│   ├── vscode/        # VSCode integration
│   └── cursor/        # Cursor IDE integration
├── themes/            # Color themes
│   ├── zolo_default.yaml    # Canonical theme
│   └── generators/          # Editor-specific generators
├── examples/          # Example .zolo files
└── Documentation/     # Full documentation
```

## Documentation

### Getting Started
- [INSTALLATION.md](Documentation/INSTALLATION.md) - Detailed installation guide
- [basic.zolo](examples/basic.zolo) - Simple syntax examples
- [advanced.zolo](examples/advanced.zolo) - Real-world configuration example

### Core Documentation
- [ARCHITECTURE.md](Documentation/ARCHITECTURE.md) - Design and architecture
- [FILE_TYPES.md](Documentation/FILE_TYPES.md) - File type detection and LSP features

### Editor Integration
- [editors/vim/README.md](editors/vim/README.md) - Vim/Neovim setup
- [editors/vscode/README.md](editors/vscode/README.md) - VSCode setup
- [editors/cursor/README.md](editors/cursor/README.md) - Cursor IDE setup


## Development

```bash
# Clone repository
git clone https://github.com/ZoloAi/ZoloMedia.git
cd ZoloMedia/zlsp

# Install in editable mode
pip install -e .

# Install for your editor
zlsp-install-vim  # or zlsp-install-vscode

# Run tests
pytest tests/

# Test parser
python3 -c "from zlsp.core.parser import loads; print(loads('key: value'))"

# Start LSP server
zolo-lsp
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Test specific module
pytest tests/unit/test_parser.py
```

## Contributing

**Core Principle:** Keep the parser as the single source of truth.

- New syntax? → Update parser
- New highlighting? → Update tokenizer
- New LSP feature? → Add provider that uses parser

**Never:** Duplicate parsing logic in grammar files or LSP server.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Credits

Built with:
- [pygls](https://github.com/openlawlibrary/pygls) - Python LSP framework
