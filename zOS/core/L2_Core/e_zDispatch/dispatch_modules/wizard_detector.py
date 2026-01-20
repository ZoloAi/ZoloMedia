# zOS/core/L2_Core/e_zDispatch/dispatch_modules/wizard_detector.py

"""
Wizard Detector Module for zDispatch Subsystem.

This module provides the WizardDetector class, which detects implicit wizard
patterns in command dicts. An implicit wizard is detected when a dict has
multiple non-metadata, non-subsystem keys.

Extracted from dispatch_launcher.py as part of Phase 3 refactoring.
This module has minimal dependencies - just pattern detection logic.

Detection Rules:
    A dict is considered an implicit wizard if:
    1. It has multiple content keys (non-metadata, non-subsystem)
    2. It's NOT a subsystem call (no zFunc, zDialog, etc.)
    3. It's NOT a CRUD call (no action, model, table)
    4. It's NOT purely organizational (not all nested dicts/lists)

Usage Example:
    detector = WizardDetector()
    
    # Check if dict is an implicit wizard
    is_wizard = detector.is_implicit_wizard(
        {'Step1': {...}, 'Step2': {...}},
        is_subsystem_call=False,
        is_crud_call=False
    )
    # Returns: True (multiple content keys)

Integration:
    - Used by dict_commands.py for command routing
    - No subsystem dependencies (pure pattern matching)

Thread Safety:
    - Stateless operations (no instance state)
    - Safe for concurrent execution
"""

from zOS import Any, Dict

class WizardDetector:
    """
    Detects implicit wizard patterns in command dicts.
    
    An implicit wizard is a dict with multiple content keys that should be
    executed as a multi-step workflow.
    
    Methods:
        is_implicit_wizard(): Main detection method
        count_content_keys(): Count non-metadata keys
    
    Example:
        detector = WizardDetector()
        
        # Implicit wizard (multiple steps)
        result = detector.is_implicit_wizard(
            {'Welcome': {...}, 'GetName': {...}, 'Confirm': {...}},
            is_subsystem_call=False,
            is_crud_call=False
        )
        # Returns: True
        
        # Not a wizard (single key)
        result = detector.is_implicit_wizard(
            {'zFunc': 'calculate'},
            is_subsystem_call=True,
            is_crud_call=False
        )
        # Returns: False
    """
    
    def is_implicit_wizard(
        self,
        zHorizontal: Dict[str, Any],
        is_subsystem_call: bool,
        is_crud_call: bool
    ) -> bool:
        """
        Detect if dict is an implicit wizard.
        
        Args:
            zHorizontal: Dict to check
            is_subsystem_call: Whether this is a subsystem call (zFunc, etc.)
            is_crud_call: Whether this is a CRUD call (action, model, etc.)
        
        Returns:
            True if implicit wizard detected, False otherwise
        
        Example:
            is_wizard = detector.is_implicit_wizard(
                {'Step1': {...}, 'Step2': {...}},
                is_subsystem_call=False,
                is_crud_call=False
            )
            # Returns: True
        
        Notes:
            - Requires multiple content keys (> 1)
            - Excludes subsystem and CRUD calls
            - Content keys are non-metadata (don't start with _)
        """
        content_keys = self.count_content_keys(zHorizontal)
        
        # Implicit wizard if multiple content keys and not subsystem/CRUD
        return (
            not is_subsystem_call and 
            not is_crud_call and 
            content_keys > 1
        )
    
    def count_content_keys(self, zHorizontal: Dict[str, Any]) -> int:
        """
        Count non-metadata keys in dict.
        
        Args:
            zHorizontal: Dict to count keys in
        
        Returns:
            Number of content keys (non-metadata)
        
        Example:
            count = detector.count_content_keys(
                {'_zClass': 'btn', 'Step1': {...}, 'Step2': {...}}
            )
            # Returns: 2 (Step1 and Step2, _zClass is metadata)
        
        Notes:
            - Metadata keys start with _
            - Content keys are everything else
        """
        return len([k for k in zHorizontal.keys() if not k.startswith('_')])
