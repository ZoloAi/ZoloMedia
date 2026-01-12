" ═══════════════════════════════════════════════════════════════
" Zolo LSP Semantic Token Colors
" ═══════════════════════════════════════════════════════════════
" File: zolo_highlights.vim
" Purpose: Color scheme for .zolo files with LSP semantic tokens
" Usage: Add to .vimrc: source ~/Projects/ZoloMedia/zlsp/editors/vim/config/zolo_highlights.vim
"
" NOTE: Format is LspSemanticTokenName (no underscore!)
" Using ctermfg for terminal compatibility (256-color palette)
" ═══════════════════════════════════════════════════════════════

" IMPORTANT: Clear default syntax highlighting that might interfere
highlight Identifier gui=NONE cterm=NONE
highlight clear Keyword
highlight clear Constant
highlight clear Special

" Root keys (salmon/orange) - TESTING: NO BOLD
highlight! LspSemanticRootKey guifg=#ffaf87 ctermfg=216 gui=NONE cterm=NONE

" Nested keys (lighter orange) - TESTING: NO BOLD
highlight! LspSemanticNestedKey guifg=#ffd787 ctermfg=222 gui=NONE cterm=NONE

" Strings (light yellow)
highlight LspSemanticString guifg=#fffbcb ctermfg=230 gui=NONE cterm=NONE

" Version strings (like strings - light yellow/cream)
highlight LspSemanticVersionString guifg=#fffbcb ctermfg=230 gui=NONE cterm=NONE

" Numbers (dark orange) - TESTING: NO BOLD
highlight LspSemanticNumber guifg=#FF8C00 ctermfg=214 gui=NONE cterm=NONE

" Type hints - revert to cyan for the text inside
highlight LspSemanticTypeHint guifg=#5fd7ff ctermfg=81 gui=NONE cterm=NONE

" Type hint parentheses (soft yellow)
syntax match zoloTypeHintParen /[()]/ containedin=zoloTypeHint contained
highlight zoloTypeHintParen guifg=#ffff5f ctermfg=227 gui=NONE cterm=NONE

" Array brackets (lighter yellow/cream)
highlight LspSemanticBracketStructural guifg=#ffd7ff ctermfg=225 gui=NONE cterm=NONE

" Booleans (deep blue)
highlight LspSemanticBoolean guifg=#0087ff ctermfg=33 gui=NONE cterm=NONE

" Comments (gray, italic)
highlight LspSemanticComment guifg=#6c6c6c ctermfg=242 gui=italic cterm=italic

" ═══════════════════════════════════════════════════════════════
" Force LSP Semantic Highlights (override after filetype loads)
" ═══════════════════════════════════════════════════════════════
augroup LspSemanticFix
  autocmd!
  autocmd FileType zolo highlight! LspSemanticRootKey ctermfg=216 guifg=#ffaf87 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticNestedKey ctermfg=222 guifg=#ffd787 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticVersionString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticNumber ctermfg=214 guifg=#FF8C00 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticTypeHint ctermfg=81 guifg=#5fd7ff cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticBoolean ctermfg=33 guifg=#0087ff cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticComment ctermfg=242 guifg=#6c6c6c cterm=italic gui=italic term=NONE
  autocmd FileType zolo highlight! LspSemanticBracketStructural ctermfg=225 guifg=#ffd7ff cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo syntax match zoloTypeHintParen /[()]/ containedin=zoloTypeHint contained
  autocmd FileType zolo highlight! zoloTypeHintParen ctermfg=227 guifg=#ffff5f cterm=NONE gui=NONE term=NONE
augroup END
