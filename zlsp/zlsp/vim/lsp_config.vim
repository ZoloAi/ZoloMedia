" ═══════════════════════════════════════════════════════════════
" Zolo LSP Configuration for Vim/Neovim
" ═══════════════════════════════════════════════════════════════
"
" This configures Vim to use the Zolo Language Server for .zolo files.
" The LSP provides:
"   - Semantic highlighting (from parser.tokenize())
"   - Diagnostics (syntax errors, type mismatches)
"   - Hover information (type hints, documentation)
"   - Code completion (type hints, common values)
"
" Requirements:
"   - Neovim 0.8+ OR Vim 9+ with LSP plugin
"   - Python 3.8+ with zolo package installed
"   - zolo-lsp command available in PATH
"
" Installation:
"   1. Install zolo package: pip install -e /path/to/zLSP
"   2. Add this file to your Vim config:
"      - Neovim: ~/.config/nvim/after/ftplugin/zolo.vim
"      - Vim: ~/.vim/after/ftplugin/zolo.vim
"   3. Or source it from your vimrc/init.vim
"
" ═══════════════════════════════════════════════════════════════

" Only run once per buffer
if exists('b:zolo_lsp_configured')
  finish
endif
let b:zolo_lsp_configured = 1

" ───────────────────────────────────────────────────────────────
" Neovim Native LSP Configuration
" ───────────────────────────────────────────────────────────────
if has('nvim-0.8')
  lua << EOF
-- Check if LSP is already configured for this buffer
if vim.b.zolo_lsp_attached then
  return
end

-- Get or create LSP client for zolo
local client_id = vim.lsp.start({
  name = 'zolo-lsp',
  cmd = {'zolo-lsp'},
  root_dir = vim.fn.getcwd(),
  filetypes = {'zolo'},
  settings = {},
  capabilities = vim.lsp.protocol.make_client_capabilities(),
})

if client_id then
  vim.b.zolo_lsp_attached = true
  
  -- Enable semantic tokens (for syntax highlighting from LSP)
  vim.lsp.buf_attach_client(0, client_id)
  
  -- Optional: Set up keybindings
  local opts = { buffer = 0, silent = true }
  vim.keymap.set('n', 'K', vim.lsp.buf.hover, opts)
  vim.keymap.set('n', 'gd', vim.lsp.buf.definition, opts)
  vim.keymap.set('n', '<leader>ca', vim.lsp.buf.code_action, opts)
  vim.keymap.set('n', '<leader>rn', vim.lsp.buf.rename, opts)
  
  print('Zolo LSP attached')
else
  print('Failed to start Zolo LSP - ensure "zolo-lsp" is in PATH')
end
EOF

" ───────────────────────────────────────────────────────────────
" Vim with vim-lsp Plugin Configuration
" ───────────────────────────────────────────────────────────────
elseif !has('nvim') && isdirectory(expand('~/.vim/plugged/vim-lsp'))
  " Using prabirshrestha/vim-lsp plugin
  " Server registration is done in .vimrc via autocmd User lsp_setup
  
  " Enable LSP features for this buffer (these will activate when vim-lsp loads)
  setlocal omnifunc=lsp#complete
  
  " Optional keybindings
  nnoremap <buffer> <silent> K :LspHover<CR>
  nnoremap <buffer> <silent> gd :LspDefinition<CR>
  nnoremap <buffer> <silent> <leader>ca :LspCodeAction<CR>
  nnoremap <buffer> <silent> <leader>rn :LspRename<CR>
  nnoremap <buffer> <silent> <leader>d :LspDocumentDiagnostics<CR>
  
  echo 'Zolo LSP configured (vim-lsp)'

" ───────────────────────────────────────────────────────────────
" Fallback: Basic Syntax Highlighting Only
" ───────────────────────────────────────────────────────────────
else
  " No LSP available - use basic syntax highlighting
  " This is a minimal fallback for older Vim versions
  
  " Comments
  syntax match zoloComment /#.*$/ contains=zoloTodo
  syntax keyword zoloTodo TODO FIXME NOTE XXX contained
  
  " Keys (approximate)
  syntax match zoloKey /^\s*\w\+:/
  
  " Strings
  syntax region zoloString start=/"/ end=/"/ skip=/\\"/
  syntax region zoloString start=/'/ end=/'/ skip=/\\'/
  
  " Numbers
  syntax match zoloNumber /\<\d\+\>/
  syntax match zoloNumber /\<\d\+\.\d\+\>/
  
  " Booleans
  syntax keyword zoloBool true false yes no True False
  
  " Null
  syntax keyword zoloNull null None
  
  " Colors (basic fallback)
  highlight link zoloComment Comment
  highlight link zoloTodo Todo
  highlight link zoloKey Identifier
  highlight link zoloString String
  highlight link zoloNumber Number
  highlight link zoloBool Boolean
  highlight link zoloNull Constant
  
  echo 'Zolo: Using basic syntax (LSP not available)'
endif

" ═══════════════════════════════════════════════════════════════
" Common Settings for All Configurations
" ═══════════════════════════════════════════════════════════════

" Indentation (2 spaces, like YAML)
setlocal expandtab
setlocal shiftwidth=2
setlocal softtabstop=2
setlocal tabstop=2

" Comments
setlocal commentstring=#\ %s
setlocal comments=:#

" Folding (optional)
setlocal foldmethod=indent
setlocal foldlevel=99

" Don't auto-insert comments on newline
setlocal formatoptions-=cro
