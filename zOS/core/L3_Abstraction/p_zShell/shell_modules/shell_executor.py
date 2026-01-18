# zCLI/subsystems/zShell/shell_modules/shell_executor.py

"""
Command Execution Engine with Wizard Canvas Mode Support.

This module provides the core command execution engine for zShell, routing user
commands to their appropriate handlers and managing the interactive wizard canvas
mode for multi-step workflows.

────────────────────────────────────────────────────────────────────────────────
ARCHITECTURE
────────────────────────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────────┐
    │                   COMMAND EXECUTOR                           │
    ├──────────────────────────────────────────────────────────────┤
    │                                                              │
    │  User Input (from InteractiveShell)                         │
    │         ↓                                                    │
    │  execute(command: str)                                       │
    │         ↓                                                    │
    │  ┌──────────────────────┐                                   │
    │  │  Wizard Canvas Mode? │                                   │
    │  └──────────────────────┘                                   │
    │    ↙              ↘                                          │
    │  YES              NO                                         │
    │   ↓               ↓                                          │
    │  Wizard          Normal                                      │
    │  Handler         Parser                                      │
    │   ↓               ↓                                          │
    │  _handle_        _execute_                                   │
    │  wizard_         parsed_                                     │
    │  command()       command()                                   │
    │   ↓               ↓                                          │
    │  18 Shell        Command                                     │
    │  Command         Map                                         │
    │  Executors       Router                                      │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘

────────────────────────────────────────────────────────────────────────────────
WIZARD CANVAS MODE
────────────────────────────────────────────────────────────────────────────────

The wizard canvas mode allows users to build multi-line workflows interactively:

    1. Enter canvas mode:       wizard --start
    2. Type YAML or commands    (each line buffered)
    3. Review buffer:           wizard --show
    4. Clear buffer:            wizard --clear
    5. Execute buffer:          wizard --run
    6. Exit canvas:             wizard --stop

Buffer Format Auto-Detection:
    - YAML format:     Delegates to zWizard.handle() for structured workflows
    - Shell commands:  Converts to wizard format, then delegates to zWizard
    - Transaction:     Supports "_transaction: true" for rollback capabilities

────────────────────────────────────────────────────────────────────────────────
COMMAND ROUTING
────────────────────────────────────────────────────────────────────────────────

The executor routes 18 command types to their handlers:

    Core Commands:      data, func, session, walker, open, auth, load, plugin
    Config Commands:    config, export (deprecated)
    Communication:      comm
    Terminal Commands:  ls, list, dir, cd, cwd, pwd, where, help, shortcut

Command Map Pattern:
    - Dictionary-based routing for O(1) lookup
    - Aliases supported (list→ls, dir→ls, cwd→pwd)
    - Deprecated commands redirected (utils→plugin, export→config)
    - Unknown commands return error dict

────────────────────────────────────────────────────────────────────────────────
MODULE CONSTANTS
────────────────────────────────────────────────────────────────────────────────

**Wizard Commands (5):**
    WIZARD_CMD_START, WIZARD_CMD_STOP, WIZARD_CMD_RUN, WIZARD_CMD_SHOW,
    WIZARD_CMD_CLEAR

**Wizard State Keys (3):**
    WIZARD_KEY_ACTIVE, WIZARD_KEY_LINES, WIZARD_KEY_FORMAT

**Command Types (18):**
    CMD_TYPE_DATA, CMD_TYPE_FUNC, CMD_TYPE_UTILS, CMD_TYPE_SESSION,
    CMD_TYPE_WALKER, CMD_TYPE_OPEN, CMD_TYPE_AUTH, CMD_TYPE_EXPORT,
    CMD_TYPE_CONFIG, CMD_TYPE_COMM, CMD_TYPE_LOAD, CMD_TYPE_PLUGIN,
    CMD_TYPE_LS, CMD_TYPE_LIST, CMD_TYPE_DIR, CMD_TYPE_CD, CMD_TYPE_CWD,
    CMD_TYPE_PWD, CMD_TYPE_SHORTCUT, CMD_TYPE_WHERE, CMD_TYPE_HELP

**Display Constants (7):**
    BANNER_WIDTH, BANNER_CHAR, WIZARD_TITLE, WIZARD_INDENT,
    WIZARD_PROMPT_INDENT, WIZARD_LINE_NUM_WIDTH, WIZARD_STEP_PREFIX

**Status Values (6):**
    STATUS_SUCCESS, STATUS_STOPPED, STATUS_EMPTY, STATUS_SHOWN,
    STATUS_CLEARED, STATUS_ERROR

**Format Types (2):**
    FORMAT_TYPE_YAML, FORMAT_TYPE_COMMANDS

**Messages (17):**
    Error messages (5), Success messages (4), Info messages (8)

────────────────────────────────────────────────────────────────────────────────
DEPENDENCIES
────────────────────────────────────────────────────────────────────────────────

- zParser:  Command parsing and type detection
- zWizard:  Wizard workflow execution with transaction support
- zDisplay: Mode-agnostic output (Terminal + Bifrost)
- zConfig:  SESSION_KEY_WIZARD_MODE constant
- yaml:     YAML parsing for wizard buffer format detection

────────────────────────────────────────────────────────────────────────────────
EXAMPLES
────────────────────────────────────────────────────────────────────────────────

**Normal Command Execution:**
    >>> executor = CommandExecutor(zcli)
    >>> executor.execute("data read users")
    None  # UI adapter pattern - displays results via zDisplay

**Wizard Canvas Mode:**
    >>> executor.execute("wizard --start")
    None  # Enters canvas mode, displays welcome banner
    
    >>> executor.execute("data read users")
    None  # Buffers line
    
    >>> executor.execute("data read posts")
    None  # Buffers line
    
    >>> executor.execute("wizard --show")
    None  # Displays buffer contents
    
    >>> executor.execute("wizard --run")
    None  # Executes buffer via zWizard, clears on success

────────────────────────────────────────────────────────────────────────────────
NOTES
────────────────────────────────────────────────────────────────────────────────

- UI Adapter Pattern: All wizard methods return None, use zDisplay for output
- Command Map: Easily extensible - add new commands by updating command_map dict
- Error Handling: Comprehensive try/except with logging for all execution paths
- Session State: Wizard canvas state persisted in zSession for cross-command continuity
- Format Detection: Smart YAML vs shell command detection with fallback to shell
- Transaction Support: Wizard buffer execution supports rollback via zWizard
"""

import yaml  # pylint: disable=import-error
from zOS import Any, Dict, List, Optional
from .commands import (
    execute_data, execute_func, execute_session, execute_walker,
    execute_open, execute_auth, execute_load,
    execute_export, execute_utils, execute_config, execute_comm,
    execute_wizard_step, execute_plugin,
    execute_ls, execute_cd, execute_pwd, execute_shortcut, execute_where, execute_help
)
from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_session import SESSION_KEY_WIZARD_MODE

# ============================================================
# WIZARD COMMANDS
# ============================================================
WIZARD_CMD_START = "wizard --start"
WIZARD_CMD_STOP = "wizard --stop"
WIZARD_CMD_RUN = "wizard --run"
WIZARD_CMD_SHOW = "wizard --show"
WIZARD_CMD_CLEAR = "wizard --clear"

# ============================================================
# WIZARD STATE KEYS
# ============================================================
WIZARD_KEY_ACTIVE = "active"
WIZARD_KEY_LINES = "lines"
WIZARD_KEY_FORMAT = "format"

# ============================================================
# COMMAND TYPES
# ============================================================
CMD_TYPE_DATA = "data"
CMD_TYPE_FUNC = "func"
CMD_TYPE_UTILS = "utils"
CMD_TYPE_SESSION = "session"
CMD_TYPE_WALKER = "walker"
CMD_TYPE_OPEN = "open"
CMD_TYPE_AUTH = "auth"
CMD_TYPE_EXPORT = "export"
CMD_TYPE_CONFIG = "config"
CMD_TYPE_COMM = "comm"
CMD_TYPE_LOAD = "load"
CMD_TYPE_PLUGIN = "plugin"
CMD_TYPE_LS = "ls"
CMD_TYPE_LIST = "list"
CMD_TYPE_DIR = "dir"
CMD_TYPE_CD = "cd"
CMD_TYPE_CWD = "cwd"
CMD_TYPE_PWD = "pwd"
CMD_TYPE_SHORTCUT = "shortcut"
CMD_TYPE_WHERE = "where"
CMD_TYPE_HELP = "help"

# ============================================================
# DISPLAY CONSTANTS
# ============================================================
BANNER_WIDTH = 63
BANNER_CHAR = "="
WIZARD_TITLE = "Wizard Canvas Mode - Active"
WIZARD_INDENT = 0
WIZARD_PROMPT_INDENT = 1
WIZARD_LINE_NUM_WIDTH = 3
WIZARD_STEP_PREFIX = "step_"

# ============================================================
# STATUS VALUES
# ============================================================
STATUS_SUCCESS = "success"
STATUS_STOPPED = "stopped"
STATUS_EMPTY = "empty"
STATUS_SHOWN = "shown"
STATUS_CLEARED = "cleared"
STATUS_ERROR = "error"

# ============================================================
# FORMAT TYPES
# ============================================================
FORMAT_TYPE_YAML = "yaml"
FORMAT_TYPE_COMMANDS = "commands"

# ============================================================
# ERROR MESSAGES
# ============================================================
ERROR_UNKNOWN_COMMAND = "Unknown command type: {}"
ERROR_EMPTY_BUFFER = "empty_buffer"
ERROR_WIZARD_FAILED = "Wizard execution failed"
ERROR_EXECUTION_FAILED = "Command execution failed: {}"
ERROR_YAML_PARSE = "YAML parsing failed: {} - treating as shell commands"

# ============================================================
# SUCCESS MESSAGES
# ============================================================
SUCCESS_WIZARD_EXIT = "Exited wizard canvas - {} lines discarded"
SUCCESS_WIZARD_CLEAR = "Buffer cleared - {} lines removed"
SUCCESS_WIZARD_RUN = "[OK] {} commands executed successfully"
SUCCESS_WIZARD_COMPLETE = "[OK] Wizard execution complete"
SUCCESS_BUFFER_CLEARED = "Buffer cleared after execution"

# ============================================================
# INFO MESSAGES
# ============================================================
INFO_WIZARD_WELCOME = "Build your workflow by typing YAML structure or shell commands."
INFO_WIZARD_BUILD = "Each Enter adds a new line to the buffer."
INFO_WIZARD_COMMANDS = "Commands:"
INFO_WIZARD_EMPTY = "Wizard buffer empty"
INFO_WIZARD_BUFFER = "Wizard Buffer ({} lines):"
INFO_FORMAT_YAML = "Detected YAML/Hybrid format"
INFO_FORMAT_SHELL = "Detected shell command format"
INFO_TRANSACTION_ENABLED = "Transaction mode: ENABLED"
INFO_EXECUTING_BUFFER = "Executing wizard buffer ({} lines)..."
INFO_EXECUTING_STEPS = "Executing {} steps via zWizard..."
INFO_EXECUTING_COMMANDS = "Executing {} commands via zWizard..."
INFO_WIZARD_EMPTY_RUN = "Wizard buffer empty - nothing to run"
INFO_ENTERED_WIZARD = "Entered wizard canvas mode"

# ============================================================
# WIZARD COMMAND DISPLAY STRINGS
# ============================================================
WIZARD_CMD_SHOW_DISPLAY = "  wizard --show    Show buffer"
WIZARD_CMD_CLEAR_DISPLAY = "  wizard --clear   Clear buffer"
WIZARD_CMD_RUN_DISPLAY = "  wizard --run     Execute buffer"
WIZARD_CMD_STOP_DISPLAY = "  wizard --stop    Exit canvas mode"

# ============================================================
# DICT KEYS
# ============================================================
KEY_TYPE = "type"
KEY_ERROR = "error"
KEY_STATUS = "status"
KEY_FORMAT = "format"
KEY_RESULT = "result"
KEY_EXCEPTION = "exception"
KEY_TRANSACTION = "_transaction"


class CommandExecutor:
    """
    Command execution engine with wizard canvas mode support.
    
    This class routes shell commands to their appropriate handlers and manages
    the interactive wizard canvas mode for building multi-step workflows.
    
    Attributes:
        zcli: The zCLI instance (provides access to all subsystems)
        logger: Logger instance for debugging and error tracking
    """

    def __init__(self, zcli: Any) -> None:
        """
        Initialize command executor.
        
        Args:
            zcli: The zCLI instance
        """
        self.zcli = zcli
        self.logger = zcli.logger

    def execute(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Parse and execute a shell command.
        
        Routes commands through one of two paths:
        1. Wizard canvas mode: Buffers lines or handles wizard commands
        2. Normal mode: Parses command via zParser and routes to handler
        
        Args:
            command: Raw shell command string from user input
            
        Returns:
            Optional[Dict[str, Any]]: Error dict if command fails, None if UI adapter,
                                     or data dict for legacy commands
                                     
        Examples:
            >>> executor.execute("data read users")
            None  # UI adapter - displays via zDisplay
            
            >>> executor.execute("invalid_command")
            {"error": "Unknown command type: invalid_command"}
            
        Notes:
            - Empty commands return None immediately
            - Wizard canvas mode detected via zSession state
            - Comprehensive error handling with logging
        """
        if not command.strip():
            return None

        wizard_mode = self._get_wizard_state()
        if wizard_mode.get(WIZARD_KEY_ACTIVE):
            return self._handle_wizard_command(command, wizard_mode)

        try:
            parsed = self.zcli.zparser.parse_command(command)

            if KEY_ERROR in parsed:
                return parsed

            return self._execute_parsed_command(parsed)

        except Exception as e:  # pylint: disable=broad-except
            self.logger.error(ERROR_EXECUTION_FAILED.format(e))
            return {KEY_ERROR: str(e)}

    def _handle_wizard_command(self, command: str, wizard_mode: Dict[str, Any]) -> None:
        """
        Handle wizard canvas mode commands.
        
        Routes wizard-specific commands (--start, --stop, --run, --show, --clear)
        to their handlers, or buffers regular commands as workflow lines.
        
        Args:
            command: Raw command string (may be wizard command or workflow line)
            wizard_mode: Wizard state dictionary from zSession
            
        Returns:
            None: UI adapter pattern - all output via zDisplay
            
        Examples:
            >>> self._handle_wizard_command("wizard --start", wizard_mode)
            None  # Displays welcome banner
            
            >>> self._handle_wizard_command("data read users", wizard_mode)
            None  # Buffers line silently
            
        Notes:
            - Commands are stripped once at start for efficiency
            - Non-wizard commands are buffered as workflow lines
            - All wizard methods return None (UI adapter pattern)
        """
        command_stripped = command.strip()
        
        if command_stripped == WIZARD_CMD_START:
            return self._wizard_start()
        
        if command_stripped == WIZARD_CMD_STOP:
            return self._wizard_stop()

        if command_stripped == WIZARD_CMD_RUN:
            return self._wizard_run()

        if command_stripped == WIZARD_CMD_SHOW:
            return self._wizard_show()

        if command_stripped == WIZARD_CMD_CLEAR:
            return self._wizard_clear()

        # Buffer line for workflow
        wizard_mode.get(WIZARD_KEY_LINES, []).append(command)
        return None

    def _wizard_start(self) -> None:
        """
        Enter wizard canvas mode and initialize buffer.
        
        Initializes wizard state in zSession and displays welcome banner with
        available commands. Canvas mode remains active until user exits.
        
        Returns:
            None: UI adapter pattern - displays banner via zDisplay
            
        Raises:
            None: Gracefully handles all errors
            
        Examples:
            >>> self._wizard_start()
            None  # Displays:
                  # ===============================================================
                  #            Wizard Canvas Mode - Active
                  # ===============================================================
                  # 
                  # Build your workflow by typing YAML structure or shell commands.
                  # ...
                  
        Notes:
            - Resets buffer on entry (clears any previous state)
            - Banner width is 63 characters for terminal compatibility
            - Logs entry for debugging
        """
        wizard_mode = self._get_wizard_state()
        
        # Initialize wizard mode state
        wizard_mode[WIZARD_KEY_ACTIVE] = True
        wizard_mode[WIZARD_KEY_LINES] = []
        wizard_mode[WIZARD_KEY_FORMAT] = None
        
        self.zcli.logger.info(INFO_ENTERED_WIZARD)
        
        # Display welcome banner
        self._display_wizard_banner()
        
        return None  # UI adapter pattern

    def _wizard_stop(self) -> None:
        """
        Exit wizard mode and discard buffer.
        
        Exits wizard canvas mode, clears buffer, and displays discard summary.
        Buffer contents are lost (not executed).
        
        Returns:
            None: UI adapter pattern - displays exit message via zDisplay
            
        Examples:
            >>> self._wizard_stop()
            None  # Displays: "Exited wizard canvas - 3 lines discarded"
            
        Notes:
            - Buffer is permanently discarded (use --run before --stop to execute)
            - Wizard state fully reset to inactive
            - Line count displayed for user awareness
        """
        wizard_mode = self._get_wizard_state()
        line_count = len(wizard_mode.get(WIZARD_KEY_LINES, []))

        wizard_mode[WIZARD_KEY_ACTIVE] = False
        wizard_mode[WIZARD_KEY_LINES] = []
        wizard_mode[WIZARD_KEY_FORMAT] = None

        self.zcli.display.zDeclare(
            SUCCESS_WIZARD_EXIT.format(line_count),
            color="INFO", indent=WIZARD_INDENT, style="single"
        )
        return None  # UI adapter pattern

    def _wizard_show(self) -> None:
        """
        Display current buffer contents.
        
        Shows all buffered lines with line numbers. Useful for reviewing workflow
        before execution.
        
        Returns:
            None: UI adapter pattern - displays buffer via zDisplay
            
        Examples:
            >>> self._wizard_show()
            None  # Displays:
                  # Wizard Buffer (3 lines):
                  #   1: data read users
                  #   2: data read posts
                  #   3: data read comments
                  
        Notes:
            - Line numbers are right-aligned to 3 characters
            - Empty buffers display "Wizard buffer empty"
            - Buffer unchanged after display (non-destructive)
        """
        wizard_mode = self._get_wizard_state()
        lines = wizard_mode.get(WIZARD_KEY_LINES, [])

        if not lines:
            self.zcli.display.zDeclare(
                INFO_WIZARD_EMPTY,
                color="INFO", indent=WIZARD_INDENT, style="single"
            )
            return None  # UI adapter pattern

        self.zcli.display.zDeclare(
            INFO_WIZARD_BUFFER.format(len(lines)),
            color="INFO", indent=WIZARD_INDENT, style="full"
        )

        for i, line in enumerate(lines, 1):
            self.zcli.display.zDeclare(
                f"{i:{WIZARD_LINE_NUM_WIDTH}}: {line}",
                color="DATA", indent=WIZARD_PROMPT_INDENT, style="single"
            )

        return None  # UI adapter pattern

    def _wizard_clear(self) -> None:
        """
        Clear buffer without exiting wizard mode.
        
        Empties the workflow buffer while keeping canvas mode active. Useful for
        starting over without re-entering wizard mode.
        
        Returns:
            None: UI adapter pattern - displays clear message via zDisplay
            
        Examples:
            >>> self._wizard_clear()
            None  # Displays: "Buffer cleared - 3 lines removed"
            
        Notes:
            - Canvas mode remains active after clear
            - Line count displayed for user awareness
            - Non-destructive to wizard state (only clears buffer)
        """
        wizard_mode = self._get_wizard_state()
        line_count = len(wizard_mode.get(WIZARD_KEY_LINES, []))
        wizard_mode[WIZARD_KEY_LINES] = []

        self.zcli.display.zDeclare(
            SUCCESS_WIZARD_CLEAR.format(line_count),
            color="INFO", indent=WIZARD_INDENT, style="single"
        )
        return None  # UI adapter pattern

    def _wizard_run(self) -> None:
        """
        Execute wizard buffer with smart format detection.
        
        Detects buffer format (YAML vs shell commands), converts to wizard format
        if needed, and delegates to zWizard for execution. Clears buffer on success.
        
        Returns:
            None: UI adapter pattern - displays execution status via zDisplay
            
        Examples:
            >>> self._wizard_run()
            None  # Displays:
                  # Executing wizard buffer (3 lines)...
                  # Detected shell command format
                  # Executing 3 commands via zWizard...
                  # [OK] 3 commands executed successfully
                  # Buffer cleared after execution
                  
        Notes:
            - Empty buffers display warning and return without execution
            - YAML format directly passed to zWizard
            - Shell commands converted to wizard format (step_1, step_2, ...)
            - Buffer cleared only on successful execution
            - Transaction support available via "_transaction: true" in YAML
        """
        wizard_mode = self._get_wizard_state()
        lines = wizard_mode.get(WIZARD_KEY_LINES, [])

        if not lines:
            self.zcli.display.zDeclare(
                INFO_WIZARD_EMPTY_RUN,
                color="WARNING", indent=WIZARD_INDENT, style="single"
            )
            return None  # UI adapter pattern

        buffer = "\n".join(lines)

        self.zcli.display.zDeclare(
            INFO_EXECUTING_BUFFER.format(len(lines)),
            color="EXTERNAL", indent=WIZARD_INDENT, style="full"
        )

        success = self._execute_wizard_buffer(buffer)

        if success:
            wizard_mode[WIZARD_KEY_LINES] = []
            self.zcli.display.zDeclare(
                SUCCESS_BUFFER_CLEARED,
                color="INFO", indent=WIZARD_INDENT, style="single"
            )

        return None  # UI adapter pattern

    def _execute_wizard_buffer(self, buffer: str) -> bool:
        """
        Smart format detection and execution.
        
        Attempts to parse buffer as YAML first. If parsing fails, treats as
        shell commands. Delegates execution to zWizard in both cases.
        
        Args:
            buffer: Multi-line string containing workflow (YAML or shell commands)
            
        Returns:
            bool: True if execution succeeded, False otherwise
            
        Examples:
            >>> self._execute_wizard_buffer("step_1: data read users\\nstep_2: data read posts")
            True  # YAML format, executed via zWizard
            
            >>> self._execute_wizard_buffer("data read users\\ndata read posts")
            True  # Shell format, converted to wizard format, executed
            
        Notes:
            - YAML parsing uses yaml.safe_load (secure)
            - Shell commands converted to wizard format: {"step_1": cmd1, "step_2": cmd2}
            - Transaction support: "_transaction: true" in YAML enables rollback
            - Comprehensive error handling with logging
        """
        try:
            wizard_obj = yaml.safe_load(buffer)

            if isinstance(wizard_obj, dict):
                self.zcli.display.zDeclare(
                    INFO_FORMAT_YAML,
                    color="INFO", indent=WIZARD_PROMPT_INDENT, style="single"
                )

                use_transaction = wizard_obj.get(KEY_TRANSACTION, False)
                if use_transaction:
                    self.zcli.display.zDeclare(
                        INFO_TRANSACTION_ENABLED,
                        color="WARNING", indent=WIZARD_PROMPT_INDENT, style="single"
                    )

                step_count = len([k for k in wizard_obj.keys() if not k.startswith("_")])
                self.zcli.display.zDeclare(
                    INFO_EXECUTING_STEPS.format(step_count),
                    color="EXTERNAL", indent=WIZARD_PROMPT_INDENT, style="single"
                )

                self.zcli.wizard.handle(wizard_obj)

                self.zcli.display.zDeclare(
                    SUCCESS_WIZARD_COMPLETE,
                    color="SUCCESS", indent=WIZARD_PROMPT_INDENT, style="single"
                )
                return True  # Success

        except yaml.YAMLError as e:
            self.logger.debug(ERROR_YAML_PARSE.format(e))

        # Fallback to shell command format
        self.zcli.display.zDeclare(
            INFO_FORMAT_SHELL,
            color="INFO", indent=WIZARD_PROMPT_INDENT, style="single"
        )
        lines = [line.strip() for line in buffer.split("\n") if line.strip()]

        self.zcli.display.zDeclare(
            INFO_EXECUTING_COMMANDS.format(len(lines)),
            color="EXTERNAL", indent=WIZARD_PROMPT_INDENT, style="single"
        )

        # Convert shell commands to wizard format
        wizard_obj = self._convert_commands_to_wizard(lines)

        # Execute via zWizard (provides transaction support and error handling)
        try:
            self.zcli.wizard.handle(wizard_obj)

            self.zcli.display.zDeclare(
                SUCCESS_WIZARD_RUN.format(len(lines)),
                color="SUCCESS", indent=WIZARD_PROMPT_INDENT, style="full"
            )
            return True  # Success
        except Exception as e:  # pylint: disable=broad-except
            self.zcli.display.zDeclare(
                f"Execution error: {e}",
                color="ERROR", indent=WIZARD_PROMPT_INDENT + 1, style="single"
            )
            return False  # Failure

    def _execute_parsed_command(self, parsed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a pre-parsed command.
        
        Routes parsed command to appropriate handler based on command type.
        Uses dictionary-based command map for O(1) lookup.
        
        Args:
            parsed: Parsed command dictionary from zParser
            
        Returns:
            Optional[Dict[str, Any]]: Result from command handler, or error dict
            
        Examples:
            >>> parsed = {"type": "data", "action": "read", "args": ["users"]}
            >>> self._execute_parsed_command(parsed)
            None  # UI adapter - displays via zDisplay
            
            >>> parsed = {"type": "invalid_cmd"}
            >>> self._execute_parsed_command(parsed)
            {"error": "Unknown command type: invalid_cmd"}
            
        Notes:
            - Command map supports aliases (list→ls, dir→ls, cwd→pwd)
            - Deprecated commands still supported but redirect with warnings
            - Unknown commands return error dict (not None)
            - Command validation done by _validate_command_type helper
        """
        command_type = parsed.get(KEY_TYPE)

        if not self._validate_command_type(command_type):
            return {KEY_ERROR: ERROR_UNKNOWN_COMMAND.format(command_type)}

        command_map = {
            CMD_TYPE_DATA: execute_data,
            CMD_TYPE_FUNC: execute_func,
            CMD_TYPE_UTILS: execute_utils,
            CMD_TYPE_SESSION: execute_session,
            CMD_TYPE_WALKER: execute_walker,
            CMD_TYPE_OPEN: execute_open,
            CMD_TYPE_AUTH: execute_auth,
            CMD_TYPE_EXPORT: execute_export,
            CMD_TYPE_CONFIG: execute_config,
            CMD_TYPE_COMM: execute_comm,
            CMD_TYPE_LOAD: execute_load,
            CMD_TYPE_PLUGIN: execute_plugin,
            CMD_TYPE_LS: execute_ls,
            CMD_TYPE_LIST: execute_ls,  # Modern alias for ls (beginner-friendly)
            CMD_TYPE_DIR: execute_ls,   # Windows alias for ls
            CMD_TYPE_CD: execute_cd,
            CMD_TYPE_CWD: execute_pwd,       # Primary: Current Working Directory
            CMD_TYPE_PWD: execute_pwd,       # Alias: Unix compatibility (Print Working Directory)
            CMD_TYPE_SHORTCUT: execute_shortcut,
            CMD_TYPE_WHERE: execute_where,
            CMD_TYPE_HELP: execute_help,
        }

        executor = command_map.get(command_type)
        if executor:
            return executor(self.zcli, parsed)

        return {KEY_ERROR: ERROR_UNKNOWN_COMMAND.format(command_type)}

    def execute_wizard_step(
        self,
        step_key: str,
        step_value: Any,
        step_context: Dict[str, Any]
    ) -> Any:
        """
        Execute a wizard step via the shell's wizard step executor.
        
        Callback method for zWizard to execute individual workflow steps in shell
        context. Handles zData, zFunc, zDisplay, and generic shell commands.
        
        Args:
            step_key: Step identifier (e.g., "step_1", "create_user")
            step_value: Step definition (command string or dict)
            step_context: Shared context dictionary for step execution
            
        Returns:
            Any: Result from step execution (varies by step type)
            
        Examples:
            >>> self.execute_wizard_step("step_1", "data read users", {})
            None  # Executes data read, returns via zDisplay
            
        Notes:
            - Called by zWizard during workflow execution
            - Context shared across all steps in workflow
            - Delegates to shell_cmd_wizard_step.py for implementation
        """
        return execute_wizard_step(self.zcli, step_key, step_value, self.logger, step_context)

    # ============================================================
    # DRY HELPER FUNCTIONS
    # ============================================================

    def _get_wizard_state(self) -> Dict[str, Any]:
        """
        Get wizard state from zSession.
        
        Single access point for wizard canvas state. Uses SESSION_KEY_WIZARD_MODE
        constant from zConfig for consistent key naming.
        
        Returns:
            Dict[str, Any]: Wizard state dictionary with keys: active, lines, format
            
        Examples:
            >>> wizard_state = self._get_wizard_state()
            >>> wizard_state
            {"active": True, "lines": ["cmd1", "cmd2"], "format": None}
            
        Notes:
            - Returns empty dict if wizard_mode not yet initialized
            - Centralized access prevents key name inconsistencies
            - State persisted across command executions
        """
        return self.zcli.session.get(SESSION_KEY_WIZARD_MODE, {})

    def _validate_command_type(self, command_type: Optional[str]) -> bool:
        """
        Validate command type before execution.
        
        Checks if command_type is non-empty and is a string. Logs invalid types
        for debugging.
        
        Args:
            command_type: Command type from parsed command dict
            
        Returns:
            bool: True if valid, False if invalid
            
        Examples:
            >>> self._validate_command_type("data")
            True
            
            >>> self._validate_command_type(None)
            False  # Logs warning
            
            >>> self._validate_command_type("")
            False  # Logs warning
            
        Notes:
            - Validation happens before command map lookup
            - Invalid types logged for debugging
            - Prevents KeyError from dict access
        """
        if not command_type or not isinstance(command_type, str):
            self.logger.warning("Invalid command type: %s", command_type)
            return False
        return True

    def _display_wizard_banner(self) -> None:
        """
        Display wizard canvas welcome banner.
        
        Centralized banner display with consistent formatting. Shows title,
        instructions, and available commands.
        
        Returns:
            None: Displays banner via zDisplay
            
        Notes:
            - Banner width controlled by BANNER_WIDTH constant (63 chars)
            - Title centered within banner
            - Command list uses DATA color for emphasis
        """
        # Top border
        self.zcli.display.zDeclare(
            BANNER_CHAR * BANNER_WIDTH,
            color="INFO", indent=WIZARD_INDENT, style="single"
        )
        # Title
        self.zcli.display.zDeclare(
            WIZARD_TITLE.center(BANNER_WIDTH),
            color="SUCCESS", indent=WIZARD_INDENT, style="single"
        )
        # Bottom border
        self.zcli.display.zDeclare(
            BANNER_CHAR * BANNER_WIDTH,
            color="INFO", indent=WIZARD_INDENT, style="single"
        )
        self.zcli.display.zDeclare("", color="INFO", indent=WIZARD_INDENT, style="single")
        
        # Instructions
        self.zcli.display.zDeclare(
            INFO_WIZARD_WELCOME,
            color="INFO", indent=WIZARD_INDENT, style="single"
        )
        self.zcli.display.zDeclare(
            INFO_WIZARD_BUILD,
            color="INFO", indent=WIZARD_INDENT, style="single"
        )
        self.zcli.display.zDeclare("", color="INFO", indent=WIZARD_INDENT, style="single")
        
        # Commands
        self.zcli.display.zDeclare(
            INFO_WIZARD_COMMANDS,
            color="INFO", indent=WIZARD_INDENT, style="single"
        )
        self.zcli.display.zDeclare(
            WIZARD_CMD_SHOW_DISPLAY,
            color="DATA", indent=WIZARD_INDENT, style="single"
        )
        self.zcli.display.zDeclare(
            WIZARD_CMD_CLEAR_DISPLAY,
            color="DATA", indent=WIZARD_INDENT, style="single"
        )
        self.zcli.display.zDeclare(
            WIZARD_CMD_RUN_DISPLAY,
            color="DATA", indent=WIZARD_INDENT, style="single"
        )
        self.zcli.display.zDeclare(
            WIZARD_CMD_STOP_DISPLAY,
            color="DATA", indent=WIZARD_INDENT, style="single"
        )
        self.zcli.display.zDeclare("", color="INFO", indent=WIZARD_INDENT, style="single")

    def _convert_commands_to_wizard(self, lines: List[str]) -> Dict[str, str]:
        """
        Convert shell command lines to wizard format.
        
        Transforms list of shell commands into wizard-compatible dictionary format
        with step keys (step_1, step_2, ...).
        
        Args:
            lines: List of shell command strings
            
        Returns:
            Dict[str, str]: Wizard format dict with step_N keys
            
        Examples:
            >>> lines = ["data read users", "data read posts"]
            >>> self._convert_commands_to_wizard(lines)
            {"step_1": "data read users", "step_2": "data read posts"}
            
        Notes:
            - Step numbering starts at 1 (user-friendly)
            - WIZARD_STEP_PREFIX constant ensures consistent naming
            - Enables transaction support via zWizard
        """
        wizard_obj = {}
        for i, command in enumerate(lines, 1):
            wizard_obj[f"{WIZARD_STEP_PREFIX}{i}"] = command
        return wizard_obj
