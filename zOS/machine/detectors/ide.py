# zOS/machine/detectors/ide.py
"""IDE and text editor detection for Zolo ecosystem machine configuration."""

import os
import platform
import shutil
from typing import Optional
from .shared import _log_info, _log_config

# IDE detection constants
IDE_ENV_VARS = ("IDE", "VISUAL_EDITOR", "EDITOR", "VISUAL")
MODERN_IDES = ("cursor", "code", "fleet", "zed")
CLASSIC_IDES = ("subl", "atom", "webstorm", "pycharm", "idea")
SIMPLE_EDITORS = ("nano", "vim", "nvim", "vi")
FALLBACK_EDITOR = "nano"


def detect_ide(log_level: Optional[str] = None, is_production: bool = False) -> str:
    """Detect IDE/editor via env vars, PATH search (modern→classic→simple), fallback to nano."""
    # Check IDE/editor env vars
    for var in IDE_ENV_VARS:
        ide_env = os.getenv(var)
        if ide_env:
            _log_config(f"IDE from env var {var}: {ide_env}", log_level, is_production)
            return ide_env

    # Check for modern GUI IDEs (prioritized by popularity/modernity)
    for ide in MODERN_IDES:
        if shutil.which(ide):
            _log_info(f"Found modern IDE: {ide}", log_level, is_production)
            return ide

    # Check for classic IDEs
    for ide in CLASSIC_IDES:
        if shutil.which(ide):
            _log_config(f"Found classic IDE: {ide}", log_level, is_production)
            return ide

    # macOS-specific: Check for Xcode
    if platform.system() == "Darwin":
        if shutil.which("xed"):  # Xcode command-line tool
            _log_config("Found Xcode (xed)", log_level, is_production)
            return "xed"

    # Fallback to simple editors
    for editor in SIMPLE_EDITORS:
        if shutil.which(editor):
            _log_config(f"Falling back to simple editor: {editor}", log_level, is_production)
            return editor

    # Final fallback
    _log_config(f"Using final fallback: {FALLBACK_EDITOR}", is_production=is_production)
    return FALLBACK_EDITOR


def enumerate_installed_ides() -> list:
    """
    Return list of all installed IDEs and text editors on this system.
    
    Returns:
        List of IDE/editor names (e.g., ["cursor", "code", "vim", "nano"])
        Sorted by priority: modern IDEs → classic IDEs → simple editors
    """
    installed = []
    system = platform.system()
    
    if system == "Darwin":
        # macOS: Check /Applications/ for GUI IDEs and PATH for CLI tools
        macos_gui_ides = [
            ("Cursor", "cursor"),
            ("Visual Studio Code", "code"),
            ("Sublime Text", "subl"),
            ("Fleet", "fleet"),
            ("Zed", "zed"),
            ("Atom", "atom"),
            ("WebStorm", "webstorm"),
            ("PyCharm", "pycharm"),
            ("IntelliJ IDEA", "idea"),
        ]
        
        for app_name, display_name in macos_gui_ides:
            if os.path.exists(f"/Applications/{app_name}.app"):
                installed.append(display_name)
        
        # CLI tools
        cli_tools = ["vim", "nvim", "emacs", "nano", "vi"]
        for tool in cli_tools:
            if shutil.which(tool) and tool not in installed:
                installed.append(tool)
                
    elif system == "Linux" or system == "Windows":
        # Linux/Windows: Check PATH for all IDEs
        all_ides = [
            "cursor", "code", "subl", "fleet", "zed", "atom",
            "webstorm", "pycharm", "idea",
            "vim", "nvim", "emacs", "nano", "vi"
        ]
        
        for ide in all_ides:
            if shutil.which(ide):
                installed.append(ide)
    
    return installed


def get_ide_launch_command(ide_name: str) -> tuple:
    """
    Get platform-specific command to launch an IDE or text editor.
    
    Args:
        ide_name: IDE/editor name (e.g., "Cursor", "code", "cursor", "subl")
                 Case-insensitive, normalized internally
    
    Returns:
        Tuple of (command, args_template) where:
        - macOS GUI IDEs: ("open", ["-a", "Cursor"]) - use 'open -a "App Name"'
        - macOS CLI tools: ("cursor", []) - direct executable
        - Linux: ("cursor", []) - direct executable
        - Windows: ("cursor", []) - direct executable  
        - Unknown: (None, []) - IDE not mapped
    
    Examples:
        >>> get_ide_launch_command("cursor")
        # macOS: ("open", ["-a", "Cursor"])
        # Linux: ("cursor", []) if in PATH
        
        >>> get_ide_launch_command("code")
        # macOS: ("code", []) - VS Code CLI usually in PATH
        # Linux: ("code", [])
    """
    system = platform.system()
    ide_lower = ide_name.lower()
    
    # macOS: GUI apps need 'open -a', CLI tools use direct command
    if system == "Darwin":
        # macOS GUI app mappings (need 'open -a')
        macos_gui_apps = {
            "cursor": "Cursor",
            "subl": "Sublime Text",
            "sublime": "Sublime Text",
            "atom": "Atom",
            "webstorm": "WebStorm",
            "pycharm": "PyCharm",
            "idea": "IntelliJ IDEA",
            "fleet": "Fleet",
            "zed": "Zed",
        }
        
        # Check if it's a GUI app
        app_name = macos_gui_apps.get(ide_lower)
        if app_name:
            return ("open", ["-a", app_name])
        
        # CLI tools that should work directly on macOS (usually in PATH)
        macos_cli_tools = {
            "code": "code",        # VS Code CLI
            "nano": "nano",
            "vim": "vim",
            "nvim": "nvim",
            "vi": "vi",
            "emacs": "emacs",
            "xed": "xed",         # Xcode editor
        }
        
        cmd = macos_cli_tools.get(ide_lower)
        if cmd and shutil.which(cmd):
            return (cmd, [])
        
        return (None, [])
    
    # Linux: Direct executable names
    elif system == "Linux":
        linux_commands = {
            "cursor": "cursor",
            "code": "code",
            "subl": "subl",
            "sublime": "subl",
            "atom": "atom",
            "webstorm": "webstorm",
            "pycharm": "pycharm",
            "idea": "idea",
            "fleet": "fleet",
            "zed": "zed",
            "nano": "nano",
            "vim": "vim",
            "nvim": "nvim",
            "vi": "vi",
            "emacs": "emacs",
        }
        
        cmd = linux_commands.get(ide_lower)
        if cmd and shutil.which(cmd):
            return (cmd, [])
        
        return (None, [])
    
    # Windows: Direct executable names
    elif system == "Windows":
        windows_commands = {
            "cursor": "cursor",
            "code": "code",
            "subl": "subl",
            "sublime": "subl",
            "atom": "atom",
            "webstorm": "webstorm",
            "pycharm": "pycharm",
            "idea": "idea",
            "fleet": "fleet",
            "zed": "zed",
            "nano": "nano",
            "vim": "vim",
            "nvim": "nvim",
            "notepad": "notepad",
        }
        
        cmd = windows_commands.get(ide_lower)
        if cmd and shutil.which(cmd):
            return (cmd, [])
        
        return (None, [])
    
    return (None, [])

