# zSys/install/detection.py
"""
Installation detection utilities (Layer 0 - System Foundation).

Provides portable installation type detection for zCLI without any
framework dependencies. Used by main.py bootstrap logger and info banner.
"""

from pathlib import Path
import os


def detect_installation_type(zcli_package, detailed: bool = False) -> str:
    """
    Detect zCLI installation type in a portable way.
    
    Args:
        zcli_package: The imported zCLI package (for __file__ access)
        detailed: If True, return detailed path info; if False, return simple type string
    
    Returns:
        str: Installation type ("editable", "standard", "uv", etc.)
    
    Examples:
        >>> import zCLI as zcli_package
        >>> detect_installation_type(zcli_package, detailed=False)
        'editable'
        >>> detect_installation_type(zcli_package, detailed=True)
        'editable (pip -e) at /Users/you/Projects/zolo-zcli/zCLI'
    
    Detection Logic:
        1. Not in site-packages → editable install (pip install -e .)
        2. VIRTUAL_ENV with 'uv' → uv environment
        3. VIRTUAL_ENV set → virtual environment
        4. Otherwise → standard (site-packages)
    
    Notes:
        - Portable across Windows, Mac, Linux
        - Based on Python packaging standards
        - No hardcoded paths or system assumptions
    """
    try:
        zcli_path = Path(zcli_package.__file__).resolve()
        is_site_packages = 'site-packages' in str(zcli_path)
        venv_path = os.getenv('VIRTUAL_ENV')

        # Determine type and detail
        if not is_site_packages:
            install_type = "editable"
            detail = f"editable (pip -e) at {zcli_path.parent}"
        elif venv_path and 'uv' in venv_path.lower():
            install_type = "uv"
            detail = f"uv environment at {venv_path}"
        elif venv_path:
            install_type = "venv"
            detail = f"venv at {venv_path}"
        else:
            install_type = "standard"
            detail = f"standard (site-packages) at {zcli_path.parent}"

        return detail if detailed else install_type

    except Exception as e:
        return f"unknown (detection failed: {e})" if detailed else "unknown"
