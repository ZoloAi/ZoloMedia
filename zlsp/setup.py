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
        
        # Automatically install file type handler
        try:
            from zolo.install_handler import install as install_handler
            install_handler()
        except Exception as e:
            print(f"\n⚠️  Automatic file handler setup failed: {e}")
            print("💡 Run 'zolo-setup-icons' for manual setup\n")
        
        # Show post-install message
        print("\n" + "=" * 70)
        print("🎉 Zolo installed successfully!")
        print("=" * 70)
        print("\n📚 Quick Start:")
        print("  import zolo")
        print('  data = zolo.load("config.zolo")')
        print("\n📖 Documentation: https://github.com/ZoloAi/Zolo/tree/main/zLSP")
        print("=" * 70 + "\n")


# Use pyproject.toml for all configuration, just add the custom command
setup(
    cmdclass={
        'install': PostInstallCommand,
    },
)
