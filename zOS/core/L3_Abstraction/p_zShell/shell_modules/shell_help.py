# zCLI/subsystems/zShell/zShell_modules/zShell_help.py

# zCLI/subsystems/zShell_modules/zShell_help.py - Help System
# --------------------------------------------------------------
"""Help system for zCLI shell - centralized command documentation."""

class HelpSystem:
    """Help system for zCLI - provides documentation and usage examples."""

    def __init__(self, display=None):
        """Initialize help system with display instance."""
        self.display = display

    # Centralized command definitions
    COMMANDS = {
        "data": {
            "desc": "Data operations (CRUD)",
            "usage": [
                "data read <table> [--model PATH] [--limit N] [--where CLAUSE]",
                "data insert <table> [--model PATH] [--fields ...] [--values ...]",
                "data update <table> [--model PATH] [--fields ...] [--values ...] [--where CLAUSE]",
                "data delete <table> [--model PATH] [--where CLAUSE]",
                "data upsert <table> [--model PATH] [--fields ...] [--values ...]",
                "data create <table> [--model PATH]",
                "data drop <table> [--model PATH]",
                "data head <table> [--model PATH]",
            ],
            "examples": [
                "data read users --model @.zTestSuite.demos.zSchema.sqlite_demo",
                "data read users --model $sqlite_demo",
                "data read users,posts --model $sqlite_demo --auto-join",
                "data insert users --model $sqlite_demo --fields name,email --values 'Alice','alice@example.com'",
                "data read users --where 'age > 25' --limit 10",
            ]
        },
        "load": {
            "desc": "Load and cache resources (schemas, UI files)",
            "usage": [
                "load <zPath> [--as ALIAS]",
                "load --show",
                "load --clear [ALIAS]",
            ],
            "examples": [
                "load @.zTestSuite.demos.zSchema.sqlite_demo --as sqlite_demo",
                "load @.zTestSuite.demos.zSchema.csv_demo --as csv_demo",
                "load --show",
                "load --clear sqlite_demo",
            ]
        },
        "wizard": {
            "desc": "Multi-step workflow orchestration",
            "usage": [
                "wizard --start",
                "wizard --stop",
                "wizard --run",
                "wizard --show",
                "wizard --clear",
            ],
            "examples": [
                "wizard --start",
                "  # Enter YAML or commands, then:",
                "wizard --run",
            ]
        },
        "func": {
            "desc": "Execute utility functions",
            "usage": [
                "func <function_name> [args...]",
                "func generate_id <prefix>",
                "func generate_API <prefix>",
            ],
            "examples": [
                "func generate_id zU",
                "func generate_API zApp",
            ]
        },
        "utils": {
            "desc": "Utility operations",
            "usage": [
                "utils <util_name> [args...]",
                "utils hash_password <password>",
            ],
            "examples": [
                "utils hash_password mypassword",
            ]
        },
        "session": {
            "desc": "Session management",
            "usage": [
                "session info",
                "session set <key> <value>",
                "session get <key>",
            ],
            "examples": [
                "session info",
                "session set zSpace /path/to/project",
            ]
        },
        "auth": {
            "desc": "Authentication",
            "usage": [
                "auth login",
                "auth logout",
                "auth status",
            ],
            "examples": [
                "auth login",
                "auth status",
            ]
        },
        "walker": {
            "desc": "Launch UI mode from shell",
            "usage": [
                "walker run",
            ],
            "examples": [
                "session set zSpace /path/to/project",
                "session set zVaFile ui.main.yaml",
                "walker run",
            ]
        },
        "open": {
            "desc": "Open files or URLs",
            "usage": [
                "open <path_or_url>",
            ],
            "examples": [
                "open @.index.html",
                "open https://example.com",
            ]
        },
        "config": {
            "desc": "Configuration management",
            "usage": [
                "config show",
                "config get <key>",
                "config set <key> <value>",
            ],
            "examples": [
                "config show",
                "config get zSpace",
            ]
        },
        "export": {
            "desc": "Export data",
            "usage": [
                "export <table> [--format FORMAT] [--output PATH]",
            ],
            "examples": [
                "export users --format csv --output users.csv",
            ]
        },
        "test": {
            "desc": "Run test suites",
            "usage": [
                "test run",
                "test session",
            ],
            "examples": [
                "test run",
                "test session",
            ]
        },
        "comm": {
            "desc": "Communication/socket operations",
            "usage": [
                "comm <operation> [args...]",
            ],
            "examples": [
                "comm status",
            ]
        },
        "history": {
            "desc": "Command history management",
            "usage": [
                "history",
                "history --clear",
                "history save [filename]",
                "history load [filename]",
                "history search <term>",
            ],
            "examples": [
                "history",
                "history --clear",
                "history save my_commands.json",
                "history search data",
            ]
        },
        "echo": {
            "desc": "Print messages and variables",
            "usage": [
                "echo <message>",
                "echo $variable",
                "echo --success <message>",
                "echo --error <message>",
            ],
            "examples": [
                "echo Hello World",
                "echo $session.zSpace",
                "echo --success Operation complete",
            ]
        },
        "ls": {
            "desc": "List directory contents",
            "usage": [
                "ls [path]",
                "ls @.zPath",
                "ls --recursive",
                "ls --all",
                "ls --long",
            ],
            "examples": [
                "ls",
                "ls @.zTestSuite.demos",
                "ls --recursive",
                "ls --long --all",
            ]
        },
        "cd": {
            "desc": "Change directory",
            "usage": [
                "cd [path]",
                "cd @.zPath",
                "cd ~",
                "cd ..",
            ],
            "examples": [
                "cd @.zTestSuite.demos",
                "cd ~",
                "cd ..",
            ]
        },
        "pwd": {
            "desc": "Print working directory",
            "usage": [
                "pwd",
            ],
            "examples": [
                "pwd",
            ]
        },
        "alias": {
            "desc": "Create command shortcuts",
            "usage": [
                "alias",
                "alias name=\"command\"",
                "alias --remove name",
                "alias --save [filename]",
                "alias --load [filename]",
                "alias --clear",
            ],
            "examples": [
                "alias",
                "alias ll=\"ls --long --all\"",
                "alias demos=\"cd @.zTestSuite.demos\"",
                "alias --remove ll",
                "alias --save my_aliases.json",
            ]
        },
        "plugin": {
            "desc": "Plugin management",
            "usage": [
                "plugin load <path>",
                "plugin show",
                "plugin clear [name]",
                "plugin reload <name>",
            ],
            "examples": [
                "plugin load @.utils.my_plugin",
                "plugin show",
                "plugin clear test_plugin",
                "plugin reload id_generator",
            ]
        },
    }

    def show_help(self):
        """Display comprehensive help information."""
        if self.display:
            self.display.header("zOS Interactive Shell", style="box")
            self.display.break_line()
            self.display.text("Available Commands:")

            # Generate command list
            for cmd, info in HelpSystem.COMMANDS.items():
                self.display.text(f"  {cmd:12} - {info['desc']}", indent=1)

            self.display.break_line()
            self.display.text("General:")
            self.display.text("  help [command]  - Show help (or help for specific command)", indent=1)
            self.display.text("  tips            - Show quick tips", indent=1)
            self.display.text("  clear/cls       - Clear screen", indent=1)
            self.display.text("  exit/quit/q     - Exit shell", indent=1)

            self.display.break_line()
            self.display.text("Usage:")
            self.display.text("  [BULLET] Type 'help <command>' for detailed help on a specific command", indent=1)
            self.display.text("  [BULLET] Use Tab for command history (up/down arrows)", indent=1)
            self.display.text("  [BULLET] Press Ctrl+C to interrupt operations", indent=1)

            self.display.break_line()
            self.display.text("Examples:")
            self.display.text("  help data       - Show detailed data command help", indent=1)
            self.display.text("  help load       - Show detailed load command help", indent=1)
            self.display.text("  help wizard     - Show detailed wizard command help", indent=1)
        else:
            # Fallback if no display available
            print("Help system requires display instance")

    def show_command_help(self, command_type):
        """Show help for a specific command type."""
        if command_type not in HelpSystem.COMMANDS:
            if self.display:
                self.display.warning(f"No help available for: {command_type}")
                self.display.info("Use 'help' for list of all commands")
            else:
                print(f"No help available for: {command_type}")
                print("Use 'help' for list of all commands")
            return

        cmd_info = HelpSystem.COMMANDS[command_type]

        if self.display:
            self.display.header(f"{command_type.upper()} Command Help", style="box")
            self.display.break_line()
            self.display.text("Description:")
            self.display.text(f"  {cmd_info['desc']}", indent=1)

            self.display.break_line()
            self.display.text("Usage:")
            for usage in cmd_info['usage']:
                self.display.text(f"  {usage}", indent=1)

            self.display.break_line()
            self.display.text("Examples:")
            for example in cmd_info['examples']:
                self.display.text(f"  {example}", indent=1)
        else:
            # Fallback
            print(f"Help for {command_type} requires display instance")

    @staticmethod
    def get_welcome_message():
        """Return welcome message for shell startup."""
        return """
============================================================
                    zOS Interactive Shell                 
============================================================

Type 'help' for available commands
Type 'exit' or 'quit' to leave

"""

    @staticmethod
    def get_quick_tips():
        """Return quick tips for shell usage."""
        return """
Quick Tips:
  [BULLET] Press Ctrl+C to interrupt long operations
  [BULLET] Use 'session info' to check your current context
  [BULLET] Commands are case-sensitive
  [BULLET] Use Tab for... (coming soon: autocomplete)
"""
