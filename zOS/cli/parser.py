# zSys/cli/parser.py
"""Argument parser configuration for zolo CLI."""

import argparse


class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter to color option strings in help output."""
    
    def _format_action_invocation(self, action):
        """Override to add SECONDARY color (yellow) to option strings."""
        if not action.option_strings:
            # Positional argument
            return super()._format_action_invocation(action)
        else:
            # Optional argument - color it yellow (SECONDARY)
            parts = []
            for option_string in action.option_strings:
                parts.append(f"\033[93m{option_string}\033[0m")
            return ', '.join(parts)


def create_parser():
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="\033[92mzOS\033[0m - the official ecosystem for Zolo applications and services",
        prog="zolo",
        formatter_class=ColoredHelpFormatter,
        add_help=False,  # Disable automatic -h, we'll add --help manually
    )
    
    # ============================================================================
    # Available Commands (added FIRST to appear before options)
    # ============================================================================
    # Show what running 'zolo' does, subcommands will be added surgically
    
    subparsers = parser.add_subparsers(
        dest="command",
        title="available commands",
        description="  \033[96mzolo\033[0m              Show version and installed products\n  \033[96mzolo machine\033[0m      Show machine configuration\n  \033[96mzolo open\033[0m         Open file or URL",
    )
    # Override the metavar to hide auto-generated command list
    subparsers.metavar = ""
    
    # Machine subcommand - Show machine configuration
    machine_parser = subparsers.add_parser(
        "machine",
        add_help=False,
        formatter_class=ColoredHelpFormatter,
        description="Show machine configuration from zConfig.machine.zolo"
    )
    machine_parser.add_argument("--help", action="help", help="Show this help message and exit")
    machine_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    machine_parser.add_argument("--open", action="store_true", 
                                help="Open configuration file in your IDE")
    machine_parser.add_argument("--edit", action="store_true",
                                help="Interactive editor for user preferences")
    
    # Machine filters (mutually exclusive)
    machine_filter = machine_parser.add_mutually_exclusive_group()
    machine_filter.add_argument("--system", action="store_true", 
                                help="Show system-detected configuration (locked)")
    machine_filter.add_argument("--user", action="store_true",
                                help="Show user preferences (editable)")
    
    # Open subcommand - Open file or URL
    open_parser = subparsers.add_parser(
        "open",
        add_help=False,
        formatter_class=ColoredHelpFormatter,
        description="Open files in your configured IDE or URLs in your browser"
    )
    open_parser.add_argument("--help", action="help", help="Show this help message and exit")
    open_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    open_parser.add_argument("target", help="File path or URL to open")
    
    # ============================================================================
    # Options (added AFTER commands to appear second)
    # ============================================================================
    
    # Add help manually (without -h shortcut)
    parser.add_argument("--help", action="help", help="Show this help message and exit")
    
    parser.add_argument("--version", action="version", version=_format_version_string())
    parser.add_argument("--verbose", action="store_true", 
                      help="Enable verbose logging")
    parser.add_argument("--dev", action="store_true",
                      help="Enable development mode")
    
    # Reorder action groups to show commands before options
    # Swap the optional arguments and subparsers groups
    parser._action_groups.reverse()
    
    # ============================================================================
    # Framework Commands (zKernel)
    # ============================================================================
    # Framework commands (shell, migrate, ztests, uninstall) have been moved to:
    # zKernel/src/cli_integration/
    #
    # They will be registered dynamically when zKernel is properly integrated.
    # See: zKernel/src/cli_integration/README.md for integration plan.
    
    return parser


def _get_ecosystem_version():
    """Get version info for all zOS packages."""
    versions = {}
    
    # Try to get each package version
    packages = ['zKernel', 'zolo', 'zOS']
    
    for name in packages:
        try:
            if name == 'zKernel':
                # Import zKernel version module
                from zKernel.version import __version__  # pylint: disable=import-outside-toplevel
                versions[name] = __version__
            elif name == 'zolo':
                # Import zolo (LSP) package
                import zolo  # pylint: disable=import-outside-toplevel
                versions[name] = getattr(zolo, '__version__', '1.0.0')
            elif name == 'zOS':
                # Import zOS package
                import zOS  # pylint: disable=import-outside-toplevel
                versions[name] = getattr(zOS, '__version__', '1.0.0')
        except (ImportError, AttributeError):
            versions[name] = 'not installed'
    
    return versions


def _format_version_string():
    """Format zOS version string."""
    versions = _get_ecosystem_version()
    lines = ["zolo OS"]
    for name, version in versions.items():
        lines.append(f"  {name}: {version}")
    return "\n".join(lines)
