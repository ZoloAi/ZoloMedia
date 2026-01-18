"""
Vim Integration Uninstaller for zlsp

Cleanly removes all installed Vim files to allow fresh reinstallation.
"""
import sys
from pathlib import Path


def detect_editor():
    """Detect which editor to uninstall from."""
    nvim_dir = Path.home() / '.config' / 'nvim'
    vim_dir = Path.home() / '.vim'
    
    # Check if user has Neovim config
    if nvim_dir.exists():
        return 'neovim', nvim_dir
    
    # Default to Vim
    return 'vim', vim_dir


def uninstall_files(target_dir):
    """Remove all zlsp Vim plugin files."""
    files_to_remove = [
        target_dir / 'ftdetect' / 'zolo.vim',
        target_dir / 'ftplugin' / 'zolo.vim',
        target_dir / 'syntax' / 'zolo.vim',
        target_dir / 'indent' / 'zolo.vim',
        target_dir / 'plugin' / 'zolo_lsp.vim',
        target_dir / 'after' / 'ftplugin' / 'zolo.vim',
        target_dir / 'after' / 'syntax' / 'zolo.vim',
        target_dir / 'colors' / 'zolo_lsp.vim',
    ]
    
    removed = []
    not_found = []
    
    for file_path in files_to_remove:
        if file_path.exists():
            try:
                file_path.unlink()
                # Use relative path for cleaner display
                relative = file_path.relative_to(target_dir)
                removed.append(str(relative))
            except Exception as e:
                print(f"  ✗ Failed to remove {file_path}: {e}")
        else:
            relative = file_path.relative_to(target_dir)
            not_found.append(str(relative))
    
    return removed, not_found


def main():
    """Main uninstallation function."""
    print("═" * 70)
    print("  zlsp Vim Integration Uninstaller")
    print("═" * 70)
    print()
    
    # Detect editor
    editor_type, target_dir = detect_editor()
    
    print(f"→ Editor: {editor_type}")
    print(f"→ Target: {target_dir}")
    print()
    
    # Confirm uninstall
    print("⚠️  This will remove all zlsp Vim plugin files.")
    print()
    
    # Check if running in CI/automated mode
    if sys.stdin.isatty():
        response = input("Continue? [y/N]: ").strip().lower()
        if response not in ('y', 'yes'):
            print("\n✗ Uninstall cancelled.")
            sys.exit(0)
        print()
    else:
        # Non-interactive mode (CI/scripts) - proceed automatically
        print("Running in non-interactive mode - proceeding...")
        print()
    
    # Uninstall files
    print("Removing zlsp Vim files...")
    removed, not_found = uninstall_files(target_dir)
    
    if removed:
        print()
        print("Removed:")
        for f in removed:
            print(f"  ✓ {f}")
    
    if not_found:
        print()
        print("Not found (already removed):")
        for f in not_found:
            print(f"  ⊗ {f}")
    
    if not removed and not not_found:
        print("  ✓ No files found (nothing to remove)")
    
    print()
    print("═" * 70)
    print("  ✓ Uninstall Complete!")
    print("═" * 70)
    print()
    
    # Instructions
    print("📝 Next steps:")
    print()
    print("1. Restart Vim to clear all caches:")
    print("   • Close ALL Vim instances")
    print("   • Start fresh")
    print()
    print("2. Reinstall if needed:")
    print("   zlsp-vim-install")
    print()
    print("💡 Tip: This clears stale autocommands and cached syntax files.")
    print()


if __name__ == '__main__':
    main()
