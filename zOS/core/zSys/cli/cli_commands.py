# zSys/cli/cli_commands.py
"""
CLI command handlers for the zolo entry point.

Bridges main.py (argument parsing) and zCLI framework (execution).
Each handler initializes zCLI with command-specific config, flushes bootstrap logs,
and delegates to the appropriate subsystem.

Handlers:
- display_info() - Version/installation info
- handle_shell_command() - Interactive zShell
- handle_config_command() - Machine/environment config display
- handle_ztests_command() - Declarative test runner
- handle_migrate_command() - Schema migrations
- handle_uninstall_command() - Uninstall wizard
- handle_script_command() - Execute Python scripts
- handle_zspark_command() - Execute zSpark.*.zolo files
"""

import subprocess
import os

def handle_script_command(boot_logger, sys, Path, script_path: str, verbose: bool = False):
    """
    Execute Python script using zolo's interpreter (solves python/python3 ambiguity).
    
    Args:
        boot_logger: BootstrapLogger instance
        sys: sys module (for sys.executable)
        Path: pathlib.Path class
        script_path: Path to Python script
        verbose: Show bootstrap logs on stdout
    
    Returns:
        int: Exit code (0 = success, non-zero = error)
    
    Examples:
        zolo zTest.py
        zolo zTest.py --verbose
    """
    # Validate file exists
    script = Path(script_path).resolve()
    if not script.exists():
        boot_logger.error("Script not found: %s", script_path)
        if verbose:
            boot_logger.print_buffered_logs()
        print(f"\n❌ Error: Script not found: {script_path}\n")
        return 1

    # Validate it's a .py file
    if script.suffix != ".py":
        boot_logger.error("Not a Python file: %s (suffix: %s)", script_path, script.suffix)
        if verbose:
            boot_logger.print_buffered_logs()
        print(f"\n❌ Error: File must be a .py file: {script_path}\n")
        return 1

    # Show bootstrap logs if verbose
    if verbose:
        boot_logger.print_buffered_logs()

    # Execute using sys.executable (solves python vs python3)
    try:
        result = subprocess.run(
            [sys.executable, str(script.absolute())],
            cwd=str(script.parent),  # Run in script's directory
            env=os.environ.copy(),
            check=False  # Don't raise exception, return exit code
        )
        return result.returncode

    except Exception as e:
        boot_logger.error("Failed to execute script: %s", str(e))
        print(f"\n❌ Error executing script: {e}\n")
        return 1

def handle_zspark_command(boot_logger, Path, zspark_path: str, verbose: bool = False, dev_mode: bool = False):
    """
    Execute declarative zSpark.*.zolo configuration file (native zolo syntax with LSP support).
    
    Args:
        boot_logger: BootstrapLogger instance
        Path: pathlib.Path class
        zspark_path: Path to zSpark.*.zolo file
        verbose: Show bootstrap logs on stdout
        dev_mode: Override deployment to Development (show banners)
    
    Returns:
        int: Exit code (0 = success, 1 = error)
    
    Examples:
        zolo zCloud
        zolo zCloud --verbose --dev
    """
    zspark_file, exit_code = _validate_zspark_file(boot_logger, Path, zspark_path, verbose)
    if exit_code != 0:
        return exit_code

    try:
        zspark_config, exit_code = _parse_zspark_file(boot_logger, Path, zspark_file, verbose)
        if exit_code != 0:
            return exit_code

        mode = _configure_zspark(boot_logger, zspark_config, zspark_file, verbose, dev_mode)

        if verbose:
            boot_logger.print_buffered_logs()

        from zOS import zOS
        zcli = zOS(zspark_config)

        if hasattr(zcli, 'logger'):
            boot_logger.flush_to_framework(zcli.logger, verbose=False)

        from zSys.formatting.colors import Colors
        colors = Colors()

        print(f"\n{colors.CONFIG}zSpark Configuration Loaded{colors.RESET}")
        print(f"  File: {zspark_file.name} | Mode: {mode}\n")

        zcli.run()
        return 0

    except Exception as e:
        error_type = "Missing required key" if isinstance(e, KeyError) else "Failed to execute"
        boot_logger.error("%s in zSpark: %s", error_type, str(e))
        if verbose:
            boot_logger.print_buffered_logs()
        print(f"\n❌ Error: {error_type} in zSpark file: {e}\n")
        if not isinstance(e, KeyError):
            import traceback
            traceback.print_exc()
        return 1

def _validate_zspark_file(boot_logger, Path, zspark_path: str, verbose: bool) -> tuple:
    """Validate zSpark file exists and has correct extension."""
    zspark_file = Path(zspark_path).resolve()
    if not zspark_file.exists():
        boot_logger.error("zSpark file not found: %s", zspark_path)
        if verbose:
            boot_logger.print_buffered_logs()
        print(f"\n❌ Error: zSpark file not found: {zspark_path}\n")
        return None, 1

    if zspark_file.suffix != ".zolo":
        boot_logger.error("Not a .zolo file: %s (suffix: %s)", zspark_path, zspark_file.suffix)
        if verbose:
            boot_logger.print_buffered_logs()
        print(f"\n❌ Error: File must be a .zolo file: {zspark_path}\n")
        return None, 1

    return zspark_file, 0

def _parse_zspark_file(boot_logger, Path, zspark_file, verbose: bool) -> tuple:
    """Parse and validate zSpark.*.zolo file."""
    import sys
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from zolo.parser import tokenize

    with open(zspark_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = tokenize(content, str(zspark_file))
    
    if result.diagnostics:
        boot_logger.error("Parsing errors in zSpark file:")
        for diag in result.diagnostics:
            severity_map = {1: 'ERROR', 2: 'WARNING', 3: 'INFO', 4: 'HINT'}
            severity = severity_map.get(diag.severity, 'UNKNOWN')
            boot_logger.error("  [%s] Line %d:%d - %s", 
                            severity, 
                            diag.range.start.line + 1, 
                            diag.range.start.character,
                            diag.message)
        
        if verbose:
            boot_logger.print_buffered_logs()
        
        print(f"\n❌ Error: Failed to parse zSpark file:\n")
        for diag in result.diagnostics:
            severity_map = {1: 'ERROR', 2: 'WARNING', 3: 'INFO', 4: 'HINT'}
            severity = severity_map.get(diag.severity, 'UNKNOWN')
            print(f"  [{severity}] Line {diag.range.start.line + 1}: {diag.message}")
        print()
        return None, 1
    
    if not isinstance(result.data, dict) or 'zSpark' not in result.data:
        boot_logger.error("Invalid zSpark file: missing 'zSpark' root key")
        if verbose:
            boot_logger.print_buffered_logs()
        print(f"\n❌ Error: Invalid zSpark file format\n")
        print("zSpark.*.zolo files must contain a root 'zSpark' key with configuration dictionary.\n")
        return None, 1
    
    return result.data['zSpark'], 0


def _configure_zspark(boot_logger, zspark_config: dict, zspark_file, verbose: bool, dev_mode: bool) -> str:
    """Apply overrides and log zSpark configuration."""
    if dev_mode:
        zspark_config['deployment'] = 'Development'
    
    if verbose:
        zspark_config['logger'] = 'DEBUG'
    
    boot_logger.session("zSpark file: %s", zspark_file.name)
    boot_logger.session("Configuration keys: %d", len(zspark_config))
    
    deployment = zspark_config.get('deployment', 'Production (default)')
    deployment_str = f"{deployment} (--dev override)" if dev_mode else deployment
    boot_logger.session("Deployment: %s", deployment_str)
    
    mode = zspark_config.get('zMode', 'N/A')
    boot_logger.session("Mode: %s", mode)
    
    logger_level = zspark_config.get('logger', 'INFO (default)')
    logger_str = f"DEBUG (--verbose override)" if verbose else logger_level
    boot_logger.session("Logger: %s", logger_str)
    
    return mode



def display_info(boot_logger, zcli_package, get_version, get_package_info, detect_install_type):
    """
    Display zolo-zcli information banner.
    
    Args:
        boot_logger: BootstrapLogger instance
        zcli_package: Imported zCLI package
        get_version: Function to get package version
        get_package_info: Function to get package info dict
        detect_install_type: Function to detect install type
    """
    install_type = detect_install_type(zcli_package, detailed=False)
    pkg_info = get_package_info()
    
    print(f"\n{pkg_info['name']} {get_version()} ({install_type})")
    print("A declarative based Framework")
    print(f"By {pkg_info['author']}")
    print("License: MIT\n")


def handle_shell_command(boot_logger, verbose: bool = False):
    """
    Handle shell command.
    
    Args:
        boot_logger: BootstrapLogger instance
        verbose: If True, show bootstrap logs on stdout
    """
    from zOS import zOS  # Lazy import
    cli = zOS()
    boot_logger.flush_to_framework(cli.logger, verbose=verbose)
    cli.run_shell()


def handle_config_command(boot_logger, verbose: bool = False):
    """
    Handle config command - display only (read-only).
    
    Args:
        boot_logger: BootstrapLogger instance
        verbose: If True, show bootstrap logs on stdout
    """
    from zOS import zOS  # Lazy import
    cli = zOS({'zMode': 'Terminal', 'logger': 'PROD', 'deployment': 'Production'})
    boot_logger.flush_to_framework(cli.logger, verbose=verbose)
    
    cli.config.persistence.show_machine_config()
    cli.config.persistence.show_environment_config()


def handle_ztests_command(boot_logger, Path, zcli_package, verbose: bool = False):
    """
    Handle zTests command (declarative test runner).
    
    Args:
        boot_logger: BootstrapLogger instance
        zCLI: zCLI class
        Path: pathlib.Path class
        zcli_package: Imported zCLI package (for __file__ access)
        verbose: If True, show bootstrap logs on stdout
    
    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    # Resolve test runner directory relative to main.py location
    try:
        import __main__
        main_file = Path(__main__.__file__).resolve()
        project_root = main_file.parent
        test_runner_dir = project_root / "zTestRunner"
    except Exception:
        # Fallback: use zCLI package location
        zcli_path = Path(zcli_package.__file__).resolve()
        project_root = zcli_path.parent.parent
        test_runner_dir = project_root / "zTestRunner"
    
    if not test_runner_dir.exists():
        boot_logger.error("zTestRunner directory not found: %s", test_runner_dir)
        from zOS import zOS  # Lazy import
        temp_cli = zOS({'zMode': 'Terminal'})
        boot_logger.flush_to_framework(temp_cli.logger, verbose=verbose)
        temp_cli.display.text(f"Error: zTestRunner directory not found at {test_runner_dir}")
        return 1
    
    from zOS import zOS  # Lazy import
    test_cli = zOS({
        "zSpace": str(test_runner_dir.absolute()),
        "zMode": "Terminal"
    })
    boot_logger.flush_to_framework(test_cli.logger, verbose=verbose)
    
    test_cli.zspark_obj["zVaFile"] = "@.zUI.test_menu"
    test_cli.zspark_obj["zBlock"] = "zVaF"
    test_cli.walker.run()
    return 0


def handle_migrate_command(boot_logger, Path, args, verbose: bool = False):
    """
    Handle schema migration command - thin CLI wrapper.
    
    Args:
        boot_logger: BootstrapLogger instance
        zCLI: zCLI class
        Path: pathlib.Path class
        args: Parsed arguments from argparse
        verbose: If True, show bootstrap logs on stdout
    
    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    app_file = args.app_file
    if not Path(app_file).exists():
        boot_logger.error("App file not found: %s", app_file)
        from zOS import zOS  # Lazy import
        temp_z = zOS({'zMode': 'Terminal', 'logger': 'PROD', 'deployment': 'Production'})
        boot_logger.flush_to_framework(temp_z.logger, verbose=verbose)
        temp_z.display.text(f"❌ Error: App file not found: {app_file}")
        return 1
    
    from zOS import zOS  # Lazy import
    z = zOS({'zMode': 'Terminal'})
    boot_logger.flush_to_framework(z.logger, verbose=verbose)
    
    return z.data.cli_migrate(
        app_file=str(Path(app_file).resolve()),
        auto_approve=getattr(args, 'auto_approve', False),
        dry_run=getattr(args, 'dry_run', False),
        specific_schema=getattr(args, 'schema', None),
        force_version=getattr(args, 'version', None)
    )


def handle_uninstall_command(boot_logger, Path, zcli_package, verbose: bool = False):
    """
    Handle uninstall command with interactive menu.
    
    Args:
        boot_logger: BootstrapLogger instance
        zCLI: zCLI class
        Path: pathlib.Path class
        zcli_package: Imported zCLI package (for __file__ access)
        verbose: If True, show bootstrap logs on stdout
    """
    zcli_package_dir = Path(zcli_package.__file__).parent
    from zOS import zOS  # Lazy import
    uninstall_cli = zOS({
        "zWorkspace": str(zcli_package_dir),
        "zVaFile": "@.UI.zUI.zcli_sys",
        "zBlock": "Uninstall"
    })
    boot_logger.flush_to_framework(uninstall_cli.logger, verbose=verbose)
    
    uninstall_cli.walker.run()




