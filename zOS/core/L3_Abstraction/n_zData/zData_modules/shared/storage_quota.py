"""
Storage quota management operations.

Provides database operations for checking and updating user storage quotas.
Works with users table storage fields.

Part of Phase 1.5: Storage Architecture & Quotas
"""

from zOS import Dict, Any


class StorageQuotaManager:
    """
    Manages storage quota queries and updates.
    
    Integrates with zData adapter for database operations.
    """
    
    def __init__(self, zdata):
        """
        Initialize with reference to zData instance.
        
        Args:
            zdata: zData instance for database access
        """
        self.zdata = zdata
        self.adapter = zdata.adapter
        self.logger = zdata.logger if hasattr(zdata, 'logger') else None
    
    def get_user_quota(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's storage quota and usage.
        
        Returns:
            dict: {
                "quota_bytes": int,
                "used_bytes": int,
                "available_bytes": int,
                "backend": str
            }
        """
        # Query users table
        users = self.adapter.select("users", where={"id": user_id})
        
        if not users or len(users) == 0:
            raise ValueError(f"User {user_id} not found")
        
        user = users[0]
        quota = int(user.get('storage_quota', 1073741824))  # Default 1GB
        used = int(user.get('storage_used', 0))
        
        return {
            "quota_bytes": quota,
            "used_bytes": used,
            "available_bytes": quota - used,
            "backend": user.get('storage_backend', 'local')
        }
    
    def check_quota(self, user_id: int, bytes_needed: int) -> bool:
        """
        Check if user has enough available quota.
        
        Args:
            user_id: User ID
            bytes_needed: Number of bytes needed
        
        Returns:
            bool: True if enough quota available
        """
        quota_info = self.get_user_quota(user_id)
        available = quota_info['available_bytes']
        
        has_quota = available >= bytes_needed
        
        if self.logger:
            self.logger.debug(
                f"[StorageQuota] User {user_id}: "
                f"needs {bytes_needed}, available {available}, "
                f"result: {has_quota}"
            )
        
        return has_quota
    
    def update_usage(self, user_id: int, bytes_delta: int) -> Dict[str, Any]:
        """
        Update user's storage usage.
        
        Args:
            user_id: User ID
            bytes_delta: Change in bytes (positive = add, negative = remove)
        
        Returns:
            dict: Updated quota info
        """
        # Get current usage
        quota_info = self.get_user_quota(user_id)
        new_used = quota_info['used_bytes'] + bytes_delta
        
        # Ensure non-negative
        if new_used < 0:
            new_used = 0
        
        # Update database
        self.adapter.update(
            "users",
            where={"id": user_id},
            values={"storage_used": new_used}
        )
        
        if self.logger:
            self.logger.info(
                f"[StorageQuota] User {user_id}: "
                f"{quota_info['used_bytes']} → {new_used} bytes "
                f"(delta: {bytes_delta:+d})"
            )
        
        # Return updated info
        return self.get_user_quota(user_id)
    
    def set_quota(self, user_id: int, quota_bytes: int) -> Dict[str, Any]:
        """
        Set user's storage quota (admin operation).
        
        Args:
            user_id: User ID
            quota_bytes: New quota in bytes
        
        Returns:
            dict: Updated quota info
        """
        self.adapter.update(
            "users",
            where={"id": user_id},
            values={"storage_quota": quota_bytes}
        )
        
        if self.logger:
            self.logger.info(f"[StorageQuota] User {user_id}: quota set to {quota_bytes} bytes")
        
        return self.get_user_quota(user_id)

