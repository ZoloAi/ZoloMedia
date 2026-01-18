# zCLI/subsystems/zWizard/zWizard_modules/__init__.py
"""
zWizard Modules - Modular Components for zWizard Subsystem
===========================================================

This package contains the modular components that make up the zWizard subsystem.
The modules are organized for clarity, testability, and reusability.

Module Organization:
--------------------
1. **wizard_hat.py**: WizardHat triple-access container (numeric, key, attribute)
2. **wizard_interpolation.py**: zHat template variable interpolation ({{ zHat.key }})
3. **wizard_transactions.py**: Database transaction management (commit/rollback)
4. **wizard_rbac.py**: Role-based access control enforcement
5. **wizard_exceptions.py**: Custom exception hierarchy
6. **wizard_examples.py**: Comprehensive usage patterns and examples

Exported Components:
-------------------
### Classes
- WizardHat: Triple-access results container
- zWizardError: Base exception class
- WizardInitializationError: Initialization failures
- WizardExecutionError: Execution failures
- WizardRBACError: Access control violations

### Functions
- interpolate_zhat(): Template variable interpolation
- check_transaction_start(): Detect transaction start
- commit_transaction(): Commit active transaction
- rollback_transaction(): Rollback on error
- checkzRBAC_access(): Enforce RBAC before step execution
- display_access_denied(): Display access denial messages

Usage:
------
```python
from zOS.L3_Abstraction.m_zWizard.zWizard_modules import (
    WizardHat,
    interpolate_zhat,
    check_transaction_start,
    WizardInitializationError,
)

# Or import specific modules
from zOS.L3_Abstraction.m_zWizard.zWizard_modules import wizard_hat
from zOS.L3_Abstraction.m_zWizard.zWizard_modules import wizard_examples
```

Architecture:
------------
- **Layer**: 2 (Orchestration)
- **Position**: 2 (After zUtils, before zData/zShell)
- **Design**: Modular, testable, industry-grade
- **Refactored**: Phase 0 (v1.5.4 Week 6.14)

Version: v1.5.4 Week 6.14 Phase 3 (Polish)
"""

# Layer 0: Constants (Public API)
from .wizard_constants import (
    SUBSYSTEM_NAME,
    SUBSYSTEM_COLOR,
    NAVIGATION_SIGNALS,
    RBAC_ACCESS_GRANTED,
    RBAC_ACCESS_DENIED,
    RBAC_ACCESS_DENIED_ZGUEST,
    ERR_MISSING_INSTANCE,
)

# Layer 1: Core Components
from .wizard_hat import WizardHat
from .wizard_interpolation import interpolate_zhat
from .wizard_transactions import (
    check_transaction_start,
    commit_transaction,
    rollback_transaction,
)
from .wizard_rbac import checkzRBAC_access, display_access_denied
from .wizard_exceptions import (
    zWizardError,
    WizardInitializationError,
    WizardExecutionError,
    WizardRBACError,
)

__all__ = [
    # Public Constants
    "SUBSYSTEM_NAME",
    "SUBSYSTEM_COLOR",
    "NAVIGATION_SIGNALS",
    "RBAC_ACCESS_GRANTED",
    "RBAC_ACCESS_DENIED",
    "RBAC_ACCESS_DENIED_ZGUEST",
    "ERR_MISSING_INSTANCE",
    # Classes & Functions
    "WizardHat",
    "interpolate_zhat",
    "check_transaction_start",
    "commit_transaction",
    "rollback_transaction",
    "checkzRBAC_access",
    "display_access_denied",
    "zWizardError",
    "WizardInitializationError",
    "WizardExecutionError",
    "WizardRBACError",
]

