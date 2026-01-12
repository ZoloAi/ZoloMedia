"""
Unit tests for LSP semantic tokenizer
"""

import pytest
from core.parser import tokenize
from core.server.semantic_tokenizer import encode_semantic_tokens, decode_semantic_tokens
from core.lsp_types import TokenType


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
    # With (bool) hint, true is tokenized as BOOLEAN
    assert TokenType.BOOLEAN in token_types or TokenType.STRING in token_types


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
    content = "users: [alice, bob, charlie]"
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.BRACKET_STRUCTURAL in token_types
    assert TokenType.STRING in token_types


def test_encode_semantic_tokens():
    """Test LSP delta encoding."""
    content = "port: 8080"
    result = tokenize(content)
    encoded = encode_semantic_tokens(result.tokens)
    
    # Should be array of integers
    assert isinstance(encoded, list)
    assert all(isinstance(x, int) for x in encoded)
    
    # Should be multiples of 5 (LSP format)
    assert len(encoded) % 5 == 0


def test_decode_semantic_tokens():
    """Test LSP delta decoding."""
    content = "port: 8080"
    result = tokenize(content)
    encoded = encode_semantic_tokens(result.tokens)
    decoded = decode_semantic_tokens(encoded)
    
    # Should decode to list of token info
    assert isinstance(decoded, list)
    assert len(decoded) > 0
    
    # Each token should have required fields
    for token in decoded:
        assert 'line' in token
        assert 'start' in token
        assert 'length' in token
        assert 'type' in token


def test_empty_content():
    """Test tokenizing empty content."""
    result = tokenize("")
    assert result.tokens == []
    encoded = encode_semantic_tokens(result.tokens)
    assert encoded == []


def test_multiline_content():
    """Test tokenizing multiline content."""
    content = """# Comment
port: 8080
host: localhost"""
    result = tokenize(content)
    
    # Should have tokens from multiple lines
    lines_with_tokens = set(t.line for t in result.tokens)
    assert len(lines_with_tokens) > 1


def test_boolean_values():
    """Test boolean value tokenization."""
    content = "enabled(bool): true\ndisabled(bool): false"
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    assert TokenType.BOOLEAN in token_types or TokenType.STRING in token_types


def test_token_positions():
    """Test that token positions are correct."""
    content = "port: 8080"
    result = tokenize(content)
    
    # First token should be at line 0
    assert result.tokens[0].line == 0
    
    # Tokens should have valid positions
    for token in result.tokens:
        assert token.line >= 0
        assert token.start_char >= 0
        assert token.length > 0


def test_version_string_tokenization():
    """Test that version strings (X.Y.Z) are tokenized as VERSION_STRING, not NUMBER."""
    content = "version: 1.0.0"
    result = tokenize(content)
    
    token_types = [t.token_type for t in result.tokens]
    # Should have VERSION_STRING token
    assert TokenType.VERSION_STRING in token_types
    # Should NOT have NUMBER token (1.0.0 is not a valid number due to multiple dots)
    assert TokenType.NUMBER not in token_types


def test_version_string_vs_number():
    """Test that version strings and actual numbers are distinguished."""
    content = """app: MyApp
version: 1.0.0
port: 8080
price: 19.99"""
    result = tokenize(content)
    
    # Collect tokens by line
    tokens_by_line = {}
    for token in result.tokens:
        if token.line not in tokens_by_line:
            tokens_by_line[token.line] = []
        tokens_by_line[token.line].append(token)
    
    # Line 1: version: 1.0.0 → should have VERSION_STRING
    line1_types = [t.token_type for t in tokens_by_line.get(1, [])]
    assert TokenType.VERSION_STRING in line1_types
    
    # Line 2: port: 8080 → should have NUMBER
    line2_types = [t.token_type for t in tokens_by_line.get(2, [])]
    assert TokenType.NUMBER in line2_types
    
    # Line 3: price: 19.99 → should have NUMBER
    line3_types = [t.token_type for t in tokens_by_line.get(3, [])]
    assert TokenType.NUMBER in line3_types


def test_version_string_patterns():
    """Test various version string formats."""
    test_cases = [
        ("version: 1.0.0", True),        # Standard semver
        ("version: 2.1.5", True),        # Another semver
        ("version: 1.0.0-alpha", False), # With suffix (string, not version token)
        ("port: 8080", False),           # Regular number
        ("price: 19.99", False),         # Float (only one dot)
    ]
    
    for content, should_have_version in test_cases:
        result = tokenize(content)
        token_types = [t.token_type for t in result.tokens]
        
        if should_have_version:
            assert TokenType.VERSION_STRING in token_types, f"Expected VERSION_STRING in: {content}"
        else:
            assert TokenType.VERSION_STRING not in token_types, f"Should NOT have VERSION_STRING in: {content}"


def test_nested_keys_with_and_without_type_hints():
    """Test that nested keys are tokenized consistently with or without type hints."""
    content = """server:
  host: localhost
  port(int): 8080
  ssl(bool): true"""
    result = tokenize(content)
    
    # Find all nested key tokens
    nested_keys = [t for t in result.tokens if t.token_type == TokenType.NESTED_KEY]
    
    # Should have 3 nested keys: host, port, ssl
    assert len(nested_keys) == 3
    
    # All should be NESTED_KEY type (not ROOT_KEY)
    for token in nested_keys:
        assert token.token_type == TokenType.NESTED_KEY


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
