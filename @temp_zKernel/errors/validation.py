# @temp_zKernel/errors/validation.py
"""
Runtime validation utilities for zKernel subsystems.

ORIGIN: zOS/errors/validation.py
STATUS: Staging for merge when zKernel joins monorepo
ACTION: DO NOT touch ~/Projects/Zolo/zKernel directly

This file contains framework-level validation logic for zKernel subsystems.
It validates that subsystems are properly initialized with a zKernel instance.

This is framework-level logic, NOT OS primitives.

TO MERGE LATER:
- Copy this file → ~/Projects/Zolo/zKernel/errors/validation.py (when copying zKernel to monorepo)
"""

def validate_zkernel_instance(zcli, subsystem_name, require_session=True):
    """Validate zKernel instance is properly initialized (catches init order issues early)."""
    if zcli is None:
        raise ValueError(
            f"{subsystem_name} received None for zKernel instance. "
            f"This indicates an initialization order issue - subsystems must be "
            f"initialized with a valid zKernel instance."
        )

    if require_session and not hasattr(zcli, 'session'):
        raise ValueError(
            f"{subsystem_name} requires zKernel instance with 'session' attribute. "
            f"Ensure zKernel is fully initialized before creating {subsystem_name}."
        )
