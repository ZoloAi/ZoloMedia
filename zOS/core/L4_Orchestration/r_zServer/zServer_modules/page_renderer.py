# zCLI/subsystems/zServer/zServer_modules/page_renderer.py

"""
Page Renderer for zServer - Converts zUI YAML to HTML.

This module renders zUI files as HTML pages for web delivery. It executes
zUI blocks in a special "Web" rendering mode where zDisplay events are
captured as HTML instead of printed to terminal.

Architecture:
    1. Load zUI file via zLoader
    2. Set session mode to "Web"
    3. Execute zUI block (zDisplay events fire)
    4. Capture HTML output from events
    5. Wrap in HTML template
    6. Return complete HTML page

Integration:
    - Called by: HTTPRouter for type: dynamic routes
    - Uses: zLoader (file loading), zWalker (block execution)
    - Session: Sets SESSION_KEY_ZMODE = "Web"

v1.5.4 Phase 3 - MVP Implementation
"""

from typing import Any, Optional, Dict
import io
import sys


class PageRenderer:
    """
    Renders zUI files as HTML pages.
    
    Attributes:
        zcli: zCLI instance
        logger: Logger instance
        html_buffer: StringIO buffer for capturing HTML output
    """
    
    def __init__(self, zcli: Any, routes: Dict = None):
        """
        Initialize page renderer.
        
        Args:
            zcli: zCLI instance providing loader, session, display
            routes: Optional routing configuration for file→route mapping
        """
        self.zcli = zcli
        self.logger = zcli.logger if hasattr(zcli, 'logger') else None
        self.html_buffer = None
        
        # Build reverse mapping: zVaFile → HTTP route for dual-mode navigation
        self._file_to_route_map = {}
        if routes:
            for route_path, route_config in routes.items():
                if isinstance(route_config, dict) and route_config.get('type') == 'dynamic':
                    zvafile = route_config.get('zVaFile', '')
                    if zvafile:
                        # Normalize file path: ./zUI_web_users.yaml → zUI_web_users
                        normalized = zvafile.replace('./', '').replace('.yaml', '')
                        self._file_to_route_map[normalized] = route_path
                        if self.logger:
                            self.logger.debug(f"[PageRenderer] Mapped {normalized} → {route_path}")
    
    def render_page(
        self,
        zVaFile: str,
        zBlock: str = "zVaF"
    ) -> str:
        """
        Render a zUI file as HTML.
        
        Args:
            zVaFile: Path to zUI file (e.g., "./zUI.web_dashboard.yaml")
            zBlock: Block to execute (default: "zVaF")
        
        Returns:
            str: Complete HTML page
        
        Examples:
            renderer = PageRenderer(zcli)
            html = renderer.render_page("./zUI.web_dashboard.yaml", "zVaF")
        """
        if self.logger:
            self.logger.info(f"[PageRenderer] Rendering: {zVaFile} -> {zBlock}")
        
        try:
            # Step 1: Load zUI file
            # If path is relative (starts with ./), make it absolute using zSpace
            if zVaFile.startswith("./"):
                import os
                zSpace = self.zcli.session.get("zSpace", os.getcwd())
                zVaFile = os.path.join(zSpace, zVaFile[2:])  # Remove ./
                if self.logger:
                    self.logger.debug(f"[PageRenderer] Resolved path: {zVaFile}")
            
            zui_data = self.zcli.loader.handle(zVaFile)
            
            if not zui_data:
                return self._render_error("Failed to load zUI file")
            
            # Step 2: TODO - Execute zUI in Web mode
            # For now, return a simple HTML template
            html_content = self._execute_zui_web_mode(zui_data, zBlock, zVaFile)
            
            # Step 3: Wrap in HTML template
            return self._wrap_in_template(html_content, zBlock)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"[PageRenderer] Error: {e}")
            return self._render_error(f"Rendering error: {str(e)}")
    
    def _execute_zui_web_mode(
        self,
        zui_data: Dict[str, Any],
        zBlock: str,
        zVaFile: str
    ) -> str:
        """
        Execute zUI block and capture HTML output.
        
        This is the core rendering logic. It converts zUI YAML to HTML.
        
        Args:
            zui_data: Parsed zUI data
            zBlock: Block to execute
            zVaFile: Original file path
        
        Returns:
            str: HTML content from zDisplay events
        """
        html_parts = []
        
        # Get block data
        block_data = zui_data.get(zBlock, {})
        
        if not block_data:
            return "<div class='error-box'><p>Block not found: {zBlock}</p></div>"
        
        if self.logger:
            self.logger.debug(f"[PageRenderer] Rendering block: {zBlock} with {len(block_data)} keys")
        
        # Extract menu items to skip their action definitions
        menu_items = []
        if "~Root*" in block_data:
            root_menu = block_data.get("~Root*", [])
            if isinstance(root_menu, list):
                menu_items = root_menu
        
        # Phase 1 MVP: Simple HTML conversion from zUI YAML
        # Convert zUI events to HTML directly (no walker execution)
        for key, value in block_data.items():
            # Skip menu action definitions (they're rendered as part of menu)
            if key in menu_items:
                continue
            
            html_parts.append(self._render_zui_element(key, value, menu_items, block_data))
        
        return "\n".join(html_parts)
    
    def _render_zui_element(self, key: str, value: Any, menu_items: list = None, block_data: Dict = None) -> str:
        """
        Render a single zUI element to HTML.
        
        Args:
            key: zUI key (e.g., "~Root*", "zDisplay", "zLink")
            value: zUI value
            menu_items: List of menu item names (to convert to links)
            block_data: Full block data (to lookup actions)
        
        Returns:
            str: HTML fragment
        """
        # Handle special keys
        if key == "~Root*":
            # Menu items - make them clickable
            return self._render_menu(value, block_data or {})
        
        # Check if value is a dict containing zDisplay
        elif isinstance(value, dict) and "zDisplay" in value:
            # Display event wrapped in dict (e.g., WelcomeHeader: {zDisplay: {...}})
            return self._render_display_event(value["zDisplay"])
        
        elif isinstance(value, dict) and "zLink" in value:
            # Link navigation (HTTP route)
            link_path = value["zLink"]
            http_route = self._convert_file_path_to_route(link_path)
            return f'<a href="{http_route}" class="btn btn-primary">Navigate</a>'
        
        elif key.startswith("_"):
            # Skip internal keys (e.g., zRBAC)
            return ""
        
        else:
            # Unknown - render as data (debug mode)
            return f"<div class='debug'><strong>{key}:</strong> {value}</div>"
    
    def _convert_file_path_to_route(self, link_path: str) -> str:
        """
        Convert zLink file path to HTTP route for web navigation.
        
        Dual-mode navigation solution:
        - Terminal: Uses file path directly (@.zUI_web_users)
        - Web: Maps file path to HTTP route (/users)
        
        Args:
            link_path: zLink value (e.g., "@.zUI_web_users")
        
        Returns:
            str: HTTP route (e.g., "/users") or original if no mapping
        """
        # Extract filename from zLink path (@.zUI_web_users → zUI_web_users)
        if link_path.startswith("@."):
            filename = link_path[2:]  # Remove @. prefix
        else:
            filename = link_path
        
        # Look up HTTP route from mapping
        http_route = self._file_to_route_map.get(filename)
        
        if http_route:
            if self.logger:
                self.logger.debug(f"[PageRenderer] Mapped file path '{link_path}' → '{http_route}'")
            return http_route
        else:
            # No mapping found, return as-is (might be HTTP route already)
            if self.logger:
                self.logger.warning(f"[PageRenderer] No route mapping for '{link_path}', using as-is")
            return link_path
    
    def _render_menu(self, items: list, block_data: Dict) -> str:
        """
        Render ~Root* menu as HTML nav with clickable links.
        
        Looks up each menu item's action (zLink/zDelta) and creates appropriate links.
        Converts file paths to HTTP routes for dual-mode compatibility.
        """
        if not items:
            return ""
        
        html = '<nav class="menu"><ul>'
        for item in items:
            # Menu items should be strings
            label = item if isinstance(item, str) else str(item)
            
            # Look up the action for this menu item
            action = block_data.get(label, {})
            
            if isinstance(action, dict):
                # Check for zLink (file path → HTTP route mapping)
                if "zLink" in action:
                    link_path = action["zLink"]
                    # Convert file path to HTTP route for web navigation
                    http_route = self._convert_file_path_to_route(link_path)
                    html += f'<li><a href="{http_route}">{label}</a></li>'
                
                # Check for zDelta (intra-file navigation)
                elif "zDelta" in action:
                    # For now, show as non-clickable (would need JavaScript or form)
                    delta_target = action["zDelta"]
                    html += f'<li><span title="Delta: {delta_target}">{label}</span></li>'
                
                else:
                    # No action, just label
                    html += f'<li>{label}</li>'
            else:
                # Not a dict, just show label
                html += f'<li>{label}</li>'
        
        html += '</ul></nav>'
        return html
    
    def _render_display_event(self, event_data: Dict[str, Any]) -> str:
        """Render zDisplay event as HTML."""
        if not isinstance(event_data, dict):
            return ""
        
        event_type = event_data.get("event", "text")
        content = event_data.get("content", "")
        indent = event_data.get("indent", 0)
        
        # Convert event types to HTML
        if event_type == "header":
            return f'<h2 style="margin-left: {indent * 20}px">{content}</h2>'
        
        elif event_type == "text":
            return f'<p style="margin-left: {indent * 20}px">{content}</p>'
        
        elif event_type == "success":
            return f'<div class="success-box" style="margin-left: {indent * 20}px">{content}</div>'
        
        elif event_type == "error":
            return f'<div class="error-box" style="margin-left: {indent * 20}px">{content}</div>'
        
        elif event_type == "warning":
            return f'<div class="warning-box" style="margin-left: {indent * 20}px">{content}</div>'
        
        elif event_type == "info":
            return f'<div class="info-box" style="margin-left: {indent * 20}px">{content}</div>'
        
        elif event_type == "list":
            items = event_data.get("items", [])
            html = f'<ul style="margin-left: {indent * 20}px">'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ul>'
            return html
        
        else:
            return f'<div style="margin-left: {indent * 20}px">{content}</div>'
    
    def _wrap_in_template(self, content: str, title: str) -> str:
        """
        Wrap HTML content in complete page template.
        
        Args:
            content: HTML content to wrap
            title: Page title
        
        Returns:
            str: Complete HTML page
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - zCLI Dynamic Web</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🎨 zCLI Dynamic Web</h1>
            <p>Powered by zUI YAML</p>
        </header>
        
        <main>
            {content}
        </main>
        
        <footer>
            <p>Generated by zCLI v1.5.4 - Demo 4: Dynamic Web UI</p>
        </footer>
    </div>
    <script src="/script.js"></script>
</body>
</html>"""
    
    def _render_error(self, message: str) -> str:
        """
        Render error page.
        
        Args:
            message: Error message
        
        Returns:
            str: HTML error page
        """
        return self._wrap_in_template(
            f"""<div class="error-box">
                <h2>⚠️ Rendering Error</h2>
                <p>{message}</p>
            </div>""",
            "Error"
        )

