# zCLI/L1_Foundation/a_zConfig/zConfig_modules/helpers/detectors/__init__.py
"""
Machine detection subsystem for zConfig.

This package provides comprehensive machine capability detection, organized by category:
- Browser detection (default browser, launch commands)
- Media apps (image viewers, video players, audio players)
- IDE detection (text editors and IDEs)
- Hardware detection (CPU, GPU, memory, network)
- System orchestration (auto-detect, config generation, zCLI install info)
"""

# Browser detection
from .browser import (
    detect_browser,
    get_browser_launch_command,
)

# Media apps (image/video/audio)
from .media_apps import (
    detect_image_viewer,
    get_image_viewer_launch_command,
    detect_video_player,
    get_video_player_launch_command,
    detect_audio_player,
    get_audio_player_launch_command,
)

# IDE detection
from .ide import (
    detect_ide,
    get_ide_launch_command,
)

# Hardware detection
from .hardware import (
    detect_memory_gb,
    detect_cpu_architecture,
    detect_gpu,
    detect_network,
)

# System orchestration
from .system import (
    detect_zcli_install_info,
    create_user_machine_config,
    auto_detect_machine,
)

__all__ = [
    # Browser
    "detect_browser",
    "get_browser_launch_command",
    # Media apps
    "detect_image_viewer",
    "get_image_viewer_launch_command",
    "detect_video_player",
    "get_video_player_launch_command",
    "detect_audio_player",
    "get_audio_player_launch_command",
    # IDE
    "detect_ide",
    "get_ide_launch_command",
    # Hardware
    "detect_memory_gb",
    "detect_cpu_architecture",
    "detect_gpu",
    "detect_network",
    # System orchestration
    "detect_zcli_install_info",
    "create_user_machine_config",
    "auto_detect_machine",
]

