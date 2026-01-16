#!/usr/bin/env python3
# @temp_zKernel/cli/zspark.py
"""
Framework-level zSpark bootstrapping command extracted from zOS.

ORIGIN: zOS/cli/cli_commands.py (lines 83-229)
STATUS: Staging for merge when zKernel joins monorepo
ACTION: DO NOT touch ~/Projects/Zolo/zKernel directly

This file contains the zSpark command handler that launches the full zKernel framework.
zSpark is the framework configuration file format (.zolo syntax) used to bootstrap
a complete zKernel application.

This is framework-level bootstrapping, NOT an OS primitive.

DEPENDENCIES:
- Requires zKernel framework (hard import on line 115: `from zKernel import zKernel`)
- Requires zlsp parser (`from zolo.parser import tokenize`)
- Requires zOS.logger.BootstrapLogger (for logging)
- Requires zOS.formatting.Colors (for terminal output)

TO MERGE LATER:
- Copy this file → ~/Projects/Zolo/zKernel/cli/zspark.py (when copying zKernel to monorepo)
- Register `zolo <zSpark_name>` command in zKernel CLI router
- This command bootstraps the full framework (zKernel(zspark_config))
"""


def handle_zspark_command(boot_logger, Path, zspark_path: str, verbose: bool = False, dev_mode: bool = False):
    """
    Execute declarative zSpark.*.zolo configuration file (native zolo syntax with LSP support).
    
    This is a FRAMEWORK command that initializes the full zKernel instance with the
    provided zSpark configuration.
    
    Args:
        boot_logger: BootstrapLogger instance (from zOS)
        Path: pathlib.Path class
        zspark_path: Path to zSpark.*.zolo file
        verbose: Show bootstrap logs on stdout
        dev_mode: Override deployment to Development (show banners)
    
    Returns:
        int: Exit code (0 = success, 1 = error)
    
    Examples:
        zolo zCloud
        zolo zCloud --verbose --dev
    
    Framework Dependencies:
        - zKernel framework (line 115: `from zKernel import zKernel`)
        - zlsp parser (line 167: `from zolo.parser import tokenize`)
        - zOS utilities (boot_logger, Colors) - these are OS-level, OK to use
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

        # ═══════════════════════════════════════════════════════════════════
        # FRAMEWORK INITIALIZATION - This is why this belongs in zKernel
        # ═══════════════════════════════════════════════════════════════════
        from zKernel import zKernel
        zcli = zKernel(zspark_config)
        # ═══════════════════════════════════════════════════════════════════

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
    """
    Validate zSpark file exists and has correct extension.
    
    Returns:
        (zspark_file: Path | None, exit_code: int)
    """
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
    """
    Parse and validate zSpark.*.zolo file using zlsp parser.
    
    Returns:
        (zspark_config: dict | None, exit_code: int)
    """
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
    """
    Apply overrides and log zSpark configuration.
    
    Args:
        boot_logger: BootstrapLogger instance
        zspark_config: Parsed zSpark configuration dictionary
        zspark_file: Path to zSpark file
        verbose: Verbose mode flag
        dev_mode: Development mode flag
    
    Returns:
        str: Mode string from configuration
    """
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
