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
