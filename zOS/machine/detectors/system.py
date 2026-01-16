# zOS/machine/detectors/system.py
"""Main orchestrator for machine detection and configuration file generation."""

import logging
import sys
import os
import platform
import socket
from pathlib import Path
from typing import Dict, Any, Optional
from importlib.metadata import distribution, PackageNotFoundError

# Module-level logger
logger = logging.getLogger("zolo.os.machine")

from .shared import (
    _log_config, _log_error, _safe_getcwd,
    DEFAULT_SHELL, DEFAULT_TIMEZONE,
    DEFAULT_TIME_FORMAT, DEFAULT_DATE_FORMAT, DEFAULT_DATETIME_FORMAT,
)
from .browser import detect_browser
from .ide import detect_ide
from .media_apps import (
    detect_image_viewer,
    detect_video_player,
    detect_audio_player,
)
from .hardware import (
    detect_memory_gb,
    detect_cpu_architecture,
    detect_gpu,
    detect_network,
)

# .zolo template for machine config file
MACHINE_CONFIG_TEMPLATE = """# Zolo Ecosystem Machine Configuration (.zolo format)

zMachine:
	machine_identity:
		os: {os}
		os_version: {os_version}
		os_name: {os_name}
		hostname: {hostname}
		architecture: {architecture}

	python_runtime:
		version: {python_version}
		implementation: {python_impl}
		build: {python_build}
		compiler: {python_compiler}
		libc_ver: {libc_ver}
		executable: {python_executable}

	user_preferences:
		browser: {browser} #> Chrome, Firefox, Arc, Safari, Brave <#
		ide: {ide} #> cursor, code, subl, vim, emacs <#
		image_viewer: {image_viewer} #> Preview (macOS), eog (Linux), Photos <#
		video_player: {video_player} #> QuickTime, VLC, Movies <#
		audio_player: {audio_player} #> Music (macOS), VLC, Audacious <#
		terminal: {terminal} #> Terminal emulator <#
		shell: {shell} #> bash, zsh, fish, tcsh <#
		lang: {lang}
		timezone: {timezone}

	time_date_formatting:
		time_format: {time_format} #> 24-hour: HH:MM:SS, 12-hour: hh:MM:SS AM/PM <#
		date_format: {date_format} #> ddmmyyyy, mmddyyyy, yyyy-mm-dd <#
		datetime_format: {datetime_format} #> ddmmyyyy HH:MM:SS, yyyy-mm-dd HH:MM:SS <#

	user_paths:
		home: {home}
		cwd: {cwd}
		username: {username}
		path: {path}

	cpu:
		processor: {processor}
		cores_total: {cpu_cores} #> Total logical CPUs <#
		cores_physical: {cpu_physical} #> Physical cores <#
		cores_logical: {cpu_logical} #> Logical cores (with hyperthreading) <#
		cores_performance: {cpu_performance} #> P-cores (Apple Silicon only) <#
		cores_efficiency: {cpu_efficiency} #> E-cores (Apple Silicon only) <#

	memory:
		total_gb: {memory_gb} #> Total system RAM in GB <#

	gpu:
		available: {gpu_available}
		type: {gpu_type}
		vendor: {gpu_vendor}
		memory_gb: {gpu_memory_gb}
		compute: {gpu_compute}

	network:
		interfaces: {network_interfaces}
		primary: {network_primary}
		ip_local: {network_ip_local}
		mac_address: {network_mac_address}
		gateway: {network_gateway}
		ip_public: {network_ip_public}

	launch_commands:
		browser: {launch_browser}
		ide: {launch_ide}
		image_viewer: {launch_image_viewer}
		video_player: {launch_video_player}
		audio_player: {launch_audio_player}

	custom: null
"""


def create_user_machine_config(path: Path, machine: Dict[str, Any]) -> None:
    """Create zConfig.machine.zolo with auto-detected values and user-editable preferences."""
    try:
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Helper to format values for .zolo format
        def fmt_value(val):
            if val is None:
                return 'null'
            elif isinstance(val, bool):
                return 'true' if val else 'false'
            elif isinstance(val, (int, float)):
                return str(val)
            elif isinstance(val, list):
                # Format as inline bracket array
                if not val:
                    return '[]'
                return '[' + ', '.join(str(v) for v in val) + ']'
            elif isinstance(val, str) and val == '':
                return '""'
            else:
                return val
        
        # Generate launch commands based on OS
        os_name = machine.get('os', 'unknown')
        browser = machine.get('browser', 'unknown')
        ide = machine.get('ide', 'unknown')
        image_viewer = machine.get('image_viewer', 'unknown')
        video_player = machine.get('video_player', 'unknown')
        audio_player = machine.get('audio_player', 'unknown')
        
        # Platform-specific launch commands
        if os_name == 'Darwin':  # macOS
            # For macOS, use 'open -a "App Name"' format (quotes only around app name if it has spaces)
            if browser == 'Chrome':
                launch_browser = 'open -a "Google Chrome"'
            elif browser == 'unknown':
                launch_browser = 'open -a Safari'
            elif ' ' in browser:
                launch_browser = f'open -a "{browser}"'
            else:
                launch_browser = f'open -a {browser}'
            
            launch_ide = ide if ide in ['code', 'cursor', 'subl', 'vim', 'emacs'] else 'code'
            
            if image_viewer == 'unknown':
                launch_image_viewer = 'open -a Preview'
            elif ' ' in image_viewer:
                launch_image_viewer = f'open -a "{image_viewer}"'
            else:
                launch_image_viewer = f'open -a {image_viewer}'
            
            if video_player == 'unknown':
                launch_video_player = 'open -a "QuickTime Player"'
            elif ' ' in video_player:
                launch_video_player = f'open -a "{video_player}"'
            else:
                launch_video_player = f'open -a {video_player}'
            
            if audio_player == 'unknown':
                launch_audio_player = 'open -a Music'
            elif ' ' in audio_player:
                launch_audio_player = f'open -a "{audio_player}"'
            else:
                launch_audio_player = f'open -a {audio_player}'
        elif os_name == 'Linux':
            launch_browser = browser.lower() if browser != 'unknown' else 'firefox'
            launch_ide = ide if ide != 'unknown' else 'code'
            launch_image_viewer = image_viewer.lower() if image_viewer != 'unknown' else 'eog'
            launch_video_player = video_player.lower() if video_player != 'unknown' else 'vlc'
            launch_audio_player = audio_player.lower() if audio_player != 'unknown' else 'audacious'
        elif os_name == 'Windows':
            launch_browser = f'start {browser}' if browser != 'unknown' else 'start msedge'
            launch_ide = ide if ide != 'unknown' else 'code'
            launch_image_viewer = 'start ms-photos:' if image_viewer != 'unknown' else 'start ms-photos:'
            launch_video_player = 'start wmplayer' if video_player != 'unknown' else 'start wmplayer'
            launch_audio_player = 'start wmplayer' if audio_player != 'unknown' else 'start wmplayer'
        else:
            launch_browser = browser
            launch_ide = ide
            launch_image_viewer = image_viewer
            launch_video_player = video_player
            launch_audio_player = audio_player

        # Format template with machine data
        # Pad values for aligned comments (40 chars total width for key:value before comment)
        def pad_for_comment(key, value, target_width=37):
            """Pad value so key: value reaches target width for comment alignment."""
            key_value = f"{key}: {value}"
            if len(key_value) < target_width:
                return value + ' ' * (target_width - len(key_value))
            return value
        
        # Get formatted values
        browser_val = fmt_value(machine.get('browser', 'unknown'))
        ide_val = fmt_value(machine.get('ide', 'unknown'))
        image_viewer_val = fmt_value(machine.get('image_viewer', 'unknown'))
        video_player_val = fmt_value(machine.get('video_player', 'unknown'))
        audio_player_val = fmt_value(machine.get('audio_player', 'unknown'))
        terminal_val = fmt_value(machine.get('terminal', 'unknown'))
        shell_val = fmt_value(machine.get('shell', 'unknown'))
        time_format_val = fmt_value(machine.get('time_format', 'unknown'))
        date_format_val = fmt_value(machine.get('date_format', 'unknown'))
        datetime_format_val = fmt_value(machine.get('datetime_format', 'unknown'))
        cpu_cores_val = fmt_value(machine.get('cpu_cores'))
        cpu_physical_val = fmt_value(machine.get('cpu_physical'))
        cpu_logical_val = fmt_value(machine.get('cpu_logical'))
        cpu_performance_val = fmt_value(machine.get('cpu_performance'))
        cpu_efficiency_val = fmt_value(machine.get('cpu_efficiency'))
        memory_gb_val = fmt_value(machine.get('memory_gb'))
        
        content = MACHINE_CONFIG_TEMPLATE.format(
            os=fmt_value(machine.get('os', 'unknown')),
            os_version=fmt_value(machine.get('os_version', 'unknown')),
            os_name=fmt_value(machine.get('os_name', 'unknown')),
            hostname=fmt_value(machine.get('hostname', 'unknown')),
            architecture=fmt_value(machine.get('architecture', 'unknown')),
            python_version=fmt_value(machine.get('python_version', 'unknown')),
            python_impl=fmt_value(machine.get('python_impl', 'unknown')),
            python_build=fmt_value(machine.get('python_build', 'unknown')),
            python_compiler=fmt_value(machine.get('python_compiler', 'unknown')),
            libc_ver=fmt_value(machine.get('libc_ver', '')),
            python_executable=fmt_value(machine.get('python_executable', 'unknown')),
            browser=pad_for_comment('browser', browser_val),
            ide=pad_for_comment('ide', ide_val),
            image_viewer=pad_for_comment('image_viewer', image_viewer_val),
            video_player=pad_for_comment('video_player', video_player_val),
            audio_player=pad_for_comment('audio_player', audio_player_val),
            terminal=pad_for_comment('terminal', terminal_val),
            shell=pad_for_comment('shell', shell_val),
            lang=fmt_value(machine.get('lang', 'unknown')),
            timezone=fmt_value(machine.get('timezone', 'unknown')),
            time_format=pad_for_comment('time_format', time_format_val),
            date_format=pad_for_comment('date_format', date_format_val),
            datetime_format=pad_for_comment('datetime_format', datetime_format_val),
            home=fmt_value(machine.get('home', 'unknown')),
            cwd=fmt_value(machine.get('cwd', 'unknown')),
            username=fmt_value(machine.get('username', 'unknown')),
            path=fmt_value(machine.get('path', 'unknown')),
            processor=fmt_value(machine.get('processor', 'unknown')),
            cpu_cores=pad_for_comment('cores_total', cpu_cores_val, 32),
            cpu_physical=pad_for_comment('cores_physical', cpu_physical_val, 32),
            cpu_logical=pad_for_comment('cores_logical', cpu_logical_val, 32),
            cpu_performance=pad_for_comment('cores_performance', cpu_performance_val, 32),
            cpu_efficiency=pad_for_comment('cores_efficiency', cpu_efficiency_val, 32),
            memory_gb=pad_for_comment('total_gb', memory_gb_val, 32),
            gpu_available=fmt_value(machine.get('gpu_available', False)),
            gpu_type=fmt_value(machine.get('gpu_type')),
            gpu_vendor=fmt_value(machine.get('gpu_vendor')),
            gpu_memory_gb=fmt_value(machine.get('gpu_memory_gb')),
            gpu_compute=fmt_value(machine.get('gpu_compute', [])),
            network_interfaces=fmt_value(machine.get('network_interfaces', [])),
            network_primary=fmt_value(machine.get('network_primary')),
            network_ip_local=fmt_value(machine.get('network_ip_local')),
            network_mac_address=fmt_value(machine.get('network_mac_address')),
            network_gateway=fmt_value(machine.get('network_gateway')),
            network_ip_public=fmt_value(machine.get('network_ip_public')),
            launch_browser=launch_browser,
            launch_ide=launch_ide,
            launch_image_viewer=launch_image_viewer,
            launch_video_player=launch_video_player,
            launch_audio_player=launch_audio_player,
        )

        path.write_text(content, encoding="utf-8")
        # Note: Always show config creation messages (not suppressed by production mode)
        _log_config(f"Created user machine config: {path}")
        _log_config("You can edit this file to customize tool preferences")

    except Exception as e:
        _log_error(f"Failed to create user machine config: {e}")


def auto_detect_machine(log_level: Optional[str] = None, is_production: bool = False) -> Dict[str, Any]:
    """Auto-detect machine identity, Python runtime, tools, and capabilities."""
    if not is_production:
        logger.debug("[zMachine] Auto-detecting machine information...")

    # Detect CPU architecture details
    cpu_arch = detect_cpu_architecture()
    
    # Detect memory first (needed for Apple Silicon GPU unified memory)
    system_memory_gb = detect_memory_gb()
    
    # Detect GPU information (pass system memory for unified memory calculation)
    gpu_info = detect_gpu(system_memory_gb=system_memory_gb)
    
    # Detect network interfaces and IPs
    network_info = detect_network()
    
    # Detect libc version (Linux-specific, handle Windows Store Python edge case)
    try:
        libc_ver = platform.libc_ver()[0]
    except (OSError, PermissionError):
        # Windows Store Python or other restricted environments
        libc_ver = ""

    machine = {
        # Identity
        "os": platform.system(),                    # Linux, Darwin, Windows
        "os_version": platform.release(),           # Kernel version
        "os_name": platform.platform(),             # Full OS name with version
        "hostname": socket.gethostname(),           # Machine name
        "architecture": platform.machine(),         # x86_64, arm64, etc.
        "processor": platform.processor(),          # CPU type
        "python_version": platform.python_version(), # 3.12.0
        "python_impl": platform.python_implementation(), # CPython, PyPy, etc.
        "python_build": platform.python_build()[0],  # Build info
        "python_compiler": platform.python_compiler(), # Compiler used
        "libc_ver": libc_ver,                       # libc version (Linux-specific)
        "python_executable": sys.executable,        # Path to Python executable

        # User tools (system defaults, user can override)
        "browser": detect_browser(log_level, is_production),
        "ide": detect_ide(log_level, is_production),
        "image_viewer": detect_image_viewer(log_level, is_production),
        "video_player": detect_video_player(log_level, is_production),
        "audio_player": detect_audio_player(log_level, is_production),
        "terminal": os.getenv("TERM", "unknown"),
        "shell": os.getenv("SHELL", DEFAULT_SHELL),
        "lang": os.getenv("LANG", "unknown"),       # System language
        "timezone": os.getenv("TZ", DEFAULT_TIMEZONE),      # Timezone if set
        "time_format": DEFAULT_TIME_FORMAT,         # Time format default
        "date_format": DEFAULT_DATE_FORMAT,         # Date format default
        "datetime_format": DEFAULT_DATETIME_FORMAT, # DateTime format default
        "home": str(Path.home()),                   # User's home directory

        # System capabilities
        "cpu_cores": os.cpu_count() or 1,           # Total logical CPUs (backward compatibility)
        "cpu_physical": cpu_arch["cpu_physical"],   # Physical cores
        "cpu_logical": cpu_arch["cpu_logical"],     # Logical cores (with hyperthreading)
        "cpu_performance": cpu_arch["cpu_performance"],  # P-cores (Apple Silicon)
        "cpu_efficiency": cpu_arch["cpu_efficiency"],    # E-cores (Apple Silicon)
        "memory_gb": system_memory_gb,              # Total system RAM (already detected)
        
        # GPU capabilities
        "gpu_available": gpu_info["gpu_available"],
        "gpu_type": gpu_info["gpu_type"],
        "gpu_vendor": gpu_info["gpu_vendor"],
        "gpu_memory_gb": gpu_info["gpu_memory_gb"],
        "gpu_compute": gpu_info["gpu_compute"],
        
        # Network interfaces
        "network_interfaces": network_info["network_interfaces"],
        "network_primary": network_info["network_primary"],
        "network_ip_local": network_info["network_ip_local"],
        "network_mac_address": network_info["network_mac_address"],
        "network_gateway": network_info["network_gateway"],
        "network_ip_public": network_info["network_ip_public"],
        
        "cwd": _safe_getcwd(),                     # Current working directory (safe)
        "username": os.getenv("USER") or os.getenv("USERNAME", "unknown"),
        "path": os.getenv("PATH", ""),             # System PATH
    }

    if not is_production:
        logger.debug("[MachineConfig] Identity: %s (%s) on %s", machine['hostname'], machine['username'], machine['os_name'])
        cpu_info = f"{machine['cpu_physical']} physical, {machine['cpu_logical']} logical"
        if machine['cpu_performance'] and machine['cpu_efficiency']:
            cpu_info += f" ({machine['cpu_performance']} P-cores, {machine['cpu_efficiency']} E-cores)"
        logger.debug("[MachineConfig] CPU: %s, %s cores", machine['processor'], cpu_info)
        logger.debug("[MachineConfig] RAM: %sGB", machine['memory_gb'])
        if machine['gpu_available']:
            gpu_mem = f", {machine['gpu_memory_gb']}GB" if machine['gpu_memory_gb'] else ""
            gpu_compute = f", {', '.join(machine['gpu_compute'])}" if machine['gpu_compute'] else ""
            logger.debug("[MachineConfig] GPU: %s%s%s", machine['gpu_type'], gpu_mem, gpu_compute)
        if machine['network_primary']:
            network_ip = machine['network_ip_local'] or "no IP"
            logger.debug("[MachineConfig] Network: %s (%s)", machine['network_primary'], network_ip)
        logger.debug("[MachineConfig] Python: %s %s on %s", machine['python_impl'], machine['python_version'], machine['architecture'])

    return machine

