" Vim filetype plugin for .zolo files
" Language: Zolo Configuration Format
" Maintainer: Zolo Media
"
" Based on vim-toml by cespare (https://github.com/cespare/vim-toml)
" Adapted for .zolo files with zlsp LSP integration

if exists('b:did_ftplugin')
  finish
endif
let b:did_ftplugin = 1

let s:save_cpo = &cpo
set cpo&vim

" Comments
setlocal commentstring=#\ %s
setlocal comments=:#

" Indentation (2 spaces, like YAML/TOML)
setlocal expandtab
setlocal shiftwidth=2
setlocal softtabstop=2
setlocal tabstop=2

" Formatting
" - Don't auto-wrap text (formatoptions-=t)
" - Auto-insert comment leader (formatoptions+=cro)
" - Allow formatting of comments with gq (formatoptions+=q)
" - Long lines are not broken in insert mode (formatoptions+=l)
setlocal formatoptions-=t
setlocal formatoptions+=croql

" Folding (optional - based on indentation)
setlocal foldmethod=indent
setlocal foldlevel=99

" Don't let format options carry over to new lines
setlocal formatoptions-=o

" Match keywords for % navigation
if exists('loaded_matchit')
  let b:match_words = '\<\%(true\|false\|yes\|no\|null\)\>:\<\%(true\|false\|yes\|no\|null\)\>'
endif

" Undo settings
let b:undo_ftplugin = 'setl commentstring< comments< expandtab< shiftwidth< softtabstop< tabstop< formatoptions< foldmethod< foldlevel<'

let &cpo = s:save_cpo
unlet s:save_cpo
