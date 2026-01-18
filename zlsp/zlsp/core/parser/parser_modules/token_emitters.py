"""
Token Emitters - Emit semantic tokens for values

Handles token emission for strings, arrays, objects, and special values.
Validation logic extracted to value_validators module for cleaner separation.
"""

import re
from typing import Optional, TYPE_CHECKING

from .validators import is_zpath_value, is_env_config_value, is_valid_number
from .value_validators import ValueValidator
from .type_hints import TYPE_HINT_PATTERN
from ...lsp_types import TokenType

if TYPE_CHECKING:
    from .token_emitter import TokenEmitter

def emit_value_tokens(value: str, line: int, start_pos: int, emitter: 'TokenEmitter', type_hint: str = None, key: str = None):
    """
    Emit semantic tokens for a value based on its detected type.
    
    Args:
        value: The value string
        line: Line number
        start_pos: Starting character position
        emitter: Token emitter
        type_hint: Optional type hint (int, float, str, bool) for semantic highlighting
        key: Optional key name for context-aware coloring
    """
    if not value:
        return
    
    # zMode value (Terminal/zBifrost) - tomato red in zSpark files
    if emitter.is_zspark_file and key == 'zMode':
        emitter.emit(line, start_pos, len(value), TokenType.ZSPARK_MODE_VALUE)
        ValueValidator.validate_for_key(key, value, line, start_pos, emitter)
        return
    
    # deployment value - only Production or Development allowed in zSpark files
    if emitter.is_zspark_file and key == 'deployment':
        # Check for environment/config value (will be bright yellow)
        if is_env_config_value(value):
            ValueValidator.validate_for_key(key, value, line, start_pos, emitter)
            emitter.emit(line, start_pos, len(value), TokenType.ENV_CONFIG_VALUE)
            return
    
    # logger value - only valid log levels allowed in zSpark files
    if emitter.is_zspark_file and key == 'logger':
        # Check for environment/config value (will be bright yellow)
        if is_env_config_value(value):
            ValueValidator.validate_for_key(key, value, line, start_pos, emitter)
            emitter.emit(line, start_pos, len(value), TokenType.ENV_CONFIG_VALUE)
            return
    
    # zVaFile value (must be zUI.*) - dark green in zSpark files
    if emitter.is_zspark_file and key == 'zVaFile':
        emitter.emit(line, start_pos, len(value), TokenType.ZSPARK_VAFILE_VALUE)
        ValueValidator.validate_for_key(key, value, line, start_pos, emitter)
        # Additional validation for file extension (too many dots)
        if value.count('.') > 1:
            from ..lsp_types import Diagnostic, Range, Position
            emitter.diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=line, character=start_pos),
                    end=Position(line=line, character=start_pos + len(value))
                ),
                message=f"Invalid zVaFile value: '{value}'. Must not have a file extension (e.g., 'zUI.zBreakpoints', not 'zUI.zBreakpoints.json').",
                severity=1,  # Error
                source="zolo-lsp"
            ))
        return
    
    # zBlock value - light purple in zSpark files
    if emitter.is_zspark_file and key == 'zBlock':
        emitter.emit(line, start_pos, len(value), TokenType.ZSPARK_SPECIAL_VALUE)
        ValueValidator.validate_for_key(key, value, line, start_pos, emitter)
        return
    
    # If type hint provided, emit based on semantic type (after hint processing)
    if type_hint:
        hint_lower = type_hint.lower()
        if hint_lower == 'str':
            # Force string token even if value looks like number/bool
            has_valid_escape = any(seq in value for seq in ['\\n', '\\t', '\\r', '\\\\', '\\"', "\\'", '\\u'])
            has_brackets = any(c in value for c in '[]{}')
            if has_valid_escape or has_brackets:
                emit_string_with_escapes(value, line, start_pos, emitter)
            else:
                emitter.emit(line, start_pos, len(value), TokenType.STRING)
            return
        elif hint_lower == 'int' or hint_lower == 'float':
            # Force number token
            emitter.emit(line, start_pos, len(value), TokenType.NUMBER)
            return
        elif hint_lower == 'bool':
            # Force boolean token
            emitter.emit(line, start_pos, len(value), TokenType.BOOLEAN)
        return
    
    # zPath (@ or ~ followed by dot-separated path)
    # ONLY in zKernel files (zUI, zSpark, zEnv, zConfig) - string-first for regular .zolo
    is_zkernel_file = emitter.is_zui_file or emitter.is_zspark_file or emitter.is_zenv_file or emitter.is_zconfig_file
    if is_zkernel_file and is_zpath_value(value):
        emitter.emit_zpath_tokens(value, line, start_pos)
        return
    
    # Array (bracket syntax)
    if value.startswith('[') and value.endswith(']'):
        emit_array_tokens(value, line, start_pos, emitter)
        return
    
    # Object (brace syntax)
    if value.startswith('{') and value.endswith('}'):
        emit_object_tokens(value, line, start_pos, emitter)
        return
    
    # Boolean
    if value.lower() in ('true', 'false'):
        emitter.emit(line, start_pos, len(value), TokenType.BOOLEAN)
        return
    
    # Number
    if is_valid_number(value):
        emitter.emit(line, start_pos, len(value), TokenType.NUMBER)
        return
    
    # Null
    if value == 'null':
        emitter.emit(line, start_pos, len(value), TokenType.NULL)
        return
    
    # Environment/Configuration constants (PROD, DEBUG, INFO, etc.)
    # ONLY in zEnv files - these are actual config values there
    # In other files (zUI, zSpark, etc.), they're just regular strings
    if emitter.is_zenv_file and is_env_config_value(value):
        emitter.emit(line, start_pos, len(value), TokenType.ENV_CONFIG_VALUE)
        return
    
    # Check for specific string types
    # Timestamp
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
        emitter.emit(line, start_pos, len(value), TokenType.TIMESTAMP_STRING)
        return
    
    # Time
    if re.match(r'^\d{2}:\d{2}(?::\d{2})?$', value):
        emitter.emit(line, start_pos, len(value), TokenType.TIME_STRING)
        return
    
    # Version
    if re.match(r'^\d+\.\d+(?:\.\d+|\.\*)+$', value):
        emitter.emit(line, start_pos, len(value), TokenType.VERSION_STRING)
        return
    
    # Ratio
    if re.match(r'^\d{1,3}:\d{1,3}$', value) and value != 'null':
        emitter.emit(line, start_pos, len(value), TokenType.RATIO_STRING)
        return
    
    # String (default)
    # Check for VALID escape sequences or brackets within the string
    # Only enter escape processing for known escapes: \n \t \r \\ \" \' \u
    # This allows Windows paths like C:\Windows to work naturally
    has_valid_escape = any(seq in value for seq in ['\\n', '\\t', '\\r', '\\\\', '\\"', "\\'", '\\u'])
    has_brackets = any(c in value for c in '[]{}')
    
    if has_valid_escape or has_brackets:
        emit_string_with_escapes(value, line, start_pos, emitter)
    else:
        emitter.emit(line, start_pos, len(value), TokenType.STRING)


def emit_string_with_escapes(value: str, line: int, start_pos: int, emitter: 'TokenEmitter'):
    """
    Emit string token with escape sequence tokens.
    String-first philosophy: Only escape sequences get special highlighting.
    Brackets/braces inside strings are just regular string characters.
    """
    pos = 0
    last_emit = 0
    
    while pos < len(value):
        # Handle escape sequences
        if value[pos] == '\\' and pos + 1 < len(value):
            # Check what kind of escape FIRST, before emitting
            next_char = value[pos + 1]
            
            if next_char in 'ntr\\\'"':
                # Known escape - emit string before it, then emit the escape
                if pos > last_emit:
                    emitter.emit(line, start_pos + last_emit, pos - last_emit, TokenType.STRING)
                emitter.emit(line, start_pos + pos, 2, TokenType.ESCAPE_SEQUENCE)
                pos += 2
                last_emit = pos
            elif next_char == 'u' and pos + 5 < len(value):
                # Unicode escape \uXXXX - emit string before it, then emit the escape
                if pos > last_emit:
                    emitter.emit(line, start_pos + last_emit, pos - last_emit, TokenType.STRING)
                emitter.emit(line, start_pos + pos, 6, TokenType.ESCAPE_SEQUENCE)
                pos += 6
                last_emit = pos
            else:
                # Unknown escape (like \W, \S, \d) - treat as literal string
                # DON'T emit anything, just skip the backslash
                # The backslash and next char will be included in the final STRING token
                pos += 1  # Only skip the backslash, next char will be part of string
        else:
            pos += 1
    
    # Emit remaining string
    if last_emit < len(value):
        emitter.emit(line, start_pos + last_emit, len(value) - last_emit, TokenType.STRING)


def emit_array_tokens(value: str, line: int, start_pos: int, emitter: 'TokenEmitter'):
    """Emit tokens for array syntax [...]."""
    # Opening bracket
    emitter.emit(line, start_pos, 1, TokenType.BRACKET_STRUCTURAL)
    
    # Parse inner content
    inner = value[1:-1].strip()
    if inner:
        # Split array items at top-level commas (respecting nesting)
        items = []
        depth = 0
        item_start = 0
        
        for i, char in enumerate(inner):
            if char in '[{':
                depth += 1
            elif char in ']}':
                depth -= 1
            elif char == ',' and depth == 0:
                # Found item boundary
                item = inner[item_start:i].strip()
                if item:
                    items.append((item, start_pos + 1 + item_start + (len(inner[item_start:i]) - len(item))))
                # Emit comma
                emitter.emit(line, start_pos + 1 + i, 1, TokenType.COMMA)
                item_start = i + 1
        
        # Last item
        item = inner[item_start:].strip()
        if item:
            items.append((item, start_pos + 1 + item_start + (len(inner[item_start:]) - len(item))))
        
        # Recursively emit tokens for each item
        for item, item_pos in items:
            emit_value_tokens(item, line, item_pos, emitter)
    
    # Closing bracket
    emitter.emit(line, start_pos + len(value) - 1, 1, TokenType.BRACKET_STRUCTURAL)


def emit_object_tokens(value: str, line: int, start_pos: int, emitter: 'TokenEmitter'):
    """Emit tokens for object syntax {...}."""
    # Opening brace
    emitter.emit(line, start_pos, 1, TokenType.BRACE_STRUCTURAL)
    
    # Parse inner content
    inner = value[1:-1].strip()
    if inner:
        # Split object pairs at top-level commas (respecting nesting)
        pairs = []
        depth = 0
        pair_start = 0
        
        for i, char in enumerate(inner):
            if char in '[{':
                depth += 1
            elif char in ']}':
                depth -= 1
            elif char == ',' and depth == 0:
                # Found pair boundary
                pair = inner[pair_start:i].strip()
                if pair and ':' in pair:
                    pairs.append((pair, start_pos + 1 + pair_start + (len(inner[pair_start:i]) - len(pair))))
                # Emit comma
                emitter.emit(line, start_pos + 1 + i, 1, TokenType.COMMA)
                pair_start = i + 1
        
        # Last pair
        pair = inner[pair_start:].strip()
        if pair and ':' in pair:
            pairs.append((pair, start_pos + 1 + pair_start + (len(inner[pair_start:]) - len(pair))))
        
        # Emit tokens for each key-value pair
        for pair, pair_pos in pairs:
            # Split on first colon (respecting nesting)
            depth = 0
            colon_idx = -1
            for i, char in enumerate(pair):
                if char in '[{':
                    depth += 1
                elif char in ']}':
                    depth -= 1
                elif char == ':' and depth == 0:
                    colon_idx = i
                    break
            
            if colon_idx >= 0:
                key = pair[:colon_idx].strip()
                val = pair[colon_idx + 1:].strip()
                
                # Calculate key position
                key_offset = len(pair[:colon_idx]) - len(key)
                key_pos = pair_pos + key_offset
                
                # Check for type hint in key
                match = TYPE_HINT_PATTERN.match(key)
                type_hint_text = None
                if match:
                    # Key has type hint: keyname(type)
                    clean_key = match.group(1)
                    type_hint_text = match.group(2)
                    
                    # Emit key name
                    emitter.emit(line, key_pos, len(clean_key), TokenType.NESTED_KEY)
                    
                    # Emit opening paren
                    paren_pos = key_pos + len(clean_key)
                    emitter.emit(line, paren_pos, 1, TokenType.TYPE_HINT_PAREN)
                    
                    # Emit type hint text
                    type_pos = paren_pos + 1
                    emitter.emit(line, type_pos, len(type_hint_text), TokenType.TYPE_HINT)
                    
                    # Emit closing paren
                    close_paren_pos = type_pos + len(type_hint_text)
                    emitter.emit(line, close_paren_pos, 1, TokenType.TYPE_HINT_PAREN)
                else:
                    # No type hint - emit key as single token
                    emitter.emit(line, key_pos, len(key), TokenType.NESTED_KEY)
                
                # Emit colon
                emitter.emit(line, pair_pos + colon_idx, 1, TokenType.COLON)
                
                # Emit value token (recursively) with semantic type hint
                if val:
                    val_offset = len(pair[:colon_idx + 1]) + (len(pair[colon_idx + 1:]) - len(val))
                    val_pos = pair_pos + val_offset
                    emit_value_tokens(val, line, val_pos, emitter, type_hint=type_hint_text)
    
    # Closing brace
    emitter.emit(line, start_pos + len(value) - 1, 1, TokenType.BRACE_STRUCTURAL)


