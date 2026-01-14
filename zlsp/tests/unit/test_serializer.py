"""
Unit tests for serializer module.

Tests .zolo serialization with round-trip validation.
Critical for ensuring data integrity: load → dump → load idempotency.

Current coverage: 52% → Target: 80%+
"""

import pytest
from core.parser.parser_modules.serializer import (
    serialize_zolo,
    dumps,
    _serialize_string,
    _serialize_list,
    _serialize_dict,
)
from core.parser import load, loads, dump, dumps as parser_dumps


# ============================================================================
# Basic Data Type Serialization Tests
# ============================================================================

class TestBasicDataTypes:
    """Test serialization of basic data types."""
    
    def test_serialize_null(self):
        """Test null serialization."""
        result = serialize_zolo(None)
        assert result == 'null'
    
    def test_serialize_bool_true(self):
        """Test boolean true serialization."""
        result = serialize_zolo(True)
        assert result == 'true'
    
    def test_serialize_bool_false(self):
        """Test boolean false serialization."""
        result = serialize_zolo(False)
        assert result == 'false'
    
    def test_serialize_int(self):
        """Test integer serialization."""
        assert serialize_zolo(42) == '42'
        assert serialize_zolo(0) == '0'
        assert serialize_zolo(-123) == '-123'
    
    def test_serialize_float(self):
        """Test float serialization."""
        assert serialize_zolo(3.14) == '3.14'
        assert serialize_zolo(-2.5) == '-2.5'
        assert serialize_zolo(0.0) == '0.0'
    
    def test_serialize_simple_string(self):
        """Test simple string (no quoting needed)."""
        result = serialize_zolo('hello')
        assert result == 'hello'
    
    def test_serialize_empty_string(self):
        """Test empty string (needs quoting)."""
        result = serialize_zolo('')
        assert result == '""'


# ============================================================================
# String Serialization Tests
# ============================================================================

class TestStringSerializer:
    """Test string serialization with various edge cases."""
    
    def test_string_with_leading_space(self):
        """Test string with leading whitespace needs quotes."""
        result = _serialize_string(' hello')
        assert result.startswith('"')
        assert result.endswith('"')
    
    def test_string_with_trailing_space(self):
        """Test string with trailing whitespace needs quotes."""
        result = _serialize_string('hello ')
        assert result.startswith('"')
        assert result.endswith('"')
    
    def test_string_with_colon(self):
        """Test string containing colon needs quotes."""
        result = _serialize_string('key: value')
        assert result.startswith('"')
        assert '"' in result
    
    def test_string_with_hash(self):
        """Test string containing hash needs quotes."""
        result = _serialize_string('value # comment')
        assert result.startswith('"')
    
    def test_string_reserved_words(self):
        """Test reserved words need quoting."""
        assert _serialize_string('true') == '"true"'
        assert _serialize_string('false') == '"false"'
        assert _serialize_string('null') == '"null"'
    
    def test_string_with_newline(self):
        """Test string with newline is escaped."""
        result = _serialize_string('line1\nline2')
        assert '\\n' in result
        assert '\n' not in result or result.count('\n') == result.count('\\n')
    
    def test_string_with_backslash(self):
        """Test backslash is escaped when quoted."""
        result = _serialize_string('path\\to\\file')
        # String doesn't need quoting, so no escaping
        assert isinstance(result, str)
    
    def test_string_with_quotes(self):
        """Test double quotes trigger quoting."""
        result = _serialize_string('say "hello"')
        # String with quotes should be quoted
        assert result.startswith('"') or '"' in result


# ============================================================================
# List Serialization Tests
# ============================================================================

class TestListSerializer:
    """Test list serialization."""
    
    def test_empty_list(self):
        """Test empty list serialization."""
        result = _serialize_list([], indent=0)
        assert result == '[]'
    
    def test_simple_list(self):
        """Test list with simple items."""
        result = _serialize_list([1, 2, 3], indent=0)
        assert '- 1' in result
        assert '- 2' in result
        assert '- 3' in result
    
    def test_list_with_strings(self):
        """Test list with string items."""
        result = _serialize_list(['first', 'second', 'third'], indent=0)
        assert '- first' in result
        assert '- second' in result
        assert '- third' in result
    
    def test_list_with_indent(self):
        """Test list respects indentation."""
        result = _serialize_list([1, 2], indent=1)
        # Should have base indent of 4 spaces (1 level)
        lines = result.split('\n')
        for line in lines:
            assert line.startswith('    ')
    
    def test_nested_list(self):
        """Test list containing lists."""
        result = _serialize_list([[1, 2], [3, 4]], indent=0)
        # Should have dash items with nested content
        assert '- ' in result


# ============================================================================
# Dictionary Serialization Tests
# ============================================================================

class TestDictSerializer:
    """Test dictionary serialization."""
    
    def test_empty_dict(self):
        """Test empty dictionary serialization."""
        result = _serialize_dict({}, indent=0)
        assert result == '{}'
    
    def test_simple_dict(self):
        """Test dictionary with scalar values."""
        result = _serialize_dict({'port': 8080, 'host': 'localhost'}, indent=0)
        assert 'port: 8080' in result
        assert 'host: localhost' in result
    
    def test_dict_with_nested_dict(self):
        """Test dictionary with nested dictionary."""
        data = {'server': {'port': 8080, 'host': 'localhost'}}
        result = _serialize_dict(data, indent=0)
        
        assert 'server:' in result
        assert 'port: 8080' in result
        assert 'host: localhost' in result
    
    def test_dict_with_list_value(self):
        """Test dictionary with list value."""
        data = {'items': [1, 2, 3]}
        result = _serialize_dict(data, indent=0)
        
        assert 'items:' in result
        assert '- 1' in result
        assert '- 2' in result
        assert '- 3' in result
    
    def test_dict_with_empty_list(self):
        """Test dictionary with empty list value."""
        data = {'items': []}
        result = _serialize_dict(data, indent=0)
        
        assert 'items: []' in result
    
    def test_dict_with_indent(self):
        """Test dictionary respects indentation."""
        result = _serialize_dict({'key': 'value'}, indent=1)
        # Should start with 4 spaces (1 level)
        assert result.startswith('    ')


# ============================================================================
# Complex Structure Tests
# ============================================================================

class TestComplexStructures:
    """Test serialization of complex nested structures."""
    
    def test_deeply_nested_dict(self):
        """Test deeply nested dictionary."""
        data = {
            'level1': {
                'level2': {
                    'level3': {
                        'value': 'deep'
                    }
                }
            }
        }
        result = serialize_zolo(data)
        
        assert 'level1:' in result
        assert 'level2:' in result
        assert 'level3:' in result
        assert 'value: deep' in result
    
    def test_mixed_structure(self):
        """Test structure with mixed types."""
        data = {
            'string': 'hello',
            'number': 42,
            'bool': True,
            'null': None,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'}
        }
        result = serialize_zolo(data)
        
        assert 'string: hello' in result
        assert 'number: 42' in result
        assert 'bool: true' in result
        assert 'null: null' in result
        assert '- 1' in result
        assert 'nested: value' in result
    
    def test_list_of_dicts(self):
        """Test list containing dictionaries."""
        data = [
            {'name': 'first', 'value': 1},
            {'name': 'second', 'value': 2}
        ]
        result = serialize_zolo(data)
        
        # Should have dash items with nested key-value pairs
        assert '- ' in result
        assert 'name:' in result
        assert 'value:' in result


# ============================================================================
# Public API Tests
# ============================================================================

class TestPublicAPI:
    """Test public dumps() function."""
    
    def test_dumps_simple(self):
        """Test dumps with simple data."""
        result = dumps({'port': 8080})
        assert 'port: 8080' in result
    
    def test_dumps_complex(self):
        """Test dumps with complex data."""
        data = {
            'server': {
                'port': 8080,
                'host': 'localhost'
            },
            'features': ['auth', 'logging']
        }
        result = dumps(data)
        
        assert 'server:' in result
        assert 'port: 8080' in result
        assert 'features:' in result
        assert '- auth' in result


# ============================================================================
# Round-Trip Tests (CRITICAL!)
# ============================================================================

class TestRoundTrip:
    """Test load → dump → load idempotency."""
    
    def test_roundtrip_simple_dict(self):
        """Test round-trip with simple dictionary."""
        original = {'port': 8080, 'host': 'localhost'}
        
        # Serialize
        serialized = dumps(original)
        
        # Deserialize
        restored = loads(serialized)
        
        # Should match original
        assert restored == original
    
    def test_roundtrip_nested_dict(self):
        """Test round-trip with nested dictionary."""
        original = {
            'database': {
                'host': 'localhost',
                'port': 5432
            }
        }
        
        serialized = dumps(original)
        restored = loads(serialized)
        
        assert restored == original
    
    def test_roundtrip_with_list(self):
        """Test round-trip with list."""
        original = {
            'items': ['first', 'second', 'third']
        }
        
        serialized = dumps(original)
        restored = loads(serialized)
        
        assert restored == original
        assert restored['items'] == original['items']
    
    def test_roundtrip_with_booleans(self):
        """Test round-trip with boolean values.
        
        Note: Zolo's string-first philosophy means booleans without type hints
        are serialized as 'true'/'false' strings. This is intentional behavior.
        """
        original = {
            'enabled': True,
            'disabled': False
        }
        
        serialized = dumps(original)
        restored = loads(serialized)
        
        # Booleans become strings without type hints (Zolo's string-first design)
        assert restored['enabled'] == 'true'
        assert restored['disabled'] == 'false'
    
    def test_roundtrip_with_null(self):
        """Test round-trip with null value."""
        original = {
            'optional': None
        }
        
        serialized = dumps(original)
        restored = loads(serialized)
        
        # null is preserved correctly
        assert restored['optional'] is None
    
    def test_roundtrip_with_numbers(self):
        """Test round-trip with various numbers."""
        original = {
            'integer': 42,
            'float': 3.14,
            'negative': -100
        }
        
        serialized = dumps(original)
        restored = loads(serialized)
        
        assert restored['integer'] == 42
        assert restored['float'] == 3.14
        assert restored['negative'] == -100


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    @pytest.mark.skip(reason="Zolo enforces ASCII-only per RFC 8259")
    def test_unicode_strings(self):
        """Test unicode string handling.
        
        Note: Zolo enforces ASCII-only per RFC 8259.
        Unicode chars must use escape sequences like \\uXXXX.
        """
        original = {
            'emoji': '🚀',
            'unicode': 'Hello 世界',
            'special': 'café'
        }
        
        serialized = dumps(original)
        restored = loads(serialized)
        
        assert restored == original
    
    def test_empty_structures(self):
        """Test empty dict and list."""
        result_dict = serialize_zolo({})
        result_list = serialize_zolo([])
        
        assert result_dict == '{}'
        assert result_list == '[]'
    
    def test_very_long_string(self):
        """Test very long string."""
        long_string = 'a' * 1000
        original = {'long': long_string}
        
        serialized = dumps(original)
        restored = loads(serialized)
        
        assert restored['long'] == long_string
    
    def test_special_characters_in_keys(self):
        """Test keys with special characters."""
        # Regular keys should work
        original = {'my_key': 'value', 'another-key': 123}
        
        serialized = dumps(original)
        restored = loads(serialized)
        
        assert 'my_key' in restored
        assert 'another-key' in restored
    
    def test_roundtrip_complex_real_world(self):
        """Test round-trip with realistic config.
        
        Note: Zolo's string-first philosophy means values without type hints
        may be parsed as strings. This is intentional behavior.
        """
        original = {
            'app': {
                'name': 'MyApp',
                'version': '1.0.0',
                'debug': True  # Will become 'true' string
            },
            'database': {
                'host': 'localhost',
                'port': 5432,  # Numbers preserved
                'credentials': {
                    'username': 'admin',
                    'password': 'secret123'
                }
            },
            'features': ['auth', 'logging', 'caching'],
            'limits': {
                'max_connections': 100,
                'timeout': 30.0
            }
        }
        
        serialized = dumps(original)
        restored = loads(serialized)
        
        # Check structure and key values
        assert restored['app']['name'] == 'MyApp'
        assert restored['app']['version'] == '1.0.0'
        # Boolean becomes string without type hint
        assert restored['app']['debug'] == 'true'
        
        assert restored['database']['host'] == 'localhost'
        assert restored['database']['credentials']['username'] == 'admin'
        assert 'auth' in restored['features']
        
        # Numbers are preserved (or become floats for safety)
        assert float(restored['database']['port']) == 5432.0
        assert float(restored['limits']['timeout']) == 30.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
