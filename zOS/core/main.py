"""CLI entry point for the zOS package."""

# Stdlib imports (BEFORE any zOS imports to avoid triggering framework init)
import sys
from pathlib import Path

# zSys imports (system utilities, safe to import)
from zSys.logger import BootstrapLogger  # pylint: disable=import-error
from zSys.install import detect_installation_type  # pylint: disable=import-error
from zSys import cli as cli_commands  # pylint: disable=import-error

# Version imports (safe to import)
from .version import get_version, get_package_info

# CLI parser factory (modular argument parsing)
from .cli import create_parser

def _get_zos_package():
    """Lazy import zOS package to avoid triggering framework initialization at module load."""
    import zOS as zos_package  # pylint: disable=import-outside-toplevel
    return zos_package

# Bootstrap Logger Initialization
boot_logger = BootstrapLogger()

boot_logger.debug("Python: %s", sys.version.split()[0])
boot_logger.debug("Installation: %s", detect_installation_type(_get_zos_package(), detailed=True))

# Main Entry Point
def main() -> None:
    """Main entry point for the zOS command."""

    try:
        parser = create_parser(get_version())

        python_file, zspark_file, args = _detect_special_files(parser)

        verbose = getattr(args, 'verbose', False)
        dev_mode = getattr(args, 'dev', False)

        _log_execution_context(args, python_file, zspark_file)

        return _route_command(args, python_file, zspark_file, verbose, dev_mode)

    except KeyboardInterrupt:
        boot_logger.info("Interrupted by user (Ctrl+C)")
        print("\n\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)

    except Exception as e:  # pylint: disable=broad-exception-caught
        boot_logger.critical("Unhandled exception: %s", str(e))
        boot_logger.emergency_dump(e)
        sys.exit(1)

def _route_command(args, python_file, zspark_file, verbose, dev_mode):
    """Route to appropriate command handler."""
    if python_file:
        return cli_commands.handle_script_command(
            boot_logger, sys, Path, python_file, verbose=verbose
        )

    if zspark_file:
        return cli_commands.handle_zspark_command(
            boot_logger, Path, zspark_file, verbose=verbose, dev_mode=dev_mode
        )

    # Get zos_package for handlers that need it
    zos_package = _get_zos_package()

    # Command routing (handlers import zOS locally to avoid premature framework init)
    handlers = {
        "shell": lambda: cli_commands.handle_shell_command(
            boot_logger, verbose=verbose
        ),
        "config": lambda: cli_commands.handle_config_command(
            boot_logger, verbose=verbose
        ),
        "ztests": lambda: cli_commands.handle_ztests_command(
            boot_logger, Path, zos_package, verbose=verbose
        ),
        "migrate": lambda: cli_commands.handle_migrate_command(
            boot_logger, Path, args, verbose=verbose
        ),
        "uninstall": lambda: cli_commands.handle_uninstall_command(
            boot_logger, Path, zos_package, verbose=verbose
        ),
    }

    if args.command in handlers:
        return handlers[args.command]()

    # Default: show info banner
    if verbose:
        boot_logger.print_buffered_logs()
    cli_commands.display_info(
        boot_logger, zos_package, get_version, get_package_info, detect_installation_type
    )
    return 0

# Special File Detection & Execution Context
def _detect_special_files(parser):
    """Detect Python (.py) files or zSpark (.zolo) files in arguments."""
    argv = sys.argv[1:]
    positional_args = [arg for arg in argv if not arg.startswith('-')]

    if not positional_args:
        return None, None, parser.parse_args()

    first_arg = positional_args[0]
    filtered_argv = [arg for arg in argv if arg != first_arg]

    # Python script execution
    if first_arg.endswith('.py'):
        boot_logger.debug("Detected Python script: %s", first_arg)
        return first_arg, None, parser.parse_args(filtered_argv)

    # zSpark.*.zolo execution
    if '.' not in first_arg:
        potential_zspark = Path.cwd() / f"zSpark.{first_arg}.zolo"
        if potential_zspark.exists():
            boot_logger.debug("Detected zSpark file: %s", potential_zspark)
            return None, str(potential_zspark), parser.parse_args(filtered_argv)

    return None, None, parser.parse_args()


def _log_execution_context(args, python_file, zspark_file):
    """Log execution context for bootstrap diagnostics."""
    verbose = getattr(args, 'verbose', False)
    dev_mode = getattr(args, 'dev', False)

    # Determine execution type
    if zspark_file:
        exec_type = "zSpark"
    elif python_file:
        exec_type = f"python ({python_file})"
    else:
        exec_type = f"command ({args.command or 'info'})"

    boot_logger.debug(
        "Execution: %s, Verbose: %s, Dev: %s",
        exec_type, verbose, dev_mode
    )





if __name__ == "__main__":
    main()
