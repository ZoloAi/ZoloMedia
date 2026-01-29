"""
Markdown Terminal Parser - Complete zMD Terminal Orchestrator

Parses markdown/HTML content and converts it to ANSI-formatted text for Terminal mode.
Acts as a mini-orchestrator within the zMD event, intelligently routing content to
appropriate zDisplay events (text, list, code blocks).

Features (Phases 1-6):
- Phase 1: Parse inline markdown: **bold**, *italic*, `code` → ANSI
- Phase 2: Strip HTML tags and map zTheme classes → ANSI colors
- Phase 3: Extract markdown lists → display.list() events
- Phase 4: Block-level parsing (paragraphs, lists, code blocks)
- Phase 5: Indentation/color parameters + robust error handling
- Phase 6: Strip markdown links (Bifrost-only feature) → plain text for Terminal

Author: zOS Framework
Version: 2.1.0 (Phase 6 Complete - Terminal/Bifrost Alignment)
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
        
        # NOTE: Emoji conversion now happens upstream in display_event_outputs.py
        # via the DRY _convert_emojis_for_terminal() helper for ALL events (header, text, rich_text)
        
        # Phase 1: Process markdown in order: code first (to protect backticks), then links, then bold, then italic
        # This prevents interference between patterns
        
        # 1. Code blocks: `code` → cyan
        text = self._convert_code(text)
        
        # 2. Links: [text](url) → text (strip URL for Terminal)
        # Special case: [*](url) → * with info color (footnote style)
        text = self._convert_links(text)
        
        # 3. Bold: **text** → bold
        text = self._convert_bold(text)
        
        # 4. Italic: *text* → italic/dim
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
    
    def _convert_links(self, text: str) -> str:
        """
        Convert markdown links to plain text with optional color.
        
        Phase 7: Markdown link parsing
        
        Handles:
        - [text](url) → text (strip URL for Terminal)
        - [*](url) → * with info color (footnote style)
        
        Pattern: [text](url) → text
        
        Args:
            text: Text with markdown links
            
        Returns:
            Text with links converted (URLs stripped, footnote asterisks colored)
        """
        # Pattern: [text](url)
        pattern = r'\[([^\]]+)\]\([^)]+\)'
        
        def replacer(match):
            link_text = match.group(1)
            
            # Special case: footnote-style link [*](url) → * with info color
            if link_text == '*':
                try:
                    from .....zSys.formatting.ztheme_to_ansi import (
                        map_ztheme_classes_to_ansi,
                        get_reset_code
                    )
                    # Apply zLink-info color (info blue)
                    ansi_codes = map_ztheme_classes_to_ansi(['zLink-info'])
                    if ansi_codes:
                        return f"{ansi_codes}*{get_reset_code()}"
                except ImportError:
                    pass
                # Fallback: just return asterisk
                return '*'
            
            # Regular link: just return the text (URL stripped for Terminal)
            return link_text
        
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
    
    # NOTE: Emoji conversion removed - now handled upstream in display_event_outputs.py
    # via the DRY _convert_emojis_for_terminal() helper for consistency across ALL events
    
    def _strip_html_with_color_mapping(self, text: str) -> str:
        """
        Strip HTML tags and map zTheme classes to ANSI colors.
        
        Phase 2: HTML class mapping
        Phase 7: Nested HTML tag support (recursive processing)
        
        Handles:
        - <span class="zText-error">text</span> → red ANSI text
        - <span class="zText-error zFont-bold">text</span> → red + bold ANSI
        - <div class="zCallout">text</div> → text (strip non-color classes)
        - <sup><a href="#anchor" class="zLink-info">*</a></sup> → * (with info color)
        - Nested HTML tags (recursively processed)
        
        Args:
            text: Text potentially containing HTML tags
            
        Returns:
            Text with HTML stripped and classes mapped to ANSI
            
        Example:
            >>> parser._strip_html_with_color_mapping('<span class="zText-error">Error!</span>')
            '\033[38;5;203mError!\033[0m'  # Red ANSI
            >>> parser._strip_html_with_color_mapping('<sup><a href="#footnote" class="zLink-info">*</a></sup>')
            '\033[38;5;111m*\033[0m'  # Info color (blue) asterisk
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
        
        # Recursively process nested HTML tags
        # Pattern: <tag attributes>content</tag>
        # Handles: class="...", href="...", style="...", and other attributes
        pattern = r'<(\w+)((?:\s+[^>]*)?)>(.+?)</\1>'
        
        def process_tag(match):
            """Process a single HTML tag (recursively handles nested tags)."""
            tag_name = match.group(1)
            attrs_str = match.group(2) or ''
            content = match.group(3)
            
            # Recursively process nested tags in content first (innermost tags first)
            # This ensures inner tags are processed before outer tags
            if '<' in content:
                # Recursively call the main function on the content
                content = self._strip_html_with_color_mapping(content)
            
            # Extract attributes
            class_match = re.search(r'class=["\']([^"\']+)["\']', attrs_str)
            href_match = re.search(r'href=["\']([^"\']+)["\']', attrs_str)
            
            classes_str = class_match.group(1) if class_match else ''
            href = href_match.group(1) if href_match else ''
            
            # Handle anchor tags (<a>) - show link text, optionally with href in Terminal
            if tag_name == 'a':
                # For Terminal mode, we can show the link text with optional href
                # For now, just show the text (Bifrost will handle the actual link)
                link_text = content
                
                # Apply color classes if present
                if classes_str:
                    classes = classes_str.split()
                    ansi_codes = map_ztheme_classes_to_ansi(classes)
                    if ansi_codes:
                        return f"{ansi_codes}{link_text}{get_reset_code()}"
                
                # No classes - just return link text
                return link_text
            
            # Handle other tags with class attributes
            if classes_str:
                classes = classes_str.split()
                ansi_codes = map_ztheme_classes_to_ansi(classes)
                
                if ansi_codes:
                    # Apply ANSI codes to content
                    return f"{ansi_codes}{content}{get_reset_code()}"
            
            # No recognized classes - just return content without tags
            return content
        
        # Process all HTML tags recursively
        # Keep processing until no more tags are found
        max_iterations = 10  # Safety limit for deeply nested tags
        iteration = 0
        while '<' in text and iteration < max_iterations:
            new_text = re.sub(pattern, process_tag, text)
            if new_text == text:  # No more changes
                break
            text = new_text
            iteration += 1
        
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
                    elif block_type == 'heading':
                        # block_content is (level, text) tuple
                        level, text = block_content
                        # Parse inline markdown in heading text
                        parsed_text = self.parse_inline(text)
                        display.header(parsed_text, indent=level)
                    elif block_type == 'blockquote':
                        self._emit_blockquote(block_content, display, indent)
                    elif block_type == 'list':
                        self._emit_list(block_content, display, indent)
                    elif block_type == 'paragraph':
                        # Parse inline markdown and output
                        # Links are now handled in parse_inline() with special footnote support
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
        
        NEW: zMD semantic multiline handling
        - \x1F (Unit Separator) = Natural YAML multiline → line break (same paragraph)
        - \n = Explicit escape sequence → paragraph break (double \n\n in Terminal)
        
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
        
        # NOTE: Inline code protection happens earlier in display_event_outputs.py
        # before decode_unicode_escapes() is called, so backticks content is already literal here
        
        # STEP 1: Process semantic distinction BEFORE splitting
        # Convert explicit \n to double newlines for paragraph breaks
        content = content.replace('\n', '\n\n')
        
        # STEP 2: Convert \x1F (YAML multilines) to single newline (line breaks within paragraph)
        content = content.replace('\x1F', '\n')
        
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
            
            # Check for heading: # through ######
            # Accept both "# Title" (standard) and "#Title" (lenient)
            heading_match = re.match(r'^(#{1,6})\s*(.+)$', stripped)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                blocks.append(('heading', (level, text)))
                i += 1
                continue
            
            # Check for blockquote: > text
            if stripped.startswith('>'):
                quote_block, lines_consumed = self._extract_blockquote_block(lines, i)
                blocks.append(('blockquote', quote_block))
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
    
    def _extract_blockquote_block(self, lines: list, start_idx: int) -> tuple:
        """
        Extract consecutive blockquote lines starting with >.
        
        Args:
            lines: All lines
            start_idx: Index of first blockquote line
            
        Returns:
            (quote_content, lines_consumed)
        """
        quote_lines = []
        i = start_idx
        
        while i < len(lines):
            stripped = lines[i].strip()
            
            # Empty line within quote - keep it if next line is still a quote
            if not stripped:
                # Look ahead to see if quote continues
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('>'):
                    quote_lines.append(lines[i])
                    i += 1
                    continue
                else:
                    # Quote block ends
                    break
            
            # Blockquote line: starts with >
            if stripped.startswith('>'):
                quote_lines.append(lines[i])
                i += 1
            else:
                # Not a blockquote line - end of block
                break
        
        return '\n'.join(quote_lines), i - start_idx
    
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
    
    def _emit_blockquote(self, content: str, display: 'zDisplay', indent: int = 0) -> None:
        """
        Extract blockquote content and emit with visual quote styling.
        
        Terminal rendering uses:
        - Left border (│) for visual distinction
        - Indentation
        - Dim color for the border
        
        Args:
            content: Markdown blockquote content (lines starting with >)
            display: zDisplay instance
            indent: Indentation level (default: 0)
        """
        # Extract lines and remove > prefix
        lines = content.strip().split('\n')
        quote_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('>'):
                # Remove > and optional space
                quote_text = stripped[1:].strip()
                # Parse inline markdown in quote line
                parsed_line = self.parse_inline(quote_text) if quote_text else ''
                quote_lines.append(parsed_line)
            elif not stripped:
                # Empty line within quote
                quote_lines.append('')
        
        # Render with styled border
        indent_str = ' ' * (indent * 4) if indent > 0 else ''
        border = f"{self.ANSI_DIM}│{self.ANSI_RESET}"
        
        for line in quote_lines:
            print(f"{indent_str}{border} {line}")
    
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
            content: Parsed paragraph content (already has ANSI codes, links already stripped)
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
    
    def _apply_zolo_colors(self, code: str) -> str:
        """
        Apply fast ANSI coloring to .zolo syntax without Pygments.
        
        Performance-focused: Uses simple regex replacements instead of full lexing.
        
        Color scheme (monokai-inspired):
        - Root keys (capitalized): Pink/Magenta (\033[95m)
        - Display events (z*): Cyan (\033[96m)
        - Metadata (_z*): Yellow (\033[93m)
        - Properties (lowercase keys): Green (\033[92m)
        - Values: White/Default
        - Comments: Dim gray (\033[2m\033[37m)
        """
        import re
        
        ANSI_RESET = '\033[0m'
        ANSI_PINK = '\033[95m'      # Root keys
        ANSI_CYAN = '\033[96m'      # Display events  
        ANSI_YELLOW = '\033[93m'    # Metadata
        ANSI_GREEN = '\033[92m'     # Properties
        ANSI_DIM_GRAY = '\033[2m\033[37m'  # Comments
        
        lines = code.split('\n')
        colored_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                colored_lines.append(line)
                continue
            
            # Comments
            if line.strip().startswith('#'):
                colored_lines.append(f"{ANSI_DIM_GRAY}{line}{ANSI_RESET}")
                continue
            
            # Try to match key: value pattern
            match = re.match(r'^(\s*)([_~^]?[a-zA-Z][a-zA-Z0-9_]*)(\([^)]+\))?([\*!]?)\s*:\s*(.*)', line)
            if match:
                indent, key, type_hint, modifier, value = match.groups()
                
                # Determine key color based on pattern
                if key[0].isupper():
                    # Root key (capitalized)
                    key_color = ANSI_PINK
                elif key.startswith('z') and len(key) > 1 and key[1].isupper():
                    # Display event (zH1, zMD, etc.)
                    key_color = ANSI_CYAN
                elif key.startswith('_z'):
                    # Metadata (_zClass, _zStyle)
                    key_color = ANSI_YELLOW
                else:
                    # Regular property
                    key_color = ANSI_GREEN
                
                # Rebuild line with colors
                colored_line = f"{indent}{key_color}{key}{ANSI_RESET}"
                if type_hint:
                    colored_line += f"{ANSI_DIM_GRAY}{type_hint}{ANSI_RESET}"
                if modifier:
                    colored_line += f"{ANSI_YELLOW}{modifier}{ANSI_RESET}"
                colored_line += f": {value}"
                
                colored_lines.append(colored_line)
            else:
                # No pattern match, keep as-is
                colored_lines.append(line)
        
        return '\n'.join(colored_lines)
    
    def _emit_code_block(self, block_data: tuple, display: 'zDisplay', indent: int = 0) -> None:
        """
        Emit a code block for Terminal display with syntax highlighting.
        
        Phase 4: Code block emission
        Phase 5: Support indentation parameter
        Phase 5.1: Wider code blocks with line wrapping
        Phase 6: Pygments syntax highlighting with fallback
        
        For Terminal mode:
        - Display with border/frame
        - Syntax highlighting via Pygments (if available)
        - Fallback to mono-color cyan if Pygments fails
        - Preserve formatting with line wrapping
        
        Args:
            block_data: Tuple of (language, code_content)
            display: zDisplay instance
            indent: Indentation level (default: 0)
        """
        import textwrap
        import re
        
        language, code_content = block_data
        
        # Debug: Log language detection
        if hasattr(display, 'zcli') and hasattr(display.zcli, 'logger'):
            display.zcli.logger.debug(f"[MarkdownParser] Code block detected - language='{language}', length={len(code_content)}")
        
        # ANSI codes for border/UI elements
        ANSI_DIM = '\033[2m'
        ANSI_RESET = '\033[0m'
        ANSI_CYAN = '\033[36m'  # Fallback color
        
        # Build indentation string
        indent_str = ' ' * (indent * 4) if indent > 0 else ''
        
        # Code block width: 100 chars (wider, but still readable)
        BOX_WIDTH = 100
        CONTENT_WIDTH = 98  # Minus 2 for border/padding
        
        # Try Pygments syntax highlighting first
        highlighted_code = None
        
        try:
            # TEMPORARY: Skip Pygments for .zolo due to performance issues
            # Use fast manual ANSI coloring instead
            if language and language.lower() == 'zolo':
                if hasattr(display, 'zcli') and hasattr(display.zcli, 'logger'):
                    display.zcli.logger.debug(f"[MarkdownParser] Using fast manual coloring for .zolo")
                
                # Simple ANSI coloring for .zolo syntax
                highlighted_code = self._apply_zolo_colors(code_content)
                
                if hasattr(display, 'zcli') and hasattr(display.zcli, 'logger'):
                    has_ansi = '\033[' in highlighted_code
                    display.zcli.logger.debug(f"[MarkdownParser] Manual coloring complete - has_ansi={has_ansi}")
            else:
                from pygments import highlight
                from pygments.lexers import get_lexer_by_name, TextLexer
                from pygments.formatters import Terminal256Formatter
                from pygments.util import ClassNotFound
                
                # Get lexer for language, fallback to text if unknown
                try:
                    lexer = get_lexer_by_name(language or 'text', stripall=True)
                except (ClassNotFound, ImportError) as e:
                    if hasattr(display, 'zcli') and hasattr(display.zcli, 'logger'):
                        display.zcli.logger.debug(f"[MarkdownParser] Lexer load failed: {e}, using TextLexer")
                    lexer = TextLexer()
                
                # Highlight with Pygments (256-color terminal support)
                formatter = Terminal256Formatter(style='monokai')
                highlighted_code = highlight(code_content, lexer, formatter)
                
                if hasattr(display, 'zcli') and hasattr(display.zcli, 'logger'):
                    has_ansi = '\033[' in highlighted_code or '\x1b[' in highlighted_code
                    display.zcli.logger.debug(f"[MarkdownParser] Pygments highlighting complete - has_ansi={has_ansi}, length={len(highlighted_code)}")
            
        except (ImportError, Exception) as e:
            # Pygments not available or failed - use fallback
            if hasattr(display, 'zcli') and hasattr(display.zcli, 'logger'):
                display.zcli.logger.debug(f"[MarkdownParser] Highlighting failed: {e}")
            highlighted_code = None
        
        # If Pygments failed, use mono-color fallback
        if highlighted_code is None:
            if hasattr(display, 'zcli') and hasattr(display.zcli, 'logger'):
                display.zcli.logger.debug(f"[MarkdownParser] Using fallback cyan coloring")
            highlighted_code = f"{ANSI_CYAN}{code_content}{ANSI_RESET}"
        
        # Split into lines for border rendering
        lines = highlighted_code.rstrip().split('\n')
        
        # Top border
        print(f"{indent_str}{ANSI_DIM}╭{'─' * BOX_WIDTH}╮{ANSI_RESET}")
        
        # Language label (if present)
        if language:
            # Display language name in cyan
            lang_label = f" {language} "
            print(f"{indent_str}{ANSI_DIM}│{ANSI_RESET}{ANSI_CYAN}{lang_label.ljust(BOX_WIDTH)}{ANSI_RESET}{ANSI_DIM}│{ANSI_RESET}")
            print(f"{indent_str}{ANSI_DIM}├{'─' * BOX_WIDTH}┤{ANSI_RESET}")
        
        # Helper to calculate visible length (excluding ANSI codes)
        def visible_length(text):
            """Calculate visible length of text, excluding ANSI escape codes."""
            ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
            return len(ansi_escape.sub('', text))
        
        # Code lines (already highlighted by Pygments)
        for line in lines:
            vis_len = visible_length(line)
            
            # If line is too long, we need to wrap it
            # Note: Wrapping highlighted text is complex, so we truncate for now
            if vis_len > CONTENT_WIDTH:
                # For highlighted text, wrapping is complex
                # Simple approach: truncate and add ellipsis
                # TODO: Implement proper wrapping that preserves ANSI codes
                display_line = line[:CONTENT_WIDTH-3] + '...'
                padding = ''
            else:
                display_line = line
                # Pad with spaces to align right border
                padding = ' ' * (CONTENT_WIDTH - vis_len)
            
            print(f"{indent_str}{ANSI_DIM}│{ANSI_RESET} {display_line}{padding} {ANSI_DIM}│{ANSI_RESET}")
        
        # Bottom border
        print(f"{indent_str}{ANSI_DIM}╰{'─' * BOX_WIDTH}╯{ANSI_RESET}")


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
