"""
Config Command Arguments

Defines CLI arguments for the 'config' command which displays
zMachine and zEnvironment configuration.
"""

import argparse


def add_subparser(subparsers) -> argparse.ArgumentParser:
    """
    Add the 'config' subcommand to the parser.
    
    Args:
        subparsers: The subparsers object from ArgumentParser
        
    Returns:
        The created config subparser
    """
    parser = subparsers.add_parser(
        "config",
        help="Display zMachine and zEnvironment configuration",
        description="Show system configuration including hardware, OS, and zOS settings"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show bootstrap process and detailed initialization"
    )
    
    return parser
