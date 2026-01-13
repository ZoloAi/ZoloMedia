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
" zKernel-specific Tokens
" ═══════════════════════════════════════════════════════════════

" zSpark root key (light green)
highlight! LspSemanticZsparkKey guifg=#87d787 ctermfg=114 gui=NONE cterm=NONE

" zConfig root key (light green)
highlight! LspSemanticZconfigKey guifg=#87d787 ctermfg=114 gui=NONE cterm=NONE

" zMachine editable keys (deep blue - user preferences)
highlight! LspSemanticZmachineEditableKey guifg=#0087ff ctermfg=33 gui=NONE cterm=NONE

" zMachine locked keys (dark red - auto-detected hardware)
highlight! LspSemanticZmachineLockedKey guifg=#d70000 ctermfg=160 gui=NONE cterm=NONE

" zSpark nested keys (purple)
highlight! LspSemanticZsparkNestedKey guifg=#875fd7 ctermfg=98 gui=NONE cterm=NONE

" zMode value (tomato red)
highlight! LspSemanticZsparkModeValue guifg=#ff0000 ctermfg=196 gui=NONE cterm=NONE

" zVaFile value (dark green)
highlight! LspSemanticZsparkVaFileValue guifg=#00d700 ctermfg=40 gui=NONE cterm=NONE

" zBlock value (salmon orange)
highlight! LspSemanticZsparkSpecialValue guifg=#ffaf87 ctermfg=216 gui=NONE cterm=NONE

" Environment/config values (bright yellow)
highlight! LspSemanticEnvConfigValue guifg=#ffff00 ctermfg=226 gui=NONE cterm=NONE

" zPath values (bright cyan)
highlight! LspSemanticZpathValue guifg=#00ffff ctermfg=51 gui=NONE cterm=NONE

" Escape sequences (bright orange)
highlight! LspSemanticEscapeSequence guifg=#ff0000 ctermfg=196 gui=NONE cterm=NONE

" Time strings (distinct from regular strings)
highlight! LspSemanticTimeString guifg=#ffd7af ctermfg=223 gui=NONE cterm=NONE

" Timestamp strings (distinct from regular strings)
highlight! LspSemanticTimestampString guifg=#ffd7af ctermfg=223 gui=NONE cterm=NONE

" Ratio strings (distinct from regular strings)
highlight! LspSemanticRatioString guifg=#ffd7af ctermfg=223 gui=NONE cterm=NONE

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
  " zKernel-specific tokens
  autocmd FileType zolo highlight! LspSemanticZsparkKey ctermfg=114 guifg=#87d787 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticZconfigKey ctermfg=114 guifg=#87d787 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticZmachineEditableKey ctermfg=33 guifg=#0087ff cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticZmachineLockedKey ctermfg=160 guifg=#d70000 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticZsparkNestedKey ctermfg=98 guifg=#875fd7 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticZsparkModeValue ctermfg=196 guifg=#ff0000 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticZsparkVaFileValue ctermfg=40 guifg=#00d700 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticZsparkSpecialValue ctermfg=216 guifg=#ffaf87 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticEnvConfigValue ctermfg=226 guifg=#ffff00 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticZpathValue ctermfg=51 guifg=#00ffff cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticEscapeSequence ctermfg=196 guifg=#ff0000 cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticTimeString ctermfg=223 guifg=#ffd7af cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticTimestampString ctermfg=223 guifg=#ffd7af cterm=NONE gui=NONE term=NONE
  autocmd FileType zolo highlight! LspSemanticRatioString ctermfg=223 guifg=#ffd7af cterm=NONE gui=NONE term=NONE
augroup END
