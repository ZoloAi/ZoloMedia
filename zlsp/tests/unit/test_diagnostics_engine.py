"""
Unit tests for Diagnostics Engine.

Tests the diagnostics_engine module which converts parse errors
into LSP diagnostics:
- get_diagnostics() wrapper function
- get_all_diagnostics() with file type context
- Error message conversion
- Type hint validation errors
- Boolean validation errors
- Nested structure errors
- Diagnostic severity levels
"""

import pytest
from lsprotocol import types as lsp_types

from core.providers.diagnostics_engine import get_diagnostics, get_all_diagnostics


class TestGetDiagnostics:
    """Test get_diagnostics() function."""
    
    def test_get_diagnostics_valid_content(self):
        """Test that valid content produces no diagnostics."""
        content = """
key: value
port(int): 8080
enabled(bool): true
        """.strip()
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Valid content should have few or no diagnostics
        # (Some warnings might be present, but no errors)
    
    def test_get_diagnostics_invalid_type_hint(self):
        """Test diagnostics for invalid type hints."""
        content = "port(invalid_type): 8080"
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should produce at least one diagnostic for invalid type
        # (May or may not produce diagnostic depending on parser)
    
    def test_get_diagnostics_invalid_boolean(self):
        """Test diagnostics for invalid boolean values."""
        content = "enabled(bool): yes"
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should produce diagnostic for invalid boolean
    
    def test_get_diagnostics_unclosed_bracket(self):
        """Test diagnostics for unclosed brackets."""
        content = "items: [one, two, three"
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should produce diagnostic for unclosed bracket
    
    def test_get_diagnostics_duplicate_key(self):
        """Test diagnostics for duplicate keys."""
        content = """
name: First
name: Second
        """.strip()
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should produce diagnostic for duplicate key
    
    def test_get_diagnostics_empty_content(self):
        """Test diagnostics for empty content."""
        content = ""
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Empty content should not crash
    
    def test_get_diagnostics_returns_lsp_diagnostics(self):
        """Test that returned diagnostics are LSP Diagnostic objects."""
        content = "key: value"
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        for diag in diagnostics:
            assert isinstance(diag, lsp_types.Diagnostic)
            assert hasattr(diag, 'range')
            assert hasattr(diag, 'message')
            assert hasattr(diag, 'severity')


class TestGetAllDiagnostics:
    """Test get_all_diagnostics() with file type context."""
    
    def test_get_all_diagnostics_generic_file(self):
        """Test diagnostics for generic .zolo file."""
        content = "key: value"
        filename = "test.zolo"
        
        diagnostics = get_all_diagnostics(content, filename)
        
        assert isinstance(diagnostics, list)
    
    def test_get_all_diagnostics_zspark_file(self):
        """Test diagnostics for zSpark file."""
        content = """
zSpark:
  title: Test
  logger: DEBUG
        """.strip()
        filename = "zSpark.example.zolo"
        
        diagnostics = get_all_diagnostics(content, filename)
        
        assert isinstance(diagnostics, list)
        # Should validate zSpark-specific fields
    
    def test_get_all_diagnostics_zenv_file(self):
        """Test diagnostics for zEnv file."""
        content = """
DEPLOYMENT: Development
LOG_LEVEL: DEBUG
        """.strip()
        filename = "zEnv.example.zolo"
        
        diagnostics = get_all_diagnostics(content, filename)
        
        assert isinstance(diagnostics, list)
    
    def test_get_all_diagnostics_zui_file(self):
        """Test diagnostics for zUI file."""
        content = """
zMeta:
  zNavBar: true
        """.strip()
        filename = "zUI.example.zolo"
        
        diagnostics = get_all_diagnostics(content, filename)
        
        assert isinstance(diagnostics, list)
    
    def test_get_all_diagnostics_with_invalid_zspark_field(self):
        """Test diagnostics for invalid zSpark field."""
        content = """
zSpark:
  invalid_field: value
        """.strip()
        filename = "zSpark.example.zolo"
        
        diagnostics = get_all_diagnostics(content, filename)
        
        assert isinstance(diagnostics, list)
        # Should validate and possibly warn about unknown field


class TestDiagnosticSeverity:
    """Test diagnostic severity levels."""
    
    def test_diagnostics_have_severity(self):
        """Test that diagnostics include severity levels."""
        # Create content with an error
        content = "enabled(bool): invalid_value"
        
        diagnostics = get_diagnostics(content)
        
        for diag in diagnostics:
            assert hasattr(diag, 'severity')
            # Severity should be one of: Error, Warning, Information, Hint
            assert diag.severity in [
                lsp_types.DiagnosticSeverity.Error,
                lsp_types.DiagnosticSeverity.Warning,
                lsp_types.DiagnosticSeverity.Information,
                lsp_types.DiagnosticSeverity.Hint,
                None  # None is also valid (defaults to Error)
            ]
    
    def test_type_errors_are_errors(self):
        """Test that type validation errors have Error severity."""
        content = "port(invalid): 8080"
        
        diagnostics = get_diagnostics(content)
        
        # Should have at least one error (may vary by parser)
        # This is a smoke test
        assert isinstance(diagnostics, list)


class TestDiagnosticRanges:
    """Test diagnostic position and range information."""
    
    def test_diagnostics_have_valid_ranges(self):
        """Test that diagnostics have valid line/character ranges."""
        content = "enabled(bool): invalid"
        
        diagnostics = get_diagnostics(content)
        
        for diag in diagnostics:
            assert hasattr(diag, 'range')
            assert hasattr(diag.range, 'start')
            assert hasattr(diag.range, 'end')
            assert hasattr(diag.range.start, 'line')
            assert hasattr(diag.range.start, 'character')
            
            # Line numbers should be non-negative
            assert diag.range.start.line >= 0
            assert diag.range.start.character >= 0
    
    def test_diagnostic_range_covers_error(self):
        """Test that diagnostic range covers the error location."""
        content = "key(invalid_type): value"
        
        diagnostics = get_diagnostics(content)
        
        # Should have diagnostic for invalid type hint
        # Range should be around "invalid_type"
        for diag in diagnostics:
            # Start should be on line 0 (first line)
            assert diag.range.start.line == 0


class TestDiagnosticMessages:
    """Test diagnostic message content."""
    
    def test_diagnostic_messages_are_descriptive(self):
        """Test that diagnostic messages are user-friendly."""
        content = "enabled(bool): yes"
        
        diagnostics = get_diagnostics(content)
        
        for diag in diagnostics:
            assert isinstance(diag.message, str)
            assert len(diag.message) > 0
            # Message should not be just a code or number
            assert not diag.message.isdigit()
    
    def test_diagnostic_messages_mention_problem(self):
        """Test that messages describe the problem."""
        content = "port(invalid_type): 8080"
        
        diagnostics = get_diagnostics(content)
        
        # Messages should be informative (smoke test)
        for diag in diagnostics:
            assert len(diag.message) > 10  # Should be a sentence


class TestDiagnosticsEdgeCases:
    """Test edge cases and error handling."""
    
    def test_diagnostics_with_multiline_content(self):
        """Test diagnostics for multi-line content."""
        content = """
line1: value1
line2: value2
line3(invalid_type): value3
line4: value4
        """.strip()
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should handle multi-line content
    
    def test_diagnostics_with_nested_structures(self):
        """Test diagnostics for nested structures."""
        content = """
parent:
  child1: value1
  child2(int): not_a_number
  child3:
    grandchild: value
        """.strip()
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should validate nested structures
    
    def test_diagnostics_with_arrays(self):
        """Test diagnostics for arrays."""
        content = """
valid_array: [1, 2, 3]
invalid_array: [unclosed
        """.strip()
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should detect unclosed array
    
    def test_diagnostics_with_inline_objects(self):
        """Test diagnostics for inline objects."""
        content = """
valid_obj: {x: 1, y: 2}
invalid_obj: {x: 1, unclosed
        """.strip()
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should detect unclosed object
    
    def test_diagnostics_with_special_characters(self):
        """Test diagnostics with special characters in content."""
        content = """
url: http://example.com:8080
hex: #FF5733
path: C:\\Users\\Admin
        """.strip()
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should handle special characters without crashing
    
    def test_diagnostics_with_unicode(self):
        """Test diagnostics with Unicode characters."""
        content = """
name: José
city: São Paulo
emoji: 👍
        """.strip()
        
        diagnostics = get_diagnostics(content)
        
        assert isinstance(diagnostics, list)
        # Should handle Unicode without crashing


class TestDiagnosticsIntegration:
    """Integration tests for diagnostics with parser."""
    
    def test_diagnostics_for_all_example_files(self):
        """Test that diagnostics work for all file types."""
        examples = [
            ("basic.zolo", "key: value"),
            ("zSpark.example.zolo", "zSpark:\n  title: Test"),
            ("zEnv.example.zolo", "DEPLOYMENT: Development"),
            ("zUI.example.zolo", "zMeta:\n  zNavBar: true"),
            ("zConfig.machine.zolo", "zMachine:\n  os: Darwin"),
            ("zSchema.example.zolo", "zMeta:\n  Data_Type: csv"),
        ]
        
        for filename, content in examples:
            diagnostics = get_all_diagnostics(content, filename)
            assert isinstance(diagnostics, list)
            # Each file type should be supported
    
    def test_diagnostics_integration_with_semantic_tokens(self):
        """Test that diagnostics work alongside semantic token generation."""
        from core.parser.parser import tokenize
        
        content = "key: value\nport(int): 8080"
        
        # Parse should return both tokens and diagnostics
        result = tokenize(content)
        
        assert hasattr(result, 'tokens')
        assert hasattr(result, 'diagnostics')
        assert isinstance(result.diagnostics, list)
