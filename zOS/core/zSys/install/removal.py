#!/usr/bin/env python3
# zSys/install/removal.py
"""
Uninstall utilities for zolo-zcli package.

Provides both core functions (reusable, return results) and CLI handlers
(interactive with zDisplay).

Supports all installation types: editable, uv, venv, standard.
"""

import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Constants
PACKAGE_NAME = "zolo-zcli"


# ═══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS - Reusable, no display, return results
# ═══════════════════════════════════════════════════════════════════════════════

def get_optional_dependencies() -> List[str]:
    """
    Get list of optional dependencies from pyproject.toml dynamically.
    
    Returns:
        List of optional dependency package names
    
    Fallback:
        If pyproject.toml not found/parseable, returns hardcoded list
    """
    try:
        import tomli
        from pathlib import Path
        
        # Find pyproject.toml (assuming we're in zSys/install/, go up two levels)
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomli.load(f)
            
            # Extract dependencies from [project.optional-dependencies]
            optional_deps = data.get("project", {}).get("optional-dependencies", {})
            
            # Collect all unique packages (may be in csv, postgresql, all, etc.)
            all_deps = set()
            for dep_list in optional_deps.values():
                for dep in dep_list:
                    # Extract package name (before any version specifier)
                    pkg = dep.split("[")[0].split(">=")[0].split("==")[0].strip()
                    all_deps.add(pkg)
            
            return sorted(list(all_deps))
    
    except (ImportError, Exception):
        pass
    
    # Fallback to hardcoded list
    return ["pandas", "psycopg2-binary"]


def remove_package() -> Tuple[bool, str]:
    """
    Remove zolo-zcli package via pip.
    
    Works with all installation types (editable, uv, venv, standard).
    
    Returns:
        (success: bool, message: str)
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", PACKAGE_NAME, "-y"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return True, "Package removed successfully"
        
        return False, f"Package removal failed: {result.stderr.strip()}"
            
    except Exception as e:
        return False, f"Package removal error: {e}"


def remove_user_data(config_dir: Path, data_dir: Path, cache_dir: Path) -> Dict[str, Tuple[bool, str]]:
    """
    Remove user data directories (config, data, cache).
    
    Args:
        config_dir: Path to config directory
        data_dir: Path to data directory
        cache_dir: Path to cache directory
    
    Returns:
        Dict with results for each directory:
        {
            "config": (success: bool, message: str),
            "data": (success: bool, message: str),
            "cache": (success: bool, message: str)
        }
    """
    results = {}
    
    dirs = {
        "config": config_dir,
        "data": data_dir,
        "cache": cache_dir
    }
    
    for name, dir_path in dirs.items():
        if not dir_path.exists():
            results[name] = (True, f"{name.title()} directory not found (already clean)")
            continue
        
        try:
            shutil.rmtree(dir_path)
            results[name] = (True, f"{name.title()} directory removed")
        except Exception as e:
            results[name] = (False, f"{name.title()} removal failed: {e}")
    
    return results


def remove_dependencies(dependencies: Optional[List[str]] = None) -> Dict[str, Tuple[bool, str]]:
    """
    Remove optional dependencies.
    
    Args:
        dependencies: List of package names to remove (defaults to auto-detected)
    
    Returns:
        Dict with results for each dependency:
        {
            "pandas": (success: bool, message: str),
            "psycopg2-binary": (success: bool, message: str),
            ...
        }
    """
    if dependencies is None:
        dependencies = get_optional_dependencies()
    
    results = {}
    
    for dep in dependencies:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", dep, "-y"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                results[dep] = (True, f"{dep} removed")
            else:
                results[dep] = (False, f"{dep} removal failed: {result.stderr.strip()}")
                
        except Exception as e:
            results[dep] = (False, f"{dep} removal error: {e}")
    
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI HANDLERS - Interactive with zDisplay, sys.exit(), user confirmation
# ═══════════════════════════════════════════════════════════════════════════════

def _confirm_action(display, action_description: str) -> bool:
    """
    Get user confirmation for destructive actions.
    
    Args:
        display: zDisplay instance
        action_description: Description of the action
    
    Returns:
        True if user confirms, False otherwise
    """
    response = display.read_string("\nType 'yes' to confirm: ").strip().lower()
    if response != "yes":
        display.error("Cancelled", indent=1)
        return False
    return True


def cli_uninstall_complete(zcli):
    """
    Complete uninstall: Remove EVERYTHING (package + data + dependencies).
    
    CLI handler with interactive confirmation and display.
    
    Args:
        zcli: zCLI instance
    
    Exits:
        0 if successful, 1 if failed
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


def cli_uninstall_package_only(zcli):
    """
    Package-only uninstall: Remove package, keep data + dependencies.
    
    Use case: Upgrade/reinstall scenario, preserve configs and data.
    
    CLI handler with interactive confirmation and display.
    
    Args:
        zcli: zCLI instance
    
    Exits:
        0 if successful, 1 if failed
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


def cli_uninstall_data_only(zcli):
    """
    Data-only uninstall: Remove user data, keep package + dependencies.
    
    Use case: Reset configuration/cache, keep framework installed.
    
    CLI handler with interactive confirmation and display.
    
    Args:
        zcli: zCLI instance
    
    Exits:
        0 if successful, 1 if failed
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

