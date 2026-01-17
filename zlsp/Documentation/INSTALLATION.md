# zlsp Installation Guide

Complete installation and troubleshooting guide for zlsp (Language Server Protocol for .zolo files).

## Quick Start

```bash
# Install zlsp
pip install zlsp

# Install for your editor
zlsp-install-all        # All editors (Vim, VSCode, Cursor)
zlsp-install-vim        # Vim/Neovim only
zlsp-install-vscode     # VSCode only
zlsp-install-cursor     # Cursor only

# Verify installation
zlsp verify
```

That's it! Open any `.zolo` file and the LSP will work automatically.

---

## Requirements

### Python
- Python 3.8 or later
- pip (package manager)

### Dependencies (auto-installed)
- `pygls 1.3.0+` - LSP framework
- `lsprotocol 2023.0.0+` - LSP types

### Editors

**Neovim** (Recommended)
- Neovim 0.8+ has built-in LSP support
- Zero configuration needed

**Vim**
- Vim 9.0+ works with vim-lsp plugin
- Vim 8 and older: fallback syntax only (no LSP)

**VSCode/Cursor**
- Any recent version (1.50+)
- Built-in LSP support

---

## Installation Methods

### Method 1: From PyPI (Production)

**Recommended for most users:**

```bash
pip install zlsp
```

This installs:
- `zlsp` Python package
- `zolo-lsp` LSP server command
- `zlsp-install-*` editor integration commands
- `zlsp verify` health check command

### Method 2: From Source (Development)

**For contributors or local development:**

```bash
cd /path/to/ZoloMedia/zlsp
pip install -e .
```

Editable install allows you to modify code and see changes immediately.

### Method 3: From Git

**Latest development version:**

```bash
pip install git+https://github.com/ZoloAi/ZoloMedia.git#subdirectory=zlsp
```

---

## Editor Integration

### Install for All Editors

```bash
zlsp-install-all
```

Automatically installs zlsp for Vim, VSCode, and Cursor.

### Install for Specific Editors

```bash
# Vim/Neovim
zlsp-install-vim

# VSCode
zlsp-install-vscode

# Cursor
zlsp-install-cursor
```

### What Gets Installed

**Vim/Neovim** (`~/.vim/` or `~/.config/nvim/`):
```
ftdetect/zolo.vim       # Auto-detect .zolo files
ftplugin/zolo.vim       # Basic settings (comments, indent)
after/ftplugin/zolo.vim # LSP client setup
syntax/zolo.vim         # Fallback syntax highlighting
indent/zolo.vim         # Indentation rules
```

**VSCode** (`~/.vscode/extensions/`):
```
zolo-lsp-1.0.0/         # Extension directory
├── package.json        # Extension manifest
├── client.js           # LSP client
└── syntaxes/           # Syntax highlighting
```

**Cursor** (`~/.cursor/extensions/`):
```
zolo-lsp-1.0.0/         # Extension directory
(same structure as VSCode)
```

---

## Verification

### Health Check

After installation, verify everything works:

```bash
zlsp verify
```

This checks:
- ✓ Python version (3.8+)
- ✓ Core dependencies (pygls, lsprotocol)
- ✓ Parser functionality
- ✓ LSP server availability
- ✓ Semantic tokenizer
- ✓ Editor integrations (Vim, VSCode, Cursor detected)

For detailed diagnostics:
```bash
zlsp verify --verbose
```

### Manual Verification

```bash
# 1. Check Python package
python3 -c "import core; print(core.__version__)"

# 2. Check LSP server command
which zolo-lsp
zolo-lsp --help

# 3. Check editor install commands
which zlsp-install-vim
which zlsp-install-vscode
which zlsp-install-cursor

# 4. Test parser
python3 -c "from core.parser import loads; print(loads('key: value'))"
# Expected: {'key': 'value'}

# 5. Check Vim files
ls ~/.vim/ftdetect/zolo.vim
ls ~/.vim/after/ftplugin/zolo.vim

# 6. Check VSCode extension
ls ~/.vscode/extensions/zolo-lsp-1.0.0/

# 7. Check Cursor extension
ls ~/.cursor/extensions/zolo-lsp-1.0.0/
```

### Test in Editor

Create a test file:
```bash
cat > test.zolo << 'EOF'
# Test configuration
name: Zolo
version(float): 1.0
enabled(bool): true

server:
  host: localhost
  port(int): 8080
EOF
```

Open it:
```bash
vim test.zolo      # or nvim test.zolo
# or
code test.zolo     # VSCode
# or
cursor test.zolo   # Cursor
```

**Expected behavior:**
- Syntax highlighting active
- Type hints recognized
- Hover over keys shows documentation
- Error detection for invalid syntax

---

## Editor-Specific Setup

### Neovim (Built-in LSP)

Neovim 0.8+ works automatically. No additional setup needed.

**Optional:** Customize LSP behavior in `~/.config/nvim/init.lua`:
```lua
-- Example: Show diagnostics in floating window
vim.diagnostic.config({
  float = { border = "rounded" },
})
```

### Vim 9+ (with vim-lsp)

Vim 9+ requires the vim-lsp plugin for LSP features.

**Using vim-plug:**
```vim
" Add to ~/.vimrc
call plug#begin()
Plug 'prabirshrestha/vim-lsp'
call plug#end()
```

Then run `:PlugInstall` and restart Vim.

**Using Vundle:**
```vim
" Add to ~/.vimrc
Plugin 'prabirshrestha/vim-lsp'
```

Then run `:PluginInstall` and restart Vim.

**Using Pathogen:**
```bash
cd ~/.vim/bundle
git clone https://github.com/prabirshrestha/vim-lsp.git
```

After installing vim-lsp, run `zlsp-install-vim` again to configure it.

### Vim 8 and Older

Vim 8 and older don't support LSP.

**What works:**
- Basic syntax highlighting (fallback)
- File type detection
- Indentation

**What doesn't work:**
- Semantic highlighting
- Real-time diagnostics
- Hover information
- Code completion

**Recommendation:** Upgrade to Vim 9+ or switch to Neovim 0.8+

### VSCode

VSCode has built-in LSP support. After running `zlsp-install-vscode`, restart VSCode.

**Verify:**
1. Open a `.zolo` file
2. Check bottom-right status bar for "Zolo Language Server"
3. Hover over keys to see documentation

### Cursor

Cursor (built on VSCode) has built-in LSP support. After running `zlsp-install-cursor`, restart Cursor.

**Verify:**
1. Open a `.zolo` file
2. Check bottom-right status bar for "Zolo Language Server"
3. Hover over keys to see documentation

---

## Troubleshooting

### "zolo-lsp not found"

**Problem:** LSP server command not in PATH

**Solution 1:** Check if it's installed
```bash
pip show zlsp
```

If not installed:
```bash
pip install zlsp
```

**Solution 2:** Add pip bin directory to PATH

Find where pip installs executables:
```bash
# macOS/Linux - System Python
which python3
# If Python is in /usr/local/bin, scripts are usually there too

# macOS - Homebrew Python
find /opt/homebrew -name "zolo-lsp" 2>/dev/null

# macOS - Framework Python
find /Library/Frameworks/Python.framework -name "zolo-lsp" 2>/dev/null

# macOS/Linux - User Python
find ~/.local/bin -name "zolo-lsp" 2>/dev/null
```

Add to PATH (in `~/.zshrc` or `~/.bashrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
# or
export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"
```

Reload shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### "No syntax highlighting"

**Problem:** Editor not detecting `.zolo` files or LSP not running

**Solution:**

1. **Check file type detection:**
   ```bash
   vim test.zolo
   :set filetype?
   # Should show: filetype=zolo
   ```

2. **If wrong filetype, reinstall:**
   ```bash
   zlsp-install-vim  # or your editor
   ```

3. **Check if files exist:**
   ```bash
   ls ~/.vim/ftdetect/zolo.vim
   ls ~/.vim/syntax/zolo.vim
   ```

4. **VSCode/Cursor:** Check Extensions panel for "Zolo LSP"

### "LSP not available" in Vim

**Problem:** Vim 9+ without vim-lsp plugin

**Solution:** Install vim-lsp (see "Vim 9+ (with vim-lsp)" section above)

**Problem:** Vim 8 or older

**Solution:** Vim 8 doesn't support LSP. Upgrade to Vim 9+ or use Neovim 0.8+

### "ModuleNotFoundError: No module named 'core'"

**Problem:** zlsp package not installed or wrong Python environment

**Solution:**

1. **Check Python version:**
   ```bash
   python3 --version  # Should be 3.8+
   ```

2. **Reinstall zlsp:**
   ```bash
   pip uninstall zlsp
   pip install zlsp
   ```

3. **Check active Python:**
   ```bash
   which python3
   which pip
   # Make sure they're from the same Python installation
   ```

4. **If using virtual environments:**
   ```bash
   # Activate the correct environment first
   source venv/bin/activate  # or your venv path
   pip install zlsp
   ```

### "zlsp verify fails"

**Problem:** One or more health checks failing

**Solution:** Run verbose mode to see details:
```bash
zlsp verify --verbose
```

Common issues:
- **Python version too old:** Upgrade to Python 3.8+
- **Missing dependencies:** Run `pip install --upgrade zlsp`
- **LSP server not found:** Check PATH (see "zolo-lsp not found" above)

### Semantic highlighting not working

**Problem:** Colors look basic, not context-aware

**Neovim:**
1. Check LSP is attached:
   ```vim
   :LspInfo
   ```
2. Should show "zolo-lsp" connected

**Vim 9+:**
1. Check vim-lsp is installed:
   ```vim
   :LspStatus
   ```
2. Should show zolo-lsp registered

**VSCode/Cursor:**
1. Check Output panel → "Zolo Language Server"
2. Should show "Server started successfully"

### "Permission denied" during installation

**Problem:** No write access to editor directories

**Solution 1:** Use user install (macOS/Linux)
```bash
pip install --user zlsp
zlsp-install-vim  # This uses ~/.vim/ which you own
```

**Solution 2:** VSCode/Cursor extensions (Windows)
Run terminal as Administrator, then:
```bash
zlsp-install-vscode
```

---

## Uninstallation

### Remove Python Package

```bash
pip uninstall zlsp
```

This removes the Python package and all command-line tools.

### Remove Editor Integrations

**Vim/Neovim:**
```bash
# Automated uninstall
zlsp-uninstall-vim

# Or manual removal:
rm ~/.vim/ftdetect/zolo.vim
rm ~/.vim/ftplugin/zolo.vim
rm ~/.vim/after/ftplugin/zolo.vim
rm ~/.vim/syntax/zolo.vim
rm ~/.vim/indent/zolo.vim

# Neovim:
rm ~/.config/nvim/ftdetect/zolo.vim
rm ~/.config/nvim/ftplugin/zolo.vim
rm ~/.config/nvim/after/ftplugin/zolo.vim
rm ~/.config/nvim/syntax/zolo.vim
rm ~/.config/nvim/indent/zolo.vim
```

**VSCode:**
```bash
# Automated uninstall
zlsp-uninstall-vscode

# Or manual removal:
rm -rf ~/.vscode/extensions/zolo-lsp-1.0.0/
```

**Cursor:**
```bash
# Automated uninstall
zlsp-uninstall-cursor

# Or manual removal:
rm -rf ~/.cursor/extensions/zolo-lsp-1.0.0/
```

**Uninstall from all editors:**
```bash
zlsp-uninstall-all
```

---

## Advanced Configuration

### Custom LSP Server Port

By default, zlsp uses stdio for LSP communication (no network port needed).

To use TCP (for remote development):
```bash
# Start server on port 9999
zolo-lsp --port 9999
```

Then configure your editor to connect to `localhost:9999`.

### Theme Customization

zlsp uses `themes/zolo_default.yaml` as the canonical theme.

**To customize colors:**

1. Copy the theme:
   ```bash
   cp ~/.local/lib/python3.*/site-packages/themes/zolo_default.yaml ~/my_theme.yaml
   ```

2. Edit `~/my_theme.yaml` to change colors

3. Tell zlsp to use it:
   ```bash
   export ZLSP_THEME=~/my_theme.yaml
   zolo-lsp
   ```

**Note:** Custom themes are advanced. Most users don't need this.

### Logging and Debugging

Enable debug logging:
```bash
# Verbose LSP server logs
zolo-lsp --log-file /tmp/zlsp.log --log-level DEBUG
```

View logs:
```bash
tail -f /tmp/zlsp.log
```

---

## Next Steps

After successful installation:

1. **Read the main README:** [README.md](../README.md) for feature overview

2. **Try examples:**
   - [basic.zolo](../examples/basic.zolo) - Simple syntax
   - [advanced.zolo](../examples/advanced.zolo) - Real-world config

3. **Explore special file types:** [zOS README](../../zOS/README.md) for zConfig, zEnv, zSpark

4. **Editor-specific guides:**
   - [Vim Guide](../editors/vim/README.md)
   - [VSCode Guide](../editors/vscode/README.md)
   - [Cursor Guide](../editors/cursor/README.md)

5. **Architecture deep dive:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Support

**Issues and Questions:**
- GitHub Issues: [ZoloMedia/issues](https://github.com/ZoloAi/ZoloMedia/issues)
- Check existing issues before creating new ones

**Documentation:**
- Main README: [README.md](../README.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- File Types: [FILE_TYPES.md](FILE_TYPES.md)

**Community:**
- Star the repo to show support
- Share your `.zolo` use cases

---

## FAQ

**Q: Do I need to restart my editor after installation?**
A: Usually yes. VSCode/Cursor need restart. Vim/Neovim can reload with `:edit` or restart.

**Q: Can I use zlsp without an editor (CLI only)?**
A: Yes! Import the parser directly:
```python
from core.parser import loads, dumps
data = loads("key: value")
```

**Q: Does zlsp work on Windows?**
A: Python package works on Windows. Editor integrations are primarily tested on macOS/Linux.

**Q: Can I use multiple versions of zlsp?**
A: Not recommended. Uninstall old version first: `pip uninstall zlsp`

**Q: Why is it called zolo-lsp instead of zlsp?**
A: The LSP server command is `zolo-lsp`, the Python package is `zlsp`. This avoids confusion.

**Q: Do I need internet to use zlsp?**
A: No. After installation, zlsp works completely offline.
