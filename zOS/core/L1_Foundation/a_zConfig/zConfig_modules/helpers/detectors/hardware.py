# zCLI/L1_Foundation/a_zConfig/zConfig_modules/helpers/detectors/hardware.py
"""Hardware detection (CPU, GPU, memory, network) for zCLI machine configuration."""

from zOS import os, platform, subprocess, importlib
from typing import Dict, Any, Optional
from .shared import BYTES_PER_GB, KB_PER_MB, MB_PER_GB


def detect_memory_gb() -> Optional[int]:
    """Detect system memory in GB via psutil or platform-specific methods."""
    # Try psutil first (most reliable, cross-platform)
    try:
        psutil = importlib.import_module("psutil")
        memory_bytes = psutil.virtual_memory().total
        return int(memory_bytes / BYTES_PER_GB)
    except Exception:
        pass  # Fall through to platform-specific methods

    # Platform-specific fallbacks
    try:
        system = platform.system()

        # Linux: read from /proc/meminfo
        if system == "Linux":
            with open("/proc/meminfo", encoding='utf-8') as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return int(kb / (KB_PER_MB * MB_PER_GB))

        # macOS: use sysctl
        elif system == "Darwin":
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                memory_bytes = int(result.stdout.strip())
                return int(memory_bytes / BYTES_PER_GB)
    except Exception:
        pass  # Silent fail - memory detection is optional

    # Couldn't detect
    return None


def detect_cpu_architecture() -> Dict[str, Any]:
    """Detect detailed CPU architecture (physical, logical, P-cores, E-cores)."""
    result = {
        "cpu_physical": None,
        "cpu_logical": None,
        "cpu_performance": None,
        "cpu_efficiency": None,
    }
    
    system = platform.system()
    
    try:
        # Try psutil first (cross-platform)
        psutil = importlib.import_module("psutil")
        result["cpu_logical"] = psutil.cpu_count(logical=True)
        result["cpu_physical"] = psutil.cpu_count(logical=False)
    except Exception:
        pass
    
    # Fallback to os.cpu_count() for logical
    if result["cpu_logical"] is None:
        result["cpu_logical"] = os.cpu_count() or 1
    
    # Platform-specific detection
    try:
        if system == "Darwin":
            # macOS: use sysctl for detailed info
            phys_result = subprocess.run(
                ["sysctl", "-n", "hw.physicalcpu"],
                capture_output=True, text=True, check=False, timeout=2
            )
            if phys_result.returncode == 0:
                result["cpu_physical"] = int(phys_result.stdout.strip())
            
            # Fallback for physical cores (needed before Apple Silicon detection)
            if result["cpu_physical"] is None:
                result["cpu_physical"] = result["cpu_logical"]
            
            # Apple Silicon: try to detect P-cores and E-cores
            if platform.machine() == "arm64" and result["cpu_physical"]:
                detected = False
                try:
                    # Try to get performance level counts (macOS 12+)
                    perf0_result = subprocess.run(
                        ["sysctl", "-n", "hw.perflevel0.logicalcpu"],
                        capture_output=True, text=True, check=False, timeout=2
                    )
                    perf1_result = subprocess.run(
                        ["sysctl", "-n", "hw.perflevel1.logicalcpu"],
                        capture_output=True, text=True, check=False, timeout=2
                    )
                    
                    if perf0_result.returncode == 0 and perf1_result.returncode == 0:
                        perf0 = int(perf0_result.stdout.strip())
                        perf1 = int(perf1_result.stdout.strip())
                        # Higher count is typically P-cores
                        result["cpu_performance"] = max(perf0, perf1)
                        result["cpu_efficiency"] = min(perf0, perf1)
                        detected = True
                except Exception:
                    pass
                
                # Fallback: Known Apple Silicon configurations
                if not detected:
                    total = result["cpu_physical"]
                    if total == 8:
                        # M1, M2: 4 P-cores + 4 E-cores
                        result["cpu_performance"] = 4
                        result["cpu_efficiency"] = 4
                    elif total == 10:
                        # M1 Pro, M2 Pro (10-core): 8 P-cores + 2 E-cores
                        result["cpu_performance"] = 8
                        result["cpu_efficiency"] = 2
                    elif total == 12:
                        # M2 Pro (12-core): 8 P-cores + 4 E-cores
                        result["cpu_performance"] = 8
                        result["cpu_efficiency"] = 4
        
        elif system == "Linux":
            # Linux: read from /sys or lscpu
            if result["cpu_physical"] is None:
                try:
                    lscpu_result = subprocess.run(
                        ["lscpu", "-p=cpu"],
                        capture_output=True, text=True, check=False, timeout=2
                    )
                    if lscpu_result.returncode == 0:
                        cores = [line for line in lscpu_result.stdout.split('\n') if line and not line.startswith('#')]
                        result["cpu_physical"] = len(cores)
                except Exception:
                    pass
    
    except Exception:
        pass  # Silent fail
    
    # Final fallback if still None (for non-Darwin systems)
    if result["cpu_physical"] is None:
        result["cpu_physical"] = result["cpu_logical"]
    
    return result


def detect_gpu(system_memory_gb: Optional[int] = None) -> Dict[str, Any]:
    """Detect GPU information (type, vendor, memory, compute APIs).
    
    Args:
        system_memory_gb: Total system RAM (for Apple Silicon unified memory)
    """
    result = {
        "gpu_available": False,
        "gpu_type": None,
        "gpu_vendor": None,
        "gpu_memory_gb": None,
        "gpu_compute": [],
    }
    
    system = platform.system()
    
    try:
        if system == "Darwin":
            # macOS: use system_profiler
            profiler_result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True, text=True, check=False, timeout=5
            )
            
            if profiler_result.returncode == 0:
                output = profiler_result.stdout
                
                # Look for GPU info
                if "Chipset Model:" in output:
                    result["gpu_available"] = True
                    
                    # Extract GPU model
                    for line in output.split('\n'):
                        if "Chipset Model:" in line:
                            result["gpu_type"] = line.split(":", 1)[1].strip()
                        elif "Vendor:" in line:
                            vendor = line.split(":", 1)[1].strip()
                            # Clean up vendor name
                            if "Apple" in vendor or "Apple" in result.get("gpu_type", ""):
                                result["gpu_vendor"] = "Apple"
                            elif "NVIDIA" in vendor:
                                result["gpu_vendor"] = "NVIDIA"
                            elif "AMD" in vendor or "ATI" in vendor:
                                result["gpu_vendor"] = "AMD"
                            elif "Intel" in vendor:
                                result["gpu_vendor"] = "Intel"
                        elif "VRAM (Dynamic, Max):" in line or "VRAM (Total):" in line:
                            # Discrete GPU VRAM
                            memory_str = line.split(":", 1)[1].strip()
                            if "GB" in memory_str:
                                result["gpu_memory_gb"] = int(memory_str.split()[0])
                            elif "MB" in memory_str:
                                result["gpu_memory_gb"] = int(memory_str.split()[0]) // 1024
                
                # Apple Silicon: unified memory (GPU can access all system RAM)
                if result["gpu_vendor"] == "Apple" and result["gpu_memory_gb"] is None:
                    if system_memory_gb:
                        # Use provided system memory (from detect_memory_gb())
                        result["gpu_memory_gb"] = system_memory_gb
                    else:
                        # Fallback: try sysctl if system_memory_gb not provided
                        try:
                            mem_result = subprocess.run(
                                ["sysctl", "-n", "hw.memsize"],
                                capture_output=True, text=True, check=False, timeout=2
                            )
                            if mem_result.returncode == 0:
                                total_ram_gb = int(mem_result.stdout.strip()) // BYTES_PER_GB
                                result["gpu_memory_gb"] = total_ram_gb
                        except Exception:
                            pass
                
                # Detect compute APIs
                if result["gpu_available"]:
                    # Metal is available on all modern macOS GPUs
                    result["gpu_compute"].append("Metal")
        
        elif system == "Linux":
            # Linux: try nvidia-smi for NVIDIA, rocm-smi for AMD
            
            # Check NVIDIA
            nvidia_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, check=False, timeout=3
            )
            if nvidia_result.returncode == 0 and nvidia_result.stdout.strip():
                result["gpu_available"] = True
                result["gpu_vendor"] = "NVIDIA"
                parts = nvidia_result.stdout.strip().split(',')
                result["gpu_type"] = parts[0].strip()
                if len(parts) > 1:
                    memory_str = parts[1].strip()
                    result["gpu_memory_gb"] = int(memory_str.split()[0]) // 1024
                result["gpu_compute"].append("CUDA")
            
            # Check AMD ROCm
            if not result["gpu_available"]:
                rocm_result = subprocess.run(
                    ["rocm-smi", "--showproductname"],
                    capture_output=True, text=True, check=False, timeout=3
                )
                if rocm_result.returncode == 0 and "GPU" in rocm_result.stdout:
                    result["gpu_available"] = True
                    result["gpu_vendor"] = "AMD"
                    result["gpu_compute"].append("ROCm")
        
        elif system == "Windows":
            # Windows: use wmic
            wmic_result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name,AdapterRAM"],
                capture_output=True, text=True, check=False, timeout=3
            )
            if wmic_result.returncode == 0:
                lines = [line.strip() for line in wmic_result.stdout.split('\n') if line.strip()]
                if len(lines) > 1:  # Skip header
                    result["gpu_available"] = True
                    gpu_line = lines[1]
                    parts = gpu_line.rsplit(None, 1)
                    if len(parts) == 2:
                        result["gpu_type"] = parts[0]
                        try:
                            ram_bytes = int(parts[1])
                            result["gpu_memory_gb"] = ram_bytes // BYTES_PER_GB
                        except ValueError:
                            pass
                    
                    # Detect vendor from name
                    if result["gpu_type"]:
                        if "NVIDIA" in result["gpu_type"]:
                            result["gpu_vendor"] = "NVIDIA"
                            result["gpu_compute"].append("CUDA")
                        elif "AMD" in result["gpu_type"] or "Radeon" in result["gpu_type"]:
                            result["gpu_vendor"] = "AMD"
                        elif "Intel" in result["gpu_type"]:
                            result["gpu_vendor"] = "Intel"
    
    except Exception:
        pass  # Silent fail - GPU detection is optional
    
    return result


def detect_network() -> Dict[str, Any]:
    """Detect network interfaces and IP addresses.
    
    Note: psutil.net_if_addrs() has known memory corruption bugs on some systems.
    We use platform-specific methods (ifconfig, netstat, ip) for reliability.
    
    Returns 6 essential properties:
      - network_interfaces: List of all interface names
      - network_primary: Active interface name
      - network_ip_local: Local IP of primary interface
      - network_mac_address: MAC address of primary interface
      - network_gateway: Default gateway/router IP
      - network_ip_public: Public IP (optional, may be None)
    """
    result = {
        "network_interfaces": [],
        "network_primary": None,
        "network_ip_local": None,
        "network_mac_address": None,
        "network_gateway": None,
        "network_ip_public": None,
    }
    
    system = platform.system()
    
    # Platform-specific detection (primary method - more reliable than psutil)
    try:
        if system in ("Linux", "Darwin"):
            # Use ifconfig for macOS/Linux
            ifconfig_result = subprocess.run(
                ["ifconfig"],
                capture_output=True, text=True, check=False, timeout=3
            )
            if ifconfig_result.returncode == 0:
                output = ifconfig_result.stdout
                current_iface = None
                current_status = "down"
                current_ip = None
                current_mac = None
                
                for line in output.split('\n'):
                    # New interface (line starts without whitespace and has :)
                    if line and not line[0].isspace() and ':' in line:
                        # Save previous interface
                        if current_iface and current_iface != "lo0" and not current_iface.startswith("lo"):
                            result["network_interfaces"].append(current_iface)
                            
                            # Determine primary (first up interface with IP)
                            if result["network_primary"] is None and current_status == "up" and current_ip:
                                result["network_primary"] = current_iface
                                result["network_ip_local"] = current_ip
                                result["network_mac_address"] = current_mac
                        
                        # Start new interface
                        current_iface = line.split(':')[0].strip()
                        current_status = "down"
                        current_ip = None
                        current_mac = None
                        
                        # Check if UP/RUNNING in the first line
                        if "UP" in line and "RUNNING" in line:
                            current_status = "up"
                    
                    # Parse interface details (indented lines)
                    elif current_iface and line.startswith('\t'):
                        line = line.strip()
                        # IPv4 address
                        if line.startswith("inet ") and not line.startswith("inet6"):
                            parts = line.split()
                            if len(parts) >= 2:
                                current_ip = parts[1]
                        # MAC address
                        elif line.startswith("ether "):
                            parts = line.split()
                            if len(parts) >= 2:
                                current_mac = parts[1]
                
                # Save last interface
                if current_iface and current_iface != "lo0" and not current_iface.startswith("lo"):
                    result["network_interfaces"].append(current_iface)
                    if result["network_primary"] is None and current_status == "up" and current_ip:
                        result["network_primary"] = current_iface
                        result["network_ip_local"] = current_ip
                        result["network_mac_address"] = current_mac
        
        elif system == "Windows":
            # Use ipconfig for Windows
            ipconfig_result = subprocess.run(
                ["ipconfig", "/all"],
                capture_output=True, text=True, check=False, timeout=3
            )
            if ipconfig_result.returncode == 0:
                # Simplified Windows parsing
                # Full implementation would need more robust parsing
                result["network_interfaces"].append("Ethernet")
                result["network_primary"] = "Ethernet"
    
    except Exception:
        pass  # Silent fail
    
    # Detect default gateway (router IP)
    try:
        if system in ("Darwin", "Linux"):
            # Try netstat first (most reliable on macOS)
            netstat_result = subprocess.run(
                ["netstat", "-rn"],
                capture_output=True, text=True, check=False, timeout=3
            )
            if netstat_result.returncode == 0:
                for line in netstat_result.stdout.split('\n'):
                    # Look for default route
                    if line.startswith("default") or line.startswith("0.0.0.0"):
                        parts = line.split()
                        if len(parts) >= 2:
                            # Second column is usually the gateway
                            gateway = parts[1]
                            # Validate it's an IP address (not a hostname like "UGScg")
                            if '.' in gateway and not gateway[0].isalpha():
                                result["network_gateway"] = gateway
                                break
        
        elif system == "Windows":
            # Use route print for Windows
            route_result = subprocess.run(
                ["route", "print", "0.0.0.0"],
                capture_output=True, text=True, check=False, timeout=3
            )
            if route_result.returncode == 0:
                for line in route_result.stdout.split('\n'):
                    if "0.0.0.0" in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            # Third column is typically the gateway
                            gateway = parts[2]
                            if '.' in gateway:
                                result["network_gateway"] = gateway
                                break
    
    except Exception:
        pass  # Silent fail
    
    # Try to get public IP (optional, requires network call)
    try:
        import urllib.request
        # Use a fast, reliable service (timeout 2 seconds)
        response = urllib.request.urlopen('https://api.ipify.org', timeout=2)
        result["network_ip_public"] = response.read().decode('utf-8').strip()
    except Exception:
        pass  # Silent fail - public IP is optional
    
    return result

