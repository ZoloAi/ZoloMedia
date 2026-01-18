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
        Validate indentation consistency (like Python 3).
        
        Like Python, Zolo allows EITHER tabs OR spaces, but not both mixed.
        - Spaces: Must be multiples of 4 (recommended)
        - Tabs: Consistent tab-only indentation allowed
        - Mixed: Fatal error (like Python 3's TabError)
        
        Args:
            lines: List of file lines
        
        Returns:
            List of indentation diagnostics
        """
        diagnostics = []
        expected_space_unit = 4  # When using spaces, must be multiples of 4
        
        # First pass: detect what type of indentation is used
        uses_tabs = False
        uses_spaces = False
        first_tab_line = None
        first_space_line = None
        
        for line_num, line in enumerate(lines):
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            # Get leading whitespace
            leading = line[:len(line) - len(line.lstrip())]
            
            if not leading:
                continue  # Root level
            
            # Detect indentation type
            if '\t' in leading:
                if not uses_tabs:
                    uses_tabs = True
                    first_tab_line = line_num
            if ' ' in leading:
                if not uses_spaces:
                    uses_spaces = True
                    first_space_line = line_num
        
        # Check for mixing tabs and spaces (Python 3 style: TabError)
        if uses_tabs and uses_spaces:
            # Report error on the second type that was introduced
            if first_space_line is not None and first_tab_line is not None:
                error_line = max(first_space_line, first_tab_line)
                indent_type = "tabs" if error_line == first_tab_line else "spaces"
                first_type = "spaces" if indent_type == "tabs" else "tabs"
                
                diagnostics.append(
                    lsp_types.Diagnostic(
                        range=lsp_types.Range(
                            start=lsp_types.Position(line=error_line, character=0),
                            end=lsp_types.Position(line=error_line, character=1)
                        ),
                        message=f"Inconsistent use of tabs and spaces in indentation (file uses {first_type}, this line uses {indent_type})",
                        severity=lsp_types.DiagnosticSeverity.Error,  # Error like Python 3
                        source="zolo-linter"
                    )
                )
            return diagnostics  # Stop here, mixing is fatal
        
        # Second pass: validate consistency based on detected type
        prev_indent = 0
        
        for line_num, line in enumerate(lines):
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            # Get leading whitespace
            leading = line[:len(line) - len(line.lstrip())]
            
            if not leading:
                prev_indent = 0
                continue  # Root level
            
            # Calculate indent level based on type
            if uses_tabs:
                # Tab-based indentation: count tabs
                curr_indent = leading.count('\t')
                
                # Check for unexpected jumps (increase by more than one level)
                if curr_indent > prev_indent + 1:
                    diagnostics.append(
                        lsp_types.Diagnostic(
                            range=lsp_types.Range(
                                start=lsp_types.Position(line=line_num, character=0),
                                end=lsp_types.Position(line=line_num, character=len(leading))
                            ),
                            message=f"Inconsistent indentation (jumped from {prev_indent} to {curr_indent} tabs)",
                            severity=lsp_types.DiagnosticSeverity.Warning,
                            source="zolo-linter"
                        )
                    )
                
                prev_indent = curr_indent
            
            elif uses_spaces:
                # Space-based indentation: must be multiples of 4
                curr_indent = len(leading)
                
                # Check if indentation is a multiple of expected_space_unit
                if curr_indent % expected_space_unit != 0:
                    diagnostics.append(
                        lsp_types.Diagnostic(
                            range=lsp_types.Range(
                                start=lsp_types.Position(line=line_num, character=0),
                                end=lsp_types.Position(line=line_num, character=len(leading))
                            ),
                            message="Inconsistent indentation (expected multiples of 4 spaces)",
                            severity=lsp_types.DiagnosticSeverity.Warning,
                            source="zolo-linter"
                        )
                    )
                    prev_indent = curr_indent
                    continue
                
                # Check for unexpected jumps (increase by more than one level)
                if curr_indent > prev_indent + expected_space_unit:
                    diagnostics.append(
                        lsp_types.Diagnostic(
                            range=lsp_types.Range(
                                start=lsp_types.Position(line=line_num, character=0),
                                end=lsp_types.Position(line=line_num, character=len(leading))
                            ),
                            message=f"Inconsistent indentation (jumped from {prev_indent} to {curr_indent} spaces)",
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
