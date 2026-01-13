# Vim Integration for Zolo LSP

Complete Vim/Neovim integration for `.zolo` files with LSP support.

## Features

✨ **Fully Automatic** - No `.vimrc` editing required!  
🎨 **Beautiful Colors** - Refined 256-color palette for terminal compatibility  
🚀 **LSP Features** - Hover, completion, diagnostics, and more  
🔒 **Non-Destructive** - Only affects `.zolo` files, leaves everything else alone

---

## Quick Setup

### Prerequisites

**Option 1: Vim 9+ with vim-lsp**
```vim
" Add to your ~/.vimrc:
call plug#begin('~/.vim/plugged')
Plug 'prabirshrestha/vim-lsp'
call plug#end()
```

Then run `:PlugInstall` in Vim.

**Option 2: Neovim** (built-in LSP, no plugin needed)

### Installation

```bash
pip install zlsp
zlsp-vim-install
```

That's it! 🎉

---

## What Gets Installed?

The installer copies files to **auto-loading directories** in `~/.vim/`:

```
~/.vim/
├── ftdetect/zolo.vim        # Detects .zolo files
├── ftplugin/zolo.vim        # File type settings
├── syntax/zolo.vim          # Fallback syntax (no LSP)
├── indent/zolo.vim          # Indentation rules
├── plugin/zolo_lsp.vim      # LSP global setup (runs on startup)
├── after/ftplugin/zolo.vim  # LSP per-file setup (runs after vim-lsp)
└── colors/zolo_lsp.vim      # Semantic token colors
```

**No `.vimrc` modification needed!** Everything auto-loads when you open a `.zolo` file.

---

## Color Scheme

Carefully tuned for terminal compatibility (256-color ANSI palette):

| Element | Color | ANSI | Description |
|---------|-------|------|-------------|
| Root keys | `#ffaf87` | 216 | Salmon/orange |
| Nested keys | `#ffd787` | 222 | Golden yellow |
| Strings | `#fffbcb` | 230 | Light cream |
| Numbers | `#FF8C00` | 214 | Dark orange |
| Type hints | `#5fd7ff` | 81 | Cyan |
| Type hint `()` | `#ffff5f` | 227 | Soft yellow |
| Array `[]` | `#ffd7ff` | 225 | Light pink |
| Booleans | `#0087ff` | 33 | Deep blue |
| Comments | `#6c6c6c` | 242 | Gray (italic) |

### Customizing Colors

Edit `~/.vim/colors/zolo_lsp.vim` and change the `ctermfg` values.

---

## Usage

Open any `.zolo` file:

```bash
vim test.zolo
```

### LSP Features

| Key | Action |
|-----|--------|
| `K` | Hover info |
| `gd` | Go to definition |
| `gr` | Find references |
| `]d` | Next diagnostic |
| `[d` | Previous diagnostic |

Check LSP status:
```vim
:LspStatus
```

---

## How It Works

### Auto-Loading Magic

Vim has **special directories** that automatically load files when certain events happen:

1. **On Vim startup** → `plugin/zolo_lsp.vim` runs
   - Registers `zolo-lsp` server with vim-lsp
   - Enables semantic tokens globally

2. **When opening `.zolo`** → Files load in order:
   - `ftdetect/zolo.vim` - Detects file type
   - `ftplugin/zolo.vim` - Sets buffer options
   - `syntax/zolo.vim` - Fallback syntax highlighting
   - `after/ftplugin/zolo.vim` - **Loads AFTER vim-lsp** ← LSP setup here!
   - `colors/zolo_lsp.vim` - Applies semantic colors

### Why `after/ftplugin/`?

The `after/` directory ensures our LSP setup runs **AFTER** vim-lsp loads, guaranteeing proper initialization order. This is how Vim plugins handle load-order dependencies.

### Scoped Highlighting

All color definitions use `autocmd FileType zolo` to ensure they **only affect `.zolo` files**:

```vim
autocmd FileType zolo highlight! LspSemanticRootKey ctermfg=216 ...
```

This means:
- ✅ Your other files are unaffected
- ✅ No conflicts with your existing color schemes
- ✅ Completely non-destructive

---

## Troubleshooting

### Colors not showing?

1. Check LSP server is running:
   ```vim
   :LspStatus
   ```

2. Verify semantic tokens are enabled:
   ```vim
   :echo g:lsp_semantic_enabled
   ```
   Should return `1`.

3. Restart Vim completely (`:source ~/.vimrc` may not be enough).

### vim-lsp not found?

Add to your `~/.vimrc`:
```vim
call plug#begin('~/.vim/plugged')
Plug 'prabirshrestha/vim-lsp'
call plug#end()
```

Then run `:PlugInstall` and restart Vim.

### Installation failed?

Make sure `zlsp` is installed:
   ```bash
pip install zlsp
which zolo-lsp  # Should show path
```

---

## Manual Installation

If you prefer not to use `zlsp-vim-install`, you can manually copy files from `zlsp/editors/vim/config/` to `~/.vim/`:

   ```bash
cp -r zlsp/editors/vim/config/* ~/.vim/
```

Then add vim-lsp to your `.vimrc` (see Prerequisites).

---

## Uninstallation

Remove the installed files:

```bash
rm -rf ~/.vim/ftdetect/zolo.vim \
       ~/.vim/ftplugin/zolo.vim \
       ~/.vim/syntax/zolo.vim \
       ~/.vim/indent/zolo.vim \
       ~/.vim/plugin/zolo_lsp.vim \
       ~/.vim/after/ftplugin/zolo.vim \
       ~/.vim/colors/zolo_lsp.vim
```

---

## Architecture

```
zlsp/editors/vim/
├── config/
│   ├── ftdetect/         # File type detection
│   ├── ftplugin/         # File type settings
│   ├── syntax/           # Fallback syntax
│   ├── indent/           # Indentation
│   ├── plugin/           # Global LSP setup
│   ├── after/ftplugin/   # LSP per-file setup (load order!)
│   └── colors/           # Semantic token colors
├── install.py            # Installation script
└── README.md             # This file
```

---

## More Info

- [LSP Server Docs](../../Documentation/ARCHITECTURE.md)
- [Zolo Format Spec](../../README.md)
- [Session Notes](../../../SESSION_NOTES.md)

---

**Made with ❤️ by Zolo.ai**
