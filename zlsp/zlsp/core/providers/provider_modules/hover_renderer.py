"""
Hover Renderer - Format hover information for .zolo files

Provides formatted hover information for:
- Type hints (using DocumentationRegistry)
- Keys and values
- Numbers, strings, escape sequences
- Context-aware documentation

Uses DocumentationRegistry as SSOT - no duplication!
"""

from typing import Optional
from ...lsp_types import SemanticToken, TokenType, Position
from ...parser.parser_modules.type_hints import TYPE_HINT_PATTERN
from .documentation_registry import DocumentationRegistry


class HoverRenderer:
    """
    Render hover information for different token types.
    
    Uses DocumentationRegistry for all documentation - zero duplication!
    """
    
    # Cache emoji descriptions instance (lazy loaded)
    _emoji_descriptions = None
    
    @staticmethod
    def render(content: str, line: int, character: int, tokens: list[SemanticToken]) -> Optional[str]:
        """
        Render hover information for a position.
        
        Args:
            content: Full .zolo file content
            line: Line number (0-based)
            character: Character position (0-based)
            tokens: List of semantic tokens from parser
        
        Returns:
            Markdown string with hover information, or None
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 HoverRenderer.render: line={line}, char={character}")
        logger.info(f"   Total tokens received: {len(tokens)}")
        
        # Find token at position
        target_pos = Position(line=line, character=character)
        token = HoverRenderer._find_token_at_position(tokens, target_pos)
        
        logger.info(f"   Token: {token.token_type if token else 'None'}")
        
        if not token:
            return None
        
        # Render based on token type
        if token.token_type in (TokenType.TYPE_HINT, TokenType.TYPE_HINT_PAREN):
            return HoverRenderer._render_type_hint(token, content)
        
        elif token.token_type in (TokenType.ROOT_KEY, TokenType.NESTED_KEY):
            return HoverRenderer._render_key(token, content, line)
        
        elif token.token_type == TokenType.NUMBER:
            return HoverRenderer._render_number(token, content)
        
        elif token.token_type == TokenType.STRING:
            return HoverRenderer._render_string(token, content)
        
        elif token.token_type == TokenType.NULL:
            return HoverRenderer._render_null()
        
        elif token.token_type == TokenType.ESCAPE_SEQUENCE:
            return HoverRenderer._render_escape(token, content)
        
        return None
    
    @staticmethod
    def _find_token_at_position(tokens: list[SemanticToken], pos: Position) -> Optional[SemanticToken]:
        """Find the token containing the given position."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Debug: Look for tokens near this line
        nearby = [t for t in tokens if t.line == pos.line]
        logger.info(f"   Found {len(nearby)} tokens on line {pos.line}")
        for t in nearby:
            logger.info(f"     Token: type={t.token_type}, char={t.start_char}-{t.start_char+t.length}, contains={t.range.contains(pos)}")
        
        for token in tokens:
            if token.range.contains(pos):
                return token
        return None
    
    @staticmethod
    def _render_type_hint(token: SemanticToken, content: str) -> Optional[str]:
        """
        Render hover info for a type hint.
        
        Uses DocumentationRegistry - no duplication!
        """
        lines = content.splitlines()
        if token.line >= len(lines):
            return None
        
        line_content = lines[token.line]
        
        # Extract type hint text directly from token position
        type_hint = line_content[token.start_char:token.start_char + token.length]
        
        # Look up documentation from registry
        doc = DocumentationRegistry.get(type_hint.lower())
        if doc:
            # Use the registry's markdown formatter
            return f"## Type Hint: `{type_hint}`\n\n{doc.to_hover_markdown()}"
        else:
            return f"## Type Hint: `{type_hint}`\n\n*Unknown type hint*"
    
    @staticmethod
    def _render_key(token: SemanticToken, content: str, line: int) -> Optional[str]:
        """Render hover info for a key."""
        lines = content.splitlines()
        if line >= len(lines):
            return None
        
        line_content = lines[line]
        
        # Extract key and value
        if ':' in line_content:
            key_part, _, value_part = line_content.partition(':')
            key_part = key_part.strip()
            value_part = value_part.strip()
            
            # Check for type hint
            match = TYPE_HINT_PATTERN.match(key_part)
            if match:
                clean_key = match.group(1)
                type_hint = match.group(2)
                
                return (
                    f"## Key: `{clean_key}`\n\n"
                    f"**Type:** `{type_hint}`\n\n"
                    f"**Value:** `{value_part if value_part else '(nested object)'}`"
                )
            else:
                # No type hint - show detected type
                if value_part:
                    detected_type = HoverRenderer._detect_value_type_name(value_part)
                    return (
                        f"## Key: `{key_part}`\n\n"
                        f"**Detected Type:** {detected_type}\n\n"
                        f"**Value:** `{value_part}`"
                    )
                else:
                    return f"## Key: `{key_part}`\n\n*Nested object*"
        
        return None
    
    @staticmethod
    def _render_number(token: SemanticToken, content: str) -> Optional[str]:
        """Render hover info for a number."""
        lines = content.splitlines()
        if token.line >= len(lines):
            return None
        
        line_content = lines[token.line]
        number_text = line_content[token.start_char:token.start_char + token.length]
        
        try:
            value = float(number_text)
            return (
                f"## Number Value\n\n"
                f"**Value:** `{number_text}`\n\n"
                f"**Type:** RFC 8259 number (stored as float)\n\n"
                f"**Parsed:** `{value}`"
            )
        except ValueError:
            return None
    
    @staticmethod
    def _render_string(token: SemanticToken, content: str) -> Optional[str]:
        """Render hover info for a string."""
        lines = content.splitlines()
        if token.line >= len(lines):
            return None
        
        line_content = lines[token.line]
        string_text = line_content[token.start_char:token.start_char + token.length]
        
        # Check if it's a special string type
        if '\\' in string_text:
            return (
                f"## String Value\n\n"
                f"**Value:** `{string_text}`\n\n"
                f"**Type:** String with escape sequences\n\n"
                f"*Contains escape sequences that will be processed*"
            )
        else:
            return (
                f"## String Value\n\n"
                f"**Value:** `{string_text}`\n\n"
                f"**Type:** String (default in .zolo)"
            )
    
    @staticmethod
    def _render_null() -> str:
        """Render hover info for null."""
        return (
            "## Null Value\n\n"
            "**Type:** RFC 8259 null primitive\n\n"
            "Represents absence of value (Python: `None`, JSON: `null`)"
        )
    
    @staticmethod
    def _render_escape(token: SemanticToken, content: str) -> Optional[str]:
        """Render hover info for an escape sequence."""
        lines = content.splitlines()
        if token.line >= len(lines):
            return None
        
        line_content = lines[token.line]
        escape_text = line_content[token.start_char:token.start_char + token.length]
        
        escape_map = {
            '\\n': 'Newline character',
            '\\t': 'Tab character',
            '\\r': 'Carriage return (terminal control)',
            '\\\\': 'Backslash character',
            '\\"': 'Double quote character',
            "\\'": 'Single quote character',
        }
        
        # Check if it's a Unicode escape
        if escape_text.startswith('\\u') or escape_text.startswith('\\U'):
            # Extract codepoint
            codepoint_str = escape_text[2:]  # Remove \u or \U prefix
            
            # Get emoji description (Phase 3: Emoji Accessibility)
            emoji_info = HoverRenderer._get_emoji_info(codepoint_str)
            
            # Format description
            if escape_text.startswith('\\U'):
                format_desc = "Extended Unicode (4-8 hex digits, for emojis & supplementary planes)"
            else:
                format_desc = "Standard Unicode (4 hex digits, BMP characters)"
            
            # Build hover text
            hover_text = (
                f"## Unicode Escape Sequence\n\n"
                f"**Sequence:** `{escape_text}`\n\n"
                f"**Codepoint:** U+{codepoint_str.upper()}\n\n"
                f"**Format:** {format_desc}\n\n"
            )
            
            # Add emoji info if available
            if emoji_info:
                hover_text += (
                    f"**Character:** {emoji_info['emoji']}\n\n"
                    f"**Description:** {emoji_info['description']}\n\n"
                )
            
            hover_text += "**Type:** RFC 8259 compliant\n\n"
            hover_text += "Will be decoded to the corresponding Unicode character"
            
            return hover_text
        elif escape_text in escape_map:
            description = escape_map[escape_text]
            return (
                f"## Escape Sequence\n\n"
                f"**Sequence:** `{escape_text}`\n\n"
                f"**Meaning:** {description}"
            )
        else:
            return (
                f"## Escape Sequence\n\n"
                f"**Sequence:** `{escape_text}`\n\n"
                f"*Unknown escape sequence*"
            )
    
    @staticmethod
    def _get_emoji_info(codepoint_str: str) -> Optional[dict]:
        """
        Get emoji character and description from codepoint.
        
        Phase 3: Emoji Accessibility Integration
        
        Args:
            codepoint_str: Hex codepoint string (e.g., "1F4F1", "0001F4F1")
            
        Returns:
            Dict with 'emoji' and 'description' keys, or None if not available
        """
        try:
            # Lazy load emoji descriptions (only once)
            if HoverRenderer._emoji_descriptions is None:
                # Try to import from zOS (if available in PYTHONPATH)
                try:
                    import sys
                    from pathlib import Path
                    
                    # Add zOS to path if not already there
                    zlsp_root = Path(__file__).parent.parent.parent.parent.parent
                    zos_path = zlsp_root.parent / "zOS" / "core"
                    if zos_path.exists() and str(zos_path) not in sys.path:
                        sys.path.insert(0, str(zos_path))
                    
                    from zSys.accessibility import get_emoji_descriptions
                    HoverRenderer._emoji_descriptions = get_emoji_descriptions()
                except ImportError:
                    # zOS not available - set to False to avoid retrying
                    HoverRenderer._emoji_descriptions = False
                    return None
            
            # If emoji descriptions failed to load, return None
            if HoverRenderer._emoji_descriptions is False:
                return None
            
            # Get description using the API
            description = HoverRenderer._emoji_descriptions.codepoint_to_description(codepoint_str)
            
            # Convert codepoint to emoji character
            try:
                emoji_char = chr(int(codepoint_str, 16))
            except (ValueError, OverflowError):
                return None
            
            # Return info if we got a valid description
            if description and description != codepoint_str:
                return {
                    'emoji': emoji_char,
                    'description': description
                }
            
            return None
            
        except Exception:
            # Graceful fallback - don't break hover on errors
            return None
    
    @staticmethod
    def _detect_value_type_name(value: str) -> str:
        """Detect and return a human-readable type name for a value."""
        if not value:
            return "empty string"
        
        # Array
        if value.startswith('[') and value.endswith(']'):
            return "array (list)"
        
        # Object
        if value.startswith('{') and value.endswith('}'):
            return "object (dict)"
        
        # Number
        try:
            float(value)
            return "number (auto-detected)"
        except ValueError:
            pass
        
        # Null
        if value == 'null':
            return "null (RFC 8259 primitive)"
        
        # Boolean (but treated as string without type hint!)
        if value in ('true', 'false'):
            return "string (use `(bool)` hint for boolean)"
        
        # String (default)
        return "string (default)"
