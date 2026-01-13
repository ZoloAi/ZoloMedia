"""
LSP Type Definitions for .zolo Language Server

Defines position tracking and semantic token types for the Language Server Protocol.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class TokenType(Enum):
    """Semantic token types for .zolo syntax elements."""
    COMMENT = "comment"
    ROOT_KEY = "rootKey"
    NESTED_KEY = "nestedKey"
    ZMETA_KEY = "zmetaKey"  # Special key for zMeta in zUI files
    BIFROST_KEY = "bifrostKey"  # Underscore-prefixed keys: _zClass, etc.
    UI_ELEMENT_KEY = "uiElementKey"  # z-prefixed UI keys: zImage, zNavBar, zUL, zSub, etc.
    ZCONFIG_KEY = "zconfigKey"  # Uppercase Z-prefixed config keys in zEnv files: ZNAVBAR, ZDATA_*, etc.
    ZSPARK_KEY = "zsparkKey"  # zSpark root key in zSpark.*.zolo files (light green)
    ZSPARK_NESTED_KEY = "zsparkNestedKey"  # ALL nested keys under zSpark root in zSpark files (purple 98)
    ZSPARK_MODE_VALUE = "zsparkModeValue"  # zMode value (Terminal/zBifrost) - tomato red 196
    ZSPARK_VAFILE_VALUE = "zsparkVaFileValue"  # zVaFile value (zUI.*) - dark green 40
    ZSPARK_SPECIAL_VALUE = "zsparkSpecialValue"  # zBlock value - light purple 99
    ENV_CONFIG_VALUE = "envConfigValue"  # Environment/config constants (PROD, DEBUG, INFO, etc.) - bright yellow 226
    ZRBAC_KEY = "zrbacKey"  # zRBAC access control metadata key (tomato color)
    ZRBAC_OPTION_KEY = "zrbacOptionKey"  # zRBAC nested option keys: zGuest, authenticated, require_role, etc. (purple)
    ZMACHINE_EDITABLE_KEY = "zmachineEditableKey"  # Editable zMachine section keys (blue/cyan - INFO)
    ZMACHINE_LOCKED_KEY = "zmachineLockedKey"  # Auto-detected zMachine section keys (red/orange - ERROR)
    TYPE_HINT = "typeHint"
    TYPE_HINT_PAREN = "typeHintParen"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    NULL = "null"
    BRACKET_STRUCTURAL = "bracketStructural"
    BRACE_STRUCTURAL = "braceStructural"
    STRING_BRACKET = "stringBracket"  # [ ] inside string values
    STRING_BRACE = "stringBrace"      # { } inside string values
    COLON = "colon"
    COMMA = "comma"
    ESCAPE_SEQUENCE = "escapeSequence"
    VERSION_STRING = "versionString"
    TIMESTAMP_STRING = "timestampString"
    TIME_STRING = "timeString"
    RATIO_STRING = "ratioString"
    ZPATH_VALUE = "zpathValue"  # zPath data references: @.static.brand.logo.png, ~.config.settings (cyan)


@dataclass
class Position:
    """Position in a text document (0-based line and character)."""
    line: int  # 0-based
    character: int  # 0-based
    
    def __lt__(self, other):
        """Compare positions for ordering."""
        if self.line != other.line:
            return self.line < other.line
        return self.character < other.character
    
    def __le__(self, other):
        return self == other or self < other
    
    def __gt__(self, other):
        return not self <= other
    
    def __ge__(self, other):
        return not self < other


@dataclass
class Range:
    """Range in a text document (start and end positions)."""
    start: Position
    end: Position
    
    def contains(self, position: Position) -> bool:
        """Check if a position is within this range."""
        return self.start <= position <= self.end
    
    def overlaps(self, other: 'Range') -> bool:
        """Check if this range overlaps with another range."""
        return (self.start <= other.end and other.start <= self.end)


@dataclass
class SemanticToken:
    """Semantic token with position, type, and optional modifiers."""
    range: Range
    token_type: TokenType
    modifiers: List[str] = field(default_factory=list)
    
    @property
    def line(self) -> int:
        """Convenience property for token line number."""
        return self.range.start.line
    
    @property
    def start_char(self) -> int:
        """Convenience property for token start character."""
        return self.range.start.character
    
    @property
    def length(self) -> int:
        """
        Calculate token length.
        For multi-line tokens, this is the character span on the last line
        (LSP semantic tokens are line-relative).
        """
        if self.range.start.line == self.range.end.line:
            return self.range.end.character - self.range.start.character
        # Multi-line token: for LSP encoding, we use end position as length
        # This allows the encoder to properly represent the multi-line span
        return self.range.end.character
    
    def __repr__(self):
        return (
            f"SemanticToken(line={self.line}, "
            f"start={self.start_char}, "
            f"length={self.length}, "
            f"type={self.token_type.value})"
        )


@dataclass
class Diagnostic:
    """Diagnostic message (error, warning, etc.) for LSP."""
    range: Range
    message: str
    severity: int = 1  # 1=Error, 2=Warning, 3=Info, 4=Hint
    source: str = "zolo-lsp"


@dataclass
class ParseResult:
    """Result of parsing a .zolo file with both data and tokens."""
    data: any  # Parsed data structure
    tokens: List[SemanticToken]  # Semantic tokens for LSP
    errors: List[str] = field(default_factory=list)  # Parse errors (deprecated, use diagnostics)
    diagnostics: List[Diagnostic] = field(default_factory=list)  # Structured diagnostics
