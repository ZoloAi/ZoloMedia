"""
Markdown Terminal Parser - Complete zMD Terminal Orchestrator

Parses markdown/HTML content and converts it to ANSI-formatted text for Terminal mode.
Acts as a mini-orchestrator within the zMD event, intelligently routing content to
appropriate zDisplay events (text, list, code blocks).

Features (Phases 1-5):
- Phase 1: Parse inline markdown: **bold**, *italic*, `code` → ANSI
- Phase 2: Strip HTML tags and map zTheme classes → ANSI colors
- Phase 3: Extract markdown lists → display.list() events
- Phase 4: Block-level parsing (paragraphs, lists, code blocks)
- Phase 5: Indentation/color parameters + robust error handling

Author: zOS Framework
Version: 2.0.0 (Phase 5 Complete)
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...zDisplay import zDisplay


class MarkdownTerminalParser:
    """
    Converts markdown content to ANSI-formatted text for Terminal display.
    
    Phase 1: Inline markdown parsing (bold, italic, code)
    Phase 2: HTML class mapping (zText-error → ANSI red)
    Phase 3: List extraction and emission
    Phase 4: Block-level parsing
    """
    
    def __init__(self):
        """Initialize the parser with ANSI code mappings."""
        # ANSI escape codes
        self.ANSI_RESET = '\033[0m'
        self.ANSI_BOLD = '\033[1m'
        self.ANSI_ITALIC = '\033[3m'  # Not supported by all terminals
        self.ANSI_CYAN = '\033[36m'   # For code blocks
        self.ANSI_DIM = '\033[2m'     # For italic fallback
    
    def parse_inline(self, text: str) -> str:
        """
        Parse inline markdown syntax and convert to ANSI codes.
        
        Phase 1: Markdown conversion (bold, italic, code)
        Phase 2: HTML stripping with class → ANSI mapping
        Phase 4 (Emoji): Emoji → [description] conversion for Terminal accessibility
        
        Handles:
        - **bold** → ANSI bold
        - *italic* → ANSI italic (or dim if not supported)
        - `code` → ANSI cyan
        - <span class="zText-error">text</span> → red ANSI text (no HTML)
        - 📱 → [mobile phone] (Terminal mode accessibility)
        
        Args:
            text: Raw markdown text
            
        Returns:
            ANSI-formatted text
            
        Example:
            >>> parser = MarkdownTerminalParser()
            >>> parser.parse_inline("This is **bold** and `code`")
            "This is \033[1mbold\033[0m and \033[36mcode\033[0m"
        """
        if not text:
            return text
        
        # Phase 2: Strip HTML tags and map classes to ANSI (FIRST - before markdown)
        # This prevents markdown patterns inside HTML from being double-processed
        text = self._strip_html_with_color_mapping(text)
        
        # Phase 4 (Emoji): Convert emojis to [description] for Terminal accessibility
        # Do this BEFORE markdown parsing to avoid interference with markdown patterns
        text = self._convert_emojis_to_descriptions(text)
        
        # Phase 1: Process markdown in order: code first (to protect backticks), then bold, then italic
        # This prevents interference between patterns
        
        # 1. Code blocks: `code` → cyan
        text = self._convert_code(text)
        
        # 2. Bold: **text** → bold
        text = self._convert_bold(text)
        
        # 3. Italic: *text* → italic/dim
        text = self._convert_italic(text)
        
        return text
    
    def _convert_code(self, text: str) -> str:
        """
        Convert `code` to ANSI cyan.
        
        Pattern: `text` → \033[36mtext\033[0m
        
        Note: Uses backtick pairs, handles inline code only (not code blocks)
        """
        # Match: `anything` but not ``` (code blocks handled separately)
        # Negative lookahead/lookbehind to avoid matching triple backticks
        pattern = r'(?<!`)(`{1})(?!`)([^`\n]+)\1(?!`)'
        
        def replacer(match):
            code_text = match.group(2)
            return f"{self.ANSI_CYAN}{code_text}{self.ANSI_RESET}"
        
        return re.sub(pattern, replacer, text)
    
    def _convert_bold(self, text: str) -> str:
        """
        Convert **bold** to ANSI bold.
        
        Pattern: **text** → \033[1mtext\033[0m
        
        Note: Handles both ** and __ for bold (markdown standard)
        """
        # Match: **text** or __text__
        # Non-greedy to handle multiple bold sections in one line
        pattern = r'\*\*(.+?)\*\*|__(.+?)__'
        
        def replacer(match):
            # Either group 1 (** style) or group 2 (__ style) will match
            bold_text = match.group(1) if match.group(1) else match.group(2)
            return f"{self.ANSI_BOLD}{bold_text}{self.ANSI_RESET}"
        
        return re.sub(pattern, replacer, text)
    
    def _convert_italic(self, text: str) -> str:
        """
        Convert *italic* to ANSI italic (or dim fallback).
        
        Pattern: *text* → \033[3mtext\033[0m (or \033[2m for dim)
        
        Note: Uses italic if supported, otherwise falls back to dim
        Avoids matching ** (bold) by using negative lookahead
        """
        # Match: *text* or _text_ but NOT **text** or __text__
        # Negative lookahead to avoid matching bold markers
        pattern = r'(?<!\*)(\*)(?!\*)(.+?)\1(?!\*)|(?<!_)(_)(?!_)(.+?)\3(?!_)'
        
        def replacer(match):
            # Either group 2 (* style) or group 4 (_ style) will match
            italic_text = match.group(2) if match.group(2) else match.group(4)
            # Use italic, but many terminals don't support it, so dim is safer
            return f"{self.ANSI_DIM}{italic_text}{self.ANSI_RESET}"
        
        return re.sub(pattern, replacer, text)
    
    def _convert_emojis_to_descriptions(self, text: str) -> str:
        """
        Convert emojis to [description] for Terminal accessibility.
        
        Phase 4 (Emoji Accessibility): Terminal mode conversion
        
        Handles:
        - Direct emojis: 📱 → [mobile phone]
        - Unicode escapes: \\u2665 → [heart] (already decoded by Python)
        - Unknown emojis: 🤷 → [emoji] (fallback)
        - Preserves ASCII punctuation: : * ` (not converted)
        
        Args:
            text: Text potentially containing emojis
            
        Returns:
            Text with emojis replaced by [descriptions]
            
        Example:
            >>> parser._convert_emojis_to_descriptions("Mobile: 📱 and Laptop: 💻")
            "Mobile: [mobile phone] and Laptop: [laptop]"
        """
        if not text:
            return text
        
        # Lazy load emoji descriptions
        try:
            from .....zSys.accessibility import get_emoji_descriptions
            emoji_desc = get_emoji_descriptions()
        except ImportError:
            # If module not available, return text unchanged
            return text
        
        # Define emoji Unicode ranges (exclude ASCII 0x00-0x7F)
        # Common emoji ranges:
        # - U+1F300–U+1F9FF: Miscellaneous Symbols and Pictographs, Emoticons, Transport, etc.
        # - U+2600–U+26FF: Miscellaneous Symbols (sun, stars, weather)
        # - U+2700–U+27BF: Dingbats (scissors, checkmarks)
        # - U+FE00–U+FE0F: Variation selectors (emoji presentation)
        # - U+1F000–U+1F0FF: Mahjong/Domino tiles
        
        def is_emoji(char: str) -> bool:
            """Check if character is in emoji Unicode ranges."""
            if not char or len(char) != 1:
                return False
            
            code_point = ord(char)
            
            # Exclude ASCII range (0x00-0x7F)
            if code_point < 0x80:
                return False
            
            # Emoji ranges
            return (
                (0x1F300 <= code_point <= 0x1F9FF) or  # Main emoji block
                (0x2600 <= code_point <= 0x26FF) or   # Misc symbols
                (0x2700 <= code_point <= 0x27BF) or   # Dingbats
                (0xFE00 <= code_point <= 0xFE0F) or   # Variation selectors
                (0x1F000 <= code_point <= 0x1F0FF) or # Tiles
                (0x1F200 <= code_point <= 0x1F2FF) or # Enclosed ideographic supplement
                (0x1F600 <= code_point <= 0x1F64F) or # Emoticons
                (0x1F680 <= code_point <= 0x1F6FF) or # Transport & map symbols
                (0x1F900 <= code_point <= 0x1F9FF) or # Supplemental symbols
                (0x2300 <= code_point <= 0x23FF) or   # Misc technical
                (0x2B00 <= code_point <= 0x2BFF) or   # Misc symbols and arrows
                (code_point >= 0x10000)               # Supplementary planes
            )
        
        # Convert only emoji characters to [description]
        result = []
        for char in text:
            if is_emoji(char):
                desc = emoji_desc.format_for_terminal(char)
                if desc and desc != char:
                    # Emoji was converted to [description]
                    result.append(desc)
                else:
                    # Emoji but no description - keep original
                    result.append(char)
            else:
                # Not an emoji - keep original (ASCII, punctuation, etc.)
                result.append(char)
        
        return ''.join(result)
    
    def _strip_html_with_color_mapping(self, text: str) -> str:
        """
        Strip HTML tags and map zTheme classes to ANSI colors.
        
        Phase 2: HTML class mapping
        
        Handles:
        - <span class="zText-error">text</span> → red ANSI text
        - <span class="zText-error zFont-bold">text</span> → red + bold ANSI
        - <div class="zCallout">text</div> → text (strip non-color classes)
        
        Args:
            text: Text potentially containing HTML tags
            
        Returns:
            Text with HTML stripped and classes mapped to ANSI
            
        Example:
            >>> parser._strip_html_with_color_mapping('<span class="zText-error">Error!</span>')
            '\033[38;5;203mError!\033[0m'  # Red ANSI
        """
        if not text or '<' not in text:
            return text
        
        # Import color mapper
        try:
            from .....zSys.formatting.ztheme_to_ansi import (
                map_ztheme_classes_to_ansi,
                get_reset_code
            )
        except ImportError:
            # Fallback: just strip tags without color mapping
            return self._strip_all_html_tags(text)
        
        # Pattern: <tag class="class1 class2">content</tag>
        # Captures: tag name, class attribute value, content
        pattern = r'<(\w+)(?:\s+class=["\']([^"\']+)["\'])?(?:\s+[^>]*)?>(.+?)</\1>'
        
        def replacer(match):
            tag_name = match.group(1)
            classes_str = match.group(2) or ''
            content = match.group(3)
            
            if classes_str:
                # Split classes and map to ANSI
                classes = classes_str.split()
                ansi_codes = map_ztheme_classes_to_ansi(classes)
                
                if ansi_codes:
                    # Apply ANSI codes to content
                    return f"{ansi_codes}{content}{get_reset_code()}"
            
            # No recognized classes - just return content without tags
            return content
        
        # Apply the pattern
        text = re.sub(pattern, replacer, text)
        
        # Clean up any remaining simple tags (no content or self-closing)
        text = self._strip_all_html_tags(text)
        
        return text
    
    def _strip_all_html_tags(self, text: str) -> str:
        """
        Strip all HTML tags without any processing.
        
        Fallback for when class mapping is not available or for
        cleaning up remaining tags.
        
        Args:
            text: Text with HTML tags
            
        Returns:
            Text with all HTML tags removed
        """
        # Remove all tags: <anything>
        return re.sub(r'<[^>]+>', '', text)
    
    def parse(self, content: str, display: 'zDisplay', indent: int = 0, color: str = None) -> None:
        """
        Main entry point for parsing markdown content.
        
        Phase 1-2: Parse inline markdown
        Phase 3: Detect lists and emit display.list() events
        Phase 3.5: Handle mixed content (paragraph + list)
        Phase 4: Full block-level parsing (code, list, paragraph)
        Phase 5: Handle indentation, color parameters, and errors
        
        Args:
            content: Markdown content to parse
            display: zDisplay instance for emitting events
            indent: Indentation level for all emitted events (default: 0)
            color: Default color for paragraphs (default: None)
        """
        # Phase 5: Error handling for robustness
        try:
            # Validate input
            if not content or not isinstance(content, str):
                return
            
            # Phase 4: Full block-level parsing
            blocks = self._split_into_blocks(content)
            
            if not blocks:
                return
            
            # Process each block according to its type
            for block_type, block_content in blocks:
                try:
                    if block_type == 'code':
                        self._emit_code_block(block_content, display, indent)
                    elif block_type == 'list':
                        self._emit_list(block_content, display, indent)
                    elif block_type == 'paragraph':
                        # Parse inline markdown and output
                        parsed_content = self.parse_inline(block_content)
                        self._emit_paragraph(parsed_content, indent, color)
                except Exception as e:
                    # Fallback: emit raw content if block processing fails
                    indent_str = ' ' * (indent * 4) if indent > 0 else ''
                    print(f"{indent_str}{block_content}")
                    # Log error if display has logger
                    if hasattr(display, 'zcli') and hasattr(display.zcli, 'logger'):
                        display.zcli.logger.debug(f"[MarkdownParser] Block parsing error: {e}")
        except Exception as e:
            # Ultimate fallback: print raw content
            indent_str = ' ' * (indent * 4) if indent > 0 else ''
            print(f"{indent_str}{content}")
            # Log error if possible
            if hasattr(display, 'zcli') and hasattr(display.zcli, 'logger'):
                display.zcli.logger.debug(f"[MarkdownParser] Fatal parsing error: {e}")
    
    def _split_into_blocks(self, content: str) -> list:
        """
        Split content into blocks (paragraphs, lists, code blocks).
        
        Phase 4: Full block-level parsing
        
        Block types:
        - Code blocks: ```language\\ncode\\n```
        - Lists: consecutive lines starting with * - or 1.
        - Paragraphs: everything else
        
        Args:
            content: Full markdown content
            
        Returns:
            List of tuples: (block_type, block_content)
            block_type: 'code', 'list', 'paragraph'
            
        Example:
            >>> parser._split_into_blocks("Intro\\n\\n```\\ncode\\n```\\n\\n* item")
            [('paragraph', 'Intro'), ('code', 'code'), ('list', '* item')]
        """
        if not content or not content.strip():
            return []
        
        blocks = []
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines between blocks
            if not stripped:
                i += 1
                continue
            
            # Check for code block: ```
            if stripped.startswith('```'):
                code_block, lines_consumed = self._extract_code_block(lines, i)
                if code_block:
                    blocks.append(('code', code_block))
                    i += lines_consumed
                    continue
            
            # Check for list item
            if re.match(r'^[\*\-]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
                list_block, lines_consumed = self._extract_list_block(lines, i)
                blocks.append(('list', list_block))
                i += lines_consumed
                continue
            
            # Otherwise it's a paragraph
            para_block, lines_consumed = self._extract_paragraph_block(lines, i)
            blocks.append(('paragraph', para_block))
            i += lines_consumed
        
        return blocks
    
    def _extract_code_block(self, lines: list, start_idx: int) -> tuple:
        """
        Extract a code block starting with ```.
        
        Phase 4: Code block extraction
        
        Args:
            lines: All lines
            start_idx: Index of opening ```
            
        Returns:
            (code_content, lines_consumed) or (None, 0) if not a code block
        """
        if not lines[start_idx].strip().startswith('```'):
            return None, 0
        
        # Extract language hint (if present)
        first_line = lines[start_idx].strip()
        language = first_line[3:].strip() if len(first_line) > 3 else ''
        
        # Find closing ```
        code_lines = []
        i = start_idx + 1
        
        while i < len(lines):
            if lines[i].strip().startswith('```'):
                # Found closing marker
                # Return code content and number of lines consumed
                code_content = '\n'.join(code_lines)
                return (language, code_content), i - start_idx + 1
            
            code_lines.append(lines[i])
            i += 1
        
        # No closing marker found - treat as regular text
        return None, 0
    
    def _extract_list_block(self, lines: list, start_idx: int) -> tuple:
        """
        Extract consecutive list items.
        
        Phase 4: List block extraction (improved from Phase 3)
        
        Args:
            lines: All lines
            start_idx: Index of first list item
            
        Returns:
            (list_content, lines_consumed)
        """
        list_lines = []
        i = start_idx
        
        while i < len(lines):
            stripped = lines[i].strip()
            
            # Empty line within list - keep it
            if not stripped:
                list_lines.append(lines[i])
                i += 1
                continue
            
            # List item line
            if re.match(r'^[\*\-]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
                list_lines.append(lines[i])
                i += 1
            else:
                # Not a list item - end of list block
                break
        
        return '\n'.join(list_lines), i - start_idx
    
    def _extract_paragraph_block(self, lines: list, start_idx: int) -> tuple:
        """
        Extract a paragraph block (continues until blank line or different block type).
        
        Phase 4: Paragraph extraction
        
        Args:
            lines: All lines
            start_idx: Index of first paragraph line
            
        Returns:
            (paragraph_content, lines_consumed)
        """
        para_lines = []
        i = start_idx
        
        while i < len(lines):
            stripped = lines[i].strip()
            
            # Empty line - end of paragraph
            if not stripped:
                break
            
            # Code block marker - end of paragraph
            if stripped.startswith('```'):
                break
            
            # List item - end of paragraph
            if re.match(r'^[\*\-]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
                break
            
            para_lines.append(lines[i])
            i += 1
        
        return '\n'.join(para_lines), i - start_idx
    
    def _is_list(self, content: str) -> bool:
        """
        Detect if content contains markdown list patterns.
        
        Detects:
        - Bullet lists: * item, - item
        - Numbered lists: 1. item, 2. item
        
        Args:
            content: Text to check
            
        Returns:
            True if content looks like a list
            
        Example:
            >>> parser._is_list("* item 1\\n* item 2")
            True
        """
        if not content:
            return False
        
        lines = content.strip().split('\n')
        
        # Check if majority of non-empty lines are list items
        list_lines = 0
        non_empty_lines = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            non_empty_lines += 1
            
            # Bullet list patterns: * item, - item
            if re.match(r'^[\*\-]\s+', line):
                list_lines += 1
            # Numbered list patterns: 1. item, 2. item
            elif re.match(r'^\d+\.\s+', line):
                list_lines += 1
        
        # If 70%+ of lines are list items, treat as a list
        if non_empty_lines > 0:
            return list_lines / non_empty_lines >= 0.7
        
        return False
    
    def _extract_list_items(self, content: str) -> list:
        """
        Extract list items from markdown content.
        
        Handles:
        - Bullet lists: * item, - item
        - Numbered lists: 1. item
        - Preserves inline markdown/HTML in items
        
        Args:
            content: Markdown list content
            
        Returns:
            List of item strings (with inline markdown parsed)
            
        Example:
            >>> parser._extract_list_items("* **bold** item\\n* `code` item")
            ['bold item', 'code item']  # With ANSI codes applied
        """
        items = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match bullet list item: * item or - item
            match = re.match(r'^[\*\-]\s+(.+)$', line)
            if match:
                item_text = match.group(1)
                # Parse inline markdown/HTML in the item
                parsed_item = self.parse_inline(item_text)
                items.append(parsed_item)
                continue
            
            # Match numbered list item: 1. item
            match = re.match(r'^\d+\.\s+(.+)$', line)
            if match:
                item_text = match.group(1)
                parsed_item = self.parse_inline(item_text)
                items.append(parsed_item)
                continue
        
        return items
    
    def _emit_list(self, content: str, display: 'zDisplay', indent: int = 0) -> None:
        """
        Extract list items and emit display.list() event.
        
        Phase 3: Emit proper list events instead of raw text
        Phase 5: Support indentation parameter
        
        Args:
            content: Markdown list content
            display: zDisplay instance
            indent: Indentation level (default: 0)
        """
        # Extract items (with inline parsing)
        items = self._extract_list_items(content)
        
        if not items:
            # Fallback to text if extraction failed
            parsed_content = self.parse_inline(content)
            self._emit_paragraph(parsed_content, indent)
            return
        
        # Detect list style (bullet vs numbered)
        first_line = content.strip().split('\n')[0].strip()
        style = 'number' if re.match(r'^\d+\.', first_line) else 'bullet'
        
        # Emit list event with indentation
        # Note: We're calling display.list() which will handle Terminal vs Bifrost
        display.list(items, style=style, indent=indent)
    
    def _emit_paragraph(self, content: str, indent: int = 0, color: str = None) -> None:
        """
        Emit a paragraph with indentation and optional color.
        
        Phase 5: Paragraph emission with indentation and color support
        
        Args:
            content: Parsed paragraph content (already has ANSI codes)
            indent: Indentation level (default: 0)
            color: Optional color override (ANSI code or None)
        """
        # Build indentation string
        indent_str = ' ' * (indent * 4) if indent > 0 else ''
        
        # Apply color if specified
        if color:
            # Map color names to ANSI codes
            from ....zSys.formatting.colors import Colors
            color_map = {
                'error': Colors.ZERROR,
                'success': Colors.ZSUCCESS,
                'warning': Colors.ZWARNING,
                'info': Colors.ZINFO,
                'primary': Colors.PRIMARY,
                'secondary': Colors.SECONDARY,
            }
            ansi_color = color_map.get(color.lower(), '')
            if ansi_color:
                content = f"{ansi_color}{content}{Colors.RESET}"
        
        # Print with indentation
        print(f"{indent_str}{content}")
    
    def _emit_code_block(self, block_data: tuple, display: 'zDisplay', indent: int = 0) -> None:
        """
        Emit a code block for Terminal display.
        
        Phase 4: Code block emission
        Phase 5: Support indentation parameter
        
        For Terminal mode:
        - Display with border/frame
        - Use distinct color (cyan/dim)
        - Preserve formatting
        
        Args:
            block_data: Tuple of (language, code_content)
            display: zDisplay instance
            indent: Indentation level (default: 0)
        """
        language, code_content = block_data
        
        # For Terminal mode, format as boxed code
        # Use ANSI cyan for code content
        ANSI_CYAN = '\033[36m'
        ANSI_DIM = '\033[2m'
        ANSI_RESET = '\033[0m'
        
        # Build indentation string
        indent_str = ' ' * (indent * 4) if indent > 0 else ''
        
        # Format with border (simple box drawing)
        lines = code_content.split('\n')
        
        # Top border
        print(f"{indent_str}{ANSI_DIM}╭{'─' * 60}╮{ANSI_RESET}")
        
        # Language label (if present)
        if language:
            print(f"{indent_str}{ANSI_DIM}│{ANSI_RESET} {ANSI_CYAN}{language}{ANSI_RESET}")
            print(f"{indent_str}{ANSI_DIM}├{'─' * 60}┤{ANSI_RESET}")
        
        # Code lines
        for line in lines:
            # Truncate long lines for terminal display
            display_line = line[:58] if len(line) > 58 else line
            print(f"{indent_str}{ANSI_DIM}│{ANSI_RESET} {ANSI_CYAN}{display_line}{ANSI_RESET}")
        
        # Bottom border
        print(f"{indent_str}{ANSI_DIM}╰{'─' * 60}╯{ANSI_RESET}")


# Utility function for easy access
def parse_markdown_inline(text: str) -> str:
    """
    Convenience function to parse inline markdown without creating a parser instance.
    
    Args:
        text: Raw markdown text
        
    Returns:
        ANSI-formatted text
        
    Example:
        >>> parse_markdown_inline("This is **bold** text")
        "This is \033[1mbold\033[0m text"
    """
    parser = MarkdownTerminalParser()
    return parser.parse_inline(text)
