"""
VS Code Integration Uninstaller for zlsp

Removes the zlsp VS Code extension and cleans up user settings.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from core.version import __version__
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.version import __version__


def get_vscode_user_settings_path() -> Path:
    """Get the path to VS Code user settings.json."""
    import platform
    
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        return Path.home() / 'Library' / 'Application Support' / 'Code' / 'User' / 'settings.json'
    elif system == 'Linux':
        return Path.home() / '.config' / 'Code' / 'User' / 'settings.json'
    elif system == 'Windows':
        return Path.home() / 'AppData' / 'Roaming' / 'Code' / 'User' / 'settings.json'
    else:
        # Fallback to Linux path
        return Path.home() / '.config' / 'Code' / 'User' / 'settings.json'


def create_settings_backup(settings_path: Path) -> Optional[Path]:
    """Create a backup of settings.json before modifying."""
    if not settings_path.exists():
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = settings_path.parent / f'settings.json.backup.{timestamp}'
    
    try:
        shutil.copy2(settings_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"  ⚠ Warning: Failed to create backup: {e}")
        return None


def remove_semantic_token_colors_from_settings(settings_path: Path) -> tuple[bool, str]:
    """
    Remove Zolo-specific semantic token colors from user's settings.json.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not settings_path.exists():
        return True, "Settings file not found (nothing to clean)"
    
    try:
        # Read current settings
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Check if our settings exist
        if 'editor.semanticTokenColorCustomizations' not in settings:
            return True, "No semantic token customizations found"
        
        customizations = settings['editor.semanticTokenColorCustomizations']
        
        if '[zolo]' not in customizations:
            return True, "No Zolo-specific customizations found"
        
        # Create backup before modifying
        backup_path = create_settings_backup(settings_path)
        if backup_path:
            print(f"  ✓ Backup created: {backup_path.name}")
        
        # Remove [zolo] section
        del customizations['[zolo]']
        
        # If customizations is now empty, remove the entire key
        if not customizations:
            del settings['editor.semanticTokenColorCustomizations']
            message = "Removed entire 'editor.semanticTokenColorCustomizations' (was empty)"
        else:
            message = "Removed '[zolo]' section from semantic token customizations"
        
        # Write back to settings.json
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline
        
        return True, message
        
    except json.JSONDecodeError as e:
        return False, f"Settings file is invalid JSON: {e}"
    except Exception as e:
        return False, f"Failed to modify settings: {e}"


def main():
    """Uninstall the VS Code extension and clean up settings."""
    print("═" * 70)
    print("  zlsp VS Code Extension Uninstaller")
    print("═" * 70)
    print()
    
    # [1/3] Check for extension
    print("[1/3] Checking for installed extension...")
    extensions_dir = Path.home() / '.vscode' / 'extensions'
    extension_dir = extensions_dir / f'zolo-lsp-{__version__}'
    
    extension_found = extension_dir.exists()
    
    if extension_found:
        print(f"  ✓ Found: {extension_dir}")
    else:
        print(f"  ℹ Extension not found: {extension_dir}")
    
    # [2/3] Check for settings
    print()
    print("[2/3] Checking for settings...")
    settings_path = get_vscode_user_settings_path()
    
    settings_found = False
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                if 'editor.semanticTokenColorCustomizations' in settings:
                    if '[zolo]' in settings['editor.semanticTokenColorCustomizations']:
                        settings_found = True
                        print(f"  ✓ Found Zolo settings: {settings_path}")
                    else:
                        print(f"  ℹ No Zolo settings found")
                else:
                    print(f"  ℹ No semantic token customizations found")
        except Exception as e:
            print(f"  ⚠ Could not read settings: {e}")
    else:
        print(f"  ℹ Settings file not found")
    
    # Check if anything to uninstall
    if not extension_found and not settings_found:
        print()
        print("  ℹ Nothing to uninstall.")
        print()
        return
    
    # Confirm uninstallation
    print()
    print("Will remove:")
    if extension_found:
        print(f"  • Extension: {extension_dir}")
    if settings_found:
        print(f"  • Settings: '[zolo]' section in settings.json")
    print()
    
    try:
        response = input("  Proceed with uninstallation? (y/N): ").strip().lower()
        if response != 'y':
            print("  Cancelled.")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return
    
    # [3/3] Perform uninstallation
    print()
    print("[3/3] Uninstalling...")
    
    success = True
    
    # Remove extension directory
    if extension_found:
        try:
            shutil.rmtree(extension_dir)
            print(f"  ✓ Extension directory removed")
        except Exception as e:
            print(f"  ✗ Failed to remove extension: {e}")
            success = False
    
    # Clean up settings
    if settings_found:
        cleanup_success, cleanup_message = remove_semantic_token_colors_from_settings(settings_path)
        if cleanup_success:
            print(f"  ✓ {cleanup_message}")
        else:
            print(f"  ✗ {cleanup_message}")
            success = False
    
    # Summary
    print()
    print("═" * 70)
    if success:
        print("  ✓ Uninstallation Complete!")
    else:
        print("  ⚠ Uninstallation Completed with Warnings")
    print("═" * 70)
    print()
    
    if success:
        print("  All Zolo LSP components removed:")
        if extension_found:
            print("    ✓ Extension directory")
        if settings_found:
            print("    ✓ User settings (semantic token colors)")
        print()
        print("  Reload VS Code to complete uninstallation:")
        print("    Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows/Linux)")
        print("    → 'Reload Window'")
        print()
    else:
        print("  Some components could not be removed.")
        print("  Check the errors above for details.")
        print()


if __name__ == '__main__':
    main()
