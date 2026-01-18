#!/usr/bin/env python3
"""
setup.py for zOS - Enables smart monorepo dependency resolution

This setup.py works alongside pyproject.toml to provide industry-standard
monorepo dependency management:

- Local development (-e): Automatically installs zlsp in editable mode
- PyPI install: Uses zlsp from PyPI  
- Standard install: Uses zlsp from PyPI

This is the industry-standard approach used by large Python monorepos.
"""

import os
import subprocess
import sys
from pathlib import Path
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.egg_info import egg_info


class PostDevelopCommand(develop):
    """Post-installation for editable/development mode."""
    
    def run(self):
        # Run the standard develop command first
        develop.run(self)
        
        # Check if we're in a monorepo with zlsp available locally
        zlsp_path = Path(__file__).parent.parent / "zlsp"
        
        if zlsp_path.exists() and (zlsp_path / "pyproject.toml").exists():
            print("\n" + "="*70)
            print("🔗 Monorepo detected! Installing zlsp in editable mode...")
            print("="*70)
            
            try:
                # Install zlsp in editable mode
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-e", str(zlsp_path)
                ])
                print("\n✅ zlsp installed in editable mode from monorepo!")
            except subprocess.CalledProcessError as e:
                print(f"\n⚠️  Warning: Could not install zlsp in editable mode: {e}")
                print("    Falling back to PyPI install...")
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", "zlsp>=1.0.0"
                    ])
                except:
                    print("    ❌ Failed to install zlsp from PyPI")
        else:
            # Not in monorepo, install from PyPI
            print("\n📦 Installing zlsp from PyPI...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "zlsp>=1.0.0"
                ])
                print("✅ zlsp installed from PyPI!")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Warning: Could not install zlsp: {e}")


class PostInstallCommand(install):
    """Post-installation for standard install mode."""
    
    def run(self):
        # Run the standard install command first
        install.run(self)
        
        # For standard installs, always use PyPI
        print("\n📦 Installing zlsp from PyPI...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "zlsp>=1.0.0"
            ])
            print("✅ zlsp installed from PyPI!")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Could not install zlsp: {e}")


# Use setup() from setuptools to leverage pyproject.toml
# but add our custom commands for intelligent dependency handling
setup(
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
)
