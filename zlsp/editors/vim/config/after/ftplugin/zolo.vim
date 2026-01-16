" ═══════════════════════════════════════════════════════════════
" Zolo LSP - File Type Plugin (Auto-loads for .zolo files)
" ═══════════════════════════════════════════════════════════════
" File: after/ftplugin/zolo.vim
" Purpose: Runs AFTER vim-lsp loads, when opening .zolo files
" Installation: Copied to ~/.vim/after/ftplugin/ by zlsp-vim-install
" ═══════════════════════════════════════════════════════════════

" Only run once per buffer
if exists('b:did_zolo_lsp_ftplugin')
  finish
endif
let b:did_zolo_lsp_ftplugin = 1

" Disable syntax file (LSP semantic tokens provide better highlighting)
" This prevents syntax patterns from interfering with semantic tokens
setlocal syntax=OFF

" Buffer-local LSP settings
setlocal omnifunc=lsp#complete
setlocal signcolumn=yes
setlocal updatetime=300

" LSP keybindings (only for .zolo files)
nnoremap <buffer> K :LspHover<CR>
nnoremap <buffer> gd :LspDefinition<CR>
nnoremap <buffer> gr :LspReferences<CR>
nnoremap <buffer> gi :LspImplementation<CR>
nnoremap <buffer> <leader>rn :LspRename<CR>
nnoremap <buffer> [d :LspPreviousDiagnostic<CR>
nnoremap <buffer> ]d :LspNextDiagnostic<CR>

" Enable LSP formatting on save (optional)
" autocmd BufWritePre <buffer> LspDocumentFormat

" ═══════════════════════════════════════════════════════════════
" Zolo LSP Semantic Token Colors (Applied directly, not via autocmd)
" ═══════════════════════════════════════════════════════════════

" Clear any conflicting syntax highlighting (ONLY for this buffer)
highlight! Identifier gui=NONE cterm=NONE
highlight! Keyword gui=NONE cterm=NONE
highlight! Constant gui=NONE cterm=NONE
highlight! Special gui=NONE cterm=NONE

" Root keys (salmon/orange)
highlight! LspSemanticRootKey ctermfg=216 guifg=#ffaf87 cterm=NONE gui=NONE term=NONE

" Nested keys (golden yellow)
highlight! LspSemanticNestedKey ctermfg=222 guifg=#ffd787 cterm=NONE gui=NONE term=NONE

" Strings (light cream yellow)
highlight! LspSemanticString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE

" Version strings (same as strings)
highlight! LspSemanticVersionString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE

" Numbers (dark orange)
highlight! LspSemanticNumber ctermfg=214 guifg=#FF8C00 cterm=NONE gui=NONE term=NONE

" Type hints (lavender)
highlight! LspSemanticTypeHint ctermfg=81 guifg=#5fd7ff cterm=NONE gui=NONE term=NONE

" Type hint parentheses (soft yellow)
highlight! LspSemanticTypeHintParen ctermfg=227 guifg=#ffff5f cterm=NONE gui=NONE term=NONE

" Array brackets (light pink/cream)
highlight! LspSemanticBracketStructural ctermfg=225 guifg=#ffd7ff cterm=NONE gui=NONE term=NONE

" Booleans (deep blue - distinct from type hints)
highlight! LspSemanticBoolean ctermfg=33 guifg=#0087ff cterm=NONE gui=NONE term=NONE

" Comments (gray, italic)
highlight! LspSemanticComment ctermfg=242 guifg=#6c6c6c cterm=italic gui=italic term=NONE
