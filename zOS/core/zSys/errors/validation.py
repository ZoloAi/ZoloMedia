# zSys/errors/validation.py
"""Runtime validation utilities for zCLI subsystems."""

def validate_zcli_instance(zcli, subsystem_name, require_session=True):
    """Validate zCLI instance is properly initialized (catches init order issues early)."""
    if zcli is None:
        raise ValueError(
            f"{subsystem_name} received None for zCLI instance. "
            f"This indicates an initialization order issue - subsystems must be "
            f"initialized with a valid zCLI instance."
        )

    if require_session and not hasattr(zcli, 'session'):
        raise ValueError(
            f"{subsystem_name} requires zCLI instance with 'session' attribute. "
            f"Ensure zCLI is fully initialized before creating {subsystem_name}."
        )
