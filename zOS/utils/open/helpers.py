"""
zOS Open Helpers

Helper functions for URL detection, normalization, and command building.

Version: 1.0.0
"""

import platform
import shutil
from typing import Optional, Tuple, List


def is_url_string(text: str) -> bool:
    """Check if a string appears to be a URL."""
    text_lower = text.lower()
    return (
        text_lower.startswith('http://') or
        text_lower.startswith('https://') or
        text_lower.startswith('www.')
    )


def normalize_url(url: str) -> str:
    """
    Normalize a URL by adding https:// if needed.
    
    Args:
        url: URL string
    
    Returns:
        Normalized URL with scheme
    
    Examples:
        >>> normalize_url("www.google.com")
        "https://www.google.com"
        
        >>> normalize_url("https://github.com")
        "https://github.com"
    """
    if url.startswith('www.'):
        return f'https://{url}'
    return url


def get_browser_command(browser: Optional[str] = None) -> Optional[Tuple[str, List[str]]]:
    """
    Get platform-specific browser launch command.
    
    Args:
        browser: Browser name (e.g., "chrome", "firefox", "safari")
    
    Returns:
        Tuple of (command, args) or None if browser not found
        
    Examples:
        >>> get_browser_command("chrome")  # macOS
        ("open", ["-a", "Google Chrome"])
        
        >>> get_browser_command("firefox")  # Linux
        ("firefox", [])
    """
    if not browser or browser == "unknown":
        return None
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        browser_map = {
            "chrome": ("open", ["-a", "Google Chrome"]),
            "firefox": ("open", ["-a", "Firefox"]),
            "safari": ("open", ["-a", "Safari"]),
            "brave": ("open", ["-a", "Brave Browser"]),
            "arc": ("open", ["-a", "Arc"]),
            "edge": ("open", ["-a", "Microsoft Edge"]),
        }
        result = browser_map.get(browser.lower())
        if result:
            return result
    
    elif system == "Linux":
        # On Linux, check if browser exists
        browser_lower = browser.lower()
        if shutil.which(browser_lower):
            return (browser_lower, [])
    
    elif system == "Windows":
        browser_map = {
            "chrome": ("start", ["chrome"]),
            "firefox": ("start", ["firefox"]),
            "edge": ("start", ["msedge"]),
        }
        result = browser_map.get(browser.lower())
        if result:
            return result
    
    return None


def get_editor_command(editor: str) -> Optional[Tuple[str, List[str]]]:
    """
    Get platform-specific editor launch command.
    
    Args:
        editor: Editor name (e.g., "cursor", "code", "vim")
    
    Returns:
        Tuple of (command, args) or None if editor not found
        
    Examples:
        >>> get_editor_command("cursor")
        ("cursor", [])
        
        >>> get_editor_command("code")
        ("code", [])
    """
    system = platform.system()
    
    # Common editors available via CLI on all platforms
    common_editors = ["cursor", "code", "vim", "nvim", "nano", "emacs", "subl"]
    
    if editor in common_editors:
        # Check if available
        if shutil.which(editor):
            return (editor, [])
    
    # Platform-specific handling
    if system == "Darwin":  # macOS
        # Some editors need to be launched via 'open -a'
        macos_app_editors = {
            "textmate": ("open", ["-a", "TextMate"]),
            "bbedit": ("open", ["-a", "BBEdit"]),
        }
        if editor.lower() in macos_app_editors:
            return macos_app_editors[editor.lower()]
    
    return None


def get_file_extension(filepath: str) -> str:
    """
    Get file extension in lowercase.
    
    Args:
        filepath: Path to file
    
    Returns:
        File extension including dot (e.g., ".py", ".txt")
        Empty string if no extension
    """
    import os
    _, ext = os.path.splitext(filepath)
    return ext.lower()


def should_open_in_browser(filepath: str) -> bool:
    """Check if file should be opened in browser (HTML files)."""
    ext = get_file_extension(filepath)
    return ext in ('.html', '.htm')


def should_open_in_editor(filepath: str) -> bool:
    """Check if file should be opened in editor (text files)."""
    ext = get_file_extension(filepath)
    text_extensions = (
        '.txt', '.md', '.py', '.js', '.ts', '.jsx', '.tsx',
        '.json', '.yaml', '.yml', '.zolo',
        '.sh', '.bash', '.zsh',
        '.c', '.cpp', '.h', '.hpp',
        '.java', '.go', '.rs', '.rb',
        '.php', '.html', '.css', '.scss',
        '.xml', '.toml', '.ini', '.cfg', '.conf',
        '.log', '.gitignore', '.env',
    )
    return ext in text_extensions
