"""
zOS File Opener Utility

Lightweight, dependency-free file opening utility for the zOS layer.
Provides primitive OS-level file opening without UI frameworks.

Architecture:
    - zOS Layer: Primitive operations (this module)
    - zKernel Layer: Framework operations (zOpen with zDisplay, zDialog, hooks)

Key Features:
    - Simple subprocess-based file opening
    - Reads IDE preference from zMachine config
    - Cross-platform support (macOS, Linux, Windows)
    - No dependencies on zKernel subsystems
    - Suitable for CLI and scripting

Usage:
    from zOS.utils.file_opener import open_file_in_editor
    
    success = open_file_in_editor("/path/to/file.txt")
    # Opens in IDE from zMachine config
    
    success = open_file_in_editor("/path/to/file.txt", editor="cursor")
    # Opens in specific editor

Version: 1.0.0
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def get_ide_from_config() -> str:
    """
    Read IDE preference from zMachine configuration.
    
    Returns:
        IDE name from zConfig.machine.zolo, or "code" as fallback
    """
    from zOS.paths import get_ecosystem_root
    
    config_path = get_ecosystem_root() / "zConfig.machine.zolo"
    
    if not config_path.exists():
        return "code"  # Default fallback
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            in_user_prefs = False
            for line in f:
                stripped = line.strip()
                
                # Check for user_preferences section
                if stripped.startswith('user_preferences:'):
                    in_user_prefs = True
                    continue
                
                # Exit section when we hit another first-level key
                if in_user_prefs and line.startswith('  ') and not line.startswith('    '):
                    if ':' in stripped and not stripped.startswith('#'):
                        # Another first-level key
                        section_name = stripped.split(':')[0].strip()
                        if section_name != 'user_preferences':
                            break
                
                # Parse ide value
                if in_user_prefs and 'ide:' in stripped:
                    # Extract value: ide: "code" or ide: "cursor"
                    value = stripped.split('ide:')[1].strip()
                    # Remove quotes and comments
                    value = value.split('#')[0].strip().strip('"').strip("'")
                    return value if value else "code"
    
    except Exception:
        pass
    
    return "code"  # Fallback


def get_editor_command(editor: str) -> tuple[Optional[list], bool]:
    """
    Get platform-specific command to launch an editor.
    
    Args:
        editor: Editor name (cursor, code, subl, vim, etc.)
        
    Returns:
        Tuple of (command list, is_terminal_editor)
        - command: List for subprocess, or None if unsupported
        - is_terminal_editor: True if editor runs in terminal (blocking), False if GUI (non-blocking)
    """
    # Normalize editor name
    editor = editor.lower().strip()
    
    # Platform detection
    is_macos = sys.platform == "darwin"
    is_linux = sys.platform.startswith("linux")
    is_windows = sys.platform == "win32"
    
    # macOS
    if is_macos:
        if editor == "cursor":
            return (["open", "-a", "Cursor"], False)
        elif editor in ("code", "vscode"):
            return (["open", "-a", "Visual Studio Code"], False)
        elif editor in ("subl", "sublime"):
            return (["open", "-a", "Sublime Text"], False)
        elif editor == "vim":
            return (["vim"], True)  # Terminal editor
        elif editor == "emacs":
            return (["emacs"], True)  # Terminal editor
        elif editor == "nano":
            return (["nano"], True)  # Terminal editor
        else:
            # Try generic open (TextEdit)
            return (["open", "-e"], False)
    
    # Linux
    elif is_linux:
        if editor == "cursor":
            return (["cursor"], False)
        elif editor in ("code", "vscode"):
            return (["code"], False)
        elif editor in ("subl", "sublime"):
            return (["subl"], False)
        elif editor == "vim":
            return (["vim"], True)  # Terminal editor
        elif editor == "emacs":
            return (["emacs"], True)  # Terminal editor
        elif editor == "nano":
            return (["nano"], True)  # Terminal editor
        elif editor == "gedit":
            return (["gedit"], False)
        else:
            # Try xdg-open
            return (["xdg-open"], False)
    
    # Windows
    elif is_windows:
        if editor == "cursor":
            return (["cursor.cmd"], False)
        elif editor in ("code", "vscode"):
            return (["code.cmd"], False)
        elif editor in ("subl", "sublime"):
            return (["subl.exe"], False)
        elif editor == "vim":
            return (["vim"], True)  # Terminal editor
        elif editor == "notepad":
            return (["notepad.exe"], False)
        else:
            # Try generic start
            return (["start", ""], False)
    
    return (None, False)


def open_file_in_editor(file_path: str, editor: Optional[str] = None) -> bool:
    """
    Open a file in the specified editor (or IDE from zMachine).
    
    This is a primitive, dependency-free file opener suitable for CLI operations.
    It does not depend on zKernel subsystems (zDisplay, zDialog, etc.).
    
    Behavior:
        - Terminal editors (vim, emacs, nano): Opens in CURRENT terminal (blocking)
        - GUI editors (cursor, code, subl): Opens in new window (non-blocking)
    
    Args:
        file_path: Path to the file to open
        editor: Specific editor name, or None to use zMachine.ide
        
    Returns:
        True if successfully launched editor, False otherwise
        
    Examples:
        >>> open_file_in_editor("/path/to/file.txt")
        True  # Opens in IDE from config
        
        >>> open_file_in_editor("/path/to/file.txt", editor="cursor")
        True  # Opens in Cursor (non-blocking)
        
        >>> open_file_in_editor("/path/to/file.txt", editor="vim")
        True  # Opens vim in current terminal (blocks until exit)
        
    Version: 1.1.0
    """
    # Resolve path
    path = Path(file_path).expanduser().resolve()
    
    # Check if file exists
    if not path.exists():
        return False
    
    # Get editor
    if editor is None:
        editor = get_ide_from_config()
    
    # Get command and editor type
    cmd, is_terminal = get_editor_command(editor)
    if cmd is None:
        return False
    
    # Build full command with file path
    full_cmd = cmd + [str(path)]
    
    # Launch editor
    try:
        if is_terminal:
            # Terminal editors: Run in current terminal (blocking)
            # This is the natural behavior developers expect
            result = subprocess.call(full_cmd)
            return result == 0
        else:
            # GUI editors: Launch in background (non-blocking)
            subprocess.Popen(
                full_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True
    
    except Exception:
        return False


__all__ = [
    "open_file_in_editor",
    "get_ide_from_config",
    "get_editor_command",
]
