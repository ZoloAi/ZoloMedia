"""
Interactive TUI editor for machine preferences.

Provides an OS-aware menu system for editing user_preferences in zConfig.machine.zolo.
Only shows applications that are actually installed on the system.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from zOS.machine.detectors import (
    enumerate_installed_browsers,
    enumerate_installed_ides,
    enumerate_installed_image_viewers,
    enumerate_installed_video_players,
    enumerate_installed_audio_players,
)
from zOS.paths import get_ecosystem_root


# ANSI color codes
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
RESET = "\033[0m"


def get_config_path() -> Path:
    """Get the path to zConfig.machine.zolo."""
    return get_ecosystem_root() / "zConfig.machine.zolo"


def load_config() -> Dict[str, Any]:
    """Load the current machine configuration."""
    config_path = get_config_path()
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_config(config: Dict[str, Any]) -> bool:
    """Save the updated configuration."""
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, indent=2, sort_keys=False, default_flow_style=False)
        return True
    except Exception as e:
        print(f"{RED}✗ Error saving configuration: {e}{RESET}")
        return False


def get_preference_info() -> Dict[str, Dict[str, Any]]:
    """
    Get information about each editable preference.
    
    Returns a dictionary with:
    - key: preference key name
    - display_name: human-readable name
    - enumerator: function to get installed options (or None for text input)
    - description: help text
    """
    return {
        "browser": {
            "display_name": "Browser",
            "enumerator": enumerate_installed_browsers,
            "description": "Default web browser for opening URLs"
        },
        "ide": {
            "display_name": "IDE / Text Editor",
            "enumerator": enumerate_installed_ides,
            "description": "Default editor for opening files"
        },
        "image_viewer": {
            "display_name": "Image Viewer",
            "enumerator": enumerate_installed_image_viewers,
            "description": "Default app for viewing images"
        },
        "video_player": {
            "display_name": "Video Player",
            "enumerator": enumerate_installed_video_players,
            "description": "Default app for playing videos"
        },
        "audio_player": {
            "display_name": "Audio Player",
            "enumerator": enumerate_installed_audio_players,
            "description": "Default app for playing audio"
        },
        "terminal": {
            "display_name": "Terminal",
            "enumerator": None,
            "description": "Terminal emulator type (usually auto-detected)"
        },
        "shell": {
            "display_name": "Shell",
            "enumerator": None,
            "description": "Shell executable path (e.g., /bin/zsh, /bin/bash)"
        },
    }


def show_main_menu(preferences: Dict[str, str]) -> None:
    """Display the main menu with current preferences."""
    print()
    print(f"{CYAN}╔{'═' * 70}╗{RESET}")
    print(f"{CYAN}║{RESET}  {BLUE}Edit User Preferences{RESET:<60} {CYAN}║{RESET}")
    print(f"{CYAN}╚{'═' * 70}╝{RESET}")
    print()
    
    print("Current preferences:")
    print()
    
    pref_info = get_preference_info()
    for i, (key, value) in enumerate(preferences.items(), 1):
        if key in pref_info:
            display_name = pref_info[key]["display_name"]
            print(f"  {CYAN}{i}.{RESET} {display_name:<20} {GREEN}{value}{RESET}")
    
    print()


def edit_preference(key: str, current_value: str, pref_info: Dict[str, Any]) -> Optional[str]:
    """
    Interactive editor for a single preference.
    
    Args:
        key: Preference key (e.g., "browser", "ide")
        current_value: Current value
        pref_info: Information about this preference
    
    Returns:
        New value, or None if cancelled
    """
    display_name = pref_info["display_name"]
    description = pref_info["description"]
    enumerator = pref_info["enumerator"]
    
    print()
    print(f"{CYAN}╔{'═' * 70}╗{RESET}")
    print(f"{CYAN}║{RESET}  {BLUE}Edit {display_name}{RESET:<60} {CYAN}║{RESET}")
    print(f"{CYAN}╚{'═' * 70}╝{RESET}")
    print()
    
    print(f"{YELLOW}{description}{RESET}")
    print()
    print(f"Current: {GREEN}{current_value}{RESET}")
    print()
    
    # Get installed options
    if enumerator:
        installed = enumerator()
        
        if installed:
            print(f"{BLUE}Installed on your system:{RESET}")
            print()
            for i, app in enumerate(installed, 1):
                marker = f"  {GREEN}(current){RESET}" if app.lower() == current_value.lower() else ""
                print(f"  {CYAN}{i}.{RESET} {app:<30} {marker}")
            print()
            
            choice = input(f"Choose (1-{len(installed)}), enter custom name, or press Enter to cancel: ")
            
            if not choice.strip():
                return None
            
            # Handle numeric choice
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(installed):
                    return installed[idx]
            
            # Handle custom entry
            return choice.strip()
        else:
            print(f"{YELLOW}⚠ No applications detected automatically.{RESET}")
            print()
            custom = input("Enter custom value, or press Enter to cancel: ")
            return custom.strip() if custom.strip() else None
    else:
        # Text input (for terminal, shell, etc.)
        new_value = input(f"Enter new value (or press Enter to keep '{current_value}'): ")
        return new_value.strip() if new_value.strip() else None


def interactive_edit() -> bool:
    """
    Main interactive editing loop.
    
    Returns:
        True if changes were made and saved, False otherwise
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"{RED}✗ {e}{RESET}")
        return False
    
    if 'zMachine' not in config or 'user_preferences' not in config['zMachine']:
        print(f"{RED}✗ Invalid configuration format{RESET}")
        return False
    
    preferences = config['zMachine']['user_preferences']
    pref_info = get_preference_info()
    changes_made = False
    
    while True:
        show_main_menu(preferences)
        
        print(f"Type a number to edit (1-{len(preferences)}), '{CYAN}s{RESET}' to save, '{CYAN}q{RESET}' to quit: ", end='')
        choice = input().strip().lower()
        
        if choice == 'q':
            if changes_made:
                print()
                save_choice = input(f"You have unsaved changes. Save before quitting? (y/n): ").strip().lower()
                if save_choice == 'y':
                    if save_config(config):
                        print(f"{GREEN}✓ Configuration saved!{RESET}")
                    else:
                        print(f"{RED}✗ Failed to save configuration{RESET}")
            print()
            print("Goodbye!")
            print()
            return changes_made
        
        if choice == 's':
            print()
            if save_config(config):
                print(f"{GREEN}✓ Configuration saved to {get_config_path().name}!{RESET}")
                changes_made = False
            else:
                print(f"{RED}✗ Failed to save configuration{RESET}")
            print()
            input("Press Enter to continue...")
            continue
        
        # Handle numeric choice
        if choice.isdigit():
            idx = int(choice) - 1
            keys = list(preferences.keys())
            
            if 0 <= idx < len(keys):
                key = keys[idx]
                
                if key in pref_info:
                    current_value = preferences[key]
                    new_value = edit_preference(key, current_value, pref_info[key])
                    
                    if new_value and new_value != current_value:
                        preferences[key] = new_value
                        config['zMachine']['user_preferences'] = preferences
                        changes_made = True
                        print()
                        print(f"{GREEN}✓{RESET} Updated {pref_info[key]['display_name']}: {BLUE}{new_value}{RESET}")
                        print()
                        input("Press Enter to continue...")
                else:
                    print(f"{RED}✗ Invalid preference key{RESET}")
            else:
                print(f"{RED}✗ Invalid choice{RESET}")
                input("Press Enter to continue...")
        else:
            print(f"{RED}✗ Invalid choice{RESET}")
            input("Press Enter to continue...")
    
    return changes_made
