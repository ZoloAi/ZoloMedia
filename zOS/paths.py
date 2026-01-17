# zOS/paths.py
r"""
Cross-platform path utilities for Zolo ecosystem.

Provides centralized path resolution for all Zolo products using OS-native conventions.
Foundation layer - used by zKernel, zLSP, zTheme, and other ecosystem products.

Architecture:
    ~/Library/Application Support/Zolo/          (ecosystem root)
        ├─ logs/                                  (ecosystem-level logs)
        │   └─ zOS.log
        ├─ zKernel/                               (product-specific)
        │   ├─ logs/
        │   ├─ zConfigs/
        │   └─ ...
        ├─ zLSP/
        │   └─ logs/
        └─ ...

Uses platformdirs for cross-platform compatibility:
    - Windows: %LOCALAPPDATA%\Zolo\
    - macOS:   ~/Library/Application Support/Zolo/
    - Linux:   ~/.local/share/Zolo/
"""

import platform
from pathlib import Path

try:
    import platformdirs
except ImportError:
    # Fallback if platformdirs not available
    platformdirs = None


# Ecosystem constants
APP_NAME = "Zolo"
APP_AUTHOR = "zolo"


def get_ecosystem_root() -> Path:
    r"""
    Get ecosystem root directory.
    
    Returns:
        Path: ~/Library/Application Support/Zolo/ (macOS)
              %LOCALAPPDATA%\Zolo\ (Windows)
              ~/.local/share/Zolo/ (Linux)
    
    Examples:
        >>> get_ecosystem_root()
        PosixPath('/Users/username/Library/Application Support/Zolo')
    """
    if platformdirs:
        return Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
    else:
        # Fallback implementation
        home = Path.home()
        system = platform.system()
        
        if system == "Windows":
            return home / "AppData" / "Local" / APP_NAME
        elif system == "Darwin":  # macOS
            return home / "Library" / "Application Support" / APP_NAME
        else:  # Linux
            return home / ".local" / "share" / APP_NAME


def get_product_root(product: str) -> Path:
    """
    Get product-specific root directory.
    
    Args:
        product: Product name (e.g., "zKernel", "zLSP", "zTheme")
    
    Returns:
        Path: ~/Library/Application Support/Zolo/{product}/ (macOS)
    
    Examples:
        >>> get_product_root("zKernel")
        PosixPath('/Users/username/Library/Application Support/Zolo/zKernel')
        
        >>> get_product_root("zLSP")
        PosixPath('/Users/username/Library/Application Support/Zolo/zLSP')
    """
    return get_ecosystem_root() / product


def get_ecosystem_logs() -> Path:
    """
    Get ecosystem-level logs directory.
    
    Returns:
        Path: ~/Library/Application Support/Zolo/logs/ (macOS)
    
    Examples:
        >>> get_ecosystem_logs()
        PosixPath('/Users/username/Library/Application Support/Zolo/logs')
    
    Note:
        Used for zOS ecosystem operations (CLI commands, installations).
        Product-specific logs go in get_product_root(product) / "logs"
    """
    return get_ecosystem_root() / "logs"


def get_product_logs(product: str) -> Path:
    """
    Get product-specific logs directory.
    
    Args:
        product: Product name (e.g., "zKernel", "zLSP")
    
    Returns:
        Path: ~/Library/Application Support/Zolo/{product}/logs/ (macOS)
    
    Examples:
        >>> get_product_logs("zKernel")
        PosixPath('/Users/username/Library/Application Support/Zolo/zKernel/logs')
    """
    return get_product_root(product) / "logs"


def get_ecosystem_cache() -> Path:
    r"""
    Get ecosystem cache directory.
    
    Returns:
        Path: ~/Library/Caches/Zolo/ (macOS)
              %LOCALAPPDATA%\Zolo\Cache (Windows)
              ~/.cache/Zolo/ (Linux)
    
    Examples:
        >>> get_ecosystem_cache()
        PosixPath('/Users/username/Library/Caches/Zolo')
    """
    if platformdirs:
        return Path(platformdirs.user_cache_dir(APP_NAME, APP_AUTHOR))
    else:
        # Fallback implementation
        home = Path.home()
        system = platform.system()
        
        if system == "Windows":
            return home / "AppData" / "Local" / APP_NAME / "Cache"
        elif system == "Darwin":  # macOS
            return home / "Library" / "Caches" / APP_NAME
        else:  # Linux
            return home / ".cache" / APP_NAME
