"""
Error Message Formatter - User-friendly error messages with suggestions

Provides utilities for creating clear, helpful error messages with:
- Plain English explanations
- "Did you mean?" suggestions for typos
- Recovery examples
- Context-aware hints
"""

from typing import Optional, List
from difflib import get_close_matches


class ErrorFormatter:
    """
    Formats error messages to be user-friendly and actionable.
    
    Principles:
    - Use plain English, not technical jargon
    - Provide specific line/column information
    - Suggest fixes when possible
    - Include examples for common mistakes
    """
    
    # Common key typos and corrections
    COMMON_KEYS = {
        'zSpark', 'zUI', 'zEnv', 'zConfig', 'zSchema',
        'zMeta', 'zVaF', 'zMachine', 'zRBAC', 'zSub',
        'zMode', 'zBlock', 'zVaFile', 'deployment', 'logger',
        'zNavBar', 'zImage', 'zText', 'zURL', 'zTable',
        'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6',
        'Data_Type', 'zMigration', 'type', 'pk', 'required',
        'rules', 'format', 'default', 'min_length', 'max_length',
    }
    
    @staticmethod
    def suggest_correction(incorrect: str, valid_options: Optional[List[str]] = None,
                          cutoff: float = 0.6) -> Optional[str]:
        """
        Suggest a correction for a typo using fuzzy matching.
        
        Args:
            incorrect: The incorrect string
            valid_options: List of valid options (if None, uses COMMON_KEYS)
            cutoff: Similarity threshold (0.0-1.0)
            
        Returns:
            Suggested correction or None if no good match
        """
        if valid_options is None:
            valid_options = list(ErrorFormatter.COMMON_KEYS)
        
        matches = get_close_matches(incorrect, valid_options, n=1, cutoff=cutoff)
        return matches[0] if matches else None
    
    @staticmethod
    def format_duplicate_key_error(
        duplicate_key: str,
        first_line: int,
        current_line: int,
        first_key_raw: str
    ) -> str:
        """
        Format a duplicate key error with helpful suggestions.
        
        Args:
            duplicate_key: The duplicated key name
            first_line: Line number of first occurrence
            current_line: Line number of duplicate
            first_key_raw: Raw key from first occurrence (with modifiers)
            
        Returns:
            Formatted error message
        """
        msg = f"Duplicate key '{duplicate_key}' at line {current_line}.\n"
        msg += f"This key already exists at line {first_line}: '{first_key_raw}'\n"
        msg += "\n"
        msg += "Keys must be unique at each level. To fix this:\n"
        msg += f"  1. Rename one of the keys (e.g., '{duplicate_key}_2' or '{duplicate_key}_alt')\n"
        msg += f"  2. Move the duplicate under a different parent\n"
        msg += f"  3. Remove the duplicate if it's unintentional\n"
        
        return msg
    
    @staticmethod
    def format_indentation_error(
        line_num: int,
        expected_type: str,
        actual_type: str,
        first_indent_line: int
    ) -> str:
        """
        Format an indentation consistency error.
        
        Args:
            line_num: Current line number
            expected_type: Expected indentation type ('tab' or 'space')
            actual_type: Actual indentation type found
            first_indent_line: Line where indentation was first detected
            
        Returns:
            Formatted error message
        """
        expected_word = 'tabs' if expected_type == 'tab' else 'spaces'
        actual_word = 'tabs' if actual_type == 'tab' else 'spaces'
        
        msg = f"Inconsistent indentation at line {line_num}.\n"
        msg += f"This file uses {expected_word} (first seen at line {first_indent_line}), "
        msg += f"but this line uses {actual_word}.\n"
        msg += "\n"
        msg += "To fix this:\n"
        msg += f"  1. Use {expected_word} for all indentation in this file\n"
        msg += f"  2. Configure your editor to insert {expected_word} when you press Tab\n"
        msg += "\n"
        msg += "Editor config examples:\n"
        if expected_type == 'space':
            msg += "  • Vim: set expandtab\n"
            msg += "  • VS Code: \"editor.insertSpaces\": true\n"
        else:
            msg += "  • Vim: set noexpandtab\n"
            msg += "  • VS Code: \"editor.insertSpaces\": false\n"
        
        return msg
    
    @staticmethod
    def format_invalid_value_error(
        key: str,
        value: str,
        valid_values: List[str],
        line: int
    ) -> str:
        """
        Format an invalid value error with suggestions.
        
        Args:
            key: The key name
            value: The invalid value
            valid_values: List of valid values
            line: Line number
            
        Returns:
            Formatted error message
        """
        msg = f"Invalid value for '{key}' at line {line}: '{value}'\n"
        msg += f"Valid options: {', '.join(valid_values)}\n"
        
        # Try to suggest a correction
        suggestion = ErrorFormatter.suggest_correction(value, valid_values)
        if suggestion:
            msg += f"\nDid you mean: '{suggestion}'?\n"
        
        return msg
    
    @staticmethod
    def format_type_error(
        expected_type: str,
        actual_value: str,
        key: Optional[str] = None,
        line: Optional[int] = None
    ) -> str:
        """
        Format a type mismatch error.
        
        Args:
            expected_type: Expected type (int, float, bool, etc.)
            actual_value: The actual value that failed
            key: Optional key name for context
            line: Optional line number
            
        Returns:
            Formatted error message
        """
        location = f" at line {line}" if line else ""
        context = f" for key '{key}'" if key else ""
        
        msg = f"Type mismatch{context}{location}.\n"
        msg += f"Expected {expected_type}, got: '{actual_value}'\n"
        msg += "\n"
        
        # Type-specific hints
        if expected_type == 'int':
            msg += "Hint: Integer values should be whole numbers without quotes.\n"
            msg += "  Example: port: 8080\n"
        elif expected_type == 'float':
            msg += "Hint: Float values should include a decimal point.\n"
            msg += "  Example: timeout: 30.5\n"
        elif expected_type == 'bool':
            msg += "Hint: Boolean values should be 'true' or 'false' (lowercase).\n"
            msg += "  Example: enabled: true\n"
        
        return msg
    
    @staticmethod
    def format_parsing_error(
        error_type: str,
        line: int,
        column: Optional[int] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Format a general parsing error.
        
        Args:
            error_type: Type of parsing error
            line: Line number
            column: Optional column number
            context: Optional context (e.g., the problematic line content)
            
        Returns:
            Formatted error message
        """
        position = f"line {line}"
        if column is not None:
            position += f", column {column}"
        
        msg = f"Parsing error at {position}: {error_type}\n"
        
        if context:
            msg += f"\nProblematic content:\n  {context}\n"
        
        msg += "\nCommon causes:\n"
        msg += "  • Missing colon after key name\n"
        msg += "  • Unmatched brackets or braces\n"
        msg += "  • Invalid characters in key names\n"
        msg += "  • Incorrect indentation\n"
        
        return msg
    
    @staticmethod
    def format_file_not_found_error(filepath: str) -> str:
        """
        Format a file not found error.
        
        Args:
            filepath: The file path that wasn't found
            
        Returns:
            Formatted error message
        """
        msg = f"File not found: {filepath}\n"
        msg += "\nPlease check:\n"
        msg += "  1. The file path is correct\n"
        msg += "  2. The file exists at this location\n"
        msg += "  3. You have permission to read the file\n"
        msg += "  4. The file extension is .zolo or .json\n"
        
        return msg
    
    @staticmethod
    def format_unsupported_extension_error(extension: str, supported: List[str]) -> str:
        """
        Format an unsupported file extension error.
        
        Args:
            extension: The unsupported extension
            supported: List of supported extensions
            
        Returns:
            Formatted error message
        """
        msg = f"Unsupported file extension: {extension}\n"
        msg += f"Supported formats: {', '.join(supported)}\n"
        msg += "\n"
        msg += "To use your file:\n"
        msg += f"  1. Save it with a supported extension (e.g., {supported[0]})\n"
        msg += f"  2. Or convert the file to a supported format\n"
        
        return msg


# Convenience functions for common error patterns
def did_you_mean(incorrect: str, valid_options: List[str]) -> Optional[str]:
    """
    Quick "did you mean?" suggestion.
    
    Args:
        incorrect: The incorrect string
        valid_options: List of valid options
        
    Returns:
        Formatted suggestion or None
    """
    suggestion = ErrorFormatter.suggest_correction(incorrect, valid_options)
    if suggestion:
        return f"Did you mean '{suggestion}'?"
    return None
