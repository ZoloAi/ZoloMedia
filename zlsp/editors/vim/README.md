# Vim Integration for Zolo LSP

Complete Vim/Neovim integration for `.zolo` files with LSP support.

## Quick Setup

### Option 1: Automatic Installation (Recommended)

```bash
pip install zlsp
zolo-vim-install
```

This will automatically:
- Install syntax files
- Configure LSP server
- Set up semantic token highlighting

### Option 2: Manual Installation

Add to your `~/.vimrc`:

```vim
" Source Zolo color scheme
source ~/Projects/ZoloMedia/zlsp/editors/vim/config/zolo_highlights.vim

" Enable semantic tokens (required for LSP highlighting)
let g:lsp_semantic_enabled = 1

" Register zolo-lsp server with vim-lsp
if executable('zolo-lsp')
  augroup ZoloLSP
    autocmd!
    autocmd User lsp_setup call lsp#register_server({
      \ 'name': 'zolo-lsp',
      \ 'cmd': {server_info->['zolo-lsp']},
      \ 'allowlist': ['zolo']
      \ })
  augroup END
endif
```

## Color Scheme

The included `zolo_highlights.vim` provides a carefully tuned color scheme:

| Element | Color | Description |
|---------|-------|-------------|
| Root keys | Orange (216) | Bold hierarchy markers |
| Nested keys | Golden (222) | Regular weight |
| Strings | Cream (230) | Light yellow |
| Numbers | Dark orange (214) | Prominent |
| Type hints | Cyan (81) | `int`, `bool`, etc. |
| Type hint `()` | Soft yellow (227) | Parentheses |
| Array `[]` | Pink/cream (225) | Brackets |
| Booleans | Deep blue (33) | `true`, `false` |
| Comments | Gray (242) | Italic |

### Customizing Colors

Edit `config/zolo_highlights.vim` and change the `ctermfg` values (256-color palette).

## Files Included

```
vim/
├── config/
│   ├── ftdetect/zolo.vim      # File type detection
│   ├── ftplugin/zolo.vim      # File type settings
│   ├── syntax/zolo.vim        # Fallback syntax (no LSP)
│   ├── indent/zolo.vim        # Indentation rules
│   ├── zolo_highlights.vim    # LSP semantic token colors
│   └── vimrc_snippet.vim      # Example .vimrc config
├── install.py                 # Installation script
└── README.md                  # This file
```

## Requirements

- Vim 8.0+ or Neovim 0.5+
- [vim-lsp](https://github.com/prabirshrestha/vim-lsp) plugin
- `zolo-lsp` server installed (`pip install zlsp`)

## Troubleshooting

### Colors not showing?

1. Check LSP server is running: `:LspStatus`
2. Verify semantic tokens enabled: `:echo g:lsp_semantic_enabled` (should be `1`)
3. Restart Vim completely (`:source ~/.vimrc` may not be enough)

### Bold text appearing unexpectedly?

The color scheme uses `autocmd FileType zolo` to override Vim's default syntax highlighting. This ensures consistent styling across different terminal emulators.

## Testing

Open a `.zolo` file:

```bash
vim zlsp/examples/basic.zolo
```

You should see:
- ✅ Root keys in orange
- ✅ Type hints in cyan with yellow parentheses
- ✅ Booleans in blue
- ✅ Numbers in orange
- ✅ Strings in cream

## More Info

- [Vim Integration Guide](../../Documentation/editors/VIM_GUIDE.md)
- [LSP Server Docs](../../Documentation/ARCHITECTURE.md)
- [Zolo Format Spec](../../README.md)
