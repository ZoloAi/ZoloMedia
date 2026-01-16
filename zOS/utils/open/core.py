"""
zOS Open Core

Main interface for file and URL opening primitives.
Provides simple bool-based API for OS-level operations.

Version: 1.0.0
"""

import os
from typing import Optional
from pathlib import Path

from .files import open_file_primitive
from .urls import open_url_primitive
from .helpers import is_url_string, normalize_url


def open_file(filepath: str, editor: Optional[str] = None) -> bool:
    """
    Open a file in the appropriate application.
    
    Args:
        filepath: Path to file to open
        editor: Optional editor override (e.g., "cursor", "code")
               If not provided, reads from zConfig.machine.zolo
    
    Returns:
        True if file opened successfully, False otherwise
    
    Examples:
        >>> open_file("/path/to/file.py")  # Uses configured IDE
        True
        
        >>> open_file("/path/to/file.py", editor="cursor")  # Explicit IDE
        True
        
        >>> open_file("/nonexistent/file.txt")
        False
    """
    # Expand user home directory
    filepath = os.path.expanduser(filepath)
    
    # Check file exists
    if not os.path.exists(filepath):
        return False
    
    # Delegate to primitive
    return open_file_primitive(filepath, editor)


def open_url(url: str, browser: Optional[str] = None) -> bool:
    """
    Open a URL in the appropriate browser.
    
    Args:
        url: URL to open (http://, https://, or www.)
        browser: Optional browser override (e.g., "chrome", "firefox")
                If not provided, reads from zConfig.machine.zolo
    
    Returns:
        True if URL opened successfully, False otherwise
    
    Examples:
        >>> open_url("https://google.com")  # Uses configured browser
        True
        
        >>> open_url("www.github.com")  # Auto-adds https://
        True
        
        >>> open_url("https://example.com", browser="firefox")  # Explicit browser
        True
    """
    # Normalize URL (add https:// if needed)
    url = normalize_url(url)
    
    # Delegate to primitive
    return open_url_primitive(url, browser)


def is_url(text: str) -> bool:
    """
    Check if a string is a URL.
    
    Args:
        text: String to check
    
    Returns:
        True if text appears to be a URL, False otherwise
    
    Examples:
        >>> is_url("https://example.com")
        True
        
        >>> is_url("www.github.com")
        True
        
        >>> is_url("/path/to/file.txt")
        False
    """
    return is_url_string(text)
