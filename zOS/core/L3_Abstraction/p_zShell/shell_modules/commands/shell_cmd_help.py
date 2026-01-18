# zCLI/subsystems/zShell/shell_modules/commands/shell_cmd_help.py
"""
Shell Command Help System - Declarative Help for Terminal Commands.

This module provides comprehensive help documentation specifically for shell terminal
commands (Group A: Basic Terminal Commands). It implements a dual-mode help system:
direct command help (via zDisplay) and declarative help UI (via zWalker).

═══════════════════════════════════════════════════════════════════════════════
ARCHITECTURAL DESIGN
═══════════════════════════════════════════════════════════════════════════════

Two-Tier Help System:
    • shell_cmd_help.py   → Shell terminal commands (where, shortcut, cd, cwd, ls)
                            Scope: Group A - Basic terminal navigation
    • shell_help.py       → System/general help (welcome messages, tips)
                            Scope: General zCLI information

Command Scope (Group A Only):
    This help system covers ONLY Group A commands - basic terminal navigation and
    convenience commands that users interact with when IN the shell. It does NOT
    cover zCLI subsystem operations (data, func, auth, etc.) as those belong to
    their respective subsystems and are documented in zUI.zcli_sys.yaml.

═══════════════════════════════════════════════════════════════════════════════
DUAL-MODE HELP SYSTEM
═══════════════════════════════════════════════════════════════════════════════

Mode 1: Direct Command Help (Terminal Output)
    Usage:    help <command>
    Method:   _show_command_help()
    Display:  zDisplay.list() with formatted sections
    Example:  help ls → Shows detailed ls command help directly

Mode 2: Declarative Help UI (Walker Navigation)
    Usage:    help (no args)
    Method:   Launch walker with zUI.zcli_sys.yaml Help block
    Display:  Interactive menu via zWalker
    Example:  help → Opens Help menu with all zCLI documentation

Walker Integration:
    The declarative help UI is launched via zWalker, which reads the Help block
    from zUI.zcli_sys.yaml. This provides an interactive navigation experience
    across all zCLI documentation sections.

═══════════════════════════════════════════════════════════════════════════════
SESSION REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

Required Session Keys:
    SESSION_KEY_ZSPARK:  Contains zSpark object for walker configuration
        Used to set zVaFile and zBlock for help UI launch

Walker Subsystem:
    The help command requires the walker subsystem to be initialized.
    Defensive checks ensure graceful fallback if walker is unavailable.

═══════════════════════════════════════════════════════════════════════════════
SHELL_COMMANDS DICTIONARY STRUCTURE
═══════════════════════════════════════════════════════════════════════════════

Each command entry contains:
    desc:           Brief description (1 line)
    syntax:         Command syntax
    actions:        Available actions (optional)
    options:        Command options (optional)
    legacy_options: Industry-standard option aliases (optional)
    path_formats:   Supported path formats (optional)
    display:        Display format info (optional)
    prompt_formats: Prompt format examples (optional)
    aliases:        Command aliases (optional)
    examples:       Usage examples (required)
    notes:          Additional notes (optional)

═══════════════════════════════════════════════════════════════════════════════
USAGE
═══════════════════════════════════════════════════════════════════════════════

Direct Command Help:
    help ls           - Show detailed ls command help
    help shortcut     - Show detailed shortcut command help
    help pwd          - Show pwd help (handles aliases)

Declarative Help UI:
    help              - Launch interactive help menu

Integration:
    # In shell executor
    execute_help(zcli, {"args": []})          # Launch help UI
    execute_help(zcli, {"args": ["ls"]})      # Show ls help directly

═══════════════════════════════════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

Terminal Mode (Direct Help):
    zOS> help ls
    
    ═══════════════════════ LS Command ════════════════════════
    
    Description:
      List directory contents (list/dir aliases)
    
    Syntax:
      ls [path] [options]
    ...

Walker Mode (Declarative Help):
    zOS> help
    
    ══════════════════════════════════════════════════════════
                          zCLI Help
    ══════════════════════════════════════════════════════════
    
    [1] CD - Change Directory
    [2] Session - Session Management
    [3] Walker - Walker Navigation
    ...
"""

from typing import Any, Dict, List

# Import session constants from zConfig
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_ZSPARK


# ═══════════════════════════════════════════════════════════════════════════
# MODULE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# Walker Configuration
HELP_VAFILE_PATH: str = "@.zCLI.UI.zUI.zcli_sys"
HELP_BLOCK_NAME: str = "Help"

# Error Messages
MSG_NO_HELP_AVAILABLE: str = "No help available for: {command}"
MSG_USE_HELP_LIST: str = "Use 'help' to see all available shell commands"
MSG_WALKER_NOT_AVAILABLE: str = "Help menu requires walker subsystem"
MSG_WALKER_NOT_INITIALIZED: str = "Walker subsystem not initialized"
MSG_LAUNCH_FAILED: str = "Failed to launch help menu: {error}"

# Log Messages
LOG_LAUNCHING_HELP: str = "Launching declarative help UI via walker"
LOG_SHOWING_COMMAND_HELP: str = "Showing help for command: %s"
LOG_COMMAND_NOT_FOUND: str = "Help requested for unknown command: %s"
LOG_WALKER_LAUNCH_SUCCESS: str = "Help menu launched successfully"
LOG_WALKER_LAUNCH_FAILED: str = "Help menu launch failed: %s"

# Command Aliases
ALIAS_PWD: str = "pwd"
ALIAS_LIST: str = "list"
ALIAS_DIR: str = "dir"

# Dictionary Keys (for SHELL_COMMANDS structure)
KEY_DESC: str = "desc"
KEY_SYNTAX: str = "syntax"
KEY_ACTIONS: str = "actions"
KEY_OPTIONS: str = "options"
KEY_LEGACY_OPTIONS: str = "legacy_options"
KEY_PATH_FORMATS: str = "path_formats"
KEY_DISPLAY: str = "display"
KEY_PROMPT_FORMATS: str = "prompt_formats"
KEY_ALIASES: str = "aliases"
KEY_EXAMPLES: str = "examples"
KEY_NOTES: str = "notes"

# Display Constants
HEADER_SHELL_COMMANDS: str = "Shell Terminal Commands"
HEADER_COMMAND_HELP: str = "{command} Command"
SECTION_GROUP_A: str = "Basic Terminal Commands (Group A):"
SECTION_DESCRIPTION: str = "Description:"
SECTION_SYNTAX: str = "Syntax:"
SECTION_ACTIONS: str = "Actions:"
SECTION_OPTIONS: str = "Options:"
SECTION_LEGACY_OPTIONS: str = "Legacy Options (industry standard):"
SECTION_PATH_FORMATS: str = "Path Formats:"
SECTION_DISPLAY: str = "Display:"
SECTION_PROMPT_FORMATS: str = "Prompt Formats:"
SECTION_ALIASES: str = "Aliases:"
SECTION_EXAMPLES: str = "Examples:"
SECTION_NOTES: str = "Notes:"
SECTION_USAGE: str = "Usage:"

# Formatting Constants
FORMAT_COMMAND_ITEM: str = "{cmd:20} {desc}"
FORMAT_INDENT: str = "  {text}"
FORMAT_NOTE: str = "  - {note}"


# ═══════════════════════════════════════════════════════════════════════════
# SHELL COMMANDS DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════════

# Shell Commands Documentation (Group A: Basic Terminal Commands)
SHELL_COMMANDS: Dict[str, Dict[str, Any]] = {
    "where": {
        "desc": "Toggle zPath display in shell prompt",
        "syntax": "where [action]",
        "actions": [
            "(no args) or status - Show current mode",
            "on                  - Enable zPath in prompt",
            "off                 - Disable zPath (default)",
            "toggle              - Switch between on/off",
        ],
        "examples": [
            "where                 # Check current status",
            "where on              # Show zPath in prompt",
            "where off             # Hide zPath from prompt",
            "where toggle          # Toggle current state",
        ],
        "prompt_formats": [
            "Default (off):  zOS> ",
            "Enabled (on):   zCLI [~.Projects.zolo-zcli]> ",
        ],
    },
    "shortcut": {
        "desc": "Create and manage command shortcuts",
        "syntax": "shortcut [name[=command]] [options]",
        "actions": [
            "(no args)            - List all shortcuts",
            "name=\"command\"       - Create/update shortcut",
            "--remove name        - Remove shortcut",
            "--save [file]        - Save shortcuts to file",
            "--load [file]        - Load shortcuts from file",
            "--clear              - Clear all shortcuts",
        ],
        "examples": [
            "shortcut                           # List all shortcuts",
            "shortcut demos=\"cd @.Demos\"         # Create shortcut",
            "shortcut ll=\"ls --sizes --hidden\"   # Create ls alias",
            "shortcut --remove ll               # Remove shortcut",
            "shortcut --save my_shortcuts.json  # Save to file",
            "shortcut --load my_shortcuts.json  # Load from file",
            "shortcut --clear                   # Clear all",
        ],
        "notes": [
            "Shortcuts persist for the session duration",
            "Use save/load for cross-session persistence",
        ],
    },
    "cd": {
        "desc": "Change current working directory",
        "syntax": "cd [path]",
        "path_formats": [
            "cd @.Demos           # Workspace-relative zPath",
            "cd ~                 # Home directory",
            "cd ..                # Parent directory",
            "cd /absolute/path    # Absolute path",
        ],
        "examples": [
            "cd @.Demos                    # Navigate to workspace/Demos",
            "cd @.zTestSuite.demos         # Deep navigation with zPath",
            "cd ~                          # Go to home directory",
            "cd ..                         # Go up one level",
        ],
        "notes": [
            "Supports zPath syntax (@.), absolute (~), and relative (..) paths",
            "Changes both OS and zSession working directory",
        ],
    },
    "cwd": {
        "desc": "Show current working directory (pwd alias)",
        "syntax": "cwd  or  pwd",
        "display": [
            "1. OS Path     - Standard filesystem path",
            "2. zPath       - zCLI declarative path format",
        ],
        "examples": [
            "cwd                   # Show current directory (both formats)",
            "pwd                   # Same as cwd (Unix compatibility)",
        ],
        "aliases": [
            "cwd - Primary (Current Working Directory)",
            "pwd - Alias (Unix standard: Print Working Directory)",
        ],
        "notes": [
            "Displays both OS path and zPath representation",
            "Use 'where on' to show zPath in prompt permanently",
        ],
    },
    "ls": {
        "desc": "List directory contents (list/dir aliases)",
        "syntax": "ls [path] [options]",
        "options": [
            "--sizes / -s         - Show file sizes",
            "--hidden / -h        - Show hidden files (.*)",
            "--deep / -d          - Recursive listing",
            "--files / -f         - Files only",
            "--dirs / -r          - Directories only",
        ],
        "legacy_options": [
            "-l, --long           - Same as --sizes (industry standard)",
            "-a, --all            - Same as --hidden (industry standard)",
            "-r, --recursive      - Same as --deep (industry standard)",
        ],
        "examples": [
            "ls                            # List current directory",
            "ls @.Demos                    # List workspace/Demos",
            "ls --sizes                    # Show with file sizes",
            "ls --hidden                   # Include hidden files",
            "ls --deep                     # Recursive listing",
            "ls --files                    # Files only",
            "ls --dirs                     # Directories only",
            "ls --sizes --hidden --deep    # Combined options",
        ],
        "aliases": [
            "ls   - Primary (Unix standard)",
            "list - Alias (beginner-friendly)",
            "dir  - Alias (Windows compatibility)",
        ],
        "notes": [
            "Supports both zPath (@.) and standard paths",
            "Output uses zDisplay list event for consistent formatting",
        ],
    },
}

# Command order for display
COMMAND_ORDER = ["where", "shortcut", "cd", "cwd", "ls"]


def execute_help(zcli: Any, parsed: Dict[str, Any]) -> None:
    """
    Execute help command to launch declarative help UI via walker.
    
    This is the shell-specific help system that documents only Group A commands
    (basic terminal commands) using zCLI's declarative paradigm. The help menu
    is defined in zUI.zcli_sys.yaml and navigated via walker.
    
    Dual-Mode Operation:
        1. With args (help <command>): Show direct command help via zDisplay
        2. No args (help): Launch declarative help UI via walker
    
    Args:
        zcli: zCLI instance with display, session, and walker subsystems
        parsed: Parsed command dictionary with optional args
        
    Returns:
        None (UI adapter pattern - displays help or launches walker)
        
    Session Requirements:
        SESSION_KEY_ZSPARK: Must exist in session for walker configuration
    
    Subsystem Requirements:
        walker: Must be initialized for declarative help UI
        
    Examples:
        >>> execute_help(zcli, {"args": []})        # Launch help menu
        >>> execute_help(zcli, {"args": ["ls"]})    # Show ls help directly
        >>> execute_help(zcli, {"args": ["pwd"]})   # Show pwd help (handles aliases)
    
    Error Handling:
        - Missing walker: Display error message, graceful fallback
        - Invalid command: Display error with available commands list
        - Walker launch failure: Display error with exception details
    """
    args = parsed.get("args", [])
    
    # If specific command requested, show detailed help directly
    if args:
        command_name = args[0].lower()
        zcli.logger.debug(LOG_SHOWING_COMMAND_HELP, command_name)
        _show_command_help(zcli, command_name)
        return
    
    # Launch declarative help UI via walker
    zcli.logger.debug(LOG_LAUNCHING_HELP)
    
    # Validate walker subsystem exists
    if not hasattr(zcli, 'walker') or zcli.walker is None:
        zcli.logger.warning(LOG_WALKER_LAUNCH_FAILED, "walker subsystem not found")
        zcli.display.error(MSG_WALKER_NOT_AVAILABLE)
        zcli.display.info(MSG_USE_HELP_LIST)
        return
    
    try:
        # Set zSpark configuration for walker
        # Use zcli.zspark_obj directly (always exists, not None)
        zcli.zspark_obj["zVaFile"] = HELP_VAFILE_PATH
        zcli.zspark_obj["zBlock"] = HELP_BLOCK_NAME
        
        # Launch walker (preserves current zMode: Terminal or zBifrost)
        zcli.walker.run()
        
        zcli.logger.debug(LOG_WALKER_LAUNCH_SUCCESS)
        
    except Exception as e:
        zcli.logger.error(LOG_WALKER_LAUNCH_FAILED, str(e))
        zcli.display.error(MSG_LAUNCH_FAILED.format(error=str(e)))
        zcli.display.info(MSG_USE_HELP_LIST)


def _show_command_help(zcli: Any, command_name: str) -> None:
    """
    Display detailed help for a specific shell command.
    
    This function normalizes command names (handles aliases), validates the command
    exists in SHELL_COMMANDS, and displays comprehensive help documentation using
    zDisplay's list event for consistent formatting.
    
    Args:
        zcli: zCLI instance with display and logger
        command_name: Name of command to show help for (aliases supported)
        
    Returns:
        None (UI adapter pattern - displays via zDisplay)
        
    Display Sections (conditional):
        - Description (required)
        - Syntax (required)
        - Actions (optional)
        - Options (optional)
        - Legacy Options (optional)
        - Path Formats (optional)
        - Display Formats (optional)
        - Prompt Formats (optional)
        - Aliases (optional)
        - Examples (required)
        - Notes (optional)
    
    Alias Handling:
        Automatically normalizes aliases to primary command names:
        - pwd → cwd
        - list → ls
        - dir → ls
    
    Examples:
        >>> _show_command_help(zcli, "ls")      # Direct command
        >>> _show_command_help(zcli, "pwd")     # Alias → cwd
        >>> _show_command_help(zcli, "list")    # Alias → ls
    
    Error Handling:
        - Unknown command: Display error with available commands hint
        - Logs command not found warning
    """
    # Normalize command name (handle aliases)
    normalized_name = _normalize_command_name(command_name)
    
    # Validate command exists
    if normalized_name not in SHELL_COMMANDS:
        zcli.logger.warning(LOG_COMMAND_NOT_FOUND, command_name)
        zcli.display.error(MSG_NO_HELP_AVAILABLE.format(command=command_name))
        zcli.display.info(MSG_USE_HELP_LIST)
        return
    
    cmd_info = SHELL_COMMANDS[normalized_name]
    
    # Header
    header_text = HEADER_COMMAND_HELP.format(command=normalized_name.upper())
    zcli.display.header(header_text, style="box")
    
    # Build list items for all sections
    items: List[str] = [
        "",
        SECTION_DESCRIPTION,
        FORMAT_INDENT.format(text=cmd_info[KEY_DESC]),
        "",
        SECTION_SYNTAX,
        FORMAT_INDENT.format(text=cmd_info[KEY_SYNTAX]),
        ""
    ]
    
    # Actions (if present)
    if KEY_ACTIONS in cmd_info:
        items.append(SECTION_ACTIONS)
        items.extend([FORMAT_INDENT.format(text=action) for action in cmd_info[KEY_ACTIONS]])
        items.append("")
    
    # Options (if present)
    if KEY_OPTIONS in cmd_info:
        items.append(SECTION_OPTIONS)
        items.extend([FORMAT_INDENT.format(text=option) for option in cmd_info[KEY_OPTIONS]])
        items.append("")
    
    # Legacy Options (if present)
    if KEY_LEGACY_OPTIONS in cmd_info:
        items.append(SECTION_LEGACY_OPTIONS)
        items.extend([FORMAT_INDENT.format(text=option) for option in cmd_info[KEY_LEGACY_OPTIONS]])
        items.append("")
    
    # Path Formats (if present)
    if KEY_PATH_FORMATS in cmd_info:
        items.append(SECTION_PATH_FORMATS)
        items.extend([FORMAT_INDENT.format(text=fmt) for fmt in cmd_info[KEY_PATH_FORMATS]])
        items.append("")
    
    # Display Formats (if present)
    if KEY_DISPLAY in cmd_info:
        items.append(SECTION_DISPLAY)
        items.extend([FORMAT_INDENT.format(text=disp) for disp in cmd_info[KEY_DISPLAY]])
        items.append("")
    
    # Prompt Formats (if present)
    if KEY_PROMPT_FORMATS in cmd_info:
        items.append(SECTION_PROMPT_FORMATS)
        items.extend([FORMAT_INDENT.format(text=fmt) for fmt in cmd_info[KEY_PROMPT_FORMATS]])
        items.append("")
    
    # Aliases (if present)
    if KEY_ALIASES in cmd_info:
        items.append(SECTION_ALIASES)
        items.extend([FORMAT_INDENT.format(text=alias) for alias in cmd_info[KEY_ALIASES]])
        items.append("")
    
    # Examples (required)
    items.append(SECTION_EXAMPLES)
    items.extend([FORMAT_INDENT.format(text=example) for example in cmd_info[KEY_EXAMPLES]])
    
    # Notes (if present)
    if KEY_NOTES in cmd_info:
        items.append("")
        items.append(SECTION_NOTES)
        items.extend([FORMAT_NOTE.format(note=note) for note in cmd_info[KEY_NOTES]])
    
    # Display as a single list (UI adapter pattern)
    zcli.display.list(items, style="none")


def _normalize_command_name(command_name: str) -> str:
    """
    Normalize command name to handle aliases.
    
    Maps command aliases to their primary command names for consistent help
    documentation lookup. Supports Unix-standard (pwd), beginner-friendly (list),
    and Windows-compatible (dir) aliases.
    
    Args:
        command_name: Command name or alias (case-insensitive)
        
    Returns:
        Normalized primary command name (lowercase)
        
    Alias Mappings:
        pwd  → cwd   (Unix standard: Print Working Directory)
        list → ls    (Beginner-friendly alternative)
        dir  → ls    (Windows compatibility)
    
    Examples:
        >>> _normalize_command_name("pwd")
        'cwd'
        >>> _normalize_command_name("PWD")
        'cwd'
        >>> _normalize_command_name("list")
        'ls'
        >>> _normalize_command_name("dir")
        'ls'
        >>> _normalize_command_name("ls")
        'ls'
        >>> _normalize_command_name("where")
        'where'
    
    Notes:
        - Case-insensitive: "PWD", "pwd", "Pwd" all map to "cwd"
        - Unknown aliases return as-is (lowercased)
        - Uses constants for alias definitions
    """
    # Alias mapping (using constants)
    alias_map: Dict[str, str] = {
        ALIAS_PWD: "cwd",
        ALIAS_LIST: "ls",
        ALIAS_DIR: "ls",
    }
    
    return alias_map.get(command_name.lower(), command_name.lower())
