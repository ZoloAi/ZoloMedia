# Zolo LSP

**Language Server Protocol implementation for `.zolo` declarative files**

Pure LSP architecture following the TOML model: single source of truth (parser) → LSP wrapper → thin editor clients.

## Features

- **String-First Philosophy** - Values are strings by default, with explicit type hints
- **Pure LSP** - No grammar files, parser is the source of truth
- **Terminal-First** - Perfect Vim/Neovim support (Phase 1)
- **Editor Agnostic** - Same LSP server for all editors (Vim, VS Code, IntelliJ)
- **Multi-Language Support** - Python SDK (ready), C++/Java/Rust (planned)

## Project Structure

```
zlsp/
├── core/          # Language-agnostic LSP implementation
│   ├── server/    # LSP protocol, semantic tokens
│   ├── parser/    # Zolo parser (single source of truth)
│   └── providers/ # Completion, hover, diagnostics
│
├── bindings/      # Language-specific SDKs
│   └── python/    # Python SDK ✅ (ready)
│       └── zlsp/  # pip install zlsp
│
├── editors/       # Editor integrations
│   └── vim/       # Vim integration ✅ (ready)
│
└── Documentation/ # All documentation
    ├── bindings/  # Per-language guides
    └── editors/   # Per-editor guides
```

**Design:** Each folder (`core/`, `bindings/python/`, `editors/vim/`) can be extracted to its own repository when ready for publication. The monorepo structure makes development easier!

## Quick Start

### Installation (One Command!)

**From PyPI (Production):**

```bash
# Install and setup - that's it!
pip install zlsp && zolo-vim-install
```

**From GitHub (Development):**

```bash
# Install from monorepo
pip install git+https://github.com/ZoloAi/Zolo.git#subdirectory=zLSP && zolo-vim-install
```

**Local Development:**

```bash
cd zlsp
pip install -e . && zolo-vim-install
```

### What Gets Installed (Automatically)

The `zolo-vim-install` command:
1. ✅ Installs Vim plugin files to `~/.vim/` or `~/.config/nvim/`
2. ✅ **Detects Vim version** and auto-installs vim-lsp if needed (Vim 9+)
3. ✅ **Sets up vim-plug** and configures your `~/.vimrc` (with backup)
4. ✅ Verifies `zolo-lsp` server is available

**No manual steps required!** Just run and use.

### Vim/Neovim Support

**Neovim 0.8+:** Built-in LSP - works automatically!
```bash
nvim test.zolo  # Just works! 🎉
```

**Vim 9+:** Auto-configured with vim-lsp during installation
```bash
vim test.zolo  # LSP enabled automatically! 🎉
```

**Vim 8 or older:** Basic syntax highlighting (no LSP)
```bash
vim test.zolo  # Basic colors only
# Recommendation: Upgrade to Vim 9+ or use Neovim
```

See [`zlsp/vim/README.md`](zlsp/vim/README.md) for troubleshooting and advanced setup.

## String-First Philosophy

Zolo's core innovation: **values are strings by default**, with explicit type hints for conversion.

```zolo
# String (default)
name: Zolo
description: A declarative config format

# Explicit type conversion
version(float): 1.0
port(int): 8080
enabled(bool): true
timeout(float): 30.5

# Force string (even if looks like number)
id(str): 12345
code(str): 007

# Null values
empty(null):
```

**Why String-First?**
- **No ambiguity** - YAML's `yes` = `true` problem doesn't exist
- **Explicit > Implicit** - Clear intent, no surprises
- **Easy to understand** - What you see is what you get

## Architecture

```
┌─────────────────────┐
│   parser.py         │  ← Single source of truth
│   (String-first)    │     • tokenize() → semantic tokens
└──────────┬──────────┘     • load/loads() → parse data
           │                • dump/dumps() → write data
           ↓
┌─────────────────────┐
│   lsp_server.py     │  ← Thin wrapper
│   (LSP Protocol)    │     Provides ALL features:
└──────────┬──────────┘     • Semantic highlighting
           │                • Diagnostics
           │                • Completion
           ↓                • Hover
    ┌──────┴──────┐
    ↓             ↓
┌────────┐    ┌────────┐
│  Vim   │    │ VS Code│  ← Thin LSP clients
│  LSP   │    │ (Phase │    (No grammar files!)
└────────┘    └───2)───┘
```

**No grammar files.** The parser provides semantic tokens directly to the LSP, which editors consume.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for detailed design docs.

## LSP Features

All features come from the LSP (no grammar files):

### ✅ Semantic Highlighting
- Keys, values, comments colored by parser
- Context-aware (zUI, zConfig, zEnv files)
- Type hints highlighted

### ✅ Diagnostics
- Syntax errors (duplicate keys, invalid YAML)
- Type mismatches (e.g., `port(int): abc`)
- Real-time error reporting

### ✅ Hover Information
- Type hint documentation
- Value type detection
- Key descriptions

### ✅ Code Completion
- Type hints: `(int)`, `(float)`, `(bool)`, etc.
- Common values: `true`, `false`, `null`
- Context-aware suggestions

## Usage

### As a Parser

```python
from zolo import load, loads, dump, dumps

# Load from file
data = load('config.zolo')

# Load from string
data = loads('''
name: Zolo
version(float): 1.0
enabled(bool): true
''')
# → {'name': 'Zolo', 'version': 1.0, 'enabled': True}

# Dump to file
dump(data, 'output.zolo')

# Dump to string
text = dumps(data)
```

### As an LSP Server

The `zolo-lsp` command starts the LSP server:

```bash
zolo-lsp
```

Editors connect to it automatically when you open a `.zolo` file.

## File Structure

```
zLSP/
├── src/zolo/
│   ├── parser.py              ← THE BRAIN (2,700+ lines)
│   ├── lsp_server.py          ← LSP wrapper (~350 lines)
│   ├── semantic_tokenizer.py  ← Token encoding
│   ├── lsp_types.py           ← Type definitions
│   ├── type_hints.py          ← String-first type system
│   ├── constants.py           ← Shared constants
│   ├── exceptions.py          ← Error types
│   ├── providers/             ← LSP feature providers
│   └── vim/                   ← Vim integration (Phase 1)
├── tests/                     ← Unit tests
├── examples/                  ← Example .zolo files
├── docs/                      ← Documentation
└── README.md                  ← This file
```

## Comparison to Other Languages

Zolo follows the same architecture as modern language servers:

| Language | Parser | LSP Server | Pattern |
|----------|--------|------------|---------|
| **TOML** | `toml` crate (Rust) | `taplo-lsp` | ✅ Same as Zolo |
| **Rust** | `rustc` parser | `rust-analyzer` | ✅ Same as Zolo |
| **YAML** | `yaml` (JS) | `yaml-language-server` | ✅ Same as Zolo |
| **Zolo** | `parser.py` | `zolo-lsp` | ✅ Pure LSP |

**We're in good company!**

## Roadmap

### ✅ Phase 1: Terminal-First (DONE)
- [x] Parser with string-first logic
- [x] LSP server wrapping parser
- [x] Vim LSP client configuration
- [x] Installation script
- [x] Documentation

### 🔜 Phase 2: VS Code (Future)
- [ ] VS Code extension (thin LSP client)
- [ ] Marketplace publishing
- [ ] Same LSP server, different client

### 🔜 Phase 3: Other Editors (Future)
- [ ] IntelliJ plugin
- [ ] Sublime Text
- [ ] Emacs

### 🔜 Phase 4: Advanced Features (Future)
- [ ] Go-to-definition
- [ ] Find references
- [ ] Rename refactoring
- [ ] Code actions

## Testing

```bash
# Run unit tests
pytest tests/

# Test parser
python3 -c "from zolo import loads; print(loads('key: value'))"

# Test LSP server
zolo-lsp --help

# Test in Vim
cd src/zolo/vim
./install.sh
nvim test.zolo
```

## Requirements

- **Python 3.8+**
- **pygls 1.3.0+** (LSP framework)
- **pyyaml 6.0+** (YAML compatibility)

For Vim:
- **Neovim 0.8+** (built-in LSP) OR
- **Vim 9+** with [vim-lsp](https://github.com/prabirshrestha/vim-lsp) plugin

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) - Detailed design docs
- [`src/zolo/vim/README.md`](src/zolo/vim/README.md) - Vim setup guide
- [`examples/`](examples/) - Example .zolo files

## Contributing

**Core principle:** Keep `parser.py` as the single source of truth.

- New syntax? → Add to `parser.py`
- New highlighting? → Update `tokenize()` in `parser.py`
- New LSP feature? → Add provider that calls `parser.py`

**Never:** Duplicate parsing logic in grammar files or LSP server.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Credits

Inspired by:
- [taplo](https://github.com/tamasfe/taplo) - TOML LSP
- [rust-analyzer](https://github.com/rust-lang/rust-analyzer) - Rust LSP
- [yaml-language-server](https://github.com/redhat-developer/yaml-language-server) - YAML LSP

Built with:
- [pygls](https://github.com/openlawlibrary/pygls) - Python LSP framework
- [PyYAML](https://pyyaml.org/) - YAML parser
