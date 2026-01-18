"""
Value Processors - Value type detection and parsing

Handles Zolo's string-first philosophy with explicit type hints.
"""

from typing import Any

from .type_hints import TYPE_HINT_PATTERN
from ...exceptions import ZoloParseError
from .validators import validate_ascii_only, is_valid_number
from .escape_processors import decode_unicode_escapes, process_escape_sequences


def detect_value_type(value: str) -> Any:
    r"""
    .zolo String-First Type Detection.
    
    Philosophy: Safe by default, explicit when needed.
    
    Auto-Detection (RFC 8259 Primitives):
    1. Array (bracket syntax): '[...]' → list
    2. Number: Valid numeric format → float (RFC 8259 default)
    3. Null: 'null' (standalone) → None (RFC 8259 primitive)
    
    Everything Else → String (including 'true', 'false'):
    - Use type hints for explicit conversion: (bool), (int), (str)
    - Booleans need hints (they're ambiguous words in natural language)
    - This prevents YAML-style surprises (NO → False, yes → True)
    - Values are predictable and safe
    
    Edge Cases:
    - Empty value (no value after colon) → '' (empty string)
    - 'null value' (null with other text) → 'null value' (string)
    
    Multi-line Support:
    - \n escape sequences are converted to actual newlines
    
    Anti-Quirk Rules:
    - '00123' (leading zero) → string (NOT octal)
    - '1.0.0' → string (NOT number)
    - 'NO', 'YES', 'true', 'false' → strings (use type hints!)
    
    Args:
        value: String value to detect and convert
    
    Returns:
        Typed value (list, float, None, or str)
    
    Examples:
        >>> detect_value_type('5000')
        5000.0
        >>> detect_value_type('null')
        None
        >>> detect_value_type('true')
        'true'
        >>> detect_value_type('')
        ''
    """
    # Validate ASCII-only BEFORE any processing (RFC 8259 compliance)
    # This catches emojis/non-ASCII and provides helpful error with \uXXXX suggestion
    validate_ascii_only(value)
    
    # Empty value (key: with nothing after) → empty string
    if not value:
        return ''
    
    # Array (bracket syntax)
    if value.startswith('[') and value.endswith(']'):
        return parse_bracket_array(value)
    
    # Object (brace syntax - flow-style)
    if value.startswith('{') and value.endswith('}'):
        return parse_brace_object(value)
    
    # Number (RFC 8259: all numbers → float)
    if is_valid_number(value):
        return float(value)
    
    # Null (RFC 8259 primitive) - standalone only!
    if value == 'null':
        return None
    
    # String (DEFAULT - everything else!)
    # This includes: 'true', 'false', 'yes', 'no', 'null value', etc.
    
    # Step 1: Decode Unicode escapes (\uXXXX) - RFC 8259 compliance
    if '\\u' in value:
        value = decode_unicode_escapes(value)
    
    # Step 2: Process other escape sequences (\n, \t, etc.)
    value = process_escape_sequences(value)
    
    return value


def parse_brace_object(value: str) -> dict:
    """
    Parse object with brace syntax {key: value, key2: value2}.
    
    Rules:
    - Strip outer braces { and }
    - Split on commas (top-level only)
    - Each item is key: value
    - Apply type detection recursively
    - Handle empty objects {}
    
    Args:
        value: String like '{x: 10, y: 20}' or '{}'
    
    Returns:
        Dictionary with typed values
    
    Examples:
        >>> parse_brace_object('{x: 10, y: 20}')
        {'x': 10.0, 'y': 20.0}
        
        >>> parse_brace_object('{name: Alice, active: true}')
        {'name': 'Alice', 'active': 'true'}
        
        >>> parse_brace_object('{}')
        {}
    """
    # Strip outer braces
    inner = value[1:-1].strip()
    
    # Empty object
    if not inner:
        return {}
    
    # Parse key-value pairs
    result = {}
    seen_keys = {}  # Track duplicates: {clean_key: original_key}
    
    # Split on commas, but respect nested brackets/braces
    pairs = split_on_comma(inner)
    
    for pair in pairs:
        pair = pair.strip()
        if ':' in pair:
            # Split on first colon
            key, _, val = pair.partition(':')
            key = key.strip()
            val = val.strip()
            
            # Strip type hint from key for duplicate checking
            match = TYPE_HINT_PATTERN.match(key)
            clean_key = match.group(1) if match else key
            
            # Check for duplicate keys (STRICT MODE - Phase 4.7)
            if clean_key in seen_keys:
                first_key = seen_keys[clean_key]
                raise ZoloParseError(
                    f"Duplicate key '{clean_key}' in flow-style object: {value}\n"
                    f"First occurrence: '{first_key}', duplicate: '{key}'.\n"
                    f"Keys must be unique within the same object."
                )
            
            seen_keys[clean_key] = key
            
            # Recursively detect type for value
            typed_value = detect_value_type(val)
            result[key] = typed_value
    
    return result


def parse_bracket_array(value: str) -> list:
    """
    Parse array with bracket syntax [item1, item2, item3].
    
    Rules:
    - Strip outer brackets [ and ]
    - Split on top-level commas (respect nested brackets/braces)
    - Trim whitespace from each item
    - Apply type detection to each item recursively
    - Handle empty arrays []
    
    Args:
        value: String like '[1, 2, 3]' or '[[1, 2], [3, 4]]'
    
    Returns:
        List with typed items
    
    Examples:
        >>> parse_bracket_array('[1, 2, 3]')
        [1.0, 2.0, 3.0]
        
        >>> parse_bracket_array('[python, yaml, test]')
        ['python', 'yaml', 'test']
        
        >>> parse_bracket_array('[[1, 2], [3, 4]]')
        [[1.0, 2.0], [3.0, 4.0]]
        
        >>> parse_bracket_array('[]')
        []
    """
    # Strip outer brackets
    inner = value[1:-1].strip()
    
    # Empty array
    if not inner:
        return []
    
    # Split on top-level commas (respect nesting)
    items = []
    for item in split_on_comma(inner):
        item = item.strip()
        # Recursively detect type for each item
        typed_item = detect_value_type(item)
        items.append(typed_item)
    
    return items


def split_on_comma(text: str) -> list[str]:
    """
    Split text on commas, but respect nested brackets/braces.
    
    Args:
        text: Text to split
    
    Returns:
        List of parts split on top-level commas
    
    Examples:
        >>> split_on_comma('a, b, c')
        ['a', 'b', 'c']
        
        >>> split_on_comma('a: [1, 2], b: 3')
        ['a: [1, 2]', 'b: 3']
    """
    parts = []
    current = []
    depth = 0  # Track nesting depth
    
    for char in text:
        if char in '[{':
            depth += 1
            current.append(char)
        elif char in ']}':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            # Top-level comma - split here
            parts.append(''.join(current))
            current = []
        else:
            current.append(char)
    
    # Add final part
    if current:
        parts.append(''.join(current))
    
    return parts
