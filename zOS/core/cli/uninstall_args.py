"""
Uninstall Command Arguments

Defines CLI arguments for the 'uninstall' command which removes
zOS and optionally its dependencies and user data.
"""

import argparse


def add_subparser(subparsers) -> argparse.ArgumentParser:
    """
    Add the 'uninstall' subcommand to the parser.
    
    Args:
        subparsers: The subparsers object from ArgumentParser
        
    Returns:
        The created uninstall subparser
    """
    parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall zOS framework",
        description="Remove zOS framework and optionally clean user data"
    )
    
    # Mutually exclusive uninstall options
    uninstall_group = parser.add_mutually_exclusive_group()
    
    uninstall_group.add_argument(
        "--clean",
        action="store_true",
        help="Remove package AND user data"
    )
    
    uninstall_group.add_argument(
        "--dependencies",
        action="store_true",
        help="Remove dependencies"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show bootstrap process and detailed initialization"
    )
    
    return parser
