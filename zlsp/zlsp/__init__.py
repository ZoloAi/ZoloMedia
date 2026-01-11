"""
zlsp: Language Server Protocol implementation for .zolo files

Provides LSP features for .zolo declarative files including:
- Parser for the .zolo file format (string-first, DRY, type-hinted)
- Syntax highlighting via semantic tokens
- Code completion
- Hover information
- Diagnostics

Parser Usage:
    from zlsp import load, loads, dump, dumps
    
    # Load from file
    data = load('config.zolo')
    
    # Load from string
    data = loads('key: value')
    
    # Dump to file
    dump(data, 'output.zolo')
    
    # Dump to string
    text = dumps(data)

Type Hints:
    port(int): 8080        # Integer
    price(float): 19.99    # Float
    enabled(bool): true    # Boolean
    id(str): 123           # Force string
    value(null):           # Null/None
"""

__version__ = "1.0.0"
__author__ = "Zolo.ai"
__license__ = "MIT"

from .parser import load, loads, dump, dumps
from .exceptions import ZoloParseError, ZoloTypeError, ZoloDumpError

__all__ = [
    # Parser API
    'load',
    'loads',
    'dump',
    'dumps',
    
    # Exceptions
    'ZoloParseError',
    'ZoloTypeError',
    'ZoloDumpError',
    
    # Metadata
    '__version__',
]
