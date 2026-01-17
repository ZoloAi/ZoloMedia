"""
Editor integrations for zlsp.

Each editor has its own subfolder with installation scripts and configuration.
"""
import sys


def install_all():
    """Install zlsp for all supported editors."""
    from editors.vim.install import main as vim_install
    from editors.vscode.install import main as vscode_install
    from editors.cursor.install import main as cursor_install
    
    print("Installing zlsp for all supported editors...\n")
    
    editors = [
        ("Vim", vim_install),
        ("VSCode", vscode_install),
        ("Cursor", cursor_install),
    ]
    
    results = {}
    for name, install_func in editors:
        print(f"\n{'='*60}")
        print(f"Installing for {name}...")
        print('='*60)
        try:
            exit_code = install_func()
            results[name] = exit_code == 0
        except Exception as e:
            print(f"✗ Error installing for {name}: {e}")
            results[name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("Installation Summary:")
    print('='*60)
    for name, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        print(f"  {name}: {status}")
    
    # Exit with non-zero if any failed
    if not all(results.values()):
        sys.exit(1)
    print("\n✓ All installations completed successfully!")
    sys.exit(0)


def uninstall_all():
    """Uninstall zlsp from all supported editors."""
    from editors.vim.uninstall import main as vim_uninstall
    from editors.vscode.uninstall import main as vscode_uninstall
    from editors.cursor.uninstall import main as cursor_uninstall
    
    print("Uninstalling zlsp from all supported editors...\n")
    
    editors = [
        ("Vim", vim_uninstall),
        ("VSCode", vscode_uninstall),
        ("Cursor", cursor_uninstall),
    ]
    
    results = {}
    for name, uninstall_func in editors:
        print(f"\n{'='*60}")
        print(f"Uninstalling from {name}...")
        print('='*60)
        try:
            exit_code = uninstall_func()
            results[name] = exit_code == 0
        except Exception as e:
            print(f"✗ Error uninstalling from {name}: {e}")
            results[name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("Uninstallation Summary:")
    print('='*60)
    for name, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        print(f"  {name}: {status}")
    
    # Exit with non-zero if any failed
    if not all(results.values()):
        sys.exit(1)
    print("\n✓ All uninstallations completed successfully!")
    sys.exit(0)
