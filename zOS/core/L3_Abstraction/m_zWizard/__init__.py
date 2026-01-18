# zCLI/subsystems/zWizard/__init__.py
"""
zWizard - Core Loop Engine for Stepped Execution

PURPOSE:
  Generic loop engine for executing sequential steps (zBlocks) with transaction
  support. Powers Shell canvas mode, Walker UI navigation, and batch data operations.

FEATURES:
  - Sequential step execution with error handling
  - Transaction management via schema_cache
  - zHat result interpolation for dependent steps
  - Navigation callbacks for flow control
  
MODES:
  - Shell Mode: YAML workflows with transaction support
  - Walker Mode: UI navigation and menu systems
  
ARCHITECTURE:
  zWizard is a pure loop engine. Shell-specific execution logic lives in
  zShell/zShell_modules/executor_commands/wizard_step_executor.py
"""

from .zWizard import zWizard  # noqa: F401

__all__ = ['zWizard']

