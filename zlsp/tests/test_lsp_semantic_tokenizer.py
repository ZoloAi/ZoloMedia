"""
Unit tests for LSP semantic tokenizer

Tests the tokenization and encoding of .zolo files for LSP.
"""

import pytest
from ..parser import tokenize
from ..semantic_tokenizer import encode_semantic_tokens, decode_semantic_tokens
from ..lsp_types import TokenType


def test_basic_tokenization():
    """Test basic key-value tokenization."""
    content = "port: 8080"
    result = tokenize(content)
    
    assert result.data is not None
    assert len(result.tokens) > 0
    
    # Should have tokens for key, colon, and value
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.ROOT_KEY in token_types
    assert TokenType.COLON in token_types
    assert TokenType.NUMBER in token_types


def test_type_hint_tokenization():
    """Test type hint tokenization."""
    content = "enabled(bool): true"
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.ROOT_KEY in token_types
    assert TokenType.TYPE_HINT in token_types
    assert TokenType.STRING in token_types  # true without (bool) is string


def test_comment_tokenization():
    """Test comment tokenization."""
    content = "# This is a comment\nport: 8080"
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.COMMENT in token_types


def test_nested_keys():
    """Test nested key tokenization."""
    content = """server:
    host: localhost
    port: 8080"""
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.ROOT_KEY in token_types
    assert TokenType.NESTED_KEY in token_types


def test_array_tokenization():
    """Test array tokenization."""
    content = "coords: [1, 2, 3]"
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.BRACKET_STRUCTURAL in token_types
    assert TokenType.COMMA in token_types


def test_object_tokenization():
    """Test object tokenization."""
    content = "point: {x: 10, y: 20}"
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.BRACE_STRUCTURAL in token_types
    assert TokenType.COMMA in token_types


def test_escape_sequence_tokenization():
    """Test escape sequence tokenization."""
    content = r"message: Hello\nWorld"
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.ESCAPE_SEQUENCE in token_types


def test_semantic_token_encoding():
    """Test LSP delta encoding of semantic tokens."""
    content = """port: 8080
host: localhost
enabled: true"""
    result = tokenize(content)
    
    # Encode tokens
    encoded = encode_semantic_tokens(result.tokens)
    
    # Should be array of integers
    assert isinstance(encoded, list)
    assert all(isinstance(x, int) for x in encoded)
    
    # Should be multiples of 5 (LSP format)
    assert len(encoded) % 5 == 0


def test_semantic_token_decoding():
    """Test decoding of LSP semantic tokens."""
    content = "port: 8080"
    result = tokenize(content)
    
    # Encode then decode
    encoded = encode_semantic_tokens(result.tokens)
    decoded = decode_semantic_tokens(encoded)
    
    # Should have same number of tokens
    assert len(decoded) == len(result.tokens)
    
    # Check first token (port key)
    assert decoded[0]['line'] == 0
    assert decoded[0]['start'] == 0


def test_token_positions():
    """Test that token positions are accurate."""
    content = "port: 8080"
    result = tokenize(content)
    
    # Find the 'port' key token
    key_token = next(t for t in result.tokens if t.token_type == TokenType.ROOT_KEY)
    
    # Should be at line 0, column 0
    assert key_token.line == 0
    assert key_token.start_char == 0
    assert key_token.length == 4  # 'port' is 4 characters


def test_multiline_tokens():
    """Test tokens across multiple lines."""
    content = """# Comment line 1
# Comment line 2
port: 8080"""
    result = tokenize(content)
    
    # Find comment tokens
    comment_tokens = [t for t in result.tokens if t.token_type == TokenType.COMMENT]
    
    # Should have 2 comment tokens
    assert len(comment_tokens) == 2
    
    # Should be on different lines
    assert comment_tokens[0].line == 0
    assert comment_tokens[1].line == 1


def test_special_string_types():
    """Test special string type detection."""
    content = """version: 1.0.0
timestamp: 2024-01-06T14:30:00
time: 14:30:00
ratio: 16:9"""
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    
    assert TokenType.VERSION_STRING in token_types
    assert TokenType.TIMESTAMP_STRING in token_types
    assert TokenType.TIME_STRING in token_types
    assert TokenType.RATIO_STRING in token_types


def test_null_value():
    """Test null value tokenization."""
    content = "optional: null"
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.NULL in token_types


def test_error_resilience():
    """Test that tokenizer handles errors gracefully."""
    # Invalid content (duplicate key)
    content = """name: first
name: second"""
    
    # Should still tokenize what it can
    result = tokenize(content)
    
    # Should have error
    assert len(result.errors) > 0
    
    # Should still have tokens
    assert len(result.tokens) > 0


def test_empty_content():
    """Test tokenization of empty content."""
    content = ""
    result = tokenize(content)
    
    assert result.data is None
    assert len(result.tokens) == 0


def test_whitespace_handling():
    """Test that whitespace doesn't create spurious tokens."""
    content = "port:    8080"  # Extra spaces after colon
    result = tokenize(content)
    
    # Should have same tokens as "port: 8080"
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.ROOT_KEY in token_types
    assert TokenType.COLON in token_types
    assert TokenType.NUMBER in token_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
