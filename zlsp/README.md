# Zolo LSP

**Language Server Protocol implementation for `.zolo` declarative files**

Pure LSP architecture following the TOML model: single source of truth (parser) → LSP wrapper → thin editor clients.

## Features

- **String-First Philosophy** - Values are strings by default, with explicit type hints
- **Pure LSP** - No grammar files, parser is the source of truth
- **Terminal-First** - Perfect Vim/Neovim support (Phase 1)
- **Editor Agnostic** - Same LSP server for all editors (Vim, VS Code, IntelliJ)
- **Multi-Language Support** - Python SDK (ready), C++/Java/Rust (planned)
- **Industry-Grade Architecture** - Modular, tested, maintainable (see below!)

## Recent Improvements (January 2026)

🎉 **Major Milestones Achieved!** The codebase has been transformed to industry-grade standards:

### Phase 1-3 Achievements (Parser & Providers):
- ✅ **Parser Modularization**: Broke monolithic 2,700-line parser into 13 focused modules (364-line thin API)
  - Each module <500 lines for maintainability
  - Extracted: BlockTracker, FileTypeDetector, KeyDetector, ValueValidator
  - Removed YAML dependency - pure .zolo format!

- ✅ **Provider Modularization**: Refactored all providers (72% code reduction!)
  - hover_provider: 285 → 55 lines (-81%)
  - completion_provider: 301 → 62 lines (-79%)
  - diagnostics_engine: 234 → 114 lines (-51%)
  - Zero duplication through DocumentationRegistry (SSOT)

- ✅ **Test Coverage**: Expanded from 162 → 494 tests
  - 80% overall coverage
  - Strategic testing of real-world scenarios
  - All 5 special file types validated

### Phase 7.1 Achievements (VS Code Integration):
- ✅ **VS Code Support**: Full editor integration with zero-config installation
  - Theme generator: 544 lines, 17 tests passing
  - Python-based installer (no npm/TypeScript dependencies!)
  - Settings injection for automatic color configuration
  - Works with ANY VS Code theme (Dark+, Light+, Monokai, etc.)

- ✅ **Industry Innovation**: Settings injection approach
  - Traditional LSPs: Manual theme activation required
  - zlsp: True zero-config (install → reload → done!)
  - Colors match Vim exactly (single source of truth)

**Result**: Clean, maintainable, industry-grade codebase with dual-editor support!

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
│   ├── vim/       # Vim integration ✅ (ready)
│   └── vscode/    # VS Code integration ✅ (ready)
│
├── themes/        # Theme system (single source of truth)
│   ├── zolo_default.yaml    # Canonical color theme
│   └── generators/          # Editor-specific generators
│       ├── vim.py           # Generates Vim ANSI highlights
│       └── vscode.py        # Generates VS Code JSON rules
│
└── Documentation/ # All documentation
    ├── bindings/  # Per-language guides
    └── editors/   # Per-editor guides
```

**Design:** Each folder (`core/`, `bindings/python/`, `editors/vim/`, `editors/vscode/`) can be extracted to its own repository when ready for publication. The monorepo structure makes development easier!

## Quick Start

### Installation (One Command!)

**From PyPI (Production):**

```bash
# Install zlsp
pip install zlsp

# Choose your editor:
zlsp-vim-install      # For Vim/Neovim
zlsp-vscode-install   # For VS Code
```

**From GitHub (Development):**

```bash
# Install from monorepo
pip install git+https://github.com/ZoloAi/Zolo.git#subdirectory=zLSP

# Choose your editor:
zlsp-vim-install      # For Vim/Neovim
zlsp-vscode-install   # For VS Code
```

**Local Development:**

```bash
cd zlsp
pip install -e .

# Choose your editor:
zlsp-vim-install      # For Vim/Neovim
zlsp-vscode-install   # For VS Code
```

---

### Vim/Neovim Support

**Installation:**
```bash
pip install zlsp
zlsp-vim-install
```

**What Gets Installed:**
1. ✅ Installs Vim plugin files to `~/.vim/` or `~/.config/nvim/`
2. ✅ **Detects Vim version** and auto-installs vim-lsp if needed (Vim 9+)
3. ✅ **Sets up vim-plug** and configures your `~/.vimrc` (with backup)
4. ✅ Verifies `zolo-lsp` server is available

**Usage:**

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

See [`editors/vim/README.md`](editors/vim/README.md) for troubleshooting and advanced setup.

---

### VS Code Support

**Installation:**
```bash
pip install zlsp
zlsp-vscode-install
```

Then reload VS Code: `Cmd+Shift+P` → "Reload Window"

**What Gets Installed:**
1. ✅ Extension to `~/.vscode/extensions/zolo-lsp-1.0.0/`
2. ✅ **Semantic token colors injected** into your `settings.json`
3. ✅ **Works with ANY theme** (Dark+, Light+, Monokai, your favorite!)
4. ✅ Verifies `zolo-lsp` server is available

**Key Innovation:** Settings injection means **zero manual configuration**:
- ✅ No theme activation required
- ✅ Works with your existing theme
- ✅ Colors match Vim exactly (single source of truth)
- ✅ Persistent across all sessions

**Usage:**
```bash
code test.zolo  # Full LSP support with beautiful colors! 🎉
```

See [`editors/vscode/README.md`](editors/vscode/README.md) for troubleshooting and advanced setup.

---

**Both editors supported with identical colors!** The LSP server is the same, only the client differs.

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
┌─────────────────────────────────────────┐
│   themes/zolo_default.yaml              │  ← Single Source of Truth (Colors)
│   (40 semantic token definitions)       │
└─────────────────┬───────────────────────┘
                  ↓
        ┌─────────┴─────────┐
        ↓                    ↓
┌──────────────┐    ┌──────────────┐
│ vim.py       │    │ vscode.py    │  ← Theme Generators
│ (ANSI codes) │    │ (JSON rules) │
└──────────────┘    └──────────────┘
        │                    │
        ↓                    ↓
    ~/.vim/          settings.json

┌─────────────────────┐
│   parser.py         │  ← Single Source of Truth (Parsing)
│   (String-first)    │     • tokenize() → semantic tokens
└──────────┬──────────┘     • load/loads() → parse data
           │                • dump/dumps() → write data
           ↓
┌─────────────────────┐
│   lsp_server.py     │  ← Thin LSP Wrapper
│   (LSP Protocol)    │     Provides ALL features:
└──────────┬──────────┘     • Semantic highlighting
           │                • Diagnostics
           │                • Completion
           ↓                • Hover
    ┌──────┴──────┐
    ↓             ↓
┌────────┐    ┌────────┐
│  Vim   │    │ VS Code│  ← Thin LSP Clients
│  LSP   │    │  LSP   │    (No grammar files!)
└────────┘    └────────┘
    ✅             ✅
```

**Key Principles:**
- **Two Single Sources of Truth**: `zolo_default.yaml` (colors) + `parser.py` (parsing)
- **Smart Adapters**: Different mechanisms for each editor, same colors
- **No grammar files**: Parser provides semantic tokens directly to LSP
- **Zero config**: Install → reload → done!

See [`Documentation/ARCHITECTURE.md`](Documentation/ARCHITECTURE.md) for detailed design docs.

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

## Editor Support Comparison

zlsp provides **identical functionality** across both supported editors:

| Feature | Vim/Neovim | VS Code | Implementation |
|---------|------------|---------|----------------|
| **Semantic Highlighting** | ✅ ANSI colors | ✅ JSON rules | Same LSP server |
| **Diagnostics** | ✅ Real-time | ✅ Real-time | Same LSP server |
| **Hover Info** | ✅ `K` | ✅ Mouse hover | Same LSP server |
| **Completion** | ✅ `Ctrl+N` | ✅ `Ctrl+Space` | Same LSP server |
| **Installation** | `zlsp-vim-install` | `zlsp-vscode-install` | Python installers |
| **Theme Activation** | ✅ None needed | ✅ None needed | Auto-config |
| **Color Consistency** | ✅ Matches VS Code | ✅ Matches Vim | Single source of truth |
| **Manual Setup** | ❌ Zero | ❌ Zero | True zero-config |

**Key Insight:** Same LSP server (`zolo-lsp`), different thin clients. Colors from one theme (`zolo_default.yaml`).

---

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

### ✅ Phase 1-6: Core & Vim (DONE)
- [x] Parser with string-first logic (modularized to 13 modules)
- [x] LSP server wrapping parser (thin architecture)
- [x] Provider modularization (72% code reduction)
- [x] Test coverage expansion (494 tests, 80% coverage)
- [x] Vim LSP client configuration
- [x] Installation script (`zlsp-vim-install`)
- [x] Comprehensive documentation
- [x] PyPI distribution

### ✅ Phase 7.1: VS Code Integration (DONE)
- [x] VS Code theme generator (544 lines, theme-driven)
- [x] Python-based installer (`zlsp-vscode-install`)
- [x] Settings injection for zero-config experience
- [x] Works with ANY VS Code theme
- [x] Same LSP server, different client
- [x] Documentation

**🎉 Both Vim and VS Code fully supported!**

### 📋 Phase 7.2+: Future Enhancements
- [ ] **Marketplace Publishing** (VS Code Marketplace)
- [ ] **Other Editors**: IntelliJ, Sublime Text, Emacs
- [ ] **Advanced LSP Features**:
  - [ ] Go-to-definition
  - [ ] Find references
  - [ ] Rename refactoring
  - [ ] Code actions
- [ ] **Performance Optimization** (if benchmarks show need)
- [ ] **Parser Enhancements** (user-driven)

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

### Getting Started
- [`Documentation/QUICKSTART.md`](Documentation/QUICKSTART.md) - Get started in 5 minutes
- [`Documentation/INSTALLATION.md`](Documentation/INSTALLATION.md) - Detailed installation guide

### File Types Reference
- [`Documentation/FILE_TYPES.md`](Documentation/FILE_TYPES.md) - Overview of all .zolo file types
- [`Documentation/zSpark.md`](Documentation/zSpark.md) - ⭐ zSpark application configuration files
- More file types coming soon (zConfig, zEnv, zUI, zSchema)

### Architecture & Design
- [`Documentation/ARCHITECTURE.md`](Documentation/ARCHITECTURE.md) - Detailed design docs
- [`REFACTORING_PLAN.md`](REFACTORING_PLAN.md) - Refactoring journey & lessons learned
- [`Documentation/ERROR_MESSAGES.md`](Documentation/ERROR_MESSAGES.md) - Error messages guide

### Editor Integration
- [`editors/vim/README.md`](editors/vim/README.md) - Vim/Neovim setup guide
- [`editors/vscode/README.md`](editors/vscode/README.md) - VS Code setup guide
- [`editors/cursor/README.md`](editors/cursor/README.md) - Cursor IDE setup guide

### Examples & Usage
- [`examples/`](examples/) - Example .zolo files (7 files covering all features)

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
