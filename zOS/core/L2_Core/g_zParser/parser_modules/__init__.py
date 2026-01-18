# zCLI/subsystems/zParser/parser_modules/__init__.py

"""
Parser modules package - specialized parsing functionality for zCLI.

This package provides comprehensive parsing capabilities for the zCLI framework,
organized into specialized modules following a bottom-up dependency architecture.
Each module handles a specific aspect of parsing, from path resolution to command
parsing to file content parsing.

Architecture Overview:
    The parser_modules package follows a three-tier architecture:
    
    **Tier 1 - Foundation (Core Utilities)**:
        - parser_utils: Core parsing utilities (expressions, dotted paths, references)
        - parser_path: Path resolution and zFile identification
    
    **Tier 2 - Specialized Parsers**:
        - parser_commands: Command string parsing (20+ command types)
        - parser_plugin: Plugin invocation resolution
        - parser_file: File content parsing (YAML, JSON, auto-detection)
        - vafile/ package: zVaFile parsing (UI, Schema, Config, Generic)
    
    **Tier 3 - Aggregation**:
        - This __init__.py: Public API aggregation and exposure

Module Breakdown:

    **parser_utils.py** (Foundation):
        Core parsing utilities for expressions, paths, and references.
        - zExpr_eval: JSON expression evaluation
        - parse_dotted_path: Dotted path parsing (e.g., "user.name")
        - handle_zRef: zRef expression handling (YAML references)
        - handle_zParser: Parser directive handling
        
        Used by: navigation_linking, multiple subsystems
        Complexity: Medium (expression evaluation, regex parsing)
    
    **parser_path.py** (Foundation):
        Path resolution and file type identification for zMachine paths.
        - zPath_decoder: Resolves zMachine.* paths to OS-specific paths
        - identify_zFile: Identifies zUI/zSchema/zConfig file types
        
        Used by: zLoader, zShell, multiple subsystems
        Complexity: High (OS-specific, multiple path formats)
    
    **parser_commands.py** (Specialized):
        Command string parsing for 20+ command types (zFunc, zLink, zOpen, etc.).
        - parse_command: Main command parser (string → structured dict)
        
        Used by: zShell_executor, wizard_step_executor
        Complexity: Very High (20 command types, quote handling, arguments)
    
    **parser_plugin.py** (Specialized):
        Plugin invocation resolution with caching and async support.
        - is_plugin_invocation: Check if string is plugin invocation
        - resolve_plugin_invocation: Resolve &Plugin.function(args) calls
        
        Used by: dispatch_launcher
        Complexity: High (caching, async, auto-injection)
    
    **parser_file.py** (Specialized):
        File content parsing (YAML, JSON) with RBAC transformation for UI files.
        - parse_file_content: Main file parser (CRITICAL - 6 external usages)
        - parse_yaml: YAML-specific parsing
        - parse_json: JSON-specific parsing
        - detect_format: Auto-detect file format
        - parse_file_by_path: Convenience method (load + parse)
        - parse_json_expr: JSON expression parsing
        
        Used by: zParser, zLoader (CRITICAL), zAuth, zFunc, zShell
        Complexity: High (RBAC transformation, UI file detection)
    
    **vafile/ package** (Specialized):
        zVaFile (zVacuum File) parsing for declarative zCLI files.
        - parse_ui_file: UI file parser with RBAC (CRITICAL for zWalker)
        - parse_schema_file: Database schema file parser
        - parse_config_file: Configuration file parser (NEW in v1.5.4)
        - parse_generic_file: Generic fallback parser
        
        Used by: parser_file (UI transformation), zData (schemas)
        Complexity: Very High (RBAC extraction, validation, metadata)

Public API Categories:

    **Path Operations** (2 functions):
        Path resolution and file type identification.
    
    **Command Operations** (1 function):
        Command string parsing to structured format.
    
    **Utility Operations** (4 functions):
        Core parsing utilities (expressions, paths, references).
    
    **Plugin Operations** (2 functions):
        Plugin invocation detection and resolution.
    
    **File Operations** (6 functions):
        File content parsing (YAML, JSON, auto-detection).
    
    **zVaFile Operations** (4 functions):
        Declarative file parsing (UI, Schema, Config, Generic).

Usage Examples:

    >>> # Path operations
    >>> from zOS.L2_Core.g_zParser.parser_modules import zPath_decoder, identify_zFile
    >>> path = zPath_decoder("zMachine.Config", logger)
    >>> file_type = identify_zFile("zUI.users.yaml")
    
    >>> # Command parsing
    >>> from zOS.L2_Core.g_zParser.parser_modules import parse_command
    >>> cmd = parse_command("zFunc users.list --limit 10", logger)
    
    >>> # Expression evaluation
    >>> from zOS.L2_Core.g_zParser.parser_modules import zExpr_eval
    >>> result = zExpr_eval('{"key": "value"}', logger)
    
    >>> # Plugin invocation
    >>> from zOS.L2_Core.g_zParser.parser_modules import is_plugin_invocation, resolve_plugin_invocation
    >>> if is_plugin_invocation("&MyPlugin.do_something()"):
    ...     result = resolve_plugin_invocation("&MyPlugin.do_something()", logger, session)
    
    >>> # File parsing
    >>> from zOS.L2_Core.g_zParser.parser_modules import parse_file_content
    >>> data = parse_file_content(raw_yaml, logger, ".yaml")
    
    >>> # zVaFile parsing
    >>> from zOS.L2_Core.g_zParser.parser_modules import parse_ui_file
    >>> ui_data = parse_ui_file(yaml_data, logger, file_path="zUI.users.yaml")

Design Principles:

    1. **Bottom-Up Dependencies**: Foundation → Specialized → Aggregation
    2. **Single Responsibility**: Each module handles one parsing aspect
    3. **No Circular Dependencies**: Clean dependency tree
    4. **Comprehensive Documentation**: Every function documented
    5. **Type Safety**: 100% type hint coverage across all modules
    6. **External Stability**: Public API signatures remain stable

Performance:

    - Most parsing is O(n) where n = input size
    - Plugin resolution uses caching for performance
    - Path resolution is O(1) (constant time lookups)
    - Command parsing handles complex quoting efficiently

Thread Safety:

    All modules are thread-safe (no shared state).
    Loggers and sessions passed as parameters.

Version History:

    - v1.5.4 Week 6.8.1: Naming conventions aligned (zParser_* → parser_*)
    - v1.5.4 Week 6.8.2: parser_utils upgraded (D → A+)
    - v1.5.4 Week 6.8.3: parser_path upgraded (D → A+)
    - v1.5.4 Week 6.8.4: parser_commands upgraded (D+ → A+)
    - v1.5.4 Week 6.8.5: parser_plugin upgraded (C+ → A+)
    - v1.5.4 Week 6.8.6: vafile/ package refactoring (monolithic → modular)
    - v1.5.4 Week 6.8.7: parser_file upgraded (D+ → A+)
    - v1.5.4 Week 6.8.8: parser_modules/__init__ upgraded (C → A+)

See Also:

    - zParser: Main facade for parser subsystem
    - zLoader: Uses parser_file for UI loading
    - zShell: Uses parse_command for command execution
    - zDispatch: Uses resolve_plugin_invocation for plugins
"""

__version__ = "1.5.4"
__author__ = "zOS Framework"


# ============================================================================
# TIER 1: FOUNDATION (Core Utilities)
# ============================================================================

# Path Operations - Path resolution and file type identification
from .parser_path import (
    zPath_decoder,      # Resolve zMachine.* paths to OS-specific paths
    identify_zFile      # Identify zUI/zSchema/zConfig file types
)

# Utility Operations - Core parsing utilities (expressions, paths, references)
from .parser_utils import (
    zExpr_eval,         # Evaluate JSON expressions (used by navigation_linking)
    parse_dotted_path,  # Parse dotted paths (e.g., "user.name")
    handle_zRef,        # Handle zRef YAML references
    handle_zParser      # Handle parser directives
)


# ============================================================================
# TIER 2: SPECIALIZED PARSERS
# ============================================================================

# Command Operations - Command string parsing to structured format
from .parser_commands import (
    parse_command       # Parse command strings (20+ types: zFunc, zLink, zOpen, etc.)
    # NOTE: _split_command is private (internal to parser_commands)
)

# Plugin Operations - Plugin invocation detection and resolution
from .parser_plugin import (
    is_plugin_invocation,       # Check if string is plugin invocation (&Plugin.func)
    resolve_plugin_invocation   # Resolve plugin calls with caching and async support
)

# File Operations - File content parsing (YAML, JSON, auto-detection)
from .parser_file import (
    parse_file_content,   # Main file parser (CRITICAL - 6 external usages)
    parse_yaml,           # YAML-specific parsing with safe_load
    parse_json,           # JSON-specific parsing
    detect_format,        # Auto-detect file format (JSON vs YAML)
    parse_file_by_path,   # Convenience: load + parse in one call
    parse_json_expr       # Parse JSON expressions (for zExpr_eval compatibility)
)

# zVaFile Operations - Declarative file parsing (UI, Schema, Config, Generic)
from .vafile import (
    parse_ui_file,        # UI file parser with RBAC extraction (CRITICAL for zWalker)
    parse_schema_file,    # Database schema file parser
    parse_config_file,    # Configuration file parser (NEW in v1.5.4)
    parse_generic_file    # Generic fallback parser for unknown types
)


# ============================================================================
# PUBLIC API DEFINITION
# ============================================================================

__all__ = [
    # ========================================================================
    # TIER 1: FOUNDATION
    # ========================================================================
    
    # Path Operations (2 functions)
    "zPath_decoder",        # Path resolution: zMachine.* → OS-specific paths
    "identify_zFile",       # File type identification: zUI/zSchema/zConfig
    
    # Utility Operations (4 functions)
    "zExpr_eval",           # Expression evaluation: JSON expressions
    "parse_dotted_path",    # Path parsing: dotted notation (user.name)
    "handle_zRef",          # Reference handling: zRef YAML references
    "handle_zParser",       # Parser directives: parser-specific commands
    
    # ========================================================================
    # TIER 2: SPECIALIZED PARSERS
    # ========================================================================
    
    # Command Operations (1 function)
    "parse_command",        # Command parsing: 20+ command types
    
    # Plugin Operations (2 functions)
    "is_plugin_invocation",        # Plugin detection: &Plugin.function
    "resolve_plugin_invocation",   # Plugin resolution: execute with caching
    
    # File Operations (6 functions)
    "parse_file_content",   # Main parser: YAML/JSON with RBAC (CRITICAL)
    "parse_yaml",           # YAML parser: safe_load with error handling
    "parse_json",           # JSON parser: json.loads with error handling
    "detect_format",        # Format detection: auto-detect JSON vs YAML
    "parse_file_by_path",   # Convenience: load file + parse content
    "parse_json_expr",      # Expression parser: JSON-like strings
    
    # zVaFile Operations (4 functions)
    "parse_ui_file",        # UI parser: RBAC extraction (CRITICAL)
    "parse_schema_file",    # Schema parser: database schemas
    "parse_config_file",    # Config parser: configuration files (NEW)
    "parse_generic_file",   # Generic parser: fallback for unknown types
]
