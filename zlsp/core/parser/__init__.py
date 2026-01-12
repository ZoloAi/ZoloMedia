"""
Zolo parser - Single source of truth for .zolo file parsing.
"""

from .parser import load, loads, dump, dumps, tokenize
from .type_hints import process_type_hints

__all__ = ["load", "loads", "dump", "dumps", "tokenize", "process_type_hints"]
