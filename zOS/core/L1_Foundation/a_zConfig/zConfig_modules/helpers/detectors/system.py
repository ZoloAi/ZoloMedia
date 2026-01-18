# zCLI/L1_Foundation/a_zConfig/zConfig_modules/helpers/detectors/system.py
"""Main orchestrator for machine detection and configuration file generation."""

import logging
import sys
from zOS import os, platform, socket, Path
from typing import Dict, Any, Optional
from importlib.metadata import distribution, PackageNotFoundError

# Module-level logger
logger = logging.getLogger(__name__)

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

# YAML template for machine config file
MACHINE_CONFIG_TEMPLATE = """
# zolo-zcli Machine Configuration
# This file was auto-generated on first run.
# You can edit this file to customize your tool preferences.

zMachine:
  # Machine Identity (auto-detected, do not edit unless needed)
  os: "{os}"
  os_version: "{os_version}"
  os_name: "{os_name}"
  hostname: "{hostname}"
  architecture: "{architecture}"

  # Python Runtime (auto-detected)
  python_version: "{python_version}"
  python_impl: "{python_impl}"
  python_build: "{python_build}"
  python_compiler: "{python_compiler}"
  libc_ver: "{libc_ver}"
  python_executable: "{python_executable}"
  
  # zCLI Installation (auto-detected, useful for troubleshooting)
  zcli_install_path: "{zcli_install_path}"
  zcli_install_type: "{zcli_install_type}"

  # Tool Preferences (customize these to your liking!)
  browser: "{browser}"          # Chrome, Firefox, Arc, Safari, etc.
  ide: "{ide}"                  # cursor, code, subl, etc.
  image_viewer: "{image_viewer}" # Preview, eog, Photos, etc.
  video_player: "{video_player}" # QuickTime Player, VLC, Movies, etc.
  audio_player: "{audio_player}" # Music, VLC, Audacious, etc.
  terminal: "{terminal}"        # Terminal emulator
  shell: "{shell}"              # bash, zsh, fish, etc.
  lang: "{lang}"
  timezone: "{timezone}"
  
  # Time/Date Formatting (customize to your preference!)
  time_format: "{time_format}"          # HH:MM:SS, HH:MM, etc.
  date_format: "{date_format}"          # ddmmyyyy, mmddyyyy, yyyy-mm-dd, etc.
  datetime_format: "{datetime_format}"  # Combined format

  # Paths (auto-detected)
  home: "{home}"
  cwd: "{cwd}"
  username: "{username}"
  path: "{path}"

  # CPU Architecture (auto-detected, read-only)
  processor: "{processor}"
  cpu_cores: {cpu_cores}              # Total logical CPUs (backward compatibility)
  cpu_physical: {cpu_physical}        # Physical cores
  cpu_logical: {cpu_logical}          # Logical cores (with hyperthreading)
  cpu_performance: {cpu_performance}  # P-cores (Apple Silicon, null otherwise)
  cpu_efficiency: {cpu_efficiency}    # E-cores (Apple Silicon, null otherwise)
  memory_gb: {memory_gb}              # Total system RAM
  
  # Resource Limits (optional, editable - limit what zCLI can use)
  # cpu_cores_limit: 4                # Limit to 4 cores (even if more detected)
  # memory_gb_limit: 8                # Limit to 8GB (even if more detected)
  
  # GPU Capabilities (auto-detected)
  gpu_available: {gpu_available}
  gpu_type: {gpu_type}
  gpu_vendor: {gpu_vendor}
  gpu_memory_gb: {gpu_memory_gb}
  gpu_compute: {gpu_compute}          # e.g., ["Metal"], ["CUDA"], ["ROCm"]
  
  # Network Interfaces (auto-detected)
  network_interfaces: {network_interfaces}       # All interface names
  network_primary: {network_primary}             # Active interface
  network_ip_local: {network_ip_local}           # Local IP (primary)
  network_mac_address: {network_mac_address}     # MAC (primary)
  network_gateway: {network_gateway}             # Default gateway/router IP
  network_ip_public: {network_ip_public}         # Public IP (optional)
  
  # Custom Fields (add your own as needed)
  # datacenter: "us-west-2"
  # cluster: "lfs-cluster"
  # lfs_node_id: "node-001"
"""


def detect_zcli_install_info() -> Dict[str, str]:
    """Detect zCLI installation path and type."""
    try:
        dist = distribution("zolo-zcli")
        
        # Get installation path
        if dist.files:
            # Get the first file's parent to find site-packages location
            first_file = next(iter(dist.files))
            install_path = str(first_file.locate().parent.parent.resolve())
        else:
            install_path = "unknown"
        
        # Determine install type (editable vs standard)
        try:
            direct_url = dist.read_text('direct_url.json')
            install_type = "editable" if direct_url and "editable" in direct_url else "standard"
        except:
            # Alternative check: if install path contains the package name at root level
            install_type = "editable" if "zolo-zcli" in install_path and "site-packages" not in install_path else "standard"
        
        return {
            "python_executable": sys.executable,
            "zcli_install_path": install_path,
            "zcli_install_type": install_type
        }
    except (PackageNotFoundError, Exception):
        # zCLI not installed or error detecting
        return {
            "python_executable": sys.executable,
            "zcli_install_path": "not_installed",
            "zcli_install_type": "unknown"
        }


def create_user_machine_config(path: Path, machine: Dict[str, Any]) -> None:
    """Create zConfig.machine.yaml with auto-detected values and user-editable preferences."""
    try:
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Format template with machine data (handle None values for YAML)
        content = MACHINE_CONFIG_TEMPLATE.format(
            os=machine.get('os', 'unknown'),
            os_version=machine.get('os_version', 'unknown'),
            os_name=machine.get('os_name', 'unknown'),
            hostname=machine.get('hostname', 'unknown'),
            architecture=machine.get('architecture', 'unknown'),
            python_version=machine.get('python_version', 'unknown'),
            python_impl=machine.get('python_impl', 'unknown'),
            python_build=machine.get('python_build', 'unknown'),
            python_compiler=machine.get('python_compiler', 'unknown'),
            libc_ver=machine.get('libc_ver', 'unknown'),
            python_executable=machine.get('python_executable', 'unknown'),
            zcli_install_path=machine.get('zcli_install_path', 'unknown'),
            zcli_install_type=machine.get('zcli_install_type', 'unknown'),
            browser=machine.get('browser', 'unknown'),
            ide=machine.get('ide', 'unknown'),
            image_viewer=machine.get('image_viewer', 'unknown'),
            video_player=machine.get('video_player', 'unknown'),
            audio_player=machine.get('audio_player', 'unknown'),
            terminal=machine.get('terminal', 'unknown'),
            shell=machine.get('shell', 'unknown'),
            lang=machine.get('lang', 'unknown'),
            timezone=machine.get('timezone', 'unknown'),
            time_format=machine.get('time_format', 'unknown'),
            date_format=machine.get('date_format', 'unknown'),
            datetime_format=machine.get('datetime_format', 'unknown'),
            home=machine.get('home', 'unknown'),
            cwd=machine.get('cwd', 'unknown'),
            username=machine.get('username', 'unknown'),
            path=machine.get('path', 'unknown'),
            processor=machine.get('processor', 'unknown'),
            cpu_cores=machine.get('cpu_cores', 'null'),
            cpu_physical=machine.get('cpu_physical', 'null'),
            cpu_logical=machine.get('cpu_logical', 'null'),
            cpu_performance=machine.get('cpu_performance', 'null'),
            cpu_efficiency=machine.get('cpu_efficiency', 'null'),
            memory_gb=machine.get('memory_gb', 'null'),
            gpu_available=machine.get('gpu_available', 'false'),
            gpu_type=machine.get('gpu_type', 'null'),
            gpu_vendor=machine.get('gpu_vendor', 'null'),
            gpu_memory_gb=machine.get('gpu_memory_gb', 'null'),
            gpu_compute=machine.get('gpu_compute', '[]'),
            network_interfaces=machine.get('network_interfaces', '[]'),
            network_primary=machine.get('network_primary', 'null'),
            network_ip_local=machine.get('network_ip_local', 'null'),
            network_mac_address=machine.get('network_mac_address', 'null'),
            network_gateway=machine.get('network_gateway', 'null'),
            network_ip_public=machine.get('network_ip_public', 'null'),
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
        logger.debug("[MachineConfig] Auto-detecting machine information...")

    # Detect zCLI installation info
    zcli_info = detect_zcli_install_info()
    
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
        "python_executable": zcli_info["python_executable"],  # Path to Python executable
        "zcli_install_path": zcli_info["zcli_install_path"],  # Where zCLI is installed
        "zcli_install_type": zcli_info["zcli_install_type"],  # editable vs standard

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

