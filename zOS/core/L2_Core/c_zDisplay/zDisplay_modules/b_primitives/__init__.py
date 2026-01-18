# zCLI/L2_Core/c_zDisplay/zDisplay_modules/b_primitives/__init__.py

"""
Tier 1 Primitives - Display Utilities & I/O
============================================

Public API for primitive utilities used by display events.
"""

from .display_utilities import ActiveStateManager, format_time_duration
from .display_primitives import zPrimitives
from .display_semantic_primitives import SemanticPrimitives

__all__ = [
    'ActiveStateManager',
    'format_time_duration',
    'zPrimitives',
    'SemanticPrimitives'
]

