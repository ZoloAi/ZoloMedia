# zCLI/subsystems/zServer/zServer.py

"""
zServer - Lightweight HTTP Static File Server

Serves static files using Python's built-in http.server.
Designed to work standalone or alongside zBifrost WebSocket server.
"""

from http.server import HTTPServer
import threading
import os
from pathlib import Path
from functools import partial

from .zServer_modules.handler import LoggingHTTPRequestHandler
from zOS.L1_Foundation.b_zComm.zComm_modules.comm_ssl import create_ssl_context


class zServer:
    """
    Lightweight HTTP static file server
    
    Features:
    - Serves static files (HTML, CSS, JS)
    - Runs in background thread
    - Integrates with zCLI logger
    - CORS enabled for local development
    - Directory listing disabled for security
    """
    
    def __init__(self, logger, *, zcli, config=None, port=None, host=None, serve_path=None, 
                 static_folder=None, template_folder=None, routes_file=None):
        """
        Initialize zServer subsystem (v1.5.8: Independent subsystem with config object support).
        
        Args:
            logger: zCLI logger instance
            zcli: zCLI instance (required for routing, auth, data integration)
            config: HttpServerConfig instance from zConfig (preferred, enables full integration)
            port: HTTP port (deprecated: use config object)
            host: Host address (deprecated: use config object)
            serve_path: Directory to serve files from (deprecated: use config object)
            static_folder: Static files folder (deprecated: use config object)
            template_folder: Jinja2 templates folder (deprecated: use config object)
            routes_file: Optional zServer.*.yaml file (deprecated: use config object)
        
        Note:
            Prefer using config object for full zCLI integration.
            Individual parameters supported for backward compatibility and testing.
        """
        self.logger = logger
        self.zcli = zcli
        
        # Extract configuration from config object (preferred) or individual parameters (backward compat)
        if config:
            # New pattern: config object from zConfig
            self.enabled = config.enabled  # Check if server is enabled
            self.port = config.port
            self.host = config.host
            self.serve_path = config.serve_path
            self.routes_file = config.routes_file  # Kept for backward compatibility
            # SSL Configuration (v1.5.10: HTTPS support)
            self.ssl_enabled = config.ssl_enabled
            self.ssl_cert = config.ssl_cert
            self.ssl_key = config.ssl_key
            # Static Mounts (v1.5.11: Multi-mount support)
            self.static_mounts = config.static_mounts.copy() if config.static_mounts else {}
        else:
            # Backward compatibility: individual parameters (assume enabled if instantiated this way)
            self.enabled = True
            self.port = port if port is not None else 8080
            self.host = host if host is not None else "127.0.0.1"
            serve_path = serve_path if serve_path is not None else "."
            self.routes_file = routes_file  # Kept for backward compatibility
            # SSL disabled by default in backward compat mode
            self.ssl_enabled = False
            self.ssl_cert = None
            self.ssl_key = None
            # No static mounts in backward compat mode
            self.static_mounts = {}
        
        self.router = None
        self.static_folder = static_folder if static_folder is not None else "static"
        self.template_folder = template_folder if template_folder is not None else "templates"
        self.ui_folder = "UI"  # zUI zVaF files folder (convention)
        
        
        # Resolve serve_path, handling case where path may not exist yet or cwd deleted
        if config:
            # Config object already has resolved path
            self.serve_path = str(Path(self.serve_path).resolve()) if self.serve_path else str(Path.cwd())
        else:
            # Backward compat: resolve the serve_path parameter
            try:
                self.serve_path = str(Path(serve_path).resolve())
            except (FileNotFoundError, OSError):
                # Path doesn't exist or cwd deleted (common in test cleanup) - use path as-is
                # If relative, it will be relative to wherever we are when server starts
                self.serve_path = str(Path(serve_path))
        
        # Auto-mount bifrost client folder for /bifrost/ URL access (v1.5.13)
        if "/bifrost/" not in self.static_mounts:
            import os
            # Try common locations: 
            # 1. {zOS_package}/bifrost (new location as of v1.5.8+)
            # 2. {cwd}/bifrost (backwards compatibility)
            try:
                # Get zOS package root (parent of core/)
                zos_root = Path(__file__).parent.parent.parent.parent
                potential_bifrost_paths = [
                    zos_root / "bifrost",  # New: zOS/bifrost/
                    Path.cwd() / "bifrost"  # Old: {cwd}/bifrost
                ]
            except Exception:
                potential_bifrost_paths = [Path.cwd() / "bifrost"]
            
            for bifrost_path in potential_bifrost_paths:
                if bifrost_path.is_dir():
                    self.static_mounts["/bifrost/"] = str(bifrost_path)
                    self.logger.info(f"[zServer] Auto-mounted bifrost: /bifrost/ → {bifrost_path}")
                    break
        
        # Auto-mount plugins folder for JavaScript plugin access (v1.5.13)
        # This enables _zScripts metadata to reference plugins via /plugins/plugin_name.js
        if "/plugins/" not in self.static_mounts:
            import os
            # Try common locations: {serve_path}/plugins, zCloud/plugins, {cwd}/plugins
            potential_plugin_paths = [
                os.path.join(self.serve_path, "plugins"),
                os.path.join(str(Path.cwd()), "zCloud", "plugins"),
                os.path.join(str(Path.cwd()), "plugins")
            ]
            
            for plugin_path in potential_plugin_paths:
                if os.path.isdir(plugin_path):
                    self.static_mounts["/plugins/"] = plugin_path
                    self.logger.info(f"[zServer] Auto-mounted plugins: /plugins/ → {plugin_path}")
                    break
        
        # ONLY load routes/schemas if zServer is enabled (opt-in subsystem)
        # This prevents route/schema loading noise in Terminal mode
        if self.enabled:
            # Auto-detect ALL zServer routes files (v1.5.9: Blueprint pattern)
            # Supports both root folder AND routes/ subfolder
            if not routes_file:
                # New pattern: Auto-detect ALL zServer.*.yaml files in both locations
                self.routes_files = self._auto_detect_routes_files()
            else:
                # Backward compatibility: Single routes_file provided explicitly
                # Convert to list format for consistent handling
                self.routes_files = [routes_file] if routes_file else []
        else:
            # Not enabled - initialize empty routes
            self.routes_files = []
            if routes_file:
                self.logger.info(f"[zServer] Using explicitly provided routes file: {routes_file}")
        
        # Load routes if any were provided or auto-detected (v1.5.9: Blueprint pattern)
        if self.routes_files and zcli:
            self._load_routes()
        
        # Auto-initialize database schemas from models/ folder (v1.5.8: Convention over configuration)
        if zcli:
            self._auto_initialize_schemas()
                    
            self.logger.info(f"[zServer] Initialized - will serve from: {self.serve_path}")
            self.logger.info(f"[zServer] Static folder: {self.static_folder}/")
            self.logger.info(f"[zServer] Template folder: {self.template_folder}/")
            self.logger.info(f"[zServer] UI folder: {self.ui_folder}/")
            if self.static_mounts:
                self.logger.info(f"[zServer] Custom mounts: {len(self.static_mounts)} registered")
                for url_prefix, fs_path in self.static_mounts.items():
                    self.logger.info(f"[zServer]   {url_prefix} → {fs_path}")
            if self.router:
                self.logger.info(f"[zServer] Declarative routing enabled: {routes_file}")
        else:
            self.routes_files = []
            self.logger.debug(f"[zServer] Disabled - skipping route/schema loading")
        
        self.server = None
        self.thread = None
        self._running = False
        self.gunicorn_manager = None  # For Production mode
    
    def _auto_detect_routes_files(self):
        """
        Auto-detect ALL zServer routing files in serve_path (v1.5.9: Blueprint pattern).
        
        Scans BOTH root folder AND routes/ subfolder for ALL zServer.*.yaml files,
        following Flask blueprint-style modular routing.
        
        Convention:
            - Root folder: Primary routes (e.g., zServer.routes.yaml)
            - routes/ folder: Modular blueprints (e.g., zServer.api.yaml, zServer.themes.yaml)
        
        Returns:
            list: List of detected routes files (paths relative to serve_path), or empty list
        """
        import glob
        
        found_files = []
        
        try:
            # 1. Look for zServer.*.yaml in ROOT folder
            root_pattern = os.path.join(self.serve_path, "zServer.*.yaml")
            root_matches = glob.glob(root_pattern)
            
            for match in root_matches:
                # Store relative path from serve_path
                rel_path = os.path.basename(match)
                found_files.append(rel_path)
                self.logger.framework.debug(f"[zServer] Found routes file (root): {rel_path}")
            
            # 2. Look for zServer.*.yaml in ROUTES/ subfolder
            routes_dir = os.path.join(self.serve_path, "routes")
            if os.path.isdir(routes_dir):
                routes_pattern = os.path.join(routes_dir, "zServer.*.yaml")
                routes_matches = glob.glob(routes_pattern)
                
                for match in routes_matches:
                    # Store relative path from serve_path (includes "routes/" prefix)
                    rel_path = os.path.relpath(match, self.serve_path)
                    found_files.append(rel_path)
                    self.logger.framework.debug(f"[zServer] Found routes file (routes/): {rel_path}")
            
            if found_files:
                self.logger.info(f"[zServer] Detected {len(found_files)} route file(s): {found_files}")
            else:
                self.logger.framework.debug("[zServer] No zServer.*.yaml files found - static serving only")
            
            return found_files
            
        except Exception as e:
            self.logger.framework.debug(f"[zServer] Auto-detection failed: {e}")
            return []
    
    def _load_routes(self):
        """
        Load routing configuration from ALL zServer.*.yaml files (v1.5.9: Blueprint pattern).
        
        Supports Flask-style blueprints: multiple route files are merged into a single router.
        Last-loaded file wins for conflicting routes.
        
        Uses zParser to load and parse routing files directly (bypassing zLoader's
        zPath decoder to avoid dot interpretation in filenames like zServer.routes.yaml).
        """
        if not self.routes_files or len(self.routes_files) == 0:
            self.logger.framework.debug("[zServer] No routes files to load - static serving only")
            return
        
        try:
            from zOS.L2_Core.g_zParser.parser_modules import parse_file_content
            from zOS.L2_Core.h_zLoader.loader_modules import load_file_raw
            
            # Merged routes structure (blueprint pattern)
            merged_data = {
                "type": "server",
                "meta": {},
                "routes": {}
            }
            
            # Load and merge all route files
            for routes_file in self.routes_files:
                try:
                    # Build full path (routes_file is relative to serve_path)
                    full_path = os.path.join(self.serve_path, routes_file)
                    
                    # Read raw file content
                    raw_content = load_file_raw(full_path, self.logger)
                    
                    # Parse content (zParser will detect zServer in path and parse as server file)
                    routes_data = parse_file_content(
                        raw_content,
                        self.logger,
                        file_extension=".yaml",
                        file_path=full_path
                    )
                    
                    if routes_data and routes_data.get("type") == "server":
                        # Merge meta (later files override earlier files)
                        if "meta" in routes_data:
                            merged_data["meta"].update(routes_data["meta"])
                        
                        # Merge routes (later files override earlier files)
                        if "routes" in routes_data:
                            route_count = len(routes_data["routes"])
                            merged_data["routes"].update(routes_data["routes"])
                            self.logger.info(f"[zServer] Loaded {route_count} routes from: {routes_file}")
                    else:
                        self.logger.warning(f"[zServer] Invalid routes file: {routes_file}")
                
                except Exception as e:
                    self.logger.error(f"[zServer] Failed to load routes from {routes_file}: {e}")
                    # Continue loading other files
            
            # Create router with merged routes
            total_routes = len(merged_data["routes"])
            if total_routes > 0:
                from .zServer_modules.router import HTTPRouter
                self.router = HTTPRouter(merged_data, self.zcli, self.logger, serve_path=self.serve_path)
                self.logger.info(f"[zServer] Router initialized with {total_routes} total routes from {len(self.routes_files)} file(s)")
            else:
                self.logger.warning("[zServer] No valid routes found - static serving only")
            
        except Exception as e:
            self.logger.error(f"[zServer] Failed to load routes: {e}")
            # Continue without router (fallback to static serving)
    
    def _auto_initialize_schemas(self):
        """
        Auto-detect and initialize database schemas from models/ folder (v1.5.8).
        
        Convention: models/zSchema.*.yaml files are auto-initialized on server start.
        This follows the same pattern as zServer.*.yaml auto-detection for routes.
        
        For each schema found:
        1. Load schema via zLoader
        2. Initialize database adapter
        3. Ensure tables exist (create if missing)
        
        Note:
            - Errors are logged but don't stop server startup
            - Multiple databases are supported (different Data_Path per schema)
            - Tables are only created if they don't exist (idempotent)
        """
        import glob
        
        # Find models folder
        models_path = os.path.join(self.serve_path, "models")
        if not os.path.exists(models_path):
            self.logger.debug("[zServer] No models/ folder found, skipping schema auto-initialization")
            return
        
        # Find all schema files
        pattern = os.path.join(models_path, "zSchema.*.yaml")
        schema_files = glob.glob(pattern)
        
        if not schema_files:
            self.logger.debug("[zServer] No zSchema files found in models/")
            return
        
        self.logger.info(f"[zServer] Found {len(schema_files)} schema file(s) in models/")
        
        # Initialize each schema
        for schema_file in schema_files:
            try:
                # Extract filename
                filename = os.path.basename(schema_file)
                
                # Load schema directly (avoid zPath interpretation of dots in filename)
                self.logger.info(f"[zServer] Loading schema: {filename}")
                
                # Use zParser directly to avoid zPath dot interpretation
                from zOS.L2_Core.g_zParser.parser_modules import parse_file_content
                from zOS.L2_Core.h_zLoader.loader_modules import load_file_raw
                
                # Read raw file content
                raw_content = load_file_raw(schema_file, self.logger)
                
                # Parse content
                schema = parse_file_content(
                    raw_content,
                    self.logger,
                    file_extension=".yaml",
                    file_path=schema_file
                )
                
                if not schema or schema == "error":
                    self.logger.warning(f"[zServer] Failed to load schema: {filename}")
                    continue
                
                # Initialize database adapter
                self.zcli.data.load_schema(schema)
                
                # Get table names from schema (exclude Meta)
                table_names = [k for k in schema.keys() if k != "zMeta"]
                
                if not table_names:
                    self.logger.warning(f"[zServer] No tables found in schema: {filename}")
                    continue
                
                # Ensure each table exists
                for table_name in table_names:
                    try:
                        # Check if table exists (for SQL databases)
                        if hasattr(self.zcli.data.adapter, 'table_exists'):
                            if not self.zcli.data.adapter.table_exists(table_name):
                                self.zcli.data.create_table(table_name)
                                self.logger.info(f"[zServer] Created table: {table_name}")
                            else:
                                self.logger.debug(f"[zServer] Table exists: {table_name}")
                        else:
                            # For CSV and other backends, just create (idempotent)
                            self.zcli.data.create_table(table_name)
                            self.logger.info(f"[zServer] Initialized table: {table_name}")
                    
                    except Exception as table_error:
                        self.logger.warning(f"[zServer] Failed to create table {table_name}: {table_error}")
                
                self.logger.info(f"[zServer] Schema initialized: {filename} ({len(table_names)} table(s))")
                
            except Exception as e:
                self.logger.warning(f"[zServer] Failed to initialize schema {filename}: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
    
    def _get_deployment(self) -> str:
        """
        Get deployment mode from zCLI config.
        
        Returns:
            str: Deployment mode ("Development", "Testing", or "Production")
        """
        if not self.zcli or not hasattr(self.zcli, 'config'):
            return "Development"
        return self.zcli.config.get_environment("deployment", "Development")
    
    def _create_ssl_context(self):
        """
        Create SSL context from config if SSL is enabled (v1.5.10: HTTPS support).
        
        Delegates to zComm Layer 0 SSL primitive for consistent SSL handling
        across all zCLI servers (HTTP, WebSocket, etc.).
        
        Returns:
            ssl.SSLContext if SSL enabled and configured, None otherwise
        
        Architecture:
            - Uses zComm.comm_ssl.create_ssl_context() primitive
            - Maintains separation of concerns (SSL = Layer 0)
            - Consistent with WebSocket server SSL implementation
        
        Example:
            >>> ssl_context = self._create_ssl_context()
            >>> if ssl_context:
            >>>     self.server.socket = ssl_context.wrap_socket(...)
        """
        # Check if SSL is enabled in config
        if not hasattr(self, 'ssl_enabled') or not self.ssl_enabled:
            return None
        
        # Delegate to zComm Layer 0 SSL primitive
        return create_ssl_context(
            ssl_enabled=self.ssl_enabled,
            ssl_cert=self.ssl_cert,
            ssl_key=self.ssl_key,
            logger=self.logger,
            log_prefix="[zServer]"
        )
    
    def start(self):
        """
        Start HTTP server (deployment-aware).
        
        Behavior based on zSpark.deployment:
        - "Development"/"Testing" → http.server (background thread)
        - "Production" → Gunicorn (subprocess)
        
        Raises:
            RuntimeError: If server is already running
            OSError: If port is already in use or Gunicorn not installed
        
        Example:
            ```python
            # Development mode
            z = zCLI({"deployment": "Development", "http_server": {"port": 8000}})
            server = z.comm.create_http_server()
            server.start()  # Starts http.server
            
            # Production mode
            z = zCLI({"deployment": "Production", "http_server": {"port": 8000}})
            server = z.comm.create_http_server()
            server.start()  # Starts Gunicorn automatically
            ```
        """
        if self._running or (self.gunicorn_manager and self.gunicorn_manager.is_running()):
            self.logger.warning("[zServer] Server is already running")
            return
        
        # Check deployment mode and route to correct server type
        deployment = self._get_deployment().lower()
        
        if deployment == "production":
            self._start_production()
        else:
            self._start_development()
    
    def _start_production(self):
        """
        Start Gunicorn subprocess (Production mode).
        
        Creates a WSGI module and starts Gunicorn to serve it.
        """
        from .zServer_modules.gunicorn_manager import GunicornManager
        
        # Create temporary WSGI module for Gunicorn
        self._create_wsgi_module()
        
        # Start Gunicorn
        self.gunicorn_manager = GunicornManager(
            app_module="_zserver_wsgi_temp:app",
            host=self.host,
            port=self.port,
            workers=4,
            logger=self.logger
        )
        
        try:
            self.gunicorn_manager.start()
            self._running = True
        except Exception as e:
            self.logger.error(f"[zServer] Failed to start Gunicorn: {e}")
            self.gunicorn_manager = None
            raise
    
    def _start_development(self):
        """
        Start http.server thread (Development/Testing mode).
        
        This is the existing http.server logic.
        """
        
        # Save and change to serve directory
        try:
            original_dir = os.getcwd()
        except FileNotFoundError:
            original_dir = self.serve_path  # Fall back if getcwd fails
        
        os.chdir(self.serve_path)
        
        self.logger.info("[zServer] Starting in Development mode (http.server)...")
        
        try:
            # Create handler with logger, router, and folder conventions (v1.5.5)
            handler = partial(
                LoggingHTTPRequestHandler, 
                logger=self.logger, 
                router=self.router,
                static_folder=self.static_folder,
                template_folder=self.template_folder,
                ui_folder=self.ui_folder,
                serve_path=self.serve_path,
                static_mounts=self.static_mounts
            )
            
            # Create HTTP server
            self.server = HTTPServer((self.host, self.port), handler)
            
            # Wrap with SSL if enabled (v1.5.10: HTTPS support)
            ssl_context = self._create_ssl_context()
            if ssl_context:
                self.server.socket = ssl_context.wrap_socket(
                    self.server.socket,
                    server_side=True
                )
                protocol = "https"
                self.logger.info("[zServer] SSL/TLS encryption enabled (HTTPS)")
            else:
                protocol = "http"
            
            self._running = True
            
            # Start server in background thread
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()
            
            self.logger.info(f"[zServer] Server started at {protocol}://{self.host}:{self.port}")
            self.logger.info(f"[zServer] Serving files from: {self.serve_path}")
            
        except OSError as e:
            self._running = False
            os.chdir(original_dir)
            if e.errno == 48:  # Address already in use
                error_msg = f"[zServer] Port {self.port} already in use"
                self.logger.error(error_msg)
                raise OSError(error_msg) from e
            raise
        except Exception as e:
            self._running = False
            os.chdir(original_dir)
            self.logger.error(f"[zServer] Failed to start: {e}")
            raise
        finally:
            # Return to original directory if server failed to start
            if not self._running:
                os.chdir(original_dir)
    
    def _run_server(self):
        """Run server (called in background thread)"""
        try:
            self.server.serve_forever()
        except Exception as e:
            self.logger.error(f"[zServer] Server error: {e}")
        finally:
            self._running = False
    
    def _create_wsgi_module(self):
        """
        Create temporary WSGI module for Gunicorn to import.
        
        Generates a self-contained Python file that Gunicorn workers can import
        and use to create the WSGI app with proper routing and configuration.
        """
        import json
        
        # Serialize configuration for the WSGI module
        config = {
            'serve_path': self.serve_path,
            'static_folder': self.static_folder,
            'template_folder': self.template_folder,
            'routes_files': self.routes_files if hasattr(self, 'routes_files') else [],
            'routes_file': self.routes_file,  # Backward compatibility
        }
        
        wsgi_content = f'''# Auto-generated WSGI module for zServer Production mode
# DO NOT EDIT - Generated by zCLI

import sys
import os

# Configuration from zServer
CONFIG = {json.dumps(config, indent=4)}

# Set working directory to serve_path
serve_path = CONFIG['serve_path']
if os.path.exists(serve_path):
    os.chdir(serve_path)

# Create WSGI app using zServer's WSGI adapter
from zOS.L4_Orchestration.r_zServer.zServer_modules.wsgi_app import zServerWSGIApp

# Create a minimal zServer-like object with the configuration
class WSGIServerConfig:
    def __init__(self, config):
        self.serve_path = config['serve_path']
        self.static_folder = config['static_folder']
        self.template_folder = config['template_folder']
        self.routes_files = config.get('routes_files', [])
        self.routes_file = config.get('routes_file')  # Backward compatibility
        self.router = None
        self.logger = None
        
        # Backward compatibility: Convert single routes_file to list
        if self.routes_file and not self.routes_files:
            self.routes_files = [self.routes_file]
        
        # Load routes if any routes_files are provided
        if self.routes_files:
            self._load_routes()
    
    def _load_routes(self):
        """Load and merge routes from ALL YAML files (v1.5.9: Blueprint pattern)."""
        try:
            import yaml
            from zOS.L4_Orchestration.r_zServer.zServer_modules.router import HTTPRouter
            from zOS.utils.logger import ConsoleLogger
            
            # Create minimal logger for WSGI
            self.logger = ConsoleLogger()
            
            # Merged routes structure (blueprint pattern)
            merged_data = {{
                "type": "server",
                "meta": {{}},
                "routes": {{}}
            }}
            
            # Load and merge all route files
            for routes_file in self.routes_files:
                try:
                    # Build full path (routes_file is relative to serve_path)
                    full_path = os.path.join(self.serve_path, routes_file)
                    
                    # Parse YAML file directly
                    with open(full_path, 'r') as f:
                        routes_data = yaml.safe_load(f)
                    
                    if routes_data and routes_data.get("type") == "server":
                        # Merge meta (later files override earlier files)
                        if "meta" in routes_data:
                            merged_data["meta"].update(routes_data["meta"])
                        
                        # Merge routes (later files override earlier files)
                        if "routes" in routes_data:
                            merged_data["routes"].update(routes_data["routes"])
                            print(f"[WSGI] Loaded routes from: {{routes_file}}")
                except Exception as e:
                    print(f"[WSGI] Failed to load routes from {{routes_file}}: {{e}}")
            
            # Create router with merged routes (zcli=None since we don't need auth in this minimal setup)
            if merged_data["routes"]:
                self.router = HTTPRouter(merged_data, zcli=None, logger=self.logger)
                print(f"[WSGI] Router initialized with {{len(merged_data['routes'])}} total routes")
            
        except Exception as e:
            print(f"[WSGI] Failed to load routes: {{e}}")
            import traceback
            traceback.print_exc()

# Create server config and WSGI app
server_config = WSGIServerConfig(CONFIG)
app = zServerWSGIApp(server_config)
'''
        
        # Write WSGI module
        with open("_zserver_wsgi_temp.py", "w") as f:
            f.write(wsgi_content)
        
        self.logger.debug("[zServer] Created WSGI module: _zserver_wsgi_temp.py")
    
    def wait(self):
        """
        Block until server is interrupted (v1.5.8: Built-in lifecycle management).
        
        Keeps the process alive while the server runs. Signal handlers (SIGINT/SIGTERM)
        registered by zCLI will automatically call shutdown, which stops the server.
        
        This eliminates boilerplate try/except/KeyboardInterrupt blocks in applications.
        
        Example:
            ```python
            # OLD (manual lifecycle)
            z = zCLI(zSpark)
            server = z.comm.create_http_server()
            server.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                server.stop()
            
            # NEW (built-in lifecycle)
            z = zCLI({"zServer": {"enabled": True, "port": 8080}})
            z.server.wait()  # That's it! Signal handlers handle cleanup
            ```
        
        Note:
            - Signal handlers (Ctrl+C, SIGTERM) already registered by zCLI
            - zCLI.shutdown() automatically calls server.stop()
            - This method just keeps the process alive
        """
        import time
        
        if not self._running and not (self.gunicorn_manager and self.gunicorn_manager.is_running()):
            self.logger.debug("[zServer] Server is not running, nothing to wait for")
            return
        
        try:
            while self._running or (self.gunicorn_manager and self.gunicorn_manager.is_running()):
                time.sleep(1)
        except KeyboardInterrupt:
            # Signal handler will call shutdown, which calls stop()
            # Just exit gracefully
            pass
    
    def stop(self):
        """Stop HTTP server (works in all modes)."""
        deployment = self._get_deployment().lower()
        
        if deployment == "production":
            # Stop Gunicorn
            if self.gunicorn_manager:
                self.gunicorn_manager.stop()
                self.gunicorn_manager = None
            
            # Clean up WSGI module
            try:
                if os.path.exists("_zserver_wsgi_temp.py"):
                    os.remove("_zserver_wsgi_temp.py")
                if os.path.exists("_zserver_wsgi_temp.pyc"):
                    os.remove("_zserver_wsgi_temp.pyc")
            except Exception as e:
                self.logger.warning(f"[zServer] Could not remove WSGI temp file: {e}")
            
            self._running = False
            self.logger.info("[zServer] Production server stopped")
        
        else:
            # Stop http.server
            if not self._running:
                self.logger.warning("[zServer] Server is not running")
                return
            
            if self.server:
                self.logger.info("[zServer] Stopping HTTP server...")
                
                # Mark as not running first to prevent new requests
                self._running = False
                
                # Shutdown must be called from a different thread to avoid deadlock
                import threading
                shutdown_thread = threading.Thread(target=self.server.shutdown)
                shutdown_thread.daemon = True
                shutdown_thread.start()
                shutdown_thread.join(timeout=2)
                
                # Close the server socket
                self.server.server_close()
                
                # Wait for server thread to finish
                if self.thread:
                    self.thread.join(timeout=2)
                
                self.logger.info("[zServer] HTTP server stopped")
    
    def is_running(self):
        """Check if server is running (works in all modes)."""
        if self.gunicorn_manager:
            return self.gunicorn_manager.is_running()
        return self._running
    
    def get_url(self):
        """Get server URL"""
        return f"http://{self.host}:{self.port}"
    
    def health_check(self):
        """
        Get health status of HTTP server
        
        Returns:
            dict: Server health status with keys:
                - running (bool): Whether server is running
                - host (str): Server host address
                - port (int): Server port
                - url (str|None): Server URL (None if not running)
                - serve_path (str): Directory being served
        """
        return {
            "running": self._running,
            "host": self.host,
            "port": self.port,
            "url": self.get_url() if self._running else None,
            "serve_path": self.serve_path
        }

