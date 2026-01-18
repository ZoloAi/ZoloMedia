" ═══════════════════════════════════════════════════════════════
" Zolo LSP - Global Setup
" ═══════════════════════════════════════════════════════════════
" File: plugin/zolo_lsp.vim
" Purpose: Auto-loads on Vim startup to enable LSP features
" Installation: Copied to ~/.vim/plugin/ by zlsp-vim-install
" ═══════════════════════════════════════════════════════════════

" Enable semantic tokens globally
let g:lsp_semantic_enabled = 1

" Register zolo-lsp server with vim-lsp
" The autocmd fires when vim-lsp is ready (User lsp_setup event)
augroup ZoloLSPSetup
  autocmd!
  autocmd User lsp_setup call s:register_zolo_lsp()
augroup END

function! s:register_zolo_lsp()
  if executable('zolo-lsp')
    call lsp#register_server({
      \ 'name': 'zolo-lsp',
      \ 'cmd': {server_info->['zolo-lsp']},
      \ 'allowlist': ['zolo'],
      \ 'workspace_config': {},
      \ })
  endif
endfunction

" ═══════════════════════════════════════════════════════════════
" Disable Syntax Highlighting for .zolo Files (LSP Provides Better)
" ═══════════════════════════════════════════════════════════════
" The syntax file (syntax/zolo.vim) is just a fallback for when LSP
" is not available. When LSP is running, we want ONLY semantic tokens,
" not a mix of syntax + semantic. This prevents bold/color conflicts.
augroup ZoloDisableSyntax
  autocmd!
  " Disable syntax when .zolo file loads
  autocmd FileType zolo setlocal syntax=OFF
  " Also clear any lingering highlight groups from before syntax was disabled
  autocmd FileType zolo call s:clear_syntax_groups()
augroup END

function! s:clear_syntax_groups()
  " Clear default groups that might have been set before syntax=OFF
  highlight! Identifier gui=NONE cterm=NONE
  highlight! Keyword gui=NONE cterm=NONE
  highlight! Constant gui=NONE cterm=NONE
  highlight! Special gui=NONE cterm=NONE
  highlight! Delimiter gui=NONE cterm=NONE ctermfg=NONE guifg=NONE
endfunction
