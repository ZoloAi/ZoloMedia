"""
Diagnostic Formatter - Convert Errors to LSP Diagnostics

Handles:
- Error message parsing and position extraction
- Severity determination
- Range calculation for highlighting
- Internal diagnostic to LSP diagnostic conversion
"""

import re
from typing import List, Optional
from lsprotocol import types as lsp_types
from ...lsp_types import Diagnostic as InternalDiagnostic


class DiagnosticFormatter:
    """
    Format errors and validation issues into LSP diagnostics.
    
    Provides methods for:
    - Converting string error messages to diagnostics
    - Converting internal Diagnostic objects to LSP format
    - Extracting position information from error messages
    - Style and linting validation
    """
    
    # Severity mapping from internal to LSP
    SEVERITY_MAP = {
        1: lsp_types.DiagnosticSeverity.Error,
        2: lsp_types.DiagnosticSeverity.Warning,
        3: lsp_types.DiagnosticSeverity.Information,
        4: lsp_types.DiagnosticSeverity.Hint
    }
    
    @staticmethod
    def from_error_message(error_msg: str, content: str) -> lsp_types.Diagnostic:
        """
        Convert an error message string to an LSP diagnostic.
        
        Attempts to extract line number and position information from error message.
        
        Args:
            error_msg: Error message string
            content: Full file content (for context)
        
        Returns:
            LSP Diagnostic object
        
        Examples:
            >>> error = "Duplicate key 'name' found at line 10."
            >>> diag = DiagnosticFormatter.from_error_message(error, content)
            >>> diag.range.start.line
            9  # 0-based
        """
        position_info = DiagnosticFormatter._extract_position(error_msg, content)
        severity = DiagnosticFormatter._determine_severity(error_msg)
        
        return lsp_types.Diagnostic(
            range=lsp_types.Range(
                start=lsp_types.Position(
                    line=position_info['line'],
                    character=position_info['start_char']
                ),
                end=lsp_types.Position(
                    line=position_info['line'],
                    character=position_info['end_char']
                )
            ),
            message=error_msg,
            severity=severity,
            source="zolo-parser"
        )
    
    @staticmethod
    def from_internal_diagnostic(diag: InternalDiagnostic) -> lsp_types.Diagnostic:
        """
        Convert internal Diagnostic to LSP Diagnostic.
        
        Args:
            diag: Internal diagnostic from parser
        
        Returns:
            LSP Diagnostic object
        """
        severity = DiagnosticFormatter.SEVERITY_MAP.get(
            diag.severity,
            lsp_types.DiagnosticSeverity.Error
        )
        
        return lsp_types.Diagnostic(
            range=lsp_types.Range(
                start=lsp_types.Position(
                    line=diag.range.start.line,
                    character=diag.range.start.character
                ),
                end=lsp_types.Position(
                    line=diag.range.end.line,
                    character=diag.range.end.character
                )
            ),
            message=diag.message,
            severity=severity,
            source=diag.source
        )
    
    @staticmethod
    def create_unexpected_error(error: Exception) -> lsp_types.Diagnostic:
        """
        Create a diagnostic for unexpected errors.
        
        Args:
            error: Exception that was caught
        
        Returns:
            LSP Diagnostic at line 0
        """
        return lsp_types.Diagnostic(
            range=lsp_types.Range(
                start=lsp_types.Position(line=0, character=0),
                end=lsp_types.Position(line=0, character=1)
            ),
            message=f"Unexpected error: {str(error)}",
            severity=lsp_types.DiagnosticSeverity.Error,
            source="zolo-lsp"
        )
    
    @staticmethod
    def validate_style(content: str) -> List[lsp_types.Diagnostic]:
        """
        Validate document for style issues.
        
        Checks for:
        - Trailing whitespace
        - Inconsistent indentation
        - Mixed quote styles (TODO)
        
        Args:
            content: Full file content
        
        Returns:
            List of style diagnostics
        """
        diagnostics = []
        lines = content.splitlines()
        
        # Check for trailing whitespace (informational)
        for line_num, line in enumerate(lines):
            if line != line.rstrip():
                diagnostics.append(
                    lsp_types.Diagnostic(
                        range=lsp_types.Range(
                            start=lsp_types.Position(
                                line=line_num,
                                character=len(line.rstrip())
                            ),
                            end=lsp_types.Position(
                                line=line_num,
                                character=len(line)
                            )
                        ),
                        message="Trailing whitespace",
                        severity=lsp_types.DiagnosticSeverity.Information,
                        source="zolo-linter"
                    )
                )
        
        # Check for inconsistent indentation
        diagnostics.extend(DiagnosticFormatter._validate_indentation(lines))
        
        return diagnostics
    
    @staticmethod
    def _validate_indentation(lines: List[str]) -> List[lsp_types.Diagnostic]:
        """
        Validate indentation consistency (.zolo standard is 4 spaces, like Python).
        
        Detects:
        - Tabs instead of spaces
        - Non-multiples of 4 spaces
        - Unexpected indentation jumps (e.g., jumping from 4 to 12 spaces)
        
        Args:
            lines: List of file lines
        
        Returns:
            List of indentation diagnostics
        """
        diagnostics = []
        expected_indent_unit = 4  # Zolo standard (like Python, aligns with Tab key)
        prev_indent = 0
        
        for line_num, line in enumerate(lines):
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            # Get leading whitespace
            leading = line[:len(line) - len(line.lstrip())]
            curr_indent = len(leading)
            
            if curr_indent == 0:
                prev_indent = 0
                continue  # Root level
            
            # Check for tabs
            if '\t' in leading:
                diagnostics.append(
                    lsp_types.Diagnostic(
                        range=lsp_types.Range(
                            start=lsp_types.Position(line=line_num, character=0),
                            end=lsp_types.Position(line=line_num, character=len(leading))
                        ),
                        message="Inconsistent indentation detected (tabs instead of spaces)",
                        severity=lsp_types.DiagnosticSeverity.Warning,
                        source="zolo-linter"
                    )
                )
                prev_indent = curr_indent
                continue
            
            # Check if indentation is a multiple of expected_indent_unit
            if curr_indent % expected_indent_unit != 0:
                diagnostics.append(
                    lsp_types.Diagnostic(
                        range=lsp_types.Range(
                            start=lsp_types.Position(line=line_num, character=0),
                            end=lsp_types.Position(line=line_num, character=len(leading))
                        ),
                        message="Inconsistent indentation detected (expected multiples of 4 spaces)",
                        severity=lsp_types.DiagnosticSeverity.Warning,
                        source="zolo-linter"
                    )
                )
                prev_indent = curr_indent
                continue
            
            # Check for unexpected jumps (increase by more than one level)
            if curr_indent > prev_indent + expected_indent_unit:
                diagnostics.append(
                    lsp_types.Diagnostic(
                        range=lsp_types.Range(
                            start=lsp_types.Position(line=line_num, character=0),
                            end=lsp_types.Position(line=line_num, character=len(leading))
                        ),
                        message=f"Inconsistent indentation detected (jumped from {prev_indent} to {curr_indent} spaces)",
                        severity=lsp_types.DiagnosticSeverity.Warning,
                        source="zolo-linter"
                    )
                )
            
            prev_indent = curr_indent
        
        return diagnostics
    
    @staticmethod
    def _extract_position(error_msg: str, content: str) -> dict:
        """
        Extract position information from error message.
        
        Args:
            error_msg: Error message string
            content: Full file content
        
        Returns:
            Dict with 'line', 'start_char', 'end_char'
        """
        line_num = 0
        start_char = 0
        error_length = 1
        
        # Extract line number
        # Patterns: "at line 42", "line 42:", "Duplicate key 'name' found at line 10."
        line_match = re.search(r'(?:at line|line)\s+(\d+)', error_msg)
        if line_match:
            line_num = int(line_match.group(1)) - 1  # Convert to 0-based
        
        lines = content.splitlines()
        
        # For duplicate key errors, highlight the key name
        key_match = re.search(r"key '([^']+)'", error_msg)
        if key_match and 0 <= line_num < len(lines):
            key_name = key_match.group(1)
            line_content = lines[line_num]
            key_pos = line_content.find(key_name)
            if key_pos != -1:
                start_char = key_pos
                error_length = len(key_name)
        
        # For indentation errors, highlight the entire line
        elif 'indentation' in error_msg.lower() and 0 <= line_num < len(lines):
            error_length = len(lines[line_num].rstrip())
        
        # For non-ASCII/Unicode errors, highlight the entire line
        elif ('non-ascii' in error_msg.lower() or 'unicode' in error_msg.lower()):
            if 0 <= line_num < len(lines):
                error_length = len(lines[line_num].rstrip())
        
        return {
            'line': line_num,
            'start_char': start_char,
            'end_char': start_char + error_length
        }
    
    @staticmethod
    def _determine_severity(error_msg: str) -> lsp_types.DiagnosticSeverity:
        """
        Determine diagnostic severity from error message.
        
        Args:
            error_msg: Error message string
        
        Returns:
            LSP DiagnosticSeverity
        """
        msg_lower = error_msg.lower()
        
        if 'warning' in msg_lower:
            return lsp_types.DiagnosticSeverity.Warning
        elif 'hint' in msg_lower:
            return lsp_types.DiagnosticSeverity.Hint
        elif 'info' in msg_lower:
            return lsp_types.DiagnosticSeverity.Information
        
        return lsp_types.DiagnosticSeverity.Error
