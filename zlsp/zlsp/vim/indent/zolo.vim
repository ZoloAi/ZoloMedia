" Vim indent file for .zolo format
" Language: Zolo Configuration Format
" Maintainer: Zolo Team

if exists("b:did_indent")
  finish
endif
let b:did_indent = 1

" Zolo uses YAML-like indentation
setlocal autoindent
setlocal smartindent
setlocal indentexpr=GetZoloIndent()
setlocal indentkeys=o,O,*<Return>,<:>,0-,0{,0},!^F

" Use 2 spaces for indentation (YAML standard)
setlocal tabstop=2
setlocal shiftwidth=2
setlocal softtabstop=2
setlocal expandtab

function! GetZoloIndent()
  " Get the line to be indented
  let lnum = v:lnum
  
  " At the start of file, use no indent
  if lnum == 1
    return 0
  endif
  
  " Find a non-blank line above the current line
  let prevlnum = prevnonblank(lnum - 1)
  
  " Hit the start of the file, use zero indent
  if prevlnum == 0
    return 0
  endif
  
  let prevline = getline(prevlnum)
  let currline = getline(lnum)
  let previndent = indent(prevlnum)
  
  " If the previous line ends with a colon, indent further
  if prevline =~ ':\s*$'
    return previndent + shiftwidth()
  endif
  
  " If the previous line ends with a colon and comment, indent further
  if prevline =~ ':\s*#'
    return previndent + shiftwidth()
  endif
  
  " If the current line is a key (contains colon), use same indent as previous key
  if currline =~ '^\s*\w\+:'
    " Check if previous line was also a key at same level
    if prevline =~ '^\s*\w\+:'
      return previndent
    endif
    " If previous was a value, dedent to previous key level
    return previndent - shiftwidth()
  endif
  
  " If current line starts with - (list item), maintain indent
  if currline =~ '^\s*-'
    return previndent
  endif
  
  " Default: maintain the indent of the previous line
  return previndent
endfunction
