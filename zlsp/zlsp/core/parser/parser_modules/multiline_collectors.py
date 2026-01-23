"""
Multiline Collectors - Collect multi-line values

Pure string processing, no dependencies.
Handles: (str) hints, dash lists, bracket arrays, pipes, triple quotes.

SEMANTIC MULTILINE JOINING:
- zText properties → Join with ' ' (space) for .zolo readability
- zMD properties → Join with '\x1F' (Unit Separator) for <br> rendering
- Other properties → Join with '\n' (default/backward compatible)
"""

from typing import Tuple, List, Optional

# Special character to mark zMD natural multilines (Unit Separator)
# This allows renderers to distinguish from explicit \n escapes
YAML_LINE_BREAK = '\x1F'


def collect_str_hint_multiline(
    lines: list[str], 
    start_idx: int, 
    parent_indent: int, 
    first_value: str,
    parent_key: Optional[str] = None
) -> Tuple[str, int]:
    """
    Collect multi-line string content when (str) type hint is used (YAML-style).
    
    Rule: Collect lines indented MORE than parent, strip base indent, preserve relative.
    
    SEMANTIC JOINING based on parent_key:
    - 'ztext' or 'content' under ztext → Join with ' ' (space) for readability
    - 'zmd' or 'content' under zmd → Join with '\x1F' (Unit Separator) for <br>
    - Other keys → Join with '\n' (backward compatible)
    
    Args:
        lines: All lines
        start_idx: Index to start collecting from (line after the key)
        parent_indent: Indentation level of the parent key
        first_value: The value on the same line as the key (if any)
        parent_key: The key name (used for semantic joining)
    
    Returns:
        Tuple of (multiline_string, lines_consumed)
    
    Examples:
        >>> # zText: space-joined
        >>> lines = ["  continues", "  here"]
        >>> collect_str_hint_multiline(lines, 0, 0, "First", "zText")
        ("First continues here", 2)
        
        >>> # zMD: line-break-joined
        >>> lines = ["  continues", "  here"]
        >>> collect_str_hint_multiline(lines, 0, 0, "First", "zMD")
        ("First\\x1Fcontinues\\x1Fhere", 2)
    """
    collected = []
    
    # Add first value if present
    if first_value:
        collected.append(first_value)
    
    base_indent = None
    lines_consumed = 0
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Stop if line is at same or less indent than parent (unless empty)
        if stripped and line_indent <= parent_indent:
            break
        
        # Stop if this looks like a new key at the same level
        if stripped and ':' in stripped and line_indent <= parent_indent:
            break
        
        # Empty line - preserve it (will be joined with separator)
        if not stripped:
            collected.append('')
            lines_consumed += 1
            continue
        
        # Set base indent from first content line
        if base_indent is None:
            base_indent = line_indent
        
        # Strip base indent, keep relative
        if base_indent is not None:
            if line_indent >= base_indent:
                relative_line = line[base_indent:] if len(line) >= base_indent else line.strip()
                collected.append(relative_line)
            else:
                collected.append(line.strip())
        else:
            collected.append(line.strip())
        
        lines_consumed += 1
    
    # Determine join character based on parent key
    clean_key = parent_key.split('__dup')[0].lower() if parent_key else None
    
    if clean_key == 'ztext':
        # zText: Join with space for .zolo readability
        join_char = ' '
    elif clean_key == 'zmd':
        # zMD: Join with Unit Separator for <br> rendering
        join_char = YAML_LINE_BREAK
    else:
        # Default: backward compatible newline joining
        join_char = '\n'
    
    return join_char.join(collected), lines_consumed


def collect_dash_list(lines: list[str], start_idx: int, parent_indent: int) -> Tuple[str, int, list]:
    """
    Collect YAML-style dash list items (- item1, - item2, etc.).
    
    Rules:
    - Detect lines starting with "- " at child indent level
    - Collect consecutive dash items
    - Stop when indent returns to parent level or less
    - Track each item's line number for token emission
    
    Args:
        lines: All lines
        start_idx: Index to start collecting from (line after the key)
        parent_indent: Indentation level of the parent key
    
    Returns:
        Tuple of (reconstructed_array_string, lines_consumed, item_line_info)
        - reconstructed_array_string: "[item1, item2, item3]"
        - lines_consumed: Number of lines consumed
        - item_line_info: List of (line_idx, dash_pos, item_content) for token emission
    
    Examples:
        >>> lines = ["  - item1", "  - item2", "  - item3"]
        >>> collect_dash_list(lines, 0, 0)
        ("[item1, item2, item3]", 3, [(0, 2, "item1"), (1, 2, "item2"), (2, 2, "item3")])
    """
    collected_items = []
    item_line_info = []  # Track (line_idx, dash_position, content) for each item
    lines_consumed = 0
    expected_indent = None
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            lines_consumed += 1
            continue
        
        # Check if line starts with dash
        if stripped.startswith('- '):
            # Set expected indent from first dash item
            if expected_indent is None:
                expected_indent = line_indent
            
            # Verify this dash is at the expected child indent level
            if line_indent != expected_indent:
                # Different indent level - stop collecting
                break
            
            # Extract item content (everything after "- ")
            item_content = stripped[2:].strip()
            
            if item_content:
                collected_items.append(item_content)
                # Track line index, dash position (for tokenization), and content
                dash_pos = line.index('-')
                item_line_info.append((i, dash_pos, item_content))
            
            lines_consumed += 1
        else:
            # Non-dash line - check if it's at parent indent or less
            if line_indent <= parent_indent:
                # Back to parent level - stop collecting
                break
            else:
                # Could be continuation or nested content - for now, stop
                # TODO: Future enhancement - support nested structures under dash items
                break
    
    # Reconstruct as single-line array format
    if collected_items:
        reconstructed = '[' + ', '.join(collected_items) + ']'
    else:
        reconstructed = '[]'
    
    return reconstructed, lines_consumed, item_line_info


def collect_bracket_array(lines: list[str], start_idx: int, parent_indent: int, first_value: str) -> Tuple[str, int, list]:
    """
    Collect multi-line array content from opening [ to closing ].
    
    SUPPORTS NESTED ARRAYS:
    - Recursively handles nested [nested_items] within arrays
    - Properly tracks bracket depth to find matching closing ]
    
    Rules:
    - Opening [ is on the key line (first_value = '[')
    - Collect lines indented MORE than parent
    - Stop when we find ] that closes THIS array level
    - Track each item's line number for token emission
    
    Args:
        lines: All lines
        start_idx: Index to start collecting from (line after opening [)
        parent_indent: Indentation level of the parent key with opening [
        first_value: The value on the same line as the key (should be '[')
    
    Returns:
        Tuple of (reconstructed_array_string, lines_consumed, item_line_info)
        - reconstructed_array_string: "[item1, item2, [nested1, nested2]]"
        - lines_consumed: Number of lines consumed (NOT including opening [)
        - item_line_info: List of (line_idx, item_content, has_comma) for token emission
    
    Examples:
        >>> lines = ["  item1,", "  item2,", "  item3", "]"]
        >>> collect_bracket_array(lines, 0, 0, "[")
        ("[item1, item2, item3]", 4, [(0, "item1", True), (1, "item2", True), (2, "item3", False)])
        
        >>> lines = ["  item1,", "  [", "    nested1,", "    nested2", "  ]", "  item3", "]"]
        >>> collect_bracket_array(lines, 0, 0, "[")
        ("[item1, [nested1, nested2], item3]", 7, [...])
    """
    collected_items = []
    item_line_info = []  # Track (line_idx, content, has_comma) for each item
    lines_consumed = 0
    
    # Determine the content indent level (first non-empty line's indent)
    content_indent = None
    for j in range(start_idx, len(lines)):
        test_line = lines[j].strip()
        if test_line and test_line != ']':
            content_indent = len(lines[j]) - len(lines[j].lstrip())
            break
    
    if content_indent is None:
        content_indent = parent_indent + 4  # Default fallback
    
    i = start_idx
    while i < len(lines):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Check if this is the closing bracket for THIS level
        # It should be at an indent <= content_indent (back-dedented from content)
        if stripped == ']':
            # Add closing bracket to item_line_info for token emission
            item_line_info.append((i, ']', False))
            lines_consumed += 1
            break
        
        if stripped.startswith(']'):
            # Add closing bracket to item_line_info for token emission
            item_line_info.append((i, ']', False))
            lines_consumed += 1
            break
        
        # Skip empty lines
        if not stripped:
            lines_consumed += 1
            i += 1
            continue
        
        # If line is dedented back to or past parent level, we might be done
        # (but ] should have been caught above)
        if line_indent < content_indent and stripped != '[':
            # This line is back-dedented - check if it's a closing bracket
            if ']' in stripped:
                break
        
        # Check if this is a nested array opening
        if stripped == '[':
            # Add the opening bracket to item_line_info for token emission
            item_line_info.append((i, '[', False))
            
            # Recursively collect the nested array starting from NEXT line
            nested_reconstructed, nested_consumed, nested_info = collect_bracket_array(
                lines, i + 1, line_indent, '['
            )
            
            # Add the nested array as a single item for reconstruction
            collected_items.append(nested_reconstructed)
            
            # Add all nested items to item_line_info for token emission
            item_line_info.extend(nested_info)
            
            # Skip past the nested array content (nested_consumed already counted)
            lines_consumed += nested_consumed + 1  # +1 for the [ line itself
            i += nested_consumed + 1
            continue
        
        # Regular array item
        # Remove trailing comma if present
        has_comma = stripped.endswith(',')
        item_content = stripped.rstrip(',').strip()
        
        if item_content and item_content != ']':
            collected_items.append(item_content)
            item_line_info.append((i, item_content, has_comma))
        
        lines_consumed += 1
        i += 1
    
    # Reconstruct as single-line array format
    if collected_items:
        reconstructed = '[' + ', '.join(collected_items) + ']'
    else:
        reconstructed = '[]'
    
    return reconstructed, lines_consumed, item_line_info


def collect_pipe_multiline(
    lines: list[str], 
    start_idx: int, 
    parent_indent: int,
    parent_key: Optional[str] = None
) -> Tuple[str, int]:
    """
    Collect multi-line string content after pipe | marker.
    
    Args:
        lines: All lines
        start_idx: Index to start collecting from
        parent_indent: Indentation level of the parent key
        parent_key: The key name (used for semantic joining)
    
    Returns:
        Tuple of (multiline_string, lines_consumed)
    """
    collected = []
    base_indent = None
    lines_consumed = 0
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        
        # If we hit a line at or less than parent indent, we're done
        if line and line_indent <= parent_indent:
            break
        
        # Set base indent from first content line
        if base_indent is None and line.strip():
            base_indent = line_indent
        
        # Collect line, stripping base indentation
        if base_indent is not None:
            if line_indent >= base_indent:
                # Strip base indent, keep relative indent
                relative_line = line[base_indent:] if len(line) >= base_indent else line.strip()
                collected.append(relative_line)
            else:
                collected.append(line.strip())
        else:
            collected.append(line.strip())
        
        lines_consumed += 1
    
    # Determine join character based on parent key
    clean_key = parent_key.split('__dup')[0].lower() if parent_key else None
    
    if clean_key == 'ztext':
        join_char = ' '
    elif clean_key == 'zmd':
        join_char = YAML_LINE_BREAK
    else:
        join_char = '\n'
    
    return join_char.join(collected), lines_consumed


def collect_triple_quote_multiline(
    lines: list[str], 
    start_idx: int, 
    initial_value: str,
    parent_key: Optional[str] = None
) -> Tuple[str, int]:
    '''
    Collect multi-line string content between triple quotes.
    
    Args:
        lines: All lines
        start_idx: Index of the line with opening triple-quotes
        initial_value: The value part (might contain opening and/or closing triple-quotes)
        parent_key: The key name (used for semantic joining)
    
    Returns:
        Tuple of (multiline_string, lines_consumed)
    '''
    # Check if it's all on one line: """content"""
    if initial_value.count('"""') >= 2:
        # Extract content between quotes
        content = initial_value.split('"""', 2)[1]
        return content, 0
    
    # Multi-line case: collect until closing """
    collected = []
    lines_consumed = 0
    
    # First line might have content after opening """
    first_line_content = initial_value[3:].strip()  # Remove opening """
    if first_line_content:
        collected.append(first_line_content)
    
    # Collect subsequent lines
    base_indent = None
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        lines_consumed += 1
        
        # Check for closing """
        if '"""' in line:
            # Get content before closing """
            closing_content = line.split('"""')[0]
            if base_indent is None and closing_content.strip():
                base_indent = len(line) - len(line.lstrip())
            if closing_content.strip():
                if base_indent is not None:
                    relative_line = closing_content[base_indent:] if len(closing_content) >= base_indent else closing_content.strip()
                    collected.append(relative_line.rstrip())
                else:
                    collected.append(closing_content.strip())
            break
        
        # Set base indent from first content line
        if base_indent is None and line.strip():
            base_indent = len(line) - len(line.lstrip())
        
        # Collect line, stripping base indentation
        if base_indent is not None:
            line_indent = len(line) - len(line.lstrip())
            if line_indent >= base_indent:
                relative_line = line[base_indent:] if len(line) >= base_indent else line.strip()
                collected.append(relative_line.rstrip())
            else:
                collected.append(line.strip())
        else:
            collected.append(line.rstrip())
    
    # Determine join character based on parent key
    clean_key = parent_key.split('__dup')[0].lower() if parent_key else None
    
    if clean_key == 'ztext':
        join_char = ' '
    elif clean_key == 'zmd':
        join_char = YAML_LINE_BREAK
    else:
        join_char = '\n'
    
    return join_char.join(collected), lines_consumed
