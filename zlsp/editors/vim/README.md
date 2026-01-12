# Zolo LSP for Vim/Neovim

Pure LSP-based support for `.zolo` files in Vim and Neovim.

## Architecture

Zolo follows the **TOML model** for language tooling:

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
│  Vim   │    │ Neovim │  ← Thin LSP clients
│  LSP   │    │  LSP   │    (No grammar files!)
└────────┘    └────────┘
```

**No grammar files.** The parser provides semantic tokens directly to the LSP, which editors consume.

## Quick Install

**Production (Recommended):**

```bash
# Install zlsp package
pip install zlsp

# Install Vim integration
zolo-vim-install
```

**Development (From Git):**

```bash
# Install from monorepo
cd /path/to/Zolo/zLSP
pip install -e .

# Install Vim integration (choose one):
zolo-vim-install                  # Using command
python -m zlsp.vim                # Using Python module
cd zlsp/vim && ./install.sh       # Using shell script
```

This will:
1. Install the `zlsp` Python package (LSP server)
2. Copy Vim configuration files to `~/.vim` or `~/.config/nvim`
3. Set up filetype detection and LSP integration

## Manual Installation

### 1. Install Python Package

```bash
cd /path/to/zLSP
pip install -e .
```

Verify:
```bash
which zolo-lsp  # Should show path to command
zolo-lsp --help # Should show LSP server help
```

### 2. Copy Vim Files

First, find the installed zlsp Vim files:

```bash
python3 -c "import zlsp.vim; import pathlib; print(pathlib.Path(zlsp.vim.__file__).parent)"
```

Then copy them:

**For Neovim:**
```bash
ZLSP_VIM=/path/from/above  # Replace with output from previous command
mkdir -p ~/.config/nvim/{ftdetect,ftplugin,after/ftplugin,syntax,indent}
cp $ZLSP_VIM/ftdetect/zolo.vim ~/.config/nvim/ftdetect/
cp $ZLSP_VIM/ftplugin/zolo.vim ~/.config/nvim/ftplugin/
cp $ZLSP_VIM/lsp_config.vim ~/.config/nvim/after/ftplugin/zolo.vim
cp $ZLSP_VIM/syntax/zolo.vim ~/.config/nvim/syntax/
cp $ZLSP_VIM/indent/zolo.vim ~/.config/nvim/indent/
```

**For Vim:**
```bash
ZLSP_VIM=/path/from/above  # Replace with output from previous command
mkdir -p ~/.vim/{ftdetect,ftplugin,after/ftplugin,syntax,indent}
cp $ZLSP_VIM/ftdetect/zolo.vim ~/.vim/ftdetect/
cp $ZLSP_VIM/ftplugin/zolo.vim ~/.vim/ftplugin/
cp $ZLSP_VIM/lsp_config.vim ~/.vim/after/ftplugin/zolo.vim
cp $ZLSP_VIM/syntax/zolo.vim ~/.vim/syntax/
cp $ZLSP_VIM/indent/zolo.vim ~/.vim/indent/
```

**Note:** This is all automated by `zolo-vim-install` command!

### 3. Restart Editor

```bash
nvim test.zolo  # or vim test.zolo
```

## Requirements

### Neovim (Recommended)
- **Neovim 0.8+** (built-in LSP)
- Python 3.8+
- `zolo-lsp` in PATH

### Vim
- **Vim 9+** with [vim-lsp](https://github.com/prabirshrestha/vim-lsp) plugin
- Python 3.8+
- `zolo-lsp` in PATH

## Features

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

## Keybindings (Default)

When LSP is active:

- `K` - Hover information
- `gd` - Go to definition
- `<leader>ca` - Code actions
- `<leader>rn` - Rename symbol

## Troubleshooting

### LSP Not Starting

1. **Check if `zolo-lsp` is in PATH:**
   ```bash
   which zolo-lsp
   ```
   If not found, add to PATH:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Test parser directly:**
   ```bash
   python3 -c "from zlsp import loads; print(loads('key: value'))"
   ```

3. **Check LSP logs (Neovim):**
   ```bash
   tail -f ~/.local/state/nvim/lsp.log
   ```

### No Syntax Highlighting

- LSP provides semantic tokens, not traditional syntax
- Ensure LSP is running: `:LspInfo` (Neovim) or `:LspStatus` (Vim)
- If LSP fails, fallback basic syntax is used

### Vim 8 or Older

- Upgrade to Vim 9+ or use Neovim 0.8+
- Or use basic syntax highlighting (limited features)

## Testing

Create a test file:

```bash
cat > test.zolo << 'EOF'
# Test file
name: Zolo
version(float): 1.0
enabled(bool): true
port(int): 8080

nested:
  key: value
  list:
    - item1
    - item2
EOF

nvim test.zolo
```

Expected:
- Comments in gray
- Keys in salmon/orange
- Values colored by type
- Hover on `version(float)` shows type hint docs

## Architecture Notes

**Why no grammar files?**

Traditional editors use **static grammar files** (TextMate, Vim syntax) that are:
- Separate from the parser (duplication)
- Limited in expressiveness
- Hard to keep in sync

Modern LSP approach:
- **Parser is the source of truth**
- LSP wraps parser
- Editors are thin clients
- No duplication, always in sync

This is how TOML (`taplo-lsp`), Rust (`rust-analyzer`), and other modern languages work.

## Next Steps

- **Phase 2:** VS Code extension (same LSP server)
- **Phase 3:** IntelliJ plugin (same LSP server)
- **Phase 4:** Web editor integration

All editors connect to the same `parser.py` brain via LSP.
