# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_links.py

"""
LinkEvents - Semantic Link Rendering for zDisplay
==================================================

Handles semantic link rendering with support for:
- Internal navigation (delta $ and zPath @)
- External URLs (http/https)
- Anchor links (#section)
- Target behavior (_blank, _self, etc.)
- Window features (width, height, etc.)

Terminal Mode:
- Internal links: Auto-navigate or prompt based on link type
- External links: Show URL, prompt to open in browser
- Anchor links: Display with icon (no scroll in Terminal)
- Target: Limited support (new terminal window if possible)

Bifrost Mode:
- Internal links: Client-side routing via BifrostClient
- External links: Native <a> tag behavior with proper security
- Anchor links: Smooth scroll to target element
- Target: Full HTML5 support including window.open()

Architecture Position:
    Layer 2: Event Handlers (this module)
    Uses: display_primitives for output, zOpen for external links
    Called by: display_events.py orchestrator

Version: v1.6.0 (Link Event Support)
"""

# Centralized imports from zCLI
from zOS import Dict, Any, Optional

# Import DRY helpers from primitives
from ..b_primitives.display_rendering_helpers import wrap_with_color

# Import constants from centralized module
from ..display_constants import (
    _EVENT_LINK,
    TARGET_SELF,
    TARGET_BLANK,
    TARGET_PARENT,
    TARGET_TOP,
    DEFAULT_TARGET,
    _LINK_TYPE_INTERNAL_DELTA,
    _LINK_TYPE_INTERNAL_ZPATH,
    _LINK_TYPE_EXTERNAL,
    _LINK_TYPE_ANCHOR,
    _LINK_TYPE_PLACEHOLDER,
    _PROMPT_LINK_INTERNAL,
    _PROMPT_LINK_EXTERNAL,
    _PROMPT_LINK_PLACEHOLDER,
    _PROMPT_LINK_ANCHOR,
    _LOG_PREFIX,
)


class LinkEvents:
    """
    Handle link event rendering for Terminal and Bifrost modes.
    
    Provides semantic link rendering with mode-aware behavior, supporting
    internal navigation, external URLs, and anchor links with full target
    and window feature control.
    
    Attributes:
        display: Parent zDisplay instance
        zcli: Root zCLI instance
        logger: Logger instance
    
    Methods:
        handle_link(): Main entry point for link rendering
    """
    
    def __init__(self, display: Any) -> None:
        """
        Initialize LinkEvents handler.
        
        Args:
            display: Parent zDisplay instance
        """
        self.display = display
        self.zcli = display.zcli
        self.logger = display.logger
        self.primitives = display.zPrimitives
        self.zColors = display.zColors  # For Terminal color support
        # Cross-references (set by zEvents)
        self.BasicOutputs = None  # Will be wired by zEvents.__init__
        self.BasicInputs = None   # Will be wired by zEvents.__init__
    
    def handle_link(self, link_data: Dict[str, Any]) -> Optional[Any]:
        """
        Main entry point for link event handling.
        
        Renders links based on mode (Terminal vs Bifrost) and link type
        (internal, external, anchor). Handles target behavior and window
        features for advanced use cases.
        
        Args:
            link_data: Dict with keys:
                - label: Link text (required)
                - href: Link destination (required)
                - target: Target behavior (_self, _blank, etc.)
                - rel: Link relationship (security)
                - window: Window features for window.open()
                - _zClass: CSS classes for styling
                - color: Color theme
        
        Returns:
            Navigation result (for internal links) or None
        
        Examples:
            # Internal link
            handle_link({"label": "About", "href": "$zAbout"})
            
            # External link with new tab
            handle_link({
                "label": "GitHub",
                "href": "https://github.com",
                "target": "_blank"
            })
            
            # Anchor link
            handle_link({"label": "Features", "href": "#features"})
        """
        href = link_data.get('href', '#')
        label = link_data.get('label', href)
        target = link_data.get('target', DEFAULT_TARGET)
        
        # Detect link type
        link_type = self._detect_link_type(href)
        
        # Route to mode-specific handler
        mode = self.zcli.session.get('zMode', 'Terminal')
        
        if mode == 'Terminal':
            return self._render_terminal(link_data, link_type)
        else:  # zBifrost
            return self._render_bifrost(link_data, link_type)
    
    def _detect_link_type(self, href: str) -> str:
        """
        Detect link type from href value.
        
        Args:
            href: Link destination
        
        Returns:
            Link type constant (delta, zpath, external, anchor, placeholder)
        
        Examples:
            _detect_link_type("$zAbout") → "delta"
            _detect_link_type("@.UI.zUI.zAbout") → "zpath"
            _detect_link_type("https://example.com") → "external"
            _detect_link_type("#features") → "anchor"
            _detect_link_type("#") → "placeholder"
        """
        if not href or href == '#':
            return _LINK_TYPE_PLACEHOLDER
        elif href.startswith('$'):
            return _LINK_TYPE_INTERNAL_DELTA
        elif href.startswith('@'):
            return _LINK_TYPE_INTERNAL_ZPATH
        elif href.startswith(('http://', 'https://')):
            return _LINK_TYPE_EXTERNAL
        elif href.startswith('#'):
            return _LINK_TYPE_ANCHOR
        else:
            # Assume internal delta if unclear
            return _LINK_TYPE_INTERNAL_DELTA
    
    def _render_terminal(self, link_data: Dict[str, Any], link_type: str) -> Optional[Any]:
        """Render link in Terminal mode with interactive y/n prompt.
        
        Displays link with button-style interaction, prompting user with (y/n).
        Default behavior is 'n' (no action) if user just presses Enter.
        
        Args:
            link_data: Link configuration dict
            link_type: Detected link type
        
        Returns:
            Navigation dict (for internal links) or action result
        """
        href = link_data.get('href', '#')
        label = link_data.get('label', href)
        target = link_data.get('target', DEFAULT_TARGET)
        color = link_data.get('color', 'PRIMARY')
        
        # Display link label
        self._display_link_label(label)
        
        try:
            response = self._prompt_link_confirmation(label, color, link_type)
            
            # Default to 'n' if empty response (just pressed Enter)
            if not response or response not in ('y', 'yes'):
                return self._handle_link_cancel(label)
            
            # Handle confirmed link based on type
            return self._execute_link_action(link_type, href, label, target)
            
        except (KeyboardInterrupt, EOFError):
            return self._handle_link_cancel(label)

    def _display_link_label(self, label: str) -> None:
        """Display the link label in button-style format."""
        self.BasicOutputs.text(f"  [{label}]", indent=1, break_after=False)

    def _prompt_link_confirmation(self, label: str, color: str, link_type: str) -> str:
        """Prompt user to confirm link click with colored prompt.
        
        Uses contextual prompts based on link type:
        - Internal links: "Navigate to: {label}? (y/n): "
        - External links: "Open {label} in browser? (y/n): "
        - Placeholder: "Click {label}? (y/n): "
        - Anchor: "{label}? (y/n): "
        """
        # Select appropriate prompt based on link type
        if link_type in (_LINK_TYPE_INTERNAL_DELTA, _LINK_TYPE_INTERNAL_ZPATH):
            prompt_template = _PROMPT_LINK_INTERNAL
        elif link_type == _LINK_TYPE_EXTERNAL:
            prompt_template = _PROMPT_LINK_EXTERNAL
        elif link_type == _LINK_TYPE_PLACEHOLDER:
            prompt_template = _PROMPT_LINK_PLACEHOLDER
        elif link_type == _LINK_TYPE_ANCHOR:
            prompt_template = _PROMPT_LINK_ANCHOR
        else:
            # Fallback to internal prompt
            prompt_template = _PROMPT_LINK_INTERNAL
        
        prompt_text = prompt_template.format(label=label)
        colored_prompt = wrap_with_color(prompt_text, color, self.zColors)
        return self.primitives.read_string(colored_prompt).strip().lower()

    def _handle_link_cancel(self, label: str) -> None:
        """Handle link cancellation (user declined or interrupted)."""
        self.BasicOutputs.text(f"  {label} cancelled.", indent=1, break_after=False)
        self.logger.debug(f"{_LOG_PREFIX} Link cancelled: {label}")
        # Return None instead of "stop" to continue with remaining wizard steps
        return None

    def _execute_link_action(self, link_type: str, href: str, label: str, target: str) -> Optional[Any]:
        """Execute the appropriate action based on link type."""
        if link_type == _LINK_TYPE_PLACEHOLDER:
            return self._handle_placeholder_link(label)
        elif link_type == _LINK_TYPE_INTERNAL_DELTA:
            return self._handle_internal_link(href, label, "Delta")
        elif link_type == _LINK_TYPE_INTERNAL_ZPATH:
            return self._handle_internal_link(href, label, "zPath")
        elif link_type == _LINK_TYPE_EXTERNAL:
            return self._handle_external_link(href, label, target)
        elif link_type == _LINK_TYPE_ANCHOR:
            return self._handle_anchor_link(href, label)
        
        return None

    def _handle_placeholder_link(self, label: str) -> None:
        """Handle placeholder link (no action)."""
        self.BasicOutputs.text(f"  {label} is a placeholder (no action).", indent=1, break_after=False)
        self.logger.debug(f"{_LOG_PREFIX} Placeholder link clicked (no action): {label}")
        return None

    def _handle_internal_link(self, href: str, label: str, link_subtype: str) -> Dict[str, str]:
        """Handle internal navigation link (Delta or zPath)."""
        self.BasicOutputs.text(f"  Navigating to {label}...", indent=1, break_after=False)
        self.logger.info(f"{_LOG_PREFIX} {link_subtype} navigation confirmed: {href}")
        return {"zLink": href}

    def _handle_external_link(self, href: str, label: str, target: str) -> None:
        """Handle external URL link and continue wizard."""
        self.BasicOutputs.text(f"     → {href}", indent=1, color="MUTED")
        self.BasicOutputs.text(f"  Opening {label} in browser...", indent=1, break_after=False)
        self.logger.info(f"{_LOG_PREFIX} External link confirmed: {href}")
        
        if target == TARGET_BLANK:
            self.logger.info(f"{_LOG_PREFIX} Opening in new window/tab (target: _blank)")
        
        # Open in browser but return None to continue wizard
        self.zcli.open.handle(f"zOpen({href})")
        return None

    def _handle_anchor_link(self, href: str, label: str) -> None:
        """Handle anchor link (Terminal limitation)."""
        self.BasicOutputs.text(f"     ⚓ {href}", indent=1, color="MUTED")
        self.BasicOutputs.text(f"  {label} is an anchor link (Terminal has no scroll).", indent=1, break_after=False)
        self.logger.debug(f"{_LOG_PREFIX} Anchor link (Terminal limitation): {href}")
        return None
    
    def _render_bifrost(self, link_data: Dict[str, Any], link_type: str) -> None:
        """
        Render link in Bifrost mode (send to frontend).
        
        Sends structured link event to frontend for semantic HTML rendering
        with proper <a> tags, target behavior, and security attributes.
        
        Args:
            link_data: Link configuration dict
            link_type: Detected link type
        
        Notes:
            - Frontend handles client-side routing for internal links
            - Security: rel="noopener noreferrer" auto-added for _blank
            - Window features: Supports custom width, height, and features
        """
        # Emit link event to frontend with all metadata
        event_data = {
            'event': _EVENT_LINK,
            'label': link_data.get('label', ''),
            'href': link_data.get('href', '#'),
            'target': link_data.get('target', DEFAULT_TARGET),
            'rel': link_data.get('rel', ''),
            'link_type': link_type,
            '_zClass': link_data.get('_zClass', ''),
            'color': link_data.get('color', ''),
            'window': link_data.get('window', {})  # For window.open() features
        }
        
        # Auto-add security for external _blank links
        if (link_type == _LINK_TYPE_EXTERNAL and 
            event_data['target'] == TARGET_BLANK and 
            not event_data['rel']):
            event_data['rel'] = 'noopener noreferrer'
            self.logger.debug(f"{_LOG_PREFIX} Auto-added rel='noopener noreferrer' for external _blank link")
        
        # Send to frontend via primitives
        self.primitives.send_gui_event('link', event_data)
        self.logger.info(f"{_LOG_PREFIX} Link event sent to Bifrost: {link_data.get('label')}")

