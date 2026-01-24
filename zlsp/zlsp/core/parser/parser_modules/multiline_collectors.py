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
    Collect YAML-style dash list items (- item1, - item2, etc.) with nested structure support.
    
    Rules:
    - Detect lines starting with "- " at child indent level
    - Collect consecutive dash items
    - Support nested dash lists (standalone dash followed by indented dashes)
    - Stop when indent returns to parent level or less
    - Track each item's line number AND continuation lines for token emission
    
    Args:
        lines: All lines
        start_idx: Index to start collecting from (line after the key)
        parent_indent: Indentation level of the parent key
    
    Returns:
        Tuple of (reconstructed_array_string, lines_consumed, item_line_info)
        - reconstructed_array_string: "[item1, item2, [nested1, nested2]]"
        - lines_consumed: Number of lines consumed
        - item_line_info: List of (line_idx, dash_pos, item_content, continuation_lines) for token emission
          - continuation_lines: List of (line_idx, content) for multiline items
    
    Examples:
        >>> lines = ["  - item1", "  - item2", "  - item3"]
        >>> collect_dash_list(lines, 0, 0)
        ("[item1, item2, item3]", 3, [(0, 2, "item1", []), (1, 2, "item2", []), (2, 2, "item3", [])])
    """
    collected_items = []
    item_line_info = []  # Track (line_idx, dash_position, content, continuation_lines) for each item
    lines_consumed = 0
    expected_indent = None
    
    i = start_idx
    while i < len(lines):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            lines_consumed += 1
            i += 1
            continue
        
        # Check if line starts with dash (either "- " or just "-" for standalone)
        if stripped.startswith('-') and (stripped == '-' or stripped.startswith('- ')):
            # Set expected indent from first dash item
            if expected_indent is None:
                expected_indent = line_indent
            
            # Verify this dash is at the expected child indent level
            if line_indent != expected_indent:
                # Different indent level - stop collecting
                break
            
            # Extract item content (everything after "- " or just the dash)
            if stripped == '-':
                item_content = ''  # Standalone dash
            else:
                item_content = stripped[2:].strip()  # After "- "
            dash_pos = line.index('-')
            
            if item_content:
                # Check if this is an inline object or array that spans multiple lines
                # Look for unclosed braces or brackets
                open_braces = item_content.count('{') - item_content.count('}')
                open_brackets = item_content.count('[') - item_content.count(']')
                
                # Check if next line is a natural YAML continuation (indented deeper, not a dash)
                has_natural_continuation = False
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    next_stripped = next_line.strip()
                    # Natural continuation: indented deeper than expected_indent, not a dash, not empty
                    if next_stripped and not next_stripped.startswith('- ') and next_indent > expected_indent:
                        has_natural_continuation = True
                
                # If we have unclosed braces/brackets OR natural continuations, collect continuation lines
                if open_braces > 0 or open_brackets > 0 or has_natural_continuation:
                    continuation_list = []  # Track (line_idx, content) for each continuation line
                    continuation_parts = []  # For reconstruction
                    continuation_consumed = 0
                    j = i + 1
                    
                    # Continue while we have unclosed braces/brackets OR natural continuations
                    while j < len(lines):
                        cont_line = lines[j]
                        cont_indent = len(cont_line) - len(cont_line.lstrip())
                        cont_stripped = cont_line.strip()
                        
                        # Stop if empty line (natural paragraph break)
                        if not cont_stripped:
                            break
                        
                        # Stop if line is at parent indent or less
                        if cont_indent <= parent_indent:
                            break
                        
                        # Stop if line is at dash indent or less (same level or above this dash)
                        if cont_indent <= expected_indent:
                            break
                        
                        # Stop if line is a dash at same or deeper level (new list item)
                        if cont_stripped.startswith('- '):
                            break
                        
                        # Add this line to continuation
                        continuation_list.append((j, cont_stripped))
                        continuation_parts.append(cont_stripped)
                        
                        # Update bracket/brace counts (for inline objects/arrays)
                        open_braces += cont_stripped.count('{') - cont_stripped.count('}')
                        open_brackets += cont_stripped.count('[') - cont_stripped.count(']')
                        
                        continuation_consumed += 1
                        j += 1
                        
                        # Stop if inline objects/arrays are closed AND next line is not a natural continuation
                        if open_braces == 0 and open_brackets == 0 and j < len(lines):
                            peek_line = lines[j]
                            peek_indent = len(peek_line) - len(peek_line.lstrip())
                            peek_stripped = peek_line.strip()
                            # If next line is not deeper indented, we're done
                            if not peek_stripped or peek_indent <= expected_indent or peek_stripped.startswith('- '):
                                break
                    
                    # Join continuation lines with space for reconstruction
                    if continuation_parts:
                        full_item = item_content + ' ' + ' '.join(continuation_parts)
                    else:
                        full_item = item_content
                    
                    collected_items.append(full_item)
                    item_line_info.append((i, dash_pos, item_content, continuation_list))
                    lines_consumed += 1 + continuation_consumed
                    i += 1 + continuation_consumed
                else:
                    # Regular dash item with content on same line (no multiline)
                    collected_items.append(item_content)
                    item_line_info.append((i, dash_pos, item_content, []))
                    lines_consumed += 1
                    i += 1
            else:
                # Standalone dash - check if there are nested dash items
                item_line_info.append((i, dash_pos, '', []))  # Track standalone dash for tokenization
                lines_consumed += 1
                
                # Look ahead for nested dash items at deeper indent (next line, i+1)
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    next_stripped = next_line.strip()
                    
                    if next_stripped.startswith('- ') and next_indent > expected_indent:
                        # Recursively collect nested dash list
                        nested_reconstructed, nested_consumed, nested_line_info = collect_dash_list(
                            lines, i + 1, expected_indent
                        )
                        collected_items.append(nested_reconstructed)
                        item_line_info.extend(nested_line_info)
                        lines_consumed += nested_consumed
                        i += nested_consumed + 1  # +1 for the standalone dash we already counted
                    else:
                        # Standalone dash with no nested content - treat as empty string
                        collected_items.append('""')
                        i += 1
                else:
                    # Standalone dash at end of file
                    collected_items.append('""')
                    i += 1
        else:
            # Non-dash line - check if it's at parent indent or less
            if line_indent <= parent_indent:
                # Back to parent level - stop collecting
                break
            else:
                # Deeper indented content that's not a dash list - stop collecting
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
        
        # Check if this is start of a multiline inline object {...}
        if stripped == '{' or stripped.startswith('{'):
            # Collect all lines until matching }
            obj_start_line = i
            obj_lines = [stripped]
            obj_line_info = [(i, stripped, False)]  # Track each line for token emission
            
            open_braces = stripped.count('{') - stripped.count('}')
            lines_consumed += 1
            i += 1
            
            # Collect lines until braces are balanced
            while i < len(lines) and open_braces > 0:
                obj_line = lines[i]
                obj_stripped = obj_line.strip()
                
                if not obj_stripped:
                    lines_consumed += 1
                    i += 1
                    continue
                
                obj_lines.append(obj_stripped)
                has_comma = obj_stripped.endswith(',')
                obj_line_info.append((i, obj_stripped.rstrip(',').strip(), has_comma))
                
                open_braces += obj_stripped.count('{') - obj_stripped.count('}')
                lines_consumed += 1
                i += 1
            
            # Reconstruct as single inline object
            reconstructed_obj = '{' + ' '.join(obj_lines[1:]) + '}'
            collected_items.append(reconstructed_obj)
            
            # Add all lines from this object to item_line_info for tokenization
            item_line_info.extend(obj_line_info)
            continue
        
        # Regular array item (single line)
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
