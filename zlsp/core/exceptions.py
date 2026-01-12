"""
Zolo Exception Classes

Defines custom exceptions for the Zolo parser.
"""


class ZoloError(Exception):
    """Base exception for all Zolo errors."""
    pass


class ZoloParseError(ZoloError):
    """Raised when parsing a Zolo file fails."""
    pass


class ZoloTypeError(ZoloError):
    """Raised when type conversion fails."""
    pass


class ZoloDumpError(ZoloError):
    """Raised when dumping data to Zolo format fails."""
    pass
