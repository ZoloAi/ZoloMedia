"""
Tests for zolo.type_hints module
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from zolo.type_hints import (
    process_type_hints,
    convert_value_by_type,
    has_type_hint,
    extract_type_hint
)
from zolo.exceptions import ZoloTypeError


def test_process_type_hints_string_first():
    """Test string-first processing."""
    data = {'port': 8080, 'enabled': True}
    result = process_type_hints(data, string_first=True)
    assert result == {'port': '8080', 'enabled': 'True'}


def test_process_type_hints_native():
    """Test native type preservation."""
    data = {'port': 8080, 'enabled': True}
    result = process_type_hints(data, string_first=False)
    assert result == {'port': 8080, 'enabled': True}


def test_process_type_hints_with_int():
    """Test integer type hint."""
    data = {'port(int)': '8080'}
    result = process_type_hints(data, string_first=True)
    assert result == {'port': 8080}
    assert isinstance(result['port'], int)


def test_process_type_hints_with_float():
    """Test float type hint."""
    data = {'price(float)': '19.99'}
    result = process_type_hints(data, string_first=True)
    assert result == {'price': 19.99}
    assert isinstance(result['price'], float)


def test_process_type_hints_with_bool():
    """Test boolean type hint."""
    data = {'enabled(bool)': 'true'}
    result = process_type_hints(data, string_first=True)
    assert result == {'enabled': True}
    assert isinstance(result['enabled'], bool)


def test_convert_value_by_type_int():
    """Test int conversion."""
    result = convert_value_by_type('8080', 'int', 'port')
    assert result == 8080
    assert isinstance(result, int)


def test_convert_value_by_type_float():
    """Test float conversion."""
    result = convert_value_by_type('19.99', 'float', 'price')
    assert result == 19.99
    assert isinstance(result, float)


def test_convert_value_by_type_bool_true():
    """Test bool conversion (true values)."""
    for value in ['true', 'yes', '1', 'on']:
        result = convert_value_by_type(value, 'bool', 'enabled')
        assert result is True


def test_convert_value_by_type_bool_false():
    """Test bool conversion (false values)."""
    for value in ['false', 'no', '0', 'off']:
        result = convert_value_by_type(value, 'bool', 'enabled')
        assert result is False


def test_convert_value_by_type_null():
    """Test null conversion."""
    result = convert_value_by_type('anything', 'null', 'value')
    assert result is None


def test_convert_value_by_type_invalid():
    """Test that invalid conversion raises ZoloTypeError."""
    with pytest.raises(ZoloTypeError):
        convert_value_by_type('not_a_number', 'int', 'port')


def test_has_type_hint():
    """Test type hint detection."""
    assert has_type_hint('port(int)') is True
    assert has_type_hint('port') is False


def test_extract_type_hint_with_hint():
    """Test extracting type hint."""
    key, hint = extract_type_hint('port(int)')
    assert key == 'port'
    assert hint == 'int'


def test_extract_type_hint_without_hint():
    """Test extracting from key without hint."""
    key, hint = extract_type_hint('port')
    assert key == 'port'
    assert hint is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
