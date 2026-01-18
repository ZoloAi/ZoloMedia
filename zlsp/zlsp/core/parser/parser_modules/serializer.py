"""
Zolo Serializer - Convert Python data to .zolo format

Pure .zolo serialization without YAML dependency.
"""

from typing import Any, List


def serialize_zolo(data: Any, indent: int = 0) -> str:
    """
    Serialize Python data structure to .zolo format.

    Args:
        data: Python object to serialize (dict, list, scalar)
        indent: Current indentation level

    Returns:
        .zolo formatted string

    Examples:
        >>> serialize_zolo({'port': 8080, 'host': 'localhost'})
        'port: 8080\\nhost: localhost'

        >>> serialize_zolo({'server': {'port': 8080}})
        'server:\\n    port: 8080'
    """
    if data is None:
        return 'null'

    if isinstance(data, bool):
        return 'true' if data else 'false'

    if isinstance(data, (int, float)):
        return str(data)

    if isinstance(data, str):
        return _serialize_string(data)

    if isinstance(data, list):
        return _serialize_list(data, indent)

    if isinstance(data, dict):
        return _serialize_dict(data, indent)

    # Fallback for unknown types
    return str(data)


def _serialize_string(value: str) -> str:
    """
    Serialize a string value with proper escaping.

    Args:
        value: String to serialize

    Returns:
        Escaped string (quoted if needed)
    """
    # Check if string needs quoting
    needs_quotes = (
        not value  # Empty string
        or value[0] in ' \t'  # Leading whitespace
        or value[-1] in ' \t'  # Trailing whitespace
        or '\n' in value  # Multiline
        or ':' in value  # Contains colon
        or '#' in value  # Contains comment char
        or value in ('true', 'false', 'null')  # Reserved words
    )

    if needs_quotes:
        # Use double quotes and escape internal quotes
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'"{escaped}"'

    return value


def _serialize_list(items: List[Any], indent: int) -> str:
    """
    Serialize a list to .zolo format.

    Args:
        items: List to serialize
        indent: Current indentation level

    Returns:
        .zolo list format (dash-style)

    Examples:
        >>> _serialize_list([1, 2, 3], 0)
        '- 1\\n- 2\\n- 3'
    """
    if not items:
        return '[]'

    lines = []
    indent_str = '    ' * indent

    for item in items:
        if isinstance(item, (dict, list)):
            # Complex item - serialize on next line
            serialized = serialize_zolo(item, indent + 1)
            lines.append(f'{indent_str}- ')
            # Add indented content
            for line in serialized.split('\n'):
                lines.append(f'{indent_str}    {line}')
        else:
            # Simple item - inline
            serialized = serialize_zolo(item, indent)
            lines.append(f'{indent_str}- {serialized}')

    return '\n'.join(lines)


def _serialize_dict(data: dict, indent: int) -> str:
    """
    Serialize a dictionary to .zolo format.

    Args:
        data: Dictionary to serialize
        indent: Current indentation level

    Returns:
        .zolo key-value format

    Examples:
        >>> _serialize_dict({'port': 8080}, 0)
        'port: 8080'
    """
    if not data:
        return '{}'

    lines = []
    indent_str = '    ' * indent

    for key, value in data.items():
        if isinstance(value, dict):
            # Nested dict - key on its own line
            lines.append(f'{indent_str}{key}:')
            nested = _serialize_dict(value, indent + 1)
            lines.append(nested)
        elif isinstance(value, list):
            # List value
            if not value:
                lines.append(f'{indent_str}{key}: []')
            else:
                lines.append(f'{indent_str}{key}:')
                list_lines = _serialize_list(value, indent + 1)
                lines.append(list_lines)
        else:
            # Scalar value
            serialized = serialize_zolo(value, indent)
            lines.append(f'{indent_str}{key}: {serialized}')

    return '\n'.join(lines)


def dumps(data: Any) -> str:
    """
    Public API: Serialize data to .zolo string.

    Args:
        data: Python object to serialize

    Returns:
        .zolo formatted string

    Examples:
        >>> dumps({'port': 8080, 'host': 'localhost'})
        'port: 8080\\nhost: localhost'
    """
    return serialize_zolo(data, indent=0)
