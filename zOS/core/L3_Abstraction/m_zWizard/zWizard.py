# zCLI/subsystems/zWizard/zWizard.py

"""
zWizard - Core Loop Engine for Stepped Execution
=================================================

The zWizard subsystem provides a declarative, multi-step workflow engine that powers
both Shell commands and Walker menu navigation. It orchestrates complex sequences
with context persistence, transaction support, and RBAC enforcement.

Core Responsibilities
--------------------
1. **Loop Execution**: Iterate through ordered key-value pairs with dispatch
2. **Navigation Handling**: Process navigation signals (zBack, exit, stop, error)
3. **Context Management**: Maintain persistent state across steps via WizardHat
4. **Transaction Support**: Optional transactional execution with rollback
5. **RBAC Integration**: Enforce role-based access control per step
6. **Error Handling**: Graceful error handling with callback support
7. **Mode Flexibility**: Support both Shell (command) and Walker (menu) modes

Architecture
-----------
### Dual-Mode Design
- **Shell Mode**: Uses `zcli` instance for command-based workflows
- **Walker Mode**: Uses `walker` instance for menu-based navigation
- **Instance Detection**: Automatically detects mode from constructor args

### Key Components
1. **zWizard.py** (this file): Main orchestrator class
2. **wizard_hat.py**: Dual-access state container (dict + attribute access)
3. **wizard_interpolation.py**: Template variable interpolation ({{ zHat.key }})
4. **wizard_transactions.py**: Transaction management for data operations
5. **wizard_rbac.py**: Role-based access control enforcement
6. **wizard_exceptions.py**: Custom exception types

### Navigation Flow
```
┌─────────────────────────────────────────────────────────────────┐
│ execute_loop(items_dict, dispatch_fn, navigation_callbacks)    │
│                                                                 │
│  For each key in items_dict:                                   │
│    1. Check RBAC access → Skip if denied                       │
│    2. Dispatch action → Execute via dispatch_fn                │
│    3. Handle result:                                           │
│       - Key jump? → Jump to that key in loop                   │
│       - Navigation signal? → Call callback or return           │
│       - Error? → Handle via error callback                     │
│    4. Continue to next key                                     │
│                                                                 │
│  Return: Navigation result or None                             │
└─────────────────────────────────────────────────────────────────┘
```

### Context Persistence (WizardHat)
The `WizardHat` container provides dual-access state management:
```python
zHat = WizardHat()
zHat["user"] = "Alice"        # Dict-style access
print(zHat.user)              # Attribute-style access → "Alice"
```

### Variable Interpolation
Steps can reference previous step results using `{{ zHat.key }}` syntax:
```yaml
step1:
  type: zFunc
  function: get_user_id
  
step2:
  type: zDisplay
  message: "User ID: {{ zHat.step1 }}"  # Interpolates step1's result
```

Navigation Signals
-----------------
### Core Signals (NAVIGATION_SIGNALS tuple)
- **zBack**: Return to previous menu/context
- **exit**: Exit the wizard/walker entirely
- **stop**: Stop current execution
- **error**: Indicate an error occurred
- **""** (empty): Error signal (treated as error)

### Navigation Callbacks
Wizards can provide custom handlers for navigation events:
```python
navigation_callbacks = {
    "on_back": handle_back,     # Called on zBack
    "on_exit": handle_exit,     # Called on exit
    "on_stop": handle_stop,     # Called on stop
    "on_error": handle_error    # Called on error
}
```

RBAC Integration
---------------
Each step can have RBAC requirements enforced automatically:
- **Check**: Uses `wizard_rbac.checkzRBAC_access()`
- **Denial**: Skips step and continues to next
- **Logging**: Logs access denials for audit trail
- **Display**: Shows access denied message if display available

Transaction Support
------------------
Wizards can execute with transactional semantics:
```yaml
_transaction: true  # Enable transaction mode
step1: 
  zData: ...
step2:
  zData: ...  # Committed together or rolled back on error
```

Integration Points
-----------------
### How zShell Uses zWizard
**Wizard Mode Execution:**
- zShell enters "wizard mode" when executing declarative YAML workflows
- Steps are dispatched via `shell.executor.execute_wizard_step()`
- Context includes `wizard_mode: True` flag for special handling
- WizardHat accumulates results across all steps
- Navigation signals control flow (zBack returns to shell prompt)

**Example Flow:**
```
1. User runs: zolo wizard my_workflow.yaml
2. zShell loads YAML, calls wizard.handle(workflow)
3. zWizard executes each step via shell executor
4. Results accumulate in zHat
5. Shell displays final results or handles navigation
```

### How zWalker Uses zWizard (Inheritance)
**Menu Orchestration:**
- zWalker inherits from zWizard, reusing the loop engine
- Menu items become wizard steps with dispatch to walker.dispatch
- Navigation signals map to menu actions (zBack = previous menu)
- RBAC protects menu items based on user roles
- WizardHat tracks menu selections and state

**Key Differences:**
- Walker uses its own dispatch instance (walker.dispatch.handle)
- Menu items don't show "zWizard Ready" message (suppressed for subclasses)
- Navigation is menu-centric (breadcrumbs, menu stack)

### Integration with zLoader.schema_cache
**Transaction Management:**
- zWizard detects transaction mode from `_transaction: true`
- Identifies database alias from `$alias` in zData model references
- Passes schema_cache through context to all zData operations
- On success: Calls `schema_cache.commit_transaction(alias)`
- On error: Calls `schema_cache.rollback_transaction(alias)`
- Always cleans up: `schema_cache.clear()` after execution

**Connection Reuse:**
- Schema cache maintains database connections across wizard steps
- Same connection used for all operations within a transaction
- Improves performance and ensures transaction isolation
- Context key: `_CONTEXT_KEY_SCHEMA_CACHE`

### Integration with zData Subsystem
**Data Operations:**
- zData operations execute within wizard context when `wizard_mode: True`
- Steps can reference previous data results: `{{ zHat.step1.id }}`
- Transaction alias from `$model` enables atomic multi-step operations
- zData returns results that are stored in WizardHat for interpolation

**Transactional Flow:**
```yaml
_transaction: true
create_user:
  zData:
    model: "$users"      # Transaction starts with "users" alias
    operation: create
    data: {name: "Alice"}

create_profile:
  zData:
    model: "$users"      # Uses same transaction
    operation: create
    data: {user_id: "{{ zHat.create_user.id }}", bio: "Developer"}

# Both operations committed together atomically
```

### Integration with zAuth (RBAC)
**Access Control:**
- Each wizard step can declare `zRBAC` metadata
- zWizard calls `checkzRBAC_access()` before executing each step
- Authentication check: `zcli.auth.is_authenticated()`
- Role check: `zcli.auth.has_role(required_role)`
- Permission check: `zcli.auth.has_permission(required_permission)`
- Denied steps are skipped (not executed), audit logged

**Context-Aware RBAC:**
- Uses active auth context (zSession, Application, or Dual mode)
- RBAC checks respect three-tier authentication model
- Access denied displayed via zDisplay (Terminal + Bifrost compatible)

### Integration with zDisplay
**Mode-Agnostic Output:**
- All wizard output goes through zDisplay subsystem
- Works in Terminal mode (direct output) and Bifrost mode (WebSocket)
- Uses declarative display events (not print statements)
- Wizard steps return None, display via `display.handle()` or `display.zDeclare()`

**Display Events:**
- Step progress: `display.zDeclare("zWizard step: X", color=SUBSYSTEM_COLOR)`
- Access denied: Multi-event sequence with error styling
- Results: Via step-specific display logic (zDisplay events)

### Integration with zDispatch
**Action Routing:**
- zWizard doesn't execute actions directly
- Delegates to `zcli.dispatch.handle(key, value, context)` (Shell mode)
- Or delegates to `walker.dispatch.handle(key, value)` (Walker mode)
- Context includes: wizard_mode, schema_cache, zHat
- Dispatch determines action type (zFunc, zDisplay, zData, etc.)

**Dispatch Context Flow:**
```
zWizard → dispatch.handle() → Action Type Detection → Subsystem Execution
          (passes context)      (zFunc, zData, etc.)  (receives context)
```

Layer Position
-------------
- **Layer**: 2 (Middle Layer - Orchestration)
- **Position**: 2 (After zUtils, before zData/zShell)
- **Initialization Order**: Depends on zConfig, zDisplay, zParser, zLoader, zFunc
- **Consumed By**: zShell (wizard mode), zWalker (menu orchestration), zData (transactions)
- **Architecture Tier**: Orchestration (coordinates multiple subsystems)

Constants Reference
------------------
### Subsystem Identity
- SUBSYSTEM_NAME: "zWizard"
- SUBSYSTEM_COLOR: "ZWIZARD"
- _MSG_READY: "zWizard Ready"

### Navigation Signals
- _SIGNAL_ZBACK, _SIGNAL_EXIT, _SIGNAL_STOP, _SIGNAL_ERROR, _SIGNAL_EMPTY
- NAVIGATION_SIGNALS: Tuple of all signals

### Context Keys
- _CONTEXT_KEY_WIZARD_MODE: Session key for wizard mode flag
- _CONTEXT_KEY_SCHEMA_CACHE: Key for schema cache in context
- _CONTEXT_KEY_ZHAT: Key for WizardHat instance

### Callbacks
- _CALLBACK_ON_BACK, _CALLBACK_ON_EXIT, _CALLBACK_ON_STOP, _CALLBACK_ON_ERROR

### Display
- _MSG_HANDLE_WIZARD, _MSG_WIZARD_STEP, _MSG_ZKEY_DISPLAY, _MSG_DISPATCH_ERROR
- _STYLE_FULL, _STYLE_SINGLE, _COLOR_MAIN, _COLOR_ERROR
- _INDENT_LEVEL_0, _INDENT_LEVEL_1, _INDENT_LEVEL_2

Usage Examples
-------------
### Shell Command Workflow
```python
wizard = zWizard(zcli=zcli_instance)
items = {
    "welcome": {"type": "zDisplay", "message": "Welcome!"},
    "get_name": {"type": "zDialog", "prompt": "Name?"},
    "greet": {"type": "zFunc", "function": "greet_user"}
}
result = wizard.execute_loop(items)
```

### Walker Menu Navigation
```python
walker = zWalker(walker_instance)  # zWalker inherits from zWizard
menu_items = {
    "users": {"label": "Manage Users", "action": "user_menu"},
    "settings": {"label": "Settings", "action": "settings_menu"}
}
result = walker.execute_loop(menu_items)
```

Dependencies
-----------
- **Internal**: zDisplay, zDispatch, zAuth (via zcli/walker)
- **Modules**: wizard_hat, wizard_interpolation, wizard_transactions, 
              wizard_rbac, wizard_exceptions
- **Config**: SESSION_KEY_WIZARD_MODE from zConfig

Version History
--------------
- v1.5.4 Week 6.14: Industry-grade modernization (Phase 0-1)
- v1.5.4 Week 3.3: RBAC integration
- Earlier: Initial implementation

Notes
-----
- zWalker inherits from zWizard, reusing loop engine for menus
- Only direct zWizard instances show "zWizard Ready" message
- All display output is mode-agnostic (Terminal + Bifrost)
- Uses UI Adapter pattern (returns None, outputs via zDisplay)
"""

from zOS import Any, Dict, Optional

from .zWizard_modules.wizard_hat import WizardHat
from .zWizard_modules.wizard_interpolation import interpolate_zhat
from .zWizard_modules.wizard_transactions import (
    check_transaction_start,
    commit_transaction,
    rollback_transaction,
)
from .zWizard_modules.wizard_rbac import checkzRBAC_access, RBAC_ACCESS_DENIED, RBAC_ACCESS_DENIED_ZGUEST
from .zWizard_modules.wizard_exceptions import (
    WizardInitializationError,
    ERR_MISSING_INSTANCE
)

# Import session constants from zConfig
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_WIZARD_MODE


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "zWizard",
    # Public Constants
    "SUBSYSTEM_NAME",
    "SUBSYSTEM_COLOR",
    "NAVIGATION_SIGNALS",
]


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS - CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# Public Constants (exported from wizard_modules)
from .zWizard_modules import (
    SUBSYSTEM_NAME,
    SUBSYSTEM_COLOR,
    NAVIGATION_SIGNALS,
)

# Internal Constants (direct import for internal use)
from .zWizard_modules.wizard_constants import (
    _MSG_READY,
    _SIGNAL_ZBACK,
    _SIGNAL_EXIT,
    _SIGNAL_STOP,
    _SIGNAL_ERROR,
    _SIGNAL_EMPTY,
    _CONTEXT_KEY_WIZARD_MODE,
    _CONTEXT_KEY_SCHEMA_CACHE,
    _CONTEXT_KEY_ZHAT,
    _CALLBACK_ON_BACK,
    _CALLBACK_ON_EXIT,
    _CALLBACK_ON_STOP,
    _CALLBACK_ON_ERROR,
    _MSG_HANDLE_WIZARD,
    _MSG_WIZARD_STEP,
    _MSG_ZKEY_DISPLAY,
    _MSG_DISPATCH_ERROR,
    _STYLE_FULL,
    _STYLE_SINGLE,
    _COLOR_MAIN,
    _COLOR_ERROR,
    _LOG_MSG_PROCESSING_KEY,
    _LOG_MSG_MENU_SELECTED,
    _LOG_MSG_DISPATCH_ERROR,
    _INDENT_LEVEL_0,
    _INDENT_LEVEL_1,
    _INDENT_LEVEL_2,
)


class zWizard:
    """Core loop engine for stepped execution in Wizard and Walker modes."""

    # Type hints for instance attributes
    zcli: Optional[Any]
    walker: Optional[Any]
    zSession: Dict[str, Any]
    logger: Any
    display: Optional[Any]
    schema_cache: Optional[Any]

    def __init__(self, zcli: Optional[Any] = None, walker: Optional[Any] = None) -> None:
        """Initialize zWizard subsystem with either zcli or walker instance."""
        # Support both zcli and walker instances
        if zcli:
            self.zcli = zcli
            self.walker = walker
            self.zSession = zcli.session
            self.logger = zcli.logger
            self.display = zcli.display
            # Get schema_cache from cache orchestrator
            self.schema_cache = zcli.loader.cache.schema_cache
        elif walker:
            self.zcli = None
            self.walker = walker
            self.zSession = getattr(walker, "zSession", None)
            if not self.zSession:
                raise WizardInitializationError("zWizard requires a walker with a session")
            # Walker should always have a logger from zcli
            if not hasattr(walker, "logger"):
                raise WizardInitializationError("zWizard requires a walker with a logger")
            self.logger = walker.logger
            self.display = getattr(walker, "display", None)
            # Get schema_cache from walker's loader (if available)
            if hasattr(walker, 'loader') and hasattr(walker.loader, 'cache'):
                self.schema_cache = walker.loader.cache.schema_cache
            else:
                self.schema_cache = None
        else:
            raise WizardInitializationError(ERR_MISSING_INSTANCE)

        # Display ready message (only for direct zWizard instances, not subclasses like zWalker)
        if self.display and self.__class__.__name__ == "zWizard":
            self.display.zDeclare(_MSG_READY, color=SUBSYSTEM_COLOR, indent=0, style="full")

    def execute_loop(
        self, 
        items_dict: Dict[str, Any], 
        dispatch_fn: Optional[Any] = None, 
        navigation_callbacks: Optional[Dict[str, Any]] = None, 
        context: Optional[Dict[str, Any]] = None, 
        start_key: Optional[str] = None,
        ws_callback: Optional[Any] = None,
        block_name: Optional[str] = None
    ) -> Any:
        """
        Core loop engine that iterates through keys, dispatches actions, and handles results.
        
        This is the heart of zWizard - a flexible loop engine that executes ordered steps
        with automatic RBAC enforcement, navigation handling, and error recovery.
        
        Supports two execution modes:
        - Terminal: Sequential blocking execution
        - Bifrost: Chunked progressive execution at ! (gate) boundaries
        
        Args:
            items_dict: Ordered dictionary of step keys and values (or file structure if block_name provided)
            dispatch_fn: Optional custom dispatch function (defaults to zcli.dispatch)
            navigation_callbacks: Optional callbacks for navigation events
            context: Optional context passed to all dispatch calls
            start_key: Optional key to start from (for resuming workflows)
            ws_callback: Optional WebSocket callback for Bifrost chunked rendering
            block_name: Optional block name to extract from items_dict before processing
        
        Returns:
            Navigation signal (zBack, exit, stop, error) or None for normal completion
        
        Examples:
            >>> # Example 1: Basic workflow execution
            >>> wizard = zWizard(zcli=zcli_instance)
            >>> workflow = {
            ...     "welcome": {"type": "zDisplay", "message": "Welcome!"},
            ...     "get_name": {"type": "zDialog", "prompt": "Name?"},
            ...     "greet": {"type": "zDisplay", "message": "Hello!"}
            ... }
            >>> result = wizard.execute_loop(workflow)
            >>> # Returns None (normal completion)
            
            >>> # Example 2: With navigation callbacks
            >>> def handle_error(error, key):
            ...     print(f"Error in {key}: {error}")
            ...     return "error"
            >>> 
            >>> callbacks = {"on_error": handle_error, "on_back": lambda sig: "zBack"}
            >>> result = wizard.execute_loop(workflow, navigation_callbacks=callbacks)
            >>> if result == "error":
            ...     print("Workflow stopped due to error")
            
            >>> # Example 3: Resume from checkpoint
            >>> result = wizard.execute_loop(workflow, start_key="greet")
            >>> # Skips "welcome" and "get_name", starts at "greet"
            
            >>> # Example 4: Custom dispatch function
            >>> def custom_dispatch(key, value):
            ...     print(f"Executing: {key}")
            ...     return zcli.dispatch.handle(key, value)
            >>> 
            >>> result = wizard.execute_loop(workflow, dispatch_fn=custom_dispatch)
            
            >>> # Example 5: With context
            >>> context = {"user_id": 42, "debug_mode": True}
            >>> result = wizard.execute_loop(workflow, context=context)
            >>> # Context passed to all dispatch calls
        
        Navigation:
            - Returns None: Normal completion (all steps executed)
            - Returns "zBack": User requested to go back
            - Returns "exit": User requested to exit
            - Returns "stop": Execution stopped
            - Returns "error": Error occurred (if callback returns it)
        
        RBAC:
            Steps with `zRBAC` metadata are checked before execution.
            Denied steps are skipped automatically and logged.
        
        See Also:
            - handle(): Higher-level method with transaction support
            - wizard_examples.py: Comprehensive usage patterns
        """
        # ════════════════════════════════════════════════════════════
        # BLOCK EXTRACTION: Extract specific block if requested
        # ════════════════════════════════════════════════════════════
        # If block_name is provided, extract that specific block from items_dict
        # This allows orchestrators (like zWalker) to process file-level structures
        # without needing to implement extraction logic themselves
        if block_name:
            if block_name in items_dict:
                self.logger.debug(f"[zWizard] Extracting block: {block_name}")
                items_dict = items_dict[block_name]
            else:
                self.logger.warning(f"[zWizard] Block '{block_name}' not found, processing all keys")
        
        # ════════════════════════════════════════════════════════════
        # MODE DETECTION: Route to appropriate execution strategy
        # ════════════════════════════════════════════════════════════
        # Bifrost mode uses chunked execution (progressive rendering at ! gates)
        # Terminal mode uses sequential blocking execution
        from zOS.L1_Foundation.a_zConfig.zConfig_modules import ZMODE_ZBIFROST
        mode = self.zcli.session.get("zMode", "Terminal")
        
        if mode == ZMODE_ZBIFROST:
            # Bifrost chunked execution (generator-based progressive rendering)
            self.logger.debug("[zWizard] Using chunked execution for Bifrost mode")
            return self._execute_loop_chunked(
                items_dict, dispatch_fn, navigation_callbacks, context, start_key, ws_callback
            )
        
        # Terminal sequential execution (default)
        self.logger.debug("[zWizard] Using sequential execution for Terminal mode")
        
        # ════════════════════════════════════════════════════════════
        # BLOCK-LEVEL RBAC: Gate for entire workflow/block
        # ════════════════════════════════════════════════════════════
        # Check if the entire block has RBAC requirements (zRBAC at block level)
        # This gate must pass BEFORE entering the loop
        rbac_signal = self._check_blockzRBAC(items_dict)
        if rbac_signal is not None:
            return rbac_signal
        
        # ════════════════════════════════════════════════════════════
        # BLOCK-LEVEL DATA RESOLUTION (v1.5.12 - Flask/Jinja Pattern)
        # ════════════════════════════════════════════════════════════
        # CRITICAL: Resolve _data BEFORE creating dispatch_fn!
        # This ensures dispatch_fn captures the enriched context with query results.
        #
        # Flow:
        #   1. Wizard detects _data in block
        #   2. Resolves queries via zData, populating context["_resolved_data"]
        #   3. Creates dispatch_fn that captures enriched context
        #   4. Wizard iterates children, passing enriched context to each
        #   5. Children can now use %data.user.name in templates
        #
        # This mimics Flask's pattern:
        #   @app.route('/account')
        #   def account():
        #       user = User.query.filter_by(email=session['email']).first()
        #       return render_template('account.html', user=user)
        #
        # But in zCLI, it's declarative:
        #   zAccount:
        #     _data:
        #       user: "@.models.zSchema.contacts"
        #     ProfileCard:
        #       - zDisplay:
        #           event: text
        #           content: "Welcome %data.user.name"
        
        if "_data" in items_dict:
            self.logger.info("[zWizard] Detected _data block, resolving queries before loop execution")
            # Initialize context if not provided
            if context is None:
                context = {}
            
            # Call dispatch's _resolve_block_data directly to avoid double-processing
            # This resolves data queries and populates context["_resolved_data"]
            # WITHOUT recursing into children (wizard loop handles children)
            try:
                resolved_data = self.zcli.dispatch.launcher._resolve_block_data(
                    items_dict["_data"], 
                    context
                )
                if resolved_data:
                    if "_resolved_data" not in context:
                        context["_resolved_data"] = {}
                    context["_resolved_data"].update(resolved_data)
                    self.logger.info(f"[zWizard] Resolved {len(resolved_data)} data queries, context enriched")
                else:
                    self.logger.warning("[zWizard] _data block present but no data resolved")
            except Exception as e:
                self.logger.error(f"[zWizard] Error resolving _data: {e}")
        
        # NOW create dispatch_fn with the enriched context
        dispatch_fn = self._get_dispatch_fn(dispatch_fn, context)
        
        # Filter out metadata keys (underscore prefix) - they don't execute, only configure
        keys_list = self._filter_keys(items_dict)
        idx = keys_list.index(start_key) if start_key and start_key in keys_list else 0

        # Main loop
        while idx < len(keys_list):
            key = keys_list[idx]
            value = items_dict[key]

            self.logger.debug(_LOG_MSG_PROCESSING_KEY, key)
            if self.display:
                self.display.zDeclare(_MSG_ZKEY_DISPLAY % key, color=_COLOR_MAIN, indent=_INDENT_LEVEL_2, style=_STYLE_SINGLE)

            # ════════════════════════════════════════════════════════════
            # SHORTHAND SYNTAX EXPANSION (zH1-zH6, zText, zImage, etc.)
            # ════════════════════════════════════════════════════════════
            # Expand shorthand display events BEFORE dispatch
            if isinstance(value, dict):
                if key == 'zImage':
                    value = {'zDisplay': {'event': 'image', **value}}
                elif key == 'zURL':
                    value = {'zDisplay': {'event': 'zURL', **value}}
                elif key.startswith('zH') and len(key) == 3 and key[2].isdigit():
                    indent_level = int(key[2])
                    if 1 <= indent_level <= 6:
                        value = {'zDisplay': {'event': 'header', 'indent': indent_level, **value}}
                elif key == 'zText':
                    value = {'zDisplay': {'event': 'text', **value}}
                elif key == 'zUL':
                    # Check for plural shorthand first (zURLs, zTexts, etc.)
                    if isinstance(value, dict):
                        plural_shorthands = ['zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs']
                        has_plural = any(ps in value for ps in plural_shorthands)
                        if has_plural:
                            # Don't wrap - let dispatch_launcher handle the plural expansion
                            pass
                        else:
                            value = {'zDisplay': {'event': 'list', 'style': 'bullet', **value}}
                elif key == 'zOL':
                    # Check for plural shorthand first (zURLs, zTexts, etc.)
                    if isinstance(value, dict):
                        plural_shorthands = ['zURLs', 'zTexts', 'zH1s', 'zH2s', 'zH3s', 'zH4s', 'zH5s', 'zH6s', 'zImages', 'zMDs']
                        has_plural = any(ps in value for ps in plural_shorthands)
                        if has_plural:
                            # Don't wrap - let dispatch_launcher handle the plural expansion
                            pass
                        else:
                            value = {'zDisplay': {'event': 'list', 'style': 'number', **value}}
                elif key == 'zTable':
                    value = {'zDisplay': {'event': 'zTable', **value}}
                elif key == 'zMD':
                    value = {'zDisplay': {'event': 'rich_text', **value}}

            # ════════════════════════════════════════════════════════════
            # RBAC Enforcement (v1.5.4 Week 3.3)
            # ════════════════════════════════════════════════════════════
            # Check if this item has RBAC requirements
            rbac_check_result = checkzRBAC_access(
                key, value, self.zcli, self.walker, self.logger, self.display
            )
            if rbac_check_result == RBAC_ACCESS_DENIED:
                # Skip this item and move to next
                idx += 1
                continue

            # Execute action via dispatch
            try:
                result = dispatch_fn(key, value)
            except Exception as e:
                error_result = self._handle_dispatch_error(e, key, navigation_callbacks)
                if error_result is not None:
                    return error_result
                continue

            # Check if result is a key jump (e.g., menu selection)
            if isinstance(result, str) and result in keys_list and result not in NAVIGATION_SIGNALS:
                self.logger.debug(_LOG_MSG_MENU_SELECTED, result)
                
                # ════════════════════════════════════════════════════════════
                # Breadcrumb Tracking for Menu Navigation (Option C: POP Semantics)
                # ════════════════════════════════════════════════════════════
                # Track menu navigation in breadcrumbs with hierarchical semantics:
                # - Child menus/items: APPEND
                # - Parent menus (with ~*): POP back to parent level
                
                if self.zcli and hasattr(self.zcli, 'navigation'):
                    # Determine if selected key is a parent menu (contains both ~ and *)
                    is_parent_menu = ('~' in result and '*' in result)
                    
                    # Check current position to determine operation
                    current_idx = keys_list.index(key) if key in keys_list else -1
                    selected_idx = keys_list.index(result)
                    
                    # If going backwards to a parent menu (anchored menu), POP
                    # If going forward or to a sibling, APPEND
                    if is_parent_menu and selected_idx < current_idx:
                        # Returning to parent menu - POP to that level
                        self.logger.debug(f"[Menu Nav] Returning to parent menu '{result}' - POP operation")
                        self.zcli.navigation.handle_zCrumbs(
                            result,
                            walker=None,  # Breadcrumbs is self-aware
                            operation='POP_TO'  # Special operation to POP to a specific key
                        )
                    else:
                        # Moving to child or sibling - APPEND
                        self.logger.debug(f"[Menu Nav] Navigating to '{result}' - APPEND operation")
                        self.zcli.navigation.handle_zCrumbs(
                            result,
                            walker=None,  # Breadcrumbs is self-aware
                            operation='APPEND'
                        )
                
                idx = keys_list.index(result)
                continue

            # Handle navigation result
            nav_result = self._handle_navigation_result(result, key, navigation_callbacks)
            if nav_result is not None:
                return nav_result

            # Continue to next key
            if navigation_callbacks and 'on_continue' in navigation_callbacks:
                navigation_callbacks['on_continue'](result, key)

            if self.display:
                self.display.zDeclare("process_keys => next zKey", color="MAIN", indent=1, style="single")

            # ════════════════════════════════════════════════════════════
            # Menu Looping: Check if we should return to a menu
            # ════════════════════════════════════════════════════════════
            # After executing a menu selection (key jump), check if there's
            # a menu in this block that we should loop back to, instead of
            # continuing sequentially through the keys.
            
            # Search backwards from current position for a menu key
            menu_idx = None
            for i in range(idx - 1, -1, -1):
                check_key = keys_list[i]
                # Detect menu pattern: contains both ~ (anchor) and * (menu) modifiers
                if '~' in check_key and '*' in check_key:
                    menu_idx = i
                    break
            
            if menu_idx is not None:
                # Found a menu - loop back to it for next selection
                self.logger.debug(f"Menu detected at index {menu_idx}, looping back to: {keys_list[menu_idx]}")
                idx = menu_idx
                continue
            
            # Normal sequential processing (no menu found)
            idx += 1

        return None
    
    def _execute_loop_chunked(
        self,
        items_dict: Dict[str, Any],
        dispatch_fn: Optional[Any] = None,
        navigation_callbacks: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        start_key: Optional[str] = None,
        ws_callback: Optional[Any] = None
    ):
        """
        Generator-based chunked execution for Bifrost mode - progressive rendering at ! gates.
        
        This generator yields chunks of keys at ! (gate) boundaries, allowing the bridge
        to send progressive HTML to the frontend via WebSocket. Each chunk is rendered
        and sent before the next chunk begins execution.
        
        Generator Pattern:
            - Yields: (chunk_keys, is_gate) tuples for bridge to render and send
            - Receives: Result from gate execution (for ! retry logic)
            - Returns: Final navigation signal or None
        
        Args:
            items_dict: Ordered dictionary of step keys and values
            dispatch_fn: Optional custom dispatch function
            navigation_callbacks: Optional callbacks for navigation events
            context: Optional context passed to all dispatch calls
            start_key: Optional key to start from
            ws_callback: Unused (kept for signature compatibility)
        
        Yields:
            Tuple[List[str], bool, Any]: (chunk_keys, is_gate, gate_value)
            - chunk_keys: List of keys in this chunk
            - is_gate: True if chunk ends with ! gate
            - gate_value: The value dict for the gate (for form rendering)
        
        Receives (via send()):
            Result from gate execution (success/failure for retry logic)
        
        Returns:
            Navigation signal or None for normal completion
        
        Security:
            Only keys up to the gate are sent to frontend - post-gate content
            is NOT exposed until gate succeeds. This maintains RBAC and prevents
            data leakage.
        
        Example:
            # Bridge code:
            gen = wizard._execute_loop_chunked(block_dict, ...)
            for chunk_keys, is_gate, gate_value in gen:
                html = render_keys(chunk_keys)
                await ws.send({'event': 'render_chunk', 'html': html})
                if is_gate:
                    result = await wait_for_form_submit()
                    gen.send(result)  # Resume with result
        """
        from zOS.L1_Foundation.a_zConfig.zConfig_modules import ZMODE_ZBIFROST
        
        self.logger.info("[zWizard] ⚡ Generator-based chunked execution for Bifrost")
        
        # Block-level RBAC check
        rbac_signal = self._check_blockzRBAC(items_dict)
        if rbac_signal is not None:
            # Yield a special error chunk so the frontend can display the denial message
            # The buffered display events contain the formatted RBAC denial message
            # We yield an empty chunk list with special metadata to signal "RBAC_DENIED"
            self.logger.info("[zWizard] Yielding RBAC denial chunk with buffered events")
            yield ([], False, {"zRBAC_denied": True, "_signal": "navigate_back"})
            return rbac_signal
        
        dispatch_fn = self._get_dispatch_fn(dispatch_fn, context)
        # Filter out metadata keys (_)
        # Note: Navbar keys (~zNavBar*) are now processed normally (not filtered)
        keys_list = self._filter_keys(items_dict)
        idx = keys_list.index(start_key) if start_key and start_key in keys_list else 0
        
        # Chunk accumulator
        current_chunk = []
        
        while idx < len(keys_list):
            key = keys_list[idx]
            value = items_dict[key]
            
            self.logger.debug(f"[zWizard.chunked] Processing key: {key}")
            
            # RBAC check
            rbac_check_result = checkzRBAC_access(
                key, value, self.zcli, self.walker, self.logger, self.display
            )
            if rbac_check_result == RBAC_ACCESS_DENIED:
                idx += 1
                continue
            
            # ════════════════════════════════════════════════════════════════
            # EXECUTE BLOCK LOGIC (v1.5.13 - Menu Support for Bifrost)
            # ════════════════════════════════════════════════════════════════
            # Before yielding keys for rendering, execute the block logic.
            # This allows modifiers (like *) to emit display events (like zMenu)
            # BEFORE the frontend tries to render them.
            #
            # Flow:
            #   1. Execute dispatch_fn (triggers menu logic, etc.)
            #   2. Check if result is None AND key has * modifier (menu)
            #   3. If menu pause, yield current chunk and stop (menu event already emitted)
            #   4. Otherwise, accumulate key for rendering
            #
            # NOTE: Navbar is filtered out of keys_list entirely (see line 876)
            # so it never reaches this execution loop.
            
            try:
                result = dispatch_fn(key, value)
                
                # Check if this is a menu (has * modifier) AND returned None (pause signal)
                # NOTE: Regular blocks (zDisplay, etc.) also return None, so we MUST check for *
                is_menu = '*' in key
                if result is None and is_menu:
                    self.logger.info(f"[zWizard.chunked] ⏸️  Menu '{key}' returned None - pausing for user interaction")
                    
                    # Add current key to chunk (it rendered a menu)
                    current_chunk.append(key)
                    
                    # Yield chunk with pause signal
                    yield (current_chunk, False, {"_paused": True})
                    
                    # Exit generator - wait for frontend to send continuation/selection
                    return None
                
            except Exception as error:
                self.logger.error(f"[zWizard.chunked] Error executing {key}: {error}")
                # Continue to next key instead of crashing
                idx += 1
                continue
            
            # Add key to current chunk
            current_chunk.append(key)
            
            # Check if this is a gate (! modifier)
            is_gate = '!' in key
            
            if is_gate:
                # Gate detected - yield chunk for rendering
                self.logger.info(f"[zWizard.chunked] 🚪 Gate: {key} - yielding chunk of {len(current_chunk)} keys")
                
                # Yield chunk to bridge for rendering (frontend will render the form)
                # Bridge will handle form submission and resume generator
                yield (current_chunk, True, value)
                
                # Start new chunk for post-gate content
                self.logger.info(f"[zWizard.chunked] ⏸️  Gate yielded - post-gate content will be sent after form submission")
                current_chunk = []
                idx += 1
                
            else:
                # Regular key - accumulate and continue
                # Will be sent in next chunk or at end
                idx += 1
        
        # Yield final chunk if any keys remain
        if current_chunk:
            self.logger.info(f"[zWizard.chunked] Final chunk: {current_chunk}")
            yield (current_chunk, False, None)
        
        return None

    def _get_dispatch_fn(self, dispatch_fn: Optional[Any], context: Optional[Dict[str, Any]]) -> Any:
        """Get or create dispatch function."""
        if dispatch_fn is not None:
            return dispatch_fn

        if self.walker:
            # FIX: Wrap the dispatch method to include walker parameter
            # Returning method reference directly (self.walker.dispatch.handle) loses walker context
            # when called as dispatch_fn(key, value) - walker defaults to None
            def walker_dispatch(key: str, value: Any) -> Any:
                # SPECIAL CASE: If key is "zWizard", wrap value back into {zWizard: value}
                # so dispatcher can properly route to _handle_wizard_dict
                if key == "zWizard":
                    return self.walker.dispatch.handle(key, {"zWizard": value}, context=context, walker=self.walker)
                return self.walker.dispatch.handle(key, value, context=context, walker=self.walker)
            return walker_dispatch

        # Fallback for standalone wizard instances (zcli.wizard)
        # Use zcli's dispatch instance with walker context
        def default_dispatch(key: str, value: Any) -> Any:
            walker = self.zcli.walker if self.zcli and hasattr(self.zcli, 'walker') else None
            # SPECIAL CASE: If key is "zWizard", wrap value back into {zWizard: value}
            # so dispatcher can properly route to _handle_wizard_dict
            if key == "zWizard":
                return self.zcli.dispatch.handle(key, {"zWizard": value}, context=context, walker=walker)
            return self.zcli.dispatch.handle(key, value, context=context, walker=walker)
        return default_dispatch

    def _handle_dispatch_error(self, error: Exception, key: str, navigation_callbacks: Optional[Dict[str, Any]]) -> Any:
        """Handle dispatch errors."""
        self.logger.error(_LOG_MSG_DISPATCH_ERROR, key, error, exc_info=True)
        if self.display:
            self.display.zDeclare(_MSG_DISPATCH_ERROR % key, color=_COLOR_ERROR, indent=_INDENT_LEVEL_1, style=_STYLE_FULL)

        if navigation_callbacks and _CALLBACK_ON_ERROR in navigation_callbacks:
            return navigation_callbacks[_CALLBACK_ON_ERROR](error, key)
        return None

    def _handle_navigation_result(self, result: Any, key: str, navigation_callbacks: Optional[Dict[str, Any]]) -> Any:
        """Handle navigation results (zBack, exit, stop, error, zLink)."""
        
        # Check for zLink navigation (must come before other dict checks)
        if isinstance(result, dict) and 'zLink' in result:
            # Route through dispatch to navigation subsystem
            # This will handle the navigation and return the signal to stop the current loop
            return self.dispatch.handle('zLink', result, walker=self.walker)
        
        # Normalize dict-based navigation signals to string signals
        # Some subsystems return {'exit': 'completed'} or similar structured data
        # We extract the signal key for hashable navigation handling
        if isinstance(result, dict) and len(result) == 1:
            signal_key = list(result.keys())[0]
            if signal_key in NAVIGATION_SIGNALS:
                self.logger.debug(f"[zWizard] Normalized dict signal {result} -> '{signal_key}'")
                result = signal_key
        
        # Map result types to callback names
        result_map = {
            _SIGNAL_ZBACK: _CALLBACK_ON_BACK,
            _SIGNAL_EXIT: _CALLBACK_ON_EXIT,
            _SIGNAL_STOP: _CALLBACK_ON_STOP,
            _SIGNAL_ERROR: _CALLBACK_ON_ERROR,
            _SIGNAL_EMPTY: _CALLBACK_ON_ERROR
        }

        # Check if result is hashable before lookup (navigation signals are primitives)
        # Non-signal results (dicts, lists, objects) pass through without navigation
        if not isinstance(result, (str, int, bool, type(None))):
            # Result is a complex type (dict, list, etc.) - not a navigation signal
            return None  # Pass through, not a navigation action
        
        callback_name = result_map.get(result)
        if callback_name and navigation_callbacks and callback_name in navigation_callbacks:
            args = (result, key) if callback_name == _CALLBACK_ON_ERROR else (result,)
            return navigation_callbacks[callback_name](*args)

        return result if result in result_map else None

    def _get_display(self) -> Optional[Any]:
        """Get display instance from zcli or walker."""
        if self.zcli:
            return self.zcli.display
        if self.walker and hasattr(self.walker, 'display'):
            return self.walker.display
        return None

    def _check_blockzRBAC(self, items_dict: Dict[str, Any]) -> Optional[str]:
        """
        Check block-level RBAC and return navigation signal if denied.
        
        Args:
            items_dict: Block dictionary to check RBAC for
        
        Returns:
            Navigation signal (_SIGNAL_ZBACK) if access denied, None if granted
        
        Notes:
            - Checks RBAC requirements at the block/workflow level
            - Displays access denied message with pause (Terminal mode)
            - Returns _SIGNAL_ZBACK for bounce-back navigation
            - Returns None for granted access (continue execution)
        """
        rbac_result = checkzRBAC_access(
            key="Block/Workflow",
            value=items_dict,
            zcli=self.zcli,
            walker=self.walker,
            logger=self.logger,
            display=self.display
        )
        
        if rbac_result == RBAC_ACCESS_DENIED:
            self.logger.warning("[zWizard] Block-level RBAC denied access")
            
            # Terminal mode: Add pause before bounce-back
            mode = self.zcli.session.get("zMode", "terminal")
            if mode != "bifrost":
                if self.display:
                    self.display.text("Press Enter to continue...", indent=1, break_after=True)
            
            return _SIGNAL_ZBACK
        
        # zGuest redirect (friendly, no pause - user is logged in)
        if rbac_result == RBAC_ACCESS_DENIED_ZGUEST:
            self.logger.info("[zWizard] Block-level zGuest redirect (user authenticated)")
            return _SIGNAL_ZBACK
        
        return None

    def _filter_keys(self, items_dict: Dict[str, Any]) -> list:
        """
        Filter metadata keys (underscore prefix) from items dictionary.
        
        Args:
            items_dict: Dictionary of wizard steps/items
        
        Returns:
            List of keys excluding metadata keys (those starting with '_')
        
        Notes:
            - Metadata keys like _data, zRBAC, _transaction configure behavior
            - They don't execute as steps, only configure the workflow
            - This ensures only actionable keys are processed in the loop
        """
        return [k for k in items_dict.keys() if not k.startswith('_')]

    def _execute_step(self, step_key: str, step_value: Any, step_context: Dict[str, Any]) -> Any:
        """Execute a single wizard step."""
        # DEBUG: Log step context to diagnose zHat passing
        self.logger.debug(f"[_execute_step] step_key: {step_key}, context keys: {step_context.keys() if step_context else 'None'}")
        if step_context and "zHat" in step_context:
            self.logger.debug(f"[_execute_step] zHat in context: {step_context['zHat']}")
        
        if self.walker:
            # Use walker's dispatch instance
            return self.walker.dispatch.handle(step_key, step_value, context=step_context)
        
        # Shell mode - use shell's wizard step executor via CLI instance
        return self.zcli.shell.executor.execute_wizard_step(step_key, step_value, step_context)

    def handle(self, zWizard_obj: Dict[str, Any]) -> Optional[Any]:
        """
        Execute a sequence of wizard steps with persistent connections and transactions.
        
        This is the high-level entry point for YAML-based wizards. It provides automatic:
        - WizardHat result accumulation (triple-access: numeric, key, attribute)
        - zHat template variable interpolation
        - Transaction management (commit/rollback)
        - Schema cache connection reuse
        - Meta key filtering (_transaction, _config, etc.)
        
        Args:
            zWizard_obj: Dictionary of wizard steps (from YAML or dict)
        
        Returns:
            WizardHat object containing all step results (triple-access)
            - result[0], result[1]: Numeric access
            - result["step_name"]: Key-based access
            - result.step_name: Attribute access
        
        Examples:
            >>> # Example 1: Basic workflow
            >>> wizard = zWizard(zcli=zcli_instance)
            >>> workflow = {
            ...     "step1": {"type": "zFunc", "function": "get_data"},
            ...     "step2": {"type": "zDisplay", "message": "Processing..."},
            ...     "step3": {"type": "zFunc", "function": "save_data"}
            ... }
            >>> result = wizard.handle(workflow)
            >>> print(result[0])  # First step result
            >>> print(result["step1"])  # Same result by name
            >>> print(result.step1)  # Same result by attribute
            
            >>> # Example 2: With zHat interpolation
            >>> workflow = {
            ...     "get_user": {"type": "zFunc", "function": "fetch_user", "args": [42]},
            ...     "greet": {
            ...         "type": "zDisplay",
            ...         "message": "Hello {{ zHat.get_user.name }}!"  # Interpolation!
            ...     }
            ... }
            >>> result = wizard.handle(workflow)
            >>> # Step2 receives interpolated message with user name
            
            >>> # Example 3: Transactional workflow
            >>> workflow = {
            ...     "_transaction": True,  # Enable transaction mode
            ...     "create_team": {
            ...         "zData": {
            ...             "model": "$teams",  # Transaction starts
            ...             "operation": "create",
            ...             "data": {"name": "Engineering"}
            ...         }
            ...     },
            ...     "add_members": {
            ...         "zData": {
            ...             "model": "$teams",  # Same transaction
            ...             "operation": "update",
            ...             "where": {"id": "{{ zHat.create_team.id }}"},
            ...             "data": {"member_count": 5}
            ...         }
            ...     }
            ... }
            >>> result = wizard.handle(workflow)
            >>> # Both operations committed atomically
            >>> print(f"Team ID: {result.create_team.id}")
            
            >>> # Example 4: Error handling with rollback
            >>> try:
            ...     result = wizard.handle(workflow)
            ... except Exception as e:
            ...     print(f"Workflow failed, transaction rolled back: {e}")
            
            >>> # Example 5: YAML-based workflow
            >>> # In workflow.yaml:
            >>> # _transaction: true
            >>> # fetch_data:
            >>> #   zFunc:
            >>> #     function: get_data
            >>> #     args: [100]
            >>> # 
            >>> # process_data:
            >>> #   zFunc:
            >>> #     function: process
            >>> #     args: ["{{ zHat.fetch_data }}"]
            >>> 
            >>> workflow = zcli.parser.load_yaml("workflow.yaml")
            >>> result = wizard.handle(workflow)
            >>> print(f"Processed {len(result)} steps")
        
        Features:
            - **WizardHat**: Results accumulate in triple-access container
            - **Interpolation**: Use {{ zHat.step_name }} to reference results
            - **Transactions**: Atomic multi-step operations with automatic rollback
            - **Meta Keys**: Keys starting with _ are filtered (configuration only)
            - **Schema Cache**: Database connections reused across steps
        
        Meta Keys:
            - _transaction (bool): Enable transaction mode
            - _config (Any): Configuration (not executed)
            - Any key starting with "_" is treated as metadata
        
        Transaction Flow:
            1. Detect _transaction: true
            2. Find first $model in zData step
            3. Start transaction with that alias
            4. Execute all steps with shared transaction
            5. On success: Commit transaction
            6. On error: Rollback transaction
            7. Always: Clean up schema cache
        
        See Also:
            - execute_loop(): Lower-level loop engine
            - wizard_examples.py: Comprehensive usage patterns
            - WizardHat: Triple-access result container
        """
        display = self._get_display()
        if display:
            display.zDeclare(_MSG_HANDLE_WIZARD, color=SUBSYSTEM_COLOR, indent=_INDENT_LEVEL_1, style=_STYLE_FULL)

        try:
            zHat = WizardHat()  # Use dual-access container
            use_transaction = zWizard_obj.get("_transaction", False)
            transaction_alias = None
            
            # NEW v1.5.12: Initialize context for entire workflow
            step_context = {
                _CONTEXT_KEY_WIZARD_MODE: True,
                _CONTEXT_KEY_SCHEMA_CACHE: self.schema_cache,
                _CONTEXT_KEY_ZHAT: zHat  # Pass zHat to context for zFunc access
            } if self.schema_cache else {_CONTEXT_KEY_WIZARD_MODE: True, _CONTEXT_KEY_ZHAT: zHat}
            
            # NEW v1.5.12: BLOCK-LEVEL DATA RESOLUTION (Flask pattern)
            # If block has _data, resolve queries BEFORE processing steps
            # This enables declarative data layer: data queries at block level, 
            # variable interpolation (%data.*) in step templates
            if "_data" in zWizard_obj:
                self.logger.info("[zWizard] Detected _data block, resolving queries...")
                # Call _resolve_block_data DIRECTLY instead of _launch_dict
                # (which would recursively execute all children)
                if self.walker:
                    # Walker mode: Use walker's dispatch launcher
                    resolved_data = self.walker.dispatch.launcher._resolve_block_data(
                        zWizard_obj["_data"], step_context
                    )
                else:
                    # Shell mode: Use zcli's dispatch launcher
                    resolved_data = self.zcli.dispatch.launcher._resolve_block_data(
                        zWizard_obj["_data"], step_context
                    )
                
                # Populate context with resolved data
                if resolved_data:
                    if "_resolved_data" not in step_context:
                        step_context["_resolved_data"] = {}
                    step_context["_resolved_data"].update(resolved_data)
                    self.logger.info(f"[zWizard] Context enriched with {len(resolved_data)} data queries: {list(resolved_data.keys())}")
                else:
                    self.logger.warning("[zWizard] _data block detected but no data was resolved!")

            for step_key, step_value in zWizard_obj.items():
                if step_key.startswith("_"):
                    continue

                if display:
                    display.zDeclare(_MSG_WIZARD_STEP % step_key, color=SUBSYSTEM_COLOR, indent=_INDENT_LEVEL_2, style=_STYLE_SINGLE)

                step_value = interpolate_zhat(step_value, zHat, self.logger)
                
                # Context is now pre-populated with _resolved_data if _data block existed

                if transaction_alias is None:
                    transaction_alias = check_transaction_start(
                        use_transaction, transaction_alias, step_value,
                        self.schema_cache, self.logger
                    )

                result = self._execute_step(step_key, step_value, step_context)
                zHat.add(step_key, result)  # Add with key for dual access

            commit_transaction(use_transaction, transaction_alias, self.schema_cache, self.logger)
            self.logger.debug("zWizard completed with zHat: %s", zHat)
            return zHat

        except Exception as e:  # pylint: disable=broad-except
            rollback_transaction(use_transaction, transaction_alias, self.schema_cache, self.logger, e)
            raise
        finally:
            if self.schema_cache:
                self.schema_cache.clear()
                self.logger.debug("Schema cache connections cleared")
