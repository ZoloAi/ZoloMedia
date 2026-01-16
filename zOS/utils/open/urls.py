"""
zOS URL Opening Primitives

URL opening functionality using subprocess and webbrowser.
Pure OS operations without framework dependencies.

Version: 1.0.0
"""

import subprocess
import webbrowser
from typing import Optional

from .helpers import get_browser_command


def open_url_primitive(url: str, browser: Optional[str] = None) -> bool:
    """
    Open URL in browser using OS primitives.
    
    Args:
        url: Full URL to open (must include scheme)
        browser: Optional browser name (e.g., "chrome", "firefox")
                If not provided, reads from zConfig or uses system default
    
    Returns:
        True if URL opened successfully, False otherwise
    
    Opening Strategy:
        1. If browser specified: Try to launch specific browser
        2. Fallback to system default browser (webbrowser module)
        3. Return False if all attempts fail
    """
    # If no browser specified, try to get from config
    if not browser:
        browser = _get_browser_from_config()
    
    # Try specific browser if requested
    if browser and browser != "unknown":
        browser_cmd = get_browser_command(browser)
        if browser_cmd:
            cmd, args = browser_cmd
            try:
                full_cmd = [cmd] + args + [url]
                result = subprocess.run(
                    full_cmd,
                    check=False,
                    timeout=5,
                    capture_output=True
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                # Fall through to system default
                pass
    
    # Fallback to system default browser
    try:
        success = webbrowser.open(url)
        return success
    except Exception:
        return False


def _get_browser_from_config() -> Optional[str]:
    """
    Read browser preference from zConfig.machine.zolo.
    
    Returns:
        Browser name from config, or None if not found
    """
    try:
        from zOS.paths import get_ecosystem_root
        
        config_path = get_ecosystem_root() / "zConfig.machine.zolo"
        
        if not config_path.exists():
            return None
        
        # Parse config file to find browser value
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('browser:'):
                    # Extract value after colon
                    value = line.split(':', 1)[1].strip()
                    # Remove comments
                    if '#>' in value:
                        value = value.split('#>')[0].strip()
                    return value
        
        return None
    except Exception:
        return None
