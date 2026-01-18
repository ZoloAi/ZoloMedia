# zCLI/subsystems/zConfig/zConfig_modules/helpers/__init__.py
"""
Helper modules for zConfig functionality.

This package provides utility functions that support zConfig's hierarchical configuration system:

1. **detectors/** - Auto-detection of machine capabilities and user preferences
   - Organized by category: browser, IDE, media apps, hardware, system
   - Creates machine-specific configuration files with detected values
   - Provides fallback detection for cross-platform compatibility

2. **environment_helpers.py** - Environment configuration management
   - Creates default environment config files (deployment, network, security, logging)
   - Provides templates for environment-specific settings
   - Supports deployment profiles (Debug, Info, Production)

3. **config_helpers.py** - Generic configuration loading and override patterns
   - Loads YAML config files with hierarchical override behavior
   - Creates config files on first run if missing
   - Provides consistent file loading across all config modules

These helpers separate detection/creation logic from configuration data management,
enabling clean architecture, testability, and reusability across zConfig subsystems.
"""

from .detectors import (
    detect_browser,
    detect_ide,
    detect_image_viewer,
    detect_video_player,
    detect_audio_player,
    detect_memory_gb,
    create_user_machine_config,
    auto_detect_machine,
    get_browser_launch_command,
    get_ide_launch_command,
    get_image_viewer_launch_command,
    get_video_player_launch_command,
    get_audio_player_launch_command,
)
from .environment_helpers import (
    create_default_env_config,
)
from .config_helpers import (
    ensure_user_directories,
    ensure_app_directory,
    initialize_system_ui,
    initialize_system_migration_schema,
    load_config_with_override,
)

__all__ = [
    "detect_browser",
    "detect_ide",
    "detect_image_viewer",
    "detect_video_player",
    "detect_audio_player",
    "detect_memory_gb",
    "create_user_machine_config",
    "auto_detect_machine",
    "get_browser_launch_command",
    "get_ide_launch_command",
    "get_image_viewer_launch_command",
    "get_video_player_launch_command",
    "get_audio_player_launch_command",
    "create_default_env_config",
    "ensure_user_directories",
    "ensure_app_directory",
    "initialize_system_ui",
    "initialize_system_migration_schema",
    "load_config_with_override",
]
