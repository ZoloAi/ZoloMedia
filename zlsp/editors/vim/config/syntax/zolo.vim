" Vim syntax file for .zolo files
" Language: Zolo Configuration Format
" Maintainer: Zolo.ai
"
" Minimal fallback syntax (when LSP is not available)
" Based on vim-toml syntax approach
" For full semantic highlighting, use zlsp LSP server

if exists('b:current_syntax')
  finish
endif

" Comments
syn match zoloComment /#.*$/ contains=zoloTodo
syn keyword zoloTodo TODO FIXME NOTE XXX contained

" Keys (basic pattern)
syn match zoloKey /^\s*\zs[A-Za-z_][A-Za-z0-9_.-]*\ze\s*[:=]/

" Type hints
syn match zoloTypeHint /([a-z]\+)/

" Strings
syn region zoloString start=/"/ end=/"/ skip=/\\"/
syn region zoloString start=/'/ end=/'/ skip=/\\'/

" Numbers
syn match zoloNumber /\<[+-]\?\d\+\>/
syn match zoloNumber /\<[+-]\?\d\+\.\d\+\>/
syn match zoloNumber /\<[+-]\?\d\+[eE][+-]\?\d\+\>/
syn match zoloNumber /\<[+-]\?\d\+\.\d\+[eE][+-]\?\d\+\>/

" Booleans
syn keyword zoloBool true false yes no True False TRUE FALSE

" Null
syn keyword zoloNull null None

" Structural characters
syn match zoloDelimiter /[:\[\]{},-]/

" Color mappings (fallback - LSP provides semantic colors)
hi def link zoloComment Comment
hi def link zoloTodo Todo
hi def link zoloKey Identifier
hi def link zoloTypeHint Type
hi def link zoloString String
hi def link zoloNumber Number
hi def link zoloBool Boolean
hi def link zoloNull Constant
hi def link zoloDelimiter Delimiter

let b:current_syntax = 'zolo'
