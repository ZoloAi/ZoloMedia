#!/usr/bin/env python3
# @temp_zKernel/cli/uninstall.py
"""
Framework-level uninstall CLI handlers extracted from zOS.

ORIGIN: zOS/install/removal.py (lines 176-345)
STATUS: Staging for merge when zKernel joins monorepo
ACTION: DO NOT touch ~/Projects/Zolo/zKernel directly

This file contains interactive CLI handlers that depend on zKernel framework
components (zcli.display, zcli.config, Walker UI, etc.).

These are framework-level CLI commands, NOT OS primitives.

DEPENDENCIES:
- Requires zOS.install.removal core functions (get_optional_dependencies, remove_package, etc.)
- Requires zKernel framework (zcli.display, zcli.config.sys_paths)

TO MERGE LATER:
- Copy this file → ~/Projects/Zolo/zKernel/cli/uninstall.py (when copying zKernel to monorepo)
- Register `zolo uninstall` command in zKernel CLI router
"""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zKernel import zCLI  # Type hint only, not runtime import


# Import OS-level functions from zOS (these remain in zOS)
# When merged into zKernel, these imports will work since zKernel depends on zOS
try:
    from zOS.install.removal import (
        remove_package,
        remove_user_data,
        remove_dependencies,
    )
except ImportError:
    # Fallback for development/testing in @temp_zKernel
    # In production (after merge), zOS will be installed as dependency
    import warnings
    warnings.warn(
        "@temp_zKernel/cli/uninstall.py: zOS not found. "
        "This is expected in staging area. After merge to zKernel, "
        "zOS will be available as dependency.",
        ImportWarning
    )
    # Dummy fallbacks for type checking
    remove_package = None
    remove_user_data = None
    remove_dependencies = None


# ═══════════════════════════════════════════════════════════════════════════════
# FRAMEWORK CLI HANDLERS - Interactive with zDisplay, requires zKernel instance
# ═══════════════════════════════════════════════════════════════════════════════

def _confirm_action(display, action_description: str) -> bool:
    """
    Get user confirmation for destructive actions (FRAMEWORK version with zDisplay).
    
    Args:
        display: zDisplay instance (from zcli.display)
        action_description: Description of the action
    
    Returns:
        True if user confirms, False otherwise
    """
    response = display.read_string("\nType 'yes' to confirm: ").strip().lower()
    if response != "yes":
        display.error("Cancelled", indent=1)
        return False
    return True


def cli_uninstall_complete(zcli: "zCLI"):
    """
    Complete uninstall: Remove EVERYTHING (package + data + dependencies).
    
    CLI handler with interactive confirmation and zDisplay output.
    
    Args:
        zcli: zKernel instance
    
    Exits:
        0 if successful, 1 if failed
    
    Framework Dependencies:
        - zcli.display (zDisplay instance)
        - zcli.config.sys_paths (system paths configuration)
    """
    display = zcli.display
    paths = zcli.config.sys_paths
    
    display.zDeclare("Complete Uninstall", color="MAIN", indent=0, style="full")
    display.warning("Removes EVERYTHING - package, data, dependencies", indent=1)
    
    if not _confirm_action(display, "complete uninstall"):
        sys.exit(1)
    
    # Remove data
    data_results = remove_user_data(
        paths.user_config_dir,
        paths.user_data_dir,
        paths.user_cache_dir
    )
    
    # Remove dependencies
    dep_results = remove_dependencies()
    
    # Remove package
    pkg_success, pkg_msg = remove_package()
    
    # Display results
    display.zDeclare("", color="MAIN", indent=0, style="full")
    
    # Data results
    data_success_count = sum(1 for success, _ in data_results.values() if success)
    if data_success_count > 0:
        display.success(f"User data removed ({data_success_count}/3 directories)", indent=1)
    
    # Dependency results
    dep_success_count = sum(1 for success, _ in dep_results.values() if success)
    if dep_success_count > 0:
        display.success(f"Dependencies removed ({dep_success_count}/{len(dep_results)} packages)", indent=1)
    
    # Package result
    if pkg_success:
        display.success(pkg_msg, indent=1)
    else:
        display.error(pkg_msg, indent=1)
    
    # Overall success
    all_success = pkg_success and data_success_count == 3 and dep_success_count == len(dep_results)
    
    if all_success:
        display.success("Complete removal successful", indent=1)
        sys.exit(0)
    
    display.warning("Completed with errors", indent=1)
    sys.exit(1)


def cli_uninstall_package_only(zcli: "zCLI"):
    """
    Package-only uninstall: Remove package, keep data + dependencies.
    
    Use case: Upgrade/reinstall scenario, preserve configs and data.
    
    CLI handler with interactive confirmation and zDisplay output.
    
    Args:
        zcli: zKernel instance
    
    Exits:
        0 if successful, 1 if failed
    
    Framework Dependencies:
        - zcli.display (zDisplay instance)
        - zcli.config.sys_paths (system paths configuration)
    """
    display = zcli.display
    paths = zcli.config.sys_paths
    
    display.zDeclare("Package Only", color="MAIN", indent=0, style="full")
    display.info("Removes package only - preserves data and dependencies", indent=1)
    
    display.list([
        f"Config: {paths.user_config_dir}",
        f"Data:   {paths.user_data_dir}",
        f"Cache:  {paths.user_cache_dir}"
    ], style="bullet", indent=2)
    
    if not _confirm_action(display, "package-only uninstall"):
        sys.exit(1)
    
    pkg_success, pkg_msg = remove_package()
    
    display.zDeclare("", color="MAIN", indent=0, style="full")
    
    if pkg_success:
        display.success("Framework removed - data preserved", indent=1)
        sys.exit(0)
    
    display.error(pkg_msg, indent=1)
    sys.exit(1)


def cli_uninstall_data_only(zcli: "zCLI"):
    """
    Data-only uninstall: Remove user data, keep package + dependencies.
    
    Use case: Reset configuration/cache, keep framework installed.
    
    CLI handler with interactive confirmation and zDisplay output.
    
    Args:
        zcli: zKernel instance
    
    Exits:
        0 if successful, 1 if failed
    
    Framework Dependencies:
        - zcli.display (zDisplay instance)
        - zcli.config.sys_paths (system paths configuration)
    """
    display = zcli.display
    paths = zcli.config.sys_paths
    
    display.zDeclare("Data Only", color="MAIN", indent=0, style="full")
    display.warning("Removes user data - keeps package installed", indent=1)
    
    display.list([
        f"Config: {paths.user_config_dir}",
        f"Data:   {paths.user_data_dir}",
        f"Cache:  {paths.user_cache_dir}"
    ], style="bullet", indent=2)
    
    if not _confirm_action(display, "data-only removal"):
        sys.exit(1)
    
    data_results = remove_user_data(
        paths.user_config_dir,
        paths.user_data_dir,
        paths.user_cache_dir
    )
    
    display.zDeclare("", color="MAIN", indent=0, style="full")
    
    success_count = sum(1 for success, _ in data_results.values() if success)
    
    if success_count > 0:
        display.success(f"User data removed ({success_count}/3 directories)", indent=1)
        display.info("Framework still installed - reinstall not needed", indent=1)
        sys.exit(0)
    
    display.warning("No data directories found", indent=1)
    sys.exit(0)
