"""
VS Code Integration Uninstaller for zlsp

Removes the zlsp VS Code extension.
"""
import shutil
import sys
from pathlib import Path

try:
    from core.version import __version__
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.version import __version__


def main():
    """Uninstall the VS Code extension."""
    print("═" * 70)
    print("  zlsp VS Code Extension Uninstaller")
    print("═" * 70)
    print()
    
    # Detect extensions directory
    extensions_dir = Path.home() / '.vscode' / 'extensions'
    extension_dir = extensions_dir / f'zolo-lsp-{__version__}'
    
    if not extension_dir.exists():
        print(f"  ℹ Extension not found: {extension_dir}")
        print(f"    Nothing to uninstall.")
        print()
        return
    
    print(f"  Found extension: {extension_dir}")
    print()
    
    # Confirm uninstallation
    try:
        response = input("  Uninstall? (y/N): ").strip().lower()
        if response != 'y':
            print("  Cancelled.")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return
    
    print()
    print(f"  Removing {extension_dir}...")
    
    try:
        shutil.rmtree(extension_dir)
        print(f"  ✓ Extension removed")
    except Exception as e:
        print(f"  ✗ Failed to remove extension: {e}")
        sys.exit(1)
    
    print()
    print("═" * 70)
    print("  ✓ Uninstallation Complete!")
    print("═" * 70)
    print()
    print("  Reload VS Code to complete uninstallation:")
    print("    Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows/Linux)")
    print("    → 'Reload Window'")
    print()


if __name__ == '__main__':
    main()
