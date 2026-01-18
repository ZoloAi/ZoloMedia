# zCLI/L1_Foundation/a_zConfig/zConfig_modules/helpers/detectors/browser.py
"""Browser detection for zCLI machine configuration."""

from zOS import os, platform, subprocess, shutil
from typing import Optional
from .shared import SUBPROCESS_TIMEOUT_SEC, _log_info, _log_warning

# Browser detection constants
BROWSER_MAPPING = {
    'google.chrome': 'Chrome',
    'chrome': 'Chrome',
    'firefox': 'Firefox',
    'safari': 'Safari',
    'arc': 'Arc',
    'brave': 'Brave',
    'edge': 'Edge',
    'opera': 'Opera',
}

LINUX_BROWSERS = ("firefox", "google-chrome", "chromium", "brave-browser")
DEFAULT_MACOS_BROWSER = "Safari"
DEFAULT_LINUX_BROWSER = "firefox"
DEFAULT_WINDOWS_BROWSER = "Edge"

# Linux browser desktop file mapping (for xdg-settings output parsing)
LINUX_BROWSER_DESKTOP_MAP = {
    'firefox': 'firefox',
    'chrome': 'google-chrome',
    'chromium': 'chromium',
    'brave': 'brave-browser',
}


def detect_browser(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """Detect default browser via env var or platform-specific methods."""
    browser = os.getenv("BROWSER")  # Check env var first
    if browser:
        return browser

    system = platform.system()
    if system == "Darwin":
        browser = _detect_macos_browser(log_level, is_production)
    elif system == "Linux":
        browser = _detect_linux_browser(log_level, is_production)
    elif system == "Windows":
        browser = DEFAULT_WINDOWS_BROWSER
    else:
        browser = "unknown"

    return browser


def _detect_macos_browser(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """Query macOS LaunchServices for default browser, fallback to Safari."""
    try:
        # Check LaunchServices database for http handler
        result = subprocess.run(
            ['defaults', 'read', 'com.apple.LaunchServices/com.apple.launchservices.secure', 'LSHandlers'],
            capture_output=True, 
            text=True, 
            timeout=SUBPROCESS_TIMEOUT_SEC, 
            check=False
        )

        output_lower = result.stdout.lower()
        for key, name in BROWSER_MAPPING.items():
            if key in output_lower:
                _log_info(f"Found default browser via LaunchServices: {name}", log_level, is_production)
                return name

    except Exception as e:
        _log_warning(f"Could not query LaunchServices: {e}", log_level, is_production)

    return DEFAULT_MACOS_BROWSER


def _detect_linux_browser(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """Query xdg-settings or PATH for default browser, fallback to firefox."""
    # Try xdg-settings first
    try:
        result = subprocess.run(
            ['xdg-settings', 'get', 'default-web-browser'],
            capture_output=True, 
            text=True, 
            timeout=SUBPROCESS_TIMEOUT_SEC, 
            check=False
        )
        if result.returncode == 0:
            browser_desktop = result.stdout.strip().lower()
            for key, browser in LINUX_BROWSER_DESKTOP_MAP.items():
                if key in browser_desktop:
                    return browser
    except Exception:
        pass  # Fall through to PATH check

    # Check PATH for common browsers
    for browser in LINUX_BROWSERS:
        if shutil.which(browser):
            return browser

    return DEFAULT_LINUX_BROWSER


def get_browser_launch_command(browser_name: str) -> tuple:
    """
    Get platform-specific command to launch a browser.
    
    Args:
        browser_name: Browser name (e.g., "Firefox", "Chrome", "firefox", "chrome")
                     Case-insensitive, normalized internally
    
    Returns:
        Tuple of (command, args_template) where:
        - macOS: ("open", ["-a", "Firefox"]) - use 'open -a "App Name"'
        - Linux: ("firefox", []) - direct executable
        - Windows: ("firefox", []) - direct executable  
        - Unknown: (None, []) - browser not mapped
    
    Examples:
        >>> get_browser_launch_command("firefox")
        # macOS: ("open", ["-a", "Firefox"])
        # Linux: ("firefox", [])
        
        >>> get_browser_launch_command("Chrome")
        # macOS: ("open", ["-a", "Google Chrome"])
        # Linux: ("google-chrome", [])
    """
    system = platform.system()
    browser_lower = browser_name.lower()
    
    # macOS: Use 'open -a "App Name"'
    if system == "Darwin":
        macos_apps = {
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "safari": "Safari",
            "arc": "Arc",
            "brave": "Brave Browser",
            "edge": "Microsoft Edge",
            "opera": "Opera",
        }
        app_name = macos_apps.get(browser_lower)
        if app_name:
            return ("open", ["-a", app_name])
        return (None, [])
    
    # Linux: Direct executable names
    elif system == "Linux":
        linux_commands = {
            "chrome": "google-chrome",
            "firefox": "firefox",
            "chromium": "chromium",
            "brave": "brave-browser",
            "edge": "microsoft-edge",
            "opera": "opera",
        }
        cmd = linux_commands.get(browser_lower)
        if cmd and shutil.which(cmd):
            return (cmd, [])
        return (None, [])
    
    # Windows: Direct executable names
    elif system == "Windows":
        windows_commands = {
            "chrome": "chrome",
            "firefox": "firefox",
            "brave": "brave",
            "edge": "msedge",
            "opera": "opera",
        }
        cmd = windows_commands.get(browser_lower)
        if cmd and shutil.which(cmd):
            return (cmd, [])
        return (None, [])
    
    return (None, [])

