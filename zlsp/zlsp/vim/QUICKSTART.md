# Vim Support for .zolo - Quick Start

## One-Line Install

```bash
zolo-vim-setup
```

That's it! Your vim is now ready for beautiful `.zolo` files.

## Test It

```bash
# Open your machine config in vim
zolo machine --open
```

## What You Get

✅ **Syntax highlighting** matching your IDE colors  
✅ **Smart indentation** (2-space, YAML-style)  
✅ **Auto file-type detection**  
✅ **Color-coded keys** (editable = blue, locked = red)

## Quick Vim Cheat Sheet

```vim
# Editing
i           Enter insert mode
ESC         Exit insert mode
:w          Save
:wq         Save and quit
:q!         Quit without saving

# Navigation  
gg          Go to top
G           Go to bottom
/text       Search
n           Next match

# Folding (collapse sections)
za          Toggle fold
zR          Open all folds
zM          Close all folds
```

## Better Colors (Optional)

Add to `~/.vimrc`:

```vim
" Enable 24-bit colors
if has('termguicolors')
  set termguicolors
endif

" Use a dark theme (optional but recommended)
colorscheme gruvbox
set background=dark
```

## Full Documentation

See `README.md` in this directory for:
- LSP integration (auto-complete, diagnostics)
- Custom keybindings
- Troubleshooting
- Advanced configuration

---

**Enjoy!** 🎨
