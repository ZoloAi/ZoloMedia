"""
Diagnostics Engine for .zolo Language Server

Converts parse errors and validation issues into LSP diagnostics.
"""

import re
from typing import List
from lsprotocol import types as lsp_types

from ..parser import tokenize
from ..exceptions import ZoloParseError
from ..lsp_types import ParseResult, Position, Range


def get_diagnostics(content: str, filename: str = None) -> List[lsp_types.Diagnostic]:
    """
    Parse .zolo content and return diagnostics.
    
    Converts parse errors and validation issues into LSP diagnostic format.
    
    Args:
        content: Raw .zolo file content
        filename: Optional filename for context-aware diagnostics
    
    Returns:
        List of LSP diagnostics
    
    Examples:
        >>> content = "name: value\\nname: duplicate"
        >>> diagnostics = get_diagnostics(content)
        >>> diagnostics[0].message
        "Duplicate key 'name' found..."
    """
    diagnostics = []
    
    try:
        # Parse content with filename for context-aware validation
        result = tokenize(content, filename=filename)
        
        # Convert parse errors to diagnostics (legacy string-based errors)
        for error in result.errors:
            diagnostic = _error_to_diagnostic(error, content)
            if diagnostic:
                diagnostics.append(diagnostic)
        
        # Add structured diagnostics from parser (new validation errors)
        for diag in result.diagnostics:
            lsp_diagnostic = lsp_types.Diagnostic(
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
                severity=diag.severity,  # 1=Error, 2=Warning, 3=Info, 4=Hint
                source=diag.source
            )
            diagnostics.append(lsp_diagnostic)
    
    except ZoloParseError as e:
        # Handle parse errors that weren't caught by tokenize()
        diagnostic = _error_to_diagnostic(str(e), content)
        if diagnostic:
            diagnostics.append(diagnostic)
    
    except Exception as e:
        # Catch-all for unexpected errors
        diagnostic = lsp_types.Diagnostic(
            range=lsp_types.Range(
                start=lsp_types.Position(line=0, character=0),
                end=lsp_types.Position(line=0, character=1)
            ),
            message=f"Unexpected error: {str(e)}",
            severity=lsp_types.DiagnosticSeverity.Error,
            source="zolo-lsp"
        )
        diagnostics.append(diagnostic)
    
    return diagnostics


def _error_to_diagnostic(error_msg: str, content: str) -> lsp_types.Diagnostic:
    """
    Convert an error message to an LSP diagnostic.
    
    Attempts to extract line number and position information from error message.
    
    Args:
        error_msg: Error message string
        content: Full file content (for context)
    
    Returns:
        LSP Diagnostic object
    """
    # Extract line number from error message
    # Common patterns:
    # - "... at line 42"
    # - "... line 42:"
    # - "Duplicate key 'name' found at line 10."
    
    line_num = 0
    char_pos = 0
    error_length = 1
    
    # Try to extract line number
    line_match = re.search(r'(?:at line|line)\s+(\d+)', error_msg)
    if line_match:
        line_num = int(line_match.group(1)) - 1  # Convert to 0-based
    
    # Try to extract more specific position info
    # For duplicate key errors, try to find the key name and highlight it
    key_match = re.search(r"key '([^']+)'", error_msg)
    if key_match:
        key_name = key_match.group(1)
        # Find key in the specified line
        lines = content.splitlines()
        if 0 <= line_num < len(lines):
            line_content = lines[line_num]
            key_pos = line_content.find(key_name)
            if key_pos != -1:
                char_pos = key_pos
                error_length = len(key_name)
    
    # Try to extract character position for indentation errors
    if 'indentation' in error_msg.lower():
        # Highlight the entire line for indentation errors
        lines = content.splitlines()
        if 0 <= line_num < len(lines):
            error_length = len(lines[line_num].rstrip())
    
    # Try to extract character position for non-ASCII errors
    if 'non-ascii' in error_msg.lower() or 'unicode' in error_msg.lower():
        # Try to find the Unicode escape sequence in the error message
        unicode_match = re.search(r'\\u([0-9A-Fa-f]{4})', error_msg)
        if unicode_match:
            # Find the offending character in the line
            lines = content.splitlines()
            if 0 <= line_num < len(lines):
                # For now, highlight the entire line
                error_length = len(lines[line_num].rstrip())
    
    # Determine severity
    severity = lsp_types.DiagnosticSeverity.Error
    if 'warning' in error_msg.lower():
        severity = lsp_types.DiagnosticSeverity.Warning
    elif 'hint' in error_msg.lower():
        severity = lsp_types.DiagnosticSeverity.Hint
    
    # Create diagnostic
    diagnostic = lsp_types.Diagnostic(
        range=lsp_types.Range(
            start=lsp_types.Position(line=line_num, character=char_pos),
            end=lsp_types.Position(line=line_num, character=char_pos + error_length)
        ),
        message=error_msg,
        severity=severity,
        source="zolo-parser"
    )
    
    return diagnostic


def validate_document(content: str) -> List[lsp_types.Diagnostic]:
    """
    Validate a .zolo document for common issues.
    
    This goes beyond parsing to check for:
    - Style issues (e.g., inconsistent naming)
    - Best practices
    - Potential problems
    
    Args:
        content: Raw .zolo file content
    
    Returns:
        List of diagnostics (warnings and hints)
    """
    diagnostics = []
    lines = content.splitlines()
    
    # Check for trailing whitespace (informational)
    for line_num, line in enumerate(lines):
        if line != line.rstrip():
            diagnostic = lsp_types.Diagnostic(
                range=lsp_types.Range(
                    start=lsp_types.Position(line=line_num, character=len(line.rstrip())),
                    end=lsp_types.Position(line=line_num, character=len(line))
                ),
                message="Trailing whitespace",
                severity=lsp_types.DiagnosticSeverity.Information,
                source="zolo-linter"
            )
            diagnostics.append(diagnostic)
    
    # Check for mixed quote styles in values (hint)
    # TODO: Implement more validation rules
    
    return diagnostics


def get_all_diagnostics(content: str, include_style: bool = True, filename: str = None) -> List[lsp_types.Diagnostic]:
    """
    Get all diagnostics for a document (errors + optional style warnings).
    
    Args:
        content: Raw .zolo file content
        include_style: Whether to include style/linter warnings
        filename: Optional filename for context-aware diagnostics
    
    Returns:
        Combined list of all diagnostics
    """
    diagnostics = get_diagnostics(content, filename=filename)
    
    if include_style:
        diagnostics.extend(validate_document(content))
    
    return diagnostics
