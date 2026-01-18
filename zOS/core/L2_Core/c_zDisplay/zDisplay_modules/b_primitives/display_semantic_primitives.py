# zCLI/subsystems/zDisplay/zDisplay_modules/display_semantic_primitives.py

"""
Semantic Rendering Primitives for zDisplay - Foundation Layer 0.5.

This module provides foundational semantic HTML element rendering primitives.
It serves as the SINGLE SOURCE OF TRUTH for how semantic elements render in
Terminal vs Bifrost mode.

Architecture Position:
    Layer 0.5: Semantic Rendering Primitives
    - Between: zPrimitives (Layer 1 I/O) and Event Packages (Layer 2)
    - Used by: BasicOutputs (for semantic argument) AND rich_text (for markdown parsing)
    - Purpose: DRY - Prevent duplicate rendering logic

Design Philosophy:
    Each semantic element has ONE renderer function that:
    1. Terminal Mode: Returns markdown-style syntax (readable, no ANSI yet)
    2. Bifrost Mode: Returns raw content (frontend wraps in HTML)
    
    This ensures:
    - display.text("code", semantic="code") → renders as `code`
    - display.rich_text("Run `code`") → renders as Run `code`
    - BOTH use SemanticPrimitives.render_code() - NO DUPLICATION!

Semantic Elements Supported (16 total):
    Inline Formatting:
        - code: Inline code
        - strong: Strong emphasis/bold
        - em: Emphasis/italic
        - mark: Highlighted text
        - del: Deleted/strikethrough text
    
    Structural:
        - blockquote: Block quotation
        - pre: Preformatted text
        - code_block: Multi-line code blocks with optional language
    
    Interactive/Metadata:
        - kbd: Keyboard input
        - cite: Citation
        - q: Inline quote
        - abbr: Abbreviation
        - time: Time/date
    
    Typography:
        - small: Small print
        - sub: Subscript
        - sup: Superscript

Usage Example:
    >>> from display_semantic_primitives import SemanticPrimitives
    >>> 
    >>> # Terminal mode
    >>> SemanticPrimitives.render_code("ls -la", mode="terminal")
    '`ls -la`'
    >>> 
    >>> # Bifrost mode
    >>> SemanticPrimitives.render_code("ls -la", mode="bifrost")
    'ls -la'  # Frontend wraps in <code>

Notes:
    - All methods are @staticmethod (no instance needed)
    - Mode parameter: "terminal" or "bifrost"
    - Terminal: Returns markdown-style formatted string
    - Bifrost: Returns raw content (HTML wrapping done by frontend)
"""


class SemanticPrimitives:
    """
    Foundational semantic rendering primitives.
    
    Single source of truth for semantic HTML element rendering across
    Terminal and Bifrost modes. Used by both semantic argument (entire element)
    and rich_text markdown parsing (inline mixing).
    
    All methods are static - no instance state needed.
    """
    
    # Inline Formatting Semantics
    
    @staticmethod
    def render_code(content: str, mode: str = "terminal") -> str:
        """
        Render inline code semantic.
        
        Terminal: `content`
        Bifrost: content (wrapped in <code> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f"`{content}`"
        return content
    
    @staticmethod
    def render_strong(content: str, mode: str = "terminal") -> str:
        """
        Render strong/bold semantic.
        
        Terminal: **content**
        Bifrost: content (wrapped in <strong> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f"**{content}**"
        return content
    
    @staticmethod
    def render_em(content: str, mode: str = "terminal") -> str:
        """
        Render emphasis/italic semantic.
        
        Terminal: *content*
        Bifrost: content (wrapped in <em> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f"*{content}*"
        return content
    
    @staticmethod
    def render_mark(content: str, mode: str = "terminal") -> str:
        """
        Render highlight/mark semantic.
        
        Terminal: ==content==
        Bifrost: content (wrapped in <mark> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f"=={content}=="
        return content
    
    @staticmethod
    def render_del(content: str, mode: str = "terminal") -> str:
        """
        Render deleted/strikethrough semantic.
        
        Terminal: ~~content~~
        Bifrost: content (wrapped in <del> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f"~~{content}~~"
        return content
    
    # Structural Semantics
    
    @staticmethod
    def render_blockquote(content: str, mode: str = "terminal") -> str:
        """
        Render blockquote semantic.
        
        Terminal: > content (prefix each line with "> ")
        Bifrost: content (wrapped in <blockquote> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            # Prefix each line with "> "
            lines = content.split('\n')
            return '\n'.join(f"> {line}" for line in lines)
        return content
    
    @staticmethod
    def render_pre(content: str, mode: str = "terminal") -> str:
        """
        Render preformatted text semantic.
        
        Terminal: content (preserve whitespace as-is)
        Bifrost: content (wrapped in <pre> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content (whitespace preserved)
        """
        # Preformatted text - preserve as-is in both modes
        return content
    
    @staticmethod
    def render_code_block(content: str, language: str = "", mode: str = "terminal") -> str:
        """
        Render code block semantic (multi-line code with optional language).
        
        Terminal: 
            ┌─ [language] ────
            │ code line 1
            │ code line 2
            └─────────────────
        
        Bifrost: ```language\ncontent\n``` (markdown preserved for frontend parsing)
        
        Args:
            content: Code content to render
            language: Optional language identifier (e.g., "python", "html", "css")
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted code block
        """
        if mode == "terminal":
            # Terminal: Render with box-drawing characters for visual separation
            lines = content.split('\n')
            
            # Build header with optional language
            lang_label = f" [{language}] " if language else " "
            header = f"┌─{lang_label}{'─' * (60 - len(lang_label))}"
            
            # Indent each line with box character
            body_lines = [f"│ {line}" for line in lines]
            
            # Footer
            footer = "└" + "─" * 60
            
            # Combine all parts
            return '\n'.join([header] + body_lines + [footer])
        
        # Bifrost: Preserve markdown triple-backtick syntax (frontend will parse)
        if language:
            return f"```{language}\n{content}\n```"
        return f"```\n{content}\n```"
    
    # Interactive/Metadata Semantics
    
    @staticmethod
    def render_kbd(content: str, mode: str = "terminal") -> str:
        """
        Render keyboard input semantic.
        
        Terminal: [content]
        Bifrost: content (wrapped in <kbd> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f"[{content}]"
        return content
    
    @staticmethod
    def render_cite(content: str, mode: str = "terminal") -> str:
        """
        Render citation semantic.
        
        Terminal: — content (em dash prefix)
        Bifrost: content (wrapped in <cite> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f"— {content}"
        return content
    
    @staticmethod
    def render_q(content: str, mode: str = "terminal") -> str:
        """
        Render inline quote semantic.
        
        Terminal: "content"
        Bifrost: content (wrapped in <q> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f'"{content}"'
        return content
    
    @staticmethod
    def render_abbr(content: str, mode: str = "terminal") -> str:
        """
        Render abbreviation semantic.
        
        Terminal: content (no special formatting, tooltip only in Bifrost)
        Bifrost: content (wrapped in <abbr> with title attribute by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        # Abbreviations don't have visual terminal representation
        # Tooltip/title is Bifrost-only feature
        return content
    
    @staticmethod
    def render_time(content: str, mode: str = "terminal") -> str:
        """
        Render time/date semantic.
        
        Terminal: content (no special formatting, datetime attribute only in Bifrost)
        Bifrost: content (wrapped in <time> with datetime attribute by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        # Time elements don't have visual terminal representation
        # datetime attribute is Bifrost-only feature
        return content
    
    # Typography Semantics
    
    @staticmethod
    def render_small(content: str, mode: str = "terminal") -> str:
        """
        Render small print semantic.
        
        Terminal: content (no size change in terminal)
        Bifrost: content (wrapped in <small> by frontend for smaller font)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        # Small text doesn't have terminal representation
        # Font size is Bifrost-only feature
        return content
    
    @staticmethod
    def render_sub(content: str, mode: str = "terminal") -> str:
        """
        Render subscript semantic.
        
        Terminal: content_subscript (underscore prefix)
        Bifrost: content (wrapped in <sub> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f"_{content}"
        return content
    
    @staticmethod
    def render_sup(content: str, mode: str = "terminal") -> str:
        """
        Render superscript semantic.
        
        Terminal: content^superscript (caret prefix)
        Bifrost: content (wrapped in <sup> by frontend)
        
        Args:
            content: Text content to render
            mode: "terminal" or "bifrost"
            
        Returns:
            str: Formatted content
        """
        if mode == "terminal":
            return f"^{content}"
        return content

