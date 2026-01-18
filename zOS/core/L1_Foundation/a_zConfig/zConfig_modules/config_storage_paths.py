"""
Storage path management for cross-platform user storage.

Provides platform-appropriate paths for user and service-specific storage:
- macOS:   ~/Library/Application Support/zolo-zcli/users/{user_id}/
- Linux:   ~/.config/zolo-zcli/users/{user_id}/
- Windows: %APPDATA%/zolo-zcli/users/{user_id}/

Part of Phase 1.5: Storage Architecture & Quotas
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path


class StoragePathManager:
    """
    Manages cross-platform storage paths for users and services.
    
    Integrates with existing zConfigPaths infrastructure.
    """
    
    def __init__(self, config):
        """
        Initialize with reference to zConfig.
        
        Args:
            config: zConfig instance for accessing paths
        """
        self.config = config
        self.logger = config.logger if hasattr(config, 'logger') else None
    
    def get_user_storage_path(self, user_id: int) -> str:
        """
        Get platform-appropriate storage path for user.
        
        Returns:
            str: Path like ~/Library/Application Support/zolo-zcli/users/123/
        """
        base = str(self.config.paths.user_data_dir)
        user_path = os.path.join(base, "users", str(user_id))
        
        # Ensure directory exists
        os.makedirs(user_path, exist_ok=True)
        
        if self.logger:
            self.logger.debug(f"[StoragePathManager] User {user_id} storage: {user_path}")
        
        return user_path
    
    def get_service_storage_path(self, user_id: int, service_name: str) -> str:
        """
        Get service-specific storage path within user's storage.
        
        Args:
            user_id: User ID
            service_name: Service name (e.g., "zvideo", "zaudio")
        
        Returns:
            str: Path like ~/Library/.../users/123/zvideo/
        """
        user_path = self.get_user_storage_path(user_id)
        service_path = os.path.join(user_path, service_name.lower())
        
        # Ensure directory exists
        os.makedirs(service_path, exist_ok=True)
        
        if self.logger:
            self.logger.debug(f"[StoragePathManager] Service {service_name} storage: {service_path}")
        
        return service_path
    
    def get_storage_info(self, path: str) -> Dict[str, Any]:
        """
        Get storage information for a path.
        
        Returns:
            dict: {"total_bytes": int, "used_bytes": int, "free_bytes": int}
        """
        import shutil
        total, used, free = shutil.disk_usage(path)
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free
        }

