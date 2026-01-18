"""
Shell Command Arguments

Defines CLI arguments for the 'shell' command which starts
the interactive zOS shell.
"""

import argparse


def add_subparser(subparsers) -> argparse.ArgumentParser:
    """
    Add the 'shell' subcommand to the parser.
    
    Args:
        subparsers: The subparsers object from ArgumentParser
        
    Returns:
        The created shell subparser
    """
    parser = subparsers.add_parser(
        "shell",
        help="Start interactive zOS shell",
        description="Launch the interactive zOS shell for running commands and workflows"
    )
    
    parser.add_argument(
        "--config",
        help="Path to custom config file (optional)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show bootstrap process and detailed initialization"
    )
    
    return parser
