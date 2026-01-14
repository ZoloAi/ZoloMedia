"""
Hover Provider for .zolo Language Server

Provides hover information showing:
- Type hints and their meanings
- Detected value types
- Key documentation
- Valid values
"""

from typing import Optional
from ..parser.parser import tokenize
from ..lsp_types import Position, SemanticToken, TokenType
from ..parser.parser_modules.type_hints import TYPE_HINT_PATTERN


# Type hint documentation
TYPE_HINT_DOCS = {
    "int": "**Integer Number**\n\nConvert value to integer.\n\nExample: `port(int): 8080`",
    "float": "**Floating Point Number**\n\nConvert value to float.\n\nExample: `pi(float): 3.14159`",
    "bool": "**Boolean**\n\nConvert value to boolean (true/false).\n\nExample: `enabled(bool): true`",
    "str": "**String**\n\nExplicitly mark value as string. Also enables multi-line YAML-style content collection.\n\nExample: `name(str): My App`",
    "list": "**List/Array**\n\nEnsure value is a list.\n\nExample: `items(list): [1, 2, 3]`",
    "dict": "**Dictionary/Object**\n\nEnsure value is a dictionary.\n\nExample: `config(dict): {key: value}`",
    "null": "**Null Value**\n\nSet value to null/None.\n\nExample: `optional(null):`",
    "raw": "**Raw String**\n\nString without escape sequence processing.\n\nExample: `regex(raw): \\d+`",
    "date": "**Date String**\n\nDate value (semantic hint).\n\nExample: `created(date): 2024-01-06`",
    "time": "**Time String**\n\nTime value (semantic hint).\n\nExample: `starts(time): 14:30:00`",
    "url": "**URL String**\n\nURL value (semantic hint).\n\nExample: `homepage(url): https://example.com`",
    "path": "**Path String**\n\nFile path (semantic hint).\n\nExample: `config(path): /etc/app/config.zolo`",
}


def get_hover_info(content: str, line: int, character: int) -> Optional[str]:
    """
    Get hover information at a specific position.
    
    Args:
        content: Full .zolo file content
        line: Line number (0-based)
        character: Character position (0-based)
    
    Returns:
        Markdown string with hover information, or None
    
    Examples:
        >>> content = "port(int): 8080"
        >>> info = get_hover_info(content, 0, 5)  # Hovering over "int"
        >>> "Integer" in info
        True
    """
    # Parse content and get tokens
    try:
        result = tokenize(content)
        tokens = result.tokens
    except Exception:
        return None
    
    # Find token at position
    target_pos = Position(line=line, character=character)
    token = _find_token_at_position(tokens, target_pos)
    
    if not token:
        return None
    
    # Get hover info based on token type
    if token.token_type in (TokenType.TYPE_HINT, TokenType.TYPE_HINT_PAREN):
        return _get_type_hint_hover(token, content)
    
    elif token.token_type in (TokenType.ROOT_KEY, TokenType.NESTED_KEY):
        return _get_key_hover(token, content, line)
    
    elif token.token_type == TokenType.NUMBER:
        return _get_number_hover(token, content)
    
    elif token.token_type == TokenType.STRING:
        return _get_string_hover(token, content)
    
    elif token.token_type == TokenType.NULL:
        return _get_null_hover()
    
    elif token.token_type == TokenType.ESCAPE_SEQUENCE:
        return _get_escape_hover(token, content)
    
    return None


def _find_token_at_position(tokens: list[SemanticToken], pos: Position) -> Optional[SemanticToken]:
    """Find the token containing the given position."""
    for token in tokens:
        if token.range.contains(pos):
            return token
    return None


def _get_type_hint_hover(token: SemanticToken, content: str) -> str:
    """Get hover info for a type hint."""
    lines = content.splitlines()
    if token.line >= len(lines):
        return None
    
    line_content = lines[token.line]
    
    # Extract type hint text
    match = TYPE_HINT_PATTERN.search(line_content)
    if match:
        type_hint = match.group(2)
        
        # Look up documentation
        doc = TYPE_HINT_DOCS.get(type_hint.lower())
        if doc:
            return f"## Type Hint: `{type_hint}`\n\n{doc}"
        else:
            return f"## Type Hint: `{type_hint}`\n\n*Unknown type hint*"
    
    return None


def _get_key_hover(token: SemanticToken, content: str, line: int) -> str:
    """Get hover info for a key."""
    lines = content.splitlines()
    if line >= len(lines):
        return None
    
    line_content = lines[line]
    
    # Extract key and value
    if ':' in line_content:
        key_part, _, value_part = line_content.partition(':')
        key_part = key_part.strip()
        value_part = value_part.strip()
        
        # Check for type hint
        match = TYPE_HINT_PATTERN.match(key_part)
        if match:
            clean_key = match.group(1)
            type_hint = match.group(2)
            
            return (
                f"## Key: `{clean_key}`\n\n"
                f"**Type:** `{type_hint}`\n\n"
                f"**Value:** `{value_part if value_part else '(nested object)'}`"
            )
        else:
            # No type hint - show detected type
            if value_part:
                detected_type = _detect_value_type_name(value_part)
                return (
                    f"## Key: `{key_part}`\n\n"
                    f"**Detected Type:** {detected_type}\n\n"
                    f"**Value:** `{value_part}`"
                )
            else:
                return f"## Key: `{key_part}`\n\n*Nested object*"
    
    return None


def _get_number_hover(token: SemanticToken, content: str) -> str:
    """Get hover info for a number."""
    lines = content.splitlines()
    if token.line >= len(lines):
        return None
    
    line_content = lines[token.line]
    number_text = line_content[token.start_char:token.start_char + token.length]
    
    try:
        value = float(number_text)
        return (
            f"## Number Value\n\n"
            f"**Value:** `{number_text}`\n\n"
            f"**Type:** RFC 8259 number (stored as float)\n\n"
            f"**Parsed:** `{value}`"
        )
    except ValueError:
        return None


def _get_string_hover(token: SemanticToken, content: str) -> str:
    """Get hover info for a string."""
    lines = content.splitlines()
    if token.line >= len(lines):
        return None
    
    line_content = lines[token.line]
    string_text = line_content[token.start_char:token.start_char + token.length]
    
    # Check if it's a special string type
    if '\\' in string_text:
        return (
            f"## String Value\n\n"
            f"**Value:** `{string_text}`\n\n"
            f"**Type:** String with escape sequences\n\n"
            f"*Contains escape sequences that will be processed*"
        )
    else:
        return (
            f"## String Value\n\n"
            f"**Value:** `{string_text}`\n\n"
            f"**Type:** String (default in .zolo)"
        )


def _get_null_hover() -> str:
    """Get hover info for null."""
    return (
        "## Null Value\n\n"
        "**Type:** RFC 8259 null primitive\n\n"
        "Represents absence of value (Python: `None`, JSON: `null`)"
    )


def _get_escape_hover(token: SemanticToken, content: str) -> str:
    """Get hover info for an escape sequence."""
    lines = content.splitlines()
    if token.line >= len(lines):
        return None
    
    line_content = lines[token.line]
    escape_text = line_content[token.start_char:token.start_char + token.length]
    
    escape_map = {
        '\\n': 'Newline character',
        '\\t': 'Tab character',
        '\\r': 'Carriage return (terminal control)',
        '\\\\': 'Backslash character',
        '\\"': 'Double quote character',
        "\\'": 'Single quote character',
    }
    
    # Check if it's a Unicode escape
    if escape_text.startswith('\\u'):
        return (
            f"## Unicode Escape Sequence\n\n"
            f"**Sequence:** `{escape_text}`\n\n"
            f"**Type:** RFC 8259 Unicode escape\n\n"
            f"Will be decoded to the corresponding Unicode character"
        )
    elif escape_text in escape_map:
        description = escape_map[escape_text]
        return (
            f"## Escape Sequence\n\n"
            f"**Sequence:** `{escape_text}`\n\n"
            f"**Meaning:** {description}"
        )
    else:
        return (
            f"## Escape Sequence\n\n"
            f"**Sequence:** `{escape_text}`\n\n"
            f"*Unknown escape sequence*"
        )


def _detect_value_type_name(value: str) -> str:
    """Detect and return a human-readable type name for a value."""
    if not value:
        return "empty string"
    
    # Array
    if value.startswith('[') and value.endswith(']'):
        return "array (list)"
    
    # Object
    if value.startswith('{') and value.endswith('}'):
        return "object (dict)"
    
    # Number
    try:
        float(value)
        return "number (auto-detected)"
    except ValueError:
        pass
    
    # Null
    if value == 'null':
        return "null (RFC 8259 primitive)"
    
    # Boolean (but treated as string without type hint!)
    if value in ('true', 'false'):
        return "string (use `(bool)` hint for boolean)"
    
    # String (default)
    return "string (default)"
