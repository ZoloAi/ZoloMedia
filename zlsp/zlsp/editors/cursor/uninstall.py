"""
Cursor IDE Integration Uninstaller for zlsp

Removes:
1. Extension directory from ~/.cursor/extensions/
2. Semantic token color customizations from settings.json

Provides complete cleanup beyond Cursor's UI uninstall.
"""
import json
import shutil
import sys
from pathlib import Path
import glob

try:
    from core.version import __version__
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.version import __version__


def get_cursor_user_settings_path():
    """Get path to Cursor's settings.json."""
    import os
    system = os.uname().sysname if hasattr(os, 'uname') else os.name
    
    if system == 'Darwin':  # macOS
        return Path.home() / 'Library' / 'Application Support' / 'Cursor' / 'User' / 'settings.json'
    elif system == 'Linux':
        return Path.home() / '.config' / 'Cursor' / 'User' / 'settings.json'
    elif system in ('Windows', 'nt'):
        appdata = os.getenv('APPDATA')
        if appdata:
            return Path(appdata) / 'Cursor' / 'User' / 'settings.json'
        else:
            return Path.home() / 'AppData' / 'Roaming' / 'Cursor' / 'User' / 'settings.json'
    else:
        return Path.home() / '.config' / 'Cursor' / 'User' / 'settings.json'


def create_settings_backup(settings_path):
    """Create a timestamped backup of settings.json."""
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = settings_path.with_suffix(f'.json.backup_{timestamp}')
    shutil.copy(settings_path, backup_path)
    return backup_path


def remove_semantic_token_colors_from_settings(settings_path):
    """
    Remove Zolo semantic token colors from settings.json.
    
    Only removes the "[zolo]" section, leaving other customizations intact.
    """
    if not settings_path.exists():
        return False
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️  Warning: {settings_path} is not valid JSON, skipping cleanup")
        return False
    
    # Check if Zolo settings exist
    if "editor.semanticTokenColorCustomizations" not in settings:
        return False
    
    if "[zolo]" not in settings["editor.semanticTokenColorCustomizations"]:
        return False
    
    # Create backup before modifying
    backup_path = create_settings_backup(settings_path)
    print(f"✓ Created backup: {backup_path}")
    
    # Remove [zolo] section
    del settings["editor.semanticTokenColorCustomizations"]["[zolo]"]
    
    # If semanticTokenColorCustomizations is now empty, remove it entirely
    if not settings["editor.semanticTokenColorCustomizations"]:
        del settings["editor.semanticTokenColorCustomizations"]
    
    # Write back
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)
    
    return True


def main():
    """
    Uninstall Zolo Language Support extension from Cursor.
    
    Performs complete cleanup:
    1. Removes extension directory
    2. Cleans up settings.json
    """
    print("=" * 70)
    print("Cursor IDE Integration Uninstaller for zlsp")
    print("=" * 70)
    print()
    
    # Step 1: Find and remove extension directory
    print("[1/2] Checking for installed extension...")
    cursor_extensions = Path.home() / '.cursor' / 'extensions'
    
    if not cursor_extensions.exists():
        print("✓ No Cursor extensions directory found")
        ext_found = False
    else:
        # Find zolo-lsp-* extension
        zolo_extensions = list(cursor_extensions.glob('zolo-lsp-*'))
        
        if not zolo_extensions:
            print("✓ No Zolo extension found in Cursor")
            ext_found = False
        else:
            ext_found = True
            print(f"✓ Found {len(zolo_extensions)} Zolo extension(s):")
            for ext in zolo_extensions:
                print(f"   {ext.name}")
    
    # Step 2: Check for settings
    print("\n[2/2] Checking for Zolo settings...")
    settings_path = get_cursor_user_settings_path()
    settings_found = False
    
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            if ("editor.semanticTokenColorCustomizations" in settings and 
                "[zolo]" in settings["editor.semanticTokenColorCustomizations"]):
                settings_found = True
                print(f"✓ Found Zolo settings in: {settings_path}")
        except:
            pass
    
    if not settings_found:
        print("✓ No Zolo settings found")
    
    # If nothing to remove, we're done
    if not ext_found and not settings_found:
        print("\n" + "=" * 70)
        print("✓ Zolo Language Support is not installed in Cursor")
        print("=" * 70)
        return 0
    
    # Confirm with user
    print("\n" + "⚠️  " + "=" * 66)
    print("About to remove:")
    if ext_found:
        print("  • Extension directory (with all files)")
    if settings_found:
        print("  • Semantic token color settings (with backup)")
    print("=" * 70)
    print()
    
    response = input("Proceed with uninstall? [y/N]: ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return 0
    
    # Perform removal
    print()
    
    # Remove extension directory
    if ext_found:
        print("Removing extension directory...")
        for ext in zolo_extensions:
            try:
                shutil.rmtree(ext)
                print(f"✓ Removed: {ext}")
            except Exception as e:
                print(f"✗ Error removing {ext}: {e}")
    
    # Remove settings
    if settings_found:
        print("Removing Zolo settings...")
        if remove_semantic_token_colors_from_settings(settings_path):
            print(f"✓ Cleaned up: {settings_path}")
        else:
            print(f"⚠️  Could not clean up settings (backup created)")
    
    # Success
    print("\n" + "=" * 70)
    print("✓ Uninstall complete!")
    print("=" * 70)
    print()
    print("🚀 Next steps:")
    print("   1. Reload Cursor: Cmd+Shift+P > 'Reload Window'")
    print("   2. Zolo Language Support is now fully removed")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
