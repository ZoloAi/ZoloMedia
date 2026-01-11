"""
Tests for zolo.parser module
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import zolo
from zolo.exceptions import ZoloParseError


def test_loads_string_first():
    """Test that .zolo defaults to string-first."""
    data = zolo.loads('port: 8080')
    assert data == {'port': '8080'}
    assert isinstance(data['port'], str)


def test_loads_with_int_hint():
    """Test integer type hint."""
    data = zolo.loads('port(int): 8080')
    assert data == {'port': 8080}
    assert isinstance(data['port'], int)


def test_loads_with_float_hint():
    """Test float type hint."""
    data = zolo.loads('price(float): 19.99')
    assert data == {'price': 19.99}
    assert isinstance(data['price'], float)


def test_loads_with_bool_hint():
    """Test boolean type hint."""
    data = zolo.loads('enabled(bool): true')
    assert data == {'enabled': True}
    assert isinstance(data['enabled'], bool)


def test_loads_yaml_quirks_solved():
    """Test that .zolo solves YAML quirks."""
    data = zolo.loads('''
country: NO
enabled: yes
light: on
version: 1.0
''')
    # All should be strings (not False, True, True, 1.0)
    assert data['country'] == 'NO'
    assert data['enabled'] == 'yes'
    assert data['light'] == 'on'
    assert data['version'] == '1.0'


def test_loads_nested_structure():
    """Test nested dict structure."""
    data = zolo.loads('''
server:
  host: localhost
  port(int): 8080
''')
    assert data['server']['host'] == 'localhost'
    assert data['server']['port'] == 8080


def test_loads_list():
    """Test list parsing."""
    data = zolo.loads('''
tags:
  - web
  - api
''')
    assert data['tags'] == ['web', 'api']


def test_loads_yaml_format():
    """Test loading .yaml format (backward compatible)."""
    data = zolo.loads('port: 8080', file_extension='.yaml')
    # Should use native YAML parsing (int, not string)
    assert data == {'port': 8080}
    assert isinstance(data['port'], int)


def test_dumps():
    """Test dumping to string."""
    data = {'port': 8080, 'enabled': True}
    output = zolo.dumps(data)
    assert 'port: 8080' in output
    assert 'enabled: true' in output


def test_dumps_json():
    """Test dumping to JSON format."""
    data = {'port': 8080, 'enabled': True}
    output = zolo.dumps(data, file_extension='.json')
    assert '"port": 8080' in output
    assert '"enabled": true' in output


def test_load_and_dump_roundtrip(tmp_path):
    """Test load/dump roundtrip."""
    # Original data
    original = {
        'app': 'Test',
        'port': 8080,
        'enabled': True
    }
    
    # Dump to file
    file_path = tmp_path / "test.zolo"
    zolo.dump(original, file_path)
    
    # Load back
    loaded = zolo.load(file_path)
    
    # Should match (note: all values become strings in .zolo)
    assert loaded['app'] == 'Test'
    assert loaded['port'] == '8080'  # String-first
    assert loaded['enabled'] == 'True'  # String-first


def test_parse_error():
    """Test that invalid syntax raises ZoloParseError."""
    with pytest.raises(ZoloParseError):
        zolo.loads('invalid: yaml: {')


def test_file_not_found():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        zolo.load('nonexistent.zolo')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
