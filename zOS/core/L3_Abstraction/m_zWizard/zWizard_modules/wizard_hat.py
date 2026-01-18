# zCLI/subsystems/zWizard/zWizard_modules/wizard_hat.py

"""
WizardHat - Triple-Access Wizard Results Container
===================================================

Supports numeric, key-based, and attribute-style access to wizard step results.

Features:
---------
- Numeric indexing: zHat[0], zHat[1], ... (backward compatible)
- Key-based access: zHat["step1"], zHat["fetch_cached"], ... (semantic)
- Attribute access: zHat.step1, zHat.fetch_cached, ... (convenient)
- Length checking: len(zHat)
- Containment checks: "step1" in zHat or 0 in zHat
- Debug representation: WizardHat(steps=2, keys=['step1', 'step2'])

Usage:
------
    >>> zHat = WizardHat()
    >>> zHat.add("fetch_data", {"files": [...]})
    >>> zHat.add("process", {"status": "done"})
    >>> 
    >>> # Access by position (backward compatible)
    >>> zHat[0]  # Returns: {"files": [...]}
    >>> 
    >>> # Access by step name (semantic)
    >>> zHat["fetch_data"]  # Returns: {"files": [...]}
    >>> zHat["process"]  # Returns: {"status": "done"}
    >>> 
    >>> # Access by attribute (convenient!)
    >>> zHat.fetch_data  # Returns: {"files": [...]}
    >>> zHat.process  # Returns: {"status": "done"}
    >>> 
    >>> # Check existence
    >>> "fetch_data" in zHat  # True
    >>> 2 in zHat  # False (only 2 steps)

Constants:
----------
- ERR_KEY_NOT_FOUND: Error message for missing keys
- ERR_INVALID_KEY_TYPE: Error message for invalid key types
- PRIVATE_LIST_KEY: Internal list storage key
- PRIVATE_DICT_KEY: Internal dict storage key

Layer: 2, Position: 2 (zWizard subsystem)
Week: 6.14
Version: v1.5.4 Phase 1 (Industry-Grade)
"""

from zOS import Any, Union

# Import constants from centralized file
from .wizard_constants import (
    _ERR_KEY_NOT_FOUND,
    _ERR_INVALID_KEY_TYPE,
    _PRIVATE_LIST_KEY,
    _PRIVATE_DICT_KEY,
)

__all__ = ["WizardHat"]


class WizardHat:
    """
    Triple-access wizard results container.
    
    Supports three access patterns:
    - Numeric indexing: zHat[0], zHat[1], ... (backward compatible)
    - Key-based access: zHat["step1"], zHat["fetch_cached"], ... (semantic)
    - Attribute access: zHat.step1, zHat.fetch_cached, ... (convenient)
    
    Example:
        >>> zHat = WizardHat()
        >>> zHat.add("fetch_data", {"files": [...]})
        >>> zHat[0]                    # Access by position
        >>> zHat["fetch_data"]         # Access by key (semantic)
        >>> zHat.fetch_data            # Access by attribute (convenient!)
    """
    
    def __init__(self):
        """Initialize dual-access container."""
        self._list: list = []   # For numeric access (backward compat)
        self._dict: dict = {}   # For key-based access (semantic)
    
    def add(self, key: str, value: Any) -> None:
        """
        Add result with both numeric and key-based access.
        
        Args:
            key: Step name (e.g., "step1", "fetch_cached")
            value: Step result
        """
        self._list.append(value)
        self._dict[key] = value
    
    def __getitem__(self, key: Union[int, str]) -> Any:
        """
        Support both zHat[0] and zHat["step1"].
        
        Args:
            key: Numeric index or string key
            
        Returns:
            Step result
            
        Raises:
            KeyError: If key is invalid
            IndexError: If numeric index is out of range
        """
        if isinstance(key, int):
            return self._list[key]
        elif isinstance(key, str):
            if key not in self._dict:
                raise KeyError(_ERR_KEY_NOT_FOUND % key)
            return self._dict[key]
        raise KeyError(_ERR_INVALID_KEY_TYPE % type(key))
    
    def __len__(self) -> int:
        """Return number of results."""
        return len(self._list)
    
    def __contains__(self, key: Union[int, str]) -> bool:
        """Check if key exists."""
        if isinstance(key, int):
            return 0 <= key < len(self._list)
        elif isinstance(key, str):
            return key in self._dict
        return False
    
    def __getattr__(self, name: str) -> Any:
        """
        Support attribute-style access: zHat.step1
        
        Args:
            name: Step name
            
        Returns:
            Step result
            
        Raises:
            AttributeError: If key is not found
        """
        # Avoid recursion for private attributes
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        # Try to get from dict
        if name in self._dict:
            return self._dict[name]
        
        raise AttributeError(_ERR_KEY_NOT_FOUND % name)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"WizardHat(steps={len(self._list)}, keys={list(self._dict.keys())})"


