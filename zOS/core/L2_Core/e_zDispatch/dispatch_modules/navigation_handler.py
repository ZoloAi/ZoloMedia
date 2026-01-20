# zOS/core/L2_Core/e_zDispatch/dispatch_modules/navigation_handler.py

"""
Navigation Handler Module for zDispatch Subsystem.

This module provides the NavigationHandler class, which handles zLink and zDelta
navigation commands. It supports inter-file navigation (zLink) and intra-file
block navigation (zDelta) with auto-discovery fallback.

Extracted from dispatch_launcher.py as part of Phase 2 refactoring.
This module depends on zNavigation subsystem and Walker, but has no internal
dispatch dependencies.

Supported Commands:
    - zLink: Inter-file navigation (menu:users, file paths, etc.)
    - zDelta: Intra-file block navigation with auto-discovery

Features:
    - zLink routing to zNavigation subsystem
    - zDelta target block resolution with fallback chain
    - Auto-discovery of blocks in separate files
    - Breadcrumb scope initialization for zDelta
    - Walker validation for navigation commands

Usage Example:
    handler = NavigationHandler(zcli, display, logger)
    
    # zLink command
    result = handler.handle_zlink({"zLink": "menu:users"}, walker)
    
    # zDelta command  
    result = handler.handle_zdelta({"zDelta": "$Demo_Block"}, walker)

Integration:
    - zNavigation: Inter-file navigation via zcli.navigation.handle_zLink()
    - Walker: Block execution and session management
    - zLoader: File loading for fallback discovery

Thread Safety:
    - Modifies walker.session in-place (zBlock, zCrumbs)
    - Not thread-safe for same walker instance
    - Safe for concurrent walkers
"""

from zOS import Any, Dict, Optional

# Import dispatch constants
from .dispatch_constants import (
    KEY_ZLINK,
    KEY_ZDELTA,
    _LABEL_HANDLE_ZDELTA,
    _DEFAULT_INDENT_HANDLER,
    _DEFAULT_STYLE_SINGLE,
)

class NavigationHandler:
    """
    Handles zLink and zDelta navigation commands.
    
    This class provides focused routing for navigation operations,
    supporting both inter-file (zLink) and intra-file (zDelta) navigation
    with auto-discovery and breadcrumb management.
    
    Attributes:
        zcli: Root zCLI instance (provides navigation, loader, logger)
        display: zDisplay instance for UI output (optional)
        logger: Logger instance for debug output
    
    Methods:
        handle_zlink(): Route zLink command to zNavigation
        handle_zdelta(): Handle zDelta intra-file navigation
        
        Private helpers:
        _resolve_delta_target_block(): Resolve target block with fallback
        _construct_fallback_zpath(): Build fallback zPath for auto-discovery
        _initialize_delta_breadcrumb_scope(): Create breadcrumb scope
        _check_walker(): Validate walker instance
        _display_handler(): Display handler label
    
    Example:
        handler = NavigationHandler(zcli, display, logger)
        
        # Inter-file navigation
        link_result = handler.handle_zlink({"zLink": "menu:users"}, walker)
        
        # Intra-file navigation with auto-discovery
        delta_result = handler.handle_zdelta({"zDelta": "$Settings"}, walker)
    """
    
    def __init__(self, zcli: Any, display: Any, logger: Any) -> None:
        """
        Initialize navigation handler.
        
        Args:
            zcli: Root zCLI instance (provides navigation, loader)
            display: zDisplay instance for UI output
            logger: Logger instance for debug output
        
        Example:
            handler = NavigationHandler(zcli, display, logger)
        """
        self.zcli = zcli
        self.display = display
        self.logger = logger
    
    # ========================================================================
    # PUBLIC API - Navigation Commands
    # ========================================================================
    
    def handle_zlink(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any]
    ) -> Optional[Any]:
        """
        Route zLink command to zNavigation subsystem.
        
        Handles inter-file navigation (menu links, file paths, etc.)
        Requires walker instance for navigation context.
        
        Args:
            zHorizontal: Dict containing KEY_ZLINK (target path)
            walker: Walker instance (required for navigation)
        
        Returns:
            Navigation result from zNavigation, or None if walker not available
        
        Example:
            result = handler.handle_zlink({"zLink": "menu:users"}, walker)
            result = handler.handle_zlink({"zLink": "@.UI.zSettings"}, walker)
        
        Notes:
            - Validates walker instance before proceeding
            - Delegates to zNavigation.handle_zLink()
            - Logs navigation attempt
        """
        if not self._check_walker(walker, "zLink"):
            return None
        
        self.logger.debug("[NavigationHandler] zLink command detected")
        return self.zcli.navigation.handle_zLink(zHorizontal, walker=walker)
    
    def handle_zdelta(
        self,
        zHorizontal: Dict[str, Any],
        walker: Optional[Any]
    ) -> Optional[Any]:
        """
        Handle zDelta intra-file block navigation.
        
        Navigates to a different block within the same UI file or
        auto-discovers blocks from separate files (fallback pattern).
        
        Args:
            zHorizontal: Dict containing KEY_ZDELTA (target block name)
            walker: Walker instance (required for navigation)
        
        Returns:
            Navigation result from walker.execute_loop(), or None if block not found
        
        Example:
            result = handler.handle_zdelta({"zDelta": "$Settings_Menu"}, walker)
            result = handler.handle_zdelta({"zDelta": "%Demo_Block"}, walker)
        
        Notes:
            - Strips $ or % prefix from target block name
            - Fallback: If block not in current file, tries loading zUI.{blockName}.yaml
            - Creates new breadcrumb scope for target block
            - Updates session zBlock to reflect navigation
        """
        if not self._check_walker(walker, "zDelta"):
            return None
        
        self._display_handler(_LABEL_HANDLE_ZDELTA)
        
        # Extract target block name
        target_block_name = zHorizontal[KEY_ZDELTA]
        
        # Strip $ or % prefix if present (delta navigation markers)
        if isinstance(target_block_name, str):
            if target_block_name.startswith(("$", "%")):
                target_block_name = target_block_name[1:]
        
        self.logger.framework.debug(f"[NavigationHandler] zDelta navigation to block: {target_block_name}")
        
        # Get current zVaFile from session
        current_zVaFile = walker.session.get("zVaFile") or walker.zSpark_obj.get("zVaFile")
        if not current_zVaFile:
            self.logger.error("[NavigationHandler] No zVaFile in session or zspark_obj")
            return None
        
        # Reload the UI file
        raw_zFile = walker.loader.handle(current_zVaFile)
        if not raw_zFile:
            self.logger.error(f"[NavigationHandler] Failed to load UI file: {current_zVaFile}")
            return None
        
        # Extract the target block dict - with fallback chain
        target_block_dict = self._resolve_delta_target_block(
            target_block_name,
            raw_zFile,
            current_zVaFile,
            walker
        )
        
        if not target_block_dict:
            self.logger.error(f"[NavigationHandler] Failed to resolve block '{target_block_name}'")
            return None
        
        # Update session and create breadcrumb scope
        walker.session["zBlock"] = target_block_name
        self._initialize_delta_breadcrumb_scope(target_block_name, current_zVaFile, walker)
        
        # Navigate to the target block
        result = walker.execute_loop(items_dict=target_block_dict)
        return result
    
    # ========================================================================
    # PRIVATE HELPERS - zDelta Resolution
    # ========================================================================
    
    def _resolve_delta_target_block(
        self,
        target_block_name: str,
        raw_zFile: Dict[str, Any],
        current_zVaFile: str,
        walker: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve target block for zDelta navigation with fallback.
        
        FALLBACK CHAIN:
        1. Try finding block in current file
        2. If not found, try loading {blockName}.yaml from same directory
        
        Args:
            target_block_name: Name of target block
            raw_zFile: Current UI file content
            current_zVaFile: Current zVaFile path
            walker: Walker instance (for loader access)
        
        Returns:
            Target block dict, or None if not found
        
        Example:
            # Block in current file
            block = _resolve_delta_target_block("Settings", raw_file, current_file, walker)
            
            # Block in separate file (auto-discovered)
            block = _resolve_delta_target_block("About", raw_file, current_file, walker)
        """
        # Try current file first
        if target_block_name in raw_zFile:
            self.logger.framework.debug(
                f"[NavigationHandler] zDelta: Block '{target_block_name}' found in current file"
            )
            return raw_zFile[target_block_name]
        
        # FALLBACK: Try loading zUI.{blockName}.yaml from same directory
        fallback_zPath = self._construct_fallback_zpath(target_block_name, current_zVaFile)
        
        self.logger.framework.debug(
            f"[NavigationHandler] zDelta: Block '{target_block_name}' not in current file, "
            f"trying fallback zPath: {fallback_zPath}"
        )
        
        # Try loading the fallback file
        try:
            fallback_zFile = walker.loader.handle(fallback_zPath)
        except Exception as e:
            self.logger.debug(f"[NavigationHandler] zDelta: Fallback failed: {e}")
            fallback_zFile = None
        
        if fallback_zFile and isinstance(fallback_zFile, dict):
            # SUCCESS: Fallback file loaded
            self.logger.info(
                f"[NavigationHandler] ✓ zDelta: Auto-discovered block '{target_block_name}' "
                f"from separate file: {fallback_zPath}"
            )
            return fallback_zFile
        else:
            # FAILED: Neither current file nor fallback file has the block
            self.logger.error(
                f"[NavigationHandler] Block '{target_block_name}' not found:\n"
                f"  - Not in current file: {current_zVaFile}\n"
                f"  - Fallback zPath not found: {fallback_zPath}"
            )
            return None
    
    def _construct_fallback_zpath(
        self,
        target_block_name: str,
        current_zVaFile: str
    ) -> str:
        """
        Construct fallback zPath for zDelta auto-discovery.
        
        File naming: zUI.{blockName}.yaml -> zPath = "@.UI.zUI.{blockName}"
        
        Args:
            target_block_name: Name of target block
            current_zVaFile: Current zVaFile path
        
        Returns:
            Fallback zPath string
        
        Example:
            current = "@.UI.zUI.index" -> fallback = "@.UI.zUI.zAbout"
            current = "@.UI.zUI.Settings" -> fallback = "@.UI.zUI.Profile"
        """
        if current_zVaFile.startswith("@"):
            # Parse current zPath to get folder
            path_parts = current_zVaFile.split(".")
            # Replace the last part with target block name
            fallback_path_parts = path_parts[:-1] + [target_block_name]
            return ".".join(fallback_path_parts)
        else:
            # Absolute path - construct relative to current file
            return f"@.UI.zUI.{target_block_name}"
    
    def _initialize_delta_breadcrumb_scope(
        self,
        target_block_name: str,
        current_zVaFile: str,
        walker: Any
    ) -> None:
        """
        Initialize new breadcrumb scope for zDelta target block.
        
        Creates new node in zCrumbs with full breadcrumb path: zVaFile.zBlock
        
        Args:
            target_block_name: Name of target block
            current_zVaFile: Current zVaFile path
            walker: Walker instance (modifies walker.session in-place)
        
        Notes:
            - Modifies walker.session["zCrumbs"] in-place
            - Creates empty breadcrumb trail for new scope
        
        Example:
            _initialize_delta_breadcrumb_scope("Settings", "@.UI.zUI.index", walker)
            # Creates: walker.session["zCrumbs"]["@.UI.zUI.index.Settings"] = []
        """
        # Construct full breadcrumb path
        zVaFile = walker.session.get("zVaFile") or current_zVaFile
        full_crumb_path = f"{zVaFile}.{target_block_name}" if zVaFile else target_block_name
        
        # Initialize empty breadcrumb trail for the new scope
        if "zCrumbs" not in walker.session:
            walker.session["zCrumbs"] = {}
        walker.session["zCrumbs"][full_crumb_path] = []
        
        self.logger.framework.debug(f"[NavigationHandler] zDelta: Created new breadcrumb scope: {full_crumb_path}")
    
    # ========================================================================
    # PRIVATE HELPERS - Validation & Display
    # ========================================================================
    
    def _check_walker(self, walker: Optional[Any], command_name: str) -> bool:
        """
        Validate walker instance for navigation commands.
        
        Args:
            walker: Walker instance to validate (can be None)
            command_name: Name of command requiring walker (for error message)
        
        Returns:
            True if walker is valid (not None), False otherwise
        
        Example:
            if not self._check_walker(walker, "zLink"):
                return None
        
        Notes:
            - Logs warning if walker is None
            - Calling code should return None if validation fails
        """
        if not walker:
            self.logger.warning(f"[NavigationHandler] {command_name} requires walker instance")
            return False
        return True
    
    def _display_handler(self, label: str) -> None:
        """
        Display handler label with consistent styling.
        
        Args:
            label: Handler label to display (from dispatch_constants)
        
        Notes:
            - Uses zDisplay.zDeclare for consistent styling
            - Style is always "single" for handler labels
            - Color comes from parent dispatch instance (via self.display)
        """
        if self.display:
            # Get color from display instance (set by parent dispatcher)
            color = getattr(self.display, 'mycolor', None)
            if color:
                self.display.zDeclare(
                    label,
                    color=color,
                    indent=_DEFAULT_INDENT_HANDLER,
                    style=_DEFAULT_STYLE_SINGLE
                )
