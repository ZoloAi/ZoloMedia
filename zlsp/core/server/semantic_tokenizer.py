"""
Semantic Tokenizer for LSP

Converts semantic tokens to LSP delta-encoded format for efficient transmission.
"""

from typing import List
from ..lsp_types import SemanticToken, TokenType


# LSP token type indices (must match legend in LSP server)
TOKEN_TYPE_MAP = {
    TokenType.COMMENT: 0,
    TokenType.ROOT_KEY: 1,
    TokenType.NESTED_KEY: 2,
    TokenType.ZMETA_KEY: 3,
    TokenType.BIFROST_KEY: 4,
    TokenType.UI_ELEMENT_KEY: 5,
    TokenType.ZCONFIG_KEY: 6,
    TokenType.ZSPARK_KEY: 7,
    TokenType.ZENV_CONFIG_KEY: 8,
    TokenType.ZNAVBAR_NESTED_KEY: 9,
    TokenType.ZSUB_KEY: 10,
    TokenType.ZSPARK_NESTED_KEY: 11,
    TokenType.ZSPARK_MODE_VALUE: 12,
    TokenType.ZSPARK_VAFILE_VALUE: 13,
    TokenType.ZSPARK_SPECIAL_VALUE: 14,
    TokenType.ENV_CONFIG_VALUE: 15,
    TokenType.ZRBAC_KEY: 16,
    TokenType.ZRBAC_OPTION_KEY: 17,
    TokenType.TYPE_HINT: 18,
    TokenType.NUMBER: 19,
    TokenType.STRING: 20,
    TokenType.BOOLEAN: 21,
    TokenType.NULL: 22,
    TokenType.BRACKET_STRUCTURAL: 23,
    TokenType.BRACE_STRUCTURAL: 24,
    TokenType.STRING_BRACKET: 25,
    TokenType.STRING_BRACE: 26,
    TokenType.COLON: 27,
    TokenType.COMMA: 28,
    TokenType.ESCAPE_SEQUENCE: 29,
    TokenType.VERSION_STRING: 30,
    TokenType.TIMESTAMP_STRING: 31,
    TokenType.TIME_STRING: 32,
    TokenType.RATIO_STRING: 33,
    TokenType.ZPATH_VALUE: 34,
    TokenType.ZMACHINE_EDITABLE_KEY: 35,
    TokenType.ZMACHINE_LOCKED_KEY: 36,
    TokenType.TYPE_HINT_PAREN: 37,
}

# Token type legend for LSP (must be registered with client)
TOKEN_TYPES_LEGEND = [
    "comment",
    "rootKey",
    "nestedKey",
    "zmetaKey",
    "bifrostKey",
    "uiElementKey",
    "zconfigKey",
    "zsparkKey",
    "zenvConfigKey",
    "znavbarNestedKey",
    "zsubKey",
    "zsparkNestedKey",
    "zsparkModeValue",
    "zsparkVaFileValue",
    "zsparkSpecialValue",
    "envConfigValue",
    "zrbacKey",
    "zrbacOptionKey",
    "typeHint",
    "number",
    "string",
    "boolean",
    "null",
    "bracketStructural",
    "braceStructural",
    "stringBracket",
    "stringBrace",
    "colon",
    "comma",
    "escapeSequence",
    "versionString",
    "timestampString",
    "timeString",
    "ratioString",
    "zpathValue",
    "zmachineEditableKey",
    "zmachineLockedKey",
    "typeHintParen",
]

TOKEN_MODIFIERS_LEGEND = []  # No modifiers yet


def encode_semantic_tokens(tokens: List[SemanticToken]) -> List[int]:
    """
    Encode semantic tokens in LSP delta format.
    
    LSP uses a delta-encoded array format:
    [deltaLine, deltaStart, length, tokenType, tokenModifiers, ...]
    
    Each token is represented by 5 integers:
    - deltaLine: Line delta from previous token (or absolute for first)
    - deltaStart: Character delta from previous token (or absolute if line changed)
    - length: Token length in characters
    - tokenType: Index into token types legend
    - tokenModifiers: Bitfield of token modifiers (0 if none)
    
    Args:
        tokens: List of semantic tokens (must be sorted by position)
    
    Returns:
        Delta-encoded array of integers for LSP
    
    Example:
        >>> tokens = [
        ...     SemanticToken(Range(Position(0, 0), Position(0, 4)), TokenType.ROOT_KEY),
        ...     SemanticToken(Range(Position(0, 4), Position(0, 5)), TokenType.COLON),
        ...     SemanticToken(Range(Position(0, 6), Position(0, 10)), TokenType.STRING),
        ... ]
        >>> encode_semantic_tokens(tokens)
        [0, 0, 4, 1, 0,  # "port" at line 0, col 0, length 4, type ROOT_KEY
         0, 4, 1, 10, 0,  # ":" at line 0, col 4, length 1, type COLON
         0, 2, 4, 5, 0]   # "8080" at line 0, col 6, length 4, type STRING
    """
    if not tokens:
        return []
    
    # Sort tokens by position (should already be sorted, but ensure it)
    sorted_tokens = sorted(tokens, key=lambda t: (t.line, t.start_char))
    
    encoded = []
    prev_line = 0
    prev_start = 0
    
    for token in sorted_tokens:
        line = token.line
        start = token.start_char
        length = token.length
        token_type_idx = TOKEN_TYPE_MAP.get(token.token_type, 0)
        modifiers = 0  # No modifiers yet
        
        # Calculate deltas
        delta_line = line - prev_line
        if delta_line == 0:
            # Same line, delta from previous token
            delta_start = start - prev_start
        else:
            # New line, absolute position
            delta_start = start
        
        # Append encoded token (5 integers)
        encoded.extend([delta_line, delta_start, length, token_type_idx, modifiers])
        
        # Update previous position
        prev_line = line
        prev_start = start
    
    return encoded


def decode_semantic_tokens(encoded: List[int]) -> List[dict]:
    """
    Decode LSP delta-encoded tokens back to absolute positions.
    
    Useful for debugging and testing.
    
    Args:
        encoded: Delta-encoded token array from LSP
    
    Returns:
        List of dictionaries with token information
    """
    if not encoded or len(encoded) % 5 != 0:
        return []
    
    tokens = []
    current_line = 0
    current_start = 0
    
    for i in range(0, len(encoded), 5):
        delta_line = encoded[i]
        delta_start = encoded[i + 1]
        length = encoded[i + 2]
        token_type_idx = encoded[i + 3]
        modifiers = encoded[i + 4]
        
        # Calculate absolute position
        current_line += delta_line
        if delta_line == 0:
            current_start += delta_start
        else:
            current_start = delta_start
        
        # Get token type name
        token_type = TOKEN_TYPES_LEGEND[token_type_idx] if token_type_idx < len(TOKEN_TYPES_LEGEND) else "unknown"
        
        tokens.append({
            "line": current_line,
            "start": current_start,
            "length": length,
            "type": token_type,
            "modifiers": modifiers
        })
    
    return tokens


def get_token_types_legend() -> List[str]:
    """Get the token types legend for LSP initialization."""
    return TOKEN_TYPES_LEGEND.copy()


def get_token_modifiers_legend() -> List[str]:
    """Get the token modifiers legend for LSP initialization."""
    return TOKEN_MODIFIERS_LEGEND.copy()
