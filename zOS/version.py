# zOS/version.py
"""Version information for zOS (Zolo Operating System)."""

__version__ = "1.0.0"

def get_version() -> str:
    """Get zOS version string."""
    return __version__

def get_package_info() -> dict:
    """
    Get zOS package information.
    
    Returns:
        dict: Package metadata
    """
    return {
        'name': 'zOS',
        'version': __version__,
        'description': 'Zolo Operating System',
        'author': 'Gal Nachshon',
        'license': 'MIT',
    }
