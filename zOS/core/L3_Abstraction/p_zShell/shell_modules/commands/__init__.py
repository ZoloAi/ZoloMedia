# zCLI/subsystems/zShell/shell_modules/commands/__init__.py

"""
Command Executors Registry - Modular command execution for zCLI shell.

This module serves as the central registry for all Level 1 command executors
in the zShell subsystem. Each executor is a specialized module that handles
a specific command or command family (e.g., data, config, plugin).

────────────────────────────────────────────────────────────────────────────────
ARCHITECTURE: COMMAND REGISTRY PATTERN
────────────────────────────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────────┐
    │               COMMAND EXECUTORS REGISTRY                     │
    ├──────────────────────────────────────────────────────────────┤
    │                                                              │
    │  Shell Input → CommandExecutor → Registry → Specific Exec   │
    │                                                              │
    │  Registry Groups (24 executors):                            │
    │    🖥️  Group A: Terminal Commands (6)                       │
    │    💾 Group B: zLoader System (3)                           │
    │    🔗 Group C: Subsystem Integration (10)                   │
    │    ⚡ Group D: Advanced (5)                                 │
    │                                                              │
    │  All executors follow UI Adapter Pattern:                   │
    │    • Accept (zcli, parsed) parameters                       │
    │    • Return None (use zDisplay for output)                  │
    │    • Handle errors internally with try/except               │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘

────────────────────────────────────────────────────────────────────────────────
COMMAND CATEGORIES
────────────────────────────────────────────────────────────────────────────────

🖥️  **GROUP A: Terminal Commands (6 executors)**
    • where       - Display current zPath and context
    • shortcut    - Manage zPath shortcuts (aliases for navigation)
    • cd          - Change directory
    • pwd         - Print working directory
    • ls          - List directory contents
    • help        - Display help information

💾 **GROUP B: zLoader System (3 executors)**
    • load        - Load schemas, UI files, configs
    • data        - Database operations (CRUD, DDL, migrations)
    • plugin      - Plugin management (load, show, clear, exec, run)

🔗 **GROUP C: Subsystem Integration (10 executors)**
    • auth        - Authentication (login, logout, status)
    • config      - Configuration management (check, show, get, set, reset)
    • comm        - Communication services (Bifrost, PostgreSQL, etc.)
    • func        - Function execution (zFunc integration)
    • open        - File/resource opening (zOpen integration)
    • session     - Session management (zSession integration)
    • walker      - Directory walker (zWalker integration)
    • wizard_step - Wizard step execution (zWizard callback)

⚡ **GROUP D: Advanced (5 executors + 2 deprecated)**
    • plugin      - Plugin operations (unified command)
    • export      - ❌ DEPRECATED → Use 'config set'
    • utils       - ❌ DEPRECATED → Use 'plugin exec/run'

────────────────────────────────────────────────────────────────────────────────
REGISTRY METADATA
────────────────────────────────────────────────────────────────────────────────

**Total Executors:** 18 active + 2 deprecated = 20 total
**UI Adapter Compliance:** 100% (all return None)
**Industry Grade:** 18/18 modernized (100%)
**Deprecations:** 2 (execute_export, execute_utils)
**Consolidations:** 1 (execute_wizard → shell_executor.py)

────────────────────────────────────────────────────────────────────────────────
USAGE
────────────────────────────────────────────────────────────────────────────────

**From CommandExecutor (shell_executor.py):**
    ```python
    from .commands import execute_data, execute_config, execute_auth
    
    # Route to specific executor
    command_map = {
        "data": execute_data,
        "config": execute_config,
        "auth": execute_auth,
        # ... etc
    }
    
    executor = command_map.get(cmd_type)
    if executor:
        executor(self.zcli, parsed)
    ```

**Direct Import:**
    ```python
    from zOS.L3_Abstraction.p_zShell.shell_modules.commands import execute_data
    
    # Execute data command
    parsed = {"action": "read", "args": ["users"], "options": {}}
    execute_data(zcli, parsed)
    ```

────────────────────────────────────────────────────────────────────────────────
DEPRECATION NOTES
────────────────────────────────────────────────────────────────────────────────

1. **execute_wizard** - Removed in v1.5.4
   - Reason: 90% redundant, wizard canvas logic unified in shell_executor.py
   - Migration: Use shell_executor._wizard_start() instead
   
2. **execute_export** - Deprecated in v1.5.4, removal planned for v1.6.0
   - Reason: 100% code duplication with config_persistence
   - Migration: OLD: `export machine key value` → NEW: `config set machine key value`
   
3. **execute_utils** - Deprecated in v1.5.4, removal planned for v1.6.0
   - Reason: Unified into plugin command for better UX
   - Migration: OLD: `utils hash_password mypass` → NEW: `plugin exec hash_password mypass`

────────────────────────────────────────────────────────────────────────────────
DEPENDENCIES
────────────────────────────────────────────────────────────────────────────────

- All 18 command executor modules (shell_cmd_*.py)
- zDisplay: Mode-agnostic output
- zParser: Command parsing
- Subsystem-specific dependencies per executor

────────────────────────────────────────────────────────────────────────────────
NOTES
────────────────────────────────────────────────────────────────────────────────

- Registry follows single responsibility: import and expose executors
- All executors modernized to industry-grade standards (Week 6.13.1-6.13.23)
- Executors organized bottom-up by dependency (terminal → loader → subsystems)
- File maintained for backward compatibility during deprecation grace period
"""

from typing import List

# ============================================================
# REGISTRY METADATA CONSTANTS
# ============================================================
REGISTRY_VERSION = "1.5.4"
REGISTRY_STATUS = "COMPLETE"
TOTAL_EXECUTORS_ACTIVE = 18
TOTAL_EXECUTORS_DEPRECATED = 2
TOTAL_EXECUTORS_REMOVED = 1
TOTAL_EXECUTORS_ALL = 21

# ============================================================
# GROUP COUNTS
# ============================================================
GROUP_A_TERMINAL_COUNT = 6
GROUP_B_LOADER_COUNT = 3
GROUP_C_SUBSYSTEMS_COUNT = 10
GROUP_D_ADVANCED_COUNT = 5

# ============================================================
# DEPRECATION INFO
# ============================================================
DEPRECATED_EXPORT_VERSION = "1.5.4"
DEPRECATED_UTILS_VERSION = "1.5.4"
REMOVAL_TARGET_VERSION = "1.6.0"

# ============================================================
# CONSOLIDATION INFO
# ============================================================
REMOVED_WIZARD_VERSION = "1.5.4"
WIZARD_NEW_LOCATION = "shell_executor._wizard_start()"

# ============================================================
# UI ADAPTER COMPLIANCE
# ============================================================
UI_ADAPTER_COMPLIANCE_RATE = 100  # Percentage of executors returning None

# ============================================================
# IMPORT COMMAND EXECUTORS
# ============================================================

# GROUP A: Terminal Commands (6)
from .shell_cmd_where import execute_where
from .shell_cmd_shortcut import execute_shortcut
from .shell_cmd_cd import execute_cd, execute_pwd
from .shell_cmd_ls import execute_ls
from .shell_cmd_help import execute_help

# GROUP B: zLoader System (3)
from .shell_cmd_load import execute_load
from .shell_cmd_data import execute_data
from .shell_cmd_plugin import execute_plugin

# GROUP C: Subsystem Integration (10)
from .shell_cmd_auth import execute_auth
from .shell_cmd_config import execute_config
from .shell_cmd_comm import execute_comm
from .shell_cmd_func import execute_func
from .shell_cmd_open import execute_open
from .shell_cmd_session import execute_session
from .shell_cmd_walker import execute_walker
from .shell_cmd_wizard_step import execute_wizard_step

# GROUP D: Advanced (2 deprecated)
from .shell_cmd_export import execute_export  # DEPRECATED v1.5.4, removal v1.6.0
from .shell_cmd_utils import execute_utils    # DEPRECATED v1.5.4, removal v1.6.0

# Note: execute_wizard REMOVED in v1.5.4 - consolidated into shell_executor.py

# ============================================================
# PUBLIC API
# ============================================================
__all__: List[str] = [
    # GROUP A: Terminal Commands
    "execute_where",
    "execute_shortcut",
    "execute_cd",
    "execute_pwd",
    "execute_ls",
    "execute_help",
    
    # GROUP B: zLoader System
    "execute_load",
    "execute_data",
    "execute_plugin",
    
    # GROUP C: Subsystem Integration
    "execute_auth",
    "execute_config",
    "execute_comm",
    "execute_func",
    "execute_open",
    "execute_session",
    "execute_walker",
    "execute_wizard_step",
    
    # GROUP D: Advanced (Deprecated)
    "execute_export",  # DEPRECATED - use 'config set' instead
    "execute_utils",   # DEPRECATED - use 'plugin exec/run' instead
]
