# zCLI/subsystems/zUtils/zUtils.py

"""
Plugin management facade for zCLI with unified cache architecture.

This module provides the zUtils subsystem, which manages plugin loading and exposure
for the zCLI framework. It serves as the primary interface for loading plugins from
zSpark configuration during boot time, with session injection and method exposure.

**Phase 2 Architecture**: zUtils now delegates to zLoader.plugin_cache for storage,
eliminating redundancy and enabling unified plugin access across all subsystems.

Purpose
-------
The zUtils subsystem serves as Layer 2, Position 1 in the zCLI architecture, providing
plugin management capabilities that are available to all higher-layer subsystems. It
handles boot-time plugin loading from zSpark configuration and delegates storage to
zLoader.plugin_cache for a unified, framework-wide plugin system.

Architecture
------------
**Layer 2, Position 1 - Core Abstraction (Plugin Management)**
    - Position: First subsystem in Layer 2, before zShell, zWizard, zData
    - Dependencies: zConfig (logger, display), zLoader (plugin_cache)
    - Used By: zCLI.py (boot-time plugin loading), zShell (utils command)
    - Purpose: Plugin loading facade + delegation to zLoader.plugin_cache

**Unified Plugin Architecture (Phase 2)**:
    ```
    zSpark plugins           Runtime plugins (&PluginName)
         ↓                            ↓
    zUtils.load_plugins()    zParser.resolve_plugin_invocation()
         ↓                            ↓
         └────────────┬───────────────┘
                      ↓
            zLoader.plugin_cache (UNIFIED STORAGE)
                      ↓
            Single source of truth for all plugins
    ```

**Benefits of Unification**:
    - Single source of truth: No redundant storage
    - Cross-access: &PluginName can access zSpark plugins
    - Unified metrics: Single cache stats for all plugins
    - No duplication: Same plugin never loaded twice

Key Features
------------
1. **Boot-Time Loading**: Loads plugins from zSpark["plugins"] during initialization
2. **Unified Storage**: Delegates to zLoader.plugin_cache (no separate storage)
3. **Session Injection**: Injects zcli instance into plugins before execution
4. **Secure Exposure**: Respects __all__ whitelist for method exposure
5. **Method Exposure**: Exposes plugin functions as methods on zUtils instance
6. **Best-Effort Loading**: Doesn't fail boot on plugin errors (graceful degradation)
7. **Progress Display**: Uses display.progress_iterator() for user feedback

Design Decisions
----------------
1. **Delegation to zLoader**: Phase 2 eliminates separate self.plugins dict. All
   plugin storage now goes through zLoader.plugin_cache, providing unified access
   for both zSpark plugins and runtime (&PluginName) plugins.

2. **Session Injection Timing**: Injecting zcli instance BEFORE exec_module() is
   critical. Allows plugins to use zcli in top-level code (imports, constants, etc.).
   This injection is now handled by zLoader.plugin_cache.load_and_cache().

3. **Secure Method Exposure**: Phase 2 adds __all__ checking. Plugins must explicitly
   declare exported functions via __all__ = ['func1', 'func2']. This prevents
   accidental exposure of imported functions (security vulnerability fix).

4. **Best-Effort Loading**: Silent failures on plugin load errors prevent boot crashes.
   Callers can inspect zLoader.plugin_cache to verify loaded plugins.

5. **Collision Avoidance**: Only exposes methods that don't collide with existing
   attributes (hasattr check). Protects zUtils instance methods from being overwritten.

Plugin Loading Strategy
-----------------------
**When to Load**:
    - During zCLI.__init__() via _load_plugins() call
    - Plugins specified in zSpark["plugins"] configuration
    - Supports both file paths and module import paths

**Load Sources**:
    - Absolute .py file paths: /path/to/plugin.py
    - Module import paths: package.module.plugin

**Storage (Phase 2)**:
    - Delegated to zLoader.plugin_cache
    - Uses filename as key (e.g., "test_plugin")
    - Enables access via both zcli.utils.function() and &PluginName.function()

**Session Injection**:
    - module.zcli = self.zcli (injected by zLoader.plugin_cache)
    - Enables plugins to access all zCLI subsystems

**Method Exposure (Phase 2 - Secure)**:
    - Checks for __all__ attribute in plugin module
    - If present: Only exposes functions listed in __all__
    - If absent: Logs warning, exposes all public callables (backward compat)
    - Skips private attributes (names starting with _)
    - Skips if name collision with existing zUtils methods
    - Tracks exposure count for logging

External Usage
--------------
**Used By**:
    - zCLI/zCLI.py (Line 119-120)
      Usage: self.utils = zUtils(self); self._load_plugins()
      Purpose: Boot-time plugin loading

    - zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_utils.py
      Usage: zcli.utils.function_name(*args)
      Purpose: Shell command access to plugin functions

**Integration with zLoader** (Phase 2):
    - zUtils delegates to zLoader.plugin_cache for all storage
    - zParser can access zSpark plugins via plugin_cache
    - Unified cache stats include both zSpark and runtime plugins

Usage Examples
--------------
**Boot-Time Loading**:
    >>> zSpark = {"plugins": ["/path/to/my_plugin.py"]}
    >>> zcli = zCLI(zSpark)
    >>> # Plugins now in zLoader.plugin_cache
    >>> zcli.utils.my_plugin_function()

**Direct Loading**:
    >>> zcli = zCLI()
    >>> zcli.utils.load_plugins(["/path/to/helper.py"])
    >>> zcli.utils.helper_function()

**Cross-Access (Phase 2)**:
    >>> # Load via zSpark
    >>> zcli = zCLI({"plugins": ["my_plugin.py"]})
    >>> # Access via &PluginName syntax
    >>> result = zcli.zparser.resolve_plugin_invocation("&my_plugin.function()")
    >>> # Works! Both use same cache

**Secure Plugin with __all__**:
    >>> # In plugin file:
    >>> from os import system  # Dangerous import
    >>> 
    >>> def safe_function():
    ...     return "Safe!"
    >>> 
    >>> __all__ = ['safe_function']  # Only this exposed
    >>> 
    >>> # Usage:
    >>> zcli.utils.safe_function()  # ✅ Works
    >>> zcli.utils.system("cmd")     # ❌ Not exposed (secure!)

**Shell Command Access**:
    >>> # From zShell:
    >>> utils my_function arg1 arg2
    >>> # Executes: zcli.utils.my_function(arg1, arg2)

Layer Position
--------------
Layer 2, Position 1 (Core Abstraction - Plugin Management)
    - Layer 0: Foundation (zConfig, zComm)
    - Layer 1: Core Subsystems (zDisplay, zAuth, zDispatch, zNavigation, zParser,
               zLoader, zFunc, zDialog, zOpen)
    - Layer 2: Core Abstraction ← THIS MODULE (Position 1)
        - zUtils (Plugin Management) ← THIS
        - zShell (Shell Interface)
        - zWizard (Loop Engine)
        - zData (Data Management)
    - Layer 3: Orchestration (zWalker)

Dependencies
------------
Internal:
    - zLoader.plugin_cache (for unified plugin storage)

External:
    - zCLI imports: importlib, importlib.util, os
    - zConfig: logger, display (via zcli instance)

Integration Notes
-----------------
**With zShell**:
    - zShell's utils command delegates to zcli.utils methods
    - Requires zUtils to be initialized before zShell (now enforced)

**With zLoader** (Phase 2 - UNIFIED):
    - zUtils delegates all storage to zLoader.plugin_cache
    - Eliminates redundancy, enables unified access
    - zSpark plugins accessible via &PluginName syntax

**With zParser** (Phase 2 - UNIFIED):
    - zParser uses zLoader.plugin_cache for &PluginName invocations
    - After Phase 2, both zUtils and zParser use same storage
    - Cross-access enabled: zSpark plugins available to &PluginName

Performance Considerations
--------------------------
- **Boot Time**: Plugin loading adds 10-50ms per plugin to boot time
- **Memory**: Delegates to zLoader.plugin_cache (typical: 5-20 plugins, 10-100KB each)
- **Method Exposure**: O(n) where n = number of __all__ items or module attributes
- **Best Practice**: Keep plugins small and focused to minimize boot impact

Thread Safety
-------------
This class is NOT thread-safe. Plugin loading delegates to zLoader.plugin_cache,
which is also not thread-safe. If using zCLI in a multi-threaded environment,
ensure plugins are loaded during initialization (single-threaded) or add proper locking.

Security Notes (Phase 2)
-------------------------
**__all__ Whitelist**:
    Plugins should define __all__ to explicitly declare exported functions.
    This prevents accidental exposure of imported functions:
    
    ```python
    # Good (secure):
    from os import system
    def my_function(): pass
    __all__ = ['my_function']  # Only my_function exposed
    
    # Bad (insecure):
    from os import system
    def my_function(): pass
    # No __all__ → both my_function AND system exposed!
    ```

**Backward Compatibility**:
    Plugins without __all__ will still work (all public callables exposed),
    but a warning is logged. This is for backward compatibility only and
    should be considered deprecated.

Phase 3 Enhancements (COMPLETE)
--------------------------------
**Collision Detection**:
    Prevents loading two plugins with the same name from different paths.
    Raises ValueError with clear error message showing existing path.

**Stats/Metrics**:
    Tracks plugin loading statistics via get_stats() method:
        - plugins_loaded: Current plugin count
        - total_loads: Total load operations
        - collisions: Collision errors
        - reloads: Auto-reloads from file changes
        - hit_rate: Cache efficiency

**Mtime Tracking & Auto-Reload**:
    Monitors plugin file modification times and auto-reloads on change.
    Throttled checks (1s interval) prevent excessive filesystem access.
    Seamless developer experience - edit plugin, auto-reload on next access.

See Also
--------
- zLoader.loader_modules.loader_cache_plugin: Unified plugin storage
- zParser.parser_modules.parser_plugin: Runtime plugin invocation via &PluginName
- zShell.shell_modules.commands.shell_cmd_utils: Shell command integration

Version History
---------------
- v1.5.4: Phase 3 modernization (collision detection, stats/metrics, mtime auto-reload)
- v1.5.4: Phase 2 modernization (unified storage, security fix, delegation to zLoader)
- v1.5.4: Phase 1 modernization (type hints, constants, docstrings, helpers, error handling)
- v1.5.3: Original implementation (89 lines, basic plugin loading)
"""

from zOS import importlib, os, time, Any, Dict, List, Optional, Union, Path

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# ============================================================================
# IMPORTS - CONSTANTS
# ============================================================================

# Public Constants (exported from utils_modules)
from .utils_modules import (
    SUBSYSTEM_NAME,
    SUBSYSTEM_COLOR,
    DEFAULT_PLUGINS_DICT,
)

# Internal Constants (direct import for internal use)
from .utils_modules.utils_constants import (
    _MSG_READY,
    _LOG_MSG_LOADING,
    _LOG_MSG_LOADED_FILE,
    _LOG_MSG_LOADED_MODULE,
    _LOG_MSG_EXPOSED_COUNT,
    _LOG_MSG_LOAD_START,
    _LOG_MSG_LOAD_SUCCESS,
    _LOG_MSG_CACHED_TO_LOADER,
    _LOG_MSG_USING_ALL,
    _WARN_MSG_LOAD_FAILED,
    _WARN_MSG_NO_MODULE,
    _WARN_MSG_COLLISION,
    _WARN_MSG_NO_ALL,
    _WARN_MSG_NOT_IN_ALL,
    _ERROR_MSG_IMPORT_FAILED,
    _ERROR_MSG_SPEC_FAILED,
    _ERROR_MSG_EXEC_FAILED,
    _ERROR_MSG_INVALID_PATH,
    _ERROR_MSG_LOADER_UNAVAILABLE,
    _ERROR_MSG_COLLISION,
    _ATTR_PREFIX_PRIVATE,
    _ATTR_NAME_ZCLI,
    _ATTR_NAME_ALL,
    _CACHE_TYPE_PLUGIN,
    _STATS_KEY_TOTAL_LOADS,
    _STATS_KEY_COLLISIONS,
    _STATS_KEY_RELOADS,
    _STATS_KEY_PLUGINS_LOADED,
    _MTIME_CHECK_INTERVAL,
    _MTIME_CACHE_KEY,
    _PATH_CACHE_KEY,
)


# ============================================================================
# ZUTILS CLASS
# ============================================================================


class zUtils:
    """
    Plugin management facade with unified cache architecture.

    This class provides the zUtils subsystem, which loads plugins from zSpark
    configuration during zCLI initialization. Phase 2: It delegates all storage
    to zLoader.plugin_cache, eliminating redundancy and enabling unified plugin
    access across zUtils (boot-time) and zParser (runtime &PluginName).

    Attributes
    ----------
    zcli : Any
        Reference to main zCLI instance (provides access to all subsystems)
    logger : Any
        Reference to zCLI logger for debug/info logging
    display : Any
        Reference to zDisplay for visual feedback and progress display
    mycolor : str
        Color key for display messages (SUBSYSTEM_COLOR constant)

    Notes
    -----
    **Phase 2 Architecture Change**:
        No longer stores plugins in self.plugins dict. All storage is delegated
        to zLoader.plugin_cache for unified access.

    **Initialization Order**:
        zUtils is the first subsystem in Layer 2, initialized before zShell, zWizard,
        and zData. This ensures plugins are available to all higher-layer subsystems.

    **Plugin Loading**:
        Plugins are loaded via load_plugins() method, typically called from zOS._load_plugins()
        immediately after zUtils initialization. Storage is delegated to zLoader.plugin_cache.
    """

    def __init__(self, zcli: Any) -> None:
        """
        Initialize zUtils subsystem with zCLI instance.

        Parameters
        ----------
        zcli : Any
            zCLI instance providing access to logger, display, and all subsystems

        Notes
        -----
        **Phase 2 Changes**:
            No longer initializes self.plugins dict. Storage is handled by zLoader.plugin_cache.

        **Phase 3 Changes**:
            Initializes stats tracking and mtime cache for observability and auto-reload.

        **Initialization Steps**:
            1. Store zcli instance reference
            2. Extract logger and display references
            3. Set color for display messages
            4. Initialize stats tracking (Phase 3)
            5. Initialize mtime cache (Phase 3)
            6. Display ready message

        **Display Message**:
            Uses zDisplay.zDeclare() to show "zUtils Ready" message during boot.
        """
        self.zcli: Any = zcli
        self.logger: Any = zcli.logger
        self.display: Any = zcli.display
        self.mycolor: str = SUBSYSTEM_COLOR

        # Phase 3: Initialize stats tracking
        self._stats: Dict[str, int] = {
            _STATS_KEY_TOTAL_LOADS: 0,
            _STATS_KEY_COLLISIONS: 0,
            _STATS_KEY_RELOADS: 0,
            _STATS_KEY_PLUGINS_LOADED: 0,
        }

        # Phase 3: Initialize mtime cache for auto-reload
        # Key: module_name, Value: {"mtime": float, "path": str, "last_check": float}
        self._mtime_cache: Dict[str, Dict[str, Any]] = {}

        # Display ready message
        self.display.zDeclare(_MSG_READY, color=self.mycolor, indent=0, style="full")

    def load_plugins(self, plugin_paths: Optional[Union[List[str], str]]) -> Dict[str, Any]:
        """
        Load plugin modules into zLoader.plugin_cache and expose methods.

        Phase 2: This method now delegates storage to zLoader.plugin_cache instead
        of maintaining a separate self.plugins dict. This enables unified access:
        plugins loaded here are also accessible via &PluginName syntax.

        Parameters
        ----------
        plugin_paths : Optional[Union[List[str], str]]
            List of plugin paths (import paths or absolute .py file paths).
            Can be None or empty list (returns empty dict).
            Supports both:
                - Absolute file paths: "/path/to/plugin.py"
                - Module import paths: "package.module.plugin"

        Returns
        -------
        Dict[str, Any]
            Dictionary of successfully loaded plugin modules from zLoader.plugin_cache.
            Key: Plugin name (filename without .py)
            Value: Loaded module object (with zcli injected)

        Notes
        -----
        **Phase 2 Loading Process**:
            1. Validate plugin_paths (return empty dict if None/empty)
            2. Iterate through paths with progress display
            3. Detect path type (file path vs import path)
            4. Load module using appropriate method
            5. Cache in zLoader.plugin_cache (unified storage)
            6. Expose module callables as methods (with __all__ security check)
            7. Return loaded plugins from zLoader.plugin_cache

        **Unified Storage**:
            Plugins are stored in zLoader.plugin_cache by filename (e.g., "test_plugin").
            This enables cross-access:
                - zcli.utils.test_function() (method exposure)
                - &test_plugin.test_function() (runtime invocation)
            Both access the same cached module!

        **Security (Phase 2)**:
            Method exposure now respects __all__ attribute:
                - If plugin has __all__: Only exposes listed functions
                - If plugin lacks __all__: Logs warning, exposes all (backward compat)
            This prevents accidental exposure of imported functions.

        **Session Injection**:
            Each plugin module receives `module.zcli = self.zcli` via
            zLoader.plugin_cache.load_and_cache(), enabling plugins to access:
                - zcli.logger: Logging functionality
                - zcli.session: Session data (zSpace, zMachine, etc.)
                - zcli.data: Data subsystem access
                - zcli.display: Display subsystem access
                - All other zCLI subsystems

        **Error Handling**:
            Best-effort loading: plugin failures don't crash boot.
            Errors are logged as warnings, and loading continues.

        Examples
        --------
        **Load from file path**:
            >>> plugins = zcli.utils.load_plugins(["/path/to/my_plugin.py"])
            >>> zcli.utils.my_plugin_function()  # Method exposure
            >>> zcli.zparser.resolve_plugin_invocation("&my_plugin.my_plugin_function()")  # Cross-access!

        **Secure plugin with __all__**:
            >>> # Plugin file:
            >>> from os import system
            >>> def safe_func(): pass
            >>> __all__ = ['safe_func']
            >>> 
            >>> # Usage:
            >>> zcli.utils.load_plugins(["my_plugin.py"])
            >>> zcli.utils.safe_func()  # ✅ Works
            >>> zcli.utils.system()      # ❌ Not exposed (secure!)

        **Access via shell**:
            >>> # From zShell:
            >>> utils my_function arg1 arg2
            >>> # Executes: zcli.utils.my_function(arg1, arg2)
        """
        # Handle None or empty list
        if not plugin_paths:
            return DEFAULT_PLUGINS_DICT.copy()

        # Convert single string to list
        if isinstance(plugin_paths, str):
            plugin_paths = [plugin_paths]

        loaded_plugins: Dict[str, Any] = {}
        
        # Use progress iterator for plugin loading
        for path in self.display.progress_iterator(plugin_paths, _LOG_MSG_LOADING):
            try:
                # Load single plugin (delegated to helper)
                result = self._load_single_plugin(path)
                
                # Store in result dict if successful
                if result:
                    module_name, module = result
                    loaded_plugins[module_name] = module

            except ImportError as e:
                self.logger.warning(_WARN_MSG_LOAD_FAILED, path, f"ImportError: {e}")
            except AttributeError as e:
                self.logger.warning(_WARN_MSG_LOAD_FAILED, path, f"AttributeError: {e}")
            except PermissionError as e:
                self.logger.warning(_WARN_MSG_LOAD_FAILED, path, f"PermissionError: {e}")
            except Exception as e:
                self.logger.warning(_WARN_MSG_LOAD_FAILED, path, e)

        return loaded_plugins

    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================

    def _load_single_plugin(self, path: str) -> Optional[tuple]:
        """
        Load a single plugin and return its name and module.

        Helper method extracted from load_plugins() to reduce complexity.
        Handles the complete loading process for one plugin including collision
        detection, loading, caching, stats tracking, mtime tracking, and method exposure.

        Parameters
        ----------
        path : str
            Plugin path (file path or module import path)

        Returns
        -------
        Optional[tuple]
            Tuple of (module_name, module) if successful, None if failed

        Raises
        ------
        ValueError
            If plugin collision detected (same name, different path)
        ImportError
            If module loading fails
        AttributeError
            If zLoader unavailable
        PermissionError
            If file access denied
        Exception
            For any other loading errors

        Notes
        -----
        This method performs the following steps:
            1. Extract module name from path
            2. Check for name collisions
            3. Load module (file path vs import path)
            4. Validate module loaded successfully
            5. Update stats (total_loads, plugins_loaded)
            6. Track mtime for auto-reload (file paths only)
            7. Expose callables as methods
            8. Log success

        All exceptions are propagated to caller for centralized error handling.
        """
        self.logger.debug(_LOG_MSG_LOAD_START, path)

        # Extract module name from path
        module_name = self._extract_module_name(path)

        # Phase 3: Collision detection
        existing_info = self._check_collision(module_name, path)
        if existing_info:
            self._stats[_STATS_KEY_COLLISIONS] += 1
            error_msg = _ERROR_MSG_COLLISION.format(
                name=module_name,
                existing_path=existing_info
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Load module and cache in zLoader.plugin_cache
        if self._is_file_path(path):
            # Check if JavaScript file
            if path.endswith('.js'):
                module = self._register_js_plugin(path, module_name)
            else:
                module = self._load_and_cache_from_file(path, module_name)
        else:
            module = self._load_and_cache_from_module(path)

        # Skip if module failed to load
        if not module:
            self.logger.warning(_WARN_MSG_NO_MODULE, path)
            return None

        # Phase 3: Update stats
        self._stats[_STATS_KEY_TOTAL_LOADS] += 1
        self._stats[_STATS_KEY_PLUGINS_LOADED] += 1

        # Phase 3: Track mtime for auto-reload
        if self._is_file_path(path):
            self._track_mtime(module_name, path)

        # Expose callables as methods (with security check)
        exposed_count = self._expose_callables_secure(module, path, module_name)

        if exposed_count > 0:
            self.logger.debug(_LOG_MSG_EXPOSED_COUNT, exposed_count, path)

        self.logger.debug(_LOG_MSG_LOAD_SUCCESS, path)

        return (module_name, module)

    def _extract_module_name(self, path: str) -> str:
        """
        Extract module name from path.

        Parameters
        ----------
        path : str
            Plugin path (file or module import path)

        Returns
        -------
        str
            Module name (filename without .py or last segment of import path)
        """
        if self._is_file_path(path):
            return Path(path).stem
        else:
            return path.split('.')[-1]

    def _is_file_path(self, path: str) -> bool:
        """
        Check if path is an absolute file path.

        Parameters
        ----------
        path : str
            Path to check

        Returns
        -------
        bool
            True if path is absolute file path ending with .py or .js, False otherwise
        """
        return isinstance(path, str) and (path.endswith('.py') or path.endswith('.js')) and os.path.isabs(path)

    def _load_and_cache_from_file(self, path: str, module_name: str) -> Optional[Any]:
        """
        Load plugin from file and cache in zLoader.plugin_cache.

        Parameters
        ----------
        path : str
            Absolute path to .py plugin file
        module_name : str
            Module name for caching

        Returns
        -------
        Optional[Any]
            Loaded module object from cache, or None if loading failed

        Raises
        ------
        ImportError
            If module spec creation or loading fails
        AttributeError
            If zLoader unavailable
        """
        # Check if zLoader available
        if not hasattr(self.zcli, 'loader') or not hasattr(self.zcli.loader, 'cache'):
            self.logger.error(_ERROR_MSG_LOADER_UNAVAILABLE.format(path=path))
            raise AttributeError(_ERROR_MSG_LOADER_UNAVAILABLE.format(path=path))

        # Delegate to zLoader.plugin_cache
        module = self.zcli.loader.cache.plugin_cache.load_and_cache(path, module_name)

        self.logger.debug(_LOG_MSG_CACHED_TO_LOADER, module_name)
        return module

    def _register_js_plugin(self, path: str, module_name: str) -> Optional[Any]:
        """
        Register a JavaScript plugin as a callable proxy module.
        
        JavaScript plugins can't be imported into Python like Python plugins.
        Instead, we create a proxy module that stores the path and allows
        functions to be called via the zFunc JS executor.
        
        Parameters
        ----------
        path : str
            Absolute path to .js plugin file
        module_name : str
            Module name for registration
        
        Returns
        -------
        Optional[Any]
            Proxy module object with __js_plugin_path__ attribute
        
        Notes
        -----
        JavaScript plugins work differently from Python plugins:
        - They are not actually "imported" into Python
        - Instead, a proxy module is created that stores the file path
        - Functions are called via Node.js subprocess when invoked through zFunc
        - Use syntax: @.plugin_name.js.function_name(args) in zFunc
        
        Example
        -------
        >>> # Register JS plugin
        >>> zcli.utils.load_plugins(["/path/to/calculator.js"])
        >>> # Use via zFunc path (recommended)
        >>> result = zcli.zfunc.handle("@.calculator.js.add(5, 3)")
        """
        from types import SimpleNamespace
        
        # Create a proxy module namespace
        proxy_module = SimpleNamespace()
        proxy_module.__name__ = module_name
        proxy_module.__file__ = path
        proxy_module.__js_plugin_path__ = path
        proxy_module.zcli = self.zcli
        
        # Store in plugin cache (same as Python plugins for consistency)
        if hasattr(self.zcli, 'loader') and hasattr(self.zcli.loader, 'cache'):
            self.zcli.loader.cache.plugin_cache._cache[module_name] = proxy_module
            self.logger.debug(f"Registered JavaScript plugin: {module_name} -> {path}")
        
        return proxy_module

    def _load_and_cache_from_module(self, path: str) -> Optional[Any]:
        """
        Load plugin from module import path.

        Note: Module import paths are not cached in zLoader.plugin_cache (only file paths).
        This is a fallback for import-based plugins.

        Parameters
        ----------
        path : str
            Module import path (e.g., "package.module.plugin")

        Returns
        -------
        Optional[Any]
            Loaded module object, or None if loading failed

        Raises
        ------
        ImportError
            If module cannot be imported
        """
        mod = importlib.import_module(path)
        # Inject session (for import-based plugins)
        setattr(mod, _ATTR_NAME_ZCLI, self.zcli)
        self.logger.debug(_LOG_MSG_LOADED_MODULE, path)
        return mod

    def _expose_single_callable(
        self,
        attr_name: str,
        module: Any,
        path: str
    ) -> bool:
        """
        Expose a single callable from a plugin module as a method.

        Helper method to eliminate duplication in _expose_callables_secure().
        Handles the common logic for exposing a callable: getting the attribute,
        checking if it's callable, checking for collisions, and exposing it.

        Parameters
        ----------
        attr_name : str
            Name of the attribute to expose
        module : Any
            Plugin module containing the attribute
        path : str
            Plugin path (for logging collisions)

        Returns
        -------
        bool
            True if callable was exposed, False if skipped

        Notes
        -----
        Skips exposure if:
            - Attribute doesn't exist on module
            - Attribute is not callable
            - Attribute name collides with existing zUtils attribute
        """
        # Check if attribute exists
        if not hasattr(module, attr_name):
            return False

        # Get attribute
        func = getattr(module, attr_name)

        # Only expose callables
        if not callable(func):
            return False

        # Skip if name collision
        if hasattr(self, attr_name):
            self.logger.debug(_WARN_MSG_COLLISION, path, attr_name)
            return False

        # Expose as method
        setattr(self, attr_name, func)
        return True

    def _expose_callables_secure(self, module: Any, path: str, module_name: str) -> int:
        """
        Expose module callables as methods with __all__ security check.

        Phase 2: This method now checks for __all__ attribute to enforce explicit
        function exports. Only functions listed in __all__ are exposed, preventing
        accidental exposure of imported functions (security vulnerability fix).

        Parameters
        ----------
        module : Any
            Plugin module to expose callables from
        path : str
            Plugin path (for logging)
        module_name : str
            Module name (for logging)

        Returns
        -------
        int
            Number of callables exposed

        Notes
        -----
        **Security (Phase 2)**:
            - If module has __all__: Only exposes functions listed in __all__
            - If module lacks __all__: Logs warning, exposes all public callables
            - Skips private attributes (names starting with _)
            - Skips if name collision with existing attributes

        **Example**:
            ```python
            # Secure plugin:
            from os import system
            def my_func(): pass
            __all__ = ['my_func']  # Only my_func exposed
            
            # Insecure plugin (backward compat):
            from os import system
            def my_func(): pass
            # No __all__ → both my_func AND system exposed (warning logged)
            ```
        """
        exposed_count = 0

        # Check if module defines __all__ (secure approach)
        if hasattr(module, _ATTR_NAME_ALL):
            all_exports = getattr(module, _ATTR_NAME_ALL)
            self.logger.debug(_LOG_MSG_USING_ALL, module_name, len(all_exports))

            # Only expose functions listed in __all__
            for attr_name in all_exports:
                if not hasattr(module, attr_name):
                    self.logger.warning(_WARN_MSG_NOT_IN_ALL, attr_name, module_name)
                    continue

                # Delegate to helper (DRY)
                if self._expose_single_callable(attr_name, module, path):
                    exposed_count += 1

        else:
            # No __all__ defined - fallback to all public callables (backward compat)
            self.logger.warning(_WARN_MSG_NO_ALL, module_name)

            for attr_name in dir(module):
                # Skip private attributes
                if attr_name.startswith(_ATTR_PREFIX_PRIVATE):
                    continue

                # Delegate to helper (DRY)
                if self._expose_single_callable(attr_name, module, path):
                    exposed_count += 1

        return exposed_count

    def _check_collision(self, module_name: str, path: str) -> Optional[str]:
        """
        Check if a plugin with this name is already loaded (Phase 3).

        Parameters
        ----------
        module_name : str
            Module name to check
        path : str
            Path of plugin being loaded

        Returns
        -------
        Optional[str]
            Path of existing plugin if collision detected, None otherwise

        Notes
        -----
        Checks both zLoader.plugin_cache and local mtime cache for collisions.
        """
        # Check if already in mtime cache
        if module_name in self._mtime_cache:
            existing_path = self._mtime_cache[module_name].get(_PATH_CACHE_KEY)
            if existing_path and existing_path != path:
                return existing_path

        # Check if already in zLoader.plugin_cache
        if hasattr(self.zcli, 'loader') and hasattr(self.zcli.loader, 'cache'):
            existing_module = self.zcli.loader.cache.get(module_name, cache_type=_CACHE_TYPE_PLUGIN)
            if existing_module:
                # Try to get path from loader cache
                plugin_list = self.zcli.loader.cache.plugin_cache.list_plugins()
                for plugin_info in plugin_list:
                    if plugin_info.get("name") == module_name:
                        existing_path = plugin_info.get("path")
                        if existing_path and existing_path != path:
                            return existing_path

        return None

    def _track_mtime(self, module_name: str, path: str) -> None:
        """
        Track file modification time for auto-reload (Phase 3).

        Parameters
        ----------
        module_name : str
            Module name
        path : str
            Absolute path to plugin file

        Notes
        -----
        Stores mtime, path, and last_check timestamp for later comparison.
        """
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            self._mtime_cache[module_name] = {
                _MTIME_CACHE_KEY: mtime,
                _PATH_CACHE_KEY: path,
                "last_check": time.time()
            }

    def _check_and_reload(self, module_name: str) -> bool:
        """
        Check if plugin file changed and reload if necessary (Phase 3).

        Parameters
        ----------
        module_name : str
            Module name to check

        Returns
        -------
        bool
            True if plugin was reloaded, False otherwise

        Notes
        -----
        Uses _MTIME_CHECK_INTERVAL to throttle filesystem checks.
        Only reloads if file modification time changed.
        """
        # Check if module is tracked
        if module_name not in self._mtime_cache:
            return False

        cache_entry = self._mtime_cache[module_name]
        current_time = time.time()
        last_check = cache_entry.get("last_check", 0)

        # Throttle checks using interval
        if current_time - last_check < _MTIME_CHECK_INTERVAL:
            return False

        # Update last check time
        cache_entry["last_check"] = current_time

        # Check if file still exists
        path = cache_entry.get(_PATH_CACHE_KEY)
        if not path or not os.path.exists(path):
            return False

        # Check if mtime changed
        current_mtime = os.path.getmtime(path)
        cached_mtime = cache_entry.get(_MTIME_CACHE_KEY, 0)

        if current_mtime > cached_mtime:
            # File changed, reload
            self.logger.info(f"Plugin file changed, reloading: {path}")
            try:
                # Reload via zLoader.plugin_cache
                if hasattr(self.zcli, 'loader') and hasattr(self.zcli.loader, 'cache'):
                    module = self.zcli.loader.cache.plugin_cache.load_and_cache(path, module_name)
                    if module:
                        # Update mtime cache
                        cache_entry[_MTIME_CACHE_KEY] = current_mtime
                        # Re-expose callables
                        self._expose_callables_secure(module, path, module_name)
                        # Update stats
                        self._stats[_STATS_KEY_RELOADS] += 1
                        self.logger.info(f"Plugin reloaded successfully: {module_name}")
                        return True
            except Exception as e:
                self.logger.warning(f"Failed to reload plugin '{module_name}': {e}")

        return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get plugin loading statistics (Phase 3).

        Returns
        -------
        Dict[str, Any]
            Statistics dictionary with the following keys:
                - plugins_loaded: Number of currently loaded plugins
                - total_loads: Total number of load operations
                - collisions: Number of collision errors
                - reloads: Number of auto-reloads due to file changes
                - hit_rate: Cache hit rate (if available from zLoader)

        Examples
        --------
        >>> stats = zcli.utils.get_stats()
        >>> print(f"Loaded {stats['plugins_loaded']} plugins")
        >>> print(f"Collisions: {stats['collisions']}")
        >>> print(f"Reloads: {stats['reloads']}")
        """
        stats = self._stats.copy()

        # Add hit_rate from zLoader.plugin_cache if available
        if hasattr(self.zcli, 'loader') and hasattr(self.zcli.loader, 'cache'):
            try:
                cache_stats = self.zcli.loader.cache.plugin_cache.get_stats()
                if cache_stats:
                    stats["cache_hits"] = cache_stats.get("hits", 0)
                    stats["cache_misses"] = cache_stats.get("misses", 0)
                    hits = cache_stats.get("hits", 0)
                    misses = cache_stats.get("misses", 0)
                    total = hits + misses
                    if total > 0:
                        stats["hit_rate"] = f"{(hits / total * 100):.1f}%"
                    else:
                        stats["hit_rate"] = "N/A"
            except Exception as e:
                self.logger.debug(f"Could not get cache stats: {e}")

        return stats

    @property
    def plugins(self) -> Dict[str, Any]:
        """
        Get loaded plugins from zLoader.plugin_cache.

        Phase 2: This property provides backward compatibility for code that
        accesses zcli.utils.plugins. It returns plugins from zLoader.plugin_cache
        instead of a local dict.

        Phase 3: Checks for file changes and auto-reloads if necessary.

        Returns
        -------
        Dict[str, Any]
            Dictionary of loaded plugins from zLoader.plugin_cache
            Key: Module name (filename without .py)
            Value: Module object

        Notes
        -----
        **Backward Compatibility**:
            Old code: `zcli.utils.plugins[path]`
            New code: Uses zLoader.plugin_cache internally
            Both work! This property bridges the gap.

        **Performance**:
            This is a dynamic property that queries zLoader.plugin_cache on each
            access. For frequent access, consider caching the result.

        **Auto-Reload (Phase 3)**:
            Checks tracked plugins for file changes and auto-reloads if necessary.
        """
        # Phase 3: Check for file changes and auto-reload
        for module_name in list(self._mtime_cache.keys()):
            self._check_and_reload(module_name)

        if not hasattr(self.zcli, 'loader') or not hasattr(self.zcli.loader, 'cache'):
            return DEFAULT_PLUGINS_DICT.copy()

        # Get plugins from zLoader.plugin_cache
        plugin_list = self.zcli.loader.cache.plugin_cache.list_plugins()

        # Convert to dict (name -> module)
        plugins_dict = {}
        for plugin_info in plugin_list:
            name = plugin_info.get("name")
            if name:
                # Get module from cache
                module = self.zcli.loader.cache.get(name, cache_type=_CACHE_TYPE_PLUGIN)
                if module:
                    plugins_dict[name] = module

        return plugins_dict
