# zSys/formatting/__init__.py
"""
Terminal formatting utilities for zKernel.

This module provides color codes and terminal output utilities used throughout
the framework, especially during pre-boot initialization.
"""

from .colors import Colors
from .terminal import print_ready_message

__all__ = [
    "Colors",
    "print_ready_message",
]

