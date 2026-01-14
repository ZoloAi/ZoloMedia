"""
Tests for DiagnosticFormatter module.

Covers:
- Error message to diagnostic conversion
- Internal diagnostic to LSP diagnostic conversion
- Position extraction from error messages
- Severity determination
- Style validation
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from lsprotocol import types as lsp_types

from core.providers.provider_modules.diagnostic_formatter import DiagnosticFormatter
from core.lsp_types import Diagnostic as InternalDiagnostic, Position, Range


class TestFromErrorMessage:
    """Test converting error messages to LSP diagnostics."""
    
    def test_basic_error_message(self):
        """Test basic error without position info."""
        error_msg = "Parse error occurred"
        content = "key: value"
        
        diag = DiagnosticFormatter.from_error_message(error_msg, content)
        
        assert isinstance(diag, lsp_types.Diagnostic)
        assert diag.message == error_msg
        assert diag.severity == lsp_types.DiagnosticSeverity.Error
        assert diag.source == "zolo-parser"
        assert diag.range.start.line == 0
    
    def test_error_with_line_number(self):
        """Test extracting line number from error message."""
        error_msg = "Syntax error at line 5"
        content = "line1\nline2\nline3\nline4\nline5"
        
        diag = DiagnosticFormatter.from_error_message(error_msg, content)
        
        # Line 5 in message → line 4 in 0-based indexing
        assert diag.range.start.line == 4
    
    def test_duplicate_key_error(self):
        """Test extracting key name and highlighting it."""
        error_msg = "Duplicate key 'username' found at line 3."
        content = "name: Alice\nemail: alice@example.com\nusername: alice123\nusername: duplicate"
        
        diag = DiagnosticFormatter.from_error_message(error_msg, content)
        
        # Should be at line 2 (0-based)
        assert diag.range.start.line == 2
        # Should highlight 'username' (8 chars)
        assert diag.range.end.character - diag.range.start.character == 8
    
    def test_indentation_error(self):
        """Test highlighting entire line for indentation errors."""
        error_msg = "Inconsistent indentation at line 2"
        content = "key: value\n   bad_indent: value"
        
        diag = DiagnosticFormatter.from_error_message(error_msg, content)
        
        assert diag.range.start.line == 1
        # Should highlight entire line
        assert diag.range.end.character > 0
    
    def test_warning_severity(self):
        """Test warning severity detection."""
        error_msg = "Warning: Trailing comma found"
        content = "key: value,"
        
        diag = DiagnosticFormatter.from_error_message(error_msg, content)
        
        assert diag.severity == lsp_types.DiagnosticSeverity.Warning
    
    def test_hint_severity(self):
        """Test hint severity detection."""
        error_msg = "Hint: Consider using type hint"
        content = "port: 8080"
        
        diag = DiagnosticFormatter.from_error_message(error_msg, content)
        
        assert diag.severity == lsp_types.DiagnosticSeverity.Hint


class TestFromInternalDiagnostic:
    """Test converting internal Diagnostic to LSP Diagnostic."""
    
    def test_error_diagnostic(self):
        """Test converting error diagnostic."""
        internal_diag = InternalDiagnostic(
            range=Range(
                start=Position(line=5, character=10),
                end=Position(line=5, character=20)
            ),
            message="Invalid value for key",
            severity=1,  # Error
            source="zolo-validator"
        )
        
        lsp_diag = DiagnosticFormatter.from_internal_diagnostic(internal_diag)
        
        assert lsp_diag.message == "Invalid value for key"
        assert lsp_diag.severity == lsp_types.DiagnosticSeverity.Error
        assert lsp_diag.source == "zolo-validator"
        assert lsp_diag.range.start.line == 5
        assert lsp_diag.range.start.character == 10
        assert lsp_diag.range.end.character == 20
    
    def test_warning_diagnostic(self):
        """Test converting warning diagnostic."""
        internal_diag = InternalDiagnostic(
            range=Range(
                start=Position(line=2, character=5),
                end=Position(line=2, character=15)
            ),
            message="Deprecated syntax",
            severity=2,  # Warning
            source="zolo-parser"
        )
        
        lsp_diag = DiagnosticFormatter.from_internal_diagnostic(internal_diag)
        
        assert lsp_diag.severity == lsp_types.DiagnosticSeverity.Warning
    
    def test_information_diagnostic(self):
        """Test converting information diagnostic."""
        internal_diag = InternalDiagnostic(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=10)
            ),
            message="Informational message",
            severity=3,  # Information
            source="zolo-linter"
        )
        
        lsp_diag = DiagnosticFormatter.from_internal_diagnostic(internal_diag)
        
        assert lsp_diag.severity == lsp_types.DiagnosticSeverity.Information
    
    def test_hint_diagnostic(self):
        """Test converting hint diagnostic."""
        internal_diag = InternalDiagnostic(
            range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=5)
            ),
            message="Consider refactoring",
            severity=4,  # Hint
            source="zolo-linter"
        )
        
        lsp_diag = DiagnosticFormatter.from_internal_diagnostic(internal_diag)
        
        assert lsp_diag.severity == lsp_types.DiagnosticSeverity.Hint
    
    def test_unknown_severity_defaults_to_error(self):
        """Test unknown severity defaults to error."""
        internal_diag = InternalDiagnostic(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=1)
            ),
            message="Unknown severity",
            severity=99,  # Unknown
            source="test"
        )
        
        lsp_diag = DiagnosticFormatter.from_internal_diagnostic(internal_diag)
        
        assert lsp_diag.severity == lsp_types.DiagnosticSeverity.Error


class TestCreateUnexpectedError:
    """Test creating diagnostics for unexpected errors."""
    
    def test_unexpected_error(self):
        """Test creating diagnostic for unexpected exception."""
        error = Exception("Something went wrong")
        
        diag = DiagnosticFormatter.create_unexpected_error(error)
        
        assert "Unexpected error" in diag.message
        assert "Something went wrong" in diag.message
        assert diag.severity == lsp_types.DiagnosticSeverity.Error
        assert diag.source == "zolo-lsp"
        assert diag.range.start.line == 0
        assert diag.range.start.character == 0
    
    def test_unexpected_error_with_complex_exception(self):
        """Test handling complex exception messages."""
        error = ValueError("Invalid value: expected int, got str")
        
        diag = DiagnosticFormatter.create_unexpected_error(error)
        
        assert "Invalid value: expected int, got str" in diag.message


class TestValidateStyle:
    """Test style validation."""
    
    def test_no_style_issues(self):
        """Test content with no style issues."""
        content = "key: value\nnested:\n  child: data"
        
        diagnostics = DiagnosticFormatter.validate_style(content)
        
        assert len(diagnostics) == 0
    
    def test_trailing_whitespace(self):
        """Test detecting trailing whitespace."""
        content = "key: value  \nnested: data"
        
        diagnostics = DiagnosticFormatter.validate_style(content)
        
        assert len(diagnostics) == 1
        assert diagnostics[0].message == "Trailing whitespace"
        assert diagnostics[0].severity == lsp_types.DiagnosticSeverity.Information
        assert diagnostics[0].source == "zolo-linter"
        assert diagnostics[0].range.start.line == 0
        assert diagnostics[0].range.start.character == 10  # After "key: value"
    
    def test_multiple_trailing_whitespace(self):
        """Test detecting multiple trailing whitespace issues."""
        content = "line1  \nline2\nline3   \nline4 "
        
        diagnostics = DiagnosticFormatter.validate_style(content)
        
        assert len(diagnostics) == 3  # Lines 0, 2, 3 have trailing whitespace
        assert all(d.message == "Trailing whitespace" for d in diagnostics)
    
    def test_trailing_whitespace_position(self):
        """Test trailing whitespace highlighting correct position."""
        content = "key: value   "
        
        diagnostics = DiagnosticFormatter.validate_style(content)
        
        assert len(diagnostics) == 1
        # Should start at character 10 (after "key: value")
        assert diagnostics[0].range.start.character == 10
        # Should end at character 13 (3 spaces)
        assert diagnostics[0].range.end.character == 13


class TestExtractPosition:
    """Test position extraction from error messages."""
    
    def test_extract_line_at_line_pattern(self):
        """Test extracting line from 'at line N' pattern."""
        error_msg = "Error at line 10"
        content = "\n" * 20
        
        pos = DiagnosticFormatter._extract_position(error_msg, content)
        
        assert pos['line'] == 9  # 0-based
    
    def test_extract_line_line_colon_pattern(self):
        """Test extracting line from 'line N:' pattern."""
        error_msg = "line 5: Syntax error"
        content = "\n" * 10
        
        pos = DiagnosticFormatter._extract_position(error_msg, content)
        
        assert pos['line'] == 4  # 0-based
    
    def test_extract_key_position(self):
        """Test extracting key position from error message."""
        error_msg = "Duplicate key 'port' found at line 2"
        content = "name: test\nport: 8080\nother: value"
        
        pos = DiagnosticFormatter._extract_position(error_msg, content)
        
        assert pos['line'] == 1
        assert pos['start_char'] == 0  # 'port' starts at 0
        assert pos['end_char'] == 4    # 'port' is 4 chars
    
    def test_no_line_number(self):
        """Test default position when no line number found."""
        error_msg = "Generic error"
        content = "key: value"
        
        pos = DiagnosticFormatter._extract_position(error_msg, content)
        
        assert pos['line'] == 0
        assert pos['start_char'] == 0


class TestDetermineSeverity:
    """Test severity determination from error messages."""
    
    def test_error_severity(self):
        """Test default error severity."""
        msg = "Parse error occurred"
        
        severity = DiagnosticFormatter._determine_severity(msg)
        
        assert severity == lsp_types.DiagnosticSeverity.Error
    
    def test_warning_keyword(self):
        """Test warning severity from keyword."""
        msg = "Warning: Deprecated syntax"
        
        severity = DiagnosticFormatter._determine_severity(msg)
        
        assert severity == lsp_types.DiagnosticSeverity.Warning
    
    def test_hint_keyword(self):
        """Test hint severity from keyword."""
        msg = "Hint: Consider using type hints"
        
        severity = DiagnosticFormatter._determine_severity(msg)
        
        assert severity == lsp_types.DiagnosticSeverity.Hint
    
    def test_info_keyword(self):
        """Test information severity from keyword."""
        msg = "Info: File parsed successfully"
        
        severity = DiagnosticFormatter._determine_severity(msg)
        
        assert severity == lsp_types.DiagnosticSeverity.Information
    
    def test_case_insensitive(self):
        """Test case-insensitive severity detection."""
        msg = "WARNING: Something happened"
        
        severity = DiagnosticFormatter._determine_severity(msg)
        
        assert severity == lsp_types.DiagnosticSeverity.Warning


class TestIntegration:
    """Integration tests for DiagnosticFormatter."""
    
    def test_end_to_end_error_conversion(self):
        """Test complete error conversion workflow."""
        error_msg = "Duplicate key 'database' found at line 15."
        content = "\n" * 14 + "database: postgres\ndatabase: mysql"
        
        diag = DiagnosticFormatter.from_error_message(error_msg, content)
        
        assert diag.message == error_msg
        assert diag.range.start.line == 14
        assert diag.severity == lsp_types.DiagnosticSeverity.Error
        assert diag.source == "zolo-parser"
    
    def test_style_validation_with_content(self):
        """Test style validation on real content."""
        content = "# zSpark configuration  \nport: 8080\nhost: localhost   "
        
        diagnostics = DiagnosticFormatter.validate_style(content)
        
        assert len(diagnostics) == 2
        assert all(d.severity == lsp_types.DiagnosticSeverity.Information for d in diagnostics)
