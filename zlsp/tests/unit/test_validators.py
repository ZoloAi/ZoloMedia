"""
Unit tests for validators module.

Tests pure validation functions:
- ASCII-only validation (RFC 8259 compliance)
- zPath detection (@.path, ~.path)
- Environment/config value detection (PROD, DEBUG, etc.)
- Number validation (RFC 8259 compliance)

Current coverage: 62% → Target: 75%+
"""

import pytest
from core.parser.parser_modules.validators import (
    validate_ascii_only,
    is_zpath_value,
    is_env_config_value,
    is_valid_number,
)
from core.exceptions import ZoloParseError


# ============================================================================
# ASCII Validation Tests
# ============================================================================

class TestValidateAsciiOnly:
    """Test ASCII-only validation (RFC 8259 compliance)."""
    
    def test_valid_ascii_string(self):
        """Test valid ASCII string passes."""
        # Should not raise
        validate_ascii_only("hello world")
        validate_ascii_only("Test123!@#")
        validate_ascii_only("simple-string_with.punctuation")
    
    def test_empty_string(self):
        """Test empty string is valid."""
        validate_ascii_only("")
    
    def test_numbers_and_symbols(self):
        """Test numbers and symbols are valid ASCII."""
        validate_ascii_only("12345")
        validate_ascii_only("!@#$%^&*()")
        validate_ascii_only("path/to/file.txt")
    
    def test_emoji_detected(self):
        """Test emoji detection raises error."""
        with pytest.raises(ZoloParseError) as exc_info:
            validate_ascii_only("Hello ♥️")
        
        error_msg = str(exc_info.value)
        assert "Non-ASCII character" in error_msg
        assert "Unicode escape" in error_msg
        assert "\\u" in error_msg
    
    def test_accented_character_detected(self):
        """Test accented character detection."""
        with pytest.raises(ZoloParseError) as exc_info:
            validate_ascii_only("café")
        
        error_msg = str(exc_info.value)
        assert "Non-ASCII character" in error_msg
        assert "é" in error_msg
    
    def test_chinese_character_detected(self):
        """Test non-Latin script detection."""
        with pytest.raises(ZoloParseError) as exc_info:
            validate_ascii_only("你好")
        
        error_msg = str(exc_info.value)
        assert "Non-ASCII character" in error_msg
    
    def test_error_message_includes_line_number(self):
        """Test error message includes line number when provided."""
        with pytest.raises(ZoloParseError) as exc_info:
            validate_ascii_only("test♥", line_num=42)
        
        error_msg = str(exc_info.value)
        assert "line 42" in error_msg
    
    def test_error_message_suggests_escape_sequence(self):
        """Test error message suggests proper Unicode escape."""
        with pytest.raises(ZoloParseError) as exc_info:
            validate_ascii_only("♥")
        
        error_msg = str(exc_info.value)
        # Should suggest escape format
        assert "\\u" in error_msg
        assert "RFC 8259" in error_msg
    
    def test_high_codepoint_surrogate_pair(self):
        """Test high codepoint (emoji) uses surrogate pair."""
        with pytest.raises(ZoloParseError) as exc_info:
            validate_ascii_only("🚀")  # U+1F680, needs surrogate pair
        
        error_msg = str(exc_info.value)
        # Should have two \u sequences for surrogate pair
        assert error_msg.count("\\u") >= 2


# ============================================================================
# zPath Detection Tests
# ============================================================================

class TestIsZpathValue:
    """Test zPath detection (@.path, ~.path)."""
    
    def test_valid_at_zpath(self):
        """Test valid @.path format."""
        assert is_zpath_value("@.user.profile.name") == True
        assert is_zpath_value("@.static.brand.logo") == True
        assert is_zpath_value("@.config.theme") == True
    
    def test_valid_tilde_zpath(self):
        """Test valid ~.path format."""
        assert is_zpath_value("~.user.settings") == True
        assert is_zpath_value("~.app.version") == True
    
    def test_single_component_zpath(self):
        """Test zPath with single component."""
        assert is_zpath_value("@.name") == True
        assert is_zpath_value("~.id") == True
    
    def test_deeply_nested_zpath(self):
        """Test zPath with many components."""
        assert is_zpath_value("@.a.b.c.d.e.f.g") == True
    
    def test_invalid_no_dot(self):
        """Test @ or ~ without dot is invalid."""
        assert is_zpath_value("@name") == False
        assert is_zpath_value("~value") == False
    
    def test_invalid_only_modifier(self):
        """Test only @ or ~ is invalid."""
        assert is_zpath_value("@") == False
        assert is_zpath_value("~") == False
    
    def test_invalid_modifier_dot_only(self):
        """Test @. or ~. without component is invalid."""
        assert is_zpath_value("@.") == False
        assert is_zpath_value("~.") == False
    
    def test_invalid_no_modifier(self):
        """Test path without @ or ~ is invalid."""
        assert is_zpath_value(".user.name") == False
        assert is_zpath_value("user.name") == False
    
    def test_invalid_wrong_modifier(self):
        """Test other symbols are not zPath."""
        assert is_zpath_value("$.path") == False
        assert is_zpath_value("#.path") == False
    
    def test_empty_string(self):
        """Test empty string is not zPath."""
        assert is_zpath_value("") == False


# ============================================================================
# Environment/Config Value Detection Tests
# ============================================================================

class TestIsEnvConfigValue:
    """Test environment/config constant detection."""
    
    def test_log_levels(self):
        """Test log level constants."""
        assert is_env_config_value("DEBUG") == True
        assert is_env_config_value("INFO") == True
        assert is_env_config_value("WARNING") == True
        assert is_env_config_value("ERROR") == True
        assert is_env_config_value("CRITICAL") == True
        assert is_env_config_value("PROD") == True
        assert is_env_config_value("SESSION") == True
    
    def test_environment_constants(self):
        """Test environment name constants."""
        assert is_env_config_value("DEVELOPMENT") == True
        assert is_env_config_value("PRODUCTION") == True
        assert is_env_config_value("STAGING") == True
        assert is_env_config_value("TEST") == True
        assert is_env_config_value("LOCAL") == True
    
    def test_state_constants(self):
        """Test state constants."""
        assert is_env_config_value("ENABLED") == True
        assert is_env_config_value("DISABLED") == True
        assert is_env_config_value("ACTIVE") == True
        assert is_env_config_value("INACTIVE") == True
        assert is_env_config_value("ON") == True
        assert is_env_config_value("OFF") == True
    
    def test_mode_constants(self):
        """Test mode constants."""
        assert is_env_config_value("STRICT") == True
        assert is_env_config_value("PERMISSIVE") == True
        assert is_env_config_value("VERBOSE") == True
        assert is_env_config_value("QUIET") == True
        assert is_env_config_value("SILENT") == True
    
    def test_mixed_case_deployment_terms(self):
        """Test mixed-case deployment terms (case-insensitive)."""
        assert is_env_config_value("Development") == True
        assert is_env_config_value("Production") == True
        assert is_env_config_value("Staging") == True
        assert is_env_config_value("Testing") == True
        assert is_env_config_value("Local") == True
        assert is_env_config_value("Beta") == True
        assert is_env_config_value("Alpha") == True
    
    def test_lowercase_deployment_terms(self):
        """Test lowercase deployment terms."""
        assert is_env_config_value("development") == True
        assert is_env_config_value("production") == True
        assert is_env_config_value("staging") == True
    
    def test_invalid_mixed_case_non_deployment(self):
        """Test mixed-case non-deployment terms are invalid."""
        assert is_env_config_value("MyApp") == False
        assert is_env_config_value("TestValue") == False
    
    def test_invalid_lowercase_non_deployment(self):
        """Test lowercase non-deployment terms are invalid."""
        assert is_env_config_value("hello") == False
        assert is_env_config_value("world") == False
    
    def test_invalid_with_numbers(self):
        """Test values with numbers are invalid."""
        assert is_env_config_value("DEBUG1") == False
        assert is_env_config_value("PROD2") == False
    
    def test_invalid_with_special_chars(self):
        """Test values with special characters are invalid."""
        assert is_env_config_value("DEBUG-MODE") == False
        assert is_env_config_value("PROD_ENV") == False
    
    def test_invalid_empty_string(self):
        """Test empty string is invalid."""
        assert is_env_config_value("") == False
    
    def test_invalid_single_char(self):
        """Test single character is invalid."""
        assert is_env_config_value("A") == False
    
    def test_invalid_unknown_uppercase(self):
        """Test unknown uppercase words are invalid."""
        assert is_env_config_value("RANDOM") == False
        assert is_env_config_value("UNKNOWN") == False


# ============================================================================
# Number Validation Tests
# ============================================================================

class TestIsValidNumber:
    """Test RFC 8259 number validation."""
    
    def test_valid_integers(self):
        """Test valid integer values."""
        assert is_valid_number("0") == True
        assert is_valid_number("5") == True
        assert is_valid_number("42") == True
        assert is_valid_number("5000") == True
    
    def test_valid_negative_integers(self):
        """Test valid negative integers."""
        assert is_valid_number("-1") == True
        assert is_valid_number("-42") == True
        assert is_valid_number("-5000") == True
    
    def test_valid_floats(self):
        """Test valid float values."""
        assert is_valid_number("0.5") == True
        assert is_valid_number("3.14") == True
        assert is_valid_number("30.5") == True
        assert is_valid_number("99.99") == True
    
    def test_valid_negative_floats(self):
        """Test valid negative floats."""
        assert is_valid_number("-0.5") == True
        assert is_valid_number("-3.14") == True
    
    def test_valid_scientific_notation(self):
        """Test valid scientific notation."""
        assert is_valid_number("1.5e10") == True
        assert is_valid_number("2E-3") == True
        assert is_valid_number("1e5") == True
        assert is_valid_number("5E10") == True
    
    def test_zero_with_decimal(self):
        """Test zero with decimal is valid."""
        assert is_valid_number("0.0") == True
        assert is_valid_number("0.5") == True
        assert is_valid_number("0.123") == True
    
    def test_invalid_leading_zeros(self):
        """Test leading zeros are invalid (anti-quirk)."""
        assert is_valid_number("00123") == False
        assert is_valid_number("01") == False
        assert is_valid_number("007") == False
    
    def test_invalid_multiple_dots(self):
        """Test multiple dots are invalid."""
        assert is_valid_number("1.0.0") == False
        assert is_valid_number("1..5") == False
    
    def test_invalid_letters(self):
        """Test non-numeric values are invalid."""
        assert is_valid_number("abc") == False
        assert is_valid_number("12a34") == False
    
    def test_invalid_special_chars(self):
        """Test special characters are invalid."""
        assert is_valid_number("1,234") == False
        assert is_valid_number("$100") == False
    
    def test_invalid_empty_string(self):
        """Test empty string is invalid."""
        assert is_valid_number("") == False
    
    def test_invalid_just_dot(self):
        """Test just dot is invalid."""
        assert is_valid_number(".") == False
        assert is_valid_number("-.") == False
    
    def test_invalid_just_minus(self):
        """Test just minus is invalid."""
        assert is_valid_number("-") == False


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and integration scenarios."""
    
    def test_ascii_validation_with_escape_sequences(self):
        """Test ASCII validation allows escape sequence syntax."""
        # These are ASCII strings representing escape sequences
        validate_ascii_only("\\n")
        validate_ascii_only("\\t")
        validate_ascii_only("\\u0041")  # ASCII 'A' as Unicode escape
    
    def test_zpath_with_numbers_in_components(self):
        """Test zPath allows numbers in path components."""
        assert is_zpath_value("@.user.id123") == True
        assert is_zpath_value("~.item.0.name") == True
    
    def test_env_config_case_sensitivity(self):
        """Test environment constants are case-sensitive (except deployment terms)."""
        # Deployment terms are case-insensitive
        assert is_env_config_value("development") == True
        assert is_env_config_value("Development") == True
        assert is_env_config_value("DEVELOPMENT") == True
        
        # Other constants must be uppercase
        assert is_env_config_value("debug") == False
        assert is_env_config_value("Debug") == False
        assert is_env_config_value("DEBUG") == True
    
    def test_number_vs_string_boundary(self):
        """Test boundary between valid numbers and strings."""
        # Valid numbers
        assert is_valid_number("123") == True
        assert is_valid_number("1.23") == True
        
        # Not numbers (these are strings)
        assert is_valid_number("123abc") == False
        assert is_valid_number("v1.2.3") == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
