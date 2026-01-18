# zCLI/subsystems/zNavigation/navigation_modules/navigation_linking.py

"""
Inter-File Linking (zLink) for zNavigation - Navigation Flow Component.

This module provides the Linking class, which handles inter-file navigation via
zLink expressions. It parses zLink syntax, validates RBAC permissions, loads
target files, and orchestrates navigation to the linked block.

Architecture
------------
The Linking class is a Tier 1 (Foundation) component that manages zLink navigation:

1. **Parse zLink Expression** (parse_zLink_expression)
   - Extracts file path and optional permission requirements
   - Supports: zLink(path) or zLink(path, {"role": "admin"})
   - Uses zParser.zExpr_eval() for permission dict parsing

2. **Check RBAC Permissions** (check_zLink_permissions)
   - Validates user permissions against required permissions
   - Reads from session[SESSION_KEY_ZAUTH]
   - Denies access if permissions don't match

3. **Execute Navigation** (handle)
   - Orchestrates the full linking flow
   - Updates session with new file/block context
   - Delegates to zLoader for file loading
   - Delegates to zWalker for block execution

zLink Syntax
------------
Basic link (no permissions)::

    zLink(@.zUI.settings.NetworkSettings)

Link with permission requirements::

    zLink(@.zUI.admin.UserManagement, {"role": "admin"})
    zLink(@.zUI.finance.Reports, {"role": "finance", "level": "manager"})

Path Format:
- @ = Base path (workspace root)
- zUI = UI directory
- filename = YAML file name (without extension)
- BlockName = Target block within file

RBAC Integration
----------------
Permission checking uses the zAuth subsystem:

1. Retrieves user auth data from session[SESSION_KEY_ZAUTH]
2. Compares user attributes with required permissions (exact match)
3. Denies access if any required permission doesn't match
4. Allows access if no permissions specified (public link)

Example::

    # User in session
    session[SESSION_KEY_ZAUTH] = {"role": "admin", "level": "manager"}
    
    # Required permissions
    required = {"role": "admin"}
    
    # Check: user["role"] == required["role"] → True (access granted)

Session Updates
---------------
The linking process updates the following session keys:

- SESSION_KEY_ZVAFOLDER: Folder containing the file
- SESSION_KEY_ZVAFILE: Filename (without extension)
- SESSION_KEY_ZBLOCK: Target block name

These session keys are used by zLoader and zWalker to maintain navigation context.

Layer Position
--------------
Layer 1, Position 4 (zNavigation) - Tier 1 (Foundation)

Integration
-----------
- Called by: zNavigation facade, dispatch_launcher (3 call sites)
- Uses: zParser (zExpr_eval), zLoader (file loading), zWalker (block execution)
- Session: Reads SESSION_KEY_ZAUTH, writes SESSION_KEY_ZVAFOLDER, etc.
- Logging: Debug for flow, info for parsing, warning for permission denials

Forward Dependencies
--------------------
This module depends on:

1. **zParser (Week 6.8):**
   - zExpr_eval() for parsing permission dict strings
   
2. **zLoader (Week 6.9):**
   - loader.handle() for loading target YAML files
   
3. **zWalker (Week 6.11):**
   - walker.display for UI declarations
   - walker.loader for file loading
   - walker.zCrumbs for breadcrumb management
   - walker.zBlock_loop() for executing target block

Usage Examples
--------------
Parse a basic zLink::

    linking = Linking(navigation_system)
    path, perms = linking.parse_zLink_expression(walker, "zLink(@.zUI.settings.Main)")
    # path = "@.zUI.settings.Main"
    # perms = {}

Parse a zLink with permissions::

    path, perms = linking.parse_zLink_expression(
        walker,
        'zLink(@.zUI.admin.Users, {"role": "admin"})'
    )
    # path = "@.zUI.admin.Users"
    # perms = {"role": "admin"}

Check permissions::

    has_access = linking.check_zLink_permissions(walker, {"role": "admin"})
    # Returns True if user has admin role, False otherwise

Execute full linking flow::

    result = linking.handle(walker, 'zLink(@.zUI.settings.Network)')
    # Navigates to Network block in settings file

Module Constants
----------------
DISPLAY_* : str
    Display settings (color, styles, indents)
STATUS_* : str
    Status values for navigation results
MSG_* : str
    Message strings for permission denials and errors
LOG_* : str
    Log message templates
PARSE_* : str
    Parsing literals for zLink expression syntax
PATH_* : str
    Path parsing constants
"""

from zOS import Any, Dict, List, Optional, Tuple
from zOS.L2_Core.g_zParser.parser_modules.parser_utils import zExpr_eval
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (
    SESSION_KEY_ZAUTH,
    SESSION_KEY_ZVAFOLDER,
    SESSION_KEY_ZVAFILE,
    SESSION_KEY_ZBLOCK,
    SESSION_KEY_ZCRUMBS,
)

from .navigation_helpers import reload_current_file
from .navigation_constants import (
    DISPLAY_COLOR_ZLINK,
    _DISPLAY_STYLE_FULL,
    _DISPLAY_STYLE_SINGLE,
    _DISPLAY_INDENT_HANDLE,
    _DISPLAY_INDENT_PARSE,
    _DISPLAY_INDENT_AUTH,
    _DISPLAY_MSG_HANDLE_ZLINK,
    _DISPLAY_MSG_PARSE,
    _DISPLAY_MSG_AUTH,
    STATUS_STOP,
    _MSG_PERMISSION_DENIED,
    _MSG_NO_WALKER,
    _LOG_INCOMING_REQUEST,
    _LOG_ZLINK_PATH,
    _LOG_REQUIRED_PERMS,
    _LOG_ZFILE_PARSED,
    _LOG_RAW_EXPRESSION,
    _LOG_STRIPPED_INNER,
    _LOG_PATH_PART,
    _LOG_PERMS_PART_RAW,
    _LOG_PARSED_PERMS,
    _LOG_WARN_NON_DICT,
    _LOG_NO_PERMS_BLOCK,
    _LOG_ZAUTH_USER,
    _LOG_REQUIRED_PERMS_CHECK,
    _LOG_NO_PERMS_REQUIRED,
    _LOG_CHECK_PERM_KEY,
    _LOG_WARN_PERM_DENIED,
    _LOG_ALL_PERMS_MATCHED,
    _PARSE_PREFIX_ZLINK,
    _PARSE_SUFFIX_RPAREN,
    _PARSE_PERMS_SEPARATOR,
    _PARSE_BRACE_OPEN,
    _PARSE_BRACE_CLOSE,
    _PATH_SEPARATOR,
    _PATH_INDEX_LAST,
    _PATH_INDEX_BLOCK,
    _PATH_INDEX_FILENAME_START,
    _PATH_PARTS_MIN,
    _PATH_PARTS_BASE_OFFSET,
    _PATH_DEFAULT_BASE,
)


# ============================================================================
# Linking Class
# ============================================================================

class Linking:
    """
    Inter-file linking manager for zNavigation.
    
    Handles zLink expressions for navigating between files and blocks. Parses
    zLink syntax, validates RBAC permissions, loads target files, and orchestrates
    navigation flow via zWalker.
    
    Attributes
    ----------
    navigation : Any
        Reference to parent navigation system
    zcli : Any
        Reference to zCLI core instance
    logger : Any
        Logger instance for linking operations
    zSession : Dict[str, Any]
        Direct reference to zcli.session (for convenience)
    
    Methods
    -------
    handle(walker, zHorizontal)
        Execute full zLink navigation flow
    parse_zLink_expression(walker, expr)
        Parse zLink expression to extract path and permissions
    check_zLink_permissions(walker, required)
        Check if user has required permissions
    
    Private Methods
    ---------------
    _update_session_path(zLink_path, selected_zBlock)
        Update session with new file/block context
    
    Examples
    --------
    Execute a zLink::
    
        linking = Linking(navigation_system)
        result = linking.handle(walker, 'zLink(@.zUI.settings.Network)')
    
    Parse and check permissions::
    
        path, perms = linking.parse_zLink_expression(
            walker,
            'zLink(@.zUI.admin.Users, {"role": "admin"})'
        )
        has_access = linking.check_zLink_permissions(walker, perms)
    
    Integration
    -----------
    - Parent: zNavigation system
    - Session: Reads SESSION_KEY_ZAUTH, writes SESSION_KEY_ZVAFOLDER/ZVAFILENAME/ZBLOCK
    - Walker: Passed as parameter for display, loader, zCrumbs, zBlock_loop access
    - Logging: Debug for flow, info for parsing, warning for denials
    
    Forward Dependencies
    --------------------
    - zParser: zExpr_eval() for permission dict parsing
    - zLoader: walker.loader.handle() for file loading
    - zWalker: walker.display, walker.zCrumbs, walker.zBlock_loop()
    """

    # Class-level type declarations
    navigation: Any  # Navigation system reference
    zcli: Any  # zCLI core instance
    logger: Any  # Logger instance
    zSession: Dict[str, Any]  # Direct reference to session

    def __init__(self, navigation: Any) -> None:
        """
        Initialize linking manager.
        
        Args
        ----
        navigation : Any
            Parent navigation system instance that provides access to zcli and logger
        
        Notes
        -----
        Stores references to the parent navigation system, zcli core, logger, and
        session for use during linking operations. The zSession reference is stored
        for convenience to avoid repeated `self.zcli.session` lookups.
        
        Session Dependencies
        --------------------
        This module manages the following session keys:
        - SESSION_KEY_ZAUTH: Read for permission checking
        - SESSION_KEY_ZVAFOLDER: Written during navigation
        - SESSION_KEY_ZVAFILE: Written during navigation
        - SESSION_KEY_ZBLOCK: Written during navigation
        """
        self.navigation = navigation
        self.zcli = navigation.zcli
        self.logger = navigation.logger
        self.zSession = self.zcli.session  # Store for convenience

    # ========================================================================
    # Private Helper Methods (extracted from handle() for decomposition)
    # ========================================================================

    def _handle_http_route_detection(
        self,
        walker: Any,
        zLink_path: str
    ) -> Optional[Any]:
        """
        Handle HTTP route detection for Web mode.
        
        Detects if zLink is an HTTP route (starts with "/") and handles it
        appropriately for Web mode (return redirect metadata) or Terminal mode
        (show warning and stop).
        
        Args:
            walker: zWalker instance with session and display
            zLink_path: Parsed zLink path
        
        Returns:
            - Redirect metadata dict if Web mode HTTP route
            - STATUS_STOP if Terminal mode HTTP route (invalid)
            - None if not an HTTP route (continue normal processing)
        """
        # HTTP ROUTE DETECTION (v1.5.4 Phase 3 - Demo 4)
        if not zLink_path.startswith("/"):
            return None  # Not an HTTP route, continue normal processing
        
        self.logger.info(f"[zLink] HTTP route detected: {zLink_path}")
        
        # Get display mode from session
        from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZMODE
        mode = walker.session.get(SESSION_KEY_ZMODE, "Terminal")
        
        if mode == "Web":
            # WEB MODE: Return metadata for HTML link rendering
            self.logger.debug(f"[zLink] Web mode - returning redirect metadata")
            return {
                "type": "http_redirect",
                "url": zLink_path,
                "mode": "web"
            }
        else:
            # TERMINAL MODE: HTTP routes don't make sense here
            self.logger.warning(f"[zLink] HTTP route '{zLink_path}' in Terminal mode - skipping navigation")
            walker.display.handle({
                "event": "warning",
                "content": f"HTTP route '{zLink_path}' cannot be navigated in Terminal mode",
                "indent": 1
            })
            return STATUS_STOP

    def _capture_source_breadcrumb(
        self,
        walker: Any,
        is_navbar_navigation: bool
    ) -> None:
        """
        Capture SOURCE context breadcrumb BEFORE navigation.
        
        Records the source location (where we're navigating FROM) by adding
        a breadcrumb for the calling key. Skips this if navbar navigation
        (will be cleared by OP_RESET anyway).
        
        Args:
            walker: zWalker instance with session and navigation
            is_navbar_navigation: Whether this is a navbar navigation (skip recording)
        """
        from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZCRUMBS
        
        # Get crumbs dict (handle enhanced format)
        crumbs_dict = walker.session.get(SESSION_KEY_ZCRUMBS, {})
        
        # Get trails from enhanced format or use old format
        if 'trails' in crumbs_dict:
            trails = crumbs_dict['trails']
        else:
            trails = crumbs_dict
        
        source_block_path = next(reversed(trails)) if trails else None
        
        # NAVBAR NAVIGATION: Skip source breadcrumb recording
        if is_navbar_navigation:
            self.logger.debug("[zLink] Skipping source breadcrumb (navbar navigation will RESET)")
            return
        
        # REGULAR NAVIGATION: Record source breadcrumb
        if source_block_path and source_block_path in trails:
            source_trail = trails[source_block_path]
            source_zKey = source_trail[-1] if source_trail else None
            
            if source_zKey:
                walker.navigation.breadcrumbs.handle_zCrumbs(source_zKey, walker=walker)
                self.logger.debug(f"Recorded source breadcrumb: {source_block_path}[{source_zKey}]")

    def _get_or_discover_block(
        self,
        walker: Any,
        zFile_parsed: Dict[str, Any],
        selected_zBlock: str,
        zFile_path: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Get block from loaded file or auto-discover from separate file.
        
        Implements fallback chain:
        1. Try finding block in loaded file
        2. If not found, try loading from zUI.{blockName}.yaml
        
        Strips navigation modifiers (^ ~) from block name for file path
        since file names don't have modifiers.
        
        Args:
            walker: zWalker instance with loader
            zFile_parsed: Loaded file content
            selected_zBlock: Target block name (may have modifiers)
            zFile_path: Original file path
        
        Returns:
            Tuple of (block_dict, block_keys)
        
        Raises:
            Returns STATUS_STOP on failure (logs error)
        """
        # Try finding block in loaded file
        if selected_zBlock in zFile_parsed:
            active_zBlock_dict = zFile_parsed[selected_zBlock]
            self.logger.debug(f"[zLink] Block '{selected_zBlock}' found in loaded file")
            return active_zBlock_dict, list(active_zBlock_dict.keys())
        
        # AUTO-DISCOVERY: Try loading from separate file
        self.logger.debug(f"[zLink] Block '{selected_zBlock}' not in file, trying auto-discovery...")
        
        # Strip navigation modifiers from block name for file path
        file_block_name = selected_zBlock.lstrip("^~")
        
        # Construct fallback zPath
        if zFile_path.startswith("@"):
            path_parts = zFile_path.split(".")
            fallback_path_parts = path_parts[:-1] + [file_block_name]
            fallback_zPath = ".".join(fallback_path_parts)
        else:
            fallback_zPath = f"@.UI.zUI.{file_block_name}"
        
        self.logger.debug(f"[zLink] Trying fallback: {fallback_zPath} (stripped modifiers from '{selected_zBlock}')")
        
        try:
            fallback_zFile = walker.loader.handle(fallback_zPath)
            if fallback_zFile and isinstance(fallback_zFile, dict):
                if selected_zBlock in fallback_zFile:
                    active_zBlock_dict = fallback_zFile[selected_zBlock]
                    self.logger.info(f"✓ [zLink] Auto-discovered block '{selected_zBlock}' from: {fallback_zPath}")
                    return active_zBlock_dict, list(active_zBlock_dict.keys())
                else:
                    raise KeyError(f"Block '{selected_zBlock}' not found in {fallback_zPath}")
            else:
                raise ValueError(f"Failed to load {fallback_zPath}")
        except Exception as e:
            self.logger.error(
                f"Block '{selected_zBlock}' not found:\n"
                f"  - Not in loaded file: {zFile_path}\n"
                f"  - Fallback failed: {fallback_zPath}\n"
                f"  - Error: {e}"
            )
            raise  # Re-raise to be caught by caller

    def _setup_bounce_back_snapshot(
        self,
        walker: Any,
        selected_zBlock: str,
        source_folder: str,
        source_file: str,
        source_block: str
    ) -> Optional[Dict[str, Any]]:
        """
        Setup bounce-back snapshot if block has ^ modifier.
        
        Detects if block name starts with ^ (bounce-back modifier) and
        saves a deep copy of current breadcrumb state for later restoration.
        Also stores the source location to enable bounce-back even with no history.
        
        Args:
            walker: zWalker instance with session
            selected_zBlock: Target block name (may have ^ prefix)
            source_folder: Source folder path before navigation
            source_file: Source file name before navigation
            source_block: Source block name before navigation
        
        Returns:
            Deep copy of breadcrumb state with source location if bounce-back enabled, None otherwise
        """
        should_bounce_back = selected_zBlock.startswith("^")
        self.logger.debug(f"[zNavigation] Block name: '{selected_zBlock}', should_bounce_back: {should_bounce_back}")
        
        if not should_bounce_back:
            return None
        
        self.logger.info(f"[zNavigation] ⬅️  Block-level bounce-back enabled for: {selected_zBlock}")
        
        # Save deep copy of current breadcrumb state
        import copy
        from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZCRUMBS
        breadcrumb_snapshot = copy.deepcopy(walker.zcli.session.get(SESSION_KEY_ZCRUMBS, {}))
        
        # Store source location for bounce-back (needed when there's no history)
        breadcrumb_snapshot['_bounce_back_source'] = {
            'folder': source_folder,
            'file': source_file,
            'block': source_block
        }
        
        self.logger.debug(f"[zNavigation] 📸 Saved breadcrumb snapshot with source: {source_folder}.{source_file}.{source_block}")
        
        return breadcrumb_snapshot

    def _restore_bounce_back(
        self,
        walker: Any,
        result: Any,
        breadcrumb_snapshot: Optional[Dict[str, Any]]
    ) -> Any:
        """
        Restore breadcrumb state after bounce-back block execution.
        
        Restores the saved breadcrumb snapshot and continues walker execution
        from the original location. Skips restoration if user already navigated
        away (zBack, exit, etc.).
        
        Args:
            walker: zWalker instance with session and loader
            result: Result from block execution
            breadcrumb_snapshot: Saved breadcrumb state (None = skip restoration)
        
        Returns:
            Result from continued walker execution, or original result
        """
        if breadcrumb_snapshot is None:
            self.logger.warning("[zNavigation] No breadcrumb snapshot to restore!")
            return result
        
        # Skip bounce-back if user already navigated away
        if isinstance(result, dict) or result in ["zBack", "exit", "stop"]:
            self.logger.debug(f"[zNavigation] Skipping bounce-back restoration, result: {result}")
            return result
        
        self.logger.info("[zNavigation] ⬅️  Restoring breadcrumbs from snapshot!")
        
        # Clear _navbar_navigation flag before restoration
        if '_navbar_navigation' in breadcrumb_snapshot:
            del breadcrumb_snapshot['_navbar_navigation']
            self.logger.debug("[zNavigation] Cleared _navbar_navigation flag from snapshot")
        
        # Restore breadcrumb state
        from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZCRUMBS
        walker.zcli.session[SESSION_KEY_ZCRUMBS] = breadcrumb_snapshot
        self.logger.debug(f"[zNavigation] ✅ Restored breadcrumbs: {breadcrumb_snapshot}")
        
        # Get active crumb from restored snapshot
        if 'trails' in breadcrumb_snapshot:
            trail_keys = list(breadcrumb_snapshot['trails'].keys())
        else:
            trail_keys = [k for k in breadcrumb_snapshot.keys() if not k.startswith('_')]
        
        active_zCrumb = trail_keys[-1] if trail_keys else None
        
        # If no history, use the source location stored in snapshot
        if not active_zCrumb:
            # Extract source location from snapshot
            source_info = breadcrumb_snapshot.get('_bounce_back_source', {})
            source_folder = source_info.get('folder', '')
            source_file = source_info.get('file', '')
            source_block = source_info.get('block', '')
            
            if not source_file:
                # No history and no source info - this shouldn't happen but handle gracefully
                self.logger.warning("[zNavigation] No history to restore and no source info - bounce-back complete")
                return result
            
            # Navbar/root navigation - bounce back to source location
            self.logger.info(f"[zNavigation] ⬅️  No history, bouncing back to source: {source_folder}.{source_file}.{source_block}")
            
            # Build source zPath
            if source_folder:
                zPath = f"{source_folder}.{source_file}"
            else:
                zPath = f"@.{source_file}"
            
            # Update session to source location
            from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (
                SESSION_KEY_ZVAFOLDER,
                SESSION_KEY_ZVAFILE,
                SESSION_KEY_ZBLOCK
            )
            walker.zcli.session[SESSION_KEY_ZVAFOLDER] = source_folder
            walker.zcli.session[SESSION_KEY_ZVAFILE] = source_file
            walker.zcli.session[SESSION_KEY_ZBLOCK] = source_block
            
            # Load source file
            self.logger.debug(f"[zNavigation] Reloading source file: {zPath}")
            zFile_parsed = reload_current_file(walker)
            
            # Get source block
            source_zBlock_dict = zFile_parsed.get(source_block, {})
            source_zBlock_keys = list(source_zBlock_dict.keys())
            
            if not source_zBlock_keys:
                self.logger.warning(f"[zNavigation] Source block '{source_block}' has no keys - cannot continue")
                return result
            
            # Continue execution from source block
            self.logger.info(f"[zNavigation] ⏯  Continuing execution in source block: {source_block}")
            result = walker.execute_loop(items_dict=source_zBlock_dict)
            return result
        
        # Parse active crumb to get file/block info
        crumb_parts = active_zCrumb.split(".")
        if len(crumb_parts) < 3:
            self.logger.warning(f"[zNavigation] Invalid crumb format: {active_zCrumb}")
            return result
        
        # Extract path, filename, and block
        zVaFolder = ".".join(crumb_parts[:-2])
        zVaFile = ".".join(crumb_parts[-2:-1])
        zBlock = crumb_parts[-1]
        
        # Construct zPath and reload file
        zPath = f"{zVaFolder}.{zVaFile}"
        self.logger.debug(f"[zNavigation] Reloading file for bounce-back: {zPath}")
        
        # Load file and get block
        raw_zFile = walker.loader.handle(zPath=zPath)
        if zBlock not in raw_zFile:
            self.logger.warning(f"[zNavigation] Block '{zBlock}' not found in {zPath}")
            return result
        
        block_dict = raw_zFile[zBlock]
        
        # Get start key from restored trail
        if 'trails' in breadcrumb_snapshot:
            trail = breadcrumb_snapshot['trails'].get(active_zCrumb, [])
        else:
            trail = breadcrumb_snapshot.get(active_zCrumb, [])
        start_key = trail[-1] if trail else None
        
        self.logger.debug(f"[zNavigation] Continuing from: {zBlock}, start_key: {start_key}")
        
        # Re-execute block to continue walker
        bounce_result = walker.execute_loop(items_dict=block_dict, start_key=start_key)
        
        # Convert soft exit dict to signal string
        if isinstance(bounce_result, dict) and bounce_result.get("exit") == "completed":
            self.logger.debug("[zNavigation] User exited after bounce-back - converting to signal")
            return "exit"
        
        return bounce_result

    # ========================================================================
    # Public API
    # ========================================================================

    def handle(self, walker: Any, zHorizontal: str) -> str:
        """
        Handle zLink navigation request.
        
        Orchestrates the full linking flow: display declaration, parsing, permission
        checking, file loading, session updates, breadcrumb tracking, and block execution.
        
        Args
        ----
        walker : Any
            Walker instance providing display, loader, zCrumbs, and zBlock_loop access
        zHorizontal : str
            zLink expression to execute (e.g., 'zLink(@.zUI.settings.Network)')
        
        Returns
        -------
        str
            Navigation result:
            - STATUS_STOP if permission denied or walker is None
            - Result from walker.zBlock_loop() on success
        
        Examples
        --------
        Basic zLink (no permissions)::
        
            result = linking.handle(walker, 'zLink(@.zUI.settings.Main)')
            # Navigates to Main block in settings file
        
        zLink with permissions::
        
            result = linking.handle(
                walker,
                'zLink(@.zUI.admin.Users, {"role": "admin"})'
            )
            # Checks permissions, then navigates if allowed
        
        Handle permission denial::
        
            result = linking.handle(walker, 'zLink(@.zUI.admin.Users, {"role": "admin"})')
            if result == STATUS_STOP:
                print("Permission denied or error occurred")
        
        Notes
        -----
        - **Display Declaration**: Shows "Handle zLink" banner
        - **Parsing**: Extracts path and permissions from expression
        - **Permission Check**: Validates RBAC if permissions specified
        - **File Loading**: Uses walker.loader.handle() to load target file
        - **Session Update**: Updates file path, filename, and block in session
        - **Breadcrumb Tracking**: Calls walker.zCrumbs.handle_zCrumbs()
        - **Block Execution**: Returns result from walker.zBlock_loop()
        
        Algorithm
        ---------
        1. Display "Handle zLink" declaration
        2. Log incoming request
        3. Parse zLink expression (path + permissions)
        4. Log parsed values
        5. If permissions required and check fails, deny access (return STATUS_STOP)
        6. Load target file via walker.loader.handle()
        7. Extract target block name from path
        8. Update session with new file/block context
        9. Validate walker instance exists
        10. Track breadcrumb (walker.zCrumbs.handle_zCrumbs)
        11. Execute target block (walker.zBlock_loop)
        12. Return result
        """
        # ====================================================================
        # ORCHESTRATOR: Simplified handle() method using extracted helpers
        # ====================================================================
        
        # Display declaration
        walker.display.zDeclare(
            _DISPLAY_MSG_HANDLE_ZLINK,
            color=DISPLAY_COLOR_ZLINK,
            indent=_DISPLAY_INDENT_HANDLE,
            style=_DISPLAY_STYLE_FULL
        )

        # Log incoming request
        self.logger.debug(_LOG_INCOMING_REQUEST, zHorizontal)
        
        # Extract zLink value from dictionary
        if isinstance(zHorizontal, dict):
            zLink_expr = zHorizontal.get('zLink', '')
        else:
            zLink_expr = zHorizontal
        
        # Parse zLink expression (path + permissions)
        zLink_path, required_perms = self.parse_zLink_expression(walker, zLink_expr)
        self.logger.debug(_LOG_ZLINK_PATH, zLink_path)
        self.logger.debug(_LOG_REQUIRED_PERMS, required_perms)
        
        # HTTP ROUTE DETECTION: Handle Web mode routes early
        http_result = self._handle_http_route_detection(walker, zLink_path)
        if http_result is not None:
            return http_result  # Either redirect metadata or STATUS_STOP
        
        # FILE-BASED NAVIGATION: Continue with normal flow
        
        # Check permissions if required
        if required_perms and not self.check_zLink_permissions(walker, required_perms):
            print(_MSG_PERMISSION_DENIED)
            return STATUS_STOP

        # Extract target block name and file path
        path_parts = zLink_path.split(_PATH_SEPARATOR)
        selected_zBlock = path_parts[_PATH_INDEX_BLOCK]
        zFile_path = _PATH_SEPARATOR.join(path_parts[:-1])
        
        # Load target file
        zFile_parsed = walker.loader.handle(zFile_path)
        self.logger.debug(_LOG_ZFILE_PARSED, zFile_parsed)

        # BREADCRUMB FIX: Capture SOURCE context before navigation
        from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (
            SESSION_KEY_ZCRUMBS,
            SESSION_KEY_ZBLOCK,
            SESSION_KEY_ZVAFILE,
            SESSION_KEY_ZVAFOLDER
        )
        crumbs_dict = walker.session.get(SESSION_KEY_ZCRUMBS, {})
        is_navbar_navigation = crumbs_dict.get("_navbar_navigation", False)
        
        # Store source location BEFORE navigation (needed for bounce-back)
        source_folder = walker.session.get(SESSION_KEY_ZVAFOLDER, '')
        source_file = walker.session.get(SESSION_KEY_ZVAFILE, '')
        source_block = walker.session.get(SESSION_KEY_ZBLOCK, '')
        
        if is_navbar_navigation:
            self.logger.info(f"[zLink] Navbar navigation detected → will trigger OP_RESET")
        
        self._capture_source_breadcrumb(walker, is_navbar_navigation)

        # Update session to TARGET location
        self._update_session_path(zLink_path, selected_zBlock)

        # Get block dict with auto-discovery fallback
        try:
            active_zBlock_dict, zBlock_keys = self._get_or_discover_block(
                walker, zFile_parsed, selected_zBlock, zFile_path
            )
        except Exception:
            return STATUS_STOP

        # Validate walker instance
        if walker is None:
            self.logger.error(_MSG_NO_WALKER)
            return STATUS_STOP

        # DO NOT initialize target breadcrumb scope - let walker_dispatch handle it
        self.logger.debug(f"Navigating to target block: {zLink_path}")

        # BLOCK-LEVEL BOUNCE-BACK: Setup snapshot if ^ modifier present
        breadcrumb_snapshot = self._setup_bounce_back_snapshot(
            walker, selected_zBlock, source_folder, source_file, source_block
        )
        should_bounce_back = breadcrumb_snapshot is not None
        
        # Execute target block
        result = walker.execute_loop(items_dict=active_zBlock_dict)
        self.logger.debug(f"[zNavigation] Block execution result: {result}, should_bounce_back: {should_bounce_back}")
        
        # BOUNCE-BACK RESTORATION: Restore snapshot and continue if flagged
        if should_bounce_back:
            result = self._restore_bounce_back(walker, result, breadcrumb_snapshot)
        
        return result

    def parse_zLink_expression(
        self,
        walker: Any,
        expr: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Parse zLink expression to extract path and permissions.
        
        Parses zLink syntax to extract the file path and optional permission
        requirements. Uses zParser.zExpr_eval() to parse permission dict strings.
        
        Args
        ----
        walker : Any
            Walker instance providing display for UI declarations
        expr : str
            zLink expression string to parse
        
        Returns
        -------
        Tuple[str, Dict[str, Any]]
            Tuple of (path, permissions):
            - path (str): File path (e.g., "@.zUI.settings.Network")
            - permissions (Dict[str, Any]): Required permissions dict (empty if none)
        
        Examples
        --------
        Parse basic zLink (no permissions)::
        
            path, perms = linking.parse_zLink_expression(
                walker,
                "zLink(@.zUI.settings.Main)"
            )
            # path = "@.zUI.settings.Main"
            # perms = {}
        
        Parse zLink with permissions::
        
            path, perms = linking.parse_zLink_expression(
                walker,
                'zLink(@.zUI.admin.Users, {"role": "admin"})'
            )
            # path = "@.zUI.admin.Users"
            # perms = {"role": "admin"}
        
        Parse zLink with multiple permissions::
        
            path, perms = linking.parse_zLink_expression(
                walker,
                'zLink(@.zUI.finance.Reports, {"role": "finance", "level": "manager"})'
            )
            # path = "@.zUI.finance.Reports"
            # perms = {"role": "finance", "level": "manager"}
        
        Notes
        -----
        - **Display Declaration**: Shows "zLink Parsing" banner
        - **Syntax**: zLink(path) or zLink(path, {"key": "value"})
        - **Permission Parsing**: Uses zParser.zExpr_eval() to convert string to dict
        - **Error Handling**: Defaults to empty dict if parsing fails or returns non-dict
        - **Logging**: Info for expressions and parsed values, warning for non-dict results
        
        Algorithm
        ---------
        1. Display "zLink Parsing" declaration
        2. Log raw expression
        3. Strip "zLink(" prefix and ")" suffix
        4. Log stripped inner contents
        5. Check if ", {" exists (indicates permissions)
        6. If permissions:
           a. Split on ", {" to separate path and permissions
           b. Reconstruct permission dict string with braces
           c. Log path and permissions parts
           d. Parse permissions with zExpr_eval()
           e. Validate result is dict (default to {} if not)
           f. Log parsed permissions
        7. If no permissions:
           a. Use inner contents as path
           b. Set permissions to empty dict
           c. Log info message
        8. Return (path, permissions) tuple
        """
        # Display declaration
        walker.display.zDeclare(
            _DISPLAY_MSG_PARSE,
            color=DISPLAY_COLOR_ZLINK,
            indent=_DISPLAY_INDENT_PARSE,
            style=_DISPLAY_STYLE_SINGLE
        )

        # Log raw expression
        self.logger.info(_LOG_RAW_EXPRESSION, expr)

        # Check if expression has "zLink(" wrapper (imperative) or is raw path (declarative YAML)
        if expr.startswith(_PARSE_PREFIX_ZLINK) and expr.endswith(_PARSE_SUFFIX_RPAREN):
            # Imperative format: zLink(@.path) → strip wrapper
            inner = expr[len(_PARSE_PREFIX_ZLINK):-1].strip()
        else:
            # Declarative YAML format: already a raw path → use as-is
            inner = expr.strip()
        
        self.logger.info(_LOG_STRIPPED_INNER, inner)

        # Check if permissions are specified
        if _PARSE_PERMS_SEPARATOR in inner:
            # Split path and permissions
            path_str, perms_str = inner.rsplit(_PARSE_PERMS_SEPARATOR, 1)
            zLink_path = path_str.strip()
            
            # Reconstruct permission dict string
            perms_str = (
                _PARSE_BRACE_OPEN +
                perms_str.strip().rstrip(_PARSE_BRACE_CLOSE) +
                _PARSE_BRACE_CLOSE
            )
            
            # Log parts
            self.logger.info(_LOG_PATH_PART, zLink_path)
            self.logger.info(_LOG_PERMS_PART_RAW, perms_str)

            # Parse permissions with zExpr_eval
            required = zExpr_eval(perms_str, self.logger)
            
            # Validate result is dict
            if not isinstance(required, dict):
                self.logger.warning(_LOG_WARN_NON_DICT)
                required = {}
            else:
                self.logger.info(_LOG_PARSED_PERMS, required)
        else:
            # No permissions specified
            zLink_path = inner
            required = {}
            self.logger.debug(_LOG_NO_PERMS_BLOCK, zLink_path)
        
        return zLink_path, required

    def check_zLink_permissions(
        self,
        walker: Any,
        required: Dict[str, Any]
    ) -> bool:
        """
        Check if user has required permissions.
        
        Validates user permissions from session against required permissions dict.
        Uses exact matching: each required permission key must exist in user dict
        with the exact same value.
        
        Args
        ----
        walker : Any
            Walker instance providing display for UI declarations
        required : Dict[str, Any]
            Required permissions dict (e.g., {"role": "admin"})
        
        Returns
        -------
        bool
            True if user has all required permissions (or no permissions required),
            False if any permission check fails
        
        Examples
        --------
        Check admin role::
        
            # User: {"role": "admin"}
            has_access = linking.check_zLink_permissions(
                walker,
                {"role": "admin"}
            )
            # Returns: True
        
        Check multiple permissions::
        
            # User: {"role": "finance", "level": "manager"}
            has_access = linking.check_zLink_permissions(
                walker,
                {"role": "finance", "level": "manager"}
            )
            # Returns: True
        
        Permission mismatch::
        
            # User: {"role": "user"}
            has_access = linking.check_zLink_permissions(
                walker,
                {"role": "admin"}
            )
            # Returns: False (logs warning)
        
        No permissions required (public link)::
        
            has_access = linking.check_zLink_permissions(walker, {})
            # Returns: True (always allows access)
        
        Notes
        -----
        - **Display Declaration**: Shows "zLink Auth" banner
        - **User Data**: Reads from session[SESSION_KEY_ZAUTH]
        - **Exact Matching**: user[key] must == required[key] for all keys
        - **No Permissions**: Returns True if required dict is empty
        - **Missing Keys**: Returns False if user dict doesn't have required key
        - **Logging**: Debug for checks, warning for denials
        
        Algorithm
        ---------
        1. Display "zLink Auth" declaration
        2. Get user dict from session[SESSION_KEY_ZAUTH]
        3. Log user dict and required permissions
        4. If no permissions required, allow access (return True)
        5. For each required permission key:
           a. Get actual value from user dict
           b. Log comparison (key, expected, actual)
           c. If actual != expected, log warning and deny (return False)
        6. Log success message
        7. Return True (all permissions matched)
        """
        # Display declaration
        walker.display.zDeclare(
            _DISPLAY_MSG_AUTH,
            color=DISPLAY_COLOR_ZLINK,
            indent=_DISPLAY_INDENT_AUTH,
            style=_DISPLAY_STYLE_SINGLE
        )

        # Get user auth data from session
        user = self.zSession.get(SESSION_KEY_ZAUTH, {})
        
        # Log user and required permissions
        self.logger.debug(_LOG_ZAUTH_USER, user)
        self.logger.debug(_LOG_REQUIRED_PERMS_CHECK, required)

        # If no permissions required, allow access
        if not required:
            self.logger.debug(_LOG_NO_PERMS_REQUIRED)
            return True

        # Check each required permission
        for key, expected in required.items():
            actual = user.get(key)
            self.logger.debug(_LOG_CHECK_PERM_KEY, key, expected, actual)
            
            if actual != expected:
                self.logger.warning(_LOG_WARN_PERM_DENIED, key, expected, actual)
                return False

        # All permissions matched
        self.logger.debug(_LOG_ALL_PERMS_MATCHED)
        return True

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _update_session_path(
        self,
        zLink_path: str,
        selected_zBlock: str
    ) -> None:
        """
        Update session with new file/block context.
        
        Parses the zLink path to extract base path, filename, and block name,
        then updates the session accordingly.
        
        Args
        ----
        zLink_path : str
            Full zLink path (e.g., "@.zUI.settings.NetworkSettings")
        selected_zBlock : str
            Target block name (e.g., "NetworkSettings")
        
        Notes
        -----
        DRY Helper: Centralizes session path updates.
        
        Session Keys Updated:
        - SESSION_KEY_ZVAFOLDER: Folder path (e.g., "")
        - SESSION_KEY_ZVAFILE: Filename (e.g., "zUI.settings")
        - SESSION_KEY_ZBLOCK: Block name (e.g., "NetworkSettings")
        
        Algorithm
        ---------
        1. Extract path to file (everything except last part)
        2. Split path into parts by "."
        3. If >= 2 parts:
           a. Extract base path (all parts except last 2)
           b. Set zVaFolder to joined base path (or "" if empty)
           c. Set zVaFile to last 2 parts joined
        4. Else (< 2 parts):
           a. Set zVaFolder to ""
           b. Set zVaFile to entire path
        5. Set zBlock to selected_zBlock
        """
        # Extract path to file (without block name)
        path_to_file = zLink_path.rsplit(_PATH_SEPARATOR, 1)[0]
        parts = path_to_file.split(_PATH_SEPARATOR)
        
        # Parse path components
        if len(parts) >= _PATH_PARTS_MIN:
            base_path_parts = parts[:_PATH_PARTS_BASE_OFFSET]
            self.zSession[SESSION_KEY_ZVAFOLDER] = (
                _PATH_SEPARATOR.join(base_path_parts) if base_path_parts else _PATH_DEFAULT_BASE
            )
            self.zSession[SESSION_KEY_ZVAFILE] = _PATH_SEPARATOR.join(
                parts[_PATH_INDEX_FILENAME_START:]
            )
        else:
            self.zSession[SESSION_KEY_ZVAFOLDER] = _PATH_DEFAULT_BASE
            self.zSession[SESSION_KEY_ZVAFILE] = path_to_file
        
        # Set block name
        self.zSession[SESSION_KEY_ZBLOCK] = selected_zBlock
