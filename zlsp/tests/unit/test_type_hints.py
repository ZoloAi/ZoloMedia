"""
Unit tests for core.parser.type_hints module
"""

import pytest
from core.parser.parser_modules.type_hints import (
    process_type_hints,
    convert_value_by_type,
    has_type_hint,
    extract_type_hint,
    TYPE_HINT_PATTERN
)
from core.exceptions import ZoloTypeError


def test_has_type_hint():
    """Test type hint detection."""
    assert has_type_hint('port(int)') == True
    assert has_type_hint('enabled(bool)') == True
    assert has_type_hint('plain_key') == False
    # Invalid type hints return False (only valid types match)
    assert has_type_hint('key_with_parens_not_hint(something)') == False


def test_extract_type_hint():
    """Test type hint extraction."""
    assert extract_type_hint('port(int)') == ('port', 'int')
    assert extract_type_hint('price(float)') == ('price', 'float')
    assert extract_type_hint('enabled(bool)') == ('enabled', 'bool')
    # Keys without type hints return (key, None)
    assert extract_type_hint('plain_key') == ('plain_key', None)


def test_convert_int():
    """Test integer conversion."""
    assert convert_value_by_type('8080', 'int', 'port') == 8080
    assert convert_value_by_type('0', 'int', 'zero') == 0
    assert convert_value_by_type('-42', 'int', 'negative') == -42


def test_convert_float():
    """Test float conversion."""
    assert convert_value_by_type('19.99', 'float', 'price') == 19.99
    assert convert_value_by_type('0.0', 'float', 'zero') == 0.0
    assert convert_value_by_type('-3.14', 'float', 'pi') == -3.14


def test_convert_bool():
    """Test boolean conversion."""
    # True values
    assert convert_value_by_type('true', 'bool', 'enabled') == True
    assert convert_value_by_type('True', 'bool', 'enabled') == True
    assert convert_value_by_type('yes', 'bool', 'enabled') == True
    assert convert_value_by_type('on', 'bool', 'enabled') == True
    assert convert_value_by_type('1', 'bool', 'enabled') == True
    
    # False values
    assert convert_value_by_type('false', 'bool', 'disabled') == False
    assert convert_value_by_type('False', 'bool', 'disabled') == False
    assert convert_value_by_type('no', 'bool', 'disabled') == False
    assert convert_value_by_type('off', 'bool', 'disabled') == False
    assert convert_value_by_type('0', 'bool', 'disabled') == False


def test_convert_list():
    """Test list conversion."""
    result = convert_value_by_type(['a', 'b', 'c'], 'list', 'items')
    assert result == ['a', 'b', 'c']
    assert isinstance(result, list)


def test_convert_dict():
    """Test dict conversion."""
    result = convert_value_by_type({'key': 'value'}, 'dict', 'config')
    assert result == {'key': 'value'}
    assert isinstance(result, dict)


def test_convert_string():
    """Test string conversion (default)."""
    assert convert_value_by_type(123, 'str', 'value') == '123'
    assert convert_value_by_type(True, 'str', 'value') == 'True'
    assert convert_value_by_type('hello', 'str', 'value') == 'hello'


def test_convert_invalid_int():
    """Test invalid integer conversion raises error."""
    with pytest.raises(ZoloTypeError):
        convert_value_by_type('not_a_number', 'int', 'port')


def test_convert_invalid_float():
    """Test invalid float conversion raises error."""
    with pytest.raises(ZoloTypeError):
        convert_value_by_type('not_a_float', 'float', 'price')


def test_type_hint_pattern_regex():
    """Test the TYPE_HINT_PATTERN regex."""
    import re
    
    # Valid patterns
    assert re.match(TYPE_HINT_PATTERN, 'key(int)')
    assert re.match(TYPE_HINT_PATTERN, 'my_key(float)')
    assert re.match(TYPE_HINT_PATTERN, 'enabled(bool)')
    
    # Invalid patterns
    assert not re.match(TYPE_HINT_PATTERN, 'key')
    assert not re.match(TYPE_HINT_PATTERN, 'key()')


def test_process_type_hints_nested():
    """Test processing type hints in nested structures."""
    data = {
        'server': {
            'port(int)': '8080',
            'enabled(bool)': 'true'
        }
    }
    result = process_type_hints(data, string_first=True)
    assert result == {
        'server': {
            'port': 8080,
            'enabled': True
        }
    }


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
