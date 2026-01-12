"""
zlsp - Python SDK for Zolo Language Server Protocol

This package provides Python bindings to the core zlsp implementation.
"""

# Import from core (using relative imports from package root)
from core.parser import load, loads, dump, dumps
from core.parser.type_hints import TypeHint
from core.exceptions import ZoloParseError, ZoloTypeError

__version__ = "1.0.0"
__all__ = ["load", "loads", "dump", "dumps", "TypeHint", "ZoloParseError", "ZoloTypeError"]
