"""
zTests Command Arguments

Defines CLI arguments for the 'ztests' command which runs
the zOS test suite.
"""

import argparse


def add_subparser(subparsers) -> argparse.ArgumentParser:
    """
    Add the 'ztests' subcommand to the parser.
    
    Args:
        subparsers: The subparsers object from ArgumentParser
        
    Returns:
        The created ztests subparser
    """
    parser = subparsers.add_parser(
        "ztests",
        help="Run zOS test suite",
        description="Execute the zOS testing framework with various test scenarios"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show bootstrap process and detailed initialization"
    )
    
    # Future test-specific arguments can be added here:
    # parser.add_argument("--suite", help="Specific test suite to run")
    # parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    # parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    
    return parser
