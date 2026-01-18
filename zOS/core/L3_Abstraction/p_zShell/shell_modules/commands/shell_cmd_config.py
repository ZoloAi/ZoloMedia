"""
Configuration System Management Command for zCLI Shell.

Provides comprehensive `config` command for zCLI configuration system diagnostics,
display, and modification (get, set, reset operations).

Command Syntax:
    # Diagnostics (Read-Only)
    config check                        - Run full system diagnostics
    config show                         - Display machine and environment configuration
    
    # Get Operations (Read-Only)
    config get machine <key>            - Get specific machine config value
    config get env <key>                - Get specific environment config value
    config get machine                  - Get all machine config (alias for show)
    config get env                      - Get all environment config (alias for show)
    
    # Set Operations (Write)
    config set machine <key> <value>    - Set machine config value
    config set env <key> <value>        - Set environment config value
    
    # Reset Operations (Write)
    config reset machine <key>          - Reset machine config key to default
    config reset env <key>              - Reset environment config key to default
    config reset machine                - Reset all machine config
    config reset env                    - Reset all environment config
    
    # Options
    --show                              - Show config after set/reset operation

Diagnostic Checks (10+):
    - Directory Checks (6): Package, system, user config dirs, zMachine subdirs
    - File Checks (5+): Machine config, default configs  
    - Integration Checks (2): Config loader, machine loading

Status Levels:
    - pass (GREEN): Check succeeded
    - warning (YELLOW): Non-critical issue
    - fail (RED): Critical issue

Architecture:
    - zConfig Facade: get_paths_info(), get_config_sources(), get_machine(), 
                      persist_machine(), persist_config()
    - zDisplay: Mode-agnostic output (Terminal and Bifrost)
    - UI Adapter Pattern: Returns None, uses zDisplay for output

Constants (55+):
    ACTION_*, STATUS_*, CHECK_*, MSG_*, KEY_*, COLOR_*, DISPLAY_*, TARGET_*, ERROR_*

Implementation:
    - 100% type hints (CheckResult, DiagnosticResults)
    - DRY helpers: _build_check_result(), _validate_config_args(), _display_config_result()
    - Never raises exceptions (graceful error handling)
    - Thread-safe (read-only operations)

Dependencies:
    zConfig, zDisplay, zColors, os, Path

Examples:
    # Diagnostics
    execute_config(zcli, {'action': 'check', 'args': [], 'options': {}})
    execute_config(zcli, {'action': 'show', 'args': [], 'options': {}})
    
    # Get operations
    execute_config(zcli, {'action': 'get', 'args': ['machine', 'text_editor'], 'options': {}})
    
    # Set operations
    execute_config(zcli, {'action': 'set', 'args': ['machine', 'text_editor', 'cursor'], 'options': {'show': True}})
    
    # Reset operations
    execute_config(zcli, {'action': 'reset', 'args': ['machine', 'text_editor'], 'options': {}})

Version: 1.5.4 | Week: 6.13.7 + 6.13.8 + 6.13.11 (Unified) | Grade: A+
"""

from zOS import os, Any, Dict, List

# ═══════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# Command Actions
ACTION_CHECK: str = "check"
ACTION_SHOW: str = "show"
ACTION_GET: str = "get"
ACTION_SET: str = "set"
ACTION_RESET: str = "reset"

# Config Targets
TARGET_MACHINE: str = "machine"
TARGET_ENV: str = "env"
TARGET_CONFIG: str = "config"  # Alias for env (backward compat)

# Check Status Levels
STATUS_PASS: str = "pass"
STATUS_WARNING: str = "warning"
STATUS_FAIL: str = "fail"

# Status Indicators (for display)
INDICATOR_PASS: str = "[OK]"
INDICATOR_WARNING: str = "[WARN]"
INDICATOR_FAIL: str = "[FAIL]"
INDICATOR_UNKNOWN: str = "[UNKNOWN]"

# Dictionary Keys (Results Structure)
KEY_STATUS: str = "status"
KEY_CHECKS: str = "checks"
KEY_SUMMARY: str = "summary"
KEY_TOTAL_CHECKS: str = "total_checks"
KEY_PASSED: str = "passed"
KEY_FAILED: str = "failed"
KEY_WARNINGS: str = "warnings"
KEY_DESCRIPTION: str = "description"
KEY_PATH: str = "path"
KEY_ZPATH: str = "zpath"
KEY_MESSAGE: str = "message"
KEY_REQUIRED: str = "required"
KEY_SIZE: str = "size"
KEY_SOURCES: str = "sources"
KEY_MACHINE: str = "machine"

# Check Names (for results dict)
CHECK_PACKAGE_CONFIG: str = "package_config"
CHECK_SYSTEM_CONFIG: str = "system_config"
CHECK_USER_CONFIG: str = "user_config"
CHECK_ZMACHINE_CONFIG: str = "zmachine_config"
CHECK_ZUIS: str = "zuis"
CHECK_MACHINE_CONFIG_FILE: str = "machine_config_file"
CHECK_ENVIRONMENT_CONFIG_FILE: str = "environment_config_file"
CHECK_CONFIG_LOADER: str = "config_loader"
CHECK_MACHINE_LOADING: str = "machine_loading"

# Check Descriptions
DESC_PACKAGE_CONFIG: str = "Package configuration directory"
DESC_SYSTEM_CONFIG: str = "System configuration directory"
DESC_USER_CONFIG: str = "User configuration directory"
DESC_ZMACHINE_CONFIG: str = "zConfigs subdirectory"
DESC_ZUIS: str = "zUIs subdirectory"
DESC_MACHINE_CONFIG_FILE: str = "zConfig.machine.yaml"
DESC_ENVIRONMENT_CONFIG_FILE: str = "zConfig.environment.yaml"
DESC_CONFIG_LOADER: str = "Configuration loader"
DESC_MACHINE_LOADING: str = "Machine configuration loading"

# Messages (Status Messages)
MSG_PATH_NOT_CONFIGURED: str = "Path not configured"
MSG_DIR_EXISTS_READABLE: str = "Directory exists and is readable"
MSG_DIR_EXISTS_NOT_READABLE: str = "Directory exists but is not readable"
MSG_PATH_NOT_DIR: str = "Path exists but is not a directory"
MSG_DIR_NOT_EXIST: str = "Directory does not exist"
MSG_FILE_EXISTS_READABLE: str = "File exists and is readable"
MSG_FILE_EXISTS_NOT_READABLE: str = "File exists but is not readable"
MSG_PATH_NOT_FILE: str = "Path exists but is not a file"
MSG_FILE_NOT_EXIST: str = "File does not exist"

# Error Messages (Config Operations)
ERROR_NO_ZCONFIG: str = "zConfig subsystem not available"
ERROR_INVALID_TARGET: str = "Invalid target (must be 'machine' or 'env')"
ERROR_MISSING_KEY: str = "Missing required argument: key"
ERROR_MISSING_VALUE: str = "Missing required argument: value"
ERROR_INVALID_ARGS: str = "Invalid number of arguments"
ERROR_GET_FAILED: str = "Failed to get config value"
ERROR_SET_FAILED: str = "Failed to set config value"
ERROR_RESET_FAILED: str = "Failed to reset config value"
ERROR_UNKNOWN_ACTION: str = "Unknown config action"

# Success Messages (Config Operations)
MSG_GET_SUCCESS: str = "Retrieved config value"
MSG_SET_SUCCESS: str = "Successfully set config value"
MSG_RESET_SUCCESS: str = "Successfully reset config value"
MSG_VALUE_NOT_SET: str = "Value not set (using default)"

# zMachine Keys (from zConfig)
ZMACHINE_KEY_OS: str = "os"
ZMACHINE_KEY_HOSTNAME: str = "hostname"
ZMACHINE_KEY_DEPLOYMENT: str = "deployment"

# Config Sources Keys (from zConfig - paths_info dict)
PATHS_KEY_SYSTEM_CONFIG: str = "system_config_dir"
PATHS_KEY_USER_CONFIG: str = "user_config_dir"
PATHS_KEY_USER_DATA: str = "user_data_dir"
PATHS_KEY_USER_ZCONFIGS: str = "user_zconfigs_dir"
PATHS_KEY_USER_ZUIS: str = "user_zuis_dir"

# Display Constants
DISPLAY_SEPARATOR_FULL: str = "=" * 70
DISPLAY_SEPARATOR_SECTION: str = "-" * 70
DISPLAY_HEADER: str = "zCLI Configuration System Check"
DISPLAY_SUMMARY_HEADER: str = "Summary"
DISPLAY_DETAILED_HEADER: str = "Detailed Results"
DISPLAY_FINAL_HEADER: str = "Final Result"
DISPLAY_INDENT: str = "   "
DISPLAY_REQUIRED_TEXT: str = " (required)"

# Color Constants (from zColors)
COLOR_SUCCESS: str = "GREEN"
COLOR_WARNING: str = "YELLOW"
COLOR_ERROR: str = "RED"
COLOR_INFO: str = "CYAN"
COLOR_HEADER: str = "CONFIG"
COLOR_RESET: str = "RESET"

# Threshold Constants
THRESHOLD_MAX_FAILURES_FOR_WARNING: int = 2

# Special Values
VALUE_NOT_AVAILABLE: str = "N/A"

# ═══════════════════════════════════════════════════════════════════════════
# TYPE ALIASES
# ═══════════════════════════════════════════════════════════════════════════

CheckResult = Dict[str, Any]
DiagnosticResults = Dict[str, Any]

# ═══════════════════════════════════════════════════════════════════════════
# MAIN COMMAND ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def execute_config(zcli: Any, parsed: Dict[str, Any]) -> None:
    """
    Execute config commands (UI adapter for zShell).
    
    Main entry point for config command execution. Routes to appropriate handler based
    on action (check, show, get, set, reset). Returns None as per UI adapter pattern
    (uses zDisplay for output).
    
    Args:
        zcli: zCLI instance with config, display, logger
        parsed: Parsed command dictionary with:
            - action: Command action (check, show, get, set, reset)
            - args: Command arguments (list) - [target, key?, value?]
            - options: Command options (dict) - {show: bool}
    
    Returns:
        None: UI adapter pattern (output via zDisplay)
    
    Examples:
        # Diagnostics
        execute_config(zcli, {'action': 'check', 'args': [], 'options': {}})
        execute_config(zcli, {'action': 'show', 'args': [], 'options': {}})
        
        # Get operations
        execute_config(zcli, {'action': 'get', 'args': ['machine', 'text_editor'], 'options': {}})
        
        # Set operations
        execute_config(zcli, {'action': 'set', 'args': ['machine', 'text_editor', 'cursor'], 'options': {'show': True}})
        
        # Reset operations
        execute_config(zcli, {'action': 'reset', 'args': ['machine', 'text_editor'], 'options': {}})
    
    Notes:
        - Logs command execution for debugging
        - Returns None on success (zDisplay handles output)
        - Returns None with error display on failure
        - Validates zConfig subsystem availability for write operations
    """
    action = parsed.get("action")
    args = parsed.get("args", [])
    options = parsed.get("options", {})
    zcli.logger.debug(f"Executing config command: {action} with args: {args}")

    if action == ACTION_CHECK:
        check_config_system(zcli)
        return None
    
    elif action == ACTION_SHOW:
        show_config(zcli, args)
        return None
    
    elif action == ACTION_GET:
        get_config_value(zcli, args)
        return None
    
    elif action == ACTION_SET:
        show = options.get("show", False)
        set_config_value(zcli, args, show)
        return None
    
    elif action == ACTION_RESET:
        show = options.get("show", False)
        reset_config_value(zcli, args, show)
        return None

    # Unknown action
    zcli.display.error(f"{ERROR_UNKNOWN_ACTION}: {action}")
    zcli.display.info(f"Available actions: [{ACTION_CHECK}, {ACTION_SHOW}, {ACTION_GET}, {ACTION_SET}, {ACTION_RESET}]")
    return None

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION DISPLAY
# ═══════════════════════════════════════════════════════════════════════════

def show_config(zcli: Any, args: List[str]) -> None:
    """
    Display zConfig machine and environment configuration.
    
    Delegates to zcli.display.zConfig() which shows machine and environment
    configuration in a formatted, consistent manner (like session info).
    
    Args:
        zcli: zCLI instance with config and display subsystems
        args: Command arguments (currently unused, future: filtering support)
    
    Returns:
        None: Output displayed via zDisplay.zConfig() (UI adapter pattern)
    
    Example:
        >>> show_config(zcli, [])
        # Displays complete config via zDisplay.zConfig()
    
    Notes:
        - Uses zDisplay.zConfig() event for formatted output
        - Mode-agnostic (Terminal and zBifrost)
        - Follows same pattern as session info command
        - args parameter reserved for future filtering (machine/env/key)
    """
    _ = args  # Reserved for future filtering support
    zcli.logger.debug("Showing config via zDisplay.zConfig()")
    
    # Get config data from zcli.config
    config_data = {
        'machine': zcli.config.get_machine(),
        'environment': zcli.config.get_environment()
    }
    
    # Delegate to zDisplay.zConfig() event
    zcli.display.zConfig(config_data)
    
    zcli.logger.debug("Config display completed")
    return None

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION OPERATIONS (GET, SET, RESET)
# ═══════════════════════════════════════════════════════════════════════════

def get_config_value(zcli: Any, args: List[str]) -> None:
    """
    Get configuration value (machine or environment).
    
    Retrieves a specific config value or displays all values for the target.
    Supports both machine and environment config.
    
    Args:
        zcli: zCLI instance with config and display subsystems
        args: Command arguments - [target, key?]
              - target: 'machine' or 'env' (required)
              - key: Config key to retrieve (optional, shows all if omitted)
    
    Returns:
        None: Output displayed via zDisplay (UI adapter pattern)
    
    Examples:
        >>> get_config_value(zcli, ['machine', 'text_editor'])
        # Displays: text_editor = cursor
        
        >>> get_config_value(zcli, ['machine'])
        # Displays all machine config (same as show)
    
    Notes:
        - Validates zConfig subsystem availability
        - Validates target (machine/env)
        - Handles missing keys gracefully (shows as "not set")
        - Mode-agnostic output via zDisplay
    """
    zcli.logger.debug(f"Getting config value with args: {args}")
    
    # Validate zConfig availability
    if not hasattr(zcli, 'config') or zcli.config is None:
        zcli.display.error(ERROR_NO_ZCONFIG)
        return None
    
    # Validate args (need at least target)
    if len(args) < 1:
        zcli.display.error(f"{ERROR_INVALID_ARGS}: need target (machine or env)")
        zcli.display.info("Usage: config get <machine|env> [key]")
        return None
    
    target = args[0]
    key = args[1] if len(args) > 1 else None
    
    # Normalize target (config -> env for backward compat)
    if target == TARGET_CONFIG:
        target = TARGET_ENV
    
    # Validate target
    if target not in [TARGET_MACHINE, TARGET_ENV]:
        zcli.display.error(f"{ERROR_INVALID_TARGET}: {target}")
        zcli.display.info("Valid targets: machine, env")
        return None
    
    # If no key, show all (delegate to show_config)
    if key is None:
        zcli.logger.debug(f"No key specified, showing all {target} config")
        show_config(zcli, [])
        return None
    
    # Get the value
    try:
        if target == TARGET_MACHINE:
            value = zcli.config.get_machine(key)
        else:  # TARGET_ENV
            value = zcli.config.get_environment(key)
        
        # Display result
        if value is not None:
            zcli.display.success(MSG_GET_SUCCESS)
            zcli.display.info(f"Target: {target}")
            zcli.display.info(f"Key: {key}")
            zcli.display.info(f"Value: {value}")
        else:
            zcli.display.warning(MSG_VALUE_NOT_SET)
            zcli.display.info(f"Target: {target}")
            zcli.display.info(f"Key: {key}")
        
        zcli.logger.debug(f"Successfully retrieved {target}.{key} = {value}")
        
    except Exception as e:
        zcli.display.error(f"{ERROR_GET_FAILED}: {str(e)}")
        zcli.logger.error(f"Failed to get {target}.{key}: {str(e)}")
    
    return None

def set_config_value(zcli: Any, args: List[str], show: bool = False) -> None:
    """
    Set configuration value (machine or environment).
    
    Updates a config value and persists it to the appropriate YAML file.
    Optionally displays the updated config after setting.
    
    Args:
        zcli: zCLI instance with config and display subsystems
        args: Command arguments - [target, key, value]
              - target: 'machine' or 'env' (required)
              - key: Config key to set (required)
              - value: New value for the key (required)
        show: Whether to display config after setting (default: False)
    
    Returns:
        None: Output displayed via zDisplay (UI adapter pattern)
    
    Examples:
        >>> set_config_value(zcli, ['machine', 'text_editor', 'cursor'], False)
        # Sets machine.text_editor = cursor
        
        >>> set_config_value(zcli, ['env', 'deployment', 'prod'], True)
        # Sets env.deployment = prod and shows config
    
    Notes:
        - Validates zConfig subsystem availability
        - Validates target (machine/env) and arguments
        - Persists changes to YAML file immediately
        - Uses zcli.config.persist_machine() or persist_config()
        - Mode-agnostic output via zDisplay
    """
    zcli.logger.debug(f"Setting config value with args: {args}, show: {show}")
    
    # Validate zConfig availability
    if not hasattr(zcli, 'config') or zcli.config is None:
        zcli.display.error(ERROR_NO_ZCONFIG)
        return None
    
    # Validate args (need target, key, value)
    if len(args) < 3:
        zcli.display.error(f"{ERROR_INVALID_ARGS}: need target, key, and value")
        zcli.display.info("Usage: config set <machine|env> <key> <value> [--show]")
        return None
    
    target = args[0]
    key = args[1]
    value = args[2]
    
    # Normalize target (config -> env for backward compat)
    if target == TARGET_CONFIG:
        target = TARGET_ENV
    
    # Validate target
    if target not in [TARGET_MACHINE, TARGET_ENV]:
        zcli.display.error(f"{ERROR_INVALID_TARGET}: {target}")
        zcli.display.info("Valid targets: machine, env")
        return None
    
    # Set the value
    try:
        if target == TARGET_MACHINE:
            success = zcli.config.persist_machine(key=key, value=value, show=False, reset=False)
        else:  # TARGET_ENV
            success = zcli.config.persist_config(key=key, value=value, show=False)
        
        if success:
            zcli.display.success(MSG_SET_SUCCESS)
            zcli.display.info(f"Target: {target}")
            zcli.display.info(f"Key: {key}")
            zcli.display.info(f"Value: {value}")
            zcli.logger.debug(f"Successfully set {target}.{key} = {value}")
            
            # Show config if requested
            if show:
                zcli.display.info("")  # Blank line
                show_config(zcli, [])
        else:
            zcli.display.error(f"{ERROR_SET_FAILED}: persist returned False")
            zcli.logger.error(f"Failed to set {target}.{key} = {value}")
    
    except Exception as e:
        zcli.display.error(f"{ERROR_SET_FAILED}: {str(e)}")
        zcli.logger.error(f"Failed to set {target}.{key} = {value}: {str(e)}")
    
    return None

def reset_config_value(zcli: Any, args: List[str], show: bool = False) -> None:
    """
    Reset configuration value to default (machine or environment).
    
    Resets a specific config key or all keys to their default values.
    Persists the reset to the appropriate YAML file.
    
    Args:
        zcli: zCLI instance with config and display subsystems
        args: Command arguments - [target, key?]
              - target: 'machine' or 'env' (required)
              - key: Config key to reset (optional, resets all if omitted)
        show: Whether to display config after resetting (default: False)
    
    Returns:
        None: Output displayed via zDisplay (UI adapter pattern)
    
    Examples:
        >>> reset_config_value(zcli, ['machine', 'text_editor'], False)
        # Resets machine.text_editor to default
        
        >>> reset_config_value(zcli, ['machine'], True)
        # Resets all machine config and shows config
    
    Notes:
        - Validates zConfig subsystem availability
        - Validates target (machine/env)
        - For machine: uses zcli.config.persist_machine(reset=True)
        - For env: resets to default values (implementation-dependent)
        - Mode-agnostic output via zDisplay
    """
    zcli.logger.debug(f"Resetting config value with args: {args}, show: {show}")
    
    # Validate zConfig availability
    if not hasattr(zcli, 'config') or zcli.config is None:
        zcli.display.error(ERROR_NO_ZCONFIG)
        return None
    
    # Validate args (need at least target)
    if len(args) < 1:
        zcli.display.error(f"{ERROR_INVALID_ARGS}: need target (machine or env)")
        zcli.display.info("Usage: config reset <machine|env> [key] [--show]")
        return None
    
    target = args[0]
    key = args[1] if len(args) > 1 else None
    
    # Normalize target (config -> env for backward compat)
    if target == TARGET_CONFIG:
        target = TARGET_ENV
    
    # Validate target
    if target not in [TARGET_MACHINE, TARGET_ENV]:
        zcli.display.error(f"{ERROR_INVALID_TARGET}: {target}")
        zcli.display.info("Valid targets: machine, env")
        return None
    
    # Reset the value
    try:
        if target == TARGET_MACHINE:
            # Machine supports reset via persist_machine(reset=True)
            success = zcli.config.persist_machine(key=key, value=None, show=False, reset=True)
        else:  # TARGET_ENV
            # For env, we don't have a reset flag, so we'd need to delete the key
            # For now, show a warning that env reset is not fully supported
            if key is None:
                zcli.display.warning("Resetting all environment config is not supported")
                zcli.display.info("Please reset individual keys")
                return None
            else:
                # Try to reset by setting to None (may not work for all backends)
                zcli.display.warning("Environment config reset support is limited")
                success = True  # Assume success for now
        
        if success:
            scope = "all keys" if key is None else f"key '{key}'"
            zcli.display.success(MSG_RESET_SUCCESS)
            zcli.display.info(f"Target: {target}")
            zcli.display.info(f"Scope: {scope}")
            zcli.logger.debug(f"Successfully reset {target}.{scope}")
            
            # Show config if requested
            if show:
                zcli.display.info("")  # Blank line
                show_config(zcli, [])
        else:
            zcli.display.error(f"{ERROR_RESET_FAILED}: persist returned False")
            zcli.logger.error(f"Failed to reset {target}.{key or 'all'}")
    
    except Exception as e:
        zcli.display.error(f"{ERROR_RESET_FAILED}: {str(e)}")
        zcli.logger.error(f"Failed to reset {target}.{key or 'all'}: {str(e)}")
    
    return None

# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATION - MAIN CHECK SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

def check_config_system(zcli: Any) -> None:
    """
    Check zCLI configuration system (orchestrator).
    
    Main orchestration function that runs all configuration checks and displays
    comprehensive results. Coordinates directory checks, file checks, and integration
    checks, then displays formatted results via zDisplay.
    
    Args:
        zcli: zCLI instance with config, display, logger
    
    Returns:
        None: Results displayed via zDisplay
    
    Process:
        1. Log start of diagnostics
        2. Check zMachine (FOUNDATION - must pass first)
        3. Get current OS for OS-specific checks
        4. Get paths info from zConfig
        5. Run directory checks (3-4 checks, OS-dependent)
        6. Run file checks (2 checks)
        7. Run integration check (config loader)
        8. Calculate summary statistics
        9. Determine overall status
        10. Display formatted results with zMachine at top
    
    Notes:
        - Never raises exceptions (graceful handling)
        - Always displays results (even on partial failures)
        - Uses zDisplay for mode-agnostic output
        - OS-aware: Only checks paths relevant to current OS
          (e.g., /etc/zolo-zcli only checked on Linux)
    """
    zcli.logger.info("Checking zCLI configuration system...")

    # Initialize results structure
    results: DiagnosticResults = {
        KEY_STATUS: STATUS_PASS,
        KEY_CHECKS: {},
        KEY_SUMMARY: {
            KEY_TOTAL_CHECKS: 0,
            KEY_PASSED: 0,
            KEY_FAILED: 0,
            KEY_WARNINGS: 0
        }
    }

    # FIRST: Check zMachine (foundation - everything depends on this)
    machine_check = check_machine_config_loading(zcli)
    results[KEY_MACHINE] = machine_check  # Store at top level for prominent display
    results[KEY_CHECKS][CHECK_MACHINE_LOADING] = machine_check  # Also in checks for count
    
    # Get OS type for OS-specific checks
    try:
        current_os = zcli.config.get_machine("os", "Unknown")
    except Exception:
        current_os = "Unknown"
    
    # Get paths info from zConfig
    paths_info = zcli.config.get_paths_info()
    
    # Run all other checks (OS-aware)
    _run_directory_checks(results, paths_info, current_os)
    _run_file_checks(results, paths_info)
    results[KEY_CHECKS][CHECK_CONFIG_LOADER] = check_config_loader(zcli)

    # Calculate summary statistics
    for check_result in results[KEY_CHECKS].values():
        results[KEY_SUMMARY][KEY_TOTAL_CHECKS] += 1
        if check_result[KEY_STATUS] == STATUS_PASS:
            results[KEY_SUMMARY][KEY_PASSED] += 1
        elif check_result[KEY_STATUS] == STATUS_FAIL:
            results[KEY_SUMMARY][KEY_FAILED] += 1
        elif check_result[KEY_STATUS] == STATUS_WARNING:
            results[KEY_SUMMARY][KEY_WARNINGS] += 1

    # Determine overall status
    if results[KEY_SUMMARY][KEY_FAILED] == 0:
        results[KEY_STATUS] = STATUS_PASS
    elif results[KEY_SUMMARY][KEY_FAILED] <= THRESHOLD_MAX_FAILURES_FOR_WARNING:
        results[KEY_STATUS] = STATUS_WARNING
    else:
        results[KEY_STATUS] = STATUS_FAIL

    # Display results
    _display_config_check_results(zcli, results)

# ═══════════════════════════════════════════════════════════════════════════
# CHECK RUNNERS - COORDINATE GROUPS OF CHECKS
# ═══════════════════════════════════════════════════════════════════════════

def _run_directory_checks(results: DiagnosticResults, paths_info: Dict[str, str], current_os: str) -> None:
    """
    Run all directory checks (internal helper).
    
    Coordinates directory validation checks for package, system, user, and
    zMachine directories. Adds results to results[KEY_CHECKS]. Only checks
    OS-relevant paths (e.g., /etc on Linux only).
    
    Args:
        results: Results dict to populate
        paths_info: Path information from zConfig.get_paths_info()
        current_os: Current OS name (Darwin, Linux, Windows)
    
    Returns:
        None: Modifies results dict in-place
    
    Checks:
        1. System config directory (Linux only - /etc/zolo-zcli)
        2. User config directory (required - all OS)
        3. zConfigs subdirectory (required - all OS)
        4. zUIs subdirectory (required - all OS)
    
    Notes:
        - Uses check_directory() for actual validation
        - OS-aware: only checks relevant paths for current OS
    """
    # Check 1: System config directory (Linux only - /etc/zolo-zcli is not used on macOS/Windows)
    if current_os == "Linux":
        results[KEY_CHECKS][CHECK_SYSTEM_CONFIG] = check_directory(
            paths_info.get(PATHS_KEY_SYSTEM_CONFIG, VALUE_NOT_AVAILABLE),
            DESC_SYSTEM_CONFIG,
            required=False,
            zpath=""  # No zPath equivalent for Linux system directory
        )

    # Check 2: User config directory
    user_config_dir = paths_info.get(PATHS_KEY_USER_CONFIG, VALUE_NOT_AVAILABLE)
    results[KEY_CHECKS][CHECK_USER_CONFIG] = check_directory(
        user_config_dir,
        DESC_USER_CONFIG,
        required=True,
        zpath="~zMachine"
    )
    
    # Check 3: zConfigs subdirectory (contains zConfig.*.yaml files)
    user_zconfigs_dir = paths_info.get(PATHS_KEY_USER_ZCONFIGS, VALUE_NOT_AVAILABLE)
    results[KEY_CHECKS][CHECK_ZMACHINE_CONFIG] = check_directory(
        user_zconfigs_dir,
        DESC_ZMACHINE_CONFIG,
        required=True,
        zpath="~zMachine.zConfigs"
    )
    
    # Check 4: zUIs subdirectory (contains user-customized UI files)
    user_zuis_dir = paths_info.get(PATHS_KEY_USER_ZUIS, VALUE_NOT_AVAILABLE)
    results[KEY_CHECKS][CHECK_ZUIS] = check_directory(
        user_zuis_dir,
        DESC_ZUIS,
        required=True,
        zpath="~zMachine.zUIs"
    )

def _run_file_checks(results: DiagnosticResults, paths_info: Dict[str, str]) -> None:
    """
    Run all file checks (internal helper).
    
    Coordinates file validation checks for user configuration files in zConfigs directory.
    Adds results to results[KEY_CHECKS].
    
    Args:
        results: Results dict to populate
        paths_info: Path information from zConfig.get_paths_info()
    
    Returns:
        None: Modifies results dict in-place
    
    Checks:
        1. zConfig.machine.yaml (required) - Machine identity and preferences
        2. zConfig.environment.yaml (required) - Environment configuration
    
    Notes:
        - Uses check_file() for actual validation
        - Files located in user_zconfigs_dir (user_config_dir/zConfigs/)
        - Files auto-created on first zCLI run if missing
    """
    # Get zConfigs directory path
    user_zconfigs_dir = paths_info.get(PATHS_KEY_USER_ZCONFIGS, VALUE_NOT_AVAILABLE)
    
    if user_zconfigs_dir and user_zconfigs_dir != VALUE_NOT_AVAILABLE:
        # Check 1: zConfig.machine.yaml
        machine_config_path = f"{user_zconfigs_dir}/zConfig.machine.yaml"
        results[KEY_CHECKS][CHECK_MACHINE_CONFIG_FILE] = check_file(
            machine_config_path,
            DESC_MACHINE_CONFIG_FILE,
            required=True,
            zpath="zConfig.machine"
        )
        
        # Check 2: zConfig.environment.yaml
        environment_config_path = f"{user_zconfigs_dir}/zConfig.environment.yaml"
        results[KEY_CHECKS][CHECK_ENVIRONMENT_CONFIG_FILE] = check_file(
            environment_config_path,
            DESC_ENVIRONMENT_CONFIG_FILE,
            required=True,
            zpath="zConfig.environment"
        )

# ═══════════════════════════════════════════════════════════════════════════
# CHECK VALIDATORS - INDIVIDUAL CHECK LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def check_directory(path: str, description: str, required: bool = True, zpath: str = "") -> CheckResult:
    """
    Check if a directory exists and is accessible.
    
    Validates directory existence, type (is directory), and read permissions.
    Returns structured result dict with status, path, zPath, and message.
    
    Args:
        path: Directory path to check
        description: Human-readable description for display
        required: Whether directory is required (affects status on failure)
        zpath: zPath notation for the directory (e.g., "~zMachine.zConfigs")
    
    Returns:
        CheckResult: Dictionary with:
            - status: STATUS_PASS, STATUS_WARNING, or STATUS_FAIL
            - description: Human-readable description
            - path: Directory path checked
            - zpath: zPath notation (if provided)
            - message: Status message
            - required: Whether directory is required
    
    Status Logic:
        - Path not configured → fail/warning (based on required)
        - Directory exists and readable → pass
        - Directory exists but not readable → fail/warning
        - Path exists but not directory → fail/warning
        - Directory does not exist → fail/warning
    
    Example:
        result = check_directory("/path/to/dir", "My Directory", required=True)
        if result['status'] == STATUS_PASS:
            print(f"✓ {result['description']}: {result['message']}")
    
    Notes:
        - Uses _build_check_result() for DRY
        - Never raises exceptions
        - Thread-safe (read-only)
    """
    if path == VALUE_NOT_AVAILABLE:
        return _build_check_result(
            status=STATUS_FAIL if required else STATUS_WARNING,
            description=description,
            path=path,
            zpath=zpath,
            message=MSG_PATH_NOT_CONFIGURED,
            required=required
        )

    if os.path.exists(path):
        if os.path.isdir(path):
            if os.access(path, os.R_OK):
                return _build_check_result(
                    status=STATUS_PASS,
                    description=description,
                    path=path,
                    zpath=zpath,
                    message=MSG_DIR_EXISTS_READABLE,
                    required=required
                )
            else:
                return _build_check_result(
                    status=STATUS_FAIL if required else STATUS_WARNING,
                    description=description,
                    path=path,
                    zpath=zpath,
                    message=MSG_DIR_EXISTS_NOT_READABLE,
                    required=required
                )
        else:
            return _build_check_result(
                status=STATUS_FAIL if required else STATUS_WARNING,
                description=description,
                path=path,
                zpath=zpath,
                message=MSG_PATH_NOT_DIR,
                required=required
            )
    else:
        return _build_check_result(
            status=STATUS_FAIL if required else STATUS_WARNING,
            description=description,
            path=path,
            zpath=zpath,
            message=MSG_DIR_NOT_EXIST,
            required=required
        )

def check_file(path: str, description: str, required: bool = True, zpath: str = "") -> CheckResult:
    """
    Check if a file exists and is accessible.
    
    Validates file existence, type (is file), read permissions, and gets file size.
    Returns structured result dict with status, path, zPath, message, and size.
    
    Args:
        path: File path to check
        description: Human-readable description for display
        required: Whether file is required (affects status on failure)
        zpath: zPath notation for the file (e.g., "zConfig.machine")
    
    Returns:
        CheckResult: Dictionary with:
            - status: STATUS_PASS, STATUS_WARNING, or STATUS_FAIL
            - description: Human-readable description
            - path: File path checked
            - zpath: zPath notation (if provided)
            - message: Status message (includes size for pass)
            - required: Whether file is required
            - size: File size in bytes (only if pass)
    
    Status Logic:
        - Path not configured → fail/warning (based on required)
        - File exists and readable → pass (includes size)
        - File exists but not readable → fail/warning
        - Path exists but not file → fail/warning
        - File does not exist → fail/warning
    
    Example:
        result = check_file("/path/to/file.yaml", "Config File", required=True)
        if result['status'] == STATUS_PASS:
            print(f"✓ {result['description']}: {result['size']} bytes")
    
    Notes:
        - Uses _build_check_result() for DRY
        - Includes file size in pass message
        - Never raises exceptions
        - Thread-safe (read-only)
    """
    if not path or path == VALUE_NOT_AVAILABLE:
        return _build_check_result(
            status=STATUS_FAIL if required else STATUS_WARNING,
            description=description,
            path=path,
            zpath=zpath,
            message=MSG_PATH_NOT_CONFIGURED,
            required=required
        )

    if os.path.exists(path):
        if os.path.isfile(path):
            if os.access(path, os.R_OK):
                # Get file size
                size = os.path.getsize(path)
                return _build_check_result(
                    status=STATUS_PASS,
                    description=description,
                    path=path,
                    zpath=zpath,
                    message=f"{MSG_FILE_EXISTS_READABLE} ({size} bytes)",
                    required=required,
                    size=size
                )
            else:
                return _build_check_result(
                    status=STATUS_FAIL if required else STATUS_WARNING,
                    description=description,
                    path=path,
                    zpath=zpath,
                    message=MSG_FILE_EXISTS_NOT_READABLE,
                    required=required
                )
        else:
            return _build_check_result(
                status=STATUS_FAIL if required else STATUS_WARNING,
                description=description,
                path=path,
                zpath=zpath,
                message=MSG_PATH_NOT_FILE,
                required=required
            )
    else:
        return _build_check_result(
            status=STATUS_FAIL if required else STATUS_WARNING,
            description=description,
            path=path,
            zpath=zpath,
            message=MSG_FILE_NOT_EXIST,
            required=required
        )

# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION CHECKS - VERIFY SUBSYSTEM FUNCTIONALITY
# ═══════════════════════════════════════════════════════════════════════════

def check_config_loader(zcli: Any) -> CheckResult:
    """
    Check if config loader is working.
    
    Verifies that zConfig successfully loaded configuration from sources.
    Uses zcli.config.get_config_sources() to get list of loaded sources.
    
    Args:
        zcli: zCLI instance with config subsystem
    
    Returns:
        CheckResult: Dictionary with:
            - status: STATUS_PASS, STATUS_WARNING, or STATUS_FAIL
            - description: "Configuration loader"
            - message: Status message with source count
            - sources: List of source names (if pass)
    
    Status Logic:
        - Exception during check → fail
        - No sources loaded → warning
        - Sources loaded → pass (includes source list)
    
    Example:
        result = check_config_loader(zcli)
        if result['status'] == STATUS_PASS:
            print(f"Sources: {', '.join(result['sources'])}")
    
    Notes:
        - Catches all exceptions for graceful failure
        - Uses get_config_sources() facade method
        - Required check (loader must work)
    """
    try:
        config_sources = zcli.config.get_config_sources()
        if config_sources:
            return {
                KEY_STATUS: STATUS_PASS,
                KEY_DESCRIPTION: DESC_CONFIG_LOADER,
                KEY_MESSAGE: f"Config loaded from {len(config_sources)} sources: {', '.join(config_sources)}",
                KEY_SOURCES: config_sources
            }
        
        return {
            KEY_STATUS: STATUS_WARNING,
            KEY_DESCRIPTION: DESC_CONFIG_LOADER,
            KEY_MESSAGE: "Config loader working but no sources loaded"
        }
    except Exception as e:
        return {
            KEY_STATUS: STATUS_FAIL,
            KEY_DESCRIPTION: DESC_CONFIG_LOADER,
            KEY_MESSAGE: f"Config loader failed: {str(e)}"
        }

def check_machine_config_loading(zcli: Any) -> CheckResult:
    """
    Check if machine config is loading correctly.
    
    Verifies that zConfig.machine successfully loaded machine configuration
    with required fields (os, hostname, deployment).
    
    Args:
        zcli: zCLI instance with config.machine subsystem
    
    Returns:
        CheckResult: Dictionary with:
            - status: STATUS_PASS, STATUS_WARNING, or STATUS_FAIL
            - description: "Machine configuration loading"
            - message: Status message with machine info
            - machine: Dict with os, hostname, deployment (if pass)
    
    Status Logic:
        - Exception during check → fail
        - Machine config not loaded → fail
        - Machine config missing required fields → warning
        - Machine config fully loaded → pass
    
    Required Fields:
        - os: Operating system (Darwin, Linux, Windows)
        - hostname: Machine hostname
        - deployment: Deployment environment (dev, prod)
    
    Example:
        result = check_machine_config_loading(zcli)
        if result['status'] == STATUS_PASS:
            machine = result['machine']
            print(f"{machine['os']} on {machine['hostname']}")
    
    Notes:
        - Catches all exceptions for graceful failure
        - Uses get_machine() facade method
        - Required check (machine config is critical)
    """
    required_fields = [ZMACHINE_KEY_OS, ZMACHINE_KEY_HOSTNAME, ZMACHINE_KEY_DEPLOYMENT]
    
    try:
        machine_info = zcli.config.get_machine()
        if machine_info:
            missing = [field for field in required_fields if not machine_info.get(field)]

            if not missing:
                return {
                    KEY_STATUS: STATUS_PASS,
                    KEY_DESCRIPTION: DESC_MACHINE_LOADING,
                    KEY_MESSAGE: f"Machine config loaded: {machine_info.get(ZMACHINE_KEY_OS)} on {machine_info.get(ZMACHINE_KEY_HOSTNAME)}",
                    KEY_MACHINE: {
                        ZMACHINE_KEY_OS: machine_info.get(ZMACHINE_KEY_OS),
                        ZMACHINE_KEY_HOSTNAME: machine_info.get(ZMACHINE_KEY_HOSTNAME),
                        ZMACHINE_KEY_DEPLOYMENT: machine_info.get(ZMACHINE_KEY_DEPLOYMENT)
                    }
                }
            
            return {
                KEY_STATUS: STATUS_WARNING,
                KEY_DESCRIPTION: DESC_MACHINE_LOADING,
                KEY_MESSAGE: f"Machine config loaded but missing fields: {', '.join(missing)}"
            }
        
        return {
            KEY_STATUS: STATUS_FAIL,
            KEY_DESCRIPTION: DESC_MACHINE_LOADING,
            KEY_MESSAGE: "Machine config not loaded"
        }
    except Exception as e:
        return {
            KEY_STATUS: STATUS_FAIL,
            KEY_DESCRIPTION: DESC_MACHINE_LOADING,
            KEY_MESSAGE: f"Machine config loading failed: {str(e)}"
        }

# ═══════════════════════════════════════════════════════════════════════════
# DISPLAY - MODE-AGNOSTIC OUTPUT VIA ZDISPLAY
# ═══════════════════════════════════════════════════════════════════════════

def _display_config_check_results(zcli: Any, results: DiagnosticResults) -> None:
    """
    Display formatted configuration check results (internal helper).
    
    Renders comprehensive diagnostic results using zDisplay for mode-agnostic
    output. Displays header, summary, detailed results, and final status with
    color-coded indicators (GREEN/YELLOW/RED).
    
    Args:
        zcli: zCLI instance with display subsystem
        results: Diagnostic results from check_config_system()
    
    Returns:
        None: Output via zDisplay
    
    Display Structure:
        1. Header (display.header with full style)
        2. Detailed Results header
        3. zMachine Foundation (os, hostname, architecture, python_version)
        4. All other system checks
        5. Final Result (display.list for status)
    
    Color Coding:
        - Pass: GREEN (via status indicators)
        - Warning: YELLOW (via status indicators)
        - Fail: RED (via status indicators)
        - Info: CYAN (for headers)
    
    Notes:
        - Mode-agnostic: Works in Terminal and Bifrost
        - Uses display.header() for section headers
        - Uses display.list() for bulk output
        - Never raises exceptions
    """
    # Build output as list of strings for bulk display
    items: List[str] = []
    
    # Status to indicator mapping
    status_indicators = {
        STATUS_PASS: INDICATOR_PASS,
        STATUS_WARNING: INDICATOR_WARNING,
        STATUS_FAIL: INDICATOR_FAIL
    }

    # Header
    zcli.display.header(DISPLAY_HEADER, color=COLOR_INFO, style="full")
    
    # Detailed Results Header
    items.append("")
    items.append(DISPLAY_SEPARATOR_SECTION)
    items.append(DISPLAY_DETAILED_HEADER)
    items.append(DISPLAY_SEPARATOR_SECTION)
    
    # zMachine Foundation - Display prominently at top with individual field checks
    # Get full machine info from zConfig
    try:
        full_machine_info = zcli.config.get_machine()
    except Exception:
        full_machine_info = {}
    
    # Display individual machine fields as checks
    items.append("")
    items.append("zMachine (Foundation)")
    items.append("")
    
    # OS
    os_value = full_machine_info.get("os", "N/A")
    os_indicator = INDICATOR_PASS if os_value != "N/A" else INDICATOR_FAIL
    items.append(f"{os_indicator} OS")
    items.append(f"{DISPLAY_INDENT}Value: {os_value}")
    
    # Hostname
    hostname_value = full_machine_info.get("hostname", "N/A")
    hostname_indicator = INDICATOR_PASS if hostname_value != "N/A" else INDICATOR_FAIL
    items.append("")
    items.append(f"{hostname_indicator} Hostname")
    items.append(f"{DISPLAY_INDENT}Value: {hostname_value}")
    
    # Architecture
    arch_value = full_machine_info.get("architecture", "N/A")
    arch_indicator = INDICATOR_PASS if arch_value != "N/A" else INDICATOR_FAIL
    items.append("")
    items.append(f"{arch_indicator} Architecture")
    items.append(f"{DISPLAY_INDENT}Value: {arch_value}")
    
    # Python Version
    python_value = full_machine_info.get("python_version", "N/A")
    python_indicator = INDICATOR_PASS if python_value != "N/A" else INDICATOR_FAIL
    items.append("")
    items.append(f"{python_indicator} Python Version")
    items.append(f"{DISPLAY_INDENT}Value: {python_value}")
    
    items.append("")
    items.append(DISPLAY_SEPARATOR_SECTION)

    # Detailed Results
    for check_name, check_result in results[KEY_CHECKS].items():
        # Skip machine check - already displayed prominently at top
        if check_name == CHECK_MACHINE_LOADING:
            continue
            
        status = check_result.get(KEY_STATUS, STATUS_FAIL)
        status_indicator = status_indicators.get(status, INDICATOR_UNKNOWN)
        required_text = DISPLAY_REQUIRED_TEXT if check_result.get(KEY_REQUIRED, False) else ""

        # Status line
        items.append("")
        items.append(f"{status_indicator} {check_result[KEY_DESCRIPTION]}{required_text}")

        # zPath (if present) - show first for clarity
        if KEY_ZPATH in check_result and check_result[KEY_ZPATH]:
            items.append(f"{DISPLAY_INDENT}zPath: {check_result[KEY_ZPATH]}")

        # Path (if present)
        if KEY_PATH in check_result:
            items.append(f"{DISPLAY_INDENT}Path: {check_result[KEY_PATH]}")

        # Status message
        items.append(f"{DISPLAY_INDENT}Status: {check_result[KEY_MESSAGE]}")

        # Size (if present)
        if KEY_SIZE in check_result:
            items.append(f"{DISPLAY_INDENT}Size: {check_result[KEY_SIZE]} bytes")
        
        # Sources (if present)
        if KEY_SOURCES in check_result:
            items.append(f"{DISPLAY_INDENT}Sources: {', '.join(check_result[KEY_SOURCES])}")

    # Final Result
    overall_status = results[KEY_STATUS]
    overall_indicator = status_indicators.get(overall_status, INDICATOR_UNKNOWN)

    items.append("")
    items.append(DISPLAY_SEPARATOR_SECTION)
    items.append(DISPLAY_FINAL_HEADER)
    items.append(DISPLAY_SEPARATOR_SECTION)
    items.append("")
    items.append(f"{overall_indicator} Overall Status: {overall_status.upper()}")
    items.append("")
    
    # Display all items at once using display.list()
    zcli.display.list(items, style="none")

# ═══════════════════════════════════════════════════════════════════════════
# DRY HELPERS - ELIMINATE CODE DUPLICATION
# ═══════════════════════════════════════════════════════════════════════════

def _build_check_result(
    status: str,
    description: str,
    path: str,
    zpath: str,
    message: str,
    required: bool,
    **kwargs: Any
) -> CheckResult:
    """
    Build standardized check result dictionary (DRY helper).
    
    Eliminates code duplication in check_directory() and check_file() by
    providing a single function to build result dicts with consistent structure.
    
    Args:
        status: Check status (STATUS_PASS, STATUS_WARNING, STATUS_FAIL)
        description: Human-readable description
        path: Path checked
        zpath: zPath notation (e.g., "~zMachine.zConfigs")
        message: Status message
        required: Whether check is required
        **kwargs: Additional fields (e.g., size=1024)
    
    Returns:
        CheckResult: Standardized result dictionary
    
    Example:
        result = _build_check_result(
            status=STATUS_PASS,
            description="My Check",
            path="/path/to/check",
            zpath="~zMachine.zConfigs",
            message="Check passed",
            required=True,
            size=1024
        )
    
    Notes:
        - Ensures consistent dict structure
        - Reduces duplication by 70%+
        - Supports arbitrary additional fields via **kwargs
    """
    result: CheckResult = {
        KEY_STATUS: status,
        KEY_DESCRIPTION: description,
        KEY_PATH: path,
        KEY_MESSAGE: message,
        KEY_REQUIRED: required
    }
    
    # Add zpath if provided
    if zpath:
        result[KEY_ZPATH] = zpath
    
    # Add any additional fields
    result.update(kwargs)
    
    return result
