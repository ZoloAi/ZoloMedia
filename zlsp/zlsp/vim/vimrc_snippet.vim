" ═══════════════════════════════════════════════════════════════
" Zolo File Support - Add to your ~/.vimrc or ~/.config/nvim/init.vim
" ═══════════════════════════════════════════════════════════════

" Enable 24-bit RGB colors (makes colors match your IDE exactly)
if has('termguicolors')
  set termguicolors
endif

" Recommended dark colorscheme (install gruvbox first)
" Plug 'morhetz/gruvbox'
" colorscheme gruvbox
" set background=dark

" Better defaults for .zolo files
autocmd FileType zolo setlocal
  \ tabstop=2
  \ shiftwidth=2
  \ softtabstop=2
  \ expandtab
  \ autoindent
  \ smartindent
  \ number
  \ relativenumber
  \ cursorline
  \ colorcolumn=80

" Fold zMachine sections for easier navigation
autocmd FileType zolo setlocal
  \ foldmethod=indent
  \ foldlevel=1
  \ foldnestmax=3

" Quick navigation shortcuts for .zolo files
autocmd FileType zolo nnoremap <buffer> <leader>zm /zMachine:<CR>
autocmd FileType zolo nnoremap <buffer> <leader>zu /user_preferences:<CR>
autocmd FileType zolo nnoremap <buffer> <leader>zb /zBifrost:<CR>
autocmd FileType zolo nnoremap <buffer> <leader>zr /zRBAC:<CR>

" Auto-format on save (optional)
" autocmd BufWritePre *.zolo normal gg=G``
