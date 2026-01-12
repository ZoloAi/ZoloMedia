# Zolo LSP Quick Start

**Get up and running with Zolo LSP in 5 minutes.**

## What You're Installing

A **pure LSP** language server for `.zolo` files that provides:
- Semantic syntax highlighting
- Real-time diagnostics (error checking)
- Hover documentation
- Code completion

**No grammar files.** Your parser (`parser.py`) is the single source of truth.

## Installation (One Command!)

### Production Install

```bash
pip install zlsp && zolo-vim-install
```

**That's it!** The installer automatically:
1. ✅ Installs zlsp package and `zolo-lsp` server
2. ✅ Copies Vim integration files
3. ✅ Detects Vim version and auto-installs vim-lsp (Vim 9+)
4. ✅ Configures your `~/.vimrc` (with backup)

### Development Install

```bash
cd /path/to/Zolo/zLSP
pip install -e . && zolo-vim-install
```

### Verify Installation

```bash
# Check command
which zolo-lsp
# Output: /path/to/bin/zolo-lsp

# Test parser
python3 -c "from zlsp import loads; print(loads('key: value'))"
# Output: {'key': 'value'}

# Check Vim files
ls ~/.vim/ftdetect/zolo.vim
# Output: /Users/you/.vim/ftdetect/zolo.vim
```

### Test It!

```bash
# Create test file
cat > test.zolo << 'EOF'
# Test Zolo file
name: Zolo
version(float): 1.0
port(int): 8080
enabled(bool): true

nested:
  key: value
  list:
    - item1
    - item2
EOF

# Open in Vim
nvim test.zolo
```

**Expected:**
- Comments in gray
- Keys in salmon/orange
- Values colored by type
- Hover on `version(float)` shows type hint docs

## Verify LSP is Working

### In Neovim

```vim
:LspInfo
```

Should show:
```
 Language client log: /path/to/lsp.log
 Detected filetype:   zolo

 1 client(s) attached to this buffer:

 Client: zolo-lsp (id: 1, bufnr: [1])
  filetypes:       zolo
  autostart:       true
  root directory:  /path/to/project
  cmd:             zolo-lsp
```

### In Vim (with vim-lsp)

```vim
:LspStatus
```

Should show `zolo-lsp` running.

## Troubleshooting

### "zolo-lsp command not found"

Add Python bin directory to PATH:

```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

# Or for system Python
export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"

# Reload shell
source ~/.zshrc  # or ~/.bashrc
```

### "LSP not starting"

1. Check Python version:
   ```bash
   python3 --version  # Should be 3.8+
   ```

2. Check package is installed:
   ```bash
   pip list | grep zolo
   ```

3. Check LSP logs (Neovim):
   ```bash
   tail -f ~/.local/state/nvim/lsp.log
   ```

### "No syntax highlighting"

- LSP provides semantic tokens, not traditional syntax
- Ensure LSP is running (`:LspInfo`)
- If LSP fails, basic fallback syntax is used

## Next Steps

### Learn String-First Philosophy

```zolo
# Strings (default)
name: Zolo
description: A config format

# Explicit type conversion
version(float): 1.0
port(int): 8080
enabled(bool): true

# Force string
id(str): 12345
```

See [README.md](README.md) for details.

### Read Architecture Docs

- [ARCHITECTURE.md](ARCHITECTURE.md) - How it all works
- [src/zolo/vim/README.md](src/zolo/vim/README.md) - Vim-specific docs

### Try Advanced Features

- Hover: `K` on a type hint
- Completion: Type `key(` and wait
- Diagnostics: Create a syntax error

### Phase 2: VS Code (Coming Soon)

Same LSP server, different client. Stay tuned!

## Summary

You now have:
- ✅ Parser installed (`parser.py` - the brain)
- ✅ LSP server running (`zolo-lsp`)
- ✅ Vim configured as LSP client
- ✅ Full LSP features (highlighting, diagnostics, hover, completion)

**No grammar files.** Everything comes from the parser via LSP.

Enjoy! 🚀
