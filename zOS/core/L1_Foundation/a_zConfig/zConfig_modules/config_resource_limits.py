"""
zConfig Resource Limits Module
===============================

Applies CPU and memory resource limits based on zMachine configuration.

Cross-Platform Strategy:
    - Soft limits: Work on all platforms (application voluntarily respects limits)
    - Hard limits: Linux-only enhancement (OS enforces limits)

Soft Limits (All Platforms):
    - Stores limits for application use
    - Can be queried by multiprocessing pools, caches, etc.

Hard Limits (Linux Only):
    - OS enforces memory limit (process killed if exceeded)
    - OS binds process to specific CPU cores

Usage:
    limits = ResourceLimits(machine_config)
    limits.apply()
    
    # Later, in application code:
    max_workers = limits.get_cpu_limit()
    pool = multiprocessing.Pool(processes=max_workers)
"""

import platform
from typing import Dict, Any, Optional


class ResourceLimits:
    """Manages CPU and memory resource limits with cross-platform support."""
    
    def __init__(self, machine_config: Dict[str, Any]):
        """
        Initialize resource limits from machine configuration.
        
        Args:
            machine_config: Dictionary containing machine detection results
        """
        self.machine_config = machine_config
        
        # Extract limits from config
        self.cpu_cores_limit = machine_config.get('cpu_cores_limit')
        self.memory_gb_limit = machine_config.get('memory_gb_limit')
        
        # Detect available hardware
        self.cpu_cores_available = machine_config.get('cpu_cores', 1)
        self.memory_gb_available = machine_config.get('memory_gb', 1)
        
        # Status tracking
        self.applied = False
        self.hard_limits_supported = platform.system() == "Linux"
        self.hard_limits_applied = False
    
    def apply(self) -> Dict[str, Any]:
        """
        Apply resource limits.
        
        Returns soft limits on all platforms, with Linux getting additional
        OS-level enforcement.
        
        Returns:
            Dict with status information:
                - cpu_limit: Effective CPU limit
                - memory_limit_gb: Effective memory limit in GB
                - soft_limits_applied: Always True
                - hard_limits_applied: True on Linux if successful
                - platform: Current platform
        """
        result = {
            "cpu_limit": self.get_cpu_limit(),
            "memory_limit_gb": self.get_memory_limit_gb(),
            "soft_limits_applied": True,
            "hard_limits_applied": False,
            "platform": platform.system(),
            "errors": []
        }
        
        # Apply Linux-specific hard limits if available
        if self.hard_limits_supported:
            try:
                self._apply_linux_hard_limits()
                result["hard_limits_applied"] = True
            except Exception as e:
                result["errors"].append(f"Hard limits failed (soft limits still active): {e}")
        
        self.applied = True
        return result
    
    def get_cpu_limit(self) -> int:
        """
        Get effective CPU core limit.
        
        Returns user-specified limit if set, otherwise returns detected cores.
        This can be used by application code to limit worker pools.
        
        Returns:
            int: Number of CPU cores to use
        """
        if self.cpu_cores_limit and self.cpu_cores_limit > 0:
            # Use smaller of limit and available
            return min(self.cpu_cores_limit, self.cpu_cores_available)
        return self.cpu_cores_available
    
    def get_memory_limit_gb(self) -> int:
        """
        Get effective memory limit in GB.
        
        Returns user-specified limit if set, otherwise returns detected memory.
        This can be used by application code to limit cache sizes.
        
        Returns:
            int: Memory limit in GB
        """
        if self.memory_gb_limit and self.memory_gb_limit > 0:
            # Use smaller of limit and available
            return min(self.memory_gb_limit, self.memory_gb_available)
        return self.memory_gb_available
    
    def get_memory_limit_bytes(self) -> int:
        """Get effective memory limit in bytes."""
        return self.get_memory_limit_gb() * 1024**3
    
    def _apply_linux_hard_limits(self) -> None:
        """
        Apply OS-enforced resource limits on Linux.
        
        Raises:
            Exception: If limits cannot be applied (gracefully caught by caller)
        """
        import resource
        import os
        
        # Apply memory limit (RLIMIT_AS = address space)
        if self.memory_gb_limit and self.memory_gb_limit > 0:
            memory_bytes = self.memory_gb_limit * 1024**3
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        
        # Apply CPU affinity (bind to specific cores)
        if self.cpu_cores_limit and self.cpu_cores_limit > 0:
            # Create a set of CPU IDs to bind to
            cpu_set = set(range(min(self.cpu_cores_limit, self.cpu_cores_available)))
            os.sched_setaffinity(0, cpu_set)
        
        self.hard_limits_applied = True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current resource limits status.
        
        Returns:
            Dict with current limits and availability info
        """
        return {
            "cpu_cores_available": self.cpu_cores_available,
            "cpu_cores_limit": self.cpu_cores_limit,
            "cpu_cores_effective": self.get_cpu_limit(),
            "memory_gb_available": self.memory_gb_available,
            "memory_gb_limit": self.memory_gb_limit,
            "memory_gb_effective": self.get_memory_limit_gb(),
            "applied": self.applied,
            "platform": platform.system(),
            "hard_limits_supported": self.hard_limits_supported,
            "hard_limits_applied": self.hard_limits_applied,
        }

