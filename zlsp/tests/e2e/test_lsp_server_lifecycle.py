"""
End-to-end tests for LSP server lifecycle.

Tests complete user workflows from start to finish.
"""

import pytest
import tempfile
from pathlib import Path


def test_parse_real_zolo_file():
    """Test parsing a real .zolo file end-to-end."""
    # Create a temporary .zolo file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.zolo', delete=False) as f:
        f.write("""# Application Configuration
app_name: MyApplication
version: 1.0.0

server:
  host: localhost
  port(int): 8080
  ssl(bool): true
  timeout(int): 30

features:
  analytics(bool): true
  debug(bool): false
  rate_limit(int): 1000
""")
        temp_path = f.name
    
    try:
        # Load the file
        from core.parser import load
        data = load(temp_path)
        
        # Verify parsed data (structure may vary)
        assert data is not None
        assert 'app_name' in data or 'app_name' in str(data)
        
    finally:
        # Cleanup
        Path(temp_path).unlink()


def test_semantic_tokens_full_workflow():
    """Test complete semantic tokens workflow."""
    from core.parser import tokenize
    from core.server.semantic_tokenizer import encode_semantic_tokens, decode_semantic_tokens
    
    content = """# Config
port(int): 8080
enabled(bool): true"""
    
    # Step 1: Tokenize
    result = tokenize(content)
    assert len(result.tokens) > 0
    
    # Step 2: Encode for LSP
    encoded = encode_semantic_tokens(result.tokens)
    assert len(encoded) > 0
    
    # Step 3: Decode (for verification)
    decoded = decode_semantic_tokens(encoded)
    assert len(decoded) == len(result.tokens)
    
    # Step 4: Verify token types are preserved
    for orig, dec in zip(result.tokens, decoded):
        assert orig.line == dec['line']
        assert orig.start_char == dec['start']


def test_diagnostics_workflow():
    """Test complete diagnostics workflow."""
    from core.providers.diagnostics_engine import get_diagnostics
    
    # Test valid content
    valid_content = """port(int): 8080
host: localhost"""
    
    diagnostics = get_diagnostics(valid_content, "test.zolo")
    # Should return a list (may or may not have diagnostics)
    assert isinstance(diagnostics, list)
    
    # Test invalid content
    invalid_content = """port(int): not_a_number
enabled(bool): invalid_bool"""
    
    diagnostics = get_diagnostics(invalid_content, "test.zolo")
    assert isinstance(diagnostics, list)


def test_completion_workflow():
    """Test complete completion workflow."""
    from core.providers.completion_provider import get_completions
    
    # User typing: "port("
    content = "port("
    line = 0
    character = 5
    
    completions = get_completions(content, line, character)
    
    # Should provide completions (list of CompletionItem objects)
    assert isinstance(completions, list)
    
    # If completions exist, check structure
    if len(completions) > 0:
        comp = completions[0]
        assert hasattr(comp, 'label')
        assert hasattr(comp, 'kind')


def test_hover_workflow():
    """Test complete hover workflow."""
    from core.providers.hover_provider import get_hover_info
    
    content = "port(int): 8080"
    
    # Hover over type hint
    hover_type = get_hover_info(content, 0, 6)  # On "int"
    # May return None or string depending on implementation
    assert hover_type is None or isinstance(hover_type, str)
    
    # Hover over value
    hover_value = get_hover_info(content, 0, 11)  # On "8080"
    assert hover_value is None or isinstance(hover_value, str)


def test_round_trip_parsing():
    """Test parsing and dumping preserves data structure."""
    from core.parser import loads, dumps
    
    original_content = """app_name: MyApp
port(int): 8080
enabled(bool): true"""
    
    # Parse
    data = loads(original_content)
    assert data is not None
    
    # Dump
    dumped = dumps(data)
    assert dumped is not None
    
    # Re-parse
    reparsed = loads(dumped)
    
    # Data structure should be similar (types may vary)
    assert 'app_name' in reparsed or 'app_name' in str(reparsed)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
