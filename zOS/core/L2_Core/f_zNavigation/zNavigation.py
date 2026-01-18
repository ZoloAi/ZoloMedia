# zCLI/subsystems/zNavigation/zNavigation.py

"""
zNavigation - Unified Navigation System Subsystem for zCLI.

This module provides the zNavigation facade class, which serves as the primary
interface for navigation operations in zCLI. It orchestrates four specialized
components to deliver menu creation, breadcrumb management, navigation state
tracking, and inter-file linking.

Facade Pattern
--------------
The zNavigation class implements the Facade pattern, providing a simplified
interface to the complex navigation subsystem. It delegates all operations to
specialized components while maintaining a clean, consistent public API.

**Key Design Principles:**
- Pure delegation (no business logic in facade)
- Clean public API for external clients
- Component encapsulation (internal structure hidden)
- Backward compatibility (standalone functions for Walker)

Component Architecture
----------------------
The zNavigation facade orchestrates four specialized components:

1. **MenuSystem** (navigation_menu_system.py)
   - Menu creation and display (create, select)
   - Orchestrates builder, renderer, and interaction components
   - Supports static, dynamic, and function-based menus
   - Integration: Called by zDispatch for * (menu) modifier

2. **Breadcrumbs** (navigation_breadcrumbs.py)
   - Navigation trail management (zCrumbs)
   - "Back" functionality (zBack)
   - Session breadcrumb storage and retrieval
   - UI file reloading based on breadcrumb state

3. **Navigation** (navigation_state.py)
   - Current navigation location tracking
   - Navigation history management (FIFO overflow)
   - Session state storage with timestamps
   - Location metadata management

4. **Linking** (navigation_linking.py)
   - Inter-file linking (zLink expressions)
   - RBAC permission checking for links
   - Session context updates (zVaFolder, zVaFile, zBlock)
   - Integration: zParser (expression eval), zLoader (file loading)

Public API
----------
The facade exposes 10 methods organized by functional area:

**Menu System (2 methods):**
- create(options, title, allow_back, walker) → str
- select(options, prompt, walker) → str

**Breadcrumbs (2 methods):**
- handle_zCrumbs(zBlock, zKey, walker) → Any
- handle_zBack(show_banner, walker) → str

**Navigation State (3 methods):**
- navigate_to(target, context) → Dict
- get_current_location() → Dict
- get_navigation_history() → List

**Inter-file Linking (1 method):**
- handle_zLink(zHorizontal, walker) → str

Backward Compatibility
----------------------
Two standalone functions maintain backward compatibility with Walker:

- handle_zLink(zHorizontal, walker) → Delegates to facade
- handle_zCrumbs(zBlock, zKey, walker) → Delegates to facade

These functions ensure legacy code continues to work while encouraging
migration to the modern facade API.

Layer Position
--------------
Layer 1, Position 4 (zNavigation) - Facade

Integration
-----------
- Parent: zCLI core (zCLI.py)
- Used By: zDispatch (menu system), zWalker (navigation), external clients
- Uses: MenuSystem, Breadcrumbs, Navigation, Linking components

Usage Examples
--------------
Via facade (recommended)::

    # Initialize zCLI (done automatically)
    zcli = zCLI()
    
    # Create navigation menu
    choice = zcli.navigation.create(
        ["Settings", "Profile", "Logout"],
        title="Main Menu",
        allow_back=True,
        walker=walker
    )
    
    # Handle breadcrumb trail
    zcli.navigation.handle_zCrumbs("menu_block", "option_key", walker)
    
    # Navigate to location
    zcli.navigation.navigate_to("users.menu.list_users")
    
    # Handle inter-file linking
    result = zcli.navigation.handle_zLink("zLink(path.to.file.block)", walker)

Via standalone functions (backward compatibility)::

    # Legacy Walker integration
    from zOS.L2_Core.f_zNavigation import handle_zLink, handle_zCrumbs
    
    # These delegate to the facade internally
    result = handle_zLink("zLink(path)", walker)
    handle_zCrumbs("block", "key", walker)

See Also
--------
- navigation_modules/ : Component implementations
- zDispatch : Menu system integration (* modifier)
- zWalker : Navigation orchestration
"""

from zOS import Any, Dict, List, Optional, Tuple, Union

from .navigation_modules.navigation_menu_system import MenuSystem
from .navigation_modules.navigation_breadcrumbs import Breadcrumbs
from .navigation_modules.navigation_state import Navigation
from .navigation_modules.navigation_linking import Linking
from .navigation_modules.navigation_constants import (
    COLOR_MENU,
    _DISPLAY_MSG_READY,
    _DISPLAY_INDENT_INIT,
    _DISPLAY_STYLE_INIT,
    _ERROR_MSG_NO_ZCLI,
    _ERROR_MSG_NO_WALKER,
    _LOG_MSG_READY,
)


# ============================================================================
# zNavigation Facade Class
# ============================================================================

class zNavigation:
    """
    Unified navigation system facade for zCLI.
    
    Provides a clean, consistent interface to the navigation subsystem by
    orchestrating four specialized components: MenuSystem, Breadcrumbs,
    Navigation, and Linking. Implements the Facade pattern with pure
    delegation (no business logic in facade).
    
    Attributes
    ----------
    zcli : Any
        Reference to zCLI core instance
    session : Dict
        Session dictionary for state management
    logger : Any
        Logger instance for navigation operations
    mycolor : str
        Display color for navigation messages (default: "MENU")
    menu : MenuSystem
        Menu creation and interaction component
    breadcrumbs : Breadcrumbs
        Navigation trail management component
    navigation : Navigation
        Navigation state and history component
    linking : Linking
        Inter-file linking component
    
    Methods
    -------
    create(options, title, allow_back, walker)
        Create and display a menu, return user choice
    select(options, prompt, walker)
        Simple selection menu without complex navigation
    handle_zCrumbs(zBlock, zKey, walker)
        Handle breadcrumb trail management
    handle_zBack(show_banner, walker)
        Handle back navigation
    navigate_to(target, context)
        Navigate to a specific target
    get_current_location()
        Get current navigation location
    get_navigation_history()
        Get navigation history
    handle_zLink(zHorizontal, walker)
        Handle inter-file linking
    
    Examples
    --------
    Create navigation menu::
    
        nav = zNavigation(zcli)
        choice = nav.create(
            ["Settings", "Profile", "Logout"],
            title="Main Menu",
            walker=walker
        )
    
    Handle breadcrumbs::
    
        nav.handle_zCrumbs("menu_block", "option_key", walker)
        result = nav.handle_zBack(show_banner=True, walker=walker)
    
    Navigate to location::
    
        nav.navigate_to("users.menu.list_users")
        location = nav.get_current_location()
    
    Integration
    -----------
    - Initialized by: zCLI.py core
    - Used by: zDispatch, zWalker, external clients
    - Delegates to: MenuSystem, Breadcrumbs, Navigation, Linking
    """

    # Class-level type declarations
    zcli: Any  # zCLI core instance
    session: Dict[str, Any]  # Session dictionary
    logger: Any  # Logger instance
    mycolor: str  # Display color
    menu: MenuSystem  # Menu system component
    breadcrumbs: Breadcrumbs  # Breadcrumbs component
    navigation: Navigation  # Navigation component
    linking: Linking  # Linking component

    def __init__(self, zcli: Any) -> None:
        """
        Initialize zNavigation subsystem with component orchestration.
        
        Args
        ----
        zcli : Any
            zCLI core instance (required)
        
        Raises
        ------
        ValueError
            If zcli parameter is None
        
        Notes
        -----
        Initialization sequence:
        1. Validate zcli parameter
        2. Store references (zcli, session, logger)
        3. Set display color (backward compatibility)
        4. Initialize 4 specialized components
        5. Display ready message
        6. Log initialization
        """
        if zcli is None:
            raise ValueError(_ERROR_MSG_NO_ZCLI)

        self.zcli = zcli
        self.session = zcli.session
        self.logger = zcli.logger
        self.mycolor = COLOR_MENU  # Keep MENU color for backward compatibility

        # Initialize navigation modules (component composition)
        self.menu = MenuSystem(self)
        self.breadcrumbs = Breadcrumbs(self)
        self.navigation = Navigation(self)
        self.linking = Linking(self)

        # Display ready message using modern zDisplay
        self.zcli.display.zDeclare(
            _DISPLAY_MSG_READY,
            color=self.mycolor,
            indent=_DISPLAY_INDENT_INIT,
            style=_DISPLAY_STYLE_INIT
        )

        self.logger.framework.debug(_LOG_MSG_READY)
        
        # Load global navbar from environment (.zEnv)
        self._global_navbar = self._load_global_navbar()

    def _load_global_navbar(self) -> Optional[List[Any]]:
        """
        Load global navigation bar from environment configuration.
        
        Delegates to zConfig for loading zEnv YAML files - this method only reads from os.environ.
        zConfig.load_dotenv() loads zEnv.base.yaml + zEnv.{environment}.yaml and injects into os.environ.
        
        Supports multiple formats (priority order):
        1. os.environ["ZNAVBAR"] (from zConfig's zEnv YAML loading) - THE zCLI WAY
        2. Legacy .zEnv file parsing (backward compatibility only)
        3. Legacy comma-separated: ZNAVBAR=zVaF,zAbout,zLogin
        
        Returns:
            Optional[List[Any]]: List of navbar items (strings or dicts with RBAC) or None
        
        Examples:
            YAML dict format (recommended, loaded by zConfig):
                Input (zEnv.base.yaml):
                    ZNAVBAR:
                      zVaF:
                      zAccount:
                        zRBAC:
                          require_role: [zAdmin]
                Output: ["zVaF", {"zAccount": {"zRBAC": {"require_role": ["zAdmin"]}}}]
            
            Legacy format:
                ZNAVBAR=zVaF,zAbout,zRegister,zLogin
                Returns: ["zVaF", "zAbout", "zRegister", "zLogin"]
        
        Notes:
            - Loaded once during initialization
            - Cached in self._global_navbar (unfiltered)
            - RBAC filtering applied later in resolve_navbar()
            - zEnv YAML files are loaded by zConfig (config_paths.load_dotenv) and injected into os.environ
            - This method does NOT parse YAML files directly - that's zConfig's responsibility
        """
        import os
        import json
        from pathlib import Path
        
        # Priority 1: Check os.environ (from zConfig's zEnv YAML loading - THE zCLI WAY)
        navbar_env = os.getenv("ZNAVBAR", "").strip()
        
        # Priority 2: Fallback to legacy .zEnv file (backward compatibility only)
        # Note: This is only for legacy setups. Modern setups use zEnv.*.yaml loaded by zConfig.
        if not navbar_env:
            legacy_env_path = Path(self.zcli.config.paths.workspace_dir) / ".zEnv"
            if legacy_env_path.exists():
                try:
                    env_data = self.zcli.zparser.parse_file_by_path(str(legacy_env_path))
                    if env_data and "ZNAVBAR" in env_data:
                        navbar_raw = env_data["ZNAVBAR"]
                        if isinstance(navbar_raw, dict):
                            navbar_items = self._parse_navbar_dict(navbar_raw)
                            if navbar_items:
                                self.logger.framework.info(f"[zNavigation] ✅ Loaded navbar from legacy .zEnv ({len(navbar_items)} items)")
                                return navbar_items
                        elif isinstance(navbar_raw, str):
                            navbar_env = navbar_raw
                except Exception as e:
                    self.logger.framework.debug(f"[zNavigation] Failed to parse legacy .zEnv: {e}")
            
            if not navbar_env:
                self.logger.framework.debug("[zNavigation] No global navbar defined in ZNAVBAR env var (zConfig should load from zEnv.*.yaml)")
                return None
        
        # Parse navbar_env (from os.environ or legacy .zEnv)
        # Check if it's JSON dict format (starts with '{') - FROM zEnv YAML flattening
        if navbar_env.startswith("{"):
            # zEnv flattened dict: Parse as JSON dict
            try:
                navbar_raw = json.loads(navbar_env)
                
                if not isinstance(navbar_raw, dict):
                    self.logger.framework.warning(f"[zNavigation] ZNAVBAR JSON is not a dict: {type(navbar_raw)}")
                    return None
                
                # Parse dict format using helper method
                navbar_items = self._parse_navbar_dict(navbar_raw)
                
                if navbar_items:
                    self.logger.framework.info(f"[zNavigation] ✅ Loaded navbar from os.environ (zEnv YAML) ({len(navbar_items)} items)")
                    return navbar_items
            
            except json.JSONDecodeError as e:
                self.logger.framework.error(f"[zNavigation] Failed to parse ZNAVBAR JSON dict: {e}")
                return None
            except Exception as e:
                self.logger.framework.error(f"[zNavigation] Error processing ZNAVBAR dict: {e}")
                return None
        
        # Check if it's JSON array format (starts with '[') - LEGACY
        elif navbar_env.startswith("["):
            # Enhanced JSON format: Parse as JSON
            try:
                navbar_raw = json.loads(navbar_env)
                
                if not isinstance(navbar_raw, list):
                    self.logger.framework.warning(f"[zNavigation] ZNAVBAR JSON is not an array: {type(navbar_raw)}")
                    return None
                
                # Transform JSON format to internal format
                # Input: [{"item": "zVaF"}, {"item": "^logout", "zRBAC": {...}}]
                # Output: ["zVaF", {"^logout": {"zRBAC": {...}}}]
                navbar_items = []
                for entry in navbar_raw:
                    if not isinstance(entry, dict):
                        self.logger.framework.warning(f"[zNavigation] Invalid navbar entry (not a dict): {entry}")
                        continue
                    
                    item_name = entry.get("item")
                    if not item_name:
                        self.logger.framework.warning(f"[zNavigation] Navbar entry missing 'item' key: {entry}")
                        continue
                    
                    # If entry has zRBAC, convert to dict format: {item_name: {zRBAC: ...}}
                    if "zRBAC" in entry:
                        navbar_items.append({item_name: {"zRBAC": entry["zRBAC"]}})
                    else:
                        # Simple string item (public)
                        navbar_items.append(item_name)
                
                if navbar_items:
                    self.logger.framework.info(f"[zNavigation] Loaded enhanced navbar (JSON) with {len(navbar_items)} items")
                    return navbar_items
            
            except json.JSONDecodeError as e:
                self.logger.framework.error(f"[zNavigation] Failed to parse ZNAVBAR JSON: {e}")
                return None
            except Exception as e:
                self.logger.framework.error(f"[zNavigation] Error processing ZNAVBAR: {e}")
                return None
        
        else:
            # Legacy format: Split by comma
            navbar_items = [item.strip() for item in navbar_env.split(",") if item.strip()]
            
            if navbar_items:
                self.logger.framework.info(f"[zNavigation] Loaded legacy navbar (comma-separated): {navbar_items}")
                return navbar_items
        
        return None

    def _parse_navbar_dict(self, navbar_raw: Dict[str, Any]) -> List[Any]:
        """
        Parse navbar dict format into internal format.
        
        Args:
            navbar_raw: Dict with item names as keys and optional metadata as values
                Example: {"zVaF": None, "zAccount": {"zRBAC": {"require_role": ["zAdmin"]}}}
                Example with sub-items: {"zProducts": {"zSub": ["zCLI", "zBifrost"]}}
        
        Returns:
            List of navbar items (strings or dicts with RBAC and/or sub-items)
                Example: ["zVaF", {"zAccount": {"zRBAC": {"require_role": ["zAdmin"]}}}]
                Example with sub-items: [{"zProducts": {"zSub": ["zCLI", "zBifrost"]}}]
        """
        navbar_items = []
        
        for item_name, item_config in navbar_raw.items():
            # If item has metadata (zRBAC or zSub), include it
            if item_config and isinstance(item_config, dict):
                metadata = {}
                if "zRBAC" in item_config:
                    metadata["zRBAC"] = item_config["zRBAC"]
                if "zSub" in item_config:
                    metadata["zSub"] = item_config["zSub"]
                
                if metadata:
                    navbar_items.append({item_name: metadata})
                else:
                    # Config dict but no recognized metadata
                    navbar_items.append(item_name)
            else:
                # Simple string item (public, no RBAC, no sub-items)
                navbar_items.append(item_name)
        
        return navbar_items

    def _filter_navbar_byzRBAC(self, navbar_items: List[Any]) -> List[Union[str, Dict[str, Any]]]:
        """
        Filter navbar items based on RBAC rules and current user authentication state.
        
        This is the "Terminal First" implementation - filtering happens in the backend
        (zLoader/zNavigation layer) ensuring consistent behavior across Terminal and Bifrost.
        
        Filtering Rules:
            1. String items (no zRBAC) → Always visible (public)
            2. Dict items with zRBAC:
                - zGuest: true → Only visible if NOT authenticated
                - authenticated: true → Only visible if authenticated
                - authenticated: false → Only visible if NOT authenticated (same as zGuest)
                - require_role: "role" → Only visible if user has that role
            3. Dict items with zSub → Preserved in output for hierarchical navigation
            4. Invalid items → Filtered out (logged as warnings)
        
        Args:
            navbar_items: Raw navbar items (strings or dicts with RBAC metadata and/or sub-items)
        
        Returns:
            List[Union[str, Dict]]: Filtered list of navbar items (strings or dicts with zSub)
        
        Examples:
            Input (not authenticated):
                ["zVaF", {"^logout": {"zRBAC": {"authenticated": true}}}, {"^zLogin": {"zRBAC": {"authenticated": false}}}]
            Output:
                ["zVaF", "^zLogin"]
            
            Input with sub-items:
                ["zVaF", {"zProducts": {"zSub": ["zCLI", "zBifrost"]}}]
            Output:
                ["zVaF", {"zProducts": {"zSub": ["zCLI", "zBifrost"]}}]
            
            Input (authenticated as zAdmin):
                ["zVaF", {"zAccount": {"zRBAC": {"require_role": "zAdmin"}}}, {"^zLogin": {"zRBAC": {"authenticated": false}}}]
            Output:
                ["zVaF", "zAccount"]
        
        Notes:
            - Uses zcli.auth.is_authenticated() for auth checks
            - Preserves zSub metadata for hierarchical menus
            - Uses zcli.auth.has_role() for role checks
            - Returns clean item names (without zRBAC metadata)
            - Logs filtered items at DEBUG level
        """
        if not navbar_items:
            return []
        
        filtered = []
        is_authenticated = self.zcli.auth.is_authenticated() if hasattr(self.zcli, 'auth') else False
        
        for item in navbar_items:
            # Case 1: Simple string item (no RBAC) - always visible
            if isinstance(item, str):
                filtered.append(item)
                continue
            
            # Case 2: Dict item with potential RBAC metadata and/or sub-items
            if isinstance(item, dict):
                # Extract the item name (key) and metadata (value)
                if len(item) != 1:
                    self.logger.framework.warning(f"[zNavigation] Invalid navbar item dict (must have exactly 1 key): {item}")
                    continue
                
                item_name = list(item.keys())[0]
                item_metadata = item[item_name]
                
                # Extract sub-items if present
                sub_items = item_metadata.get("zSub") if isinstance(item_metadata, dict) else None
                
                # If no metadata or no zRBAC, treat as public
                if not isinstance(item_metadata, dict) or "zRBAC" not in item_metadata:
                    # If has sub-items, include them in output (preserve metadata wrapper)
                    if sub_items:
                        filtered.append({item_name: {"zSub": sub_items}})
                    else:
                        filtered.append(item_name)
                    continue
                
                # Extract RBAC rules
                rbac_rules = item_metadata.get("zRBAC", {})
                
                # Check zGuest (guest-only - must NOT be authenticated)
                if rbac_rules.get("zGuest"):
                    if not is_authenticated:
                        filtered.append({item_name: {"zSub": sub_items}} if sub_items else item_name)
                        self.logger.framework.debug(f"[zNavigation] Navbar item '{item_name}' visible (zGuest: user not authenticated)")
                    else:
                        self.logger.framework.debug(f"[zNavigation] Navbar item '{item_name}' hidden (zGuest: user is authenticated)")
                    continue
                
                # Check authenticated (must be authenticated OR must NOT be authenticated)
                if "authenticated" in rbac_rules:
                    auth_required = rbac_rules.get("authenticated")
                    if auth_required is True:
                        # authenticated: true - must be authenticated
                        if is_authenticated:
                            filtered.append({item_name: {"zSub": sub_items}} if sub_items else item_name)
                            self.logger.framework.debug(f"[zNavigation] Navbar item '{item_name}' visible (authenticated: true)")
                        else:
                            self.logger.framework.debug(f"[zNavigation] Navbar item '{item_name}' hidden (not authenticated)")
                    elif auth_required is False:
                        # authenticated: false - must NOT be authenticated (guest-only)
                        if not is_authenticated:
                            filtered.append({item_name: {"zSub": sub_items}} if sub_items else item_name)
                            self.logger.framework.debug(f"[zNavigation] Navbar item '{item_name}' visible (authenticated: false, user is guest)")
                        else:
                            self.logger.framework.debug(f"[zNavigation] Navbar item '{item_name}' hidden (authenticated: false, user is authenticated)")
                    continue
                
                # Check require_role (must have specific role)
                required_role = rbac_rules.get("require_role")
                if required_role:
                    if is_authenticated and hasattr(self.zcli, 'auth') and self.zcli.auth.has_role(required_role):
                        filtered.append({item_name: {"zSub": sub_items}} if sub_items else item_name)
                        self.logger.framework.debug(f"[zNavigation] Navbar item '{item_name}' visible (has role: {required_role})")
                    else:
                        self.logger.framework.debug(f"[zNavigation] Navbar item '{item_name}' hidden (missing role: {required_role})")
                    continue
                
                # No RBAC rules matched - treat as public
                filtered.append({item_name: {"zSub": sub_items}} if sub_items else item_name)
                continue
            
            # Case 3: Invalid item type
            self.logger.framework.warning(f"[zNavigation] Invalid navbar item type: {type(item)} ({item})")
        
        self.logger.framework.debug(f"[zNavigation] Filtered navbar: {len(navbar_items)} → {len(filtered)} items")
        return filtered

    def resolve_navbar(self, raw_zFile: Dict[str, Any], route_meta: Optional[Dict[str, Any]] = None) -> Optional[List[str]]:
        """
        Resolve navigation bar for a given zVaFile based on meta.zNavBar with route fallback.
        
        Resolution Logic (Priority Chain):
            1. If zVaFile meta.zNavBar is a list → return it (highest priority: local override)
            2. If zVaFile meta.zNavBar: true → return global navbar from .zEnv
            3. If zVaFile meta.zNavBar is false/missing AND route meta.zNavBar: true → return global navbar (lowest priority: route fallback)
            4. Otherwise → return None (no navbar)
        
        Args:
            raw_zFile: Parsed YAML dictionary from zVaFile
            route_meta: Optional route metadata from zServer.routes.yaml (for fallback)
        
        Returns:
            Optional[List[str]]: Resolved navbar items or None
        
        Examples:
            # Priority 1: Local override (custom navbar)
            zVaFile meta.zNavBar: ["Custom", "Items"]
            Returns: ["Custom", "Items"]
            
            # Priority 2: zVaFile opt-in to global navbar
            zVaFile meta.zNavBar: true
            Returns: ["zVaF", "zAbout", "zRegister", "zLogin"] (from .zEnv)
            
            # Priority 3: Route fallback (if zVaFile has no navbar)
            zVaFile meta.zNavBar: missing/false
            Route meta.zNavBar: true
            Returns: ["zVaF", "zAbout", "zRegister", "zLogin"] (from .zEnv)
            
            # No navbar
            All meta.zNavBar: false/missing
            Returns: None
        
        Notes:
            - Local navbar always wins (DRY principle with override)
            - Route meta provides fallback for files without navbar
            - zServer routes can enforce navbar for all pages via meta.zNavBar: true
        """
        if not raw_zFile or not isinstance(raw_zFile, dict):
            return None
        
        # Get zVaFile zMeta section
        meta_section = raw_zFile.get("zMeta", {})
        if not isinstance(meta_section, dict):
            meta_section = {}
        
        # Get zNavBar value from zVaFile
        navbar_value = meta_section.get("zNavBar")
        
        # Normalize string 'true'/'false' to boolean (for .zolo file compatibility)
        if isinstance(navbar_value, str):
            navbar_value = navbar_value.lower() == 'true'
        
        # Priority 1: Local override (list of items)
        if isinstance(navbar_value, list):
            if len(navbar_value) > 0:
                self.logger.framework.debug(f"[zNavigation] Using local navbar (priority 1): {navbar_value}")
                # Return raw (unfiltered) navbar - filtering happens dynamically in zDispatch
                return navbar_value
            else:
                self.logger.framework.debug("[zNavigation] Empty local navbar, skipping")
                return None
        
        # Priority 2: zVaFile opt-in to global navbar (true)
        if navbar_value is True:
            if self._global_navbar:
                self.logger.framework.debug(f"[zNavigation] Injecting global navbar from zVaFile (priority 2): {self._global_navbar}")
                # Return raw (unfiltered) navbar - filtering happens dynamically in zDispatch
                return self._global_navbar
            else:
                self.logger.framework.warning("[zNavigation] meta.zNavBar: true but no global navbar defined in .zEnv")
                return None
        
        # Priority 3: Route fallback (if zVaFile has no navbar setting)
        # Check if route metadata has zNavBar: true
        if route_meta and isinstance(route_meta, dict):
            route_navbar_value = route_meta.get("zNavBar")
            
            # Normalize string 'true'/'false' to boolean (for .zolo file compatibility)
            if isinstance(route_navbar_value, str):
                route_navbar_value = route_navbar_value.lower() == 'true'
            
            if route_navbar_value is True:
                if self._global_navbar:
                    self.logger.framework.debug(f"[zNavigation] Injecting global navbar from route fallback (priority 3): {self._global_navbar}")
                    # Return raw (unfiltered) navbar - filtering happens dynamically in zDispatch
                    return self._global_navbar
                else:
                    self.logger.framework.warning("[zNavigation] Route meta.zNavBar: true but no global navbar defined in .zEnv")
                    return None
            elif isinstance(route_navbar_value, list) and len(route_navbar_value) > 0:
                self.logger.framework.debug(f"[zNavigation] Using route navbar fallback (priority 3): {route_navbar_value}")
                # Return raw (unfiltered) navbar - filtering happens dynamically in zDispatch
                return route_navbar_value
        
        # Case 4: No navbar (false, None, or missing everywhere)
        self.logger.framework.debug("[zNavigation] No navbar configured (zVaFile or route)")
        return None

    # ========================================================================
    # Menu System Methods
    # ========================================================================

    def create(
        self,
        options: Any,
        title: Optional[str] = None,
        allow_back: bool = True,
        walker: Optional[Any] = None
    ) -> str:
        """
        Create and display a menu, return user choice.
        
        Delegates to MenuSystem for full-featured menu creation with navigation
        support. Integrates with breadcrumb system and supports "Back" option.
        
        Args
        ----
        options : Any
            List of menu options or dict with options
        title : Optional[str], default=None
            Optional menu title
        allow_back : bool, default=True
            Whether to add "Back" option
        walker : Optional[Any], default=None
            Optional walker instance for context
        
        Returns
        -------
        str
            Selected option string (or "zBack" if back chosen)
        
        Examples
        --------
        Basic menu::
        
            choice = nav.create(
                ["Settings", "Profile", "Logout"],
                title="Main Menu",
                walker=walker
            )
        
        Anchor menu (no back)::
        
            choice = nav.create(
                ["Yes", "No"],
                title="Confirm",
                allow_back=False,
                walker=walker
            )
        
        Notes
        -----
        - Called by zDispatch for * (menu) modifier
        - Delegates to MenuSystem.create()
        - Mode-agnostic (Terminal/Bifrost)
        """
        return self.menu.create(options, title=title, allow_back=allow_back, walker=walker)

    def select(
        self,
        options: List[str],
        prompt: str = "Select option",
        walker: Optional[Any] = None
    ) -> str:
        """
        Simple selection menu without complex navigation.
        
        Delegates to MenuSystem for simplified menu without "Back" option or
        navigation features. Used for quick selections.
        
        Args
        ----
        options : List[str]
            List of options to select from
        prompt : str, default="Select option"
            Prompt text to display
        walker : Optional[Any], default=None
            Optional walker instance for context
        
        Returns
        -------
        str
            Selected option string
        
        Examples
        --------
        Color selection::
        
            color = nav.select(
                ["Red", "Green", "Blue"],
                prompt="Choose a color",
                walker=walker
            )
        
        Quick yes/no::
        
            answer = nav.select(["Yes", "No"], walker=walker)
        
        Notes
        -----
        - No "Back" option (hardcoded allow_back=False)
        - Delegates to MenuSystem.select()
        - Simpler display than create()
        """
        return self.menu.select(options, prompt=prompt, walker=walker)

    # ========================================================================
    # Breadcrumbs Methods
    # ========================================================================

    def handle_zCrumbs(
        self,
        zKey: str,
        walker: Optional[Any] = None,
        operation: str = "APPEND"
    ) -> Any:
        """
        Handle breadcrumb trail management.
        
        Delegates to Breadcrumbs for adding navigation crumbs to session,
        enabling "Back" functionality and navigation trail display.
        Self-aware: reads session state to determine active block path.
        
        Args
        ----
        zKey : str
            Key identifier for breadcrumb
        walker : Optional[Any], default=None
            Optional walker instance for context
        operation : str, default="APPEND"
            Breadcrumb operation: "APPEND" or "REPLACE"
        
        Returns
        -------
        Any
            Breadcrumb operation result
        
        Examples
        --------
        Add breadcrumb::
        
            nav.handle_zCrumbs("users_menu", "list_users_key", walker)
        
        Notes
        -----
        - Stores breadcrumb in session (zCrumbs key)
        - Enables zBack functionality
        - Delegates to Breadcrumbs.handle_zCrumbs()
        - Breadcrumbs reads session state to determine block path
        - Supports APPEND (default) and REPLACE operations
        """
        return self.breadcrumbs.handle_zCrumbs(zKey, walker=walker, operation=operation)

    def handle_zBack(
        self,
        show_banner: bool = True,
        walker: Optional[Any] = None
    ) -> Tuple[Dict[str, Any], List[str], Optional[str]]:
        """
        Handle back navigation.
        
        Delegates to Breadcrumbs for navigating back in the breadcrumb trail,
        reloading the previous UI file and restoring navigation state.
        
        Args
        ----
        show_banner : bool, default=True
            Whether to display "zBack" banner
        walker : Optional[Any], default=None
            Optional walker instance for context
        
        Returns
        -------
        Tuple[Dict[str, Any], List[str], Optional[str]]
            A tuple containing:
            - block_dict: Dict of the active block's content
            - block_keys: List of all keys in the active block
            - start_key: The key to resume from (or None if trail is empty)
        
        Examples
        --------
        Navigate back with banner::
        
            result = nav.handle_zBack(show_banner=True, walker=walker)
        
        Silent back navigation::
        
            result = nav.handle_zBack(show_banner=False, walker=walker)
        
        Notes
        -----
        - Pops breadcrumb from session trail
        - Reloads previous UI file
        - Delegates to Breadcrumbs.handle_zBack()
        """
        return self.breadcrumbs.handle_zBack(show_banner=show_banner, walker=walker)

    # ========================================================================
    # Navigation Methods
    # ========================================================================

    def navigate_to(
        self,
        target: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Navigate to a specific target.
        
        Delegates to Navigation for updating current location and adding to
        navigation history with optional context metadata.
        
        Args
        ----
        target : str
            Navigation target (file, block, key, etc.)
        context : Optional[Dict[str, Any]], default=None
            Optional navigation context metadata
        
        Returns
        -------
        Dict[str, Any]
            Navigation result with status and target
        
        Examples
        --------
        Navigate to file/block::
        
            result = nav.navigate_to("users.menu.list_users")
        
        Navigate with context::
        
            result = nav.navigate_to(
                "users.detail",
                context={"user_id": 123}
            )
        
        Notes
        -----
        - Updates session current_location
        - Adds to navigation_history (FIFO overflow)
        - Delegates to Navigation.navigate_to()
        """
        return self.navigation.navigate_to(target, context=context)

    def get_current_location(self) -> Dict[str, Any]:
        """
        Get current navigation location.
        
        Delegates to Navigation for retrieving current location from session,
        including target and context metadata.
        
        Returns
        -------
        Dict[str, Any]
            Current location dict with target, context, timestamp
        
        Examples
        --------
        Get current location::
        
            location = nav.get_current_location()
            print(f"Current: {location['target']}")
        
        Notes
        -----
        - Reads from session (current_location key)
        - Returns empty dict if no location set
        - Delegates to Navigation.get_current_location()
        """
        return self.navigation.get_current_location()

    def get_navigation_history(self) -> List[Dict[str, Any]]:
        """
        Get navigation history.
        
        Delegates to Navigation for retrieving full navigation history from
        session, limited to last 50 entries (FIFO overflow).
        
        Returns
        -------
        List[Dict[str, Any]]
            List of navigation history entries
        
        Examples
        --------
        Get history::
        
            history = nav.get_navigation_history()
            for entry in history:
                print(f"Visited: {entry['target']}")
        
        Notes
        -----
        - Reads from session (navigation_history key)
        - Limited to 50 entries (FIFO overflow)
        - Delegates to Navigation.get_navigation_history()
        """
        return self.navigation.get_navigation_history()

    # ========================================================================
    # Linking Methods
    # ========================================================================

    def handle_zLink(
        self,
        zHorizontal: str,
        walker: Optional[Any] = None
    ) -> str:
        """
        Handle inter-file linking.
        
        Delegates to Linking for parsing zLink expressions, checking RBAC
        permissions, loading target files, and updating session context.
        
        Args
        ----
        zHorizontal : str
            zLink expression (e.g., "zLink(path.to.file.block)")
        walker : Optional[Any], default=None
            Optional walker instance for context
        
        Returns
        -------
        str
            Result of link navigation
        
        Examples
        --------
        Basic link::
        
            result = nav.handle_zLink(
                "zLink(users.menu.list_users)",
                walker=walker
            )
        
        Link with permissions::
        
            result = nav.handle_zLink(
                "zLink(admin.settings, {role: 'admin'})",
                walker=walker
            )
        
        Notes
        -----
        - Parses zLink expression (zParser integration)
        - Checks RBAC permissions if specified
        - Loads target file (zLoader integration)
        - Updates session context (zVaFolder, zVaFile, zBlock)
        - Delegates to Linking.handle()
        """
        return self.linking.handle(walker=walker, zHorizontal=zHorizontal)


# ============================================================================
# Standalone Functions (Backward Compatibility)
# ============================================================================

def handle_zLink(zHorizontal: str, walker: Optional[Any] = None) -> str:
    """
    Standalone link handler function for Walker compatibility.
    
    Provides backward compatibility with legacy Walker code by maintaining
    the standalone function interface while delegating to the modern facade.
    
    Args
    ----
    zHorizontal : str
        zLink expression to handle
    walker : Optional[Any], default=None
        Walker instance (required)
    
    Returns
    -------
    str
        Result of link navigation
    
    Raises
    ------
    ValueError
        If walker parameter is not provided
    
    Examples
    --------
    Legacy Walker usage::
    
        from zOS.L2_Core.f_zNavigation import handle_zLink
        result = handle_zLink("zLink(path)", walker)
    
    Notes
    -----
    - Backward compatibility for Walker integration
    - Delegates to walker.zcli.navigation.handle_zLink()
    - Modern code should use facade directly (zcli.navigation.handle_zLink)
    """
    if not walker:
        raise ValueError(f"handle_zLink {_ERROR_MSG_NO_WALKER}")
    
    return walker.zcli.navigation.handle_zLink(zHorizontal=zHorizontal, walker=walker)


def handle_zCrumbs(
    zKey: str,
    walker: Optional[Any] = None,
    operation: str = "APPEND"
) -> Any:
    """
    Standalone breadcrumbs handler function for Walker compatibility.
    
    Self-aware: reads session state to determine active block path.
    Delegates to the modern facade for actual breadcrumb handling.
    
    Args
    ----
    zKey : str
        Key identifier for breadcrumb
    walker : Optional[Any], default=None
        Walker instance (required)
    operation : str, default="APPEND"
        Breadcrumb operation: "APPEND" or "REPLACE"
    
    Returns
    -------
    Any
        Breadcrumb operation result
    
    Raises
    ------
    ValueError
        If walker parameter is not provided
    
    Examples
    --------
    Walker usage::
    
        from zOS.L2_Core.f_zNavigation import handle_zCrumbs
        handle_zCrumbs("key", walker)
    
    Notes
    -----
    - Delegates to walker.zcli.navigation.handle_zCrumbs()
    - Breadcrumbs reads session state for block path (Delta link support)
    - Modern code should use facade directly (zcli.navigation.handle_zCrumbs)
    - Supports APPEND (default) and REPLACE operations
    """
    if not walker:
        raise ValueError(f"handle_zCrumbs {_ERROR_MSG_NO_WALKER}")
    
    return walker.zcli.navigation.handle_zCrumbs(zKey=zKey, walker=walker, operation=operation)
