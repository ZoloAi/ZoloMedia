# zCLI/subsystems/zLoader/zLoader.py

"""
zLoader facade for file loading, caching, and zParser delegation.

This module provides the main facade (Tier 5) for zLoader subsystem, handling
zVaFile (UI, Schema, Config) loading with intelligent caching and delegation to
zParser for path resolution and content parsing. It serves as the public interface
between zCLI and the internal zLoader 6-tier architecture.

Purpose
-------
The zLoader facade serves as Tier 5 (Facade) in the zLoader architecture, providing
a simple, unified interface for loading and parsing zVaFiles. It delegates to:
    - CacheOrchestrator (Tier 3) for intelligent caching
    - zParser subsystem for path resolution and file parsing
    - load_file_raw (Tier 1) for raw file I/O

Architecture
------------
**Tier 5 - Facade (Public Interface to zCLI)**
    - Position: Public interface between zCLI and internal zLoader components
    - Delegates To: CacheOrchestrator (Tier 3), zParser, load_file_raw (Tier 1)
    - Used By: zCLI.py, zDispatch, zNavigation (via walker)
    - Purpose: Unified file loading + intelligent caching + zParser delegation

**6-Tier Architecture**:
    - Tier 1: Foundation (loader_io.py - Raw file I/O)
    - Tier 2: Cache Implementations (SystemCache, PinnedCache, SchemaCache, PluginCache)
    - Tier 3: Cache Orchestrator (CacheOrchestrator - Unified cache router)
    - Tier 4: Package Aggregator (loader_modules/__init__.py - Public API exposure)
    - Tier 5: Facade ← THIS MODULE
    - Tier 6: Package Root (__init__.py - zLoader package entry point)

Key Responsibilities
--------------------
1. **File Loading**: Load zVaFiles (UI, Schema, Config) from disk or cache
2. **Intelligent Caching**: Cache UI/config files, skip schemas (loaded fresh)
3. **zParser Delegation**: Delegate path resolution and parsing to zParser subsystem
4. **Session Integration**: Support session-based file loading (zPath=None)

Caching Strategy
----------------
**Cached (System Cache)**:
    - UI files (zUI.*.yaml): User interface definitions
    - Config files (zConfig.*.yaml): Configuration files
    - Cache Key: f"parsed:{absolute_filepath}" (uses OS path for consistency)
    - Cache Type: "system" (LRU eviction, max_size=100)

**NOT Cached (Fresh Load)**:
    - Schema files (zSchema.*.yaml): Database schemas
    - Reason: Schemas should reflect latest DB structure
    - Detection: "zSchema" in filename or ".yaml|zSchema" extension

**Cache Key Construction**:
    - Format: "parsed:{absolute_filepath}"
    - Example: "parsed:/Users/name/workspace/zUI.users.yaml"
    - Uses absolute OS path for session-independent consistency
    - Ensures same file always uses same cache key (prevents duplicates)

Integration Points
------------------
**Week 6.6 (zDispatch)**:
    - dispatch_launcher.py (line 447): raw_zFile = self.zcli.loader.handle(zVaFile)
    - dispatch_modifiers.py (line 570): raw_zFile = self.zcli.loader.handle(zVaFile)
    - Purpose: Load UI files for command dispatch and modifier resolution

**Week 6.7 (zNavigation)**:
    - navigation_linking.py: walker.loader.handle() (via walker parameter)
    - Purpose: Load target UI files when processing zLink expressions

**Week 6.8 (zParser)**:
    - Uses zpath_decoder: Path resolution (zPath → full OS path)
    - Uses identify_zfile: File type identification and extension detection
    - Uses parse_file_content: Parse raw YAML/JSON content into Python objects

External Usage
--------------
**Used By**:
    - zCLI.py: zcli.loader.handle(zPath)
    - zDispatch (via zcli.loader): self.zcli.loader.handle(zVaFile)
    - zNavigation (via walker.loader): walker.loader.handle()

Usage Examples
--------------
**UI File Loading (with zPath)**:
    >>> loader = zLoader(zcli)
    >>> ui_data = loader.handle("@.zUI.users.yaml")
    >>> # Returns: Parsed UI dictionary (cached for subsequent loads)

**UI File Loading (session fallback)**:
    >>> loader = zLoader(zcli)
    >>> ui_data = loader.handle()  # zPath=None, uses session values
    >>> # Returns: Parsed UI dictionary from session context

**Config File Loading**:
    >>> loader = zLoader(zcli)
    >>> config_data = loader.handle("~.zMachine.zConfig.app.yaml")
    >>> # Returns: Parsed config dictionary (cached)

**Schema File Loading (fresh load)**:
    >>> loader = zLoader(zcli)
    >>> schema_data = loader.handle("@.zSchema.users.yaml")
    >>> # Returns: Parsed schema dictionary (NOT cached, always fresh)

Layer Position
--------------
Layer 1, Position 6 (zLoader - Tier 5 Facade)
    - Tier 1: Foundation (loader_io.py)
    - Tier 2: Cache Implementations (4 caches)
    - Tier 3: Cache Orchestrator (cache_orchestrator.py)
    - Tier 4: Package Aggregator (loader_modules/__init__.py)
    - Tier 5: Facade ← THIS MODULE
    - Tier 6: Package Root (__init__.py)

Dependencies
------------
Internal:
    - loader_modules.CacheOrchestrator (Tier 3)
    - loader_modules.load_file_raw (Tier 1)
    - zParser.zpath_decoder, identify_zfile, parse_file_content

External:
    - zCLI imports: Any, Dict, Optional (for type hints)

See Also
--------
- cache_orchestrator.py: Unified cache router (Tier 3)
- loader_io.py: Raw file I/O (Tier 1)
- zParser: Path resolution and content parsing

Version History
---------------
- v1.5.4: Industry-grade upgrade (type hints, constants, comprehensive docs,
          integration points documentation, caching strategy documentation)
- v1.5.3: Original implementation (file loading, caching, zParser delegation)
"""

from zOS import Any, Dict, Optional
from .loader_modules import CacheOrchestrator, load_file_raw

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Color Constants
COLOR_KEY: str = "LOADER"

# File Type Constants
FILE_TYPE_UI: str = "zUI"
FILE_TYPE_SCHEMA: str = "zSchema"

# Session Keys (TODO: Import from zConfig when available)
SESSION_KEY_VAFILE: str = "zVaFile"
SESSION_KEY_VAFOLDER: str = "zVaFolder"

# Cache Constants
CACHE_KEY_PREFIX: str = "parsed:"
CACHE_TYPE_SYSTEM: str = "system"
CACHE_TYPE_PLUGIN: str = "plugin"

# Default Values
DEFAULT_PATH_SYMBOL: str = "@"
SCHEMA_EXTENSION: str = ".yaml|zSchema"

# Plugin Constants
PLUGIN_EXTENSION: str = ".py"
ZMACHINE_PREFIX: str = "zMachine."

# Display Messages
MSG_READY: str = "zLoader Ready"
MSG_START: str = "zLoader"
MSG_CACHED: str = "zLoader return (cached)"
MSG_RETURN: str = "zLoader return"

# Error Messages
ERROR_PLUGIN_NOT_FOUND: str = "Plugin file not found: {filepath}"
ERROR_PLUGIN_LOAD_FAILED: str = "Failed to load plugin: {error}"
ERROR_NO_PARSER: str = "zParser subsystem not available"

# ============================================================================
# ZLOADER CLASS
# ============================================================================


class zLoader:
    """
    Middleware layer for loading and caching zVaFiles (UI, Schema, Config).

    The zLoader class serves as the main facade for the zLoader subsystem, providing
    intelligent file loading with caching and delegation to zParser for path resolution
    and content parsing. It implements a smart caching strategy that caches UI/config
    files but loads schemas fresh each time.

    Attributes
    ----------
    zcli : Any
        Reference to main zCLI instance (provides access to all subsystems)
    logger : Any
        Reference to zCLI logger for debug/info logging
    zSession : Dict[str, Any]
        Reference to zCLI session dictionary for state management
    display : Any
        Reference to zDisplay for visual feedback (zDeclare calls)
    mycolor : str
        Color key for display messages (COLOR_KEY constant)
    cache : CacheOrchestrator
        Tier 3 cache orchestrator for managing all cache tiers
    zpath_decoder : Callable
        zParser method for path resolution (zPath → full OS path)
    identify_zfile : Callable
        zParser method for file type identification
    parse_file_content : Callable
        zParser method for parsing raw YAML/JSON content

    Caching Strategy
    ----------------
    **Cached (System Cache)**:
        - UI files (zUI.*.yaml): User interface definitions
        - Config files (zConfig.*.yaml): Configuration files
        - Cache Key: "parsed:{absolute_filepath}" (uses OS path for consistency)
        - Cache Type: "system" (LRU eviction, max_size=100)

    **NOT Cached (Fresh Load)**:
        - Schema files (zSchema.*.yaml): Database schemas
        - Reason: Schemas should reflect latest DB structure
        - Detection: "zSchema" in filename or ".yaml|zSchema" extension
    """

    def __init__(self, zcli: Any) -> None:
        """
        Initialize zLoader with zCLI instance.

        Parameters
        ----------
        zcli : Any
            Main zCLI instance providing access to:
                - session: Session dictionary for state management
                - logger: Logger for debug/info logging
                - display: zDisplay for visual feedback
                - zparser: zParser for path resolution and parsing

        Notes
        -----
        - Initializes cache orchestrator (manages all 4 cache tiers)
        - Stores parser method references for cleaner code
        - Displays "zLoader Ready" message via zDisplay
        """
        self.zcli = zcli
        self.logger = zcli.logger
        self.zSession = zcli.session
        self.display = zcli.display
        self.mycolor = COLOR_KEY

        # Initialize cache orchestrator (manages all cache tiers including plugins)
        self.cache = CacheOrchestrator(self.zSession, self.logger, zcli)

        # Store parser method references for cleaner code
        self.zpath_decoder = zcli.zparser.zPath_decoder
        self.identify_zfile = zcli.zparser.identify_zFile
        self.parse_file_content = zcli.zparser.parse_file_content
        self.display.zDeclare(MSG_READY, color=self.mycolor, indent=0, style="full")

    def handle(self, zPath: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point for zVaFile loading and parsing.

        Loads and parses a zVaFile (UI, Schema, Config) with intelligent caching.
        Delegates to zParser for path resolution and content parsing. Supports
        both explicit zPath specification and session-based fallback (zPath=None).

        Parameters
        ----------
        zPath : Optional[str], default=None
            Declarative path to zVaFile (e.g., "@.zUI.users.yaml")
            - If None: Uses session values (SESSION_KEY_VAFILE, SESSION_KEY_VAFOLDER)
            - If provided: Explicit path to load
            - Symbols: "@" (workspace-relative), "~" (absolute), none (relative to cwd)

        Returns
        -------
        Dict[str, Any]
            Parsed zVaFile content as Python dictionary. Structure depends on file type:
                - UI files: {zName, zLoad, zBlock, zOptions, etc.}
                - Schema files: {tables, fields, constraints, etc.}
                - Config files: {settings, values, etc.}

        Raises
        ------
        FileNotFoundError
            If zVaFile cannot be found (via zParser)
        ParseError
            If zVaFile content is invalid YAML/JSON (via zParser)

        Examples
        --------
        **UI File Loading (with zPath)**:
            >>> loader = zLoader(zcli)
            >>> ui_data = loader.handle("@.zUI.users.yaml")
            >>> # Returns: {'zName': 'users', 'zBlock': [...], ...}

        **UI File Loading (session fallback)**:
            >>> # Session has: {'zVaFile': 'users.yaml', 'zVaFolder': '@'}
            >>> loader = zLoader(zcli)
            >>> ui_data = loader.handle()  # zPath=None
            >>> # Returns: {'zName': 'users', 'zBlock': [...], ...}

        **Config File Loading**:
            >>> loader = zLoader(zcli)
            >>> config_data = loader.handle("~.zMachine.zConfig.app.yaml")
            >>> # Returns: {'setting1': 'value1', 'setting2': 'value2', ...}

        **Schema File Loading (fresh load)**:
            >>> loader = zLoader(zcli)
            >>> schema_data = loader.handle("@.zSchema.users.yaml")
            >>> # Returns: {'tables': [...], 'fields': [...], ...} (NOT cached)

        **Navigation Linking (via walker.loader)**:
            >>> # In navigation_linking.py:
            >>> target_ui = walker.loader.handle(target_file)
            >>> # Returns: Parsed target UI dictionary

        **Command Dispatch (via zcli.loader)**:
            >>> # In dispatch_launcher.py or dispatch_modifiers.py:
            >>> raw_zFile = self.zcli.loader.handle(zVaFile)
            >>> # Returns: Parsed UI dictionary for command dispatch

        Notes
        -----
        **Caching Strategy**:
            - Cached: UI files (zUI.*), Config files (zConfig.*)
            - NOT Cached: Schema files (zSchema.*) - always loaded fresh
            - Cache Key: "parsed:{absolute_filepath}" (uses OS path for consistency)
            - Cache Type: "system" (LRU eviction, max_size=100)
            - Mtime Invalidation: Automatically detects file changes and reloads

        **zParser Delegation**:
            - Path Resolution: self.zpath_decoder(zPath, zType)
            - File Identification: self.identify_zfile(zVaFile, zVaFile_fullpath)
            - Content Parsing: self.parse_file_content(zFile_raw, zFile_extension, ...)

        **Integration Points**:
            - zDispatch: dispatch_launcher.py, dispatch_modifiers.py
            - zNavigation: navigation_linking.py (via walker.loader)
            - zCLI: Direct access via zcli.loader
        """
        self.display.zDeclare(MSG_START, color=self.mycolor, indent=1, style="single")
        self.logger.debug("zFile_zObj: %s", zPath)

        # Determine if we should use session values (UI file loading)
        # When zPath is None and session has zVaFile, use session values
        zType = FILE_TYPE_UI if not zPath and self.zSession.get(SESSION_KEY_VAFILE) else None

        # Step 1: Use zParser for path resolution and file discovery
        zVaFile_fullpath, zVaFile = self.zpath_decoder(zPath, zType)
        zFilePath_identified, zFile_extension = self.identify_zfile(zVaFile, zVaFile_fullpath)
        self.logger.debug("zFilePath_identified!\n%s", zFilePath_identified)

        # Detect if this is a zSchema file (should not be cached)
        is_schema = FILE_TYPE_SCHEMA in zVaFile or zFile_extension == SCHEMA_EXTENSION

        if not is_schema:
            # Step 2: Check system cache (UI and config files)
            # Use absolute filepath for cache key (session-independent)
            # This ensures same file always uses same cache key, preventing duplicates
            cache_key = f"{CACHE_KEY_PREFIX}{zFilePath_identified}"
            cached = self.cache.get(cache_key, cache_type=CACHE_TYPE_SYSTEM, filepath=zFilePath_identified)
            if cached is not None:
                self.display.zDeclare(MSG_CACHED, color=self.mycolor, indent=1, style="~")
                self.logger.debug("[SystemCache] Cache hit: %s", cache_key)
                return cached
        else:
            self.logger.debug("[zSchema] Skipping cache - schemas are loaded fresh each time")

        # Step 4: Load raw file content (PRIORITY 3 - Disk I/O)
        self.logger.debug("[Priority 3] Cache miss - loading from disk")
        zFile_raw = load_file_raw(zFilePath_identified, self.logger, self.display)
        # Only log raw content if file is very small (< 200 chars) for debugging
        # Removed: Too noisy for standard DEBUG mode

        # Step 5: Parse using zParser (delegates to zParser)
        result = self.parse_file_content(zFile_raw, zFile_extension, session=self.zSession, file_path=zFilePath_identified)
        self.logger.debug("zLoader parse result:\n%s", result)

        # Step 5.5: Inject meta.zNavBar as synthetic keys (if present)
        # This transforms the zVaFile structure BEFORE caching
        result = self._inject_navbar_if_present(result)

        # Step 6: Return result (cache only if not a schema)
        self.display.zDeclare(MSG_RETURN, color=self.mycolor, indent=1, style="~")

        # Don't cache schemas - they should be loaded fresh each time
        if is_schema:
            self.logger.debug("[zSchema] Not caching - returning fresh data")
            return result

        # Cache other resources (UI, configs, etc.) in system cache
        # Use absolute filepath for cache key (same as get() for consistency)
        cache_key = f"{CACHE_KEY_PREFIX}{zFilePath_identified}"
        return self.cache.set(cache_key, result, cache_type=CACHE_TYPE_SYSTEM, filepath=zFilePath_identified)

    def _inject_navbar_if_present(self, raw_zFile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject meta.zNavBar as synthetic menu keys into all blocks (if present).
        
        This transformation happens AFTER parsing and BEFORE caching, ensuring that
        navbar items appear as natural menu options to downstream subsystems (zWalker,
        zWizard, zDispatch, zDisplay). The navbar logic is centralized in zNavigation.
        
        Parameters
        ----------
        raw_zFile : Dict[str, Any]
            Parsed zVaFile structure (may contain meta.zNavBar)
        
        Returns
        -------
        Dict[str, Any]
            Transformed zVaFile with navbar items injected into all blocks
        
        Notes
        -----
        **Architecture**:
            - zLoader: Transformation layer (this method)
            - zNavigation: Resolves navbar items (global, local, route fallback)
            - zWalker/zWizard: Process navbar items like any other keys
            - zDispatch: Handles navbar selections
            - zDisplay: Renders navbar items
        
        **Synthetic Key Format**:
            - Key: _zNavBar_{blockName} (e.g., "_zNavBar_zVaF")
            - Value: ${blockName} (e.g., "$zVaF" - delta link)
        """
        # Safety check
        if not isinstance(raw_zFile, dict):
            return raw_zFile
        
        # Get route metadata from session (for server-side routes)
        route_meta = self.zSession.get('_router_meta', {})
        
        # Resolve navbar items via zNavigation (handles global, local, route fallback)
        navbar_items = self.zcli.navigation.resolve_navbar(raw_zFile, route_meta=route_meta)
        
        # No navbar to inject
        if not navbar_items or len(navbar_items) == 0:
            return raw_zFile
        
        self.logger.debug(f"[zLoader] Injecting navbar items into all blocks: {navbar_items}")
        
        # Create navbar menu with modifiers
        # Format: ~zNavBar*: [$zVaF, $zAbout, {zAccount: {zRBAC: ...}}, ...]
        # ~ = no back modifier (anchor menu)
        # * = explicit menu marker
        # Items display cleanly (zDisplay strips $), backend handles delta/zLink
        # Dict items (with RBAC) are kept as-is for dynamic filtering in zDispatch
        navbar_menu_items = []
        for item in navbar_items:
            if isinstance(item, str):
                # Simple string item - add delta prefix
                navbar_menu_items.append(f"${item}")
            elif isinstance(item, dict):
                # Dict item with RBAC metadata - keep as-is (no prefix)
                # Dispatch will filter and extract the key, then add prefix
                navbar_menu_items.append(item)
            else:
                # Unknown type - skip
                self.logger.warning(f"[zLoader] Unknown navbar item type: {type(item)} ({item})")
        
        navbar_key = {"~zNavBar*": navbar_menu_items}
        
        # Inject into all top-level blocks (skip "meta" and blocks with modifiers like ^)
        for block_name, block_content in raw_zFile.items():
            # Skip metadata block
            if block_name == "meta" or block_name.startswith("_"):
                continue
            
            # Skip blocks with ^ prefix (bounce-back blocks) - they should bounce immediately after content
            if block_name.startswith("^"):
                self.logger.debug(f"[zLoader] Skipping navbar injection for bounce-back block: {block_name}")
                continue
            
            # Only inject into dict blocks (not lists or primitives)
            if isinstance(block_content, dict):
                # Inject at the end of the block
                raw_zFile[block_name] = {**block_content, **navbar_key}
                self.logger.debug(f"[zLoader] Injected navbar menu into block: {block_name}")
        
        return raw_zFile

    def load_plugin_from_zpath(self, zpath: str) -> Any:
        """
        Load a plugin module from a zPath (facade method for shell commands).

        This method provides a unified interface for loading plugins from zPath notation,
        handling path resolution, file validation, and plugin loading via the plugin cache.
        It's designed as a backend facade to keep shell commands thin and testable.

        Parameters
        ----------
        zpath : str
            Declarative path to plugin file using zPath notation:
                - "@.plugins.my_plugin" - Workspace-relative path
                - "~.plugins.custom" - Absolute path
                - "zMachine.plugins.helper" - zMachine path
                - Automatically adds .py extension if not present

        Returns
        -------
        Any
            Loaded plugin module object with zcli instance injected.
            Module can be accessed via: module.function_name()

        Raises
        ------
        FileNotFoundError
            If plugin file cannot be found at resolved path
        ValueError
            If plugin loading fails (e.g., syntax error, collision)
        RuntimeError
            If zParser subsystem is not available

        Examples
        --------
        **Load Plugin from Workspace**:
            >>> loader = zLoader(zcli)
            >>> module = loader.load_plugin_from_zpath("@.plugins.auth")
            >>> result = module.hash_password("mypassword")

        **Load Plugin from Absolute Path**:
            >>> loader = zLoader(zcli)
            >>> module = loader.load_plugin_from_zpath("~/custom/plugins/generator")
            >>> id = module.generate_id()

        **Load Plugin from zMachine**:
            >>> loader = zLoader(zcli)
            >>> module = loader.load_plugin_from_zpath("zMachine.plugins.helper")
            >>> result = module.helper_function()

        Notes
        -----
        **Backend Facade Pattern**:
            This method serves as a facade to:
            1. zParser: Path resolution (zPath → absolute file path)
            2. Plugin Cache: Module loading + session injection + caching

        **Why This Method Exists**:
            Prevents shell commands from doing backend logic:
            - Manual zPath parsing (lines 56-70 in old plugin.py) → Backend
            - File existence checks (lines 73-75) → Backend
            - Direct plugin_cache access → Backend facade

        **Integration Points**:
            - shell_cmd_plugin_mgmt.py: load_plugin(), reload_plugin()
            - Future: Plugin installation, dependency resolution

        **Error Handling**:
            Raises proper exceptions that shell commands can catch and display:
            - FileNotFoundError: Plugin file not found
            - ValueError: Plugin collision or load error
            - RuntimeError: zParser unavailable

        **Session Injection**:
            Plugin cache automatically injects zcli instance into loaded modules.
            Plugins can access: zcli.logger, zcli.session, zcli.data, zcli.auth, etc.
        """
        import os
        from pathlib import Path

        # Validate zParser availability
        if not hasattr(self.zcli, "zparser") or self.zcli.zparser is None:
            raise RuntimeError(ERROR_NO_PARSER)

        # Step 1: Resolve zPath to absolute file path
        if zpath.startswith(ZMACHINE_PREFIX):
            # zMachine paths (e.g., "zMachine.plugins.helper")
            file_path = self.zcli.zparser.resolve_zmachine_path(zpath)
        else:
            # @ or ~ paths (e.g., "@.plugins.auth", "~/plugins/custom")
            symbol = DEFAULT_PATH_SYMBOL if zpath.startswith(DEFAULT_PATH_SYMBOL) else (
                "~" if zpath.startswith("~") else DEFAULT_PATH_SYMBOL
            )
            path_str = zpath[1:] if zpath.startswith((DEFAULT_PATH_SYMBOL, "~")) else zpath
            path_parts = path_str.split(".")

            # Prepend symbol for resolve_symbol_path
            zRelPath_parts = [symbol] + path_parts
            file_path = self.zcli.zparser.resolve_symbol_path(symbol, zRelPath_parts)

        # Step 2: Add .py extension if not present
        if not file_path.endswith(PLUGIN_EXTENSION):
            file_path = f"{file_path}{PLUGIN_EXTENSION}"

        # Step 3: Validate file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(ERROR_PLUGIN_NOT_FOUND.format(filepath=file_path))

        # Step 4: Extract module name (filename without extension)
        module_name = Path(file_path).stem

        # Step 5: Load via plugin cache (handles caching + session injection)
        try:
            module = self.cache.plugin_cache.load_and_cache(file_path, module_name)
            self.logger.framework.debug("Loaded plugin: %s from %s", module_name, file_path)
            return module
        except Exception as e:
            self.logger.error("Failed to load plugin %s: %s", module_name, str(e))
            raise ValueError(ERROR_PLUGIN_LOAD_FAILED.format(error=str(e))) from e


# ============================================================================
# MODULE METADATA
# ============================================================================

__all__ = ["zLoader"]
