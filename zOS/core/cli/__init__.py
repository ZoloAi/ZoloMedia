"""
CLI Argument Parser for zOS Framework

This module provides a modular CLI argument parsing system where each
command group is defined in its own file for better maintainability.

Structure:
    cli/
        __init__.py          - Main parser factory (this file)
        shell_args.py        - Shell command arguments
        config_args.py       - Config command arguments
        ztests_args.py       - zTests command arguments
        migrate_args.py      - Migrate command arguments
        uninstall_args.py    - Uninstall command arguments
        
Usage:
    from cli import create_parser
    parser = create_parser()
    args = parser.parse_args()
"""

import argparse
from typing import Optional

# Import command modules
from . import shell_args
from . import config_args
from . import ztests_args
from . import migrate_args
from . import uninstall_args


def create_parser(version: str) -> argparse.ArgumentParser:
    """
    Create and configure the main argument parser for zOS.
    
    Args:
        version: Version string to display (e.g., "1.5.8")
        
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Zolo zOS Framework - YAML-driven CLI for interactive applications",
        prog="zolo",
    )
    
    # Global arguments
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"zOS {version}"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Show bootstrap process and detailed initialization"
    )
    parser.add_argument(
        "--dev", 
        action="store_true",
        help="Enable Development mode (show framework banners and internal flow)"
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command", 
        help="Available commands"
    )
    
    # Add each command's subparser
    shell_args.add_subparser(subparsers)
    config_args.add_subparser(subparsers)
    ztests_args.add_subparser(subparsers)
    migrate_args.add_subparser(subparsers)
    uninstall_args.add_subparser(subparsers)
    
    return parser


__all__ = ["create_parser"]
