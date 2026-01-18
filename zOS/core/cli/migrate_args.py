"""
Migrate Command Arguments

Defines CLI arguments for the 'migrate' command which handles
schema migrations for zOS applications.
"""

import argparse


def add_subparser(subparsers) -> argparse.ArgumentParser:
    """
    Add the 'migrate' subcommand to the parser.
    
    Args:
        subparsers: The subparsers object from ArgumentParser
        
    Returns:
        The created migrate subparser
    """
    parser = subparsers.add_parser(
        "migrate",
        help="Run schema migrations for an application",
        description="Execute database schema migrations for zOS applications"
    )
    
    # Required positional argument
    parser.add_argument(
        "app_file",
        help="Path to application file (e.g., zTest.py or app.py)"
    )
    
    # Migration control arguments
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migrations without executing"
    )
    
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    parser.add_argument(
        "--schema",
        help="Migrate specific schema only"
    )
    
    parser.add_argument(
        "--version",
        help="Force specific version (e.g., v2.0.0)"
    )
    
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show migration history"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show bootstrap process and detailed initialization"
    )
    
    return parser
