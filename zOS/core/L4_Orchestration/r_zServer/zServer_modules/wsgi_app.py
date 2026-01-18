# zCLI/subsystems/zServer/zServer_modules/wsgi_app.py

"""
WSGI Application for zServer Production Mode

Minimal WSGI adapter that bridges Gunicorn to zServer's handler logic.
NO code duplication - reuses existing handler, router, and renderer.
"""

from typing import Any, Callable, Iterable, List, Tuple


class zServerWSGIApp:
    """
    WSGI application for zServer (called by Gunicorn in Production).
    
    This is a thin translation layer that adapts WSGI interface to
    zServer's existing handler logic. All routing, rendering, and
    file serving logic is reused from the handler - zero duplication.
    
    Attributes:
        zserver: zServer instance with router, logger, etc.
        router: HTTPRouter instance (from zserver)
        logger: Logger instance (from zserver)
    """
    
    def __init__(self, zserver: Any):
        """
        Initialize WSGI application.
        
        Args:
            zserver: zServer instance providing router, logger, serve_path, etc.
        """
        self.zserver = zserver
        self.router = zserver.router
        self.logger = zserver.logger
        self.serve_path = zserver.serve_path
        self.static_folder = zserver.static_folder
        self.template_folder = zserver.template_folder
        self.static_mounts = zserver.static_mounts  # v1.5.11: Multi-mount support
    
    def __call__(
        self, 
        environ: dict, 
        start_response: Callable
    ) -> Iterable[bytes]:
        """
        WSGI application callable.
        
        Called by Gunicorn for each HTTP request. Translates WSGI environ
        to zServer's routing logic, then converts response back to WSGI format.
        
        Args:
            environ: WSGI environment dict (HTTP request info)
            start_response: WSGI start_response callable
        
        Returns:
            Iterable[bytes]: Response body
        """
        # Extract request info from WSGI environ
        path = environ.get('PATH_INFO', '/')
        method = environ.get('REQUEST_METHOD', 'GET')
        
        try:
            # Handle request using zServer's existing logic
            status, headers, body = self._handle_request(path, method, environ)
            
            # Convert to WSGI format
            start_response(status, headers)
            return [body]
        
        except Exception as e:
            # Error handling
            self.logger.error(f"[WSGI] Error handling request {path}: {e}")
            return self._error_response(start_response, 500, str(e))
    
    def _handle_request(
        self, 
        path: str, 
        method: str, 
        environ: dict
    ) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """
        Handle HTTP request using zServer's router and handler logic.
        
        This method orchestrates the request handling by reusing existing
        zServer components (router, renderer, file serving).
        
        Args:
            path: HTTP request path
            method: HTTP request method
            environ: WSGI environment dict
        
        Returns:
            Tuple of (status_line, headers, body)
        """
        # Check custom static mounts FIRST (v1.5.11: User-defined mount points)
        for url_prefix, fs_path in self.static_mounts.items():
            if path.startswith(url_prefix):
                return self._handle_mounted_file(path, url_prefix, fs_path)
        
        # Handle /static/* files directly (Flask convention)
        if path.startswith('/static/'):
            return self._handle_static_file(path)
        
        # Handle favicon.ico
        if path == '/favicon.ico':
            return self._handle_favicon()
        
        # Check if router exists
        if not self.router:
            return self._error_response_tuple(404, "No routes configured")
        
        # Route matching (uses existing HTTPRouter)
        route = self.router.match_route(path)
        if not route:
            return self._error_response_tuple(404, f"Route not found: {path}")
        
        # RBAC check (uses existing zAuth integration)
        has_access, error_page = self.router.check_access(route)
        if not has_access:
            return self._error_response_tuple(403, "Access Denied")
        
        # Handle based on route type
        route_type = route.get('type', 'static')
        
        if route_type == 'template':
            return self._handle_template_route(route)
        elif route_type == 'zWalker':
            # zWalker: Execute zVaF blocks server-side (Phase 1.2+)
            # For now, just render the template (full execution comes in Phase 3)
            return self._handle_template_route(route)
        elif route_type == 'static':
            return self._handle_static_route(route)
        elif route_type == 'content':
            return self._handle_content_route(route)
        elif route_type == 'form':
            return self._handle_form_route(route, method, environ)
        elif route_type == 'json':
            return self._handle_json_route(route, path)
        elif route_type == 'dynamic':
            return self._handle_dynamic_route(route)
        else:
            return self._error_response_tuple(501, f"Route type '{route_type}' not supported")
    
    def _handle_template_route(self, route: dict) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """Handle template route using Jinja2."""
        try:
            from jinja2 import Environment, FileSystemLoader
            import os
            
            template_name = route.get("template", "")
            context = route.get("context", {})
            
            templates_dir = os.path.join(self.serve_path, self.template_folder)
            env = Environment(loader=FileSystemLoader(templates_dir))
            template = env.get_template(template_name)
            html_content = template.render(**context)
            
            body = html_content.encode('utf-8')
            headers = [
                ('Content-Type', 'text/html; charset=utf-8'),
                ('Content-Length', str(len(body))),
            ]
            
            return ('200 OK', headers, body)
        
        except Exception as e:
            self.logger.error(f"[WSGI] Template error: {e}")
            return self._error_response_tuple(500, f"Template error: {str(e)}")
    
    def _handle_static_route(self, route: dict) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """Handle static file route."""
        try:
            import os
            import mimetypes
            
            file_path = self.router.resolve_file_path(route)
            
            if not os.path.exists(file_path):
                return self._error_response_tuple(404, f"File not found: {file_path}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            headers = [
                ('Content-Type', content_type),
                ('Content-Length', str(len(content))),
            ]
            
            return ('200 OK', headers, content)
        
        except Exception as e:
            self.logger.error(f"[WSGI] Static file error: {e}")
            return self._error_response_tuple(500, f"File error: {str(e)}")
    
    def _handle_content_route(self, route: dict) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """Handle inline content route."""
        html_content = route.get("content", "")
        body = html_content.encode('utf-8')
        
        headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(body))),
        ]
        
        return ('200 OK', headers, body)
    
    def _handle_dynamic_route(self, route: dict) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """Handle dynamic zWalker route."""
        try:
            from .page_renderer import PageRenderer
            
            zVaFile = route.get("zVaFile", "")
            zBlock = route.get("zBlock", "zVaF")
            
            routes = self.router.routes.get('routes', {}) if hasattr(self.router, 'routes') else {}
            renderer = PageRenderer(self.zserver.zcli, routes=routes)
            html_content = renderer.render_page(zVaFile, zBlock)
            
            body = html_content.encode('utf-8')
            headers = [
                ('Content-Type', 'text/html; charset=utf-8'),
                ('Content-Length', str(len(body))),
            ]
            
            return ('200 OK', headers, body)
        
        except Exception as e:
            self.logger.error(f"[WSGI] Dynamic route error: {e}")
            return self._error_response_tuple(500, f"Dynamic rendering error: {str(e)}")
    
    def _error_response_tuple(
        self, 
        code: int, 
        message: str
    ) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """Create error response tuple."""
        status_map = {
            403: '403 Forbidden',
            404: '404 Not Found',
            500: '500 Internal Server Error',
            501: '501 Not Implemented',
        }
        
        status = status_map.get(code, f'{code} Error')
        html = f"<html><body><h1>{status}</h1><p>{message}</p></body></html>"
        body = html.encode('utf-8')
        
        headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(body))),
        ]
        
        return (status, headers, body)
    
    def _handle_mounted_file(
        self, 
        path: str, 
        url_prefix: str, 
        fs_root: str
    ) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """
        Handle custom mount point requests (v1.5.11: Multi-mount support).
        
        Generic mount handler for WSGI/Production mode.
        Serves files from any configured filesystem location with security checks.
        
        Args:
            path: Request path (e.g., "/bifrost/src/client.js")
            url_prefix: Mount URL prefix (e.g., "/bifrost/")
            fs_root: Filesystem root path (absolute)
        
        Returns:
            Tuple of (status_line, headers, body)
        
        Security:
            - Directory traversal protection
            - No directory listing
            - File existence validation
        """
        try:
            import os
            import mimetypes
            from urllib.parse import unquote
            
            # Remove URL prefix to get relative path within mount
            relative_path = path[len(url_prefix):]
            
            # Decode URL encoding
            relative_path = unquote(relative_path)
            
            # Build absolute path within mount
            file_path = os.path.join(fs_root, relative_path)
            
            # Security: Prevent directory traversal
            file_path = os.path.abspath(file_path)
            mount_root = os.path.abspath(fs_root)
            
            if not file_path.startswith(mount_root):
                self.logger.warning(f"[WSGI] Directory traversal attempt blocked: {path}")
                return self._error_response_tuple(403, "Access denied")
            
            # Check if file exists
            if not os.path.exists(file_path):
                return self._error_response_tuple(404, f"File not found: {path}")
            
            # Check if it's a directory
            if os.path.isdir(file_path):
                return self._error_response_tuple(403, "Directory listing is disabled")
            
            # Serve the file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            headers = [
                ('Content-Type', content_type),
                ('Content-Length', str(len(content))),
            ]
            
            # Disable caching for JS files during development
            if file_path.endswith('.js'):
                headers.append(('Cache-Control', 'no-cache, no-store, must-revalidate'))
            else:
                headers.append(('Cache-Control', 'public, max-age=3600'))
            
            return ('200 OK', headers, content)
        
        except Exception as e:
            self.logger.error(f"[WSGI] Error serving mounted file {path}: {e}")
            return self._error_response_tuple(500, f"Error serving file: {str(e)}")
    
    def _handle_static_file(self, path: str) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """Handle /static/* requests (Flask convention)."""
        try:
            import os
            import mimetypes
            
            # Remove /static/ prefix and build file path
            file_rel_path = path[8:]  # Remove "/static/"
            file_path = os.path.join(self.serve_path, self.static_folder, file_rel_path)
            
            if not os.path.exists(file_path):
                return self._error_response_tuple(404, f"Static file not found: {path}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            headers = [
                ('Content-Type', content_type),
                ('Content-Length', str(len(content))),
            ]
            
            return ('200 OK', headers, content)
        
        except Exception as e:
            self.logger.error(f"[WSGI] Error serving static file {path}: {e}")
            return self._error_response_tuple(500, f"Error serving static file: {str(e)}")
    
    def _handle_favicon(self) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """Handle /favicon.ico request."""
        try:
            import os
            
            # Try to serve favicon from static folder
            favicon_path = os.path.join(self.serve_path, self.static_folder, 'favicon.ico')
            
            if os.path.exists(favicon_path):
                with open(favicon_path, 'rb') as f:
                    content = f.read()
                
                headers = [
                    ('Content-Type', 'image/x-icon'),
                    ('Content-Length', str(len(content))),
                ]
                
                return ('200 OK', headers, content)
            else:
                # Return 404 for missing favicon
                return self._error_response_tuple(404, "Favicon not found")
        
        except Exception as e:
            self.logger.error(f"[WSGI] Error serving favicon: {e}")
            return self._error_response_tuple(500, f"Error serving favicon: {str(e)}")
    
    def _handle_form_route(
        self, 
        route: dict, 
        method: str, 
        environ: dict
    ) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """
        Handle form route - declarative web form processing (zDialog pattern).
        
        Args:
            route: Route definition with model, fields, onSubmit, etc.
            method: HTTP method
            environ: WSGI environment dict
        
        Returns:
            Tuple of (status_line, headers, body)
        """
        try:
            # Only accept POST for forms
            if method != 'POST':
                return self._error_response_tuple(405, "Form routes only accept POST")
            
            # Read POST body
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            body = environ['wsgi.input'].read(content_length)
            content_type = environ.get('CONTENT_TYPE', '')
            
            # Parse form data
            from .form_utils import parse_form_data, process_form_submission
            
            form_data = parse_form_data(body, content_type, self.logger)
            
            # Process form submission
            success, redirect_url, error_message = process_form_submission(
                route, form_data, self.zserver.zcli, self.logger
            )
            
            if success and redirect_url:
                # Redirect to success page (303 See Other)
                return self._redirect_response(redirect_url)
            elif not success and redirect_url:
                # Redirect to error page with error message
                error_url = f"{redirect_url}?error={error_message}" if error_message else redirect_url
                return self._redirect_response(error_url)
            elif success:
                # No redirect - send success message
                html = "<h1>Form submitted successfully</h1>"
                body = html.encode('utf-8')
                headers = [
                    ('Content-Type', 'text/html; charset=utf-8'),
                    ('Content-Length', str(len(body))),
                ]
                return ('200 OK', headers, body)
            else:
                # No redirect - send error message
                html = f"<h1>Form submission failed</h1><p>{error_message}</p>"
                body = html.encode('utf-8')
                headers = [
                    ('Content-Type', 'text/html; charset=utf-8'),
                    ('Content-Length', str(len(body))),
                ]
                return ('400 Bad Request', headers, body)
        
        except Exception as e:
            self.logger.error(f"[WSGI] Form route error: {e}")
            return self._error_response_tuple(500, f"Form processing failed: {str(e)}")
    
    def _handle_json_route(
        self, 
        route: dict, 
        path: str
    ) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """
        Handle JSON route - declarative JSON response.
        
        Args:
            route: Route definition with data field
            path: Request path (for query param extraction)
        
        Returns:
            Tuple of (status_line, headers, body)
        """
        try:
            # Extract query parameters
            from .form_utils import extract_query_params
            query_params = extract_query_params(path)
            
            # Render JSON response
            from .json_utils import render_json_response
            
            body, status_code, headers_dict = render_json_response(
                route, self.zserver.zcli, self.logger, query_params
            )
            
            # Convert headers dict to list of tuples
            headers = [(k, v) for k, v in headers_dict.items()]
            
            # Convert status code to WSGI status line
            status_map = {
                200: '200 OK',
                201: '201 Created',
                400: '400 Bad Request',
                404: '404 Not Found',
                500: '500 Internal Server Error',
            }
            status_line = status_map.get(status_code, f'{status_code} Status')
            
            return (status_line, headers, body)
        
        except Exception as e:
            self.logger.error(f"[WSGI] JSON route error: {e}")
            return self._error_response_tuple(500, f"JSON rendering failed: {str(e)}")
    
    def _redirect_response(
        self, 
        location: str
    ) -> Tuple[str, List[Tuple[str, str]], bytes]:
        """Create redirect response (303 See Other for POST-redirect-GET)."""
        headers = [
            ('Location', location),
            ('Content-Length', '0'),
        ]
        return ('303 See Other', headers, b'')
    
    def _error_response(
        self, 
        start_response: Callable, 
        code: int, 
        message: str
    ) -> Iterable[bytes]:
        """Create error response for WSGI."""
        status, headers, body = self._error_response_tuple(code, message)
        start_response(status, headers)
        return [body]


# Module exports
__all__ = ['zServerWSGIApp']

