"""
Zolo Parser

Main parser module with public API (load, loads, dump, dumps, tokenize).
"""

import yaml
import json
from pathlib import Path
from typing import Any, Union, Optional, IO, List, Tuple
import re

from .type_hints import process_type_hints, TYPE_HINT_PATTERN
from .constants import FILE_EXT_ZOLO, FILE_EXT_YAML, FILE_EXT_YML, FILE_EXT_JSON
from ..exceptions import ZoloParseError, ZoloDumpError
from ..lsp_types import SemanticToken, TokenType, Position, Range, ParseResult, Diagnostic


def _char_to_utf16_offset(text: str, char_offset: int) -> int:
    """
    Convert a Python character offset to UTF-16 code unit offset.
    
    VSCode's LSP uses UTF-16 code units for positions, but Python uses characters.
    Multi-byte characters like emojis (🤢) count as 1 in Python but 2 in UTF-16.
    
    Args:
        text: The text string
        char_offset: Character offset (Python string indexing)
    
    Returns:
        UTF-16 code unit offset (for LSP)
    """
    # Get the substring up to the character offset
    substring = text[:char_offset]
    # Encode to UTF-16 and count code units (each unit is 2 bytes, skip BOM)
    utf16_bytes = substring.encode('utf-16-le')
    return len(utf16_bytes) // 2


class TokenEmitter:
    """Helper class to track positions and emit semantic tokens during parsing."""
    
    def __init__(self, content: str, filename: Optional[str] = None):
        self.content = content
        self.lines = content.splitlines(keepends=False)  # Keep lines for UTF-16 conversion
        self.tokens: List[SemanticToken] = []
        self.diagnostics: List['Diagnostic'] = []  # Validation errors and warnings
        self.comment_ranges: List[Tuple[int, int, int, int]] = []  # [(start_line, start_col, end_line, end_col), ...]
        self.filename = filename
        self.is_zui_file = filename and Path(filename).name.startswith('zUI.') if filename else False
        self.is_zenv_file = filename and Path(filename).name.startswith('zEnv.') if filename else False
        self.is_zspark_file = filename and Path(filename).name.startswith('zSpark.') if filename else False
        self.is_zconfig_file = filename and Path(filename).name.startswith('zConfig.') if filename else False
        
        # Extract component name from zUI files (e.g., "zVaF" from "zUI.zVaF.zolo")
        self.zui_component_name = None
        if self.is_zui_file and filename:
            name = Path(filename).stem  # "zUI.zVaF"
            if name.startswith('zUI.'):
                self.zui_component_name = name[4:]  # Extract "zVaF"
        
        # Extract component name from zSpark files (e.g., "zCloud" from "zSpark.zCloud.zolo")
        self.zspark_component_name = None
        if self.is_zspark_file and filename:
            name = Path(filename).stem  # "zSpark.zCloud"
            if name.startswith('zSpark.'):
                self.zspark_component_name = name[7:]  # Extract "zCloud"
        
        # Extract component name from zConfig files (e.g., "machine" from "zConfig.machine.zolo")
        self.zconfig_component_name = None
        if self.is_zconfig_file and filename:
            name = Path(filename).stem  # "zConfig.machine"
            if name.startswith('zConfig.'):
                self.zconfig_component_name = name[8:]  # Extract "machine"
        
        # Track zRBAC blocks to color nested option keys (zGuest, authenticated, require_role, etc.)
        self.zrbac_blocks: List[Tuple[int, int]] = []  # [(indent_level, line_number), ...]
        
        # Track zImage blocks to color nested option keys (src, alt_text, caption, etc.)
        self.zimage_blocks: List[Tuple[int, int]] = []  # [(indent_level, line_number), ...]
        
        # Track zText blocks to color nested option keys (content, indent, etc.)
        self.ztext_blocks: List[Tuple[int, int]] = []  # [(indent_level, line_number), ...]
        
        # Track zMD blocks to color nested option keys (content, indent, pause, etc.)
        self.zmd_blocks: List[Tuple[int, int]] = []  # [(indent_level, line_number), ...]
        
        # Track zURL blocks to color nested option keys (label, href, target, etc.)
        self.zurl_blocks: List[Tuple[int, int]] = []  # [(indent_level, line_number), ...]
        
        # Track header blocks (zH1-zH6) to color nested option keys (label, color, style, etc.)
        self.header_blocks: List[Tuple[int, int]] = []  # [(indent_level, line_number), ...]
        
        # Track plural shorthand blocks to color nested option keys 2+ levels deep
        # (zURLs, zTexts, zImages, etc. with user-defined item keys in between)
        self.plural_shorthand_blocks: List[Tuple[int, int, str]] = []  # [(indent_level, line_number, shorthand_name), ...]
        
        # Track zMachine blocks to color nested section keys (user_preferences, cpu, etc.)
        self.zmachine_blocks: List[Tuple[int, int]] = []  # [(indent_level, line_number), ...]
    
    def add_comment_range(self, start_line: int, start_col: int, end_line: int, end_col: int):
        """Track a comment range to avoid overlapping tokens."""
        self.comment_ranges.append((start_line, start_col, end_line, end_col))
    
    def enter_zrbac_block(self, indent: int, line: int):
        """Mark that we're entering a zRBAC block at the given indentation level."""
        self.zrbac_blocks.append((indent, line))
    
    def update_zrbac_blocks(self, current_indent: int, current_line: int):
        """Update zRBAC block tracking based on current indentation level.
        Exit blocks that have lower or equal indentation than current."""
        # Remove blocks with indent >= current_indent (we've exited them)
        self.zrbac_blocks = [(indent, line) for indent, line in self.zrbac_blocks if indent < current_indent]
    
    def is_in_zrbac_block(self, current_indent: int) -> bool:
        """Check if we're currently inside a zRBAC block at the given indentation level."""
        return any(indent < current_indent for indent, _ in self.zrbac_blocks)
    
    def enter_zimage_block(self, indent: int, line: int):
        """Mark that we're entering a zImage block at the given indentation level."""
        self.zimage_blocks.append((indent, line))
    
    def update_zimage_blocks(self, current_indent: int, current_line: int):
        """Update zImage block tracking based on current indentation level.
        Exit blocks that have lower or equal indentation than current."""
        # Remove blocks with indent >= current_indent (we've exited them)
        self.zimage_blocks = [(indent, line) for indent, line in self.zimage_blocks if indent < current_indent]
    
    def is_in_zimage_block(self, current_indent: int) -> bool:
        """Check if we're currently inside a zImage block at the given indentation level."""
        return any(indent < current_indent for indent, _ in self.zimage_blocks)
    
    def enter_ztext_block(self, indent: int, line: int):
        """Mark that we're entering a zText block at the given indentation level."""
        self.ztext_blocks.append((indent, line))
    
    def update_ztext_blocks(self, current_indent: int, current_line: int):
        """Update zText block tracking based on current indentation level.
        Exit blocks that have lower or equal indentation than current."""
        # Remove blocks with indent >= current_indent (we've exited them)
        self.ztext_blocks = [(indent, line) for indent, line in self.ztext_blocks if indent < current_indent]
    
    def is_in_ztext_block(self, current_indent: int) -> bool:
        """Check if we're currently inside a zText block at the given indentation level."""
        return any(indent < current_indent for indent, _ in self.ztext_blocks)
    
    def enter_zmd_block(self, indent: int, line: int):
        """Mark that we're entering a zMD block at the given indentation level."""
        self.zmd_blocks.append((indent, line))
    
    def update_zmd_blocks(self, current_indent: int, current_line: int):
        """Update zMD block tracking based on current indentation level.
        Exit blocks that have lower or equal indentation than current."""
        # Remove blocks with indent >= current_indent (we've exited them)
        self.zmd_blocks = [(indent, line) for indent, line in self.zmd_blocks if indent < current_indent]
    
    def is_in_zmd_block(self, current_indent: int) -> bool:
        """Check if we're currently inside a zMD block at the given indentation level."""
        return any(indent < current_indent for indent, _ in self.zmd_blocks)
    
    def enter_zurl_block(self, indent: int, line: int):
        """Mark that we're entering a zURL block at the given indentation level."""
        self.zurl_blocks.append((indent, line))
    
    def update_zurl_blocks(self, current_indent: int, current_line: int):
        """Update zURL block tracking based on current indentation level.
        Exit blocks that have lower or equal indentation than current."""
        # Remove blocks with indent >= current_indent (we've exited them)
        self.zurl_blocks = [(indent, line) for indent, line in self.zurl_blocks if indent < current_indent]
    
    def is_in_zurl_block(self, current_indent: int) -> bool:
        """Check if we're currently inside a zURL block at the given indentation level."""
        return any(indent < current_indent for indent, _ in self.zurl_blocks)
    
    def enter_header_block(self, indent: int, line: int):
        """Mark that we're entering a header block (zH1-zH6) at the given indentation level."""
        self.header_blocks.append((indent, line))
    
    def update_header_blocks(self, current_indent: int, current_line: int):
        """Update header block tracking based on current indentation level.
        Exit blocks that have lower or equal indentation than current."""
        # Remove blocks with indent >= current_indent (we've exited them)
        self.header_blocks = [(indent, line) for indent, line in self.header_blocks if indent < current_indent]
    
    def is_in_header_block(self, current_indent: int) -> bool:
        """Check if we're currently inside a header block (zH1-zH6) at the given indentation level."""
        return any(indent < current_indent for indent, _ in self.header_blocks)
    
    def enter_plural_shorthand_block(self, indent: int, line: int, shorthand_name: str):
        """Mark that we're entering a plural shorthand block (zURLs, zTexts, etc.)."""
        self.plural_shorthand_blocks.append((indent, line, shorthand_name))
    
    def update_plural_shorthand_blocks(self, current_indent: int, current_line: int):
        """Update plural shorthand block tracking based on current indentation level.
        Exit blocks that have lower or equal indentation than current."""
        # Remove blocks with indent >= current_indent (we've exited them)
        self.plural_shorthand_blocks = [
            (indent, line, name) 
            for indent, line, name in self.plural_shorthand_blocks 
            if indent < current_indent
        ]
    
    def get_plural_shorthand_context(self, current_indent: int) -> Optional[str]:
        """Get the plural shorthand name if we're 2+ levels deep inside one.
        
        Structure:
            zUL:              # indent 2
              zURLs:          # indent 4 (shorthand)
                github_cli:   # indent 6 (user item key)
                  label: ...  # indent 8 (option) <- We color these purple
        
        Returns:
            Shorthand name (e.g., 'zURLs') if we're at option level, None otherwise
        """
        for shorthand_indent, _, shorthand_name in self.plural_shorthand_blocks:
            # We want keys that are 2+ levels deeper than the shorthand
            # (past the user-defined item key like 'github_cli')
            if current_indent > shorthand_indent + 2:
                return shorthand_name
        return None
    
    def enter_zmachine_block(self, indent: int, line: int):
        """Mark that we're entering a zMachine block at the given indentation level."""
        self.zmachine_blocks.append((indent, line))
    
    def update_zmachine_blocks(self, current_indent: int, current_line: int):
        """Update zMachine block tracking based on current indentation level.
        Exit blocks that have lower or equal indentation than current."""
        # Remove blocks with indent >= current_indent (we've exited them)
        self.zmachine_blocks = [(indent, line) for indent, line in self.zmachine_blocks if indent < current_indent]
    
    def is_in_zmachine_block(self, current_indent: int) -> bool:
        """Check if we're currently inside a zMachine block at the given indentation level."""
        return any(indent < current_indent for indent, _ in self.zmachine_blocks)
    
    def split_modifiers(self, key: str) -> tuple:
        """Split key into prefix modifiers, core name, and suffix modifiers.
        
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
    
    def emit_zpath_tokens(self, value: str, line: int, start_pos: int):
        """Emit semantic token for zPath syntax.
        
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
        """Get all emitted tokens."""
        return sorted(self.tokens, key=lambda t: (t.line, t.start_char))


def tokenize(content: str, filename: Optional[str] = None) -> ParseResult:
    """
    Parse .zolo content and return both parsed data and semantic tokens for LSP.
    
    This is the primary entry point for the Language Server Protocol to get
    semantic highlighting information along with parsed data.
    
    Args:
        content: Raw .zolo file content
        filename: Optional filename for context-aware tokenization (e.g., zUI files)
    
    Returns:
        ParseResult with data, tokens, and any errors
    
    Examples:
        >>> result = tokenize("port: 8080\\nhost: localhost")
        >>> result.data
        {'port': 8080.0, 'host': 'localhost'}
        >>> result.tokens
        [SemanticToken(...), SemanticToken(...), ...]
    """
    emitter = TokenEmitter(content, filename=filename)
    errors = []
    
    try:
        # Parse with token emission
        data = _parse_zolo_content_with_tokens(content, emitter)
        return ParseResult(data=data, tokens=emitter.get_tokens(), errors=errors, diagnostics=emitter.diagnostics)
    except ZoloParseError as e:
        # Still return tokens even if parse failed
        errors.append(str(e))
        return ParseResult(data=None, tokens=emitter.get_tokens(), errors=errors, diagnostics=emitter.diagnostics)


def load(fp: Union[str, Path, IO], file_extension: Optional[str] = None) -> Any:
    """
    Load data from a .zolo file (or compatible format).
    
    Args:
        fp: File path (str/Path) or file-like object
        file_extension: Optional file extension override (.zolo, .yaml, .json)
                       If None, will detect from file path or default to .zolo
    
    Returns:
        Parsed data (dict, list, or scalar)
    
    Raises:
        ZoloParseError: If parsing fails
        FileNotFoundError: If file doesn't exist
    
    Examples:
        >>> # Load .zolo file (string-first)
        >>> data = zolo.load('config.zolo')
        
        >>> # Load .yaml file (native types)
        >>> data = zolo.load('config.yaml')
        
        >>> # Load with explicit extension
        >>> data = zolo.load('config.txt', file_extension='.zolo')
    """
    # Handle file path vs file-like object
    if isinstance(fp, (str, Path)):
        file_path = Path(fp)
        
        # Detect file extension if not provided
        if file_extension is None:
            file_extension = file_path.suffix.lower()
            if not file_extension:
                file_extension = FILE_EXT_ZOLO  # Default to .zolo
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise ZoloParseError(f"Error reading file {file_path}: {e}") from e
    else:
        # File-like object
        try:
            content = fp.read()
        except Exception as e:
            raise ZoloParseError(f"Error reading from file object: {e}") from e
        
        # Try to detect extension from file name
        if file_extension is None and hasattr(fp, 'name'):
            file_extension = Path(fp.name).suffix.lower()
        if not file_extension:
            file_extension = FILE_EXT_ZOLO  # Default to .zolo
    
    # Parse content
    return loads(content, file_extension=file_extension)


def loads(s: str, file_extension: Optional[str] = None) -> Any:
    """
    Load data from a .zolo string (or compatible format).
    
    Args:
        s: String content to parse
        file_extension: Optional file extension hint (.zolo, .yaml, .json)
                       Defaults to .zolo if not provided
    
    Returns:
        Parsed data (dict, list, or scalar)
    
    Raises:
        ZoloParseError: If parsing fails
    
    Examples:
        >>> # Parse .zolo string (string-first)
        >>> data = zolo.loads('port: 8080')
        {'port': '8080'}  # String by default
        
        >>> # Parse with type hint
        >>> data = zolo.loads('port(int): 8080')
        {'port': 8080}  # Integer via type hint
        
        >>> # Parse .yaml string (native types)
        >>> data = zolo.loads('port: 8080', file_extension='.yaml')
        {'port': 8080}  # Integer via YAML
    """
    if not s or not s.strip():
        return None
    
    # Default to .zolo if not specified
    if file_extension is None:
        file_extension = FILE_EXT_ZOLO
    
    # Normalize extension
    file_extension = file_extension.lower()
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension
    
    # Determine if string-first should be applied
    # .zolo files now use RFC 8259 type detection (like JSON)
    # string_first = False means: respect native types (int, float, bool, null)
    # Only YAML files (.yaml/.yml) would use string_first if we wanted that
    string_first = False
    
    # Parse based on format
    try:
        if file_extension == FILE_EXT_JSON:
            # Parse as JSON
            parsed = json.loads(s)
        elif file_extension == FILE_EXT_ZOLO:
            # Custom .zolo parser (no YAML quirks)
            # TODO: Implement custom parsing logic
            parsed = _parse_zolo_content(s)
        else:
            # Parse as YAML (for .yaml, .yml files)
            parsed = yaml.safe_load(s)
        
        # Process type hints
        parsed = process_type_hints(parsed, string_first=string_first)
        
        return parsed
    
    except yaml.YAMLError as e:
        raise ZoloParseError(f"YAML parsing error: {e}") from e
    except json.JSONDecodeError as e:
        raise ZoloParseError(f"JSON parsing error: {e}") from e
    except Exception as e:
        raise ZoloParseError(f"Parsing error: {e}") from e


def _parse_zolo_content(content: str) -> Any:
    """
    Custom .zolo parser without YAML quirks.
    
    Implementation follows ZOLO_PARSER_IMPLEMENTATION_PLAN.md
    Current: Phase 1-2 Complete (Comments, Types, Arrays, Nested Objects)
    """
    # Step 1.1: Strip comments and prepare lines
    lines, line_mapping = _strip_comments_and_prepare_lines(content)
    
    # Step 4.8: Check indentation consistency (Python-style)
    _check_indentation_consistency(lines)
    
    # Step 2.3: Parse with nested object support
    result = _parse_lines(lines, line_mapping)
    
    return result


def _parse_zolo_content_with_tokens(content: str, emitter: TokenEmitter) -> Any:
    """
    Custom .zolo parser with token emission for LSP.
    
    This version tracks positions and emits semantic tokens during parsing.
    """
    # Step 1: Strip comments and prepare lines (with token emission)
    lines, line_mapping = _strip_comments_and_prepare_lines_with_tokens(content, emitter)
    
    # Step 2: Check indentation consistency
    _check_indentation_consistency(lines)
    
    # Step 3: Parse with token emission
    result = _parse_lines_with_tokens(lines, line_mapping, emitter)
    
    return result


def _check_indentation_consistency(lines: list[str]) -> None:
    """
    Check that indentation is consistent (Python-style).
    
    Allows either tabs OR spaces for indentation, but forbids mixing.
    This is superior to YAML's arbitrary "spaces only" rule because:
    - Tabs are semantic (1 tab = 1 level)
    - Spaces are flexible (user choice)
    - Mixing is chaos (forbidden!)
    
    Args:
        lines: List of lines to check
    
    Raises:
        ZoloParseError: If tabs and spaces are mixed in indentation
    
    Philosophy:
        Like Python, .zolo cares about CONSISTENCY, not character type.
        Choose tabs (semantic) OR spaces (traditional), but be consistent!
    """
    first_indent_type = None  # 'tab' or 'space'
    first_indent_line = None
    
    for line_num, line in enumerate(lines, 1):
        # Skip empty lines and lines with no indentation
        if not line.strip():
            continue
        
        # Get indentation characters
        stripped = line.lstrip()
        if len(stripped) == len(line):
            # No indentation
            continue
        
        indent_chars = line[:len(line) - len(stripped)]
        
        # Check what this line uses
        has_tab = '\t' in indent_chars
        has_space = ' ' in indent_chars
        
        # ERROR: Mixed tabs and spaces in SAME line
        if has_tab and has_space:
            raise ZoloParseError(
                f"Mixed tabs and spaces in indentation at line {line_num}.\n"
                f"Use either tabs OR spaces consistently (Python convention).\n"
                f"Hint: Configure your editor to use one type of indentation."
            )
        
        # Determine this line's indent type
        current_type = 'tab' if has_tab else 'space'
        
        # Track first indent type seen in file
        if first_indent_type is None:
            first_indent_type = current_type
            first_indent_line = line_num
        # ERROR: Different type than rest of file
        elif first_indent_type != current_type:
            indent_word = 'tabs' if first_indent_type == 'tab' else 'spaces'
            current_word = 'tabs' if current_type == 'tab' else 'spaces'
            raise ZoloParseError(
                f"Inconsistent indentation at line {line_num}.\n"
                f"File uses {indent_word} (first seen at line {first_indent_line}),\n"
                f"but this line uses {current_word}.\n"
                f"Use either tabs OR spaces consistently (Python convention)."
            )


def _strip_comments_and_prepare_lines(content: str) -> Tuple[list[str], dict]:
    """
    Phase 1, Step 1.1: Strip comments from .zolo content.
    
    Rules:
    - Full-line comments: # at line start (after optional whitespace at any indent level)
    - Inline comments: #> ... <# (paired delimiters)
    - Multi-line comments supported with #> ... <#
    - Unpaired #> or <# are treated as literal text
    - # without > is a literal character (hex colors, hashtags, etc.)
    - Skip empty lines after comment removal
    - Preserve indentation
    
    Args:
        content: Raw .zolo file content
    
    Returns:
        Tuple of (cleaned_lines, line_mapping)
        - cleaned_lines: List of cleaned lines (no comments, no empty lines)
        - line_mapping: Dict mapping cleaned line index to original line number (1-based)
    
    Examples:
        >>> lines, mapping = _strip_comments_and_prepare_lines("# Full line comment\\nkey: value")
        >>> lines
        ['key: value']
        >>> mapping[0]
        2
        
        >>> lines, mapping = _strip_comments_and_prepare_lines("section:\\n    # Indented comment\\n    key: value")
        >>> lines
        ['section:', '    key: value']
        
        >>> lines, mapping = _strip_comments_and_prepare_lines("key: value #> comment <#")
        >>> lines
        ['key: value']
        
        >>> lines, mapping = _strip_comments_and_prepare_lines("color: #fffcbf #> nice <#")
        >>> lines
        ['color: #fffcbf']
        
        >>> lines, mapping = _strip_comments_and_prepare_lines("tag: #python")
        >>> lines
        ['tag: #python']
    """
    lines = content.splitlines()
    
    # Phase 1: Identify full-line comments
    full_line_comment_lines = set()
    for line_num, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith('#') and not stripped.startswith('#>'):
            full_line_comment_lines.add(line_num)
    
    # Phase 2: Find all #> ... <# comments (including multi-line)
    comment_line_ranges = []  # Store (start_line, start_col, end_line, end_col) tuples
    
    search_pos = 0
    while search_pos < len(content):
        # Find opening #>
        start = content.find('#>', search_pos)
        if start == -1:
            break  # No more arrow comments
        
        # Check if this #> is within a full-line comment
        start_line = content[:start].count('\n')
        if start_line in full_line_comment_lines:
            # Skip this #>, it's inside a full-line comment
            search_pos = start + 2
            continue
        
        # Find matching closing <#
        end = content.find('<#', start + 2)
        if end == -1:
            # No matching <# found, skip this #>
            search_pos = start + 2
            continue
        
        # Store this comment range (from #> to <# inclusive)
        start_col = start - content.rfind('\n', 0, start) - 1
        end_line = content[:end + 2].count('\n')
        end_col = end + 2 - content.rfind('\n', 0, end + 2) - 1
        
        comment_line_ranges.append((start_line, start_col, end_line, end_col))
        search_pos = end + 2
    
    # Phase 3: Build cleaned lines (remove comments, skip full-line comments)
    cleaned_lines = []
    line_mapping = {}  # Maps cleaned index -> original line number (1-based)
    
    for line_num, line in enumerate(lines):
        # Skip full-line comments
        if line_num in full_line_comment_lines:
            continue
        
        # Remove inline comments from this line
        working_line = line
        for c_start_line, c_start_col, c_end_line, c_end_col in comment_line_ranges:
            if c_start_line == c_end_line == line_num:
                # Single-line comment on this line
                working_line = working_line[:c_start_col] + working_line[c_end_col:]
            elif c_start_line == line_num:
                # This line starts a multi-line comment - remove from comment start to end of line
                working_line = working_line[:c_start_col]
            elif c_start_line < line_num < c_end_line:
                # This line is in the middle of a multi-line comment - skip it entirely
                working_line = ""
                break
            elif c_end_line == line_num:
                # This line ends a multi-line comment - keep text after <#
                working_line = working_line[c_end_col:]
        
        # Strip trailing whitespace (but preserve leading indentation)
        working_line = working_line.rstrip()
        
        # Skip empty lines
        if working_line:
            line_mapping[len(cleaned_lines)] = line_num + 1  # 1-based line numbers
            cleaned_lines.append(working_line)
    
    return cleaned_lines, line_mapping


def _strip_comments_and_prepare_lines_with_tokens(content: str, emitter: TokenEmitter) -> Tuple[list[str], dict]:
    """
    Strip comments and prepare lines while emitting comment tokens.
    Handles both full-line comments and multi-line #> ... <# comments.
    
    Returns:
        Tuple of (cleaned_lines, line_mapping)
        line_mapping maps cleaned line index to original line number
    """
    lines = content.splitlines()
    
    # Phase 1: Identify full-line comments (these should be ignored for inline comment processing)
    # Full-line comments can appear at any indentation level
    # A line is a full-line comment if it starts with # (after optional whitespace) but not #>
    full_line_comment_lines = set()
    for line_num, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        # A line is a full-line comment if it starts with # (but not #>)
        if stripped.startswith('#') and not stripped.startswith('#>'):
            full_line_comment_lines.add(line_num)
            # Emit token for this full-line comment (starting from first # character to end of line)
            # Use the full line length (minus any trailing newline) to ensure we cover everything
            comment_length = len(line) - indent  # From first # to end of line
            emitter.emit(line_num, indent, comment_length, TokenType.COMMENT)
            # Track this comment range to prevent other tokens from overlapping
            emitter.add_comment_range(line_num, indent, line_num, len(line))
    
    # Phase 2: Find and emit all #> ... <# comments (including multi-line)
    # Only search in content that's NOT part of full-line comments
    comment_char_ranges = []  # Store (char_start, char_end) tuples in original content
    comment_line_ranges = []  # Store (start_line, start_col, end_line, end_col) tuples
    
    search_pos = 0
    while search_pos < len(content):
        # Find opening #>
        start = content.find('#>', search_pos)
        if start == -1:
            break  # No more arrow comments
        
        # Check if this #> is within a full-line comment
        start_line = content[:start].count('\n')
        if start_line in full_line_comment_lines:
            # Skip this #>, it's inside a full-line comment
            search_pos = start + 2
            continue
        
        # Find matching closing <#
        end = content.find('<#', start + 2)
        if end == -1:
            # No matching <# found, skip this #>
            search_pos = start + 2
            continue
        
        # Store this comment range (from #> to <# inclusive)
        comment_char_ranges.append((start, end + 2))
        search_pos = end + 2
    
    # Emit comment tokens for all found ranges
    for char_start, char_end in comment_char_ranges:
        # Convert absolute character positions to line/column
        start_line = content[:char_start].count('\n')
        start_col = char_start - content.rfind('\n', 0, char_start) - 1
        
        end_line = content[:char_end].count('\n')
        end_col = char_end - content.rfind('\n', 0, char_end) - 1
        
        # Track this comment range to avoid overlapping tokens
        emitter.add_comment_range(start_line, start_col, end_line, end_col)
        comment_line_ranges.append((start_line, start_col, end_line, end_col))
        
        if start_line == end_line:
            # Single-line comment
            emitter.emit(start_line, start_col, char_end - char_start, TokenType.COMMENT)
            
            # Check if there's text after <# on the same line - emit as STRING
            line_text = lines[start_line]
            text_after = line_text[end_col:].strip()
            if text_after:
                # Find where the non-whitespace text starts
                after_start = end_col
                while after_start < len(line_text) and line_text[after_start].isspace():
                    after_start += 1
                if after_start < len(line_text):
                    emitter.emit(start_line, after_start, len(line_text) - after_start, TokenType.STRING)
        else:
            # Multi-line comment - emit separate tokens for each line
            # This is more compatible with LSP's semantic token format
            lines_in_comment = content[char_start:char_end].splitlines(keepends=False)
            current_line = start_line
            
            for i, line_text in enumerate(lines_in_comment):
                if i == 0:
                    # First line: from start_col to end of line
                    emitter.emit(current_line, start_col, len(lines[current_line]) - start_col, TokenType.COMMENT)
                elif i == len(lines_in_comment) - 1:
                    # Last line: from start of line to end_col
                    # Get the indentation of this line
                    actual_line = lines[current_line]
                    indent = len(actual_line) - len(actual_line.lstrip())
                    emitter.emit(current_line, indent, end_col - indent, TokenType.COMMENT)
                    
                    # Check if there's text after <# on the last line - emit as STRING
                    text_after = actual_line[end_col:].strip()
                    if text_after:
                        # Find where the non-whitespace text starts
                        after_start = end_col
                        while after_start < len(actual_line) and actual_line[after_start].isspace():
                            after_start += 1
                        if after_start < len(actual_line):
                            emitter.emit(current_line, after_start, len(actual_line) - after_start, TokenType.STRING)
                else:
                    # Middle lines: entire line is comment
                    actual_line = lines[current_line]
                    indent = len(actual_line) - len(actual_line.lstrip())
                    emitter.emit(current_line, indent, len(actual_line) - indent, TokenType.COMMENT)
                current_line += 1
    
    # Phase 3: Build cleaned lines (remove comments, skip full-line comments)
    cleaned_lines = []
    line_mapping = {}  # Maps cleaned index -> original line number
    pending_append = None  # Store text to append to previous cleaned line
    
    # Process each original line individually
    for line_num, line in enumerate(lines):
        # Skip full-line comments
        if line_num in full_line_comment_lines:
            continue
        
        # Remove inline comments from this line
        working_line = line
        for c_start_line, c_start_col, c_end_line, c_end_col in comment_line_ranges:
            if c_start_line == c_end_line == line_num:
                # Single-line comment on this line
                working_line = working_line[:c_start_col] + working_line[c_end_col:]
            elif c_start_line == line_num:
                # This line starts a multi-line comment - remove from comment start to end of line
                working_line = working_line[:c_start_col]
            elif c_start_line < line_num < c_end_line:
                # This line is in the middle of a multi-line comment - skip it entirely
                working_line = ""
                break
            elif c_end_line == line_num:
                # This line ends a multi-line comment - keep text after <#
                text_after = working_line[c_end_col:].strip()
                if text_after:
                    # Append this text to the line that started the comment
                    pending_append = text_after
                working_line = ""
                break
        
        # Handle pending append
        if pending_append and cleaned_lines:
            cleaned_lines[-1] += " " + pending_append
            pending_append = None
        
        # Strip trailing whitespace
        working_line = working_line.rstrip()
        
        # Skip empty lines
        if working_line:
            line_mapping[len(cleaned_lines)] = line_num
            cleaned_lines.append(working_line)
    
    return cleaned_lines, line_mapping


def _parse_lines_with_tokens(lines: list[str], line_mapping: dict, emitter: TokenEmitter) -> dict:
    r"""
    Parse lines with token emission for LSP.
    
    Similar to _parse_lines() but emits semantic tokens for all syntax elements.
    """
    if not lines:
        return {}
    
    structured_lines = []
    i = 0
    line_number = 0
    
    while i < len(lines):
        line = lines[i]
        original_line_num = line_mapping.get(i, i)
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()
            
            # Find key position in original line
            key_start = line.find(key)
            
            # Emit colon token
            colon_pos = line.find(':', key_start)
            emitter.emit(original_line_num, colon_pos, 1, TokenType.COLON)
            
            # Check for type hint
            match = TYPE_HINT_PATTERN.match(key)
            if match:
                clean_key = match.group(1)
                type_hint = match.group(2)
                
                # Emit root or nested key token
                if indent == 0:
                    # Split modifiers from clean_key (key without type hint)
                    prefix_mods, core_key, suffix_mods = emitter.split_modifiers(clean_key)
                    current_pos = key_start
                    
                    # Emit prefix modifiers (purple)
                    for mod in prefix_mods:
                        emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                    
                    # Determine token type for core key and emit
                    # Special handling for zMeta and component name in zUI files
                    if emitter.is_zui_file and (core_key == 'zMeta' or core_key == emitter.zui_component_name):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMETA_KEY)
                    # Special handling for zSpark root key in zSpark files (LIGHT GREEN - ANSI 114)
                    elif emitter.is_zspark_file and core_key == 'zSpark':
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSPARK_KEY)
                    # Special handling for uppercase Z-prefixed config keys in zEnv files (GREEN)
                    elif emitter.is_zenv_file and core_key.isupper() and core_key.startswith('Z'):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZCONFIG_KEY)
                    # Special handling for z-prefixed root keys in zConfig files (GREEN) - e.g., zMachine
                    elif emitter.is_zconfig_file and core_key.startswith('z') and len(core_key) > 1 and core_key[1].isupper():
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZCONFIG_KEY)
                        # If this is zMachine, enter the block for nested key tracking
                        if core_key == 'zMachine':
                            emitter.enter_zmachine_block(indent, original_line_num)
                    # Check for zSub at root level (ERROR - zSub must always be nested)
                    elif core_key == 'zSub':
                        # zSub at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"'zSub' cannot be at root level. It must be nested under a parent key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                        # Still emit as ROOT_KEY token for highlighting
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    # Check for zRBAC at root level (ERROR - zRBAC must always be nested)
                    elif core_key == 'zRBAC':
                        # zRBAC at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"'zRBAC' cannot be at root level. It must be nested under a parent key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                        # Still emit as ROOT_KEY token for highlighting
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    # Check for z-prefixed UI elements at root level (ERROR in zUI files)
                    elif emitter.is_zui_file and core_key.startswith('z') and core_key[1:2].isupper():
                        # This is a UI element at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"UI element '{core_key}' cannot be at root level. It must be nested under a root key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                        # Still emit as ROOT_KEY token for highlighting
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    else:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    
                    current_pos += len(core_key)
                    
                    # Emit suffix modifiers (purple)
                    for mod in suffix_mods:
                        emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                else:
                    # Update block tracking (exit blocks we've left based on indentation)
                    emitter.update_zrbac_blocks(indent, original_line_num)
                    emitter.update_zimage_blocks(indent, original_line_num)
                    emitter.update_ztext_blocks(indent, original_line_num)
                    emitter.update_zmd_blocks(indent, original_line_num)
                    emitter.update_zurl_blocks(indent, original_line_num)
                    emitter.update_header_blocks(indent, original_line_num)
                    emitter.update_zmachine_blocks(indent, original_line_num)
                    
                    # Split modifiers from clean_key (key without type hint)
                    prefix_mods, core_key, suffix_mods = emitter.split_modifiers(clean_key)
                    current_pos = key_start
                    
                    # Emit prefix modifiers (purple)
                    for mod in prefix_mods:
                        emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                    
                    # Determine token type for core key and emit
                    # Check for zRBAC key (TOMATO in all .zolo files)
                    if core_key == 'zRBAC':
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_KEY)
                        # Mark that we're entering a zRBAC block
                        emitter.enter_zrbac_block(indent, original_line_num)
                    # Check for zSpark nested keys (purple 98 in zSpark files only)
                    elif emitter.is_zspark_file:
                        # ALL nested keys under zSpark root get purple color
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSPARK_NESTED_KEY)
                    # Check for zRBAC option keys (PURPLE in zUI and zEnv files only)
                    elif emitter.is_in_zrbac_block(indent) and (emitter.is_zui_file or emitter.is_zenv_file):
                        ZRBAC_OPTIONS = {'zGuest', 'authenticated', 'require_role', 'require_auth', 'require_permission'}
                        if core_key in ZRBAC_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zMachine nested section keys in zConfig files
                    elif emitter.is_in_zmachine_block(indent) and emitter.is_zconfig_file:
                        # Define editable sections (blue/cyan - INFO level)
                        ZMACHINE_EDITABLE_SECTIONS = {
                            'user_preferences', 'time_date_formatting', 'launch_commands', 'custom'
                        }
                        # Define locked/auto-detected sections (red/orange - ERROR level)
                        ZMACHINE_LOCKED_SECTIONS = {
                            'machine_identity', 'python_runtime', 'cpu', 'memory', 'gpu', 'network', 'user_paths'
                        }
                        
                        if core_key in ZMACHINE_EDITABLE_SECTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMACHINE_EDITABLE_KEY)
                        elif core_key in ZMACHINE_LOCKED_SECTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMACHINE_LOCKED_KEY)
                        else:
                            # Unknown key - default to nested key
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zImage key (GOLD in zUI files) and enter block
                    elif core_key == 'zImage' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zImage block
                        emitter.enter_zimage_block(indent, original_line_num)
                    # Check for zImage option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zimage_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZIMAGE_OPTIONS = {'src', 'alt_text', 'caption', 'open_prompt', 'indent', 'color'}
                        if core_key in ZIMAGE_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zText key (GOLD in zUI files) and enter block
                    elif core_key == 'zText' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zText block
                        emitter.enter_ztext_block(indent, original_line_num)
                    # Check for zText option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_ztext_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZTEXT_OPTIONS = {'content', 'indent', 'color', 'break_after'}
                        if core_key in ZTEXT_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zMD key (GOLD in zUI files) and enter block
                    elif core_key == 'zMD' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zMD block
                        emitter.enter_zmd_block(indent, original_line_num)
                    # Check for zMD option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zmd_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZMD_OPTIONS = {'content', 'indent', 'pause', 'break_message', 'format'}
                        if core_key in ZMD_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zURL key (GOLD in zUI files) and enter block
                    elif core_key == 'zURL' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zURL block
                        emitter.enter_zurl_block(indent, original_line_num)
                    # Check for zURL option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zurl_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZURL_OPTIONS = {'label', 'href', 'target', 'color', 'rel', 'window'}
                        if core_key in ZURL_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zH1-zH6 keys (GOLD in zUI files) and enter block
                    elif core_key in {'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'} and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a header block
                        emitter.enter_header_block(indent, original_line_num)
                    # Check for header option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_header_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        HEADER_OPTIONS = {'label', 'color', 'style', 'semantic', 'indent'}
                        if core_key in HEADER_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for plural shorthand option keys (PURPLE in zUI files, 2+ levels deep, excluding Bifrost)
                    elif not core_key.startswith('_') and emitter.is_zui_file:
                        plural_context = emitter.get_plural_shorthand_context(indent)
                        if plural_context:
                            # Define valid options for each plural shorthand type
                            PLURAL_OPTIONS = {
                                'zURLs': {'label', 'href', 'target', 'rel', 'color', 'window'},
                                'zTexts': {'content', 'indent', 'color'},
                                'zImages': {'src', 'alt_text', 'caption', 'open_prompt', 'indent', 'color'},
                                'zH1s': {'label', 'color', 'indent'},
                                'zH2s': {'label', 'color', 'indent'},
                                'zH3s': {'label', 'color', 'indent'},
                                'zH4s': {'label', 'color', 'indent'},
                                'zH5s': {'label', 'color', 'indent'},
                                'zH6s': {'label', 'color', 'indent'},
                                'zMDs': {'content', 'indent', 'color'},
                            }
                            if plural_context in PLURAL_OPTIONS and core_key in PLURAL_OPTIONS[plural_context]:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                            else:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                        else:
                            # Check if this IS a plural shorthand container itself
                            PLURAL_SHORTHANDS = {'zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 
                                               'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs'}
                            if core_key in PLURAL_SHORTHANDS:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                                emitter.enter_plural_shorthand_block(indent, original_line_num, core_key)
                            # Check for zSub key (GOLD in both zUI and zEnv files)
                            elif core_key == 'zSub':
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                            # Check for specific shorthand display event keys (strict whitelist)
                            elif core_key in {'zNavBar', 'zImage', 'zUL', 'zOL', 'zURL', 'zURLs', 'zText', 'zMD', 'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'}:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                            else:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zSub key (GOLD in both zUI and zEnv files)
                    elif core_key == 'zSub':
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                    # Check for underscore-prefixed keys (Bifrost keys)
                    elif core_key.startswith('_'):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.BIFROST_KEY)
                    # Check for specific shorthand display event keys (strict whitelist)
                    elif emitter.is_zui_file and core_key in {'zNavBar', 'zImage', 'zUL', 'zOL', 'zURL', 'zURLs', 'zText', 'zMD'}:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                    else:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    
                    current_pos += len(core_key)
                    
                    # Emit suffix modifiers (purple)
                    for mod in suffix_mods:
                        emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                
                # Emit type hint token (after modifiers and core key)
                hint_start = key_start + len(clean_key) + 1  # +1 for opening paren
                emitter.emit(original_line_num, hint_start, len(type_hint), TokenType.TYPE_HINT)
                
                has_str_hint = type_hint.lower() == 'str'
            else:
                # No type hint
                if indent == 0:
                    # Split modifiers from key name
                    prefix_mods, core_key, suffix_mods = emitter.split_modifiers(key)
                    current_pos = key_start
                    
                    # Emit prefix modifiers (purple)
                    for mod in prefix_mods:
                        emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                    
                    # Determine token type for core key and emit
                    # Special handling for zMeta and component name in zUI files
                    if emitter.is_zui_file and (core_key == 'zMeta' or core_key == emitter.zui_component_name):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMETA_KEY)
                    # Special handling for zSpark root key in zSpark files (LIGHT GREEN - ANSI 114)
                    elif emitter.is_zspark_file and core_key == 'zSpark':
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSPARK_KEY)
                    # Special handling for uppercase Z-prefixed config keys in zEnv files (GREEN)
                    elif emitter.is_zenv_file and core_key.isupper() and core_key.startswith('Z'):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZCONFIG_KEY)
                    # Special handling for z-prefixed root keys in zConfig files (GREEN) - e.g., zMachine
                    elif emitter.is_zconfig_file and core_key.startswith('z') and len(core_key) > 1 and core_key[1].isupper():
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZCONFIG_KEY)
                        # If this is zMachine, enter the block for nested key tracking
                        if core_key == 'zMachine':
                            emitter.enter_zmachine_block(indent, original_line_num)
                    # Check for zSub at root level (ERROR - zSub must always be nested)
                    elif core_key == 'zSub':
                        # zSub at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"'zSub' cannot be at root level. It must be nested under a parent key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                        # Still emit as ROOT_KEY token for highlighting
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    # Check for zRBAC at root level (ERROR - zRBAC must always be nested)
                    elif core_key == 'zRBAC':
                        # zRBAC at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"'zRBAC' cannot be at root level. It must be nested under a parent key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                        # Still emit as ROOT_KEY token for highlighting
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    # Check for z-prefixed UI elements at root level (ERROR in zUI files)
                    elif emitter.is_zui_file and core_key.startswith('z') and core_key[1:2].isupper():
                        # This is a UI element at root level - emit error
                        error_range = Range(
                            Position(original_line_num, current_pos),
                            Position(original_line_num, current_pos + len(core_key))
                        )
                        diagnostic = Diagnostic(
                            range=error_range,
                            message=f"UI element '{core_key}' cannot be at root level. It must be nested under a root key.",
                            severity=1  # Error
                        )
                        emitter.diagnostics.append(diagnostic)
                        # Still emit as ROOT_KEY token for highlighting
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    else:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ROOT_KEY)
                    
                    current_pos += len(core_key)
                    
                    # Emit suffix modifiers (purple)
                    for mod in suffix_mods:
                        emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                else:
                    # Update block tracking (exit blocks we've left based on indentation)
                    emitter.update_zrbac_blocks(indent, original_line_num)
                    emitter.update_zimage_blocks(indent, original_line_num)
                    emitter.update_ztext_blocks(indent, original_line_num)
                    emitter.update_zmd_blocks(indent, original_line_num)
                    emitter.update_zurl_blocks(indent, original_line_num)
                    emitter.update_header_blocks(indent, original_line_num)
                    emitter.update_zmachine_blocks(indent, original_line_num)
                    emitter.update_plural_shorthand_blocks(indent, original_line_num)
                    
                    # Split modifiers from key name
                    prefix_mods, core_key, suffix_mods = emitter.split_modifiers(key)
                    current_pos = key_start
                    
                    # Emit prefix modifiers (purple)
                    for mod in prefix_mods:
                        emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                    
                    # Determine token type for core key and emit
                    # Check for zRBAC key (TOMATO in all .zolo files)
                    if core_key == 'zRBAC':
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_KEY)
                        # Mark that we're entering a zRBAC block
                        emitter.enter_zrbac_block(indent, original_line_num)
                    # Check for zSpark nested keys (purple 98 in zSpark files only)
                    elif emitter.is_zspark_file:
                        # ALL nested keys under zSpark root get purple color
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZSPARK_NESTED_KEY)
                    # Check for zRBAC option keys (PURPLE in zUI and zEnv files only)
                    elif emitter.is_in_zrbac_block(indent) and (emitter.is_zui_file or emitter.is_zenv_file):
                        ZRBAC_OPTIONS = {'zGuest', 'authenticated', 'require_role', 'require_auth', 'require_permission'}
                        if core_key in ZRBAC_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zMachine nested section keys in zConfig files
                    elif emitter.is_in_zmachine_block(indent) and emitter.is_zconfig_file:
                        # Define editable sections (blue/cyan - INFO level)
                        ZMACHINE_EDITABLE_SECTIONS = {
                            'user_preferences', 'time_date_formatting', 'launch_commands', 'custom'
                        }
                        # Define locked/auto-detected sections (red/orange - ERROR level)
                        ZMACHINE_LOCKED_SECTIONS = {
                            'machine_identity', 'python_runtime', 'cpu', 'memory', 'gpu', 'network', 'user_paths'
                        }
                        
                        if core_key in ZMACHINE_EDITABLE_SECTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMACHINE_EDITABLE_KEY)
                        elif core_key in ZMACHINE_LOCKED_SECTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZMACHINE_LOCKED_KEY)
                        else:
                            # Unknown key - default to nested key
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zImage key (GOLD in zUI files) and enter block
                    elif core_key == 'zImage' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zImage block
                        emitter.enter_zimage_block(indent, original_line_num)
                    # Check for zImage option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zimage_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZIMAGE_OPTIONS = {'src', 'alt_text', 'caption', 'open_prompt', 'indent', 'color'}
                        if core_key in ZIMAGE_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zText key (GOLD in zUI files) and enter block
                    elif core_key == 'zText' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zText block
                        emitter.enter_ztext_block(indent, original_line_num)
                    # Check for zText option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_ztext_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZTEXT_OPTIONS = {'content', 'indent', 'color', 'break_after'}
                        if core_key in ZTEXT_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zMD key (GOLD in zUI files) and enter block
                    elif core_key == 'zMD' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zMD block
                        emitter.enter_zmd_block(indent, original_line_num)
                    # Check for zMD option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zmd_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZMD_OPTIONS = {'content', 'indent', 'pause', 'break_message', 'format'}
                        if core_key in ZMD_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zURL key (GOLD in zUI files) and enter block
                    elif core_key == 'zURL' and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a zURL block
                        emitter.enter_zurl_block(indent, original_line_num)
                    # Check for zURL option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_zurl_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        ZURL_OPTIONS = {'label', 'href', 'target', 'color', 'rel', 'window'}
                        if core_key in ZURL_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zH1-zH6 keys (GOLD in zUI files) and enter block
                    elif core_key in {'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'} and emitter.is_zui_file:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                        # Mark that we're entering a header block
                        emitter.enter_header_block(indent, original_line_num)
                    # Check for header option keys (PURPLE in zUI files only, excluding Bifrost keys)
                    elif emitter.is_in_header_block(indent) and emitter.is_zui_file and not core_key.startswith('_'):
                        HEADER_OPTIONS = {'label', 'color', 'style', 'semantic', 'indent'}
                        if core_key in HEADER_OPTIONS:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                        else:
                            emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for plural shorthand option keys (PURPLE in zUI files, 2+ levels deep, excluding Bifrost)
                    elif not core_key.startswith('_') and emitter.is_zui_file:
                        plural_context = emitter.get_plural_shorthand_context(indent)
                        if plural_context:
                            # Define valid options for each plural shorthand type
                            PLURAL_OPTIONS = {
                                'zURLs': {'label', 'href', 'target', 'rel', 'color', 'window'},
                                'zTexts': {'content', 'indent', 'color'},
                                'zImages': {'src', 'alt_text', 'caption', 'open_prompt', 'indent', 'color'},
                                'zH1s': {'label', 'color', 'indent'},
                                'zH2s': {'label', 'color', 'indent'},
                                'zH3s': {'label', 'color', 'indent'},
                                'zH4s': {'label', 'color', 'indent'},
                                'zH5s': {'label', 'color', 'indent'},
                                'zH6s': {'label', 'color', 'indent'},
                                'zMDs': {'content', 'indent', 'color'},
                            }
                            if plural_context in PLURAL_OPTIONS and core_key in PLURAL_OPTIONS[plural_context]:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.ZRBAC_OPTION_KEY)
                            else:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                        else:
                            # Check if this IS a plural shorthand container itself
                            PLURAL_SHORTHANDS = {'zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 
                                               'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs'}
                            if core_key in PLURAL_SHORTHANDS:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                                emitter.enter_plural_shorthand_block(indent, original_line_num, core_key)
                            # Check for zSub key (GOLD in both zUI and zEnv files)
                            elif core_key == 'zSub':
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                            # Check for specific shorthand display event keys (strict whitelist)
                            elif core_key in {'zNavBar', 'zImage', 'zUL', 'zOL', 'zURL', 'zURLs', 'zText', 'zMD', 'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6'}:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                            else:
                                emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    # Check for zSub key (GOLD in both zUI and zEnv files)
                    elif core_key == 'zSub':
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                    # Check for underscore-prefixed keys (Bifrost keys)
                    elif core_key.startswith('_'):
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.BIFROST_KEY)
                    # Check for specific shorthand display event keys (strict whitelist)
                    elif emitter.is_zui_file and core_key in {'zNavBar', 'zImage', 'zUL', 'zOL', 'zURL', 'zURLs', 'zText', 'zMD'}:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.UI_ELEMENT_KEY)
                    else:
                        emitter.emit(original_line_num, current_pos, len(core_key), TokenType.NESTED_KEY)
                    
                    current_pos += len(core_key)
                    
                    # Emit suffix modifiers (purple)
                    for mod in suffix_mods:
                        emitter.emit(original_line_num, current_pos, 1, TokenType.ZRBAC_OPTION_KEY)
                        current_pos += 1
                has_str_hint = False
            
            # Handle (str) multi-line values
            if has_str_hint:
                # Emit value token for first line if present
                if value:
                    value_start = colon_pos + 1
                    # Skip whitespace after colon
                    while value_start < len(line) and line[value_start] == ' ':
                        value_start += 1
                    # For (str) values, always emit as STRING (even if it starts with #)
                    emitter.emit(original_line_num, value_start, len(value), TokenType.STRING)
                
                # Collect and emit tokens for continuation lines
                lines_consumed = 0
                for j in range(i + 1, len(lines)):
                    cont_line = lines[j]
                    cont_original_line = line_mapping.get(j, j)
                    cont_indent = len(cont_line) - len(cont_line.lstrip())
                    cont_stripped = cont_line.strip()
                    
                    # Stop if line is at same or less indent than parent (unless empty)
                    if cont_stripped and cont_indent <= indent:
                        break
                    
                    # Stop if this looks like a new key
                    if cont_stripped and ':' in cont_stripped and cont_indent <= indent:
                        break
                    
                    # Emit STRING token for this continuation line
                    if cont_stripped:
                        # Find where content starts (after indentation)
                        content_start = len(cont_line) - len(cont_line.lstrip())
                        emitter.emit(cont_original_line, content_start, len(cont_stripped), TokenType.STRING)
                    
                    lines_consumed += 1
                
                # Store structured line info
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': value,
                    'line': line,
                    'line_number': original_line_num,
                    'is_multiline': True
                })
                i += lines_consumed + 1
                line_number += lines_consumed + 1
            # Handle multi-line arrays (value == '[')
            elif value == '[':
                # Find opening bracket position
                value_start = colon_pos + 1
                while value_start < len(line) and line[value_start] == ' ':
                    value_start += 1
                bracket_pos = value_start
                
                # Emit opening bracket
                emitter.emit(original_line_num, bracket_pos, 1, TokenType.BRACKET_STRUCTURAL)
                
                # Collect multi-line array content
                reconstructed, lines_consumed, item_line_info = _collect_bracket_array(
                    lines, i + 1, indent, value
                )
                
                # Emit tokens for each array item line
                for item_line_idx, item_content, has_comma in item_line_info:
                    item_original_line = line_mapping.get(item_line_idx, item_line_idx)
                    item_line = lines[item_line_idx]
                    item_indent = len(item_line) - len(item_line.lstrip())
                    
                    # Find where item content starts
                    content_start = item_indent
                    
                    # Emit token for the item content
                    _emit_value_tokens(item_content, item_original_line, content_start, emitter)
                    
                    # Emit comma if present
                    if has_comma:
                        comma_pos = item_indent + len(item_content)
                        emitter.emit(item_original_line, comma_pos, 1, TokenType.COMMA)
                
                # Find and emit closing bracket
                closing_line_idx = i + lines_consumed
                if closing_line_idx < len(lines):
                    closing_line = lines[closing_line_idx]
                    closing_original_line = line_mapping.get(closing_line_idx, closing_line_idx)
                    closing_bracket_pos = closing_line.find(']')
                    if closing_bracket_pos >= 0:
                        emitter.emit(closing_original_line, closing_bracket_pos, 1, TokenType.BRACKET_STRUCTURAL)
                
                # Store structured line info with reconstructed value
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': reconstructed,
                    'line': line,
                    'line_number': original_line_num,
                    'is_multiline': True,
                    'multiline_type': 'array'  # Mark as array for type detection
                })
                i += lines_consumed + 1
                line_number += lines_consumed + 1
            # Handle dash lists (YAML-style: key:\n  - item1\n  - item2)
            elif not value and i + 1 < len(lines):
                # Check if next line starts with dash at child indent
                next_line = lines[i + 1]
                next_indent = len(next_line) - len(next_line.lstrip())
                next_stripped = next_line.strip()
                
                if next_stripped.startswith('- ') and next_indent > indent:
                    # Collect dash list items
                    reconstructed, lines_consumed, item_line_info = _collect_dash_list(lines, i + 1, indent)
                    
                    # Emit tokens for each dash list item line
                    for item_line_idx, dash_pos, item_content in item_line_info:
                        item_original_line = line_mapping.get(item_line_idx, item_line_idx)
                        
                        # Emit dash as BRACKET_STRUCTURAL (same color as [ ])
                        emitter.emit(item_original_line, dash_pos, 1, TokenType.BRACKET_STRUCTURAL)
                        
                        # Emit token for the item content (after "- ")
                        content_start = dash_pos + 2  # After "- "
                        _emit_value_tokens(item_content, item_original_line, content_start, emitter)
                    
                    # Store structured line info with reconstructed value
                    structured_lines.append({
                        'indent': indent,
                        'key': key,
                        'value': reconstructed,
                        'line': line,
                        'line_number': original_line_num,
                        'is_multiline': True,
                        'multiline_type': 'dash_list'  # Mark as dash list for type detection
                })
                    i += lines_consumed + 1
                    line_number += lines_consumed + 1
                else:
                    # Empty value (no dash list)
                    structured_lines.append({
                        'indent': indent,
                        'key': key,
                        'value': value,
                        'line': line,
                        'line_number': original_line_num,
                        'is_multiline': False
                    })
                    i += 1
                    line_number += 1
            else:
                # Regular value (not multi-line)
                if value:
                    value_start = colon_pos + 1
                    # Skip whitespace after colon
                    while value_start < len(line) and line[value_start] == ' ':
                        value_start += 1
                    # Extract core key (without modifiers and type hints) for context-aware coloring
                    clean_key = TYPE_HINT_PATTERN.match(key).group(1) if TYPE_HINT_PATTERN.match(key) else key
                    _, core_key, _ = emitter.split_modifiers(clean_key)
                    _emit_value_tokens(value, original_line_num, value_start, emitter, key=core_key)
                
                # Store structured line info
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': value,
                    'line': line,
                    'line_number': original_line_num,
                    'is_multiline': False
                })
                i += 1
                line_number += 1
        else:
            i += 1
            line_number += 1
    
    # Build nested structure (without token emission, as tokens already emitted)
    return _build_nested_dict(structured_lines, 0, 0)


def _parse_lines(lines: list[str], line_mapping: dict = None) -> dict:
    r"""
    Phase 2, Step 2.3 + Phase 3: Parse lines with nested object and multi-line string support.
    
    Uses indentation to build nested dictionary structure:
    - Track indent level for each line
    - Build parent-child relationships
    - Support nested objects at any depth
    - Support multi-line strings: pipe, triple-quotes, escape sequences
    
    Args:
        lines: Cleaned lines (from Step 1.1)
        line_mapping: Optional dict mapping cleaned line index to original line number (1-based)
    
    Returns:
        Nested dictionary structure
    
    Examples:
        >>> _parse_lines(["name: MyApp", "port: 5000"])
        {'name': 'MyApp', 'port': 5000.0}
        
        >>> _parse_lines(["server:", "  host: localhost", "  port: 5000"])
        {'server': {'host': 'localhost', 'port': 5000.0}}
    """
    if not lines:
        return {}
    
    # Default line mapping if not provided (for backwards compatibility)
    if line_mapping is None:
        line_mapping = {i: i + 1 for i in range(len(lines))}
    
    # Parse lines into structured data with indentation info and multi-line handling
    structured_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Get original line number from mapping
        original_line_number = line_mapping.get(i, i + 1)
        
        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()
            
            # Validate key is ASCII-only (RFC 8259 compliance)
            _validate_ascii_only(key, original_line_number)
            
            # Check if key has (str) type hint for multi-line collection
            match = TYPE_HINT_PATTERN.match(key)
            has_str_hint = match and match.group(2).lower() == 'str'
            
            # Multi-line ONLY enabled with (str) hint
            # | and """ are now literal characters (bread and butter!)
            if has_str_hint:
                # (str) type hint: collect YAML-style indented multi-line
                multiline_value, lines_consumed = _collect_str_hint_multiline(lines, i + 1, indent, value)
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': multiline_value,
                    'line': line,
                    'line_number': original_line_number,
                    'is_multiline': True
                })
                i += lines_consumed + 1
            # Handle multi-line arrays (value == '[')
            elif value == '[':
                # Collect multi-line array content
                reconstructed, lines_consumed, _ = _collect_bracket_array(lines, i + 1, indent, value)
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': reconstructed,
                    'line': line,
                    'line_number': original_line_number,
                    'is_multiline': True,
                    'multiline_type': 'array'  # Mark as array for type detection
                })
                i += lines_consumed + 1
            # Handle dash lists (YAML-style: key:\n  - item1\n  - item2)
            elif not value and i + 1 < len(lines):
                # Check if next line starts with dash at child indent
                next_line = lines[i + 1]
                next_indent = len(next_line) - len(next_line.lstrip())
                next_stripped = next_line.strip()
                
                if next_stripped.startswith('- ') and next_indent > indent:
                    # Collect dash list items
                    reconstructed, lines_consumed, _ = _collect_dash_list(lines, i + 1, indent)
                    structured_lines.append({
                        'indent': indent,
                        'key': key,
                        'value': reconstructed,
                        'line': line,
                        'line_number': original_line_number,
                        'is_multiline': True,
                        'multiline_type': 'dash_list'  # Mark as dash list for type detection
                    })
                    i += lines_consumed + 1
                else:
                    # Empty value (no dash list)
                    structured_lines.append({
                        'indent': indent,
                        'key': key,
                        'value': value,
                        'line': line,
                        'line_number': original_line_number,
                        'is_multiline': False
                    })
                    i += 1
            else:
                # Regular value - | and """ are literal characters
                structured_lines.append({
                    'indent': indent,
                    'key': key,
                    'value': value,
                    'line': line,
                    'line_number': original_line_number,
                    'is_multiline': False
                })
                i += 1
        else:
            i += 1
    
    # Build nested structure
    return _build_nested_dict(structured_lines, 0, 0)


def _collect_str_hint_multiline(lines: list[str], start_idx: int, parent_indent: int, first_value: str) -> tuple[str, int]:
    """
    Collect multi-line string content when (str) type hint is used (YAML-style).
    
    Rule: Collect lines indented MORE than parent, strip base indent, preserve relative.
    
    Args:
        lines: All lines
        start_idx: Index to start collecting from (line after the key)
        parent_indent: Indentation level of the parent key
        first_value: The value on the same line as the key (if any)
    
    Returns:
        Tuple of (multiline_string, lines_consumed)
    
    Examples:
        >>> # Key with inline value
        >>> lines = ["  continues", "  here"]
        >>> _collect_str_hint_multiline(lines, 0, 0, "First")
        ("First\\ncontinues\\nhere", 2)
        
        >>> # Key without inline value
        >>> lines = ["  First", "  Second"]
        >>> _collect_str_hint_multiline(lines, 0, 0, "")
        ("First\\nSecond", 2)
    """
    collected = []
    
    # Add first value if present
    if first_value:
        collected.append(first_value)
    
    base_indent = None
    lines_consumed = 0
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Stop if line is at same or less indent than parent (unless empty)
        if stripped and line_indent <= parent_indent:
            break
        
        # Stop if this looks like a new key at the same level
        if stripped and ':' in stripped and line_indent <= parent_indent:
            break
        
        # Empty line - preserve it
        if not stripped:
            collected.append('')
            lines_consumed += 1
            continue
        
        # Set base indent from first content line
        if base_indent is None:
            base_indent = line_indent
        
        # Strip base indent, keep relative
        if base_indent is not None:
            if line_indent >= base_indent:
                relative_line = line[base_indent:] if len(line) >= base_indent else line.strip()
                collected.append(relative_line)
            else:
                collected.append(line.strip())
        else:
            collected.append(line.strip())
        
        lines_consumed += 1
    
    return '\n'.join(collected), lines_consumed


def _collect_dash_list(lines: list[str], start_idx: int, parent_indent: int) -> tuple[str, int, list]:
    """
    Collect YAML-style dash list items (- item1, - item2, etc.).
    
    Rules:
    - Detect lines starting with "- " at child indent level
    - Collect consecutive dash items
    - Stop when indent returns to parent level or less
    - Track each item's line number for token emission
    
    Args:
        lines: All lines
        start_idx: Index to start collecting from (line after the key)
        parent_indent: Indentation level of the parent key
    
    Returns:
        Tuple of (reconstructed_array_string, lines_consumed, item_line_info)
        - reconstructed_array_string: "[item1, item2, item3]"
        - lines_consumed: Number of lines consumed
        - item_line_info: List of (line_idx, dash_pos, item_content) for token emission
    
    Examples:
        >>> lines = ["  - item1", "  - item2", "  - item3"]
        >>> _collect_dash_list(lines, 0, 0)
        ("[item1, item2, item3]", 3, [(0, 2, "item1"), (1, 2, "item2"), (2, 2, "item3")])
    """
    collected_items = []
    item_line_info = []  # Track (line_idx, dash_position, content) for each item
    lines_consumed = 0
    expected_indent = None
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            lines_consumed += 1
            continue
        
        # Check if line starts with dash
        if stripped.startswith('- '):
            # Set expected indent from first dash item
            if expected_indent is None:
                expected_indent = line_indent
            
            # Verify this dash is at the expected child indent level
            if line_indent != expected_indent:
                # Different indent level - stop collecting
                break
            
            # Extract item content (everything after "- ")
            item_content = stripped[2:].strip()
            
            if item_content:
                collected_items.append(item_content)
                # Track line index, dash position (for tokenization), and content
                dash_pos = line.index('-')
                item_line_info.append((i, dash_pos, item_content))
            
            lines_consumed += 1
        else:
            # Non-dash line - check if it's at parent indent or less
            if line_indent <= parent_indent:
                # Back to parent level - stop collecting
                break
            else:
                # Could be continuation or nested content - for now, stop
                # TODO: Future enhancement - support nested structures under dash items
                break
    
    # Reconstruct as single-line array format
    if collected_items:
        reconstructed = '[' + ', '.join(collected_items) + ']'
    else:
        reconstructed = '[]'
    
    return reconstructed, lines_consumed, item_line_info


def _collect_bracket_array(lines: list[str], start_idx: int, parent_indent: int, first_value: str) -> tuple[str, int, list]:
    """
    Collect multi-line array content from opening [ to closing ].
    
    Rules:
    - Opening [ is on the key line (first_value = '[')
    - Collect lines indented MORE than parent
    - Stop when we find ] at same or less indent than parent
    - Track each item's line number for token emission
    
    Args:
        lines: All lines
        start_idx: Index to start collecting from (line after opening [)
        parent_indent: Indentation level of the parent key
        first_value: The value on the same line as the key (should be '[')
    
    Returns:
        Tuple of (reconstructed_array_string, lines_consumed, item_line_info)
        - reconstructed_array_string: "[item1, item2, item3]"
        - lines_consumed: Number of lines consumed
        - item_line_info: List of (line_idx, item_content, has_comma) for token emission
    
    Examples:
        >>> lines = ["  item1,", "  item2,", "  item3", "]"]
        >>> _collect_bracket_array(lines, 0, 0, "[")
        ("[item1, item2, item3]", 4, [(0, "item1", True), (1, "item2", True), (2, "item3", False)])
    """
    collected_items = []
    item_line_info = []  # Track (line_idx, content, has_comma) for each item
    lines_consumed = 0
    closing_bracket_line = None
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Check if this is the closing bracket
        if stripped == ']' or (stripped.startswith(']') and line_indent <= parent_indent):
            closing_bracket_line = i
            lines_consumed += 1
            break
        
        # Skip empty lines
        if not stripped:
            lines_consumed += 1
            continue
        
        # Collect array item
        # Remove trailing comma if present
        has_comma = stripped.endswith(',')
        item_content = stripped.rstrip(',').strip()
        
        if item_content:
            collected_items.append(item_content)
            item_line_info.append((i, item_content, has_comma))
        
        lines_consumed += 1
    
    # Reconstruct as single-line array format
    if collected_items:
        reconstructed = '[' + ', '.join(collected_items) + ']'
    else:
        reconstructed = '[]'
    
    return reconstructed, lines_consumed, item_line_info


def _collect_pipe_multiline(lines: list[str], start_idx: int, parent_indent: int) -> tuple[str, int]:
    """
    Collect multi-line string content after pipe | marker.
    
    Args:
        lines: All lines
        start_idx: Index to start collecting from
        parent_indent: Indentation level of the parent key
    
    Returns:
        Tuple of (multiline_string, lines_consumed)
    """
    collected = []
    base_indent = None
    lines_consumed = 0
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        
        # If we hit a line at or less than parent indent, we're done
        if line and line_indent <= parent_indent:
            break
        
        # Set base indent from first content line
        if base_indent is None and line.strip():
            base_indent = line_indent
        
        # Collect line, stripping base indentation
        if base_indent is not None:
            if line_indent >= base_indent:
                # Strip base indent, keep relative indent
                relative_line = line[base_indent:] if len(line) >= base_indent else line.strip()
                collected.append(relative_line)
            else:
                collected.append(line.strip())
        else:
            collected.append(line.strip())
        
        lines_consumed += 1
    
    return '\n'.join(collected), lines_consumed


def _collect_triple_quote_multiline(lines: list[str], start_idx: int, initial_value: str) -> tuple[str, int]:
    '''
    Collect multi-line string content between triple quotes.
    
    Args:
        lines: All lines
        start_idx: Index of the line with opening triple-quotes
        initial_value: The value part (might contain opening and/or closing triple-quotes)
    
    Returns:
        Tuple of (multiline_string, lines_consumed)
    '''
    # Check if it's all on one line: """content"""
    if initial_value.count('"""') >= 2:
        # Extract content between quotes
        content = initial_value.split('"""', 2)[1]
        return content, 0
    
    # Multi-line case: collect until closing """
    collected = []
    lines_consumed = 0
    
    # First line might have content after opening """
    first_line_content = initial_value[3:].strip()  # Remove opening """
    if first_line_content:
        collected.append(first_line_content)
    
    # Collect subsequent lines
    base_indent = None
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        lines_consumed += 1
        
        # Check for closing """
        if '"""' in line:
            # Get content before closing """
            closing_content = line.split('"""')[0]
            if base_indent is None and closing_content.strip():
                base_indent = len(line) - len(line.lstrip())
            if closing_content.strip():
                if base_indent is not None:
                    relative_line = closing_content[base_indent:] if len(closing_content) >= base_indent else closing_content.strip()
                    collected.append(relative_line.rstrip())
                else:
                    collected.append(closing_content.strip())
            break
        
        # Set base indent from first content line
        if base_indent is None and line.strip():
            base_indent = len(line) - len(line.lstrip())
        
        # Collect line, stripping base indentation
        if base_indent is not None:
            line_indent = len(line) - len(line.lstrip())
            if line_indent >= base_indent:
                relative_line = line[base_indent:] if len(line) >= base_indent else line.strip()
                collected.append(relative_line.rstrip())
            else:
                collected.append(line.strip())
        else:
            collected.append(line.rstrip())
    
    return '\n'.join(collected), lines_consumed


def _build_nested_dict(structured_lines: list[dict], start_idx: int, current_indent: int) -> dict:
    """
    Recursively build nested dictionary from structured lines.
    
    Args:
        structured_lines: List of parsed line dictionaries
        start_idx: Index to start parsing from
        current_indent: Current indentation level we're parsing at
    
    Returns:
        Nested dictionary
    
    Raises:
        ZoloParseError: If duplicate keys are found at the same nesting level
    """
    result = {}
    seen_keys = {}  # Track: {clean_key: (line_number, original_key)}
    i = start_idx
    
    while i < len(structured_lines):
        line_info = structured_lines[i]
        indent = line_info['indent']
        key = line_info['key']
        value = line_info['value']
        line_number = line_info.get('line_number', '?')
        
        # If we've moved to a different indent level, stop
        if indent != current_indent:
            break
        
        # Strip type hint from key for duplicate checking
        # Example: "port(int)" → "port"
        match = TYPE_HINT_PATTERN.match(key)
        clean_key = match.group(1) if match else key
        
        # UI event shorthands are exempt from duplicate key checks
        # These represent sequential UI elements, not dictionary keys
        is_ui_event_shorthand = (
            clean_key in ['zText', 'zImage', 'zMD', 'zURL', 'zUL', 'zOL', 'zTable'] or
            (clean_key.startswith('zH') and len(clean_key) == 3 and clean_key[2].isdigit())
        )
        
        # Check for duplicate keys (STRICT MODE - Phase 4.7)
        # Exempt UI event shorthands (they represent sequences, not dict keys)
        if not is_ui_event_shorthand and clean_key in seen_keys:
            first_line, first_key = seen_keys[clean_key]
            raise ZoloParseError(
                f"Duplicate key '{clean_key}' found at line {line_number}.\n"
                f"First occurrence: '{first_key}' at line {first_line}.\n"
                f"Keys must be unique within the same level.\n"
                f"Hint: Did you mean to use a different key name?"
            )
        
        # Track seen keys (even UI shorthands, for consistency)
        seen_keys[clean_key] = (line_number, key)
        
        # Check if next line is a child (more indented)
        has_children = False
        child_indent = None
        if i + 1 < len(structured_lines):
            next_indent = structured_lines[i + 1]['indent']
            if next_indent > indent:
                has_children = True
                child_indent = next_indent
        
        if has_children:
            # Recursively parse children
            child_dict = _build_nested_dict(structured_lines, i + 1, child_indent)
            
            # Override Python dict behavior: Use suffix for duplicate UI event keys
            # This preserves both the values AND their interleaved position
            if is_ui_event_shorthand and key in result:
                # Key already exists - add numeric suffix to preserve order
                counter = 2
                suffixed_key = f"{key}__dup{counter}"
                while suffixed_key in result:
                    counter += 1
                    suffixed_key = f"{key}__dup{counter}"
                result[suffixed_key] = child_dict
            else:
                # Normal case - set/overwrite key
                result[key] = child_dict
            
            # Skip all child lines (find next line at current indent or less)
            i += 1
            while i < len(structured_lines) and structured_lines[i]['indent'] > indent:
                i += 1
        else:
            # Leaf node - detect value type or use multi-line string
            if line_info.get('is_multiline', False):
                # Check if it's a multi-line array/dash list (needs type detection) or string (use as-is)
                if line_info.get('multiline_type') in ('array', 'dash_list'):
                    # Multi-line array or dash list: run type detection on reconstructed value
                    typed_value = _detect_value_type(value) if value else ''
                else:
                    # Multi-line string: already processed, use as-is
                    typed_value = value
            else:
                # Detect value type (including \n escape sequences)
                typed_value = _detect_value_type(value) if value else ''
            
            # Override Python dict behavior: Use suffix for duplicate UI event keys
            # This preserves both the values AND their interleaved position
            if is_ui_event_shorthand and key in result:
                # Key already exists - add numeric suffix to preserve order
                counter = 2
                suffixed_key = f"{key}__dup{counter}"
                while suffixed_key in result:
                    counter += 1
                    suffixed_key = f"{key}__dup{counter}"
                result[suffixed_key] = typed_value
            else:
                # Normal case - set/overwrite key
                result[key] = typed_value
            i += 1
    
    return result


def _parse_root_key_value_pairs(lines: list[str]) -> dict:
    """
    Phase 1, Steps 1.2-1.3: Parse basic key-value pairs with type detection.
    
    Rules:
    - Only parse lines at root level (no leading whitespace)
    - Split on first `:` occurrence
    - Trim whitespace from key and value
    - Apply RFC 8259 type detection (Step 1.3)
    - Skip nested lines (will be handled in Phase 2)
    
    Args:
        lines: Cleaned lines (from Step 1.1)
    
    Returns:
        Dictionary with root-level key-value pairs (typed values)
    
    Examples:
        >>> _parse_root_key_value_pairs(["name: MyApp", "port: 5000"])
        {'name': 'MyApp', 'port': 5000.0}
        
        >>> _parse_root_key_value_pairs(["debug: true", "db: null"])
        {'debug': True, 'db': None}
    """
    result = {}
    
    for line in lines:
        # Check if this is a root-level line (no leading whitespace)
        if line and line[0] not in (' ', '\t'):
            # Check if line contains a colon (key: value pattern)
            if ':' in line:
                # Split on first colon only
                key, _, value = line.partition(':')
                
                # Trim whitespace
                key = key.strip()
                value = value.strip()
                
                # Step 1.3: Detect and convert value type
                typed_value = _detect_value_type(value)
                
                result[key] = typed_value
    
    return result


def _emit_value_tokens(value: str, line: int, start_pos: int, emitter: TokenEmitter, type_hint: str = None, key: str = None):
    """
    Emit semantic tokens for a value based on its detected type.
    
    Args:
        value: The value string
        line: Line number
        start_pos: Starting character position
        emitter: Token emitter
        type_hint: Optional type hint (int, float, str, bool) for semantic highlighting
        key: Optional key name for context-aware coloring
    """
    if not value:
        return
    
    # zMode value (Terminal/zBifrost) - tomato red in zSpark files
    if emitter.is_zspark_file and key == 'zMode':
        emitter.emit(line, start_pos, len(value), TokenType.ZSPARK_MODE_VALUE)
        # Validate zMode value
        if value not in ('Terminal', 'zBifrost'):
            from ..lsp_types import Diagnostic, Range, Position
            emitter.diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=line, character=start_pos),
                    end=Position(line=line, character=start_pos + len(value))
                ),
                message=f"Invalid zMode value: '{value}'. Expected 'Terminal' or 'zBifrost'.",
                severity=1,  # Error
                source="zolo-lsp"
            ))
        return
    
    # zVaFile value (must be zUI.*) - dark green in zSpark files
    if emitter.is_zspark_file and key == 'zVaFile':
        emitter.emit(line, start_pos, len(value), TokenType.ZSPARK_VAFILE_VALUE)
        # Validate zVaFile format: must be zUI.* with no file extension
        if not value.startswith('zUI.'):
            from ..lsp_types import Diagnostic, Range, Position
            emitter.diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=line, character=start_pos),
                    end=Position(line=line, character=start_pos + len(value))
                ),
                message=f"Invalid zVaFile value: '{value}'. Must start with 'zUI.' (e.g., 'zUI.zBreakpoints').",
                severity=1,  # Error
                source="zolo-lsp"
            ))
        elif value.count('.') > 1:
            # Check for file extension (more than one dot means likely a file extension)
            from ..lsp_types import Diagnostic, Range, Position
            emitter.diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=line, character=start_pos),
                    end=Position(line=line, character=start_pos + len(value))
                ),
                message=f"Invalid zVaFile value: '{value}'. Must not have a file extension (e.g., 'zUI.zBreakpoints', not 'zUI.zBreakpoints.json').",
                severity=1,  # Error
                source="zolo-lsp"
            ))
        return
    
    # zBlock value - light purple in zSpark files
    if emitter.is_zspark_file and key == 'zBlock':
        emitter.emit(line, start_pos, len(value), TokenType.ZSPARK_SPECIAL_VALUE)
        return
    
    # If type hint provided, emit based on semantic type (after hint processing)
    if type_hint:
        hint_lower = type_hint.lower()
        if hint_lower == 'str':
            # Force string token even if value looks like number/bool
            has_valid_escape = any(seq in value for seq in ['\\n', '\\t', '\\r', '\\\\', '\\"', "\\'", '\\u'])
            has_brackets = any(c in value for c in '[]{}')
            if has_valid_escape or has_brackets:
                _emit_string_with_escapes(value, line, start_pos, emitter)
            else:
                emitter.emit(line, start_pos, len(value), TokenType.STRING)
            return
        elif hint_lower == 'int' or hint_lower == 'float':
            # Force number token
            emitter.emit(line, start_pos, len(value), TokenType.NUMBER)
            return
        elif hint_lower == 'bool':
            # Force boolean token
            emitter.emit(line, start_pos, len(value), TokenType.BOOLEAN)
        return
    
    # zPath (@ or ~ followed by dot-separated path)
    # ONLY in zKernel files (zUI, zSpark, zEnv, zConfig) - string-first for regular .zolo
    is_zkernel_file = emitter.is_zui_file or emitter.is_zspark_file or emitter.is_zenv_file or emitter.is_zconfig_file
    if is_zkernel_file and _is_zpath_value(value):
        emitter.emit_zpath_tokens(value, line, start_pos)
        return
    
    # Array (bracket syntax)
    if value.startswith('[') and value.endswith(']'):
        _emit_array_tokens(value, line, start_pos, emitter)
        return
    
    # Object (brace syntax)
    if value.startswith('{') and value.endswith('}'):
        _emit_object_tokens(value, line, start_pos, emitter)
        return
    
    # Boolean
    if value.lower() in ('true', 'false'):
        emitter.emit(line, start_pos, len(value), TokenType.BOOLEAN)
        return
    
    # Number
    if _is_valid_number(value):
        emitter.emit(line, start_pos, len(value), TokenType.NUMBER)
        return
    
    # Null
    if value == 'null':
        emitter.emit(line, start_pos, len(value), TokenType.NULL)
        return
    
    # Environment/Configuration constants (PROD, DEBUG, INFO, etc.)
    if _is_env_config_value(value):
        emitter.emit(line, start_pos, len(value), TokenType.ENV_CONFIG_VALUE)
        return
    
    # Check for specific string types
    # Timestamp
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
        emitter.emit(line, start_pos, len(value), TokenType.TIMESTAMP_STRING)
        return
    
    # Time
    if re.match(r'^\d{2}:\d{2}(?::\d{2})?$', value):
        emitter.emit(line, start_pos, len(value), TokenType.TIME_STRING)
        return
    
    # Version
    if re.match(r'^\d+\.\d+(?:\.\d+|\.\*)+$', value):
        emitter.emit(line, start_pos, len(value), TokenType.VERSION_STRING)
        return
    
    # Ratio
    if re.match(r'^\d{1,3}:\d{1,3}$', value) and value != 'null':
        emitter.emit(line, start_pos, len(value), TokenType.RATIO_STRING)
        return
    
    # String (default)
    # Check for VALID escape sequences or brackets within the string
    # Only enter escape processing for known escapes: \n \t \r \\ \" \' \u
    # This allows Windows paths like C:\Windows to work naturally
    has_valid_escape = any(seq in value for seq in ['\\n', '\\t', '\\r', '\\\\', '\\"', "\\'", '\\u'])
    has_brackets = any(c in value for c in '[]{}')
    
    if has_valid_escape or has_brackets:
        _emit_string_with_escapes(value, line, start_pos, emitter)
    else:
        emitter.emit(line, start_pos, len(value), TokenType.STRING)


def _emit_string_with_escapes(value: str, line: int, start_pos: int, emitter: TokenEmitter):
    """
    Emit string token with escape sequence tokens.
    String-first philosophy: Only escape sequences get special highlighting.
    Brackets/braces inside strings are just regular string characters.
    """
    pos = 0
    last_emit = 0
    
    while pos < len(value):
        # Handle escape sequences
        if value[pos] == '\\' and pos + 1 < len(value):
            # Check what kind of escape FIRST, before emitting
            next_char = value[pos + 1]
            
            if next_char in 'ntr\\\'"':
                # Known escape - emit string before it, then emit the escape
                if pos > last_emit:
                    emitter.emit(line, start_pos + last_emit, pos - last_emit, TokenType.STRING)
                emitter.emit(line, start_pos + pos, 2, TokenType.ESCAPE_SEQUENCE)
                pos += 2
                last_emit = pos
            elif next_char == 'u' and pos + 5 < len(value):
                # Unicode escape \uXXXX - emit string before it, then emit the escape
                if pos > last_emit:
                    emitter.emit(line, start_pos + last_emit, pos - last_emit, TokenType.STRING)
                emitter.emit(line, start_pos + pos, 6, TokenType.ESCAPE_SEQUENCE)
                pos += 6
                last_emit = pos
            else:
                # Unknown escape (like \W, \S, \d) - treat as literal string
                # DON'T emit anything, just skip the backslash
                # The backslash and next char will be included in the final STRING token
                pos += 1  # Only skip the backslash, next char will be part of string
        else:
            pos += 1
    
    # Emit remaining string
    if last_emit < len(value):
        emitter.emit(line, start_pos + last_emit, len(value) - last_emit, TokenType.STRING)


def _emit_array_tokens(value: str, line: int, start_pos: int, emitter: TokenEmitter):
    """Emit tokens for array syntax [...]."""
    # Opening bracket
    emitter.emit(line, start_pos, 1, TokenType.BRACKET_STRUCTURAL)
    
    # Parse inner content
    inner = value[1:-1].strip()
    if inner:
        # Split array items at top-level commas (respecting nesting)
        items = []
        depth = 0
        item_start = 0
        
        for i, char in enumerate(inner):
            if char in '[{':
                depth += 1
            elif char in ']}':
                depth -= 1
            elif char == ',' and depth == 0:
                # Found item boundary
                item = inner[item_start:i].strip()
                if item:
                    items.append((item, start_pos + 1 + item_start + (len(inner[item_start:i]) - len(item))))
                # Emit comma
                emitter.emit(line, start_pos + 1 + i, 1, TokenType.COMMA)
                item_start = i + 1
        
        # Last item
        item = inner[item_start:].strip()
        if item:
            items.append((item, start_pos + 1 + item_start + (len(inner[item_start:]) - len(item))))
        
        # Recursively emit tokens for each item
        for item, item_pos in items:
            _emit_value_tokens(item, line, item_pos, emitter)
    
    # Closing bracket
    emitter.emit(line, start_pos + len(value) - 1, 1, TokenType.BRACKET_STRUCTURAL)


def _emit_object_tokens(value: str, line: int, start_pos: int, emitter: TokenEmitter):
    """Emit tokens for object syntax {...}."""
    # Opening brace
    emitter.emit(line, start_pos, 1, TokenType.BRACE_STRUCTURAL)
    
    # Parse inner content
    inner = value[1:-1].strip()
    if inner:
        # Split object pairs at top-level commas (respecting nesting)
        pairs = []
        depth = 0
        pair_start = 0
        
        for i, char in enumerate(inner):
            if char in '[{':
                depth += 1
            elif char in ']}':
                depth -= 1
            elif char == ',' and depth == 0:
                # Found pair boundary
                pair = inner[pair_start:i].strip()
                if pair and ':' in pair:
                    pairs.append((pair, start_pos + 1 + pair_start + (len(inner[pair_start:i]) - len(pair))))
                # Emit comma
                emitter.emit(line, start_pos + 1 + i, 1, TokenType.COMMA)
                pair_start = i + 1
        
        # Last pair
        pair = inner[pair_start:].strip()
        if pair and ':' in pair:
            pairs.append((pair, start_pos + 1 + pair_start + (len(inner[pair_start:]) - len(pair))))
        
        # Emit tokens for each key-value pair
        for pair, pair_pos in pairs:
            # Split on first colon (respecting nesting)
            depth = 0
            colon_idx = -1
            for i, char in enumerate(pair):
                if char in '[{':
                    depth += 1
                elif char in ']}':
                    depth -= 1
                elif char == ':' and depth == 0:
                    colon_idx = i
                    break
            
            if colon_idx >= 0:
                key = pair[:colon_idx].strip()
                val = pair[colon_idx + 1:].strip()
                
                # Calculate key position
                key_offset = len(pair[:colon_idx]) - len(key)
                key_pos = pair_pos + key_offset
                
                # Check for type hint in key
                match = TYPE_HINT_PATTERN.match(key)
                type_hint_text = None
                if match:
                    # Key has type hint: keyname(type)
                    clean_key = match.group(1)
                    type_hint_text = match.group(2)
                    
                    # Emit key name
                    emitter.emit(line, key_pos, len(clean_key), TokenType.NESTED_KEY)
                    
                    # Emit opening paren
                    paren_pos = key_pos + len(clean_key)
                    emitter.emit(line, paren_pos, 1, TokenType.TYPE_HINT_PAREN)
                    
                    # Emit type hint text
                    type_pos = paren_pos + 1
                    emitter.emit(line, type_pos, len(type_hint_text), TokenType.TYPE_HINT)
                    
                    # Emit closing paren
                    close_paren_pos = type_pos + len(type_hint_text)
                    emitter.emit(line, close_paren_pos, 1, TokenType.TYPE_HINT_PAREN)
                else:
                    # No type hint - emit key as single token
                    emitter.emit(line, key_pos, len(key), TokenType.NESTED_KEY)
                
                # Emit colon
                emitter.emit(line, pair_pos + colon_idx, 1, TokenType.COLON)
                
                # Emit value token (recursively) with semantic type hint
                if val:
                    val_offset = len(pair[:colon_idx + 1]) + (len(pair[colon_idx + 1:]) - len(val))
                    val_pos = pair_pos + val_offset
                    _emit_value_tokens(val, line, val_pos, emitter, type_hint=type_hint_text)
    
    # Closing brace
    emitter.emit(line, start_pos + len(value) - 1, 1, TokenType.BRACE_STRUCTURAL)


def _validate_ascii_only(value: str, line_num: int = None) -> None:
    """
    Validate that value contains only ASCII characters (RFC 8259 compliance).
    
    Non-ASCII characters (emojis, accented letters, etc.) are detected and
    a helpful error message suggests the proper Unicode escape format.
    
    This provides error-driven education:
    - User can naturally type/paste emojis: icon: ♥️
    - Parser catches it and suggests: icon: \\u2764\\uFE0F
    - User learns the RFC 8259 compliant format
    - No IDE integration needed!
    
    Args:
        value: String value to validate
        line_num: Optional line number for error messages
    
    Raises:
        ZoloParseError: If non-ASCII characters are detected
    
    Examples:
        >>> _validate_ascii_only("hello")  # OK
        >>> _validate_ascii_only("♥️")  # Raises error with suggestion
    """
    for i, char in enumerate(value):
        if ord(char) > 127:  # Non-ASCII detected
            # Convert character to Unicode escape sequence
            codepoint = ord(char)
            
            if codepoint <= 0xFFFF:
                # Basic Multilingual Plane (most characters)
                escape = f"\\u{codepoint:04X}"
            else:
                # Supplementary plane (emojis, etc.) - use surrogate pair
                # Formula: U+10000 to U+10FFFF
                high_surrogate = ((codepoint - 0x10000) >> 10) + 0xD800
                low_surrogate = ((codepoint - 0x10000) & 0x3FF) + 0xDC00
                escape = f"\\u{high_surrogate:04X}\\u{low_surrogate:04X}"
            
            # Get character name for better error message
            char_name = None
            try:
                import unicodedata
                char_name = unicodedata.name(char, None)
            except:
                pass
            
            # Build helpful error message
            line_info = f" at line {line_num}" if line_num else ""
            char_desc = f" ({char_name})" if char_name else ""
            
            error_msg = (
                f"Non-ASCII character '{char}' detected{line_info}.\n"
                f"Unicode: U+{codepoint:04X}{char_desc}\n"
                f"\n"
                f"RFC 8259 requires ASCII-only. Use Unicode escape instead:\n"
                f"  {escape}\n"
                f"\n"
                f"Hint: Copy the escape sequence above and replace the character.\n"
                f"      This teaches you the RFC 8259 compliant format!"
            )
            
            raise ZoloParseError(error_msg)


def _detect_value_type(value: str) -> Any:
    r"""
    .zolo String-First Type Detection.
    
    Philosophy: Safe by default, explicit when needed.
    
    Auto-Detection (RFC 8259 Primitives):
    1. Array (bracket syntax): '[...]' → list
    2. Number: Valid numeric format → float (RFC 8259 default)
    3. Null: 'null' (standalone) → None (RFC 8259 primitive)
    
    Everything Else → String (including 'true', 'false'):
    - Use type hints for explicit conversion: (bool), (int), (str)
    - Booleans need hints (they're ambiguous words in natural language)
    - This prevents YAML-style surprises (NO → False, yes → True)
    - Values are predictable and safe
    
    Edge Cases:
    - Empty value (no value after colon) → '' (empty string)
    - 'null value' (null with other text) → 'null value' (string)
    
    Multi-line Support:
    - \n escape sequences are converted to actual newlines
    
    Anti-Quirk Rules:
    - '00123' (leading zero) → string (NOT octal)
    - '1.0.0' → string (NOT number)
    - 'NO', 'YES', 'true', 'false' → strings (use type hints!)
    
    Args:
        value: String value to detect and convert
    
    Returns:
        Typed value (list, float, None, or str)
    
    Examples:
        >>> _detect_value_type('5000')
        5000.0
        >>> _detect_value_type('null')
        None
        >>> _detect_value_type('true')
        'true'
        >>> _detect_value_type('')
        ''
    """
    # Validate ASCII-only BEFORE any processing (RFC 8259 compliance)
    # This catches emojis/non-ASCII and provides helpful error with \uXXXX suggestion
    _validate_ascii_only(value)
    
    # Empty value (key: with nothing after) → empty string
    if not value:
        return ''
    
    # Array (bracket syntax)
    if value.startswith('[') and value.endswith(']'):
        return _parse_bracket_array(value)
    
    # Object (brace syntax - flow-style)
    if value.startswith('{') and value.endswith('}'):
        return _parse_brace_object(value)
    
    # Number (RFC 8259: all numbers → float)
    if _is_valid_number(value):
        return float(value)
    
    # Null (RFC 8259 primitive) - standalone only!
    if value == 'null':
        return None
    
    # String (DEFAULT - everything else!)
    # This includes: 'true', 'false', 'yes', 'no', 'null value', etc.
    
    # Step 1: Decode Unicode escapes (\uXXXX) - RFC 8259 compliance
    if '\\u' in value:
        value = _decode_unicode_escapes(value)
    
    # Step 2: Process other escape sequences (\n, \t, etc.)
    value = _process_escape_sequences(value)
    
    return value


def _parse_brace_object(value: str) -> dict:
    """
    Parse object with brace syntax {key: value, key2: value2}.
    
    Rules:
    - Strip outer braces { and }
    - Split on commas (top-level only)
    - Each item is key: value
    - Apply type detection recursively
    - Handle empty objects {}
    
    Args:
        value: String like '{x: 10, y: 20}' or '{}'
    
    Returns:
        Dictionary with typed values
    
    Examples:
        >>> _parse_brace_object('{x: 10, y: 20}')
        {'x': 10.0, 'y': 20.0}
        
        >>> _parse_brace_object('{name: Alice, active: true}')
        {'name': 'Alice', 'active': 'true'}
        
        >>> _parse_brace_object('{}')
        {}
    """
    # Strip outer braces
    inner = value[1:-1].strip()
    
    # Empty object
    if not inner:
        return {}
    
    # Parse key-value pairs
    result = {}
    seen_keys = {}  # Track duplicates: {clean_key: original_key}
    
    # Split on commas, but respect nested brackets/braces
    pairs = _split_on_comma(inner)
    
    for pair in pairs:
        pair = pair.strip()
        if ':' in pair:
            # Split on first colon
            key, _, val = pair.partition(':')
            key = key.strip()
            val = val.strip()
            
            # Strip type hint from key for duplicate checking
            match = TYPE_HINT_PATTERN.match(key)
            clean_key = match.group(1) if match else key
            
            # Check for duplicate keys (STRICT MODE - Phase 4.7)
            if clean_key in seen_keys:
                first_key = seen_keys[clean_key]
                raise ZoloParseError(
                    f"Duplicate key '{clean_key}' in flow-style object: {value}\n"
                    f"First occurrence: '{first_key}', duplicate: '{key}'.\n"
                    f"Keys must be unique within the same object."
                )
            
            seen_keys[clean_key] = key
            
            # Recursively detect type for value
            typed_value = _detect_value_type(val)
            result[key] = typed_value
    
    return result


def _split_on_comma(text: str) -> list[str]:
    """
    Split text on commas, but respect nested brackets/braces.
    
    Args:
        text: Text to split
    
    Returns:
        List of parts split on top-level commas
    
    Examples:
        >>> _split_on_comma('a, b, c')
        ['a', 'b', 'c']
        
        >>> _split_on_comma('a: [1, 2], b: 3')
        ['a: [1, 2]', 'b: 3']
    """
    parts = []
    current = []
    depth = 0  # Track nesting depth
    
    for char in text:
        if char in '[{':
            depth += 1
            current.append(char)
        elif char in ']}':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            # Top-level comma - split here
            parts.append(''.join(current))
            current = []
        else:
            current.append(char)
    
    # Add final part
    if current:
        parts.append(''.join(current))
    
    return parts


def _decode_unicode_escapes(value: str) -> str:
    r"""
    Decode Unicode escape sequences to actual characters.
    
    Supports:
    - Basic Unicode: copyright symbol, accented characters
    - Emoji (surrogate pairs): multi-byte emoji
    - Multiple escapes in one string
    
    This is the RFC 8259 compliant way to represent Unicode in .zolo files.
    The VSCode extension provides a zEmoji helper to make writing these easier.
    
    Args:
        value: String that may contain Unicode escape sequences
    
    Returns:
        String with Unicode escapes decoded to actual characters
    
    Examples:
        Copyright: escape code to symbol
        Café: escape code to accented e
        Emoji: surrogate pair to emoji character
    """
    # Use Python's unicode_escape codec to decode
    # This handles both basic Unicode and surrogate pairs correctly
    try:
        # Encode as bytes, then decode using unicode_escape codec
        # This properly handles surrogate pairs for emoji
        result = value.encode('utf-8').decode('unicode_escape')
        # Re-encode and decode to handle any remaining issues
        result = result.encode('utf-16', 'surrogatepass').decode('utf-16')
        return result
    except Exception:
        # If decoding fails, return original value
        return value


def _process_escape_sequences(value: str) -> str:
    r"""
    Process escape sequences in strings - PERMISSIVE approach.
    
    Known escapes (processed):
    - \n → newline
    - \t → tab
    - \r → carriage return (zDisplay terminal control!)
    - \\ → backslash
    - \" → double quote
    - \' → single quote
    
    Unknown escapes (preserved as-is):
    - \d, \w, \x → Kept literal for regex, Windows paths
    - Example: "C:\Windows" → "C:\\Windows" (works!)
    
    Args:
        value: String that may contain escape sequences
    
    Returns:
        String with escape sequences processed
    
    Note:
        \uXXXX Unicode escapes are handled by _decode_unicode_escapes()
        before this function is called.
    """
    # Replace escape sequences (order matters - \\ must be after others)
    value = value.replace('\\n', '\n')
    value = value.replace('\\t', '\t')
    value = value.replace('\\r', '\r')
    value = value.replace('\\\\', '\\')
    value = value.replace('\\"', '"')
    value = value.replace("\\'", "'")
    
    # Unknown escapes already preserved as-is (string-first!)
    return value


def _is_zpath_value(value: str) -> bool:
    """
    Check if value is a zPath (zKernel path resolution syntax).
    
    zPath format:
    - Starts with @ or ~ modifier
    - Followed by dot-separated path components
    - Examples: @.static.brand.logo.png, ~.config.theme
    
    Args:
        value: String to check
    
    Returns:
        True if valid zPath, False otherwise
    """
    if not value:
        return False
    
    # Must start with @ or ~
    if value[0] not in ('@', '~'):
        return False
    
    # Must have at least one dot after the modifier
    if len(value) < 2 or value[1] != '.':
        return False
    
    # Must have at least one path component after the first dot
    if len(value) < 3:
        return False
    
    return True


def _is_env_config_value(value: str) -> bool:
    """
    Check if value is an environment/configuration constant.
    
    Detects ALL-CAPS strings that represent configuration states:
    - Log levels: PROD, DEBUG, INFO, WARN, ERROR, TRACE
    - Environments: DEV, DEVELOPMENT, STAGING, PRODUCTION, TEST
    - States: ENABLED, DISABLED, ACTIVE, INACTIVE, ON, OFF
    
    Args:
        value: String to check
    
    Returns:
        True if value matches env/config pattern, False otherwise
    """
    if not value or len(value) < 2:
        return False
    
    # Must be all uppercase
    if not value.isupper():
        return False
    
    # Must be alphabetic only (no numbers, no special chars)
    if not value.isalpha():
        return False
    
    # Whitelist of common environment/config constants
    ENV_CONSTANTS = {
        # Log levels
        'PROD', 'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'TRACE', 'FATAL',
        # Environments
        'DEV', 'DEVELOPMENT', 'STAGING', 'PRODUCTION', 'TEST', 'LOCAL',
        # States
        'ENABLED', 'DISABLED', 'ACTIVE', 'INACTIVE', 'ON', 'OFF',
        'YES', 'NO',
        # Modes
        'STRICT', 'PERMISSIVE', 'NORMAL', 'VERBOSE', 'QUIET', 'SILENT',
    }
    
    return value in ENV_CONSTANTS


def _is_valid_number(value: str) -> bool:
    r"""
    Check if value is a valid RFC 8259 number.
    
    Rules:
    - Must match: -?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?
    - Anti-quirk: NO leading zeros (except '0' or '0.x')
    
    Valid:
        5000, -42, 0, 30.5, 1.5e10, 2E-3, 0.5
    
    Invalid (Anti-Quirk):
        00123 (leading zero), 01 (leading zero), 1.0.0 (multiple dots)
    
    Args:
        value: String to check
    
    Returns:
        True if valid number, False otherwise
    """
    if not value:
        return False
    
    # Anti-quirk: Check for leading zeros (except '0' or '0.something')
    if len(value) > 1 and value[0] == '0' and value[1].isdigit():
        # This is like '00123' or '01' - NOT a valid number
        return False
    
    # Try to parse as float
    try:
        float(value)
        return True
    except ValueError:
        return False


def _parse_bracket_array(value: str) -> list:
    """
    Phase 2, Step 2.1: Parse array with bracket syntax [item1, item2, item3].
    
    Rules:
    - Strip outer brackets [ and ]
    - Split on top-level commas (respect nested brackets/braces)
    - Trim whitespace from each item
    - Apply type detection to each item recursively
    - Handle empty arrays []
    
    Args:
        value: String like '[1, 2, 3]' or '[[1, 2], [3, 4]]'
    
    Returns:
        List with typed items
    
    Examples:
        >>> _parse_bracket_array('[1, 2, 3]')
        [1.0, 2.0, 3.0]
        
        >>> _parse_bracket_array('[python, yaml, test]')
        ['python', 'yaml', 'test']
        
        >>> _parse_bracket_array('[[1, 2], [3, 4]]')
        [[1.0, 2.0], [3.0, 4.0]]
        
        >>> _parse_bracket_array('[]')
        []
    """
    # Strip outer brackets
    inner = value[1:-1].strip()
    
    # Empty array
    if not inner:
        return []
    
    # Split on top-level commas (respect nesting)
    items = []
    for item in _split_on_comma(inner):
        item = item.strip()
        # Recursively detect type for each item
        typed_item = _detect_value_type(item)
        items.append(typed_item)
    
    return items


def dump(data: Any, fp: Union[str, Path, IO], file_extension: Optional[str] = None, **kwargs) -> None:
    """
    Dump data to a .zolo file (or compatible format).
    
    Args:
        data: Data to dump (dict, list, or scalar)
        fp: File path (str/Path) or file-like object
        file_extension: Optional file extension override (.zolo, .yaml, .json)
                       If None, will detect from file path or default to .zolo
        **kwargs: Additional arguments passed to YAML/JSON dumper
                 For YAML: default_flow_style=False, allow_unicode=True
                 For JSON: indent=2, ensure_ascii=False
    
    Raises:
        ZoloDumpError: If dumping fails
    
    Examples:
        >>> data = {'port': 8080, 'enabled': True}
        >>> zolo.dump(data, 'config.zolo')
        
        >>> # Dump as JSON
        >>> zolo.dump(data, 'config.json')
        
        >>> # Dump with custom kwargs
        >>> zolo.dump(data, 'config.yaml', default_flow_style=True)
    """
    # Convert to string
    content = dumps(data, file_extension=file_extension, **kwargs)
    
    # Handle file path vs file-like object
    if isinstance(fp, (str, Path)):
        file_path = Path(fp)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise ZoloDumpError(f"Error writing file {file_path}: {e}") from e
    else:
        # File-like object
        try:
            fp.write(content)
        except Exception as e:
            raise ZoloDumpError(f"Error writing to file object: {e}") from e


def dumps(data: Any, file_extension: Optional[str] = None, **kwargs) -> str:
    """
    Dump data to a .zolo string (or compatible format).
    
    Args:
        data: Data to dump (dict, list, or scalar)
        file_extension: Optional file extension hint (.zolo, .yaml, .json)
                       Defaults to .zolo if not provided
        **kwargs: Additional arguments passed to YAML/JSON dumper
    
    Returns:
        Formatted string
    
    Raises:
        ZoloDumpError: If dumping fails
    
    Examples:
        >>> data = {'port': 8080, 'enabled': True}
        >>> print(zolo.dumps(data))
        port: 8080
        enabled: true
        
        >>> # Dump as JSON
        >>> print(zolo.dumps(data, file_extension='.json'))
        {
          "port": 8080,
          "enabled": true
        }
    """
    # Default to .zolo if not specified
    if file_extension is None:
        file_extension = FILE_EXT_ZOLO
    
    # Normalize extension
    file_extension = file_extension.lower()
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension
    
    # Dump based on format
    try:
        if file_extension == FILE_EXT_JSON:
            # Dump as JSON
            json_kwargs = {
                'indent': 2,
                'ensure_ascii': False,
            }
            json_kwargs.update(kwargs)
            return json.dumps(data, **json_kwargs)
        else:
            # Dump as YAML (default for .zolo, .yaml, .yml)
            yaml_kwargs = {
                'default_flow_style': False,
                'allow_unicode': True,
                'sort_keys': False,
            }
            yaml_kwargs.update(kwargs)
            return yaml.dump(data, **yaml_kwargs)
    
    except Exception as e:
        raise ZoloDumpError(f"Dumping error: {e}") from e
