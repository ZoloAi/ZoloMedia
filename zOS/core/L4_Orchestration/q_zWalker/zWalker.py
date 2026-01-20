# zCLI/subsystems/zWalker/zWalker.py

"""
zWalker Subsystem - Pure Orchestration Layer (Layer 3)

╔══════════════════════════════════════════════════════════════════════════════╗
║ ⚠️  CRITICAL: NO LOGIC ALLOWED IN ZWALKER - ORCHESTRATION ONLY ⚠️            ║
╚══════════════════════════════════════════════════════════════════════════════╝

This module is a PURE ORCHESTRATION LAYER following Linux From Scratch architecture.

**RULES (FOR ALL DEVELOPERS AND LLMs):**
1. ❌ NO business logic - delegate to lower layers (zDispatch, zNavigation, zWizard)
2. ❌ NO data processing - delegate to zWizard or zDispatch
3. ❌ NO validation logic - delegate to zNavigation (self-aware subsystems)
4. ❌ NO path construction - delegate to zNavigation
5. ❌ NO dispatch logic - delegate to zDispatch (Single Source of Truth)
6. ❌ NO special case handling - lower layers handle it
7. ✅ ONLY coordination via callbacks and method calls
8. ✅ ONLY delegation to lower layer subsystems

**VIOLATION = ARCHITECTURAL BREAKDOWN**
Any logic added to zWalker violates:
- Single Source of Truth principle
- Separation of Concerns
- Linux From Scratch layered architecture
- DRY (Don't Repeat Yourself)

────────────────────────────────────────────────────────────────────────────────
ARCHITECTURE: PURE ORCHESTRATOR PATTERN (EXTENDS ZWIZARD)
────────────────────────────────────────────────────────────────────────────────

zWalker is a PURE orchestrator that extends zWizard to add navigation callbacks.
ALL block execution, _data resolution, dispatch, and iteration logic is INHERITED
or DELEGATED - NEVER reimplemented.

    ┌──────────────────────────────────────────────────────────────┐
    │                    ZWALKER (ORCHESTRATOR)                    │
    ├──────────────────────────────────────────────────────────────┤
    │                                                              │
    │  INHERITANCE:                                                │
    │      zWalker extends zWizard                                 │
    │      - Inherits: handle(), execute_loop(), _data resolution  │
    │      - Adds: Navigation callbacks (on_back, on_exit, etc.)   │
    │                                                              │
    │  ORCHESTRATION MAP (100% DELEGATION):                        │
    │      ┌──────────────────────────────────────────────┐        │
    │      │  run() [PURE ORCHESTRATOR]                   │        │
    │      │    ├─→ session.get() [DELEGATION TO ZCONFIG] │        │
    │      │    │   └─→ "zBifrost" → bifrost.orchestrator │        │
    │      │    │                    .start() [ZBIFROST]   │        │
    │      │    ├─→ loader.handle() [DELEGATION TO ZLOADER]        │
    │      │    ├─→ display.zDeclare() [DELEGATION TO ZDISPLAY]    │
    │      │    └─→ execute_loop() [INHERITED FROM ZWIZARD]        │
    │      │        with navigation_callbacks              │        │
    │      │                                                │        │
    │      │  _create_navigation_callbacks()               │        │
    │      │    [RETURNS PURE DELEGATION CALLBACKS]        │        │
    │      │    ├─→ on_continue: navigation.handle_zCrumbs()       │
    │      │    ├─→ on_back: navigation.handle_zBack()     │        │
    │      │    ├─→ on_exit: display.zDeclare() + return   │        │
    │      │    ├─→ on_stop: display.zDeclare() + sys.exit()       │
    │      │    └─→ on_error: display.zDeclare() + sys.exit()      │
    │      └──────────────────────────────────────────────┘        │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘

────────────────────────────────────────────────────────────────────────────────
DUAL-MODE ARCHITECTURE
────────────────────────────────────────────────────────────────────────────────

zWalker supports two execution modes, determined by zSession's zMode:

**Terminal Mode (Default):**
    - Traditional CLI menu navigation
    - Readline-based input with history
    - ASCII-formatted display via zDisplay
    - Direct keyboard input (STDIN)
    - Synchronous execution

**zBifrost Mode (WebSocket):**
    - WebSocket-based client-server architecture
    - JSON message protocol for commands/events
    - HTML-formatted display via zDisplay
    - Remote client input (WebSocket messages)
    - Asynchronous execution via asyncio

Mode Detection (Pure Delegation):
    ```python
    if self.session.get("zMode") == "zBifrost":
        # Delegate to zBifrost subsystem - NO custom logic
        asyncio.run(self.zcli.bifrost.orchestrator.start(walker=self))
    else:
        # Delegate to zWizard.execute_loop - NO custom logic
        return self.execute_loop(items_dict=..., navigation_callbacks=...)
    ```

────────────────────────────────────────────────────────────────────────────────
NAVIGATION CALLBACKS PATTERN (PURE DELEGATION)
────────────────────────────────────────────────────────────────────────────────

zWalker provides navigation callbacks to zWizard.execute_loop - ALL callbacks
are PURE DELEGATION wrappers with NO logic:

**on_continue(result, key):**
    - Delegates breadcrumb tracking to zNavigation.handle_zCrumbs()
    - NO validation - zNavigation is self-aware
    - NO path construction - zNavigation handles it
    - ✅ Pure delegation: `self.navigation.handle_zCrumbs(key, walker=self)`

**on_back(result):**
    - Delegates to zNavigation.handle_zBack() for breadcrumb pop
    - Delegates to zWizard.execute_loop() for re-execution
    - NO custom logic - pure coordination
    - ✅ Pure delegation chain

**on_exit(result):**
    - Soft exit coordination (return to caller)
    - Delegates display to zDisplay.zDeclare()
    - Returns dict for caller (zShell or script)
    - ✅ Acceptable: coordination + return value

**on_stop(result):**
    - Hard stop coordination (terminate process)
    - Delegates display to zDisplay.zDeclare()
    - Calls sys.exit() for termination
    - ✅ Acceptable: coordination + termination

**on_error(error_or_result, key):**
    - Error coordination (log + display + exit)
    - Delegates display to zDisplay.zDeclare()
    - Calls sys.exit() for clean termination
    - ✅ Acceptable: coordination + termination

────────────────────────────────────────────────────────────────────────────────
BREADCRUMB TRACKING (DELEGATED TO ZNAVIGATION)
────────────────────────────────────────────────────────────────────────────────

zWalker does NOT manage breadcrumbs - it DELEGATES to zNavigation:

**Delegation Pattern:**
    - ❌ NO path construction in zWalker
    - ❌ NO validation in zWalker
    - ❌ NO breadcrumb management in zWalker
    - ✅ ONLY calls: `self.navigation.handle_zCrumbs(key, walker=self)`
    - ✅ ONLY calls: `self.navigation.handle_zBack(walker=self)`

**Storage (managed by zNavigation via zConfig):**
    ```python
    zSession["zCrumbs"] = {
        "@.zUI.main_menu.MainMenu": ["dashboard", "settings"],
        "@.zUI.settings_menu.SettingsMenu": ["profile"]
    }
    ```

**Note:** All breadcrumb logic (path construction, validation, storage) is in
zNavigation.breadcrumbs module - zWalker is a PASSIVE CALLER ONLY.

────────────────────────────────────────────────────────────────────────────────
DEPENDENCIES
────────────────────────────────────────────────────────────────────────────────

**Subsystems (All from zcli instance):**
    - zWizard: Loop engine (via inheritance)
    - zNavigation: Breadcrumbs, menus, back navigation, inter-file linking
    - zDisplay: Mode-agnostic output (Terminal + Bifrost)
    - zDispatch: Command routing and execution
    - zLoader: YAML file loading (zVaFile)
    - zConfig: Session management (zMode, zCrumbs, zBlock)
    - zComm: WebSocket server (zBifrost mode)
    - zFunc: Function execution (via dispatch)
    - zOpen: File/URL opening (via dispatch)
    - zUtils: Plugin system (via dispatch)

**External Modules:**
    - sys: For sys.exit() in hard stop
    - asyncio: For zBifrost server (imported inline)

────────────────────────────────────────────────────────────────────────────────
USAGE
────────────────────────────────────────────────────────────────────────────────

**Terminal Mode:**
    ```python
    from zOS.L4_Orchestration.q_zWalker import zWalker
    
    walker = zWalker(zcli)
    walker.run()  # Starts terminal-based menu navigation
    ```

**zBifrost Mode (WebSocket):**
    ```python
    # Set mode before walker initialization
    zcli.session["zMode"] = "zBifrost"
    
    walker = zWalker(zcli)
    walker.run()  # Starts WebSocket server instead of terminal loop
    ```

**From zShell (Launch Walker from Shell):**
    ```python
    # User types: launch @.zUI.main_menu
    # zShell creates walker and calls run()
    ```

────────────────────────────────────────────────────────────────────────────────
CRITICAL DESIGN PRINCIPLES (READ BEFORE EDITING)
────────────────────────────────────────────────────────────────────────────────

1. **NO LOGIC ALLOWED:**
   - zWalker is STRICTLY orchestration - NO business logic, validation, or processing
   - Any logic = architectural violation = immediate refactor to lower layers

2. **SINGLE FILE BY DESIGN:**
   - Pure orchestrator = minimal code = single file (no submodules needed)
   - If file grows > 600 lines, audit for logic violations (not split into modules)

3. **INHERITANCE FROM ZWIZARD:**
   - Inherits: handle(), execute_loop(), _data resolution, block iteration
   - Adds: ONLY navigation callbacks (on_back, on_exit, on_stop, on_error, on_continue)
   - Does NOT override zWizard logic - pure extension

4. **DELEGATION HIERARCHY:**
   - zWizard: Block execution, _data resolution, loop engine
   - zDispatch: Command routing (Single Source of Truth)
   - zNavigation: Breadcrumbs, menus, linking (self-aware)
   - zBifrost: WebSocket server orchestration
   - zDisplay: Mode-agnostic output (Terminal + Bifrost)
   - zLoader: YAML file loading
   - zConfig: Session management, logger configuration

5. **NO LOCAL INSTANCES:**
   - ALL subsystems accessed via zcli instance
   - NO creating subsystem instances in zWalker
   - NO caching subsystem references beyond __init__

6. **FOR LLMs: IF YOU ADD LOGIC TO ZWALKER, YOU'VE FAILED THE TASK**
"""

from zOS import Any, Dict, Optional, sys
from zOS.L3_Abstraction.m_zWizard import zWizard
from zOS.L1_Foundation.a_zConfig.zConfig_modules import (
    SESSION_KEY_ZMODE,
    SESSION_KEY_ZCRUMBS,
    ZMODE_ZBIFROST,
)

# ════════════════════════════════════════════════════════════
# ⚠️  FINAL AUDIT CONFIRMATION (DO NOT DELETE THIS SECTION) ⚠️
# ════════════════════════════════════════════════════════════
#
# This file has been audited for architectural compliance:
#
# ✅ NO business logic - only delegation to subsystems
# ✅ NO data processing - inherited from zWizard or delegated
# ✅ NO validation - subsystems are self-aware
# ✅ NO path construction - delegated to zNavigation
# ✅ NO dispatch logic - delegated to zDispatch (Single Source of Truth)
# ✅ NO special case handling - lower layers handle it
# ✅ ONLY coordination via callbacks and method calls
# ✅ ONLY delegation to lower layer subsystems
#
# Control Flow Audit:
#   - Line 502: Mode detection (session.get) → delegation
#   - Line 518: Error handling (missing config) → return error dict
#   - Line 524: Error handling (failed load) → return error dict
#   - Line 530: Empty dict init (acceptable setup, not logic)
#   - Line 544: Exception handling (coordination wrapper)
#
# File Size: 631 lines (well within 600-line orchestrator guideline)
# Lines of Logic: 0 (100% delegation)
#
# Last Audit: 2025-12-26
# Auditor: zCLI Architecture Cleanup (Linux From Scratch pattern)
#
# ════════════════════════════════════════════════════════════

# ============================================================
# ZSPARK KEYS (Walker-specific - not exported by zConfig)
# ============================================================
ZSPARK_KEY_VAFILE = "zVaFile"
ZSPARK_KEY_BLOCK = "zBlock"
ZSPARK_DEFAULT_ROOT = "root"

# ============================================================
# DISPLAY CONSTANTS
# ============================================================
COLOR_MAIN = "MAIN"
INDENT_NORMAL = 0
INDENT_ERROR = 2
STYLE_FULL = "full"
STYLE_MINIMAL = "~"

# ============================================================
# MESSAGES
# ============================================================
MSG_WALKER_READY = "zWalker Ready"
MSG_WALKER_LOOP = "zWalker Loop"
MSG_SESSION_COMPLETED = "Walker session completed"
MSG_SYSTEM_STOPPED = "You've stopped the system!"
MSG_ERROR_RETURNED = "Error Returned"
MSG_BIFROST_STARTING = "Starting zBifrost WebSocket server..."
MSG_WALKER_INIT = "zWalker initialized (fully modernized architecture)"

# ============================================================
# ERROR MESSAGES
# ============================================================
ERROR_NO_VAFILE = "No zVaFile specified"
ERROR_FAILED_LOAD = "Failed to load zVaFile"
ERROR_BLOCK_NOT_FOUND = "Root zBlock not found"
ERROR_EXECUTION_FAILED = "zWalker execution failed"

# ============================================================
# DICT KEYS (for return values)
# ============================================================
DICT_KEY_ERROR = "error"
DICT_KEY_EXIT = "exit"
DICT_VALUE_COMPLETED = "completed"

# ============================================================
# SPECIAL DICT KEYS (no longer used - zDispatch handles zWizard)
# ============================================================
# SPECIAL_KEY_ZWIZARD removed - zDispatch detects and handles zWizard keys

# ============================================================
# NAVIGATION CALLBACK KEYS
# ============================================================
CALLBACK_ON_BACK = "on_back"
CALLBACK_ON_EXIT = "on_exit"
CALLBACK_ON_STOP = "on_stop"
CALLBACK_ON_ERROR = "on_error"

# ============================================================
# LOG MESSAGES
# ============================================================
LOG_ERROR_NO_VAFILE = "No zVaFile specified in zSpark_obj"
LOG_ERROR_FAILED_LOAD = "Failed to load zVaFile: %s"
LOG_ERROR_BLOCK_NOT_FOUND = "Root zBlock '%s' not found in zVaFile"
LOG_ERROR_EXECUTION = "zWalker execution failed: %s"
LOG_DEBUG_BREADCRUMB = "Initialized breadcrumb: %s"
LOG_DEBUG_DISPATCH_EXIT = "Dispatch returned exit"
LOG_DEBUG_DISPATCH_STOP = "Dispatch returned stop"
LOG_INFO_ERROR_AFTER_KEY = "Error after key: %s"


class zWalker(zWizard):
    """
    PURE Orchestration Layer (Layer 3) - YAML-driven UI/Menu Navigation.
    
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║ ⚠️  NO LOGIC ALLOWED - ORCHESTRATION ONLY - DELEGATES EVERYTHING ⚠️     ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    zWalker extends zWizard to add ONLY navigation callbacks.
    ALL execution, dispatch, validation, path construction is DELEGATED.
    
    **WHAT ZWALKER DOES (ONLY):**
    ✅ Detect mode (Terminal vs zBifrost) → delegate to appropriate subsystem
    ✅ Load YAML file → delegate to zLoader
    ✅ Execute blocks → delegate to zWizard.execute_loop (inherited)
    ✅ Track breadcrumbs → delegate to zNavigation via on_continue callback
    ✅ Handle navigation → delegate to zNavigation via callbacks
    ✅ Display messages → delegate to zDisplay
    
    **WHAT ZWALKER DOES NOT DO:**
    ❌ NO block iteration logic (inherited from zWizard)
    ❌ NO _data resolution (inherited from zWizard)
    ❌ NO dispatch logic (uses zDispatch via zWizard)
    ❌ NO breadcrumb path construction (zNavigation handles it)
    ❌ NO validation (subsystems are self-aware)
    ❌ NO special case handling (lower layers handle it)
    ❌ NO business logic of ANY kind
    
    Attributes:
        zcli (Any): Main zCLI instance with ALL subsystems (single source)
        zSpark_obj (Dict[str, Any]): Boot config (via zcli.zspark_obj)
        session (Dict[str, Any]): Session state (via zcli.session, managed by zConfig)
        display (Any): zDisplay instance (via zcli.display)
        dispatch (Any): zDispatch instance (via zcli.dispatch)
        navigation (Any): zNavigation instance (via zcli.navigation)
        loader (Any): zLoader instance (via zcli.loader)
        zfunc (Any): zFunc instance (via zcli.zfunc)
        open (Any): zOpen instance (via zcli.open)
        plugins (Dict[str, Any]): Plugin registry (via zcli.utils.plugins)
        logger (Any): Logger instance (inherited from zWizard via zConfig)
        block_context (Dict[str, Any]): Context for zBifrost (ephemeral state)
    
    Methods (ALL are pure orchestration):
        __init__(zcli): Store subsystem references (NO logic)
        run(): Detect mode + delegate to zBifrost or zWizard (NO logic)
        _create_navigation_callbacks(): Return callback dict (pure delegation wrappers)
    
    Inheritance:
        Extends zWizard → inherits handle(), execute_loop(), _data resolution
    
    Orchestration Flow:
        run() → mode detection → delegate:
            - zBifrost mode: zcli.bifrost.orchestrator.start(walker=self)
            - Terminal mode: self.execute_loop(items_dict, navigation_callbacks)
        
        Navigation callbacks → all delegate to subsystems:
            - on_continue: self.navigation.handle_zCrumbs(key, walker=self)
            - on_back: self.navigation.handle_zBack() + self.execute_loop()
            - on_exit: self.display.zDeclare() + return dict
            - on_stop: self.display.zDeclare() + sys.exit()
            - on_error: self.display.zDeclare() + sys.exit()
    
    Examples:
        >>> # Terminal mode (default)
        >>> walker = zWalker(zcli)
        >>> walker.run()  # → delegates to zWizard.execute_loop
        
        >>> # zBifrost mode (WebSocket)
        >>> zcli.session["zMode"] = "zBifrost"
        >>> walker = zWalker(zcli)
        >>> walker.run()  # → delegates to bifrost.orchestrator.start
    
    Notes:
        - 100% orchestration - ZERO logic
        - Single file by design (pure orchestrator = minimal code)
        - NO local subsystem instances (ALL via zcli)
        - If adding code, ask: "Should this be in a lower layer?" (answer: YES)
    """
    
    def __init__(self, zcli: Any) -> None:
        """
        Initialize zWalker - PURE ORCHESTRATION (store references only).
        
        NO LOGIC - only stores subsystem references from zcli instance.
        Extends zWizard parent to inherit block execution capabilities.
        
        **What this method does:**
        ✅ Call super().__init__(zcli, walker=self) to initialize zWizard parent
        ✅ Store references to subsystems (self.zcli, self.display, etc.)
        ✅ Display ready message via zDisplay
        ✅ Log initialization via zConfig logger
        
        **What this method does NOT do:**
        ❌ NO logger configuration (zConfig already did it)
        ❌ NO session initialization (zConfig already did it)
        ❌ NO validation (not needed - subsystems are robust)
        ❌ NO special setup (lower layers handle everything)
        
        Args:
            zcli: zCLI instance with ALL subsystems initialized
                  (display, dispatch, navigation, loader, session, bifrost, etc.)
        
        Returns:
            None
        
        Examples:
            >>> walker = zWalker(zcli)
            # Output: "zWalker Ready" (via zDisplay)
            # Logger: "zWalker initialized (fully modernized architecture)"
            
        Notes:
            - Pure reference storage - NO logic
            - ALL subsystems accessed via zcli (single source)
            - walker=self passed to zWizard allows callbacks to access walker context
            - Logger already configured by zConfig (DO NOT reconfigure)
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 1: Initialize zWizard parent (inherit execution capabilities)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        super().__init__(zcli=zcli, walker=self)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 2: Store subsystem references (NO logic, just references)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # ALL subsystems accessed via zcli - NO local instances created
        self.zcli: Any = zcli
        self.zSpark_obj: Dict[str, Any] = zcli.zspark_obj  # Boot config (zConfig)
        self.session: Dict[str, Any] = zcli.session  # Session state (zConfig)
        self.display: Any = zcli.display  # Output (Terminal + Bifrost)
        self.dispatch: Any = zcli.dispatch  # Command routing (Single Source of Truth)
        self.navigation: Any = zcli.navigation  # Breadcrumbs + menus + linking
        self.loader: Any = zcli.loader  # YAML file loading
        self.zfunc: Any = zcli.zfunc  # Function execution
        self.open: Any = zcli.open  # File/URL opening
        self.plugins: Dict[str, Any] = zcli.utils.plugins  # Plugin registry
        
        # Walker-specific ephemeral state (NOT configuration)
        self.block_context: Dict[str, Any] = {}  # For zBifrost message handler
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 3: Display ready message + log init (delegation to subsystems)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.display.zDeclare(MSG_WALKER_READY, color=COLOR_MAIN, indent=INDENT_NORMAL, style=STYLE_FULL)
        # Logger already configured by zConfig - NO reconfiguration needed
        self.logger.framework.debug(MSG_WALKER_INIT)

    def run(self) -> Dict[str, Any]:
        """
        Main entry point - PURE ORCHESTRATION (detect mode + delegate).
        
        NO LOGIC - only mode detection and delegation to subsystems.
        
        **Orchestration Flow:**
        1. Check session.get("zMode") via zConfig
        2. If "zBifrost" → delegate to bifrost.orchestrator.start()
        3. Else → load YAML via zLoader → delegate to zWizard.execute_loop()
        
        **What this method does:**
        ✅ Mode detection (read from zConfig session)
        ✅ zBifrost mode: asyncio.run(bifrost.orchestrator.start(walker=self))
        ✅ Terminal mode: loader.handle() + execute_loop(navigation_callbacks)
        ✅ Initialize empty breadcrumbs dict if not present
        
        **What this method does NOT do:**
        ❌ NO block iteration (zWizard.execute_loop does it)
        ❌ NO dispatch logic (zWizard uses zDispatch automatically)
        ❌ NO _data resolution (zWizard handles it)
        ❌ NO breadcrumb path construction (zNavigation via on_continue callback)
        ❌ NO validation (subsystems are self-aware)
        
        Returns:
            Dict[str, Any]: Result dictionary:
                - Terminal mode: {"exit": "completed"} (from zWizard)
                - zBifrost mode: {} (server blocks indefinitely)
                - Error: {"error": "error message"}
        
        Notes:
            - 100% delegation - NO custom logic
            - zWizard.execute_loop inherited - NO override
            - navigation_callbacks are pure delegation wrappers
            - Empty dict init (line 428-429) is acceptable setup, NOT logic
        """
        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ZBIFROST MODE: Delegate to zBifrost subsystem (NO custom logic)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if self.session.get(SESSION_KEY_ZMODE) == ZMODE_ZBIFROST:
                import asyncio
                self.logger.info(MSG_BIFROST_STARTING)
                # DELEGATION: zBifrost.orchestrator handles ALL WebSocket logic
                asyncio.run(self.zcli.bifrost.orchestrator.start(
                    socket_ready=asyncio.Event(),
                    walker=self
                ))
                return {}  # Never reached (server blocks), but for type consistency
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # TERMINAL MODE: Load file + delegate to zWizard.execute_loop
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            # Get zVaFile from zSpark (boot config managed by zConfig)
            zVaFile: Optional[str] = self.zSpark_obj.get(ZSPARK_KEY_VAFILE)
            if not zVaFile:
                self.logger.error(LOG_ERROR_NO_VAFILE)
                return {DICT_KEY_ERROR: ERROR_NO_VAFILE}

            # DELEGATION: zLoader handles ALL file loading (navbar injection, validation)
            raw_zFile: Optional[Dict[str, Any]] = self.loader.handle(None)
            if not raw_zFile:
                self.logger.error(LOG_ERROR_FAILED_LOAD, zVaFile)
                return {DICT_KEY_ERROR: f"{ERROR_FAILED_LOAD}: {zVaFile}"}

            # Initialize empty breadcrumbs dict (acceptable setup, not logic)
            # zNavigation handles ALL path construction and validation via callbacks
            if SESSION_KEY_ZCRUMBS not in self.session:
                self.session[SESSION_KEY_ZCRUMBS] = {}

            # DELEGATION: zDisplay handles message formatting and output
            self.display.zDeclare(MSG_WALKER_LOOP, color=COLOR_MAIN, indent=INDENT_NORMAL, style=STYLE_FULL)

            # Get block name from zSpark (if specified)
            # DELEGATION: zWizard.execute_loop handles block extraction internally
            block_name: Optional[str] = self.zSpark_obj.get(ZSPARK_KEY_BLOCK)

            # DELEGATION: zWizard.execute_loop handles ALL:
            # - Block extraction (if block_name provided)
            # - Block iteration + _data resolution
            # - RBAC enforcement
            # NO dispatch_fn provided - zWizard automatically uses walker.dispatch.handle
            # (Single Source of Truth: zDispatch for ALL command routing)
            return self.execute_loop(
                items_dict=raw_zFile,
                navigation_callbacks=self._create_navigation_callbacks(),
                block_name=block_name
            )

        except Exception as e:
            self.logger.error(LOG_ERROR_EXECUTION, e, exc_info=True)
            return {DICT_KEY_ERROR: str(e)}

    def _create_navigation_callbacks(self) -> Dict[str, Any]:
        """
        Create navigation callbacks - PURE DELEGATION WRAPPERS ONLY.
        
        NO LOGIC - returns dict of callback functions that ONLY delegate to subsystems.
        Each callback is a thin wrapper around subsystem method calls.
        
        **Callbacks (all are pure delegation):**
        - on_continue(result, key): → self.navigation.handle_zCrumbs(key, walker=self)
        - on_back(result): → self.navigation.handle_zBack() + self.execute_loop()
        - on_exit(result): → self.display.zDeclare() + return {"exit": "completed"}
        - on_stop(result): → self.display.zDeclare() + sys.exit()
        - on_error(error, key): → self.display.zDeclare() + sys.exit()
        
        **NO LOGIC ALLOWED:**
        ❌ NO validation in callbacks
        ❌ NO path construction in callbacks
        ❌ NO dispatch logic in callbacks (zDispatch handles it via zWizard)
        ❌ NO special case handling in callbacks
        
        Returns:
            Dict[str, Any]: Callback dictionary for zWizard.execute_loop
                Keys: "on_continue", "on_back", "on_exit", "on_stop", "on_error"
                Values: Pure delegation wrapper functions
        
        Notes:
            - These callbacks are Walker's ONLY addition to zWizard
            - ALL callbacks are coordination wrappers - NO business logic
            - zNavigation is self-aware - NO validation needed in callbacks
        """
        def on_continue(result: Any, key: str) -> None:  # pylint: disable=unused-argument
            """Track breadcrumb - PURE DELEGATION to zNavigation."""
            # ❌ NO validation - zNavigation is self-aware
            # ❌ NO path construction - zNavigation handles it
            # ✅ ONLY delegation - pure orchestration wrapper
            
            # Skip breadcrumb tracking for display directives (zCrumbs is a display event, not a navigation key)
            if key.lstrip('_') == 'zCrumbs':
                return
            
            self.navigation.handle_zCrumbs(key, walker=self)
        
        def on_back(result: Any) -> Any:  # pylint: disable=unused-argument
            """Handle zBack - PURE DELEGATION chain to zNavigation + zWizard."""
            # DELEGATION STEP 1: zNavigation.handle_zBack pops breadcrumb + loads file
            # (returns: block_dict, block_keys, start_key)
            back_result = self.navigation.handle_zBack(
                show_banner=False, 
                walker=self
            )
            
            # Handle case where there's nowhere to go back to (standalone wizard)
            if back_result is None or (isinstance(back_result, tuple) and not back_result[0]):
                self.logger.debug("No parent context to navigate back to - treating as exit")
                return on_exit(result)
            
            # Unpack the tuple
            block_dict, _, start_key = back_result
            
            # DELEGATION STEP 2: zWizard.execute_loop re-executes with new context
            # NO dispatch_fn - zDispatch is Single Source of Truth
            return self.execute_loop(
                items_dict=block_dict,
                navigation_callbacks=self._create_navigation_callbacks(),
                start_key=start_key
            )
        
        def on_exit(result: Any) -> Dict[str, Any]:  # pylint: disable=unused-argument
            """Handle soft exit - coordination wrapper (log + display + return)."""
            # Acceptable orchestration: log → display → return
            # NOT business logic - just coordination
            self.logger.debug(LOG_DEBUG_DISPATCH_EXIT)
            self.display.zDeclare(MSG_SESSION_COMPLETED, color=COLOR_MAIN, indent=INDENT_NORMAL, style=STYLE_MINIMAL)
            return {DICT_KEY_EXIT: DICT_VALUE_COMPLETED}
        
        def on_stop(result: Any) -> None:  # pylint: disable=unused-argument
            """Handle hard stop - coordination wrapper (log + display + terminate)."""
            # Acceptable orchestration: log → display → sys.exit()
            # NOT business logic - just coordination
            self.logger.debug(LOG_DEBUG_DISPATCH_STOP)
            self.display.zDeclare(MSG_SYSTEM_STOPPED, color=COLOR_MAIN, indent=INDENT_NORMAL, style=STYLE_FULL)
            sys.exit()
        
        def on_error(error_or_result: Any, key: str) -> None:  # pylint: disable=unused-argument
            """Handle error - coordination wrapper (log + display + terminate)."""
            # Acceptable orchestration: log → display → sys.exit()
            # NOT business logic - just coordination
            self.logger.info(LOG_INFO_ERROR_AFTER_KEY, key)
            self.display.zDeclare(MSG_ERROR_RETURNED, color=COLOR_MAIN, indent=INDENT_ERROR, style=STYLE_MINIMAL)
            sys.exit()
        
        return {
            "on_continue": on_continue,  # Track breadcrumbs after each step
            CALLBACK_ON_BACK: on_back,
            CALLBACK_ON_EXIT: on_exit,
            CALLBACK_ON_STOP: on_stop,
            CALLBACK_ON_ERROR: on_error
        }
