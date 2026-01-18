# zCLI/subsystems/zServer/zServer_modules/handler.py

"""
Custom HTTP request handler with logging integration
"""

from http.server import SimpleHTTPRequestHandler
import os


class LoggingHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with zCLI logger integration + routing (v1.5.5: Flask conventions)"""
    
    def __init__(self, *args, logger=None, router=None, static_folder="static", template_folder="templates", ui_folder="UI", serve_path=".", static_mounts=None, **kwargs):
        self.zcli_logger = logger
        self.router = router  # HTTPRouter instance (optional)
        self.static_folder = static_folder  # Flask convention: static files folder
        self.template_folder = template_folder  # Flask convention: templates folder
        self.ui_folder = ui_folder  # zUI zVaF files folder
        self.serve_path = serve_path  # Base directory for serving files
        self.static_mounts = static_mounts or {}  # Custom mount points: {"/url_prefix/": "/fs_path/"}
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to use zCLI logger instead of stderr"""
        if self.zcli_logger:
            self.zcli_logger.info(f"[zServer] {self.address_string()} - {format % args}")
        else:
            # Fallback to default behavior if no logger
            super().log_message(format, *args)
    
    def end_headers(self):
        """Add CORS headers for local development"""
        # Allow local development access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.end_headers()
    
    def list_directory(self, path):
        """Disable directory listing for security"""
        self.send_error(403, "Directory listing is disabled")
        return None
    
    def send_error(self, code, message=None, explain=None):
        """
        Override send_error to serve custom zTheme error pages.
        
        Looks for templates/{code}.html first, falls back to built-in pages.
        """
        try:
            # Try to serve custom error page from templates/
            error_page_path = os.path.join(self.serve_path, self.template_folder, f"{code}.html")
            
            if os.path.exists(error_page_path):
                # Serve custom error page
                with open(error_page_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(code)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-length", len(content))
                self.end_headers()
                self.wfile.write(content)
                return
        except Exception as e:
            if self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Error serving custom error page: {e}")
        
        # Fallback to built-in error pages
        from .error_pages import get_error_page, has_error_page
        
        if has_error_page(code):
            html = get_error_page(code, message)
            content = html.encode('utf-8')
            
            self.send_response(code)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-length", len(content))
            self.end_headers()
            self.wfile.write(content)
        else:
            # Ultimate fallback to Python's default
            super().send_error(code, message, explain)
    
    def do_GET(self):
        """
        Handle GET requests with Flask-like conventions (v1.5.12 - SECURITY ENHANCED).
        
        Flow:
            0. SECURITY: Block access to sensitive paths (models/, .zEnv, etc.)
            1. Check for favicon.ico and serve default if not found
            2. Check for /static/* and auto-serve from static_folder
            3. Check for /UI/* and auto-serve from ui_folder (zVaF files)
            4. If router exists: Use declarative routing
            5. Otherwise: Fallback to static file serving (current behavior)
        """
        # SECURITY v1.5.12: Block access to sensitive folders and files
        # This prevents exposure of database credentials, configuration, and internal files
        blocked_paths = [
            '/models/',      # Database schemas (may contain connection info)
            '/zConfigs/',    # Configuration files
            '/.zEnv',        # Environment variables (database credentials!)
            '/.env',         # Alternative env file naming
            '/.git/',        # Version control
            '/routes/',      # Server route definitions
            '/__pycache__/', # Python cache
            '/zCLI/',        # Framework internals
        ]
        
        # Check if path starts with or contains any blocked path
        for blocked in blocked_paths:
            if self.path.startswith(blocked) or blocked in self.path:
                if hasattr(self, 'zcli_logger') and self.zcli_logger:
                    self.zcli_logger.warning(f"[SECURITY] Blocked access attempt to: {self.path}")
                self.send_error(403, "Access Forbidden")
                return
        
        # Handle favicon.ico with default zolo favicon
        if self.path == '/favicon.ico':
            return self._serve_default_favicon()
        
        # Check custom static mounts FIRST (user-defined mount points)
        for url_prefix, fs_path in self.static_mounts.items():
            if self.path.startswith(url_prefix):
                return self._serve_mounted_file(url_prefix, fs_path)
        
        # Auto-serve /static/* from static_folder (Flask convention)
        if self.path.startswith('/static/'):
            return self._serve_static_file()
        
        # Auto-serve /UI/* from ui_folder (zUI zVaF files) - case-sensitive to match folder
        ui_prefix = f'/{self.ui_folder}/'
        if self.path.startswith(ui_prefix) or self.path.lower().startswith(ui_prefix.lower()):
            return self._serve_ui_file()
        
        # Check if router exists (declarative routing mode)
        if self.router:
            # DEBUG: Log that router exists
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.info(f"[Handler] Router exists, processing route: {self.path}")
            return self._handle_routed_request()
        
        # Fallback: Static file serving (backward compatible)
        if hasattr(self, 'zcli_logger') and self.zcli_logger:
            self.zcli_logger.warning(f"[Handler] No router - falling back to static file serving for: {self.path}")
        return super().do_GET()
    
    def do_POST(self):
        """
        Handle POST requests for forms and APIs (v1.5.7 Phase 1.2).
        
        Flow:
            1. If router exists: Use declarative routing
            2. Otherwise: Return 405 Method Not Allowed
        """
        # Check if router exists (declarative routing mode)
        if self.router:
            return self._handle_routed_request()
        
        # No router - POST not supported
        return self.send_error(405, "POST not supported without routing")
    
    def _serve_default_favicon(self):
        """Serve default zolo favicon from zServer static folder"""
        import os
        
        # Path to default favicon in zServer static folder
        zserver_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        favicon_path = os.path.join(zserver_dir, 'static', 'favicon.ico')
        
        if not os.path.exists(favicon_path):
            # No default favicon, return 404
            return self.send_error(404, "Favicon not found")
        
        try:
            with open(favicon_path, 'rb') as f:
                favicon_data = f.read()
            
            self.send_response(200)
            self.send_header("Content-type", "image/x-icon")
            self.send_header("Content-length", len(favicon_data))
            self.send_header("Cache-Control", "public, max-age=86400")  # Cache for 1 day
            self.end_headers()
            self.wfile.write(favicon_data)
            
        except Exception as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Error serving favicon: {e}")
            return self.send_error(500, f"Error serving favicon: {str(e)}")
    
    def _serve_static_file(self):
        """
        Auto-serve files from /static/* (Flask convention).
        
        Maps /static/js/hello.js → {serve_path}/static/js/hello.js
        """
        import os
        import mimetypes
        from urllib.parse import unquote
        
        # Remove /static/ prefix to get relative path
        relative_path = self.path[8:]  # Remove '/static/'
        
        # Decode URL encoding (e.g., %20 → space)
        relative_path = unquote(relative_path)
        
        # Build absolute path: {serve_path}/{static_folder}/{relative_path}
        file_path = os.path.join(self.serve_path, self.static_folder, relative_path)
        
        # Security: Prevent directory traversal
        file_path = os.path.abspath(file_path)
        static_root = os.path.abspath(os.path.join(self.serve_path, self.static_folder))
        
        if not file_path.startswith(static_root):
            return self.send_error(403, "Access denied")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return self.send_error(404, f"File not found: {self.path}")
        
        # Check if it's a directory (not allowed)
        if os.path.isdir(file_path):
            return self.send_error(403, "Directory listing is disabled")
        
        # Serve the file
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-length", len(content))
            
            # Disable caching for JavaScript files during development
            if file_path.endswith('.js'):
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("X-Dev-Cache", "disabled")  # Debug header
            else:
                self.send_header("Cache-Control", "public, max-age=3600")  # Cache for 1 hour
            
            self.end_headers()
            self.wfile.write(content)
            
            if self.zcli_logger:
                self.zcli_logger.debug(f"[Handler] Served static file: {self.path}")
            
        except Exception as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Error serving static file: {e}")
            return self.send_error(500, f"Error serving file: {str(e)}")
    
    def _serve_mounted_file(self, url_prefix, fs_root):
        """
        Serve file from a custom mount point (v1.5.11: Multi-mount support).
        
        Generic mount handler that serves files from any configured filesystem location.
        Each mount has its own security boundary (directory traversal protection).
        
        Args:
            url_prefix (str): URL prefix (e.g., "/bifrost/", "/shared/")
            fs_root (str): Filesystem root path (absolute)
        
        Example:
            url_prefix="/bifrost/", fs_root="/Users/gal/bifrost/"
            Request: /bifrost/src/client.js
            Serves: /Users/gal/bifrost/src/client.js
        
        Security:
            - Directory traversal protection per mount
            - No directory listing
            - Validates file exists and is readable
        """
        import os
        import mimetypes
        from urllib.parse import unquote
        
        # Remove URL prefix to get relative path within mount
        relative_path = self.path[len(url_prefix):]
        
        # Decode URL encoding (e.g., %20 → space)
        relative_path = unquote(relative_path)
        
        # Build absolute path within mount
        file_path = os.path.join(fs_root, relative_path)
        
        # Security: Prevent directory traversal attacks
        file_path = os.path.abspath(file_path)
        mount_root = os.path.abspath(fs_root)
        
        if not file_path.startswith(mount_root):
            if self.zcli_logger:
                self.zcli_logger.warning(f"[Handler] Directory traversal attempt blocked: {self.path}")
            return self.send_error(403, "Access denied")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return self.send_error(404, f"File not found: {self.path}")
        
        # Check if it's a directory (not allowed)
        if os.path.isdir(file_path):
            return self.send_error(403, "Directory listing is disabled")
        
        # Serve the file
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Guess MIME type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Send response
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-length", len(content))
            
            # Disable caching for JavaScript files during development
            if file_path.endswith('.js'):
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("X-Dev-Cache", "disabled")
            else:
                self.send_header("Cache-Control", "public, max-age=3600")
            
            self.end_headers()
            self.wfile.write(content)
            
            if self.zcli_logger:
                self.zcli_logger.debug(f"[Handler] Served from mount {url_prefix}: {self.path}")
        
        except Exception as e:
            if self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Error serving mounted file {self.path}: {e}")
            return self.send_error(500, f"Error serving file: {str(e)}")
    
    def _serve_ui_file(self):
        """
        Auto-serve zVaF files from /UI/* (zUI convention).
        
        Maps /UI/zUI.index.yaml → {serve_path}/UI/zUI.index.yaml
        """
        import os
        import mimetypes
        from urllib.parse import unquote
        
        # Remove /UI/ prefix to get relative path (case-insensitive match)
        ui_prefix = f'/{self.ui_folder}/'
        ui_prefix_len = len(ui_prefix)
        
        # Handle both exact case and lowercase URLs
        if self.path.startswith(ui_prefix):
            relative_path = self.path[ui_prefix_len:]
        else:
            # Case-insensitive fallback
            relative_path = self.path[ui_prefix_len:]
        
        # Decode URL encoding (e.g., %20 → space)
        relative_path = unquote(relative_path)
        
        # Build absolute path: {serve_path}/{ui_folder}/{relative_path}
        file_path = os.path.join(self.serve_path, self.ui_folder, relative_path)
        
        # Security: Prevent directory traversal
        file_path = os.path.abspath(file_path)
        ui_root = os.path.abspath(os.path.join(self.serve_path, self.ui_folder))
        
        if not file_path.startswith(ui_root):
            return self.send_error(403, "Access denied")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return self.send_error(404, f"UI file not found: {self.path}")
        
        # Check if it's a directory (not allowed)
        if os.path.isdir(file_path):
            return self.send_error(403, "Directory listing is disabled")
        
        # Serve the YAML file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Force YAML content type
            content_type = 'application/x-yaml'
            
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-length", len(content.encode('utf-8')))
            self.send_header("Cache-Control", "no-cache")  # Don't cache UI files during development
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
            if self.zcli_logger:
                self.zcli_logger.debug(f"[Handler] Served UI file: {self.path}")
            
        except Exception as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Error serving UI file: {e}")
            return self.send_error(500, f"Error serving UI file: {str(e)}")
    
    def _handle_routed_request(self):
        """Handle request using HTTPRouter with RBAC enforcement"""
        # Strip query parameters for route matching
        from urllib.parse import urlparse
        clean_path = urlparse(self.path).path
        
        # DEBUG: Log route matching attempt
        if hasattr(self, 'zcli_logger') and self.zcli_logger:
            self.zcli_logger.info(f"[Handler] Attempting to match route: {clean_path}")
            self.zcli_logger.info(f"[Handler] Router has {len(self.router.auto_discovered_routes)} auto-discovered routes")
        
        # Match route (without query parameters)
        route = self.router.match_route(clean_path)
        if not route:
            # No route found - 404
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.warning(f"[Handler] No route match found for: {self.path}")
            return self.send_error(404, "Route not found")
        
        # Check RBAC
        has_access, error_page = self.router.check_access(route)
        if not has_access:
            # Access denied - serve 403 error page (built-in or custom)
            return self.send_error(403, "Access Denied")
        
        # Access granted - serve based on route type
        route_type = route.get("type", "static")
        if hasattr(self, 'zcli_logger') and self.zcli_logger:
            self.zcli_logger.info(f"[Handler] Route type: {route_type} for path: {clean_path}")
        
        if route_type == "static":
            # Serve static file directly
            file_path = self.router.resolve_file_path(route)
            
            # Check if file exists
            if not os.path.exists(file_path):
                return self.send_error(404, f"File not found: {file_path}")
            
            # Check if it's a directory (not allowed for static routes)
            if os.path.isdir(file_path):
                return self.send_error(403, "Directory listing is disabled")
            
            # Serve the file directly
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Determine content type
                import mimetypes
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
                
                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.send_header("Content-length", len(content))
                self.end_headers()
                self.wfile.write(content)
                
            except Exception as e:
                if hasattr(self, 'zcli_logger') and self.zcli_logger:
                    self.zcli_logger.error(f"[Handler] Error serving static file: {e}")
                return self.send_error(500, f"Error serving file: {str(e)}")
        
        elif route_type == "content":
            # Serve inline HTML content (like Flask return "<h1>...</h1>")
            return self._handle_content_route(route)
        
        elif route_type == "template":
            # Serve Jinja2 template (like Flask render_template())
            return self._handle_template_route(route)
        
        elif route_type == "zWalker":
            # zWalker: Execute zVaF blocks via zWalker (server-side rendering)
            return self._handle_zwalker_route(route)
        
        elif route_type == "form":
            # Handle declarative web form (zDialog pattern - v1.5.7)
            return self._handle_form_route(route)
        
        elif route_type == "json":
            # Handle declarative JSON response (v1.5.7)
            return self._handle_json_route(route)
        
        elif route_type == "dynamic":
            # Serve dynamically generated HTML from zUI
            return self._handle_dynamic_route(route)
        
        elif route_type == "zFunc":
            # Call plugin function directly (for file uploads, API endpoints, etc.)
            return self._handle_zfunc_route(route)
        
        # Unknown route type
        return self.send_error(501, f"Route type '{route_type}' not supported")
    
    def _handle_content_route(self, route: dict):
        """
        Handle content route - serve inline HTML string (like Flask return "<h1>...</h1>").
        
        Args:
            route: Route definition with "content" field
        
        Returns:
            None: Sends HTTP response directly
        """
        try:
            # Extract HTML content from route
            html_content = route.get("content", "")
            
            if not html_content:
                return self.send_error(500, "Content route missing 'content' field")
            
            # Send HTML response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", len(html_content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            # Log error and send 500
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Content route error: {e}")
            return self.send_error(500, f"Content serving failed: {str(e)}")
    
    def _handle_template_route(self, route: dict):
        """
        Handle template route - render Jinja2 template (like Flask render_template()).
        
        Now zWalker-aware: If route has zVaFile, it will be converted to URL and injected
        into template context for client-side loading (mixed mode support).
        
        Args:
            route: Route definition with "template" field and optional "context" dict
        
        Returns:
            None: Sends HTTP response directly
        """
        try:
            template_name = route.get("template", "")
            if not template_name:
                return self.send_error(500, "Template route missing 'template' field")
            
            # Get context data (variables to pass to template)
            context = route.get("context", {})
            
            # Get zcli instance from router
            if not hasattr(self.router, 'zcli'):
                return self.send_error(500, "zCLI instance not available")
            
            # Auto-inject zSession values (zVaFile, zVaFolder, zBlock) into context
            # so templates can render them without manual Jinja plumbing
            zcli = self.router.zcli
            if hasattr(zcli, 'session') and zcli.session:
                # Check if this is the root route "/" - if so, use zSpark defaults (not session)
                from urllib.parse import urlparse
                clean_path = urlparse(self.path).path
                is_root_route = (clean_path == "/" or clean_path == "")
                
                # Only inject if not already present in route context
                if "zVaFile" not in context:
                    if is_root_route and hasattr(zcli, 'spark') and zcli.spark:
                        # Root route: Use zSpark default (declarative, not stateful)
                        context["zVaFile"] = zcli.spark.get("zVaFile")
                    else:
                        # Other routes: Use session state (allows navigation memory)
                        context["zVaFile"] = zcli.session.get("zVaFile")
                
                if "zVaFolder" not in context:
                    if is_root_route and hasattr(zcli, 'spark') and zcli.spark:
                        context["zVaFolder"] = zcli.spark.get("zVaFolder")
                    else:
                        context["zVaFolder"] = zcli.session.get("zVaFolder")
                
                if "zBlock" not in context:
                    if is_root_route and hasattr(zcli, 'spark') and zcli.spark:
                        # Root route: Use zSpark default block (prevents session bleed)
                        context["zBlock"] = zcli.spark.get("zBlock")
                    else:
                        # Other routes: Use session state
                        context["zBlock"] = zcli.session.get("zBlock")
                
                # Debug: log what we got and from where
                if self.zcli_logger:
                    source = "zSpark (root route)" if is_root_route else "zSession"
                    self.zcli_logger.info(f"[Handler] Auto-injected from {source}: zVaFile={context.get('zVaFile')}, zVaFolder={context.get('zVaFolder')}, zBlock={context.get('zBlock')}")
            
            # Route-level overrides (opt-in): Explicit route config takes precedence
            # This allows routes to override zSpark/session defaults
            zVaFile = route.get("zVaFile")
            if zVaFile:
                ui_file_path = self._convert_zpath_to_url(zVaFile)
                context["zVaFile"] = ui_file_path
                if self.zcli_logger:
                    self.zcli_logger.debug(f"[Handler] Route override: zVaFile={ui_file_path}")
            
            zBlock = route.get("zBlock")
            if zBlock:
                context["zBlock"] = zBlock
                if self.zcli_logger:
                    self.zcli_logger.debug(f"[Handler] Route override: zBlock={zBlock}")
            
            # Get templates directory from serve_path (Flask convention)
            import os
            from jinja2 import Environment, FileSystemLoader, TemplateNotFound
            
            templates_dir = os.path.join(self.serve_path, self.template_folder)
            
            # Create Jinja2 environment
            env = Environment(loader=FileSystemLoader(templates_dir))
            
            # Add cache-busting timestamp
            import time
            context['timestamp'] = int(time.time() * 1000)
            
            # Render template
            template = env.get_template(template_name)
            html_content = template.render(**context)
            
            # Resolve navbar with route metadata fallback (same as zWalker routes)
            resolved_navbar = None
            if hasattr(zcli, 'navigation'):
                # Load the zVaFile to check its meta.zNavBar (if provided in context)
                zVaFile = context.get("zVaFile")
                zVaFolder = context.get("zVaFolder")
                try:
                    # Construct zPath from zVaFolder/zVaFile (e.g., "@.UI" + "zUI.zAbout" → "@.UI.zUI.zAbout")
                    if zVaFile and zVaFolder:
                        # Remove @ prefix and leading dots from folder
                        folder_parts = zVaFolder.lstrip('@.').split('.')
                        file_parts = zVaFile.split('.')
                        # Construct full zPath
                        zPath = '@.' + '.'.join(folder_parts + file_parts)
                        raw_zFile = zcli.loader.handle(zPath=zPath)
                        
                        # Extract zMeta section from YAML for client-side features (v1.5.13: _zScripts support)
                        if raw_zFile and isinstance(raw_zFile, dict):
                            meta_section = raw_zFile.get("zMeta", {})
                            if isinstance(meta_section, dict):
                                context["zVaFile_meta"] = meta_section
                                if self.zcli_logger:
                                    self.zcli_logger.info(f"[Handler] Extracted YAML zMeta for client: {list(meta_section.keys())}")
                            else:
                                context["zVaFile_meta"] = {}
                        else:
                            context["zVaFile_meta"] = {}
                    else:
                        raw_zFile = None
                    
                    # Get router meta for fallback
                    route_meta = self.router.meta if self.router and hasattr(self.router, 'meta') else {}
                    # Resolve navbar with priority chain (returns raw navbar with RBAC metadata)
                    resolved_navbar = zcli.navigation.resolve_navbar(raw_zFile, route_meta=route_meta) if raw_zFile else None
                    
                    # 🔒 RBAC Filter: Apply dynamic RBAC filtering for Bifrost (same as Terminal)
                    # This filters out items the current user can't access before injecting into HTML
                    if resolved_navbar:
                        resolved_navbar = zcli.navigation._filter_navbar_byzRBAC(resolved_navbar)
                        if self.zcli_logger:
                            self.zcli_logger.debug(f"[Handler] RBAC-filtered navbar for Bifrost: {resolved_navbar}")
                except Exception:
                    resolved_navbar = None
            
            # Auto-inject zUI config script before </head> (if zSession values present)
            # This makes zBifrost/zSession integration automatic for HTML authors
            zui_config_values = {
                "zVaFile": context.get("zVaFile"),
                "zVaFolder": context.get("zVaFolder"),
                "zBlock": context.get("zBlock"),
                "title": zcli.config.zSpark.get("title") if hasattr(zcli, 'config') and hasattr(zcli.config, 'zSpark') and zcli.config.zSpark else None,
                "zNavBar": resolved_navbar,  # Use RBAC-filtered navbar (clean strings only)
                "zMeta": context.get("zVaFile_meta", {})  # v1.5.13: Include YAML metadata for client features (_zScripts, etc)
            }
            # Only inject if at least one value is present (not all None)
            if any(v is not None for v in zui_config_values.values()):
                import json
                zui_config_json = json.dumps(zui_config_values, indent=4)
                zui_config_script = f'\n<!-- zUI Config (auto-injected from zSession) -->\n<script id="zui-config" type="application/json">\n{zui_config_json}\n</script>\n</head>'
                html_content = html_content.replace('</head>', zui_config_script, 1)
                if self.zcli_logger:
                    self.zcli_logger.info(f"[Handler] Auto-injected <script id='zui-config'> into HTML head")
            else:
                if self.zcli_logger:
                    self.zcli_logger.debug(f"[Handler] Skipped zui-config injection (all values None)")
            
            # Send HTML response
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-length", len(html_content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
        except TemplateNotFound as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Template not found: {e}")
            return self.send_error(404, f"Template not found: {template_name}")
        except Exception as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Template rendering error: {e}")
            return self.send_error(500, f"Template rendering failed: {str(e)}")
    
    def _handle_zwalker_route(self, route: dict):
        """
        Handle zWalker route - Execute zVaF blocks server-side using zVaF.html template.
        
        Supports hierarchical fallbacks: route → session
        - zVaFolder: route value OR session default
        - zVaFile: route value OR session default
        - zBlock: route value OR session default
        
        Args:
            route: Route definition with optional "context" dict
        
        Returns:
            None: Sends HTTP response directly
        """
        try:
            # Import needed modules
            import os
            from jinja2 import Environment, FileSystemLoader, TemplateNotFound
            
            # Get zcli instance for session access
            zcli = self.router.zcli if hasattr(self.router, 'zcli') else None
            
            # zWalker routes always use zVaF.html (full declarative mode)
            template_name = "zVaF.html"
            
            # Get context data (variables to pass to template)
            context = route.get("context", {})
            
            # NEW v1.5.12: Resolve _data queries at route level (Flask pattern)
            # This executes database queries BEFORE rendering, storing results in context
            if "_data" in route and zcli:
                resolved_data = self._resolve_route_data(route["_data"], zcli)
                if resolved_data:
                    context["_resolved_data"] = resolved_data
                    if hasattr(self, 'zcli_logger') and self.zcli_logger:
                        self.zcli_logger.info(f"[Handler] Resolved {len(resolved_data)} data queries for route")
            
            # Apply hierarchical fallbacks: route → zSpark (root) / session (other)
            # Route-level values override defaults
            if zcli:
                # Check if this is the root route "/" - if so, use zSpark defaults (not session)
                from urllib.parse import urlparse
                clean_path = urlparse(self.path).path
                is_root_route = (clean_path == "/" or clean_path == "")
                
                # Priority: route → zSpark (root) / session (other)
                if is_root_route and hasattr(zcli, 'spark') and zcli.spark:
                    # Root route: Use zSpark defaults (declarative, not stateful)
                    zVaFolder = route.get("zVaFolder") or zcli.spark.get("zVaFolder")
                    zVaFile = route.get("zVaFile") or zcli.spark.get("zVaFile")
                    zBlock = route.get("zBlock") or zcli.spark.get("zBlock")
                else:
                    # Other routes: Use session state (allows navigation memory)
                    zVaFolder = route.get("zVaFolder") or zcli.session.get("zVaFolder")
                    zVaFile = route.get("zVaFile") or zcli.session.get("zVaFile")
                    zBlock = route.get("zBlock") or zcli.session.get("zBlock")
                
                if hasattr(self, 'zcli_logger') and self.zcli_logger:
                    source = "zSpark (root)" if is_root_route else "zSession"
                    self.zcli_logger.debug(f"[Handler] zWalker resolved from {source} - Folder: {zVaFolder}, File: {zVaFile}, Block: {zBlock}")
            else:
                # No session available - use route values only
                zVaFolder = route.get("zVaFolder")
                zVaFile = route.get("zVaFile")
                zBlock = route.get("zBlock")
            
            # Store resolved values in context for template/future use
            if zVaFolder:
                context["zVaFolder"] = zVaFolder
            if zVaFile:
                context["zVaFile"] = zVaFile
            if zBlock:
                context["zBlock"] = zBlock
            
            # Store route metadata in session for zWalker access (navbar fallback)
            # This allows zWalker to check route-level meta.zNavBar as fallback
            if zcli and hasattr(zcli, 'session'):
                # Get router's route metadata (if exists)
                if self.router and hasattr(self.router, 'route_map'):
                    # Try to get route metadata from router
                    matched_route = self.router.route_map.get(self.path)
                    if not matched_route:
                        # Try auto-discovered routes
                        matched_route = self.router.auto_discovered_routes.get(self.path)
                    
                    if matched_route:
                        # Store route metadata for walker access
                        zcli.session['_route_meta'] = matched_route
                        
                # Also inject router meta (global route config) as fallback
                if self.router and hasattr(self.router, 'meta'):
                    zcli.session['_router_meta'] = self.router.meta
            
            # Get templates directory from serve_path
            templates_dir = os.path.join(self.serve_path, self.template_folder)
            
            # Create Jinja2 environment
            env = Environment(loader=FileSystemLoader(templates_dir))
            
            # Add cache-busting timestamp
            import time
            context['timestamp'] = int(time.time() * 1000)
            
            # Render template with context (Jinja2 support)
            template = env.get_template(template_name)
            html_content = template.render(**context)
            
            # Resolve navbar with route metadata fallback
            resolved_navbar = None
            if zcli and hasattr(zcli, 'navigation'):
                # Load the zVaFile to check its meta.zNavBar
                try:
                    # Construct zPath from zVaFolder/zVaFile (e.g., "@.UI" + "zUI.zAbout" → "@.UI.zUI.zAbout")
                    if zVaFile and zVaFolder:
                        # Remove @ prefix and leading dots from folder
                        folder_parts = zVaFolder.lstrip('@.').split('.')
                        file_parts = zVaFile.split('.')
                        # Construct full zPath
                        zPath = '@.' + '.'.join(folder_parts + file_parts)
                        raw_zFile = zcli.loader.handle(zPath=zPath)
                        
                        # Extract zMeta section from YAML for client-side features (v1.5.13: _zScripts support)
                        if raw_zFile and isinstance(raw_zFile, dict):
                            meta_section = raw_zFile.get("zMeta", {})
                            if isinstance(meta_section, dict):
                                context["zVaFile_meta"] = meta_section
                                if self.zcli_logger:
                                    self.zcli_logger.info(f"[Handler] Extracted YAML zMeta for client: {list(meta_section.keys())}")
                            else:
                                context["zVaFile_meta"] = {}
                        else:
                            context["zVaFile_meta"] = {}
                    else:
                        raw_zFile = None
                    
                    # Get router meta for fallback
                    route_meta = self.router.meta if self.router and hasattr(self.router, 'meta') else {}
                    # Resolve navbar with priority chain (returns raw navbar with RBAC metadata)
                    resolved_navbar = zcli.navigation.resolve_navbar(raw_zFile, route_meta=route_meta) if raw_zFile else None
                    
                    # 🔒 RBAC Filter: Apply dynamic RBAC filtering for Bifrost (same as Terminal)
                    # This filters out items the current user can't access before injecting into HTML
                    if resolved_navbar:
                        resolved_navbar = zcli.navigation._filter_navbar_byzRBAC(resolved_navbar)
                        if self.zcli_logger:
                            self.zcli_logger.debug(f"[Handler] RBAC-filtered navbar for zWalker route: {resolved_navbar}")
                except Exception as e:
                    if hasattr(self, 'zcli_logger') and self.zcli_logger:
                        self.zcli_logger.warning(f"[Handler] Could not resolve navbar: {e}")
                    resolved_navbar = None
            
            # Auto-inject zUI config script before </head> (same as template routes)
            zui_config_values = {
                "zVaFile": context.get("zVaFile"),
                "zVaFolder": context.get("zVaFolder"),
                "zBlock": context.get("zBlock"),
                "title": zcli.config.zSpark.get("title") if zcli and hasattr(zcli, 'config') and hasattr(zcli.config, 'zSpark') and zcli.config.zSpark else None,
                "zNavBar": resolved_navbar,  # Use RBAC-filtered navbar (clean strings only)
                "zMeta": context.get("zVaFile_meta", {}),  # v1.5.13: Include YAML metadata for client features (_zScripts, etc)
                "websocket": {
                    "ssl_enabled": zcli.config.websocket.ssl_enabled if zcli and hasattr(zcli, 'config') and hasattr(zcli.config, 'websocket') else False,
                    "host": zcli.config.websocket.host if zcli and hasattr(zcli, 'config') and hasattr(zcli.config, 'websocket') else "127.0.0.1",
                    "port": zcli.config.websocket.port if zcli and hasattr(zcli, 'config') and hasattr(zcli.config, 'websocket') else 8765
                }
            }
            if any(v is not None for v in zui_config_values.values()):
                import json
                zui_config_json = json.dumps(zui_config_values, indent=4)
                zui_config_script = f'\n<!-- zUI Config (auto-injected from zSession) -->\n<script id="zui-config" type="application/json">\n{zui_config_json}\n</script>\n</head>'
                html_content = html_content.replace('</head>', zui_config_script, 1)
                if self.zcli_logger:
                    self.zcli_logger.info(f"[Handler] zWalker route - Auto-injected zui-config: {zui_config_values}")
            
            # Send HTML response
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-length", len(html_content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
            if self.zcli_logger:
                self.zcli_logger.debug(f"[Handler] Served zWalker route: {self.path}")
            
        except TemplateNotFound as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Template not found: {e}")
            return self.send_error(404, f"Template not found: {template_name}")
        except Exception as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] zWalker rendering error: {e}")
            return self.send_error(500, f"zWalker rendering failed: {str(e)}")
    
    def _convert_zpath_to_url(self, zpath: str) -> str:
        """
        Convert zCLI zPath to URL path for client-side fetching.
        
        Args:
            zpath: zCLI path, can be:
                - Absolute: "@.UI.zUI.index.zVaF" (workspace/UI/zUI.index.yaml)
                - Relative: "zUI.index.zVaF" (assumes UI folder)
        
        Returns:
            str: URL path like "/ui/zUI.index.yaml"
        
        Note:
            The UI folder prefix is stripped since /ui/* already maps to UI/ folder.
            Dots in filenames are preserved (zUI.index.yaml).
        """
        original_path = zpath
        
        # Remove @ prefix (absolute path marker)
        if zpath.startswith("@."):
            zpath = zpath[2:]
        elif zpath.startswith("@"):
            zpath = zpath[1:]
        
        # Remove .zVaF suffix if present
        if zpath.endswith(".zVaF"):
            zpath = zpath[:-5]
        
        # Strip UI folder prefix if present (since /ui/* already maps to UI/)
        # Handles: "UI.zUI.index" or "UI/zUI.index"
        if zpath.startswith("UI."):
            zpath = zpath[3:]  # Remove "UI."
        elif zpath.startswith("UI/"):
            zpath = zpath[3:]  # Remove "UI/"
        
        # Add .yaml extension if not present
        if not zpath.endswith(".yaml"):
            zpath += ".yaml"
        
        # Build URL path (dots are preserved as part of filename)
        # Use actual ui_folder name for URL (case-sensitive)
        url_path = f"/{self.ui_folder}/{zpath}"
        
        # Log conversion for debugging
        if hasattr(self, 'zcli_logger') and self.zcli_logger:
            self.zcli_logger.debug(f"[Handler] zPath conversion: {original_path} → {url_path}")
        
        return url_path
    
    def _handle_dynamic_route(self, route: dict):
        """
        Handle dynamic route - render zUI to HTML.
        
        Args:
            route: Route definition with zVaFile and zBlock
        
        Returns:
            None: Sends HTTP response directly
        """
        try:
            # Extract zVaF file and block from route
            zVaFile = route.get("zVaFile", "")
            zBlock = route.get("zBlock", "zVaF")
            
            if not zVaFile:
                return self.send_error(500, "Dynamic route missing zVaFile")
            
            # Get zcli instance from router
            if not hasattr(self.router, 'zcli'):
                return self.send_error(500, "zCLI instance not available")
            
            # Import and create page renderer with routes for dual-mode navigation
            from .page_renderer import PageRenderer
            routes = self.router.routes.get('routes', {}) if hasattr(self.router, 'routes') else {}
            renderer = PageRenderer(self.router.zcli, routes=routes)
            
            # Render zUI to HTML
            html_content = renderer.render_page(zVaFile, zBlock)
            
            # Send HTML response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", len(html_content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            # Log error and send 500
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Dynamic route error: {e}")
            return self.send_error(500, f"Dynamic rendering failed: {str(e)}")
    
    def _handle_form_route(self, route: dict):
        """
        Handle form route - declarative web form processing (zDialog pattern).
        
        Args:
            route: Route definition with model, fields, onSubmit, etc.
        
        Returns:
            None: Sends HTTP response (redirect or error)
        """
        try:
            # Only accept POST for forms
            if self.command != 'POST':
                return self.send_error(405, "Form routes only accept POST")
            
            # Get zcli instance from router
            if not hasattr(self.router, 'zcli'):
                return self.send_error(500, "zCLI instance not available")
            
            # Read POST body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            content_type = self.headers.get('Content-Type', '')
            
            # Parse form data
            from .form_utils import parse_form_data, process_form_submission
            
            form_data = parse_form_data(body, content_type, self.zcli_logger)
            
            # Process form submission
            success, redirect_url, error_message = process_form_submission(
                route, form_data, self.router.zcli, self.zcli_logger
            )
            
            if success and redirect_url:
                # Redirect to success page
                self.send_response(303)  # See Other (POST-redirect-GET pattern)
                self.send_header("Location", redirect_url)
                self.end_headers()
            elif not success and redirect_url:
                # Redirect to error page with error message in query param
                error_url = f"{redirect_url}?error={error_message}" if error_message else redirect_url
                self.send_response(303)
                self.send_header("Location", error_url)
                self.end_headers()
            elif success:
                # No redirect specified - send success message
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                response_html = "<h1>Form submitted successfully</h1>"
                self.send_header("Content-length", len(response_html.encode('utf-8')))
                self.end_headers()
                self.wfile.write(response_html.encode('utf-8'))
            else:
                # No redirect specified - send error message
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                response_html = f"<h1>Form submission failed</h1><p>{error_message}</p>"
                self.send_header("Content-length", len(response_html.encode('utf-8')))
                self.end_headers()
                self.wfile.write(response_html.encode('utf-8'))
            
        except Exception as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] Form route error: {e}")
            return self.send_error(500, f"Form processing failed: {str(e)}")
    
    def _handle_json_route(self, route: dict):
        """
        Handle JSON route - declarative JSON response.
        
        Args:
            route: Route definition with data field
        
        Returns:
            None: Sends HTTP JSON response
        """
        try:
            # Get zcli instance from router
            if not hasattr(self.router, 'zcli'):
                return self.send_error(500, "zCLI instance not available")
            
            # Extract query parameters for placeholder resolution
            from .form_utils import extract_query_params
            query_params = extract_query_params(self.path)
            
            # Render JSON response
            from .json_utils import render_json_response
            
            body, status_code, headers = render_json_response(
                route, self.router.zcli, self.zcli_logger, query_params
            )
            
            # Send response
            self.send_response(status_code)
            for header_name, header_value in headers.items():
                self.send_header(header_name, header_value)
            self.end_headers()
            self.wfile.write(body)
            
        except Exception as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] JSON route error: {e}")
            return self.send_error(500, f"JSON rendering failed: {str(e)}")
    
    def _handle_zfunc_route(self, route: dict):
        """
        Handle zFunc route - call plugin function directly (for file uploads, API endpoints).
        
        Args:
            route: Route definition with handler field (&plugin.function)
        
        Returns:
            None: Sends HTTP response based on function return value
        """
        if hasattr(self, 'zcli_logger') and self.zcli_logger:
            self.zcli_logger.info(f"[Handler] _handle_zfunc_route called for: {route.get('handler', 'UNKNOWN')}")
        
        try:
            # Get zcli instance from router
            if not hasattr(self.router, 'zcli'):
                if self.zcli_logger:
                    self.zcli_logger.error("[Handler] No zcli instance on router")
                return self.send_error(500, "zCLI instance not available")
            
            # Get handler reference
            handler = route.get("handler", "")
            if self.zcli_logger:
                self.zcli_logger.info(f"[Handler] Got handler: {handler}")
            
            if not handler or not handler.startswith("&"):
                if self.zcli_logger:
                    self.zcli_logger.error(f"[Handler] Invalid handler: {handler}")
                return self.send_error(500, "Invalid handler reference - must start with &")
            
            # Parse handler reference: &plugin.function
            handler_parts = handler[1:].split(".")
            if len(handler_parts) != 2:
                if self.zcli_logger:
                    self.zcli_logger.error(f"[Handler] Invalid handler parts: {handler_parts}")
                return self.send_error(500, "Invalid handler format - expected &plugin.function")
            
            plugin_name, function_name = handler_parts
            if self.zcli_logger:
                self.zcli_logger.info(f"[Handler] Loading plugin: {plugin_name}, function: {function_name}")
            
            # Get plugin from loader's plugin cache
            zcli = self.router.zcli
            if self.zcli_logger:
                self.zcli_logger.info(f"[Handler] Got zcli from router")
            
            if not hasattr(zcli, 'loader') or not hasattr(zcli.loader, 'cache'):
                if self.zcli_logger:
                    self.zcli_logger.error("[Handler] Loader subsystem not available")
                return self.send_error(500, "Loader subsystem not available")
            
            # Try to get plugin from cache
            if self.zcli_logger:
                self.zcli_logger.info(f"[Handler] Loading plugin: {plugin_name}")
            
            plugin = zcli.loader.cache.plugin_cache.get(plugin_name)
            
            if not plugin:
                # Plugin not in cache, try to load it
                import os
                # Plugins are relative to the current working directory
                plugin_path = os.path.join(os.getcwd(), 'plugins', f'{plugin_name}.py')
                
                if self.zcli_logger:
                    self.zcli_logger.info(f"[Handler] Looking for plugin at: {plugin_path}")
                
                if not os.path.exists(plugin_path):
                    if self.zcli_logger:
                        self.zcli_logger.error(f"[Handler] Plugin file not found: {plugin_path}")
                    return self.send_error(500, f"Plugin '{plugin_name}' not found")
                
                try:
                    plugin = zcli.loader.cache.plugin_cache.load_and_cache(plugin_path, plugin_name)
                    if self.zcli_logger:
                        self.zcli_logger.info(f"[Handler] Plugin loaded from file: {plugin_name}")
                except Exception as load_err:
                    if self.zcli_logger:
                        self.zcli_logger.error(f"[Handler] Failed to load plugin: {load_err}", exc_info=True)
                    return self.send_error(500, f"Failed to load plugin '{plugin_name}': {str(load_err)}")
            
            if not plugin:
                if self.zcli_logger:
                    self.zcli_logger.error(f"[Handler] Plugin '{plugin_name}' returned None")
                return self.send_error(500, f"Plugin '{plugin_name}' not found")
            
            if self.zcli_logger:
                self.zcli_logger.info(f"[Handler] Plugin loaded successfully: {plugin_name}")
            
            # Get function from plugin
            if not hasattr(plugin, function_name):
                if self.zcli_logger:
                    self.zcli_logger.error(f"[Handler] Function '{function_name}' not found in plugin '{plugin_name}'")
                return self.send_error(500, f"Function '{function_name}' not found in plugin '{plugin_name}'")
            
            func = getattr(plugin, function_name)
            
            # Resolve schema (route-level 'model' overrides meta-level 'schema')
            schema_ref = route.get('model') or self.router.meta.get('schema')
            schema_context = None
            
            if schema_ref and schema_ref.startswith('@'):
                # Load schema from zData
                try:
                    # Schema reference format: @.zSchema.users
                    schema_name = schema_ref.split('.')[-1] if '.' in schema_ref else schema_ref[1:]
                    
                    # Try to get loaded schema from zServer's schema cache
                    if hasattr(self.router, 'zcli') and hasattr(self.router.zcli, 'data'):
                        # Get schema metadata
                        schema_context = {
                            'schema_name': schema_name,
                            'schema_ref': schema_ref,
                            'table_name': schema_name  # By convention
                        }
                        
                        if self.zcli_logger:
                            self.zcli_logger.debug(f"[Handler] Resolved schema for route: {schema_ref}")
                except Exception as e:
                    if self.zcli_logger:
                        self.zcli_logger.warning(f"[Handler] Failed to load schema {schema_ref}: {e}")
            
            # Build request context
            request_context = {
                'method': self.command,
                'path': self.path,
                'headers': dict(self.headers),
                'route': route,
                'route_params': route.get('_route_params', {}),
                'schema': schema_context  # Inject schema context
            }
            
            # Read request body for POST/PUT
            if self.command in ['POST', 'PUT', 'PATCH']:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    request_context['body'] = self.rfile.read(content_length)
                    request_context['content_type'] = self.headers.get('Content-Type', '')
            
            # Call function with zcli + request context as kwargs
            # Plugin signature: def my_function(zcli, **kwargs)
            if self.zcli_logger:
                self.zcli_logger.info(f"[Handler] Calling {plugin_name}.{function_name} with context keys: {list(request_context.keys())}")
            result = func(zcli, **request_context)
            
            # Handle response based on result type
            if isinstance(result, dict):
                # Check if binary response (Phase 3.2 - media delivery)
                if '_binary' in result:
                    # Binary response (images, files, etc.)
                    binary_data = result['_binary']
                    mimetype = result.get('_mimetype', 'application/octet-stream')
                    status_code = result.get('status_code', 200)
                    
                    self.send_response(status_code)
                    self.send_header('Content-Type', mimetype)
                    self.send_header('Content-Length', len(binary_data))
                    self.end_headers()
                    self.wfile.write(binary_data)
                else:
                    # JSON response
                    import json
                    body = json.dumps(result).encode('utf-8')
                    self.send_response(result.get('status_code', 200))
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', len(body))
                    self.end_headers()
                    self.wfile.write(body)
            elif isinstance(result, str):
                # Plain text response
                body = result.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Length', len(body))
                self.end_headers()
                self.wfile.write(body)
            elif isinstance(result, bytes):
                # Binary response
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', len(result))
                self.end_headers()
                self.wfile.write(result)
            else:
                # Assume success with no body
                self.send_response(204)
                self.end_headers()
            
        except Exception as e:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.error(f"[Handler] zFunc route error: {e}", exc_info=True)
            return self.send_error(500, f"Function execution failed: {str(e)}")
    
    def _resolve_route_data(self, data_block: dict, zcli: any) -> dict:
        """
        Execute data queries defined in route _data block (Flask pattern).
        
        This is the route-level equivalent of Flask's:
            @app.route('/account')
            def account():
                user = User.query.filter_by(email=session['email']).first()
                return render_template('account.html', user=user)
        
        Args:
            data_block: _data section from route definition
            zcli: zCLI instance for data access
        
        Returns:
            Dictionary of query results: {"user": {...}, "stats": [...]}
        
        Examples:
            # In zServer.routes.yaml:
            routes:
              "/account":
                _data:
                  user: "@.models.zSchema.contacts"  # Model reference
                  # OR
                  stats:
                    zData:  # Explicit query
                      action: read
                      model: "@.models.zSchema.user_stats"
        """
        results = {}
        
        if not zcli:
            if hasattr(self, 'zcli_logger') and self.zcli_logger:
                self.zcli_logger.warning("[Handler] No zCLI instance - cannot resolve _data")
            return results
        
        for key, query_def in data_block.items():
            try:
                # Handle shorthand: user: "@.models.zSchema.contacts"
                if isinstance(query_def, str) and query_def.startswith('@.models.'):
                    # Shorthand model reference - convert to zData request
                    # Auto-filter by authenticated user ID for security
                    
                    # Get authenticated user ID from zAuth (supports 3-layer architecture)
                    zauth = zcli.session.get('zAuth', {})
                    active_app = zauth.get('active_app')
                    
                    # Try app-specific auth first (applications layer)
                    if active_app:
                        app_auth = zauth.get('applications', {}).get(active_app, {})
                        user_id = app_auth.get('id')
                    else:
                        # Fallback to Zolo platform auth (zSession layer - future SSO)
                        user_id = zauth.get('zSession', {}).get('id')
                    
                    query_def = {
                        "zData": {
                            "action": "read",
                            "model": query_def,
                            "options": {
                                "where": f"id = {user_id}" if user_id else "1 = 0",  # Security: no ID = no results
                                "limit": 1
                            }
                        }
                    }
                
                # Handle explicit zData block
                if isinstance(query_def, dict) and "zData" in query_def:
                    # Execute zData query in SILENT mode (v1.5.12)
                    # Silent mode: returns rows without displaying, works in any zMode
                    query_def["zData"]["silent"] = True
                    
                    result = zcli.data.handle_request(query_def["zData"])
                    
                    # Extract first record if limit=1 (single record query)
                    if isinstance(result, list) and query_def["zData"].get("options", {}).get("limit") == 1 and len(result) > 0:
                        results[key] = result[0]  # Return dict instead of list for single record
                    else:
                        results[key] = result
                    
                    if hasattr(self, 'zcli_logger') and self.zcli_logger:
                        result_type = type(results[key]).__name__
                        result_count = len(result) if isinstance(result, list) else 1
                        self.zcli_logger.debug(f"[Handler] Query '{key}' returned {result_type} ({result_count} records)")
                else:
                    if hasattr(self, 'zcli_logger') and self.zcli_logger:
                        self.zcli_logger.warning(f"[Handler] Invalid _data entry: {key}")
                    results[key] = None
                    
            except Exception as e:
                if hasattr(self, 'zcli_logger') and self.zcli_logger:
                    self.zcli_logger.error(f"[Handler] Query '{key}' failed: {e}")
                results[key] = None
        
        return results

