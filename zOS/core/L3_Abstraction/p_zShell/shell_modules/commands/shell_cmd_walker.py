# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_walker.py

"""
Shell Walker Command Executor.

This module provides the shell command interface for launching the zWalker subsystem,
which enables declarative stepped execution through zVaFile blocks. The walker command
validates session configuration, builds zSpark context, and launches walker sessions
while preserving mode and session state.

OVERVIEW:
    The 'walker run' command launches a walker session using configuration stored in
    the session dictionary. Walker provides interactive, stepped navigation through
    declarative UI blocks defined in zVaFiles, supporting both Terminal and zBifrost
    modes with full zAuth context awareness.

WALKER VS WIZARD:
    • Walker: User-facing stepped execution (declarative, menu-driven, YAML-defined)
    • Wizard: Developer-facing loop engine (programmatic, buffer-based, code-driven)
    
    Walker extends Wizard for end-users navigating through zUI blocks. Wizard provides
    the core loop infrastructure that Walker builds upon for declarative UX.

COMMAND SYNTAX:
    walker run              # Launch walker with session configuration
    
    Required session fields:
        - zSpace: Workspace root directory
        - zVaFile: Active zVaFile name (e.g., "zUI.users")
        - zVaFolder: Folder containing zVaFile (e.g., "@.data")
        - zBlock: Starting block name (e.g., "Root", "Help")

SESSION REQUIREMENTS:
    Walker is session-driven - it reads configuration from 4 required session keys:
    
    1. SESSION_KEY_ZSPACE: Workspace root (constant "home base")
       Example: "/Users/name/Projects/myapp"
       
    2. SESSION_KEY_ZVAFILE: Active zVaFile name (without extension)
       Example: "zUI.users"
       
    3. SESSION_KEY_ZVAFOLDER: Folder containing zVaFile (zPath notation)
       Example: "@.data" or "~zMachine.zUIs"
       
    4. SESSION_KEY_ZBLOCK: Starting block for walker
       Example: "Root", "Help", "UserMenu"
    
    Use 'session set <key> <value>' to configure these fields before running walker.

WALKER FLOW:
    1. Validation: Check all 4 required session fields are set
    2. Mode Preservation: Store current zMode (Terminal/zBifrost)
    3. zSpark Build: Construct full zPath and update zspark_obj
    4. Walker Launch: Import and instantiate zWalker with zcli
    5. Execution: Walker runs until exit/stop signal
    6. Mode Restore: Defensively restore original zMode

ZAUTH AWARENESS:
    Walker inherits zAuth context from session (SESSION_KEY_ZAUTH). When navigating
    through zVaFile blocks, walker respects RBAC protection enforced by zNavigation.
    Auth validation is handled by the navigation layer, not the walker command itself.
    
    Protected blocks require active auth context:
        - Admin-only blocks check role permissions
        - Tier-specific content filtered by auth level
        - Unauthorized access triggers navigation errors
    
    No explicit auth check in walker command - zAuth context flows through session
    and is validated downstream by zNavigation when loading protected blocks.

MODE HANDLING:
    Walker preserves the session's zMode (Terminal or zBifrost) throughout execution.
    The mode determines output display (terminal vs WebSocket) but walker logic is
    mode-agnostic. Mode restoration after walker exit is defensive programming to
    guard against edge cases where walker might mutate session state.

ZSPARK CONFIGURATION:
    Walker updates zspark_obj (zSpark context) with session configuration:
        - zSpace: Workspace root for path resolution
        - zVaFile: Full zPath to file (zVaFolder.zVaFile, no <zBlock> suffix)
        - zVaFolder: Folder path for relative resolution
        - zBlock: Starting block (applied after file loads)
        - zMode: Terminal/zBifrost (preserved from session)
    
    zSpark provides initialization context to subsystems. Walker sets these fields
    before launching so zLoader, zNavigation, and zDispatch have correct context.

ARCHITECTURE:
    Shell commands act as UI adapters, not programmatic APIs:
    • execute_walker(): Main entry point, orchestrates walker launch
    • _validate_walker_session(): Validates required session fields
    • _build_walker_zspark(): Constructs zSpark from session config
    • _restore_session_mode(): Defensive mode restoration after walker exits
    
    Returns None on success (or when walker exits), displays directly via zDisplay.
    For programmatic walker access, use zWalker subsystem directly.

UI ADAPTER PATTERN:
    This command follows the shell UI adapter pattern:
    • Returns None on success (walker completed)
    • Returns error dict on validation failure (for shell_executor to display)
    • Uses zDisplay for user feedback (not dict returns)
    • No JSON output in terminal - user sees friendly messages only

TYPE SAFETY:
    All functions include comprehensive type hints using types imported from
    the zCLI namespace for consistency across the framework.

ERROR HANDLING:
    Gracefully handles missing session fields, walker import failures, walker
    crashes, and sys.exit() calls. Specific exception types ensure precise
    error reporting (ImportError, AttributeError, KeyError, Exception).

CROSS-SUBSYSTEM DEPENDENCIES:
    • zWalker: Walker subsystem (dynamic import, core execution engine)
    • zSession: Session state management (reads 4+ session keys)
    • zSpark: Initialization context (zspark_obj configuration)
    • zAuth: Authentication context (inherited from session, validated by zNavigation)
    • zDisplay: User feedback (error/success messages - future enhancement)
    • zConfig: Session constants (SESSION_KEY_*)

RELATED:
    • zWalker: Core walker subsystem for stepped execution
    • zWizard: Loop engine that walker extends
    • zNavigation: Handles block traversal and RBAC enforcement
    • shell_cmd_wizard: Shell command for wizard mode (buffer-based)
    • shell_cmd_help: Uses walker to display help menu

FUTURE ENHANCEMENTS:
    • --require-auth flag for explicit auth validation before launch
    • --mode flag to override session mode (force Terminal or zBifrost)
    • walker status: Show current walker state (active/inactive)
    • walker list: Show available walkers in workspace

Author: zOS Framework
Version: 1.5.4+
Module: zShell (Command Executors - Group C: zCLI Subsystem Integration)
"""

from zOS import Any, Dict, Optional

# Import SESSION_KEY_* constants from zConfig for refactor-proof session access
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import (
    SESSION_KEY_ZSPACE,
    SESSION_KEY_ZVAFILE,
    SESSION_KEY_ZVAFOLDER,
    SESSION_KEY_ZBLOCK,
    SESSION_KEY_ZMODE,
    SESSION_KEY_BROWSER,
    SESSION_KEY_IDE,
)

# ============================================================================
# MODULE CONSTANTS
# ============================================================================

# Action Constants
ACTION_RUN: str = "run"

# Dict Key Constants (from parser)
DICT_KEY_ACTION: str = "action"
DICT_KEY_ERROR: str = "error"
DICT_KEY_NOTE: str = "note"
DICT_KEY_SUCCESS: str = "success"
DICT_KEY_RESULT: str = "result"

# Default Values
DEFAULT_ZMODE: str = "Terminal"
DEFAULT_ZVAFOLDER: str = "@"
DEFAULT_ZBLOCK: str = "Root"

# Required Session Fields (for validation)
REQUIRED_FIELD_ZSPACE: str = "zSpace"
REQUIRED_FIELD_ZVAFILE: str = "zVaFile"
REQUIRED_FIELD_ZVAFOLDER: str = "zVaFolder"
REQUIRED_FIELD_ZBLOCK: str = "zBlock"

# Error Messages
MSG_MISSING_FIELDS: str = "Missing required session fields: {fields}"
MSG_MISSING_FIELDS_HINT: str = "Use 'session set <field> <value>' to configure Walker"
MSG_WALKER_IMPORT_FAILED: str = "Failed to import zWalker subsystem: {error}"
MSG_WALKER_LAUNCH_FAILED: str = "Walker launch failed: {error}"
MSG_UNKNOWN_ACTION: str = "Unknown walker command: {action}. Use: walker run"

# Success Messages
MSG_WALKER_COMPLETED: str = "Walker session completed"
MSG_WALKER_EXITED_NORMALLY: str = "Walker exited normally"
MSG_WALKER_EXIT_CODE: str = "Walker exited with code {code}"

# Log Messages
LOG_LAUNCHING_WALKER: str = "Launching Walker from session configuration..."
LOG_CREATING_WALKER: str = "Creating zWalker instance from zOS..."
LOG_STARTING_WALKER: str = "Starting Walker in %s mode..."
LOG_WALKER_EXITED: str = "Walker exited normally"
LOG_WALKER_EXIT_SYSEXIT: str = "Walker exited via sys.exit(%s)"
LOG_WALKER_ERROR: str = "Failed to launch Walker: %s"
LOG_MODE_RESTORED: str = "Restored session mode to: %s"

# Exit Code Constants
EXIT_CODE_SUCCESS: int = 0
EXIT_CODE_NONE: None = None


# ============================================================================
# PUBLIC API
# ============================================================================

def execute_walker(zcli: Any, parsed: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Execute walker commands like 'walker run'.
    
    Launches zWalker subsystem using session configuration. Validates required
    session fields (zSpace, zVaFile, zVaFolder, zBlock), builds zSpark context,
    and instantiates walker with full zcli access. Preserves session mode
    (Terminal/zBifrost) throughout execution.
    
    Args:
        zcli: zCLI instance with full subsystem access
            - zcli.session: Session dictionary (reads 4 required fields)
            - zcli.zspark_obj: zSpark context (updates with walker config)
            - zcli.logger: Logger instance (logs walker lifecycle)
            - zcli.display: zDisplay instance (future: user feedback)
        
        parsed: Parsed command dictionary from zParser
            - parsed["action"]: Command action (e.g., "run")
    
    Returns:
        None on success (walker completed or exited normally)
        Dict[str, str] on validation error (missing fields, import failure)
            {"error": "...", "note": "..."}
    
    Session Requirements:
        Walker requires 4 session fields to be set before launch:
        
        1. zSpace: Workspace root directory (absolute path)
           Set via: session set zSpace /path/to/workspace
           
        2. zVaFile: Active zVaFile name without extension
           Set via: session set zVaFile zUI.myapp
           
        3. zVaFolder: Folder containing zVaFile (zPath notation)
           Set via: session set zVaFolder @.data
           
        4. zBlock: Starting block name for walker
           Set via: session set zBlock Root
    
    Walker Flow:
        1. Read action from parsed command
        2. Validate all required session fields present
        3. Store current zMode for defensive restoration
        4. Build zSpark configuration from session
        5. Import zWalker subsystem (dynamic to avoid circular deps)
        6. Instantiate walker with zcli instance
        7. Launch walker.run() and wait for completion
        8. Handle exit signals (normal exit, sys.exit(), exceptions)
        9. Defensively restore original zMode to session
        10. Return success or error
    
    Mode Handling:
        Walker preserves session zMode (Terminal or zBifrost) throughout execution.
        After walker exits, mode is defensively restored to guard against edge cases
        where walker might mutate session state. This is defensive programming - the
        walker subsystem is designed to preserve mode, but restoration ensures session
        integrity regardless of walker behavior.
    
    zAuth Context:
        Walker inherits zAuth context from SESSION_KEY_ZAUTH in session. No explicit
        auth validation in this command - zAuth context flows through session and is
        validated downstream by zNavigation when loading RBAC-protected blocks.
    
    Examples:
        # Configure session (one-time setup)
        session set zSpace @.
        session set zVaFile zUI.users
        session set zVaFolder @.data
        session set zBlock Root
        
        # Launch walker
        walker run
        
        # Walker displays menu, user navigates blocks
        # On exit, returns to shell prompt
    
    Error Cases:
        - Missing session fields → Returns error dict with hint
        - Walker import failure → Returns error dict (zWalker not available)
        - Walker launch failure → Returns error dict with exception message
        - Walker sys.exit() → Caught gracefully, returns success or note
    
    Notes:
        • Walker sessions are interactive - user navigates through blocks
        • Walker respects session mode (Terminal displays in terminal, Bifrost via WebSocket)
        • Walker cache persists in session until sys.exit() (see zWalker.on_stop)
        • For programmatic walker access, import and use zWalker directly
    
    Related:
        • shell_cmd_help: Uses walker to display help menu
        • shell_cmd_wizard: Buffer-based wizard mode (developer-facing)
        • zWalker.run(): Core walker execution method
    """
    action = parsed[DICT_KEY_ACTION]
    
    if action == ACTION_RUN:
        # Log walker launch initiation
        zcli.logger.info(LOG_LAUNCHING_WALKER)
        
        # Validate required session fields (Phase 1)
        validation_error = _validate_walker_session(zcli)
        if validation_error:
            return validation_error
        
        # Store current mode for defensive restoration (Phase 2)
        current_mode = zcli.session.get(SESSION_KEY_ZMODE, DEFAULT_ZMODE)
        
        # Build zSpark configuration from session (Phase 3)
        _build_walker_zspark(zcli)
        
        # Import and launch Walker (Phase 4)
        try:
            from zOS.L4_Orchestration.q_zWalker.zWalker import zWalker
            
            zcli.logger.info(LOG_CREATING_WALKER)
            walker = zWalker(zcli)
            
            zcli.logger.info(LOG_STARTING_WALKER, current_mode)
            result = walker.run()
            
            # Walker exited normally - restore mode and return success
            zcli.logger.info(LOG_WALKER_EXITED)
            _restore_session_mode(zcli, current_mode)
            
            return {
                DICT_KEY_SUCCESS: MSG_WALKER_COMPLETED,
                DICT_KEY_RESULT: result
            }
            
        except ImportError as e:
            # zWalker subsystem not available (missing dependency)
            zcli.logger.error(LOG_WALKER_ERROR, e, exc_info=True)
            _restore_session_mode(zcli, current_mode)
            return {DICT_KEY_ERROR: MSG_WALKER_IMPORT_FAILED.format(error=str(e))}
            
        except SystemExit as e:
            # Walker called sys.exit() - this is normal for "stop" command
            zcli.logger.info(LOG_WALKER_EXIT_SYSEXIT, e.code)
            _restore_session_mode(zcli, current_mode)
            
            # Distinguish normal exit (0/None) from error exit (non-zero)
            if e.code == EXIT_CODE_SUCCESS or e.code == EXIT_CODE_NONE:
                return {DICT_KEY_SUCCESS: MSG_WALKER_EXITED_NORMALLY}
            else:
                return {DICT_KEY_NOTE: MSG_WALKER_EXIT_CODE.format(code=e.code)}
            
        except AttributeError as e:
            # Malformed zcli instance (missing expected attributes)
            zcli.logger.error(LOG_WALKER_ERROR, e, exc_info=True)
            _restore_session_mode(zcli, current_mode)
            return {DICT_KEY_ERROR: MSG_WALKER_LAUNCH_FAILED.format(error=str(e))}
            
        except KeyError as e:
            # Missing session key (shouldn't happen after validation, but defensive)
            zcli.logger.error(LOG_WALKER_ERROR, e, exc_info=True)
            _restore_session_mode(zcli, current_mode)
            return {DICT_KEY_ERROR: MSG_WALKER_LAUNCH_FAILED.format(error=str(e))}
            
        except Exception as e:
            # Catch-all for unexpected walker failures
            zcli.logger.error(LOG_WALKER_ERROR, e, exc_info=True)
            _restore_session_mode(zcli, current_mode)
            return {DICT_KEY_ERROR: MSG_WALKER_LAUNCH_FAILED.format(error=str(e))}
    
    else:
        # Unknown action (only "run" is supported currently)
        return {DICT_KEY_ERROR: MSG_UNKNOWN_ACTION.format(action=action)}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _validate_walker_session(zcli: Any) -> Optional[Dict[str, str]]:
    """
    Validate that all required session fields are set for walker launch.
    
    Checks session dictionary for 4 required fields: zSpace, zVaFile, zVaFolder,
    zBlock. If any are missing or empty, returns error dict with list of missing
    fields and configuration hint.
    
    Args:
        zcli: zCLI instance with session access
            - zcli.session: Session dictionary to validate
    
    Returns:
        None if validation passes (all required fields present and non-empty)
        Dict[str, str] if validation fails:
            {"error": "Missing required session fields: ...",
             "note": "Use 'session set <field> <value>' to configure Walker"}
    
    Validation Logic:
        For each required field (zSpace, zVaFile, zVaFolder, zBlock):
        1. Check if field exists in session
        2. Check if field value is truthy (not None, not empty string)
        3. Add to missing list if either check fails
    
    Session Field Details:
        - zSpace: Workspace root (SESSION_KEY_ZSPACE)
        - zVaFile: Active zVaFile name (SESSION_KEY_ZVAFILE)
        - zVaFolder: Folder containing zVaFile (SESSION_KEY_ZVAFOLDER)
        - zBlock: Starting block (SESSION_KEY_ZBLOCK)
    
    Examples:
        # All fields present - returns None (validation passes)
        session = {"zSpace": "/workspace", "zVaFile": "zUI.app", ...}
        _validate_walker_session(zcli)  # → None
        
        # Missing zBlock - returns error dict
        session = {"zSpace": "/workspace", "zVaFile": "zUI.app", "zVaFolder": "@."}
        _validate_walker_session(zcli)
        # → {"error": "Missing required session fields: zBlock",
        #    "note": "Use 'session set <field> <value>' to configure Walker"}
    
    Notes:
        • Uses SESSION_KEY_* constants for refactor-proof field access
        • Empty string ("") treated as missing (truthy check)
        • None treated as missing (truthy check)
        • Provides helpful hint for user to configure missing fields
    """
    # Define required fields using human-readable names (for error messages)
    required_fields = [
        REQUIRED_FIELD_ZSPACE,
        REQUIRED_FIELD_ZVAFILE,
        REQUIRED_FIELD_ZVAFOLDER,
        REQUIRED_FIELD_ZBLOCK
    ]
    
    # Check each field and collect missing ones
    missing = []
    for field in required_fields:
        # Map human-readable name to SESSION_KEY_* constant
        if field == REQUIRED_FIELD_ZSPACE:
            session_key = SESSION_KEY_ZSPACE
        elif field == REQUIRED_FIELD_ZVAFILE:
            session_key = SESSION_KEY_ZVAFILE
        elif field == REQUIRED_FIELD_ZVAFOLDER:
            session_key = SESSION_KEY_ZVAFOLDER
        elif field == REQUIRED_FIELD_ZBLOCK:
            session_key = SESSION_KEY_ZBLOCK
        else:
            session_key = field  # Fallback (shouldn't happen)
        
        # Check if field is missing or empty
        if not zcli.session.get(session_key):
            missing.append(field)
    
    # Return error if any fields are missing
    if missing:
        return {
            DICT_KEY_ERROR: MSG_MISSING_FIELDS.format(fields=", ".join(missing)),
            DICT_KEY_NOTE: MSG_MISSING_FIELDS_HINT
        }
    
    # All fields present - validation passed
    return None


def _build_walker_zspark(zcli: Any) -> None:
    """
    Build zSpark configuration from session and update zspark_obj.
    
    Reads walker configuration from session (4 required fields + mode), constructs
    full zPath from zVaFolder + zVaFile, and updates zcli.zspark_obj with walker
    initialization context. zSpark provides context to subsystems during walker
    execution.
    
    Args:
        zcli: zCLI instance with session and zspark_obj access
            - zcli.session: Session dictionary (reads 5 fields)
            - zcli.zspark_obj: zSpark context dict (updates 5 fields)
    
    Returns:
        None (updates zcli.zspark_obj in place)
    
    zSpark Fields Updated:
        1. zSpace: Workspace root (from SESSION_KEY_ZSPACE)
           Used by zLoader for workspace-relative path resolution
           
        2. zVaFile: Full zPath to file (zVaFolder.zVaFile, no <zBlock>)
           Example: "@.data.zUI.users" (not "@.data.zUI.users<Root>")
           Used by zLoader to locate and load the zVaFile
           
        3. zVaFolder: Folder path (from SESSION_KEY_ZVAFOLDER)
           Example: "@.data" or "~zMachine.zUIs"
           Used for relative path resolution within walker
           
        4. zBlock: Starting block name (from SESSION_KEY_ZBLOCK)
           Example: "Root", "Help", "UserMenu"
           Applied by zNavigation after file loads (separate from zVaFile path)
           
        5. zMode: Terminal or zBifrost (from SESSION_KEY_ZMODE)
           Determines output display mechanism (terminal or WebSocket)
    
    zPath Construction:
        Walker constructs full zPath by concatenating:
        zVaFolder + "." + zVaFile (no <zBlock> suffix)
        
        Example:
            zVaFolder: "@.data"
            zVaFile: "zUI.users"
            → Full zPath: "@.data.zUI.users"
        
        zBlock is separate - it's applied after zLoader loads the file.
        Including <zBlock> in zPath would confuse the loader.
    
    Default Values:
        If session fields are missing (shouldn't happen after validation), uses:
        - zVaFolder: "@" (workspace root)
        - zBlock: "Root" (default starting block)
        - zMode: "Terminal" (default mode)
    
    Examples:
        # Session configuration
        session = {
            "zSpace": "/Users/name/workspace",
            "zVaFile": "zUI.users",
            "zVaFolder": "@.data",
            "zBlock": "UserMenu",
            "zMode": "Terminal"
        }
        
        # After _build_walker_zspark(zcli)
        zspark_obj = {
            "zSpace": "/Users/name/workspace",
            "zVaFile": "@.data.zUI.users",  # Full zPath (no <UserMenu>)
            "zVaFolder": "@.data",
            "zBlock": "UserMenu",           # Separate - applied after load
            "zMode": "Terminal"
        }
    
    Notes:
        • Direct zspark_obj.update() is acceptable (public API pattern)
        • zBlock is NOT appended to zVaFile path (loader expects file path only)
        • zSpark context flows to zLoader, zNavigation, zDispatch
        • Session is read-only here (not mutated)
    """
    # Read session configuration with defaults
    zva_folder = zcli.session.get(SESSION_KEY_ZVAFOLDER, DEFAULT_ZVAFOLDER)
    zva_file = zcli.session[SESSION_KEY_ZVAFILE]  # Required (validated)
    zblock = zcli.session.get(SESSION_KEY_ZBLOCK, DEFAULT_ZBLOCK)
    current_mode = zcli.session.get(SESSION_KEY_ZMODE, DEFAULT_ZMODE)
    
    # Construct full zPath: zVaFolder.zVaFile (NO <zBlock> suffix)
    # Example: "@.data" + "." + "zUI.users" → "@.data.zUI.users"
    full_zpath = f"{zva_folder}.{zva_file}"
    
    # Update zSpark context for walker execution
    zcli.zspark_obj.update({
        SESSION_KEY_ZSPACE: zcli.session[SESSION_KEY_ZSPACE],  # Workspace root
        SESSION_KEY_ZVAFILE: full_zpath,     # Full zPath to file (e.g., "@.data.zUI.users")
        SESSION_KEY_ZVAFOLDER: zva_folder,   # Folder path for relative resolution
        SESSION_KEY_ZBLOCK: zblock,          # Starting block (applied after load)
        SESSION_KEY_ZMODE: current_mode      # Terminal or zBifrost
    })
    
    # Optionally update session with tool preferences from incoming zSpark
    # (allows programmatic walker launches to override browser/IDE)
    if "browser" in zcli.zspark_obj and zcli.zspark_obj["browser"] is not None:
        zcli.session[SESSION_KEY_BROWSER] = zcli.zspark_obj["browser"]
        zcli.logger.debug("Walker: session[browser] set from zSpark: %s", zcli.zspark_obj["browser"])
    
    if "ide" in zcli.zspark_obj and zcli.zspark_obj["ide"] is not None:
        zcli.session[SESSION_KEY_IDE] = zcli.zspark_obj["ide"]
        zcli.logger.debug("Walker: session[ide] set from zSpark: %s", zcli.zspark_obj["ide"])


def _restore_session_mode(zcli: Any, original_mode: str) -> None:
    """
    Defensively restore session zMode after walker exits.
    
    Updates SESSION_KEY_ZMODE in session to original value that was captured before
    walker launch. This is defensive programming - walker subsystem is designed to
    preserve mode, but restoration ensures session integrity in edge cases where
    walker might mutate mode state.
    
    Args:
        zcli: zCLI instance with session access
            - zcli.session: Session dictionary (updates zMode field)
            - zcli.logger: Logger instance (logs mode restoration)
        
        original_mode: Mode captured before walker launch
            Expected values: "Terminal" or "zBifrost"
    
    Returns:
        None (updates zcli.session[SESSION_KEY_ZMODE] in place)
    
    Rationale:
        Walker subsystem (zWalker) is designed to preserve zMode throughout execution.
        However, this restoration provides defensive protection against:
        1. Edge cases where walker code might mutate mode
        2. Plugin/extension code running within walker context
        3. Future walker enhancements that might need mode switching
        4. Exception paths that exit without proper cleanup
    
    Mode Values:
        - "Terminal": CLI terminal mode (stdout display)
        - "zBifrost": WebSocket mode (browser display)
    
    Examples:
        # Before walker launch
        current_mode = zcli.session.get("zMode", "Terminal")  # "Terminal"
        
        # Walker runs (might mutate mode in edge case)
        walker.run()  # Internally preserves mode, but defensive restoration needed
        
        # After walker exit - restore original
        _restore_session_mode(zcli, current_mode)
        # zcli.session["zMode"] → "Terminal" (guaranteed)
    
    Notes:
        • Called in all exit paths (success, sys.exit, exceptions)
        • Logs mode restoration at info level
        • Uses SESSION_KEY_ZMODE constant for refactor-proof access
        • Idempotent - safe to call multiple times with same mode
    """
    zcli.session[SESSION_KEY_ZMODE] = original_mode
    zcli.logger.info(LOG_MODE_RESTORED, original_mode)
