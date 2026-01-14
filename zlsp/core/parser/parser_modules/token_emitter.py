"""
Token Emitter - Semantic token emission with unified block tracking

Now using BlockTracker - replacing 17+ individual tracking lists! 🎉
"""

from pathlib import Path
from typing import List, Optional, Tuple

from .block_tracker import BlockTracker
from .file_type_detector import FileTypeDetector, FileType
from ...lsp_types import SemanticToken, TokenType, Position, Range, Diagnostic


def _char_to_utf16_offset(text: str, char_offset: int) -> int:
    """
    Convert Python character offset to UTF-16 code unit offset.
    
    LSP uses UTF-16 positions, but Python uses Unicode code points.
    This matters for emoji and characters outside the Basic Multilingual Plane.
    
    Args:
        text: Line text
        char_offset: Character offset in Python string
    
    Returns:
        UTF-16 code unit offset for LSP
    """
    # Take substring up to the character offset
    substring = text[:char_offset]
    # Encode to UTF-16LE and count bytes, divide by 2 for code units
    utf16_bytes = substring.encode('utf-16-le')
    return len(utf16_bytes) // 2


class TokenEmitter:
    """
    Semantic token emitter with unified block tracking.
    
    Tracks parsing context (file type, nested blocks) and emits semantic tokens
    for LSP clients to enable syntax highlighting.
    
    Uses BlockTracker for DRY block context management.
    """
    
    def __init__(self, content: str, filename: Optional[str] = None):
        """
        Initialize token emitter.
        
        Args:
            content: File content to parse
            filename: Optional filename for file type detection
        """
        self.content = content
        self.lines = content.splitlines(keepends=False)  # Keep lines for UTF-16 conversion
        self.tokens: List[SemanticToken] = []
        self.diagnostics: List[Diagnostic] = []  # Validation errors and warnings
        self.comment_ranges: List[Tuple[int, int, int, int]] = []  # [(start_line, start_col, end_line, end_col), ...]
        self.filename = filename
        
        # 🎯 FILE TYPE DETECTION - using FileTypeDetector
        self.file_detector = FileTypeDetector(filename)
        
        # Convenience properties for backward compatibility
        self.is_zui_file = self.file_detector.is_zui()
        self.is_zenv_file = self.file_detector.is_zenv()
        self.is_zspark_file = self.file_detector.is_zspark()
        self.is_zconfig_file = self.file_detector.is_zconfig()
        self.is_zschema_file = self.file_detector.is_zschema()
        
        # Component names (for zUI.zVaF.zolo -> "zVaF", etc.)
        component = self.file_detector.component_name
        self.zui_component_name = component if self.is_zui_file else None
        self.zspark_component_name = component if self.is_zspark_file else None
        self.zconfig_component_name = component if self.is_zconfig_file else None
        
        # 🎉 UNIFIED BLOCK TRACKING - replaces 17+ individual lists!
        self.block_tracker = BlockTracker()
    
    # ========================================================================
    # COMMENT TRACKING
    # ========================================================================
    
    def add_comment_range(self, start_line: int, start_col: int, end_line: int, end_col: int):
        """Track a comment range to avoid overlapping tokens."""
        self.comment_ranges.append((start_line, start_col, end_line, end_col))
    
    # ========================================================================
    # BLOCK TRACKING - Now using BlockTracker! 🚀
    # ========================================================================
    
    def enter_block(self, block_type: str, indent: int, line: int, data: Optional[str] = None):
        """Enter a new block context (delegates to BlockTracker)."""
        self.block_tracker.enter_block(block_type, indent, line, data)
    
    def enter_block_single(self, block_type: str, indent: int, line: int):
        """Enter a single-instance block (ZNAVBAR, zMeta) - delegates to BlockTracker."""
        self.block_tracker.enter_block_single(block_type, indent, line)
    
    def update_blocks(self, current_indent: int, current_line: int):
        """Update all block contexts based on indentation - delegates to BlockTracker."""
        self.block_tracker.update_blocks(current_indent, current_line)
    
    def is_inside_block(self, block_type: str, current_indent: int) -> bool:
        """Check if inside a block - delegates to BlockTracker."""
        return self.block_tracker.is_inside(block_type, current_indent)
    
    def is_first_level_in_block(self, block_type: str, current_indent: int) -> bool:
        """Check if at first nesting level under a block - delegates to BlockTracker."""
        return self.block_tracker.is_first_level(block_type, current_indent)
    
    def is_at_depth_in_block(self, block_type: str, current_indent: int, min_depth: int = 1) -> bool:
        """Check if at specific depth in a block - delegates to BlockTracker."""
        return self.block_tracker.is_at_depth(block_type, current_indent, min_depth)
    
    def get_block_data(self, block_type: str) -> Optional[str]:
        """Get additional data from a block - delegates to BlockTracker."""
        return self.block_tracker.get_block_data(block_type)
    
    # Compatibility methods for legacy code patterns
    def enter_zrbac_block(self, indent: int, line: int):
        """Legacy: Enter zRBAC block."""
        self.enter_block('zRBAC', indent, line)
    
    def update_zrbac_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update zRBAC blocks."""
        self.update_blocks(current_indent, current_line)
    
    def is_in_zrbac_block(self, current_indent: int) -> bool:
        """Legacy: Check if in zRBAC block."""
        return self.is_inside_block('zRBAC', current_indent)
    
    def enter_zimage_block(self, indent: int, line: int):
        """Legacy: Enter zImage block."""
        self.enter_block('zImage', indent, line)
    
    def update_zimage_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update zImage blocks."""
        self.update_blocks(current_indent, current_line)
    
    def is_in_zimage_block(self, current_indent: int) -> bool:
        """Legacy: Check if in zImage block."""
        return self.is_inside_block('zImage', current_indent)
    
    def enter_ztext_block(self, indent: int, line: int):
        """Legacy: Enter zText block."""
        self.enter_block('zText', indent, line)
    
    def update_ztext_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update zText blocks."""
        self.update_blocks(current_indent, current_line)
    
    def is_in_ztext_block(self, current_indent: int) -> bool:
        """Legacy: Check if in zText block."""
        return self.is_inside_block('zText', current_indent)
    
    def enter_zmd_block(self, indent: int, line: int):
        """Legacy: Enter zMD block."""
        self.enter_block('zMD', indent, line)
    
    def update_zmd_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update zMD blocks."""
        self.update_blocks(current_indent, current_line)
    
    def is_in_zmd_block(self, current_indent: int) -> bool:
        """Legacy: Check if in zMD block."""
        return self.is_inside_block('zMD', current_indent)
    
    def enter_zurl_block(self, indent: int, line: int):
        """Legacy: Enter zURL block."""
        self.enter_block('zURL', indent, line)
    
    def update_zurl_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update zURL blocks."""
        self.update_blocks(current_indent, current_line)
    
    def is_in_zurl_block(self, current_indent: int) -> bool:
        """Legacy: Check if in zURL block."""
        return self.is_inside_block('zURL', current_indent)
    
    def enter_header_block(self, indent: int, line: int):
        """Legacy: Enter header block (zH1-zH6)."""
        self.enter_block('header', indent, line)
    
    def update_header_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update header blocks."""
        self.update_blocks(current_indent, current_line)
    
    def is_in_header_block(self, current_indent: int) -> bool:
        """Legacy: Check if in header block."""
        return self.is_inside_block('header', current_indent)
    
    def enter_plural_shorthand_block(self, indent: int, line: int, shorthand_name: str):
        """Legacy: Enter plural shorthand block (zURLs, zTexts, etc.)."""
        self.enter_block('plural_shorthand', indent, line, data=shorthand_name)
    
    def update_plural_shorthand_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update plural shorthand blocks."""
        self.update_blocks(current_indent, current_line)
    
    def get_plural_shorthand_context(self, current_indent: int) -> Optional[str]:
        """Get plural shorthand name if at option level (2+ levels deep)."""
        # Check if we're 2+ levels deeper than the shorthand block
        if self.is_at_depth_in_block('plural_shorthand', current_indent, min_depth=3):
            return self.get_block_data('plural_shorthand')
        return None
    
    def enter_zmachine_block(self, indent: int, line: int):
        """Legacy: Enter zMachine block."""
        self.enter_block('zMachine', indent, line)
    
    def update_zmachine_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update zMachine blocks."""
        self.update_blocks(current_indent, current_line)
    
    def is_in_zmachine_block(self, current_indent: int) -> bool:
        """Legacy: Check if in zMachine block."""
        return self.is_inside_block('zMachine', current_indent)
    
    def enter_znavbar_block(self, indent: int, line: int):
        """Enter ZNAVBAR block (single instance)."""
        self.enter_block_single('ZNAVBAR', indent, line)
    
    def update_znavbar_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update znavbar blocks."""
        self.update_blocks(current_indent, current_line)
    
    def is_znavbar_first_level(self, current_indent: int) -> bool:
        """Check if at first nesting level under ZNAVBAR (not grandchildren)."""
        return self.is_first_level_in_block('ZNAVBAR', current_indent)
    
    def enter_zmeta_block(self, indent: int, line: int):
        """Enter zMeta block (single instance)."""
        self.enter_block_single('zMeta', indent, line)
    
    def update_zmeta_blocks(self, current_indent: int, current_line: int):
        """Legacy: Update zmeta blocks."""
        self.update_blocks(current_indent, current_line)
    
    def is_inside_zmeta(self, current_indent: int) -> bool:
        """Check if at first nesting level under zMeta (not deeper)."""
        return self.is_first_level_in_block('zMeta', current_indent)
    
    # ========================================================================
    # KEY MODIFIER HANDLING
    # ========================================================================
    
    def split_modifiers(self, key: str) -> tuple:
        """
        Split key into prefix modifiers, core name, and suffix modifiers.
        
        Dispatcher modifiers in zUI.*.zolo, zEnv.*.zolo, and zSpark.*.zolo files:
        - PREFIX: ^ (bounce), ~ (anchor)
        - SUFFIX: * (menu), ! (required)
        
        Args:
            key: Full key string (may include modifiers)
        
        Returns:
            Tuple of (prefix_modifiers: str, core_key: str, suffix_modifiers: str)
        
        Example:
            ^logout → ("^", "logout", "")
            ~ZNAVBAR* → ("~", "ZNAVBAR", "*")
            menu*! → ("", "menu", "*!")
        """
        # Only split modifiers in zUI, zEnv, and zSpark files
        if not (self.is_zui_file or self.is_zenv_file or self.is_zspark_file):
            return ("", key, "")
        
        # Define modifier characters
        PREFIX_MODIFIERS = {'^', '~'}
        SUFFIX_MODIFIERS = {'*', '!'}
        
        core_key = key
        prefix_mods = ""
        suffix_mods = ""
        
        # Extract prefix modifiers
        while core_key and core_key[0] in PREFIX_MODIFIERS:
            prefix_mods += core_key[0]
            core_key = core_key[1:]
        
        # Extract suffix modifiers
        while core_key and core_key[-1] in SUFFIX_MODIFIERS:
            suffix_mods = core_key[-1] + suffix_mods  # Prepend to maintain order
            core_key = core_key[:-1]
        
        return (prefix_mods, core_key, suffix_mods)
    
    # ========================================================================
    # TOKEN EMISSION
    # ========================================================================
    
    def emit_zpath_tokens(self, value: str, line: int, start_pos: int):
        """
        Emit semantic token for zPath syntax.
        
        zPath format: @.static.brand.logo.png or ~.config.theme
        The entire zPath is colored with a single semantic token (cyan: ZPATH_VALUE)
        
        Args:
            value: The zPath string (e.g., "@.static.brand.logo.png")
            line: Line number
            start_pos: Starting character position
        """
        if not value:
            return
        
        # Emit the entire zPath value as a single token
        self.emit(line, start_pos, len(value), TokenType.ZPATH_VALUE)
    
    def _overlaps_comment(self, line: int, start: int, end: int) -> bool:
        """Check if a position range overlaps with any comment."""
        for c_start_line, c_start_col, c_end_line, c_end_col in self.comment_ranges:
            if line == c_start_line == c_end_line:
                # Same line comment
                if not (end <= c_start_col or start >= c_end_col):
                    return True
            elif line == c_start_line:
                # Token on comment start line
                if start < c_start_col:
                    continue  # Token is before comment
                return True  # Token starts in or after comment start
            elif c_start_line < line < c_end_line:
                # Token is on a middle line of multi-line comment
                return True
            elif line == c_end_line:
                # Token on comment end line
                if end > c_end_col:
                    continue  # Token is after comment
                return True  # Token ends in or before comment end
        return False
    
    def emit(self, line: int, start_char: int, length: int, token_type: TokenType):
        """
        Emit a semantic token with UTF-16 position conversion.
        
        Args:
            line: Line number (0-based)
            start_char: Character offset in Python string (NOT UTF-16)
            length: Length in Python characters (NOT UTF-16)
            token_type: Token type
        """
        if length <= 0:
            return
        
        # Get the line text for UTF-16 conversion
        if line >= len(self.lines):
            return
        line_text = self.lines[line]
        
        # For non-comment tokens, check if they overlap with comments and truncate if needed
        if token_type != TokenType.COMMENT:
            end_char = start_char + length
            
            # Check if this token overlaps any comment
            for c_start_line, c_start_col, c_end_line, c_end_col in self.comment_ranges:
                if line == c_start_line and start_char < c_start_col < end_char:
                    # Token would extend into a comment - truncate it
                    length = c_start_col - start_char
                    end_char = start_char + length
                    if length <= 0:
                        return  # Token is entirely within comment
                    break
        
        # Convert Python character positions to UTF-16 code unit positions
        utf16_start = _char_to_utf16_offset(line_text, start_char)
        utf16_end = _char_to_utf16_offset(line_text, start_char + length)
        
        token = SemanticToken(
            range=Range(
                start=Position(line=line, character=utf16_start),
                end=Position(line=line, character=utf16_end)
            ),
            token_type=token_type
        )
        self.tokens.append(token)
    
    def emit_range(self, start_line: int, start_char: int, end_line: int, end_char: int, token_type: TokenType):
        """
        Emit a token with explicit start and end positions (UTF-16 converted).
        
        Args:
            start_line: Start line number
            start_char: Start character offset in Python string
            end_line: End line number
            end_char: End character offset in Python string
            token_type: Token type
        """
        # Convert positions to UTF-16
        if start_line >= len(self.lines) or end_line >= len(self.lines):
            return
        
        start_line_text = self.lines[start_line]
        end_line_text = self.lines[end_line]
        
        utf16_start = _char_to_utf16_offset(start_line_text, start_char)
        utf16_end = _char_to_utf16_offset(end_line_text, end_char)
        
        token = SemanticToken(
            range=Range(
                start=Position(line=start_line, character=utf16_start),
                end=Position(line=end_line, character=utf16_end)
            ),
            token_type=token_type
        )
        self.tokens.append(token)
    
    def get_tokens(self) -> List[SemanticToken]:
        """Get all emitted tokens, sorted by position."""
        return sorted(self.tokens, key=lambda t: (t.line, t.start_char))
