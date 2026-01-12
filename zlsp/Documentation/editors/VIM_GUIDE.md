# zlsp Vim Integration

**Complete Vim support for `.zolo` files, following [vim-toml](https://github.com/cespare/vim-toml) best practices**

## Structure

```
zlsp/vim/
├── ftdetect/zolo.vim      ← Auto-detect .zolo files
├── ftplugin/zolo.vim      ← Basic settings (NEW! ✅)
├── syntax/zolo.vim        ← Fallback syntax highlighting
├── indent/zolo.vim        ← Indentation rules
├── lsp_config.vim         ← LSP client setup (loads as after/ftplugin)
├── install.sh             ← One-command installation
└── README.md              ← Documentation
```

## Comparison: vim-toml vs zlsp

### vim-toml (Traditional Syntax Plugin)
```
vim-toml/
├── ftdetect/toml.vim    ← Detect .toml files
├── ftplugin/toml.vim    ← Settings
├── syntax/toml.vim      ← 200+ lines of regex
└── test/                ← Tests
```

**Approach:** Pure syntax highlighting (static regex patterns)

### zlsp (Modern LSP Plugin)
```
zlsp/vim/
├── ftdetect/zolo.vim    ← ✅ Detect .zolo files
├── ftplugin/zolo.vim    ← ✅ Settings (based on vim-toml)
├── syntax/zolo.vim      ← ✅ Minimal fallback (50 lines)
├── indent/zolo.vim      ← ✅ Indentation
├── lsp_config.vim       ← ✅ LSP setup (vim-toml doesn't have!)
└── install.sh           ← ✅ Installer (vim-toml doesn't have!)
```

**Approach:** LSP-first with syntax fallback

---

## What Each File Does

### 1. `ftdetect/zolo.vim` - File Detection
```vim
au BufRead,BufNewFile *.zolo set filetype=zolo
```

**Purpose:** Tell Vim that `*.zolo` files have filetype `zolo`

**Like vim-toml:** Same approach, just for `.zolo` files

---

### 2. `ftplugin/zolo.vim` - Basic Settings (NEW! ✅)
```vim
" Comments
setlocal commentstring=#\ %s
setlocal comments=:#

" Indentation (2 spaces)
setlocal expandtab
setlocal shiftwidth=2
setlocal softtabstop=2

" Formatting
setlocal formatoptions-=t formatoptions+=croql

" Folding
setlocal foldmethod=indent
setlocal foldlevel=99
```

**Purpose:** Configure Vim behavior for `.zolo` files

**Based on:** vim-toml's `ftplugin/toml.vim` - exact same approach!

**What it gives you:**
- ✅ `#` comments work properly
- ✅ 2-space indentation (like YAML/TOML)
- ✅ Code folding based on indentation
- ✅ Smart formatting with `gq`

---

### 3. `syntax/zolo.vim` - Fallback Syntax
```vim
" Minimal fallback (50 lines)
syn match zoloComment /#.*$/
syn match zoloKey /^\s*\zs[A-Za-z_][A-Za-z0-9_.-]*\ze\s*:/
syn keyword zoloBool true false yes no
" ... etc
```

**Purpose:** Basic syntax highlighting when LSP isn't available

**vs vim-toml:** Their syntax file is 200+ lines (primary feature). Ours is 50 lines (fallback only).

**Why smaller?** We rely on LSP for semantic highlighting!

---

### 4. `indent/zolo.vim` - Indentation Rules
```vim
" Smart indentation for nested structures
```

**Purpose:** Auto-indent nested keys

**Advantage:** vim-toml doesn't have this! We're ahead.

---

### 5. `lsp_config.vim` → `after/ftplugin/zolo.vim` - LSP Setup
```vim
" Neovim 0.8+:
lua vim.lsp.start({
  name = 'zolo-lsp',
  cmd = {'zolo-lsp'},
  filetypes = {'zolo'}
})

" Vim 9+ with vim-lsp plugin:
call lsp#register_server({...})

" Fallback: basic syntax
```

**Purpose:** Connect to `zolo-lsp` server for smart features

**The Big Advantage:** vim-toml has NO LSP support!

**What LSP gives you:**
- ✅ **Semantic highlighting** - Context-aware colors
- ✅ **Real-time diagnostics** - Errors as you type
- ✅ **Hover documentation** - Press `K` on type hints
- ✅ **Code completion** - Autocomplete `(int)`, `(float)`, etc.
- ✅ **Go-to-definition** (future)
- ✅ **Find references** (future)

---

### 6. `install.sh` - One-Command Installation
```bash
./install.sh
```

**Purpose:** Install all Vim files to correct locations

**Advantage:** vim-toml requires manual installation. We're easier!

---

## Installation

### Quick Install
```bash
cd /Users/galnachshon/Projects/Zolo/zLSP/zlsp/vim
./install.sh
```

### What Gets Installed

**For Neovim:**
```
~/.config/nvim/
├── ftdetect/zolo.vim          ← File detection
├── ftplugin/zolo.vim          ← Basic settings
├── after/ftplugin/zolo.vim    ← LSP config
├── syntax/zolo.vim            ← Fallback syntax
└── indent/zolo.vim            ← Indentation
```

**For Vim:**
```
~/.vim/
├── ftdetect/zolo.vim
├── ftplugin/zolo.vim
├── after/ftplugin/zolo.vim
├── syntax/zolo.vim
└── indent/zolo.vim
```

---

## Features Comparison

| Feature | vim-toml | zlsp | Winner |
|---------|----------|------|--------|
| **File detection** | ✅ | ✅ | Tie |
| **Basic settings** | ✅ | ✅ | Tie |
| **Syntax highlighting** | ✅ Static (200+ lines) | ✅ LSP-based + fallback | **zlsp** |
| **Indentation** | ❌ | ✅ | **zlsp** |
| **LSP support** | ❌ | ✅ | **zlsp** |
| **Real-time errors** | ❌ | ✅ | **zlsp** |
| **Autocomplete** | ❌ | ✅ | **zlsp** |
| **Hover docs** | ❌ | ✅ | **zlsp** |
| **Easy install** | ❌ Manual | ✅ Script | **zlsp** |

---

## Usage

Once installed, just open a `.zolo` file:

```bash
nvim test.zolo
```

### Automatic Behavior

1. **Vim detects** `.zolo` file → sets `filetype=zolo`
2. **Loads** `ftplugin/zolo.vim` → basic settings
3. **Loads** `after/ftplugin/zolo.vim` → starts `zolo-lsp`
4. **LSP connects** → provides smart features
5. **Fallback** `syntax/zolo.vim` used if LSP unavailable

### Keybindings (When LSP Active)

- `K` - Hover documentation
- `gd` - Go to definition
- `<leader>ca` - Code actions
- `<leader>rn` - Rename symbol

---

## Design Philosophy

### vim-toml Approach (Traditional)
```
Static syntax file → Regex patterns → Vim applies colors
```

**Pros:** Simple, fast, no dependencies  
**Cons:** Dumb (can't understand context), no diagnostics

### zlsp Approach (Modern)
```
LSP server (zolo-lsp) → Semantic tokens → Vim applies colors
                      ↘ Diagnostics → Vim shows errors
                      ↘ Completions → Vim shows suggestions
```

**Pros:** Smart (context-aware), rich features, same across editors  
**Cons:** Requires Phase 1 (zolo-lsp installed)

**Best of both:** We keep a minimal syntax fallback for when LSP isn't available!

---

## Status

✅ **Complete Vim integration** matching vim-toml quality  
✅ **PLUS** advanced LSP features vim-toml doesn't have  
✅ **Ready for Phase 2** (when user is ready to install)

---

## Next: Phase 2

When ready, run:
```bash
./install.sh
```

This completes Phase 2 (Vim integration) and gives you full LSP features!
