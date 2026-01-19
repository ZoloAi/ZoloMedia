# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_outputs.py

"""
BasicOutputs - Foundation Event Package for zDisplay
====================================================

This is the MOST CRITICAL event package in the zDisplay subsystem. ALL 7 other
event packages depend on BasicOutputs for fundamental display operations.

Foundation Role
---------------
BasicOutputs is the FOUNDATION of the entire events system:
- **0 dependencies** - true foundation layer
- **59 references** across 7 event files
- **Used by ALL 7 other event packages** (100% dependency)

This makes BasicOutputs the highest-impact file in the events system. Any change
here affects every other event package.

Architecture - Dual-Mode I/O Pattern
------------------------------------
BasicOutputs implements the dual-mode I/O pattern that all events follow:

1. **GUI Mode (Bifrost):** Try to send clean JSON event via send_gui_event()
   - Returns True if successful
   - Event sent via WebSocket to GUI frontend
   - Structured data (label, color, style, etc.)

2. **Terminal Mode (Fallback):** Build formatted text output
   - If GUI mode not available or fails
   - Format text with colors, styles, indentation
   - Output via write_line() primitive

This pattern ensures:
- GUI users get rich, interactive displays
- Terminal users get formatted text with colors
- Graceful degradation (always works in terminal)

Layer Position
--------------
BasicOutputs occupies the Event Layer in the zDisplay architecture:

```
Layer 3: display_delegates.py (PRIMARY API)
    ↓
Layer 2: display_events.py (ORCHESTRATOR)
    ↓
Layer 2: events/display_event_outputs.py (BasicOutputs) ← THIS MODULE
    ↓
Layer 1: display_primitives.py (FOUNDATION I/O)
    ↓
Layer 0: zConfig (session) + zComm (WebSocket)
```

Dependency Graph
----------------
ALL 7 other event packages depend on BasicOutputs:

```
display_event_outputs.py (BasicOutputs) ← FOUNDATION (0 dependencies)
    ↑
    ├── display_event_inputs.py (BasicInputs)
    │   Uses: header() for selection prompts
    │
    ├── display_event_signals.py (Signals)
    │   Uses: header() for error/warning/success headers
    │
    ├── display_event_data.py (BasicData)
    │   Uses: header() for list/json display headers
    │
    ├── display_event_timebased.py (TimeBased)
    │   Uses: text() for progress bar labels
    │
    ├── display_event_advanced.py (AdvancedData)
    │   Uses: header() for zTable titles and pagination
    │
    ├── [REMOVED] display_event_auth.py (zAuthEvents)
    │   Auth UI now composed in zAuth subsystem using generic display events
    │
    └── display_event_system.py (zSystem)
        Uses: header() + text() for zDeclare, zSession, zCrumbs, zMenu, zDialog
```

Methods
-------
BasicOutputs provides 2 fundamental display methods:

1. **header(label, color, indent, style)** - Formatted section headers
   - Three styles: full (═), single (─), wave (~)
   - Centered text with configurable colors
   - Used by ALL 7 other event packages

2. **text(content, indent, break_after, break_message)** - Display text
   - Optional indentation
   - Optional break/pause for user acknowledgment
   - Used extensively by zSystem events

zCLI Integration
----------------
- **Initialized by:** display_events.py (zEvents.__init__)
- **Accessed via:** zcli.display.zEvents.BasicOutputs
- **Used by:** All 7 other event packages (composition)
- **No session access** - delegates to primitives layer

Usage Statistics
----------------
- **59 total references** across zDisplay codebase
- **7 dependent packages** (100% of other event packages)
- **2 fundamental methods** (header + text)
- **~280 lines** after industry-grade refactoring

Thread Safety
-------------
Not thread-safe. All display operations should occur on the main thread or
with appropriate synchronization.

Example
-------
```python
# Via display_events orchestrator:
events = zEvents(display_instance)
events.BasicOutputs.header("Section Title", color="CYAN", style="full")
events.BasicOutputs.text("Some content", indent=1, break_after=True)

# Direct usage (rare):
basic_outputs = BasicOutputs(display_instance)
basic_outputs.header("Error", color="RED", style="single")
```
"""

from zOS import Any, Optional, Tuple

# Import DRY helpers from primitives
from ..b_primitives.display_rendering_helpers import wrap_with_color, apply_indent_to_lines

# Import constants from centralized module
from ..display_constants import (
    DEFAULT_COLOR,  # PUBLIC
    _CHAR_DOUBLE_LINE,
    _CHAR_SINGLE_LINE,
    _CHAR_WAVE,
    _INDENT_WIDTH,
    _BASE_WIDTH,
    _EVENT_NAME_HEADER,
    _EVENT_NAME_TEXT,
    DEFAULT_BREAK_MESSAGE,  # PUBLIC
    _KEY_LABEL,
    _KEY_COLOR,
    _KEY_INDENT,
    _KEY_STYLE,
    _KEY_CONTENT,
    _KEY_BREAK,
    _KEY_BREAK_MESSAGE,
    _INDENT_STR,
)

# Module-specific style constants (public API for external use)
DEFAULT_STYLE_FULL = "full"
DEFAULT_STYLE_SINGLE = "single"
DEFAULT_STYLE_WAVE = "wave"

# BasicOutputs Class

class BasicOutputs:
    """Foundation event package providing fundamental output methods.
    
    This is the MOST CRITICAL event class in zDisplay. ALL 7 other event
    packages depend on BasicOutputs for their display operations.
    
    **Foundation Status:**
    - 0 dependencies (true foundation)
    - 59 references across 7 event files
    - Used by ALL 7 other event packages
    
    **Methods:**
    - header(): Formatted section headers (used by ALL 7 packages)
    - text(): Display text with break/pause (used by zSystem + TimeBased)
    
    **Pattern:**
    All methods implement dual-mode I/O (GUI-first, terminal fallback).
    """

    # Type hints for instance attributes
    display: Any  # Parent zDisplay instance
    zPrimitives: Any  # Primitives instance for I/O operations
    zColors: Any  # Colors instance for terminal styling

    def __init__(self, display_instance: Any) -> None:
        """Initialize BasicOutputs with parent display reference.
        
        Args:
            display_instance: Parent zDisplay instance providing primitives and colors
            
        Note:
            This is called by display_events.py (zEvents.__init__) during
            display initialization.
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors

    # Helper Methods

    def _build_indent(self, indent: int) -> str:
        """Build indentation string (DRY helper).
        
        Args:
            indent: Indentation level (0 = no indent)
            
        Returns:
            str: Indentation string (2 spaces per level)
        """
        return _INDENT_STR * indent
    
    def _apply_semantic(self, content: str, semantic: str) -> str:
        """Apply semantic rendering using primitives (DRY helper).
        
        Uses SemanticPrimitives to render content with semantic HTML element styling.
        This ensures consistent rendering whether using semantic argument or rich_text
        markdown parsing.
        
        Args:
            content: Text content to render
            semantic: Semantic type (e.g., "code", "strong", "em", "kbd", etc.)
            
        Returns:
            str: Formatted content with semantic styling applied
                 Returns original content if semantic type is unknown
        
        Example:
            >>> self._apply_semantic("ls -la", "code")
            '`ls -la`'
            >>> self._apply_semantic("Important", "strong")
            '**Important**'
        
        Note:
            Terminal mode: Applies markdown-style formatting
            Bifrost mode: Returns raw content (frontend wraps in HTML)
        """
        from ..display_semantic_primitives import SemanticPrimitives
        
        # Get the renderer for this semantic type
        renderer = getattr(SemanticPrimitives, f"render_{semantic}", None)
        if renderer:
            # Determine mode
            mode = "terminal" if self.display.mode in ["Terminal", "Walker", ""] else "bifrost"
            return renderer(content, mode)
        
        # Unknown semantic type - return content as-is
        return content
    
    def _convert_emojis_for_terminal(self, text: str) -> str:
        """
        DRY helper: Convert emojis to [description] for terminal accessibility.
        
        Used by ALL output events (header, text, rich_text) to ensure consistent
        emoji handling across the display system. This is the single source of truth
        for emoji conversion in Terminal mode.
        
        Only converts in Terminal mode; Bifrost uses emojis with aria-label.
        
        Args:
            text: Content that may contain emojis
        
        Returns:
            Text with emojis converted to [description] format for Terminal
        
        Example:
            "📱 Mobile" → "[mobile phone] Mobile" (Terminal)
            "📱 Mobile" → "📱 Mobile" (Bifrost, unchanged)
        """
        # Only convert in Terminal mode
        if self.display.mode not in ["Terminal", "Walker", ""]:
            return text
        
        try:
            from .....zSys.accessibility import get_emoji_descriptions
            emoji_desc = get_emoji_descriptions()
            
            # Regex to find emojis (Unicode emoji ranges)
            import re
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map
                "\U0001F1E0-\U0001F1FF"  # flags
                "\U00002600-\U000026FF"  # Miscellaneous Symbols
                "\U00002700-\U000027BF"  # Dingbats
                "\U0001F900-\U0001F9FF"  # Supplemental Symbols
                "\U0001FA70-\U0001FAFF"  # Symbols Extended-A
                "\U0000200D"            # Zero Width Joiner
                "]+",
                flags=re.UNICODE
            )
            
            def replacer(match):
                emoji = match.group(0)
                return emoji_desc.format_for_terminal(emoji)
            
            return emoji_pattern.sub(replacer, text)
        except Exception as e:
            # Fallback: return text unchanged if emoji system fails
            self.display.zcli.logger.warning(f"Emoji conversion failed: {e}")
            return text
    
    def _parse_markdown(self, content: str) -> str:
        """Parse markdown syntax using semantic primitives (DRY helper).
        
        Parses common markdown inline syntax and applies semantic rendering
        using SemanticPrimitives. This ensures rich_text markdown parsing
        uses the SAME rendering logic as the semantic argument.
        
        Markdown Syntax Parsed:
            - ```code blocks``` → multi-line code blocks
            - `code` → inline code
            - **strong** → bold/strong emphasis
            - *em* → italic/emphasis
            - ==mark== → highlighted text
            - ~~del~~ → strikethrough/deleted text
        
        Args:
            content: Text with markdown syntax
            
        Returns:
            str: Content with markdown parsed and semantic formatting applied
        
        Example:
            >>> self._parse_markdown("Run `ls -la` to see **all** files")
            # Terminal: "Run `ls -la` to see **all** files" (markdown as-is currently)
            # Bifrost: Will parse and wrap in HTML
        
        Note:
            Parsing order matters to prevent conflicts:
            1. Code blocks (highest priority - multi-line before inline)
            2. Inline code (don't parse markers inside code)
            3. Strong (before em to handle ** before *)
            4. Em
            5. Mark
            6. Del
        """
        import re
        from ..b_primitives.display_semantic_primitives import SemanticPrimitives
        
        # Determine mode
        mode = "terminal" if self.display.mode in ["Terminal", "Walker", ""] else "bifrost"
        
        # Parse in order: code blocks, inline code, strong, em, mark, del (prevent conflicts)
        
        # 1. Code blocks: ```language\ncode\n``` (highest priority - must be before inline code)
        content = re.sub(
            r'```(\w*)\n?(.*?)\n?```',
            lambda m: SemanticPrimitives.render_code_block(m.group(2), m.group(1), mode),
            content,
            flags=re.DOTALL
        )
        
        # 2. Inline code: `text`
        content = re.sub(
            r'`([^`]+)`',
            lambda m: SemanticPrimitives.render_code(m.group(1), mode),
            content
        )
        
        # 3. Bold: **text** (before * to prevent conflict)
        content = re.sub(
            r'\*\*([^*]+)\*\*',
            lambda m: SemanticPrimitives.render_strong(m.group(1), mode),
            content
        )
        
        # 4. Italic: *text*
        content = re.sub(
            r'\*([^*]+)\*',
            lambda m: SemanticPrimitives.render_em(m.group(1), mode),
            content
        )
        
        # 5. Highlight: ==text==
        content = re.sub(
            r'==([^=]+)==',
            lambda m: SemanticPrimitives.render_mark(m.group(1), mode),
            content
        )
        
        # 6. Strikethrough: ~~text~~
        content = re.sub(
            r'~~([^~]+)~~',
            lambda m: SemanticPrimitives.render_del(m.group(1), mode),
            content
        )
        
        return content

    # Output Methods

    def header(self, label: str, color: str = DEFAULT_COLOR, indent: int = 0, style: str = DEFAULT_STYLE_FULL, semantic: Optional[str] = None, **kwargs) -> None:
        """Display formatted section header with styling.
        
        FOUNDATION METHOD - Used by ALL 7 other event packages for displaying
        section headers with consistent styling.
        
        Args:
            label: Header text to display
            color: Color name for styling
            indent: Indentation level
            style: Header line style ("full", "single", "wave")
            semantic: Optional semantic HTML element type
            **kwargs: Additional parameters for GUI mode
        """
        # Resolve dynamic content
        label = self._resolve_header_label(label, semantic, kwargs)
        
        # Try GUI mode first
        if self._try_header_gui_mode(label, color, indent, style, semantic, kwargs):
            return
        
        # Terminal mode - render formatted header
        self._render_header_terminal(label, color, indent, style)

    def _resolve_header_label(self, label: str, semantic: Optional[str], kwargs: dict) -> str:
        """Resolve %variables, &functions, semantic formatting, and emoji conversion in label."""
        # Resolve %variable references
        if "%" in label:
            from zOS.L2_Core.g_zParser.parser_modules.parser_functions import resolve_variables
            context = kwargs.get('_context', {})
            label = resolve_variables(label, self.display.zcli, context)
        
        # Resolve &function calls
        if "&" in label:
            from zOS.L2_Core.g_zParser.parser_modules.parser_functions import resolve_function_call
            label = resolve_function_call(label, self.display.zcli)
        
        # Apply semantic rendering for terminal mode
        if semantic and self.display.mode in ["Terminal", "Walker", ""]:
            label = self._apply_semantic(label, semantic)
        
        # Convert emojis to [description] for terminal accessibility (DRY helper)
        label = self._convert_emojis_for_terminal(label)
        
        return label

    def _try_header_gui_mode(self, label: str, color: str, indent: int, style: str, 
                             semantic: Optional[str], kwargs: dict) -> bool:
        """Try to send header as GUI event, return True if successful."""
        event_data = {
            _KEY_LABEL: label,
            _KEY_COLOR: color,
            _KEY_INDENT: indent,
            _KEY_STYLE: style,
            **kwargs
        }
        
        if semantic:
            event_data["semantic"] = semantic
        
        return self.zPrimitives.send_gui_event(_EVENT_NAME_HEADER, event_data)

    def _render_header_terminal(self, label: str, color: str, indent: int, style: str) -> None:
        """Render header for terminal mode with width-safe formatting."""
        # Decode Unicode escapes for terminal display (preserves ASCII-safe storage)
        from zlsp.core.parser.parser_modules.escape_processors import decode_unicode_escapes
        if '\\u' in label or '\\U' in label:
            label = decode_unicode_escapes(label)
        
        term_width = self.zPrimitives.get_terminal_columns()
        indent_str, inner_width = self._calculate_header_dimensions(indent, term_width)
        
        if inner_width <= 0:
            self.zPrimitives.line("")
            return
        
        sep = self._get_header_separator(style)
        line_out = self._build_header_line(label, color, inner_width, sep)
        
        content = f"{indent_str}{line_out}"
        self.zPrimitives.line(content)

    def _calculate_header_dimensions(self, indent: int, term_width: int) -> Tuple[str, int]:
        """Calculate indent string and inner width for header."""
        indent_str = self._build_indent(indent)
        if len(indent_str) >= term_width:
            indent_str = indent_str[: max(0, term_width - 1)]
        
        inner_width = term_width - len(indent_str)
        return indent_str, inner_width

    def _get_header_separator(self, style: str) -> str:
        """Get separator character based on style."""
        if style == DEFAULT_STYLE_FULL:
            return "="
        elif style == DEFAULT_STYLE_SINGLE:
            return "-"
        elif style == DEFAULT_STYLE_WAVE:
            return "*"
        else:
            return "-"

    def _build_header_line(self, label: str, color: str, inner_width: int, sep: str) -> str:
        """Build the header line with title, color, and separators."""
        title = (label or "").strip()
        
        if not title:
            return sep * inner_width
        
        # Format title with appropriate width
        title_plain = self._format_header_title(title, inner_width)
        title_colored = self._apply_header_color(title, title_plain, color, inner_width)
        
        # Center the title with separators
        remaining = inner_width - len(title_plain)
        if remaining >= 2:
            left = remaining // 2
            right = remaining - left
            return (sep * left) + title_colored + (sep * right)
        else:
            return title_colored + (sep * max(0, remaining))

    def _format_header_title(self, title: str, inner_width: int) -> str:
        """Format title text to fit within available width."""
        if inner_width >= 3:
            title_core_max = inner_width - 2
            title_core = title[:title_core_max]
            return f" {title_core} "
        else:
            return title[:inner_width]

    def _apply_header_color(self, title: str, title_plain: str, color: str, inner_width: int) -> str:
        """Apply color formatting to header title."""
        if not color or color == DEFAULT_COLOR:
            return title_plain
        
        try:
            if isinstance(color, str) and not color.startswith('\033'):
                color_code = getattr(self.zColors, color.upper(), self.zColors.RESET)
            else:
                color_code = color
            
            reset_code = getattr(self.zColors, "RESET", "")
            title_core = title[:(inner_width - 2)] if inner_width >= 3 else title[:inner_width]
            
            if inner_width >= 3:
                return f" {color_code}{title_core}{reset_code} "
            else:
                return f"{color_code}{title_plain}{reset_code}"
        except Exception:
            return title_plain

    def text(
        self, 
        content: str, 
        indent: int = 0, 
        pause: bool = False,
        break_message: Optional[str] = None,
        break_after: Optional[bool] = None,
        semantic: Optional[str] = None,
        _context: Optional[dict] = None,  # NEW v1.5.12: Context for %data.* resolution
        **kwargs  # Additional parameters (e.g., 'class' for CSS classes)
    ) -> None:
        """Display text with optional indentation and pause.
        
        FOUNDATION METHOD - Used extensively by zSystem events and TimeBased for
        displaying content with optional user acknowledgment.
        
        Implements dual-mode I/O pattern:
        1. GUI Mode: Send clean JSON event with pause metadata
        2. Terminal Mode: Display text, optionally pause for Enter key
        
        Args:
            content: Text content to display
            indent: Indentation level (default: 0)
                    Each level = 2 spaces
            pause: Pause for user acknowledgment (default: False)
                         If True, displays break message and waits for Enter
            break_message: Custom break message (default: "Press Enter to continue...")
                          Only used if pause is True
            break_after: Legacy parameter - use 'pause' instead
                         Maintained for backward compatibility
            semantic: Optional semantic HTML element type (e.g., "code", "strong", "kbd")
                     Terminal: Applies markdown-style formatting
                     Bifrost: Passed to frontend for HTML wrapping
            **kwargs: Additional parameters (e.g., 'class' for zBifrost CSS classes)
                      Ignored in Terminal mode, passed through in GUI mode
                          
        Returns:
            None
            
        Example:
            self.BasicOutputs.text("Operation complete")
            self.BasicOutputs.text("Details...", indent=1, pause=False)
            self.BasicOutputs.text("Warning!", pause=True, break_message="Press Enter to proceed")
            self.BasicOutputs.text("Styled text", indent=0, class="zLead")
            self.BasicOutputs.text("pip install requests", semantic="code")  # NEW
            self.BasicOutputs.text("Press Enter", semantic="kbd")  # NEW
            
        Note:
            Used by: zSystem (zDeclare, zSession, zCrumbs, zMenu),
                     TimeBased (progress bar labels, spinner text)
        """
        # Handle backward compatibility: break_after overrides pause if provided
        should_break = break_after if break_after is not None else pause
        
        # NEW: Resolve %variable references (e.g., %session.username, %myvar, %data.user.name)
        # CRITICAL: Must happen BEFORE sending GUI event!
        if "%" in content:
            from zOS.L2_Core.g_zParser.parser_modules.parser_functions import resolve_variables
            content = resolve_variables(content, self.display.zcli, _context)
        
        # NEW: Resolve &function calls (e.g., &zNow, &zNow('date'))
        if "&" in content:
            from zOS.L2_Core.g_zParser.parser_modules.parser_functions import resolve_function_call
            content = resolve_function_call(content, self.display.zcli)
        
        # Apply semantic rendering if specified (terminal mode only)
        if semantic and self.display.mode in ["Terminal", "Walker", ""]:
            content = self._apply_semantic(content, semantic)
        
        # Convert emojis to [description] for terminal accessibility (DRY helper)
        content = self._convert_emojis_for_terminal(content)
        
        # Build event dict with all parameters (AFTER variable resolution)
        # Keep escape sequences as-is for Bifrost to decode client-side
        event_data = {
            _KEY_CONTENT: content,
            _KEY_INDENT: indent,
            _KEY_BREAK: should_break,
            _KEY_BREAK_MESSAGE: break_message,
            **kwargs  # Pass through any additional parameters (like 'class')
        }
        
        # Add semantic to event_data for Bifrost (if provided)
        if semantic:
            event_data["semantic"] = semantic
        
        # Try GUI mode first - send clean event with break metadata
        if self.zPrimitives.send_gui_event(_EVENT_NAME_TEXT, event_data):
            return  # GUI event sent successfully

        # Terminal mode - output text and optionally pause
        # Decode Unicode escapes for terminal display (preserves ASCII-safe storage in .zolo files)
        if '\\u' in content or '\\U' in content:
            from zlsp.core.parser.parser_modules.escape_processors import decode_unicode_escapes
            content = decode_unicode_escapes(content)
        
        # Apply indentation
        if indent > 0:
            indent_str = self._build_indent(indent)
            content = f"{indent_str}{content}"

        # Display text using primitive
        self.zPrimitives.line(content)

        # Auto-break if enabled (pause for user input)
        if should_break:
            # Build break message
            message = break_message or DEFAULT_BREAK_MESSAGE
            if indent > 0:
                indent_str = self._build_indent(indent)
                message = f"{indent_str}{message}"

            # Display message and wait for Enter using primitives
            self.zPrimitives.line(message)
            self.zPrimitives.read_string("")  # Wait for Enter (discard result)

    def rich_text(
        self,
        content: str,
        indent: int = 0,
        pause: bool = False,
        break_message: Optional[str] = None,
        format: str = "markdown",
        **kwargs
    ) -> None:
        """Display rich text with inline formatting (markdown-style).
        
        NEW EVENT - Supports inline semantic markup using markdown syntax.
        This enables mixing bold, italic, code, and other inline styles within
        a single text block.
        
        Markdown Syntax Supported:
            - `code` -> <code> inline code
            - **bold** -> <strong> strong emphasis
            - *italic* -> <em> emphasis
            - ~~strikethrough~~ -> <del> deleted text
            - ==highlight== -> <mark> highlighted text
            - [text](url) -> <a> hyperlinks
        
        Dual-Mode Behavior:
            - Terminal: Parses markdown and displays with semantic formatting
                       (uses same SemanticPrimitives as semantic argument)
            - Bifrost: Sends markdown with format="markdown" for HTML parsing
        
        Args:
            content: Text with markdown inline formatting
            indent: Indentation level (default: 0)
            pause: Pause for user acknowledgment (default: False)
            break_message: Custom break message if pause=True
            format: Format type (default: "markdown")
            **kwargs: Additional parameters passed to Bifrost
        
        Returns:
            None
        
        Examples:
            # Simple inline code
            self.BasicOutputs.rich_text("Run `ls -la` to see files")
            
            # Multiple styles
            self.BasicOutputs.rich_text(
                "**Important:** Use `pip install` for *Python* packages"
            )
            
            # With indentation
            self.BasicOutputs.rich_text(
                "See the `config.yaml` file for **settings**",
                indent=1
            )
            
            # With link
            self.BasicOutputs.rich_text(
                "Visit [our docs](https://example.com) for help"
            )
        
        Note:
            Terminal mode parses markdown using SemanticPrimitives.
            This ensures consistency with semantic argument rendering.
        """
        # Build event dict
        event_data = {
            _KEY_CONTENT: content,
            _KEY_INDENT: indent,
            _KEY_BREAK: pause,
            _KEY_BREAK_MESSAGE: break_message,
            "format": format,  # Tell Bifrost this is markdown
            **kwargs
        }
        
        # Try GUI mode first - send clean event
        if self.zPrimitives.send_gui_event("rich_text", event_data):
            return  # GUI event sent successfully
        
        # Terminal mode - parse markdown to ANSI and display
        # Phase 1-3: Use markdown parser (inline + lists + HTML)
        from .markdown_terminal_parser import MarkdownTerminalParser
        
        # Step 1: Decode Unicode escapes BEFORE parsing (preserves ASCII-safe storage in .zolo files)
        if '\\u' in content or '\\U' in content:
            from zlsp.core.parser.parser_modules.escape_processors import decode_unicode_escapes
            content = decode_unicode_escapes(content)
        
        # Step 2: Convert emojis to [description] for terminal accessibility (DRY helper)
        content = self._convert_emojis_for_terminal(content)
        
        # Step 3: Parse markdown (will emit list events if content is a list, otherwise prints)
        # Phase 3: Parser can now detect lists and call display.list() automatically
        # Phase 5: Pass indentation and color parameters
        parser = MarkdownTerminalParser()
        # Extract color from kwargs if present
        color = kwargs.get('color', None)
        parser.parse(content, display=self.display, indent=indent, color=color)
        
        # Note: Parser handles output (either via display.list() or print())
        # Indentation is handled by the display events themselves
        
        # Auto-break if enabled
        if pause:
            message = break_message or DEFAULT_BREAK_MESSAGE
            if indent > 0:
                indent_str = self._build_indent(indent)
                message = f"{indent_str}{message}"
            self.zPrimitives.line(message)
            self.zPrimitives.read_string("")  # Wait for Enter
