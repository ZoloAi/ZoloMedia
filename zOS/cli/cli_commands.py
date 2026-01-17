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


# ═══════════════════════════════════════════════════════════════════════════════
# NOTE: zSpark framework command moved to @temp_zKernel/cli/zspark.py
# ═══════════════════════════════════════════════════════════════════════════════
#
# The following function has been extracted to @temp_zKernel (framework layer):
# - handle_zspark_command(boot_logger, Path, zspark_path, ...) - Line 115: `from zKernel import zKernel`
#
# Plus helper functions:
# - _validate_zspark_file(...)
# - _parse_zspark_file(...)
# - _configure_zspark(...)
#
# This is a framework bootstrapping command that initializes the full zKernel instance.
# zSpark is the framework configuration file format (.zolo syntax).
#
# It will be merged into zKernel when it joins the monorepo.
#
# ═══════════════════════════════════════════════════════════════════════════════


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
    from zOS.utils.open import open_file
    from zOS.machine import get_machine_info
    
    config_path = get_ecosystem_root() / "zConfig.machine.zolo"
    
    if verbose:
        boot_logger.print_buffered_logs()
    
    if not config_path.exists():
        print(f"\n⚠️  Configuration file not found: {config_path}")
        print("Run 'zolo' once to generate the configuration file.\n")
        return
    
    # Get IDE from machine config
    machine = get_machine_info()
    ide = machine.get('ide', 'code')
    
    # Show opening message
    print(f"\nOpening {config_path.name} in {ide}...\n")
    
    # Open file
    success = open_file(str(config_path))
    
    if success:
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


def handle_open_command(boot_logger, target: str, verbose: bool = False):
    r"""
    Open file or URL using zOS primitives.
    
    Args:
        boot_logger: BootstrapLogger instance
        target: Path or URL to open
        verbose: Show debug info
    
    Examples:
        zolo open www.google.com
        zolo open ~/Documents/file.pdf
        zolo open ~/Library/Application\ Support/Zolo/zConfig.machine.zolo
    """
    from zOS.utils.open import open_file, open_url, is_url
    from zOS.machine import get_machine_info
    
    if verbose:
        boot_logger.print_buffered_logs()
    
    # Get IDE/browser preferences from machine config
    try:
        machine = get_machine_info()
        browser = machine.get('browser', 'chrome')
        ide = machine.get('ide', 'code')
    except Exception:
        # If config not available, use defaults
        browser = 'chrome'
        ide = 'code'
    
    # Detect type and open
    if is_url(target):
        # URL
        print(f"Opening {target} in {browser}...")
        success = open_url(target, browser=browser)
        if success:
            print(f"✓ Opened {target}")
            return 0
        else:
            print(f"✗ Failed to open {target}")
            return 1
    else:
        # File
        # Expand ~ and resolve paths
        import os
        target = os.path.expanduser(target)
        
        if not os.path.exists(target):
            print(f"✗ File not found: {target}")
            return 1
        
        print(f"Opening {target} in {ide}...")
        success = open_file(target, editor=ide)
        if success:
            print(f"✓ Opened {target}")
            return 0
        else:
            print(f"✗ Failed to open {target}")
            return 1

