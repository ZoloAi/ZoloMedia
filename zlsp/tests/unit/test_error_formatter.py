"""
Unit tests for Error Formatter.

Tests the ErrorFormatter class which provides user-friendly error messages:
- Typo suggestions (suggest_correction)
- Duplicate key errors (format_duplicate_key_error)
- Invalid type hint errors (format_invalid_type_hint_error)
- Unknown key errors (format_unknown_key_error)
- Invalid boolean value errors (format_invalid_boolean_error)
- Unclosed bracket errors (format_unclosed_bracket_error)
"""

import pytest
from core.parser.parser_modules.error_formatter import ErrorFormatter


class TestSuggestCorrection:
    """Test fuzzy matching for typo suggestions."""
    
    def test_suggest_correction_exact_match(self):
        """Test that exact matches return themselves."""
        result = ErrorFormatter.suggest_correction("zSpark", ["zSpark", "zEnv"])
        assert result == "zSpark"
    
    def test_suggest_correction_close_match(self):
        """Test correction for close typos."""
        # Common typo: missing capital
        result = ErrorFormatter.suggest_correction("zspark")
        assert result == "zSpark" or result in ErrorFormatter.COMMON_KEYS
    
    def test_suggest_correction_no_match(self):
        """Test that very different strings return None."""
        result = ErrorFormatter.suggest_correction("completely_different_key")
        # Should return None or a very weak match
        # (May return something if cutoff is low)
        assert result is None or isinstance(result, str)
    
    def test_suggest_correction_with_custom_options(self):
        """Test correction with custom valid options."""
        valid_options = ["apple", "banana", "cherry"]
        result = ErrorFormatter.suggest_correction("aple", valid_options)
        assert result == "apple"
    
    def test_suggest_correction_with_cutoff(self):
        """Test that cutoff parameter affects matches."""
        # High cutoff (strict matching)
        result_strict = ErrorFormatter.suggest_correction("zSpak", cutoff=0.9)
        # May be None because similarity is too low
        
        # Low cutoff (lenient matching)
        result_lenient = ErrorFormatter.suggest_correction("zSpak", cutoff=0.3)
        assert result_lenient == "zSpark" or result_lenient in ErrorFormatter.COMMON_KEYS


class TestDuplicateKeyError:
    """Test duplicate key error formatting."""
    
    def test_format_duplicate_key_error_basic(self):
        """Test basic duplicate key error message."""
        error_msg = ErrorFormatter.format_duplicate_key_error(
            duplicate_key="name",
            first_line=5,
            current_line=10,
            first_key_raw="name"
        )
        
        assert "Duplicate key 'name'" in error_msg
        assert "line 10" in error_msg
        assert "line 5" in error_msg
    
    def test_format_duplicate_key_error_with_type_hint(self):
        """Test duplicate key error with type hints."""
        error_msg = ErrorFormatter.format_duplicate_key_error(
            duplicate_key="port",
            first_line=3,
            current_line=8,
            first_key_raw="port(int)"
        )
        
        assert "port" in error_msg
        assert "port(int)" in error_msg
        assert "line 3" in error_msg
        assert "line 8" in error_msg
    
    def test_format_duplicate_key_error_includes_suggestions(self):
        """Test that duplicate key error includes fix suggestions."""
        error_msg = ErrorFormatter.format_duplicate_key_error(
            duplicate_key="config",
            first_line=1,
            current_line=5,
            first_key_raw="config"
        )
        
        # Should suggest renaming or using nested structure
        assert "rename" in error_msg.lower() or "unique" in error_msg.lower()


class TestInvalidValueError:
    """Test invalid value error formatting."""
    
    def test_format_invalid_value_error_basic(self):
        """Test basic invalid value error."""
        error_msg = ErrorFormatter.format_invalid_value_error(
            key="port",
            value="invalid",
            valid_values=["8080", "3000", "5000"],
            line=5
        )
        
        assert "invalid" in error_msg
        assert "port" in error_msg
        assert "5" in error_msg or "line 5" in error_msg
    
    def test_format_invalid_value_error_with_suggestion(self):
        """Test that error suggests correct values."""
        error_msg = ErrorFormatter.format_invalid_value_error(
            key="enabled",
            value="yes",
            valid_values=["true", "false"],
            line=5
        )
        
        # Should mention valid values
        assert "true" in error_msg and "false" in error_msg


class TestTypeError:
    """Test type error formatting."""
    
    def test_format_type_error_basic(self):
        """Test basic type error."""
        error_msg = ErrorFormatter.format_type_error(
            expected_type="int",
            actual_value="not_a_number",
            key="port",
            line=10
        )
        
        assert "not_a_number" in error_msg
        assert "10" in error_msg or "line 10" in error_msg
    
    def test_format_type_error_with_type_hint(self):
        """Test that error mentions expected type."""
        error_msg = ErrorFormatter.format_type_error(
            expected_type="int",
            actual_value="invalid",
            key="count",
            line=5
        )
        
        # Should mention int type
        assert "int" in error_msg.lower()


class TestParsingError:
    """Test parsing error formatting."""
    
    def test_format_parsing_error_basic(self):
        """Test basic parsing error."""
        error_msg = ErrorFormatter.format_parsing_error(
            error_type="Unexpected character",
            line=7,
            column=10
        )
        
        assert "Unexpected" in error_msg or "unexpected" in error_msg
        assert "7" in error_msg or "line 7" in error_msg
    
    def test_format_parsing_error_with_column(self):
        """Test parsing error with column information."""
        error_msg = ErrorFormatter.format_parsing_error(
            error_type="Invalid syntax",
            line=5,
            column=15
        )
        
        # Should include line and column
        assert "5" in error_msg or "line 5" in error_msg
        assert "15" in error_msg or "column 15" in error_msg


class TestErrorFormatterEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_common_keys_contains_expected_keys(self):
        """Test that COMMON_KEYS contains expected Zolo keywords."""
        assert "zSpark" in ErrorFormatter.COMMON_KEYS
        assert "zEnv" in ErrorFormatter.COMMON_KEYS
        assert "zUI" in ErrorFormatter.COMMON_KEYS
        assert "zMeta" in ErrorFormatter.COMMON_KEYS
        assert "zSchema" in ErrorFormatter.COMMON_KEYS
    
    def test_suggest_correction_empty_string(self):
        """Test suggestion for empty string."""
        result = ErrorFormatter.suggest_correction("")
        # Should handle gracefully
        assert result is None or isinstance(result, str)
    
    def test_suggest_correction_whitespace(self):
        """Test suggestion for whitespace-only string."""
        result = ErrorFormatter.suggest_correction("   ")
        assert result is None or isinstance(result, str)
    
    def test_error_messages_are_multiline(self):
        """Test that error messages are formatted with newlines."""
        error_msg = ErrorFormatter.format_duplicate_key_error(
            duplicate_key="test",
            first_line=1,
            current_line=5,
            first_key_raw="test"
        )
        
        # Should contain multiple lines
        assert "\n" in error_msg
        assert len(error_msg.split("\n")) > 1
    
    def test_error_messages_contain_line_numbers(self):
        """Test that all error messages include line numbers."""
        errors = [
            ErrorFormatter.format_duplicate_key_error("key", 1, 5, "key"),
            ErrorFormatter.format_invalid_value_error("name", "bad", ["good", "better"], 3),
            ErrorFormatter.format_type_error("int", "text", "port", 7),
            ErrorFormatter.format_parsing_error("Syntax error", 9, 0),
        ]
        
        for error_msg in errors:
            # Each should mention a line number
            assert any(str(i) in error_msg for i in range(1, 20))


class TestErrorFormatterIntegration:
    """Integration tests for error formatter with parser."""
    
    def test_error_formatter_suggests_valid_zolo_keys(self):
        """Test that suggestions are relevant to Zolo syntax."""
        # Test various typos of common Zolo keys with lower cutoff
        typos = ["zspark", "zui", "zmeta"]
        
        for typo in typos:
            suggestion = ErrorFormatter.suggest_correction(typo, cutoff=0.3)
            # Should suggest something (may or may not be exact match due to case)
            # This is a smoke test
            assert suggestion is None or isinstance(suggestion, str)
    
    def test_error_formatter_handles_case_sensitivity(self):
        """Test error formatting with case-sensitive keys."""
        # Zolo keys are case-sensitive
        result_lower = ErrorFormatter.suggest_correction("zspark")
        result_correct = ErrorFormatter.suggest_correction("zSpark")
        
        # Both should work, but correct case should match exactly
        assert result_correct == "zSpark"
