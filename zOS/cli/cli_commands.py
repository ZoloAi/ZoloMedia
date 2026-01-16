# zOS/cli/cli_commands.py
"""
CLI command handlers for the zolo entry point.

Bridges main.py (argument parsing) and zOS (execution).
Each handler initializes zOS with command-specific config, flushes bootstrap logs,
and delegates to the appropriate subsystem.

Active Handlers (zOS - no zKernel init):
- display_info() - Version banner, ecosystem status
- handle_machine_command() - Show machine config (all sections)
- handle_machine_open_command() - Open config in IDE
- handle_machine_edit_command() - Interactive preference editor
- handle_machine_system_command() - Show system-detected config (locked)
- handle_machine_user_command() - Show user preferences (editable)
- handle_script_command() - Execute Python scripts with zKernel context
- handle_zspark_command() - Execute zSpark.*.zolo files

Commented Handlers (zKernel - require framework init):
- handle_shell_command() - Interactive REPL shell
- handle_ztests_command() - Declarative test runner
- handle_migrate_command() - Schema migration orchestrator
- handle_uninstall_command() - Package removal with cleanup
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

        from zKernel import zKernel
        zcli = zKernel(zspark_config)

        if hasattr(zcli, 'logger'):
            boot_logger.flush_to_framework(zcli.logger, verbose=verbose)

        from zOS.formatting.colors import Colors
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



def display_info(boot_logger, zcli_package, zos_version, zos_pkg_info, detect_install_type, zos_logger=None):
    """
    Display zOS (Zolo Operating System) information banner.
    
    Args:
        boot_logger: BootstrapLogger instance
        zcli_package: Imported zKernel package (for detection)
        zos_version: zOS version string
        zos_pkg_info: zOS package info dict
        detect_install_type: Function to detect install type
        zos_logger: Optional zOS logger for logging OS activity
    """
    # Ensure machine config exists (generates on first run)
    from zOS.machine import get_machine_info
    from zOS.paths import get_ecosystem_root
    config_path = get_ecosystem_root() / "zConfig.machine.zolo"
    
    if not config_path.exists():
        boot_logger.debug("Generating zConfig.machine.zolo on first run...")
        try:
            # This will auto-detect and save the config file
            get_machine_info()
            boot_logger.info("Generated machine config at %s", config_path)
        except Exception as e:
            boot_logger.warning("Could not generate machine config: %s", e)
    
    # Get zOS install type
    if zcli_package and hasattr(zcli_package, '__file__'):
        install_type = "pip -e" if "editable" in str(zcli_package.__file__) else "pip"
    else:
        install_type = "standalone"
    
    if zos_logger:
        zos_logger.info("zOS: %s (%s)", zos_version, install_type)
    
    # Display zOS banner
    print(f"\n{zos_pkg_info['name']} v{zos_version}")
    print(f"{zos_pkg_info['description']}")
    print(f"By {zos_pkg_info['author']} • License: {zos_pkg_info['license']}")
    
    # Show installed products
    print(f"\nInstalled Products:")
    
    # Collect installed products for single log entry
    installed_products = []
    
    # Try to detect zKernel
    try:
        from zKernel.version import get_version as get_zkernel_version
        zkernel_version = get_zkernel_version()
        zkernel_install = detect_install_type(zcli_package, detailed=False)
        installed_products.append(f"zKernel {zkernel_version} ({zkernel_install})")
        print(f"  • zKernel {zkernel_version} ({zkernel_install})")
    except ImportError:
        print(f"  • zKernel (not installed)")
    
    # Try to detect zLSP
    try:
        from core import version as zlsp_version_module
        # Try to get version from package metadata
        try:
            from importlib.metadata import version as get_pkg_version
            zlsp_version = get_pkg_version('zlsp')
            # Detect install type by checking if it's in site-packages or source
            import core
            import site
            site_packages = [sp for sp in site.getsitepackages() if sp]
            is_editable = not any(str(core.__file__).startswith(sp) for sp in site_packages)
            zlsp_install = "pip -e" if is_editable else "pip"
            installed_products.append(f"zLSP {zlsp_version} ({zlsp_install})")
            print(f"  • zLSP {zlsp_version} ({zlsp_install})")
        except Exception:
            print(f"  • zLSP (installed, version unknown)")
    except ImportError:
        print(f"  • zLSP (not installed)")
    
    # Log all installed products as single INFO message
    if zos_logger and installed_products:
        zos_logger.info("Installed products: %s", ", ".join(installed_products))
    
    print()


def handle_machine_command(boot_logger, verbose: bool = False):
    """
    Show machine configuration from zConfig.machine.zolo.
    
    Args:
        boot_logger: BootstrapLogger instance
        verbose: If True, show bootstrap logs on stdout
    """
    from zOS.machine import get_machine_info
    from zOS.paths import get_ecosystem_root
    from pathlib import Path
    
    # Get machine config file path
    config_path = get_ecosystem_root() / "zConfig.machine.zolo"
    
    if verbose:
        boot_logger.print_buffered_logs()
    
    # Display config
    print("\n" + "=" * 60)
    print("zMachine Configuration")
    print("=" * 60)
    
    if config_path.exists():
        print(f"\nFile: {config_path}\n")
        with open(config_path, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"\n⚠️  Configuration file not found: {config_path}")
        print("\nGenerating machine info...\n")
        
        # Show machine info directly
        machine_info = get_machine_info()
        # Convert zMachine object to dict if needed
        if hasattr(machine_info, '__dict__'):
            for key, value in vars(machine_info).items():
                print(f"{key}: {value}")
        else:
            print(str(machine_info))
    
    print("=" * 60 + "\n")


def handle_machine_open_command(boot_logger, verbose: bool = False):
    """
    Open machine configuration file in IDE.
    
    Args:
        boot_logger: BootstrapLogger instance
        verbose: If True, show bootstrap logs on stdout
    """
    from zOS.paths import get_ecosystem_root
    from zOS.utils.file_opener import open_file_in_editor, get_ide_from_config, get_editor_command
    
    config_path = get_ecosystem_root() / "zConfig.machine.zolo"
    
    if verbose:
        boot_logger.print_buffered_logs()
    
    if not config_path.exists():
        print(f"\n⚠️  Configuration file not found: {config_path}")
        print("Run 'zolo' once to generate the configuration file.\n")
        return
    
    # Get IDE from config
    ide = get_ide_from_config()
    
    # Check if it's a terminal editor
    _, is_terminal = get_editor_command(ide)
    
    if is_terminal:
        # Terminal editor: no pre-message, just launch (blocks)
        print()  # Blank line for spacing
    else:
        # GUI editor: show launching message
        print(f"\nOpening {config_path.name} in {ide}...\n")
    
    # Open file (blocks for terminal editors, returns immediately for GUI)
    success = open_file_in_editor(str(config_path))
    
    if success:
        if not is_terminal:
            # Only show success message for GUI editors
            print(f"✓ Opened in {ide}\n")
    else:
        print(f"✗ Failed to open in {ide}")
        print(f"  Try opening manually: {config_path}\n")


def handle_machine_edit_command(boot_logger, verbose: bool = False):
    """
    Launch interactive editor for user preferences.
    
    Args:
        boot_logger: BootstrapLogger instance
        verbose: If True, show bootstrap logs on stdout
    """
    from zOS.cli.interactive_editor import interactive_edit
    
    if verbose:
        boot_logger.print_buffered_logs()
    
    # Launch interactive editor
    interactive_edit()


def handle_machine_system_command(boot_logger, verbose: bool = False):
    """
    Show system-detected machine configuration (locked sections).
    
    Args:
        boot_logger: BootstrapLogger instance
        verbose: If True, show bootstrap logs on stdout
    """
    from zOS.paths import get_ecosystem_root
    
    # System (locked) sections
    SYSTEM_SECTIONS = [
        'machine_identity',
        'python_runtime',
        'cpu',
        'memory',
        'gpu',
        'network',
        'user_paths',
        'time_date_formatting',
        'launch_commands'
    ]
    
    config_path = get_ecosystem_root() / "zConfig.machine.zolo"
    
    if verbose:
        boot_logger.print_buffered_logs()
    
    print("\n" + "=" * 60)
    print("zMachine System Configuration (Locked)")
    print("=" * 60)
    
    if config_path.exists():
        print(f"\nFile: {config_path}\n")
        
        # Parse and filter system sections
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_zmachine = False
        current_section = None
        output_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Check for zMachine block start
            if stripped.startswith('zMachine'):
                in_zmachine = True
                output_lines.append(line)
                continue
            
            if in_zmachine:
                # Check for section headers (first-level indented keys under zMachine)
                # They should have exactly 2 spaces of indentation
                if line.startswith('  ') and not line.startswith('    ') and stripped and not stripped.startswith('#') and ':' in stripped:
                    # New section (first-level key)
                    section_name = stripped.split(':')[0].strip()
                    if section_name in SYSTEM_SECTIONS:
                        current_section = section_name
                        output_lines.append(line)
                    else:
                        current_section = None
                elif current_section:
                    # Inside a system section (either nested content or blank lines)
                    # Continue until we hit another first-level key
                    if line.startswith('  ') and not line.startswith('    '):
                        # Another first-level key, stop current section
                        if stripped and not stripped.startswith('#') and ':' in stripped:
                            section_name = stripped.split(':')[0].strip()
                            if section_name in SYSTEM_SECTIONS:
                                current_section = section_name
                                output_lines.append(line)
                            else:
                                current_section = None
                        else:
                            output_lines.append(line)
                    else:
                        # Nested content or blank line
                        output_lines.append(line)
        
        print(''.join(output_lines))
    else:
        print(f"\n⚠️  Configuration file not found: {config_path}\n")
    
    print("=" * 60 + "\n")


def handle_machine_user_command(boot_logger, verbose: bool = False):
    """
    Show user-editable machine configuration (user preferences).
    
    Args:
        boot_logger: BootstrapLogger instance
        verbose: If True, show bootstrap logs on stdout
    """
    from zOS.paths import get_ecosystem_root
    
    # User (editable) sections
    USER_SECTIONS = [
        'user_preferences',
        'custom'
    ]
    
    config_path = get_ecosystem_root() / "zConfig.machine.zolo"
    
    if verbose:
        boot_logger.print_buffered_logs()
    
    print("\n" + "=" * 60)
    print("zMachine User Configuration (Editable)")
    print("=" * 60)
    
    if config_path.exists():
        print(f"\nFile: {config_path}\n")
        
        # Parse and filter user sections
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_zmachine = False
        current_section = None
        output_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Check for zMachine block start
            if stripped.startswith('zMachine'):
                in_zmachine = True
                output_lines.append(line)
                continue
            
            if in_zmachine:
                # Check for section headers (first-level indented keys under zMachine)
                # They should have exactly 2 spaces of indentation
                if line.startswith('  ') and not line.startswith('    ') and stripped and not stripped.startswith('#') and ':' in stripped:
                    # New section (first-level key)
                    section_name = stripped.split(':')[0].strip()
                    if section_name in USER_SECTIONS:
                        current_section = section_name
                        output_lines.append(line)
                    else:
                        current_section = None
                elif current_section:
                    # Inside a user section (either nested content or blank lines)
                    # Continue until we hit another first-level key
                    if line.startswith('  ') and not line.startswith('    '):
                        # Another first-level key, stop current section
                        if stripped and not stripped.startswith('#') and ':' in stripped:
                            section_name = stripped.split(':')[0].strip()
                            if section_name in USER_SECTIONS:
                                current_section = section_name
                                output_lines.append(line)
                            else:
                                current_section = None
                        else:
                            output_lines.append(line)
                    else:
                        # Nested content or blank line
                        output_lines.append(line)
        
        print(''.join(output_lines))
    else:
        print(f"\n⚠️  Configuration file not found: {config_path}\n")
    
    print("=" * 60 + "\n")


# ============================================================================
# Framework Command Handlers (zKernel)
# ============================================================================
# Framework commands (shell, migrate, ztests, uninstall) have been moved to:
# zKernel/src/cli_integration/
#
# They will be registered dynamically when zKernel is properly integrated.
# See: zKernel/src/cli_integration/README.md for integration plan.
#
# Commands:
#   - shell      → zKernel/src/cli_integration/shell_command.py
#   - migrate    → zKernel/src/cli_integration/migrate_command.py
#   - ztests     → zKernel/src/cli_integration/ztests_command.py
#   - uninstall  → zKernel/src/cli_integration/uninstall_command.py


# ============================================================================
# zOS Command Handlers (ACTIVE)
# ============================================================================

def handle_install_command(boot_logger, sys, Path, args, verbose: bool = False):
    """
    Install Zolo OS packages.
    
    Args:
        boot_logger: BootstrapLogger instance
        sys: sys module (for sys.executable)
        Path: pathlib.Path class
        args: Parsed arguments with package, source flags, extras
        verbose: Show detailed output
    
    Returns:
        int: Exit code (0 = success, non-zero = error)
    
    Examples:
        zolo install zKernel --local --editable
        zolo install zKernel --git --branch v1.5.8
        zolo install zKernel --git --branch main --postgres
    """
    package = args.package
    boot_logger.info("Installing %s...", package)
    
    # Build pip command
    pip_cmd = [sys.executable, "-m", "pip", "install"]
    
    # Add editable flag
    if args.editable:
        pip_cmd.append("-e")
    
    # Determine source
    if args.local:
        # Local folder
        package_path = Path.cwd() / package
        if not package_path.exists():
            boot_logger.error("Package folder not found: %s", package_path)
            if verbose:
                boot_logger.print_buffered_logs()
            print(f"\n❌ Error: {package} folder not found at {package_path}\n")
            return 1
        pip_cmd.append(str(package_path))
    
    elif args.git:
        # From GitHub - branch represents version
        repo_url = "git+https://github.com/yourusername/Zolo.git"
        if args.branch != "main":
            repo_url += f"@{args.branch}"
        repo_url += f"#subdirectory={package}"
        pip_cmd.append(repo_url)
    
    else:
        # PyPI not supported - OS uses git branches for versioning
        boot_logger.error("PyPI installation not supported. Use --local or --git")
        if verbose:
            boot_logger.print_buffered_logs()
        print("\n❌ Error: Please use --local or --git for installation\n")
        print("   Examples:")
        print(f"     zolo install {package} --local --editable")
        print(f"     zolo install {package} --git --branch v1.5.8\n")
        return 1
    
    # Add extras for zKernel
    if package == "zKernel":
        extras = []
        if args.all_extras:
            extras.append("all")
        else:
            if args.postgres:
                extras.append("postgres")
            if args.csv:
                extras.append("csv")
        
        if extras and not args.local and not args.git:
            # Modify last argument to include extras
            pip_cmd[-1] += f"[{','.join(extras)}]"
    
    # Execute pip
    boot_logger.debug("Running: %s", " ".join(pip_cmd))
    if verbose:
        boot_logger.print_buffered_logs()
    
    print(f"\n🔧 Installing {package}...\n")
    try:
        result = subprocess.run(pip_cmd, check=False)
        if result.returncode == 0:
            print(f"\n✅ {package} installed successfully!\n")
        else:
            print(f"\n❌ Installation failed (exit code {result.returncode})\n")
        return result.returncode
    except Exception as e:
        boot_logger.error("Installation failed: %s", e)
        print(f"\n❌ Installation error: {e}\n")
        return 1


