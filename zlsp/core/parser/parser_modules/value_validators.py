"""
Value Validators - Context-aware value validation

Validates special values in different .zolo file types and generates diagnostics.
Separates validation logic from token emission for cleaner architecture.
"""

from typing import Optional, TYPE_CHECKING

from ...lsp_types import Diagnostic, Range, Position

if TYPE_CHECKING:
    from .token_emitter import TokenEmitter


class ValueValidator:
    """
    Context-aware value validator for special .zolo file types.
    
    Validates values based on file type and key context, generating
    appropriate diagnostics for invalid values.
    """
    
    # Valid values for each special key
    VALID_VALUES = {
        'zMode': {'Terminal', 'zBifrost'},
        'deployment': {'Production', 'Development'},
        'logger': {'DEBUG', 'SESSION', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'PROD'},
    }
    
    @staticmethod
    def validate_zmode(value: str, line: int, start_pos: int) -> Optional[Diagnostic]:
        """
        Validate zMode value (Terminal/zBifrost).
        
        Args:
            value: The value to validate
            line: Line number
            start_pos: Start position
            
        Returns:
            Diagnostic if invalid, None if valid
        """
        valid_values = ValueValidator.VALID_VALUES['zMode']
        if value not in valid_values:
            return Diagnostic(
                range=Range(
                    start=Position(line=line, character=start_pos),
                    end=Position(line=line, character=start_pos + len(value))
                ),
                message=f"Invalid zMode value: '{value}'. Expected: {' or '.join(valid_values)}.",
                severity=1,  # Error
                source="zolo-lsp"
            )
        return None
    
    @staticmethod
    def validate_deployment(value: str, line: int, start_pos: int) -> Optional[Diagnostic]:
        """
        Validate deployment value (Production/Development).
        
        Args:
            value: The value to validate
            line: Line number
            start_pos: Start position
            
        Returns:
            Diagnostic if invalid, None if valid
        """
        valid_values = ValueValidator.VALID_VALUES['deployment']
        if value not in valid_values:
            return Diagnostic(
                range=Range(
                    start=Position(line=line, character=start_pos),
                    end=Position(line=line, character=start_pos + len(value))
                ),
                message=f"Invalid deployment value: '{value}'. Expected: {' or '.join(valid_values)}.",
                severity=1,  # Error
                source="zolo-lsp"
            )
        return None
    
    @staticmethod
    def validate_logger(value: str, line: int, start_pos: int) -> Optional[Diagnostic]:
        """
        Validate logger value (valid log levels).
        
        Args:
            value: The value to validate
            line: Line number
            start_pos: Start position
            
        Returns:
            Diagnostic if invalid, None if valid
        """
        valid_values = ValueValidator.VALID_VALUES['logger']
        if value not in valid_values:
            return Diagnostic(
                range=Range(
                    start=Position(line=line, character=start_pos),
                    end=Position(line=line, character=start_pos + len(value))
                ),
                message=f"Invalid logger value: '{value}'. Expected one of: {', '.join(sorted(valid_values))}.",
                severity=1,  # Error
                source="zolo-lsp"
            )
        return None
    
    @staticmethod
    def validate_zvafile(value: str, line: int, start_pos: int) -> Optional[Diagnostic]:
        """
        Validate zVaFile value (must be zUI.*).
        
        Args:
            value: The value to validate
            line: Line number
            start_pos: Start position
            
        Returns:
            Diagnostic if invalid, None if valid
        """
        if not value.startswith('zUI.'):
            return Diagnostic(
                range=Range(
                    start=Position(line=line, character=start_pos),
                    end=Position(line=line, character=start_pos + len(value))
                ),
                message=f"Invalid zVaFile value: '{value}'. Must start with 'zUI.' (e.g., 'zUI.zBreakpoints').",
                severity=1,  # Error
                source="zolo-lsp"
            )
        return None
    
    @staticmethod
    def validate_zblock(value: str, line: int, start_pos: int) -> Optional[Diagnostic]:
        """
        Validate zBlock value (must be zBlock.*).
        
        Args:
            value: The value to validate
            line: Line number
            start_pos: Start position
            
        Returns:
            Diagnostic if invalid, None if valid
        """
        if not value.startswith('zBlock.'):
            return Diagnostic(
                range=Range(
                    start=Position(line=line, character=start_pos),
                    end=Position(line=line, character=start_pos + len(value))
                ),
                message=f"Invalid zBlock value: '{value}'. Must start with 'zBlock.' (e.g., 'zBlock.Navbar').",
                severity=1,  # Error
                source="zolo-lsp"
            )
        return None
    
    @staticmethod
    def validate_for_key(
        key: str,
        value: str,
        line: int,
        start_pos: int,
        emitter: 'TokenEmitter'
    ) -> bool:
        """
        Validate value based on key context and add diagnostic if invalid.
        
        Args:
            key: The key name
            value: The value to validate
            line: Line number
            start_pos: Start position
            emitter: TokenEmitter to add diagnostics to
            
        Returns:
            True if validation was performed (regardless of result), False if no validation for this key
        """
        diagnostic = None
        
        # zSpark-specific validations
        if emitter.is_zspark_file:
            if key == 'zMode':
                diagnostic = ValueValidator.validate_zmode(value, line, start_pos)
            elif key == 'deployment':
                diagnostic = ValueValidator.validate_deployment(value, line, start_pos)
            elif key == 'logger':
                diagnostic = ValueValidator.validate_logger(value, line, start_pos)
            elif key == 'zVaFile':
                diagnostic = ValueValidator.validate_zvafile(value, line, start_pos)
            elif key == 'zBlock':
                diagnostic = ValueValidator.validate_zblock(value, line, start_pos)
            else:
                return False  # No validation for this key
            
            if diagnostic:
                emitter.diagnostics.append(diagnostic)
            return True
        
        return False  # No validation performed


# Helper function for backward compatibility
def validate_special_value(
    key: str,
    value: str,
    line: int,
    start_pos: int,
    emitter: 'TokenEmitter'
) -> bool:
    """
    Convenience function to validate special values.
    
    Args:
        key: The key name
        value: The value to validate
        line: Line number
        start_pos: Start position
        emitter: TokenEmitter to add diagnostics to
        
    Returns:
        True if validation was performed, False otherwise
    """
    return ValueValidator.validate_for_key(key, value, line, start_pos, emitter)
