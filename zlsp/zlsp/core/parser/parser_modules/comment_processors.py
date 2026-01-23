"""
Comment Processors - Comment stripping and tokenization

Handles Zolo's dual comment syntax:
- Full-line comments: # at line start
- Inline comments: #> ... <#
"""

from typing import Tuple

from ...lsp_types import TokenType


# Forward reference for type hints - actual import happens at module level
TYPE_CHECKING = False
if TYPE_CHECKING:
    from .token_emitter import TokenEmitter


def strip_comments_and_prepare_lines(content: str) -> Tuple[list[str], dict]:
    """
    Strip comments from .zolo content.
    
    Rules:
    - Full-line comments: # at line start (after optional whitespace at any indent level)
    - Inline comments: #> ... <# (paired delimiters)
    - Multi-line comments supported with #> ... <#
    - Unpaired #> or <# are treated as literal text
    - # without > is a literal character (hex colors, hashtags, etc.)
    - EXCEPTION: Lines inside zMD.content/zText.content are NOT treated as comments (markdown syntax!)
    - Skip empty lines after comment removal
    - Preserve indentation
    
    Args:
        content: Raw .zolo file content
    
    Returns:
        Tuple of (cleaned_lines, line_mapping)
        - cleaned_lines: List of cleaned lines (no comments, no empty lines)
        - line_mapping: Dict mapping cleaned line index to original line number (1-based)
    """
    lines = content.splitlines()
    
    # Phase 0: Identify multiline string contexts (zMD.content, zText.content, etc.)
    # Lines inside these contexts should NOT have # stripped (it's markdown syntax!)
    multiline_string_lines = set()
    
    for line_num, line in enumerate(lines):
        indent = len(line) - len(line.lstrip())
        stripped = line.lstrip()
        
        # Check if this line starts a multiline string context
        # Pattern: "content:" under zMD/zText, or other auto-multiline properties
        if stripped.startswith('content:') or stripped.startswith('label:'):
            # Look back to see if parent is zMD or zText
            parent_indent = None
            parent_key = None
            for prev_line_num in range(line_num - 1, -1, -1):
                prev_line = lines[prev_line_num]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                prev_stripped = prev_line.lstrip()
                
                if prev_indent < indent and prev_stripped and ':' in prev_stripped:
                    parent_indent = prev_indent
                    parent_key = prev_stripped.split(':')[0].strip().lower()
                    break
            
            # If parent is zMD or zText, mark subsequent indented lines as multiline string
            if parent_key in ('zmd', 'ztext'):
                # Mark all subsequent lines with greater indentation as multiline string content
                for next_line_num in range(line_num + 1, len(lines)):
                    next_line = lines[next_line_num]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    next_stripped = next_line.lstrip()
                    
                    # Stop if we hit a line with equal/less indentation that has a key
                    if next_indent <= indent and next_stripped and ':' in next_stripped:
                        break
                    
                    # Stop if we hit an empty line followed by a key at same/less indent
                    if not next_stripped:
                        # Check next non-empty line
                        for check_num in range(next_line_num + 1, len(lines)):
                            check_line = lines[check_num]
                            check_indent = len(check_line) - len(check_line.lstrip())
                            check_stripped = check_line.lstrip()
                            if check_stripped:
                                if check_indent <= indent and ':' in check_stripped:
                                    # Stop here, this is the end of multiline
                                    break
                                break
                    
                    # This line is inside multiline string context
                    if next_indent > indent or not next_stripped:
                        multiline_string_lines.add(next_line_num)
    
    # Phase 1: Identify full-line comments (EXCEPT lines inside multiline string contexts)
    full_line_comment_lines = set()
    for line_num, line in enumerate(lines):
        # Skip if this line is inside a multiline string context
        if line_num in multiline_string_lines:
            continue
        
        stripped = line.lstrip()
        if stripped.startswith('#') and not stripped.startswith('#>'):
            full_line_comment_lines.add(line_num)
    
    # Phase 2: Find all #> ... <# comments (including multi-line)
    comment_line_ranges = []  # Store (start_line, start_col, end_line, end_col) tuples
    
    search_pos = 0
    while search_pos < len(content):
        # Find opening #>
        start = content.find('#>', search_pos)
        if start == -1:
            break  # No more arrow comments
        
        # Check if this #> is within a full-line comment
        start_line = content[:start].count('\n')
        if start_line in full_line_comment_lines:
            # Skip this #>, it's inside a full-line comment
            search_pos = start + 2
            continue
        
        # Find matching closing <#
        end = content.find('<#', start + 2)
        if end == -1:
            # No matching <# found, skip this #>
            search_pos = start + 2
            continue
        
        # Store this comment range (from #> to <# inclusive)
        start_col = start - content.rfind('\n', 0, start) - 1
        end_line = content[:end + 2].count('\n')
        end_col = end + 2 - content.rfind('\n', 0, end + 2) - 1
        
        comment_line_ranges.append((start_line, start_col, end_line, end_col))
        search_pos = end + 2
    
    # Phase 3: Build cleaned lines (remove comments, skip full-line comments)
    cleaned_lines = []
    line_mapping = {}  # Maps cleaned index -> original line number (1-based)
    
    for line_num, line in enumerate(lines):
        # Skip full-line comments
        if line_num in full_line_comment_lines:
            continue
        
        # Remove inline comments from this line
        working_line = line
        for c_start_line, c_start_col, c_end_line, c_end_col in comment_line_ranges:
            if c_start_line == c_end_line == line_num:
                # Single-line comment on this line
                working_line = working_line[:c_start_col] + working_line[c_end_col:]
            elif c_start_line == line_num:
                # This line starts a multi-line comment - remove from comment start to end of line
                working_line = working_line[:c_start_col]
            elif c_start_line < line_num < c_end_line:
                # This line is in the middle of a multi-line comment - skip it entirely
                working_line = ""
                break
            elif c_end_line == line_num:
                # This line ends a multi-line comment - keep text after <#
                working_line = working_line[c_end_col:]
        
        # Strip trailing whitespace (but preserve leading indentation)
        working_line = working_line.rstrip()
        
        # Skip empty lines
        if working_line:
            line_mapping[len(cleaned_lines)] = line_num + 1  # 1-based line numbers
            cleaned_lines.append(working_line)
    
    return cleaned_lines, line_mapping


def strip_comments_and_prepare_lines_with_tokens(content: str, emitter: 'TokenEmitter') -> Tuple[list[str], dict]:
    """
    Strip comments and prepare lines while emitting comment tokens.
    Handles both full-line comments and multi-line #> ... <# comments.
    
    EXCEPTION: Lines inside zMD.content/zText.content are NOT treated as comments (markdown syntax!)
    
    Returns:
        Tuple of (cleaned_lines, line_mapping)
        line_mapping maps cleaned line index to original line number
    """
    lines = content.splitlines()
    
    # Phase 0: Identify multiline string contexts (zMD.content, zText.content, etc.)
    # Lines inside these contexts should NOT have # stripped (it's markdown syntax!)
    multiline_string_lines = set()
    
    for line_num, line in enumerate(lines):
        indent = len(line) - len(line.lstrip())
        stripped = line.lstrip()
        
        # Check if this line starts a multiline string context
        # Pattern: "content:" under zMD/zText, or other auto-multiline properties
        if stripped.startswith('content:') or stripped.startswith('label:'):
            # Look back to see if parent is zMD or zText
            parent_indent = None
            parent_key = None
            for prev_line_num in range(line_num - 1, -1, -1):
                prev_line = lines[prev_line_num]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                prev_stripped = prev_line.lstrip()
                
                if prev_indent < indent and prev_stripped and ':' in prev_stripped:
                    parent_indent = prev_indent
                    parent_key = prev_stripped.split(':')[0].strip().lower()
                    break
            
            # If parent is zMD or zText, mark subsequent indented lines as multiline string
            if parent_key in ('zmd', 'ztext'):
                # Mark all subsequent lines with greater indentation as multiline string content
                for next_line_num in range(line_num + 1, len(lines)):
                    next_line = lines[next_line_num]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    next_stripped = next_line.lstrip()
                    
                    # Stop if we hit a line with equal/less indentation that has a key
                    if next_indent <= indent and next_stripped and ':' in next_stripped:
                        break
                    
                    # Stop if we hit an empty line followed by a key at same/less indent
                    if not next_stripped:
                        # Check next non-empty line
                        for check_num in range(next_line_num + 1, len(lines)):
                            check_line = lines[check_num]
                            check_indent = len(check_line) - len(check_line.lstrip())
                            check_stripped = check_line.lstrip()
                            if check_stripped:
                                if check_indent <= indent and ':' in check_stripped:
                                    # Stop here, this is the end of multiline
                                    break
                                break
                    
                    # This line is inside multiline string context
                    if next_indent > indent or not next_stripped:
                        multiline_string_lines.add(next_line_num)
    
    # Phase 1: Identify full-line comments (EXCEPT lines inside multiline string contexts)
    # Full-line comments can appear at any indentation level
    # A line is a full-line comment if it starts with # (after optional whitespace) but not #>
    full_line_comment_lines = set()
    for line_num, line in enumerate(lines):
        # Skip if this line is inside a multiline string context
        if line_num in multiline_string_lines:
            continue
        
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        # A line is a full-line comment if it starts with # (but not #>)
        if stripped.startswith('#') and not stripped.startswith('#>'):
            full_line_comment_lines.add(line_num)
            # Emit token for this full-line comment (starting from first # character to end of line)
            # Use the full line length (minus any trailing newline) to ensure we cover everything
            comment_length = len(line) - indent  # From first # to end of line
            emitter.emit(line_num, indent, comment_length, TokenType.COMMENT)
            # Track this comment range to prevent other tokens from overlapping
            emitter.add_comment_range(line_num, indent, line_num, len(line))
    
    # Phase 2: Find and emit all #> ... <# comments (including multi-line)
    # Only search in content that's NOT part of full-line comments
    comment_char_ranges = []  # Store (char_start, char_end) tuples in original content
    comment_line_ranges = []  # Store (start_line, start_col, end_line, end_col) tuples
    
    search_pos = 0
    while search_pos < len(content):
        # Find opening #>
        start = content.find('#>', search_pos)
        if start == -1:
            break  # No more arrow comments
        
        # Check if this #> is within a full-line comment
        start_line = content[:start].count('\n')
        if start_line in full_line_comment_lines:
            # Skip this #>, it's inside a full-line comment
            search_pos = start + 2
            continue
        
        # Find matching closing <#
        end = content.find('<#', start + 2)
        if end == -1:
            # No matching <# found, skip this #>
            search_pos = start + 2
            continue
        
        # Store this comment range (from #> to <# inclusive)
        comment_char_ranges.append((start, end + 2))
        search_pos = end + 2
    
    # Emit comment tokens for all found ranges
    for char_start, char_end in comment_char_ranges:
        # Convert absolute character positions to line/column
        start_line = content[:char_start].count('\n')
        start_col = char_start - content.rfind('\n', 0, char_start) - 1
        
        end_line = content[:char_end].count('\n')
        end_col = char_end - content.rfind('\n', 0, char_end) - 1
        
        # Track this comment range to avoid overlapping tokens
        emitter.add_comment_range(start_line, start_col, end_line, end_col)
        comment_line_ranges.append((start_line, start_col, end_line, end_col))
        
        if start_line == end_line:
            # Single-line comment
            emitter.emit(start_line, start_col, char_end - char_start, TokenType.COMMENT)
            
            # Check if there's text after <# on the same line - emit as STRING
            line_text = lines[start_line]
            text_after = line_text[end_col:].strip()
            if text_after:
                # Find where the non-whitespace text starts
                after_start = end_col
                while after_start < len(line_text) and line_text[after_start].isspace():
                    after_start += 1
                if after_start < len(line_text):
                    emitter.emit(start_line, after_start, len(line_text) - after_start, TokenType.STRING)
        else:
            # Multi-line comment - emit separate tokens for each line
            # This is more compatible with LSP's semantic token format
            lines_in_comment = content[char_start:char_end].splitlines(keepends=False)
            current_line = start_line
            
            for i, line_text in enumerate(lines_in_comment):
                if i == 0:
                    # First line: from start_col to end of line
                    emitter.emit(current_line, start_col, len(lines[current_line]) - start_col, TokenType.COMMENT)
                elif i == len(lines_in_comment) - 1:
                    # Last line: from start of line to end_col
                    # Get the indentation of this line
                    actual_line = lines[current_line]
                    indent = len(actual_line) - len(actual_line.lstrip())
                    emitter.emit(current_line, indent, end_col - indent, TokenType.COMMENT)
                    
                    # Check if there's text after <# on the last line - emit as STRING
                    text_after = actual_line[end_col:].strip()
                    if text_after:
                        # Find where the non-whitespace text starts
                        after_start = end_col
                        while after_start < len(actual_line) and actual_line[after_start].isspace():
                            after_start += 1
                        if after_start < len(actual_line):
                            emitter.emit(current_line, after_start, len(actual_line) - after_start, TokenType.STRING)
                else:
                    # Middle lines: entire line is comment
                    actual_line = lines[current_line]
                    indent = len(actual_line) - len(actual_line.lstrip())
                    emitter.emit(current_line, indent, len(actual_line) - indent, TokenType.COMMENT)
                current_line += 1
    
    # Phase 3: Build cleaned lines (remove comments, skip full-line comments)
    cleaned_lines = []
    line_mapping = {}  # Maps cleaned index -> original line number
    pending_append = None  # Store text to append to previous cleaned line
    
    # Process each original line individually
    for line_num, line in enumerate(lines):
        # Skip full-line comments
        if line_num in full_line_comment_lines:
            continue
        
        # Remove inline comments from this line
        working_line = line
        for c_start_line, c_start_col, c_end_line, c_end_col in comment_line_ranges:
            if c_start_line == c_end_line == line_num:
                # Single-line comment on this line
                working_line = working_line[:c_start_col] + working_line[c_end_col:]
            elif c_start_line == line_num:
                # This line starts a multi-line comment - remove from comment start to end of line
                working_line = working_line[:c_start_col]
            elif c_start_line < line_num < c_end_line:
                # This line is in the middle of a multi-line comment - skip it entirely
                working_line = ""
                break
            elif c_end_line == line_num:
                # This line ends a multi-line comment - keep text after <#
                text_after = working_line[c_end_col:].strip()
                if text_after:
                    # Append this text to the line that started the comment
                    pending_append = text_after
                working_line = ""
                break
        
        # Handle pending append
        if pending_append and cleaned_lines:
            cleaned_lines[-1] += " " + pending_append
            pending_append = None
        
        # Strip trailing whitespace
        working_line = working_line.rstrip()
        
        # Skip empty lines
        if working_line:
            line_mapping[len(cleaned_lines)] = line_num
            cleaned_lines.append(working_line)
    
    return cleaned_lines, line_mapping
