"""
zOS File Opening Primitives

File opening functionality using subprocess and webbrowser.
Pure OS operations without framework dependencies.

Version: 1.0.0
"""

import os
import subprocess
import webbrowser
from typing import Optional

from .helpers import (
    get_editor_command,
    get_file_extension,
    should_open_in_browser,
    should_open_in_editor,
)


def open_file_primitive(filepath: str, editor: Optional[str] = None) -> bool:
    """
    Open file in appropriate application using OS primitives.
    
    Args:
        filepath: Absolute path to file
        editor: Optional editor override (e.g., "cursor", "code")
                If not provided, reads from zConfig
    
    Returns:
        True if file opened successfully, False otherwise
    
    Opening Strategy:
        1. Detect file type by extension
        2. HTML files: Open in browser (file:// URL)
        3. Text files: Open in editor
        4. Other: Return False
    """
    # Check file exists
    if not os.path.exists(filepath):
        return False
    
    # Route based on file type
    if should_open_in_browser(filepath):
        return _open_html_file(filepath)
    elif should_open_in_editor(filepath):
        return _open_text_file(filepath, editor)
    else:
        # Unsupported file type
        return False


def _open_html_file(filepath: str) -> bool:
    """Open HTML file in browser."""
    try:
        # Convert to file:// URL
        file_url = f"file://{os.path.abspath(filepath)}"
        return webbrowser.open(file_url)
    except Exception:
        return False


def _open_text_file(filepath: str, editor: Optional[str] = None) -> bool:
    """Open text file in editor."""
    # If no editor specified, get from config
    if not editor:
        editor = _get_editor_from_config()
    
    # Get editor command
    if not editor:
        editor = "code"  # Fallback default
    
    editor_cmd = get_editor_command(editor)
    if not editor_cmd:
        # Try default system editor
        return _try_system_open(filepath)
    
    cmd, args = editor_cmd
    
    try:
        full_cmd = [cmd] + args + [filepath]
        result = subprocess.run(
            full_cmd,
            check=False,
            timeout=5,
            capture_output=True
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Fallback to system open
        return _try_system_open(filepath)


def _try_system_open(filepath: str) -> bool:
    """Try to open file with system default application."""
    import platform
    
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", filepath], check=True, timeout=5)
            return True
        elif system == "Linux":
            subprocess.run(["xdg-open", filepath], check=True, timeout=5)
            return True
        elif system == "Windows":
            os.startfile(filepath)  # type: ignore
            return True
    except Exception:
        pass
    
    return False


def _get_editor_from_config() -> Optional[str]:
    """
    Read IDE preference from zConfig.machine.zolo.
    
    Returns:
        Editor name from config, or None if not found
    """
    try:
        from zOS.paths import get_ecosystem_root
        
        config_path = get_ecosystem_root() / "zConfig.machine.zolo"
        
        if not config_path.exists():
            return None
        
        # Parse config file to find ide value
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('ide:'):
                    # Extract value after colon
                    value = line.split(':', 1)[1].strip()
                    # Remove comments
                    if '#>' in value:
                        value = value.split('#>')[0].strip()
                    return value
        
        return None
    except Exception:
        return None
