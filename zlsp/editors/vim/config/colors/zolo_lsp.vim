" ═══════════════════════════════════════════════════════════════
" Zolo LSP Semantic Token Colors
" ═══════════════════════════════════════════════════════════════
" File: colors/zolo_lsp.vim
" Purpose: Color scheme for .zolo files with LSP semantic tokens
" Installation: Auto-loaded by after/ftplugin/zolo.vim
"
" NOTE: All highlights are scoped to .zolo files only via autocmd
" This file is NON-DESTRUCTIVE and won't affect other file types
" ═══════════════════════════════════════════════════════════════

" Only run once
if exists('g:loaded_zolo_lsp_colors')
  finish
endif
let g:loaded_zolo_lsp_colors = 1

" ═══════════════════════════════════════════════════════════════
" Zolo-Specific Semantic Token Highlights
" ═══════════════════════════════════════════════════════════════
" All highlights are applied via autocmd FileType zolo to ensure
" they only affect .zolo files and override any conflicting rules
" ═══════════════════════════════════════════════════════════════

augroup ZoloLSPColors
  autocmd!
  
  " Root keys (salmon/orange)
  autocmd FileType zolo highlight! LspSemanticRootKey ctermfg=216 guifg=#ffaf87 cterm=NONE gui=NONE term=NONE
  
  " Nested keys (golden yellow)
  autocmd FileType zolo highlight! LspSemanticNestedKey ctermfg=222 guifg=#ffd787 cterm=NONE gui=NONE term=NONE
  
  " Strings (light cream yellow)
  autocmd FileType zolo highlight! LspSemanticString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE
  
  " Version strings (same as strings)
  autocmd FileType zolo highlight! LspSemanticVersionString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE
  
  " Numbers (dark orange)
  autocmd FileType zolo highlight! LspSemanticNumber ctermfg=214 guifg=#FF8C00 cterm=NONE gui=NONE term=NONE
  
  " Type hints (cyan)
  autocmd FileType zolo highlight! LspSemanticTypeHint ctermfg=81 guifg=#5fd7ff cterm=NONE gui=NONE term=NONE
  
  " Type hint parentheses (soft yellow)
  autocmd FileType zolo highlight! LspSemanticTypeHintParen ctermfg=227 guifg=#ffff5f cterm=NONE gui=NONE term=NONE
  
  " Array brackets (light pink/cream)
  autocmd FileType zolo highlight! LspSemanticBracketStructural ctermfg=225 guifg=#ffd7ff cterm=NONE gui=NONE term=NONE
  
  " Booleans (deep blue - distinct from type hints)
  autocmd FileType zolo highlight! LspSemanticBoolean ctermfg=33 guifg=#0087ff cterm=NONE gui=NONE term=NONE
  
  " Comments (gray, italic)
  autocmd FileType zolo highlight! LspSemanticComment ctermfg=242 guifg=#6c6c6c cterm=italic gui=italic term=NONE
  
  " Clear any conflicting syntax highlighting (ONLY for .zolo files)
  autocmd FileType zolo highlight! Identifier gui=NONE cterm=NONE
  autocmd FileType zolo highlight! Keyword gui=NONE cterm=NONE
  autocmd FileType zolo highlight! Constant gui=NONE cterm=NONE
  autocmd FileType zolo highlight! Special gui=NONE cterm=NONE
augroup END

" ═══════════════════════════════════════════════════════════════
" Color Palette Reference (256-color ANSI)
" ═══════════════════════════════════════════════════════════════
" 33  - Deep blue (booleans)
" 81  - Cyan (type hints)
" 214 - Dark orange (numbers)
" 216 - Salmon/orange (root keys)
" 222 - Golden yellow (nested keys)
" 225 - Light pink/cream (array brackets)
" 227 - Soft yellow (type hint parentheses)
" 230 - Light cream (strings, version strings)
" 242 - Gray (comments)
" ═══════════════════════════════════════════════════════════════
