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
        - Emoji usage (INFO - suggests Unicode escapes for professionalism)
        - Mixed quote styles (TODO)
        
        Skips validation inside markdown code blocks (```...```).
        
        Args:
            content: Full file content
        
        Returns:
            List of style diagnostics
        """
        diagnostics = []
        lines = content.splitlines()
        
        # First, identify code block ranges to skip validation
        code_block_lines = DiagnosticFormatter._get_code_block_lines(lines)
        
        # Check for trailing whitespace (informational)
        for line_num, line in enumerate(lines):
            # Skip lines inside code blocks
            if line_num in code_block_lines:
                continue
            
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
        
        # Check for inconsistent indentation (also skips code blocks)
        diagnostics.extend(DiagnosticFormatter._validate_indentation(lines, code_block_lines))
        
        # Check for emoji usage - suggest Unicode escapes (NEW!)
        diagnostics.extend(DiagnosticFormatter._validate_emoji_usage(lines, code_block_lines))
        
        return diagnostics
    
    @staticmethod
    def _get_code_block_lines(lines: List[str]) -> set:
        """
        Get line numbers that are inside markdown code blocks.
        
        Code blocks are delimited by triple backticks (```).
        
        Args:
            lines: List of file lines
        
        Returns:
            Set of line numbers inside code blocks
        """
        code_block_lines = set()
        in_code_block = False
        
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            
            # Check for code block delimiter
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                # Include the delimiter line itself
                code_block_lines.add(line_num)
                continue
            
            # If inside code block, mark this line
            if in_code_block:
                code_block_lines.add(line_num)
        
        return code_block_lines
    
    @staticmethod
    def _validate_emoji_usage(lines: List[str], code_block_lines: set) -> List[lsp_types.Diagnostic]:
        r"""
        Validate emoji usage and suggest Unicode escapes for professionalism.
        
        Provides INFO-level hints when emojis are used directly in values.
        Suggests the Unicode escape format (\uXXXX or \UXXXXXXXX) as a more
        professional, portable, and RFC 8259 compliant alternative.
        
        Skips validation inside markdown code blocks.
        
        Args:
            lines: List of file lines
            code_block_lines: Set of line numbers inside code blocks
        
        Returns:
            List of emoji usage diagnostics (INFO severity)
        """
        import unicodedata
        import re
        
        diagnostics = []
        
        # Regex to find string values (after the colon)
        # Matches: key: value or key(type): value
        value_pattern = re.compile(r'^(\s*)([^:]+?)(?:\([^)]+\))?\s*:\s*(.*)$')
        
        for line_num, line in enumerate(lines):
            # Skip code blocks
            if line_num in code_block_lines:
                continue
            
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # Parse the line to get the value portion
            match = value_pattern.match(line)
            if not match:
                continue
            
            indent, key, value = match.groups()
            
            # Skip if no value
            if not value:
                continue
            
            # Find the value's position in the line
            value_start = line.index(value)
            
            # Check each character in the value for emojis
            for i, char in enumerate(value):
                codepoint = ord(char)
                
                # Only check non-ASCII characters
                if codepoint <= 127:
                    continue
                
                # Check if it's in emoji ranges
                is_emoji = (
                    (0x1F600 <= codepoint <= 0x1F64F) or  # emoticons
                    (0x1F300 <= codepoint <= 0x1F5FF) or  # symbols & pictographs
                    (0x1F680 <= codepoint <= 0x1F6FF) or  # transport & map
                    (0x1F1E0 <= codepoint <= 0x1F1FF) or  # flags
                    (0x2600 <= codepoint <= 0x26FF) or   # Miscellaneous Symbols
                    (0x2700 <= codepoint <= 0x27BF) or   # Dingbats
                    (0x1F900 <= codepoint <= 0x1F9FF) or  # Supplemental Symbols
                    (0x1FA70 <= codepoint <= 0x1FAFF)     # Symbols Extended-A
                )
                
                if not is_emoji:
                    continue
                
                # Generate appropriate escape sequence
                if codepoint <= 0xFFFF:
                    escape = f"\\u{codepoint:04X}"
                else:
                    escape = f"\\U{codepoint:08X}"
                
                # Get character name
                try:
                    char_name = unicodedata.name(char, f"U+{codepoint:04X}")
                except:
                    char_name = f"U+{codepoint:04X}"
                
                diagnostics.append(
                    lsp_types.Diagnostic(
                        range=lsp_types.Range(
                            start=lsp_types.Position(
                                line=line_num,
                                character=value_start + i
                            ),
                            end=lsp_types.Position(
                                line=line_num,
                                character=value_start + i + 1
                            )
                        ),
                        message=f"Emoji '{char}' ({char_name}). Pro tip: Use Unicode escape {escape} for portability and professionalism",
                        severity=lsp_types.DiagnosticSeverity.Information,
                        source="zolo-linter",
                        code="emoji-to-escape"
                    )
                )
                
                # Only report first emoji per line to avoid spam
                break
        
        return diagnostics
    
    @staticmethod
    def _validate_indentation(lines: List[str], code_block_lines: set = None) -> List[lsp_types.Diagnostic]:
        """
        Validate indentation consistency (like Python 3).
        
        Like Python, Zolo allows EITHER tabs OR spaces, but not both mixed.
        - Spaces: Must be multiples of 4 (recommended)
        - Tabs: Consistent tab-only indentation allowed
        - Mixed: Fatal error (like Python 3's TabError)
        
        Skips validation inside markdown code blocks.
        
        Args:
            lines: List of file lines
            code_block_lines: Set of line numbers inside code blocks (optional)
        
        Returns:
            List of indentation diagnostics
        """
        diagnostics = []
        expected_space_unit = 4  # When using spaces, must be multiples of 4
        
        if code_block_lines is None:
            code_block_lines = set()
        
        # First pass: detect what type of indentation is used
        uses_tabs = False
        uses_spaces = False
        first_tab_line = None
        first_space_line = None
        
        for line_num, line in enumerate(lines):
            # Skip code block lines
            if line_num in code_block_lines:
                continue
            
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
            # Skip code block lines
            if line_num in code_block_lines:
                continue
            
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
