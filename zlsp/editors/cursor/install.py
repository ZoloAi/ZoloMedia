"""
Cursor IDE Integration Installer for zlsp

Fully automated installer that:
1. Generates extension files from canonical theme (themes/zolo_default.yaml)
2. Installs to Cursor extensions directory (~/.cursor/extensions/)
3. No manual configuration required
4. Everything "just works" for .zolo files

Note: Cursor IDE is a VS Code fork, so we use the same extension format!

This is a thin wrapper around the shared VSCodeBasedInstaller.
"""

import sys
from pathlib import Path

# Import shared base installer
try:
    from editors._shared import VSCodeBasedInstaller
except ImportError:
    # Fallback if running from different context
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from editors._shared import VSCodeBasedInstaller


def main():
    """
    Main installation function for Cursor IDE.
    
    Returns:
        0 on success, 1 on failure
    """
    installer = VSCodeBasedInstaller(
        editor_name="Cursor",
        dir_name=".cursor",
        settings_name="Cursor",
        requires_registry=True  # Cursor requires extensions.json registry
    )
    
    return installer.install()


if __name__ == '__main__':
    sys.exit(main())
