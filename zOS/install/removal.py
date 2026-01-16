#!/usr/bin/env python3
# zOS/install/removal.py
"""
OS-level uninstall utilities for Zolo packages.

Provides core removal functions (reusable, return results) for package management.
These are OS primitives with no framework dependencies.

Framework-level CLI handlers (with zDisplay) have been extracted to:
@temp_zKernel/cli/uninstall.py (will be merged into zKernel when it joins monorepo)

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
# CORE FUNCTIONS - OS primitives, no framework dependencies, return results
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
        
        # Find pyproject.toml (assuming we're in zOS/install/, go up two levels)
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
    Remove zolo-zcli package via pip (OS-level primitive).
    
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
    Remove user data directories (config, data, cache) - OS-level primitive.
    
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
    Remove optional dependencies (OS-level primitive).
    
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
# NOTE: Framework CLI handlers moved to @temp_zKernel/cli/uninstall.py
# ═══════════════════════════════════════════════════════════════════════════════
#
# The following functions have been extracted to @temp_zKernel (framework layer):
# - cli_uninstall_complete(zcli) - Uses zcli.display, zcli.config.sys_paths
# - cli_uninstall_package_only(zcli) - Uses zcli.display, zcli.config.sys_paths
# - cli_uninstall_data_only(zcli) - Uses zcli.display, zcli.config.sys_paths
#
# These are framework-level CLI commands that depend on zKernel framework components.
# They will be merged into zKernel when it joins the monorepo.
#
# For OS-level uninstall needs, use the core functions above directly.
#
# ═══════════════════════════════════════════════════════════════════════════════
