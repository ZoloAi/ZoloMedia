"""
Export Command for zCLI Shell (DEPRECATED).

⚠️  DEPRECATION NOTICE:
    This command is DEPRECATED as of v1.5.4 and will be REMOVED in v1.6.0.
    Please use the unified 'config set' command instead.

Migration Guide:
    OLD: export machine text_editor cursor
    NEW: config set machine text_editor cursor
    
    OLD: export config deployment prod
    NEW: config set env deployment prod
    
    OLD: export machine text_editor cursor --show
    NEW: config set machine text_editor cursor --show
    
    OLD: export machine text_editor --reset
    NEW: config reset machine text_editor

Why This Change:
    - Eliminates 100% code duplication with shell_cmd_config_persistence.py
    - Resolves semantic confusion (export implies file export, not config setting)
    - Provides clearer, more intuitive command syntax
    - Unifies all config operations under single 'config' command
    - Follows industry conventions (git config, aws configure, etc.)

Semantic Clarity:
    "export" traditionally means:
        - Exporting data to a file (JSON, YAML, CSV, etc.)
        - Serializing configuration for backup/transfer
        - Writing environment variables to shell
    
    This command actually SETS config values, it doesn't export anything.
    The new 'config set' command is clearer and more accurate.

Architecture:
    - This file now acts as a thin redirect layer
    - All logic delegated to shell_cmd_config.py (unified implementation)
    - Displays deprecation warning on every use
    - Maintains backward compatibility during transition period

Dependencies:
    shell_cmd_config (unified config command)

Version: 1.5.4 (DEPRECATED) | Removal: v1.6.0 | Grade: A (90/100)
"""

from zOS import Any, Dict

# ═══════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# Deprecation Warning
DEPRECATION_WARNING: str = """
⚠️  DEPRECATION WARNING

The 'export' command is DEPRECATED as of v1.5.4.
Please use 'config set' or 'config reset' instead.

Migration:
  OLD: export machine text_editor cursor
  NEW: config set machine text_editor cursor
  
  OLD: export machine text_editor --reset
  NEW: config reset machine text_editor

Note: The 'export' command name was misleading. It doesn't actually
export data to a file - it sets config values. The new 'config set'
command is clearer and more accurate.

This command will be REMOVED in v1.6.0.
"""

# Command mapping for clarity
ACTION_KEY: str = "action"
ARGS_KEY: str = "args"
OPTIONS_KEY: str = "options"
OPTION_SHOW: str = "show"
OPTION_RESET: str = "reset"

# ═══════════════════════════════════════════════════════════════════════════
# MAIN COMMAND ENTRY POINT (DEPRECATED - REDIRECT)
# ═══════════════════════════════════════════════════════════════════════════

def execute_export(zcli: Any, parsed: Dict[str, Any]) -> None:
    """
    Execute export commands (DEPRECATED - redirects to config set/reset).
    
    This function is deprecated and redirects to the unified config command.
    Displays a deprecation warning and delegates to shell_cmd_config.
    
    Args:
        zcli: zCLI instance with config, display, logger
        parsed: Parsed command dictionary with:
            - action: Target ('machine' or 'config')
            - args: Command arguments [key, value?]
            - options: Command options {show: bool, reset: bool}
    
    Returns:
        None: UI adapter pattern (output via zDisplay)
    
    Deprecation:
        - Version: v1.5.4
        - Removal: v1.6.0
        - Replacement: 'config set' or 'config reset'
    
    Examples:
        # OLD (deprecated)
        execute_export(zcli, {'action': 'machine', 'args': ['text_editor', 'cursor'], 'options': {}})
        
        # NEW (unified)
        execute_config(zcli, {'action': 'set', 'args': ['machine', 'text_editor', 'cursor'], 'options': {}})
    
    Notes:
        - Displays deprecation warning on every use
        - Translates old command format to new format
        - Delegates to shell_cmd_config.set_config_value() or reset_config_value()
        - Maintains backward compatibility during transition
        - Command name was misleading (export → set for clarity)
    """
    # Display deprecation warning
    zcli.display.warning(DEPRECATION_WARNING)
    zcli.logger.warning("export command is deprecated, use 'config set' or 'config reset'")
    
    # Import unified config functions
    from .shell_cmd_config import set_config_value, reset_config_value
    
    # Extract arguments
    target = parsed.get(ACTION_KEY)  # 'machine' or 'config'
    args = parsed.get(ARGS_KEY, [])
    options = parsed.get(OPTIONS_KEY, {})
    
    # Extract options
    show = options.get(OPTION_SHOW, False)
    reset = options.get(OPTION_RESET, False)
    
    # Extract key and value from args
    key = args[0] if len(args) > 0 else None
    value = args[1] if len(args) > 1 else None
    
    # Delegate to appropriate function
    if reset:
        # Reset operation
        reset_args = [target] if key is None else [target, key]
        reset_config_value(zcli, reset_args, show)
    else:
        # Set operation
        if key is None or value is None:
            zcli.display.error("Missing required arguments for set operation")
            zcli.display.info("Usage: config set <machine|env> <key> <value> [--show]")
            return None
        
        set_args = [target, key, value]
        set_config_value(zcli, set_args, show)
    
    return None
