# Installing vim-lsp for Vim 9.1

## Why You Need This

**Vim 9.1 does NOT have built-in LSP support.** You need the `vim-lsp` plugin to:
- Enable LSP client functionality
- Get semantic highlighting from `zolo-lsp` server
- Enable diagnostics, hover, completion

**Neovim 0.8+** has built-in LSP - no plugin needed!

---

## Option 1: Install vim-plug (Recommended)

### Step 1: Install vim-plug

```bash
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
```

### Step 2: Update ~/.vimrc

Add to the **TOP** of your `~/.vimrc`:

```vim
" vim-plug plugin manager
call plug#begin('~/.vim/plugged')

" LSP client for Vim
Plug 'prabirshrestha/vim-lsp'

call plug#end()

" Rest of your existing config below...
" (keep your existing syntax on, filetype plugin indent on, etc.)
```

### Step 3: Install Plugins

```bash
# Open Vim and run:
vim +PlugInstall +qall

# Or inside Vim:
:PlugInstall
```

### Step 4: Test

```bash
vim /Users/galnachshon/Projects/Zolo/test.zolo
```

**Expected:** LSP activates, semantic highlighting works, no more "LSP not available" message.

---

## Option 2: Use Neovim Instead (Easier!)

If you don't want to deal with Vim plugins, **Neovim has built-in LSP**:

```bash
# Install Neovim (if not already installed)
brew install neovim

# Test with zlsp
nvim /Users/galnachshon/Projects/Zolo/test.zolo
```

**No plugins needed!** LSP works automatically.

---

## Option 3: Accept Basic Syntax (No LSP)

If you don't need advanced LSP features, you can use the basic syntax highlighting:

**What works:**
- Comments highlighted
- Keys highlighted (salmon/orange)
- Strings, numbers, booleans colored
- Indentation
- Basic syntax validation

**What doesn't work:**
- Real-time diagnostics from parser
- Hover information
- Context-aware semantic highlighting (zUI, zConfig, zEnv files)
- Autocompletion

---

## Testing LSP After Installation

### 1. Check LSP Status

```vim
" In Vim:
:LspStatus

" Expected output:
" zolo-lsp: running
```

### 2. Test Features

Open `test.zolo`:
```zolo
# Test file
name: Zolo
version(float): 1.0
port(int): 8080

nested:
  key: value
```

**Test hover:**
- Move cursor to `version(float)`
- Press `K`
- Should show type hint documentation

**Test diagnostics:**
- Change to `port(int): abc` (invalid)
- Should show error highlighting

**Test completion:**
- Type `enabled(` and wait
- Should show type hint suggestions: `bool)`, `int)`, etc.

---

## Current Installation Summary

✅ **zlsp package:** Installed
✅ **zolo-lsp command:** Available in PATH
✅ **Vim files:** Installed in `~/.vim/`
✅ **Filetype detection:** Working
❌ **vim-lsp plugin:** Not installed (needed for LSP features)

---

## Recommended Action

**For Vim users:**
```bash
# 1. Install vim-plug
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

# 2. Add to ~/.vimrc (at the top):
# call plug#begin('~/.vim/plugged')
# Plug 'prabirshrestha/vim-lsp'
# call plug#end()

# 3. Install plugins
vim +PlugInstall +qall

# 4. Test
vim test.zolo
```

**For Neovim users:**
```bash
# Just use it - LSP works automatically!
nvim test.zolo
```
