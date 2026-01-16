"""CLI entry point for the zolo OS command."""

# Stdlib imports (BEFORE any zKernel imports to avoid triggering framework init)
import sys
import os
from pathlib import Path

# zSys imports (system utilities, safe to import)
from zOS.logger import BootstrapLogger, EcosystemLogger
from zOS.install import detect_installation_type
from zOS import cli as cli_commands
from zOS.cli.parser import create_parser


# Lazy Import Helper (needed for bootstrap)
def _get_zkernel_package(): # pylint: disable=import-outside-toplevel
    """Lazy import zKernel package to avoid triggering framework initialization at module load."""
    import zKernel as zkernel_package # pylint: disable=import-outside-toplevel,import-error  # type: ignore
    return zkernel_package

# Bootstrap & Main Entry Point
boot_logger = BootstrapLogger()

boot_logger.debug("Python: %s", sys.version.split()[0])
# NOTE: Installation detection disabled until zKernel is available in monorepo
# boot_logger.debug(
#     "Installation: %s", 
#     detect_installation_type(_get_zkernel_package(), detailed=True)
# )

def main() -> None:
    """Main entry point for the zolo OS command."""

    try:
        parser = create_parser()
        python_file, zspark_file, args = _detect_special_files(parser)

        verbose = getattr(args, 'verbose', False)
        dev_mode = getattr(args, 'dev', False)

        # Set environment variable for verbose logging (industry standard)
        # This allows LoggerConfig to enable console output for all logs
        if verbose:
            os.environ['ZKERNEL_VERBOSE'] = '1'

        _log_execution_context(args, python_file, zspark_file)

        return _route_command(args, python_file, zspark_file, verbose, dev_mode)

    except KeyboardInterrupt:
        boot_logger.info("Interrupted by user (Ctrl+C)")
        print("\n\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)

    except Exception as e:  # pylint: disable=broad-except
        # Intentional catch-all: last line of defense for logging unhandled exceptions
        boot_logger.critical("Unhandled exception: %s", str(e))
        boot_logger.emergency_dump(e)
        sys.exit(1)


# Execution Flow Helpers (in order of execution)

def _detect_special_files(parser):
    """Detect Python (.py) files or zSpark (.zolo) files in arguments."""
    argv = sys.argv[1:]
    positional_args = [arg for arg in argv if not arg.startswith('-')]
    
    # Log raw arguments received
    if argv:
        boot_logger.debug("Arguments: %s", ' '.join(argv))
    
    if not positional_args:
        args = parser.parse_args()
        boot_logger.debug("Parsed command: %s", getattr(args, 'command', None) or "version")
        return None, None, args
    
    first_arg = positional_args[0]
    filtered_argv = [arg for arg in argv if arg != first_arg]
    
    # Python script execution
    if first_arg.endswith('.py'):
        boot_logger.debug("Detected Python script: %s", first_arg)
        args = parser.parse_args(filtered_argv)
        boot_logger.debug("Parsed command: %s (with script)", getattr(args, 'command', None) or "run")
        return first_arg, None, args
    
    # NOTE: zSpark.*.zolo execution has been extracted to @temp_zKernel/cli/zspark.py
    # This was a framework bootstrapping command (initializes zKernel instance)
    # Commented out as handle_zspark_command is no longer in zOS
    #
    # if '.' not in first_arg:
    #     potential_zspark = Path.cwd() / f"zSpark.{first_arg}.zolo"
    #     if potential_zspark.exists():
    #         boot_logger.debug("Detected zSpark file: %s", potential_zspark)
    #         args = parser.parse_args(filtered_argv)
    #         boot_logger.debug("Parsed command: %s (with zSpark)", getattr(args, 'command', None) or "run")
    #         return None, str(potential_zspark), args
    
    args = parser.parse_args()
    boot_logger.debug("Parsed command: %s", getattr(args, 'command', None) or "version")
    return None, None, args


def _log_execution_context(args, python_file, zspark_file):
    """Log execution context for bootstrap diagnostics."""
    verbose = getattr(args, 'verbose', False)
    dev_mode = getattr(args, 'dev', False)
    
    # Determine execution type
    # NOTE: zspark_file detection disabled (extracted to @temp_zKernel)
    if zspark_file:
        exec_type = "zSpark (framework - no longer supported in zOS)"
    elif python_file:
        exec_type = f"python ({python_file})"
    else:
        exec_type = "zCLI"
    
    boot_logger.debug(
        "Execution: %s, Verbose: %s, Dev: %s", 
        exec_type, verbose, dev_mode
    )


def _route_command(args, python_file, zspark_file, verbose, dev_mode):
    """Route to appropriate command handler."""
    if python_file:
        return cli_commands.handle_script_command(boot_logger, sys, Path, python_file, verbose=verbose)

    # NOTE: zSpark command extracted to @temp_zKernel/cli/zspark.py (framework bootstrapping)
    if zspark_file:
        print("\n❌ Error: zSpark command is no longer available in standalone zOS")
        print("zSpark is a framework bootstrapping command that requires zKernel.")
        print("It has been extracted to @temp_zKernel and will be available when zKernel joins the monorepo.\n")
        return 1
        # return cli_commands.handle_zspark_command(boot_logger, Path, zspark_file, verbose=verbose, dev_mode=dev_mode)

    # Install command doesn't need zkernel_package
    if hasattr(args, 'command') and args.command == 'install':
        return cli_commands.handle_install_command(boot_logger, sys, Path, args, verbose=verbose)

    # Get zkernel_package for handlers that need it (optional until zKernel is in monorepo)
    try:
        zkernel_package = _get_zkernel_package()
    except ModuleNotFoundError:
        boot_logger.debug("zKernel not available (standalone zOS mode)")
        zkernel_package = None

    # Command routing (handlers import zKernel locally to avoid premature framework init)
    # NOTE: zKernel-specific commands commented out during refactoring
    
    command = getattr(args, 'command', None)
    
    # Handle machine command with flags
    if command == "machine":
        # Check for --edit flag first (interactive editor)
        if getattr(args, 'edit', False):
            return cli_commands.handle_machine_edit_command(boot_logger, verbose=verbose)
        # Check for --open flag (can be combined with filters)
        elif getattr(args, 'open', False):
            return cli_commands.handle_machine_open_command(boot_logger, verbose=verbose)
        elif getattr(args, 'system', False):
            return cli_commands.handle_machine_system_command(boot_logger, verbose=verbose)
        elif getattr(args, 'user', False):
            return cli_commands.handle_machine_user_command(boot_logger, verbose=verbose)
        else:
            # No flag, show all
            return cli_commands.handle_machine_command(boot_logger, verbose=verbose)
    
    # Handle open command
    if command == "open":
        target = getattr(args, 'target', None)
        if target:
            return cli_commands.handle_open_command(boot_logger, target, verbose=verbose)
        else:
            print("Error: Please specify a file or URL to open")
            return 1
    
    handlers = {
        # "shell": lambda: cli_commands.handle_shell_command(boot_logger, verbose=verbose),
        # "ztests": lambda: cli_commands.handle_ztests_command(boot_logger, Path, zkernel_package, verbose=verbose),
        # "migrate": lambda: cli_commands.handle_migrate_command(boot_logger, Path, args, verbose=verbose),
        # "uninstall": lambda: cli_commands.handle_uninstall_command(boot_logger, Path, zkernel_package, verbose=verbose),
    }

    if command and command in handlers:
        return handlers[command]()

    # Default: show info banner (OS command - no zKernel init)
    # Use zOS logger for persistence and verbose console output
    # Bootstrap handles console output in mkna format
    zos_logger = EcosystemLogger(verbose=verbose)
    boot_logger.flush_to_ecosystem(zos_logger, verbose=verbose)
    
    # Import zOS version information
    from zOS.version import get_version as get_zos_version, get_package_info as get_zos_info
    cli_commands.display_info(
        boot_logger, 
        zkernel_package, 
        get_zos_version(), 
        get_zos_info(), 
        detect_installation_type,
        zos_logger=zos_logger
    )
    return 0


# Alternative Entry Points

def ztests_main() -> None:
    """Entry point for zTests command (legacy compatibility)."""
    sys.argv = ['zolo', 'ztests'] + sys.argv[1:]
    main()


if __name__ == "__main__":
    main()
