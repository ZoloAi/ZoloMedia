" ═══════════════════════════════════════════════════════════════
" Zolo - Clear Syntax File Interference
" ═══════════════════════════════════════════════════════════════
" File: after/syntax/zolo.vim
" Purpose: Runs AFTER syntax/zolo.vim loads to clear conflicting groups
" 
" This file is loaded AFTER syntax/zolo.vim in Vim's load order,
" ensuring our highlight clearing happens LAST.
" ═══════════════════════════════════════════════════════════════

" Only run for zolo files
if &filetype !=# 'zolo'
  finish
endif

" Clear syntax highlighting groups that conflict with LSP semantic tokens
" The syntax file (syntax/zolo.vim) links keys to Identifier (bold),
" and delimiters to Delimiter (magenta). We clear these so LSP tokens
" can take precedence.

highlight! Identifier gui=NONE cterm=NONE
highlight! Keyword gui=NONE cterm=NONE
highlight! Constant gui=NONE cterm=NONE
highlight! Special gui=NONE cterm=NONE
highlight! Delimiter gui=NONE cterm=NONE ctermfg=NONE guifg=NONE

" Debug message (comment out in production)
" echom "zolo after/syntax loaded - cleared conflicting groups"
