# zlsp Installation Guide

Complete guide to installing zlsp (Zolo Language Server Protocol) for Vim and other editors.

## Architecture Overview

```
┌─────────────────────┐
│   zlsp package      │  ← Python package
│   ├── parser.py     │     • Tokenize & parse .zolo files
│   ├── lsp_server.py │     • LSP protocol wrapper
│   └── vim/          │     • Vim integration files
└─────────┬───────────┘
          │
          ↓ (LSP Protocol)
    ┌─────┴─────┐
    ↓           ↓
┌────────┐  ┌────────┐
│  Vim   │  │ Neovim │  ← Editor clients
└────────┘  └────────┘
```

**Key Principle:** Single parser, wrapped by LSP, consumed by thin editor clients (TOML architecture).

---

## Installation Methods

### Method 1: Production Install (PyPI) - RECOMMENDED

**One command does everything:**

```bash
pip install zlsp && zolo-vim-install
```

**What this does automatically:**
1. ✅ Installs zlsp Python package and `zolo-lsp` server
2. ✅ Installs Vim integration files
3. ✅ Detects your Vim version
4. ✅ **Auto-installs vim-lsp** (if Vim 9+)
5. ✅ Configures your `~/.vimrc` (with backup)
6. ✅ Ready to use!

**Then just:**
```bash
vim test.zolo  # LSP works automatically! 🎉
```

---

### Method 2: From GitHub (Public Repo)

**One command installation:**

```bash
pip install git+https://github.com/ZoloAi/Zolo.git#subdirectory=zLSP && zolo-vim-install
```

**That's it!** vim-lsp auto-configured for Vim 9+.

```bash
vim test.zolo  # Works! 🎉
```

---

### Method 3: Local Development (Editable)

**For developers working on zlsp itself:**

```bash
# 1. Navigate and install
cd /path/to/Zolo/zLSP
pip install -e .

# 2. Run automated installer
zolo-vim-install

# That's it! vim-lsp auto-configured.
vim test.zolo
```

**Alternative installer commands (all do the same thing):**
```bash
zolo-vim-install           # Preferred
python -m zlsp.vim         # Python module
cd zlsp/vim && ./install.sh  # Shell script
```

---

## What Gets Installed

### Python Package (`pip install zlsp`)

Creates:
- `zlsp` Python package in site-packages
- `zolo-lsp` command in PATH (LSP server)
- `zolo-vim-install` command in PATH (Vim installer)

### Vim Integration (`zolo-vim-install`)

Copies to `~/.vim/` (Vim) or `~/.config/nvim/` (Neovim):

```
~/.vim/
├── ftdetect/
│   └── zolo.vim                 # Auto-detect .zolo files
├── ftplugin/
│   └── zolo.vim                 # Basic settings (comments, indent)
├── after/ftplugin/
│   └── zolo.vim                 # LSP client setup
├── syntax/
│   └── zolo.vim                 # Fallback syntax (if LSP unavailable)
└── indent/
    └── zolo.vim                 # Indentation rules
```

---

## Verification

### Check Installation

```bash
# 1. Verify zlsp package
python3 -c "import zlsp; print(zlsp.__version__)"

# 2. Verify zolo-lsp command
which zolo-lsp
zolo-lsp --help

# 3. Verify zolo-vim-install command
which zolo-vim-install

# 4. Test parser
python3 -c "from zlsp import loads; print(loads('key: value'))"

# 5. Check Vim files (Vim)
ls -l ~/.vim/ftdetect/zolo.vim
ls -l ~/.vim/after/ftplugin/zolo.vim

# 6. Check Vim files (Neovim)
ls -l ~/.config/nvim/ftdetect/zolo.vim
ls -l ~/.config/nvim/after/ftplugin/zolo.vim
```

### Test in Editor

```bash
# Create test file
cat > test.zolo << 'EOF'
# Test file
name: Zolo
version(float): 1.0
enabled(bool): true

nested:
  key: value
EOF

# Open in Vim/Neovim
vim test.zolo
```

**Expected behavior:**
- **Neovim 0.8+:** LSP activates automatically, semantic highlighting works
- **Vim 9+ with vim-lsp:** LSP activates, semantic highlighting works
- **Vim 9+ without vim-lsp:** Fallback syntax highlighting (basic colors)
- **Vim 8 or older:** Fallback syntax highlighting (basic colors)

---

## Requirements by Editor

### Neovim (Recommended)

✅ **Best experience** - Built-in LSP support!

- Neovim 0.8+
- Python 3.8+
- `zlsp` package installed
- `zolo-lsp` in PATH

**Installation:**
```bash
pip install zlsp
zolo-vim-install
nvim test.zolo  # Works automatically!
```

### Vim 9+

✅ **Full LSP features** with vim-lsp plugin

- Vim 9.0+
- Python 3.8+
- `zlsp` package installed
- `zolo-lsp` in PATH
- **vim-lsp plugin required**

**Installation:**
```bash
pip install zlsp
zolo-vim-install

# Add to ~/.vimrc:
call plug#begin()
Plug 'prabirshrestha/vim-lsp'
call plug#end()

# Install plugin:
:PlugInstall

# Restart Vim:
vim test.zolo
```

### Vim 8 or Older

⚠️ **Limited** - Basic syntax only (no LSP)

- Vim 8 or older
- No LSP features
- Fallback syntax highlighting only

**Recommendation:** Upgrade to Vim 9+ or use Neovim 0.8+

---

## Troubleshooting

### "zolo-lsp not found"

**Problem:** `zolo-lsp` command not in PATH

**Solution:**
```bash
# Check if it exists
find /Library/Frameworks/Python.framework -name "zolo-lsp" 2>/dev/null
find ~/Library/Python -name "zolo-lsp" 2>/dev/null

# Add to PATH (add to ~/.zshrc or ~/.bashrc):
export PATH="$HOME/.local/bin:$PATH"
export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bashrc
```

### "LSP not available" in Vim

**Problem:** Vim 9+ without vim-lsp plugin

**Solution:** Install vim-lsp plugin (see Vim 9+ section above)

### "No syntax highlighting"

**Problem:** LSP not running, fallback syntax not working

**Solution:**
```bash
# Check filetype detection
vim test.zolo
:set filetype?
# Should show: filetype=zolo

# If not, reinstall Vim integration
zolo-vim-install

# Check if files exist
ls ~/.vim/ftdetect/zolo.vim
ls ~/.vim/syntax/zolo.vim
```

### "ModuleNotFoundError: No module named 'zlsp'"

**Problem:** zlsp not installed

**Solution:**
```bash
pip install zlsp
# Or for development:
cd /path/to/Zolo/zLSP
pip install -e .
```

---

## Uninstallation

### Remove Python Package

```bash
pip uninstall zlsp
```

### Remove Vim Integration

```bash
# Vim
rm ~/.vim/ftdetect/zolo.vim
rm ~/.vim/ftplugin/zolo.vim
rm ~/.vim/after/ftplugin/zolo.vim
rm ~/.vim/syntax/zolo.vim
rm ~/.vim/indent/zolo.vim

# Neovim
rm ~/.config/nvim/ftdetect/zolo.vim
rm ~/.config/nvim/ftplugin/zolo.vim
rm ~/.config/nvim/after/ftplugin/zolo.vim
rm ~/.config/nvim/syntax/zolo.vim
rm ~/.config/nvim/indent/zolo.vim
```

---

## Next Steps

After installation:

1. **Test basic functionality:**
   ```bash
   vim test.zolo
   # Type: name: Zolo
   # Expect: Colors, indentation, comments work
   ```

2. **Test LSP features (Neovim 0.8+ or Vim 9+ with vim-lsp):**
   - Hover: Move cursor to key, press `K`
   - Diagnostics: Introduce syntax error, see error message
   - Completion: Type `port(` and wait for suggestions

3. **Read documentation:**
   - `zlsp/vim/README.md` - Vim-specific details
   - `ARCHITECTURE.md` - System design
   - `QUICKSTART.md` - Quick examples

4. **Configure colors** (optional):
   - Edit `~/.vimrc` or `~/.config/nvim/init.lua`
   - Customize LSP semantic token colors

---

## Support

- **Issues:** Report bugs on GitHub
- **Documentation:** See `zlsp/vim/README.md`
- **Examples:** See `examples/basic.zolo`
- **Architecture:** See `ARCHITECTURE.md`
