#!/usr/bin/env python3
"""
Development Installation Script for Zolo Monorepo

This script handles editable (-e) installations of all ZoloMedia packages
in the correct dependency order.

WHY THIS EXISTS:
Python's pip cannot automatically install local monorepo dependencies in
editable mode. This script ensures proper installation order and uses
--no-cache-dir to avoid stale cached wheels.

DEPENDENCY ORDER (critical!):
1. zlsp    (no dependencies)
2. zOS     (depends on zlsp)
3. (future packages will be added here)

Usage:
    python install-dev.py              # Install all packages (recommended)
    python install-dev.py --zlsp-only  # Install only zlsp
    python install-dev.py --zos-only   # Install only zOS
"""

import subprocess
import sys
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def install_package(name, path):
    """Install a package in editable mode with --no-cache-dir."""
    print_info(f"Installing {name} in editable mode from {path}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-e", str(path), "--no-cache-dir"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        print_success(f"{name} installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install {name}")
        print(e.output.decode() if e.output else str(e))
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Install Zolo packages in development mode")
    parser.add_argument("--zos-only", action="store_true", help="Install only zOS")
    parser.add_argument("--zlsp-only", action="store_true", help="Install only zlsp")
    args = parser.parse_args()

    print_header("🚀 Zolo Monorepo - Development Installation")

    # Get the monorepo root (where this script is located)
    monorepo_root = Path(__file__).parent.resolve()
    zos_path = monorepo_root / "zOS"
    zlsp_path = monorepo_root / "zlsp"

    # Verify packages exist
    if not zos_path.exists():
        print_error(f"zOS package not found at {zos_path}")
        sys.exit(1)
    if not zlsp_path.exists():
        print_error(f"zlsp package not found at {zlsp_path}")
        sys.exit(1)

    success = True

    # Install packages based on flags
    if args.zlsp_only:
        success = install_package("zlsp", zlsp_path)
    elif args.zos_only:
        success = install_package("zOS", zos_path)
    else:
        # Install both (default) - ORDER MATTERS!
        print_info("Installing both packages in dependency order...")
        print()
        
        # Install zlsp FIRST (zOS depends on it for .zolo file parsing)
        if install_package("zlsp", zlsp_path):
            print()
            # Then install zOS (will use the local editable zlsp we just installed)
            success = install_package("zOS", zos_path)
        else:
            success = False

    print()
    if success:
        print_header("✅ Installation Complete!")
        print_info("Your development environment is ready!")
        print()
        print("📝 What this means:")
        print("   • Edit zOS/core/*.py → changes take effect immediately")
        print("   • Edit zlsp/core/*.py → changes take effect immediately")
        print("   • No need to reinstall after code changes")
        print()
        print("🧪 Test your installation:")
        print("   zolo --version")
        print("   zlsp info")
        print()
        print("📚 Learn more:")
        print("   cd zOS && cat README.md")
        print("   cd zlsp && cat README.md")
        print()
    else:
        print_header("❌ Installation Failed")
        print_error("Some packages failed to install. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
