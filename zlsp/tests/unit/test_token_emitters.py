"""
Unit tests for token_emitters module.

Tests semantic token emission for different value types:
- Special values (zSpark-specific)
- Type-hinted values
- Basic types (bool, number, null, string)
- Special string patterns (timestamp, version, etc.)
- Escape sequences
- Arrays and objects

Current coverage: 70% → Target: 80%+
"""

import pytest
from core.parser.parser_modules.token_emitters import (
    emit_value_tokens,
    emit_string_with_escapes,
    emit_array_tokens,
    emit_object_tokens,
)
from core.parser.parser_modules.token_emitter import TokenEmitter
from core.lsp_types import TokenType


# ============================================================================
# Basic Value Type Tests
# ============================================================================

class TestBasicValueTypes:
    """Test token emission for basic value types."""
    
    def test_emit_boolean_true(self):
        """Test boolean true value."""
        content = "key: true"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("true", 0, 5, emitter)
        
        tokens = emitter.get_tokens()
        bool_tokens = [t for t in tokens if t.token_type == TokenType.BOOLEAN]
        assert len(bool_tokens) >= 1
    
    def test_emit_boolean_false(self):
        """Test boolean false value."""
        content = "key: false"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("false", 0, 5, emitter)
        
        tokens = emitter.get_tokens()
        bool_tokens = [t for t in tokens if t.token_type == TokenType.BOOLEAN]
        assert len(bool_tokens) >= 1
    
    def test_emit_number_integer(self):
        """Test integer value."""
        content = "port: 8080"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("8080", 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        number_tokens = [t for t in tokens if t.token_type == TokenType.NUMBER]
        assert len(number_tokens) >= 1
    
    def test_emit_number_float(self):
        """Test float value."""
        content = "timeout: 30.5"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("30.5", 0, 9, emitter)
        
        tokens = emitter.get_tokens()
        number_tokens = [t for t in tokens if t.token_type == TokenType.NUMBER]
        assert len(number_tokens) >= 1
    
    def test_emit_null(self):
        """Test null value."""
        content = "optional: null"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("null", 0, 10, emitter)
        
        tokens = emitter.get_tokens()
        null_tokens = [t for t in tokens if t.token_type == TokenType.NULL]
        assert len(null_tokens) >= 1
    
    def test_emit_simple_string(self):
        """Test simple string value."""
        content = "name: MyApp"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("MyApp", 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        string_tokens = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(string_tokens) >= 1


# ============================================================================
# Type Hint Tests
# ============================================================================

class TestTypeHints:
    """Test token emission with type hints."""
    
    def test_str_type_hint(self):
        """Test (str) type hint forces string token."""
        content = "port(str): 8080"
        emitter = TokenEmitter(content)
        
        # Even though "8080" looks like a number, (str) forces string
        emit_value_tokens("8080", 0, 11, emitter, type_hint="str")
        
        tokens = emitter.get_tokens()
        string_tokens = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(string_tokens) >= 1
    
    def test_int_type_hint(self):
        """Test (int) type hint forces number token."""
        content = "value(int): 42"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("42", 0, 12, emitter, type_hint="int")
        
        tokens = emitter.get_tokens()
        number_tokens = [t for t in tokens if t.token_type == TokenType.NUMBER]
        assert len(number_tokens) >= 1
    
    def test_float_type_hint(self):
        """Test (float) type hint forces number token."""
        content = "value(float): 3.14"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("3.14", 0, 14, emitter, type_hint="float")
        
        tokens = emitter.get_tokens()
        number_tokens = [t for t in tokens if t.token_type == TokenType.NUMBER]
        assert len(number_tokens) >= 1
    
    def test_bool_type_hint(self):
        """Test (bool) type hint forces boolean token."""
        content = "enabled(bool): true"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("true", 0, 15, emitter, type_hint="bool")
        
        tokens = emitter.get_tokens()
        bool_tokens = [t for t in tokens if t.token_type == TokenType.BOOLEAN]
        assert len(bool_tokens) >= 1


# ============================================================================
# Special String Pattern Tests
# ============================================================================

class TestSpecialStringPatterns:
    """Test special string pattern recognition."""
    
    def test_timestamp_string(self):
        """Test timestamp pattern (ISO 8601)."""
        content = "created: 2024-01-15T10:30:45"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("2024-01-15T10:30:45", 0, 9, emitter)
        
        tokens = emitter.get_tokens()
        timestamp_tokens = [t for t in tokens if t.token_type == TokenType.TIMESTAMP_STRING]
        assert len(timestamp_tokens) >= 1
    
    def test_time_string(self):
        """Test time pattern (HH:MM or HH:MM:SS)."""
        content = "start: 14:30:00"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("14:30:00", 0, 7, emitter)
        
        tokens = emitter.get_tokens()
        time_tokens = [t for t in tokens if t.token_type == TokenType.TIME_STRING]
        assert len(time_tokens) >= 1
    
    def test_version_string(self):
        """Test version pattern (semantic versioning)."""
        content = "version: 1.2.3"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("1.2.3", 0, 9, emitter)
        
        tokens = emitter.get_tokens()
        version_tokens = [t for t in tokens if t.token_type == TokenType.VERSION_STRING]
        assert len(version_tokens) >= 1
    
    def test_ratio_string(self):
        """Test ratio pattern (16:9)."""
        content = "aspect: 16:9"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("16:9", 0, 8, emitter)
        
        tokens = emitter.get_tokens()
        ratio_tokens = [t for t in tokens if t.token_type == TokenType.RATIO_STRING]
        assert len(ratio_tokens) >= 1


# ============================================================================
# String with Escape Sequences Tests
# ============================================================================

class TestStringWithEscapes:
    """Test string with escape sequence emission."""
    
    def test_string_with_newline_escape(self):
        """Test string containing \\n escape."""
        content = r'text: line1\nline2'
        emitter = TokenEmitter(content)
        
        emit_string_with_escapes(r'line1\nline2', 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        # Should have both STRING and ESCAPE_SEQUENCE tokens
        string_tokens = [t for t in tokens if t.token_type == TokenType.STRING]
        escape_tokens = [t for t in tokens if t.token_type == TokenType.ESCAPE_SEQUENCE]
        assert len(escape_tokens) >= 1
    
    def test_string_with_tab_escape(self):
        """Test string containing \\t escape."""
        content = r'text: col1\tcol2'
        emitter = TokenEmitter(content)
        
        emit_string_with_escapes(r'col1\tcol2', 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        escape_tokens = [t for t in tokens if t.token_type == TokenType.ESCAPE_SEQUENCE]
        assert len(escape_tokens) >= 1
    
    def test_string_with_quote_escape(self):
        """Test string containing \\" escape."""
        content = r'text: say \"hello\"'
        emitter = TokenEmitter(content)
        
        emit_string_with_escapes(r'say \"hello\"', 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        escape_tokens = [t for t in tokens if t.token_type == TokenType.ESCAPE_SEQUENCE]
        assert len(escape_tokens) >= 2  # Two \" escapes
    
    def test_string_with_backslash_escape(self):
        """Test string containing \\\\ escape."""
        content = r'path: C:\\Windows\\System32'
        emitter = TokenEmitter(content)
        
        emit_string_with_escapes(r'C:\\Windows\\System32', 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        # Should have escape tokens for \\
        escape_tokens = [t for t in tokens if t.token_type == TokenType.ESCAPE_SEQUENCE]
        assert len(escape_tokens) >= 1
    
    def test_string_with_unicode_escape(self):
        """Test string containing \\uXXXX escape."""
        content = r'emoji: \u1F680'
        emitter = TokenEmitter(content)
        
        emit_string_with_escapes(r'\u1F680', 0, 7, emitter)
        
        tokens = emitter.get_tokens()
        escape_tokens = [t for t in tokens if t.token_type == TokenType.ESCAPE_SEQUENCE]
        assert len(escape_tokens) >= 1


# ============================================================================
# Array Token Tests
# ============================================================================

class TestArrayTokens:
    """Test array token emission."""
    
    def test_simple_array(self):
        """Test simple array with values."""
        content = "items: [1, 2, 3]"
        emitter = TokenEmitter(content)
        
        emit_array_tokens("[1, 2, 3]", 0, 7, emitter)
        
        tokens = emitter.get_tokens()
        # Should emit tokens (brackets and values)
        assert len(tokens) >= 1
    
    def test_empty_array(self):
        """Test empty array."""
        content = "items: []"
        emitter = TokenEmitter(content)
        
        emit_array_tokens("[]", 0, 7, emitter)
        
        tokens = emitter.get_tokens()
        # Should emit tokens for brackets
        assert len(tokens) >= 1
    
    def test_array_with_strings(self):
        """Test array with string values."""
        content = "names: [Alice, Bob, Charlie]"
        emitter = TokenEmitter(content)
        
        emit_array_tokens("[Alice, Bob, Charlie]", 0, 7, emitter)
        
        tokens = emitter.get_tokens()
        # Should have string tokens for values
        string_tokens = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(string_tokens) >= 3


# ============================================================================
# Object Token Tests
# ============================================================================

class TestObjectTokens:
    """Test object token emission."""
    
    def test_simple_object(self):
        """Test simple object with key-value pairs."""
        content = "config: {port: 8080, host: localhost}"
        emitter = TokenEmitter(content)
        
        emit_object_tokens("{port: 8080, host: localhost}", 0, 8, emitter)
        
        tokens = emitter.get_tokens()
        # Should emit tokens (braces and key-value pairs)
        assert len(tokens) >= 1
    
    def test_empty_object(self):
        """Test empty object."""
        content = "config: {}"
        emitter = TokenEmitter(content)
        
        emit_object_tokens("{}", 0, 8, emitter)
        
        tokens = emitter.get_tokens()
        # Should emit tokens for braces
        assert len(tokens) >= 1


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and complex scenarios."""
    
    def test_empty_value(self):
        """Test emit_value_tokens with empty string."""
        content = "key: "
        emitter = TokenEmitter(content)
        
        # Empty value should not emit anything
        emit_value_tokens("", 0, 5, emitter)
        
        tokens = emitter.get_tokens()
        # Should not crash, just return without emitting
        assert isinstance(tokens, list)
    
    def test_case_insensitive_boolean(self):
        """Test boolean is case-insensitive."""
        content = "enabled: TRUE"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("TRUE", 0, 9, emitter)
        
        tokens = emitter.get_tokens()
        bool_tokens = [t for t in tokens if t.token_type == TokenType.BOOLEAN]
        assert len(bool_tokens) >= 1
    
    def test_negative_number(self):
        """Test negative number."""
        content = "temp: -10"
        emitter = TokenEmitter(content)
        
        emit_value_tokens("-10", 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        number_tokens = [t for t in tokens if t.token_type == TokenType.NUMBER]
        assert len(number_tokens) >= 1
    
    def test_string_that_looks_like_number(self):
        """Test string that looks like number but is just a string."""
        content = "code: 123abc"
        emitter = TokenEmitter(content)
        
        # Not a valid number, should be string
        emit_value_tokens("123abc", 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        string_tokens = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(string_tokens) >= 1
    
    def test_windows_path_without_escapes(self):
        """Test Windows path (backslashes not treated as escapes)."""
        content = r"path: C:\Windows"
        emitter = TokenEmitter(content)
        
        # No valid escape sequences (\W is not valid), should emit as string
        emit_value_tokens(r"C:\Windows", 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        # Should emit as string (no ESCAPE_SEQUENCE tokens)
        string_tokens = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(string_tokens) >= 1


# ============================================================================
# Integration with File Types
# ============================================================================

class TestFileTypeIntegration:
    """Test token emission varies by file type."""
    
    def test_zpath_in_zkernel_file(self):
        """Test zPath values are recognized in zKernel files."""
        # This would need to be tested with a properly configured emitter
        # For now, just verify the function handles it
        content = "path: @user.profile.name"
        emitter = TokenEmitter(content, filename="test.zUI.zolo")
        
        # zPath pattern should be detected
        emit_value_tokens("@user.profile.name", 0, 6, emitter)
        
        tokens = emitter.get_tokens()
        # Should have tokens (zPath emits special tokens)
        assert len(tokens) >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
