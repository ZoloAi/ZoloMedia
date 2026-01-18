"""
VS Code Integration Installer for zlsp

Fully automated installer that:
1. Generates extension files from canonical theme (themes/zolo_default.yaml)
2. Installs to VS Code extensions directory (~/.vscode/extensions/)
3. No manual configuration required
4. Everything "just works" for .zolo files

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
    Main installation function for VS Code.
    
    Returns:
        0 on success, 1 on failure
    """
    installer = VSCodeBasedInstaller(
        editor_name="VS Code",
        dir_name=".vscode",
        settings_name="Code",
        requires_registry=False  # VS Code doesn't need extensions.json
    )
    
    return installer.install()


if __name__ == '__main__':
    sys.exit(main())
