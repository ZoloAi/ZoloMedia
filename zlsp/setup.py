"""
Setup script for zolo package with post-install notification.

This is a minimal setup.py that wraps pyproject.toml and adds
a post-install message to notify users about the icon setup.
"""

from setuptools import setup
from setuptools.command.install import install
import sys


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    
    def run(self):
        install.run(self)
        
        # Show post-install message
        print("\n" + "=" * 70)
        print("🎉 zlsp installed successfully!")
        print("=" * 70)
        print("\n📚 Quick Start:")
        print("  # Install Vim integration:")
        print("  zolo-vim-install")
        print("\n  # Use in Python:")
        print("  import zlsp")
        print('  data = zlsp.loads("key: value")')
        print("\n📖 Documentation: https://github.com/ZoloAi/ZoloMedia/tree/main/zlsp")
        print("=" * 70 + "\n")


# Use pyproject.toml for all configuration, just add the custom command
setup(
    cmdclass={
        'install': PostInstallCommand,
    },
)
