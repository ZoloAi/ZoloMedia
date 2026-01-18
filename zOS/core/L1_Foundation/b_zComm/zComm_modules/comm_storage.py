# zCLI/subsystems/zComm/zComm_modules/comm_storage.py
"""
Object Storage Client for zCLI - Hierarchical Config Aware.

Provides unified interface to storage backends with automatic config
resolution through zConfig's 5-layer hierarchy.

Hierarchy (lowest → highest priority):
    1. System defaults: STORAGE_BACKEND=local (in zConfig.defaults.yaml)
    2. User config: User's storage preferences
    3. User config (legacy): Backward compat
    4. .zEnv: STORAGE_BACKEND=s3, STORAGE_S3_BUCKET=my-bucket
    5. zSpark: {"storage_backend": "s3"} (runtime override)

Usage:
    # Backend auto-detected from config hierarchy
    zcli.comm.storage.put("path/to/file.jpg", data)
    
    # Config examples (.zEnv):
    STORAGE_BACKEND=local
    STORAGE_LOCAL_ROOT=storage/
"""

from pathlib import Path
from typing import Optional, Union, BinaryIO, Any
from .comm_constants import (
    STORAGE_DEFAULT_BACKEND,
    STORAGE_SUPPORTED_BACKENDS,
    STORAGE_CONFIG_KEY_BACKEND,
    STORAGE_CONFIG_KEY_LOCAL_ROOT,
    STORAGE_CONFIG_KEY_S3_BUCKET,
    STORAGE_CONFIG_KEY_S3_REGION
)

# Module Constants
_LOG_PREFIX = "[StorageClient]"


class StorageClient:
    """
    Unified object storage interface with hierarchical config resolution.
    
    Automatically selects backend based on zConfig's 5-layer hierarchy.
    """
    
    def __init__(self, zcli: Any):
        """
        Initialize storage client with auto-detected backend.
        
        Args:
            zcli: zCLI instance (provides access to config hierarchy)
        """
        self.zcli = zcli
        self.logger = zcli.logger
        
        # Get backend from config hierarchy (auto-cascades through all 5 layers!)
        backend = self._get_config(STORAGE_CONFIG_KEY_BACKEND, STORAGE_DEFAULT_BACKEND)
        
        # Validate backend
        if backend not in STORAGE_SUPPORTED_BACKENDS:
            self.logger.warning(
                f"{_LOG_PREFIX} Unknown backend '{backend}', falling back to 'local'"
            )
            backend = "local"
        
        # Initialize appropriate adapter
        self.backend = backend
        self.adapter = self._create_adapter(backend)
        
        self.logger.framework.info(f"{_LOG_PREFIX} Initialized with backend: {backend}")
    
    def _get_config(self, key: str, default: Any = None) -> Any:
        """
        Get config value from zConfig hierarchy (respects all 5 layers).
        
        Args:
            key: Config key (e.g., "storage_backend")
            default: Default value if not found
        
        Returns:
            Config value from highest priority layer
        """
        # Try environment dict first (zConfig managed)
        value = self.zcli.config.environment.env.get(key)
        if value is not None:
            return value
        
        # Fallback to OS environment (for uppercase env vars like STORAGE_BACKEND)
        from zOS import os
        upper_key = key.upper()
        value = os.environ.get(upper_key)
        if value is not None:
            return value
        
        return default
    
    def _create_adapter(self, backend: str):
        """Create storage adapter based on backend type."""
        if backend == "local":
            return LocalAdapter(self.zcli, self._get_config)
        elif backend == "s3":
            return S3Adapter(self.zcli, self._get_config)
        elif backend == "azure":
            return AzureBlobAdapter(self.zcli, self._get_config)
        elif backend == "gcs":
            return GCSAdapter(self.zcli, self._get_config)
        else:
            # Fallback
            return LocalAdapter(self.zcli, self._get_config)
    
    # ═══════════════════════════════════════════════════════════
    # Public API (Backend-Agnostic)
    # ═══════════════════════════════════════════════════════════
    
    def put(self, key: str, data: Union[bytes, BinaryIO]) -> str:
        """
        Upload file to storage.
        
        Args:
            key: Storage key (e.g., "storage/users/00/01/2345/avatar.jpg")
            data: File data (bytes or file-like object)
        
        Returns:
            str: Full path or URL to stored file
        """
        return self.adapter.put(key, data)
    
    def get(self, key: str) -> bytes:
        """
        Download file from storage.
        
        Args:
            key: Storage key
        
        Returns:
            bytes: File data
        """
        return self.adapter.get(key)
    
    def delete(self, key: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            key: Storage key
        
        Returns:
            bool: True if deleted, False if not found
        """
        return self.adapter.delete(key)
    
    def exists(self, key: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            key: Storage key
        
        Returns:
            bool: True if exists, False otherwise
        """
        return self.adapter.exists(key)
    
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate URL for file access.
        
        Args:
            key: Storage key
            expires_in: URL expiration in seconds (default: 1 hour)
        
        Returns:
            str: Public or presigned URL
        """
        return self.adapter.get_url(key, expires_in)


# ═══════════════════════════════════════════════════════════
# Storage Adapters (Backend Implementations)
# ═══════════════════════════════════════════════════════════

class StorageAdapter:
    """Abstract base class for storage adapters."""
    
    def put(self, key: str, data: Union[bytes, BinaryIO]) -> str:
        raise NotImplementedError
    
    def get(self, key: str) -> bytes:
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        raise NotImplementedError
    
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        raise NotImplementedError


class LocalAdapter(StorageAdapter):
    """Local filesystem storage adapter."""
    
    def __init__(self, zcli: Any, get_config: callable):
        self.zcli = zcli
        self.logger = zcli.logger
        self.get_config = get_config
        
        # Get root from config (Layer 4: .zEnv, Layer 5: zSpark)
        root_path = self.get_config(STORAGE_CONFIG_KEY_LOCAL_ROOT)
        
        if root_path:
            self.root = Path(root_path)
        elif zcli.config.app_root:
            # Use app-specific storage (Phase 1.1)
            self.root = zcli.config.app_root
        else:
            # Fallback: current directory
            self.root = Path.cwd() / "storage"
        
        self.logger.framework.debug(f"{_LOG_PREFIX} LocalAdapter root: {self.root}")
    
    def put(self, key: str, data: Union[bytes, BinaryIO]) -> str:
        """Save file to local filesystem."""
        file_path = self.root / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(data, bytes):
            file_path.write_bytes(data)
        else:
            file_path.write_bytes(data.read())
        
        self.logger.framework.debug(f"{_LOG_PREFIX} Saved: {file_path}")
        return str(file_path)
    
    def get(self, key: str) -> bytes:
        """Read file from local filesystem."""
        file_path = self.root / key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return file_path.read_bytes()
    
    def delete(self, key: str) -> bool:
        """Delete file from local filesystem."""
        file_path = self.root / key
        if file_path.exists():
            file_path.unlink()
            self.logger.framework.debug(f"{_LOG_PREFIX} Deleted: {file_path}")
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if file exists."""
        return (self.root / key).exists()
    
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Return local file path (no URL for local storage)."""
        return str(self.root / key)


class S3Adapter(StorageAdapter):
    """
    AWS S3 storage adapter (Phase 1.3b).
    
    Uses boto3 for S3 operations with automatic credential detection:
    1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    2. AWS credentials file (~/.aws/credentials)
    3. IAM role (if running on EC2/ECS/Lambda)
    """
    
    def __init__(self, zcli: Any, get_config: callable):
        self.zcli = zcli
        self.logger = zcli.logger
        self.get_config = get_config
        
        # Import boto3 (lazy import - only when S3 backend is used)
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            self.boto3 = boto3
            self.ClientError = ClientError
            self.NoCredentialsError = NoCredentialsError
        except ImportError:
            self.logger.error(f"{_LOG_PREFIX} boto3 not installed! Run: pip install boto3")
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
        
        # Get S3 configuration from zConfig hierarchy
        self.bucket = self.get_config(STORAGE_CONFIG_KEY_S3_BUCKET)
        self.region = self.get_config(STORAGE_CONFIG_KEY_S3_REGION, 'us-east-1')
        
        if not self.bucket:
            raise ValueError("STORAGE_S3_BUCKET must be configured in .zEnv for S3 backend")
        
        # Initialize S3 client (credentials auto-detected from environment)
        try:
            self.client = boto3.client('s3', region_name=self.region)
            
            # Verify bucket exists and we have access
            self.client.head_bucket(Bucket=self.bucket)
            
            self.logger.framework.info(
                f"{_LOG_PREFIX} S3Adapter initialized: s3://{self.bucket} (region: {self.region})"
            )
        except self.NoCredentialsError:
            self.logger.error(
                f"{_LOG_PREFIX} AWS credentials not found! Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .zEnv"
            )
            raise
        except self.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                self.logger.error(f"{_LOG_PREFIX} S3 bucket '{self.bucket}' does not exist!")
            elif error_code == '403':
                self.logger.error(f"{_LOG_PREFIX} Access denied to bucket '{self.bucket}'. Check IAM permissions.")
            else:
                self.logger.error(f"{_LOG_PREFIX} S3 error: {e}")
            raise
    
    def put(self, key: str, data: Union[bytes, BinaryIO]) -> str:
        """Upload file to S3."""
        try:
            # Convert BinaryIO to bytes if needed
            if not isinstance(data, bytes):
                data = data.read()
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data
            )
            
            self.logger.framework.debug(f"{_LOG_PREFIX} Uploaded: s3://{self.bucket}/{key}")
            return f"s3://{self.bucket}/{key}"
            
        except self.ClientError as e:
            self.logger.error(f"{_LOG_PREFIX} Failed to upload {key}: {e}")
            raise
    
    def get(self, key: str) -> bytes:
        """Download file from S3."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            data = response['Body'].read()
            
            self.logger.framework.debug(f"{_LOG_PREFIX} Downloaded: s3://{self.bucket}/{key}")
            return data
            
        except self.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: {key}")
            else:
                self.logger.error(f"{_LOG_PREFIX} Failed to download {key}: {e}")
                raise
    
    def delete(self, key: str) -> bool:
        """Delete file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            
            self.logger.framework.debug(f"{_LOG_PREFIX} Deleted: s3://{self.bucket}/{key}")
            return True
            
        except self.ClientError as e:
            self.logger.error(f"{_LOG_PREFIX} Failed to delete {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            else:
                self.logger.error(f"{_LOG_PREFIX} Error checking existence of {key}: {e}")
                raise
    
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate presigned URL for temporary access.
        
        Args:
            key: S3 object key
            expires_in: URL expiration in seconds (default: 1 hour)
        
        Returns:
            Presigned URL that expires after expires_in seconds
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            
            self.logger.framework.debug(
                f"{_LOG_PREFIX} Generated presigned URL for {key} (expires in {expires_in}s)"
            )
            return url
            
        except self.ClientError as e:
            self.logger.error(f"{_LOG_PREFIX} Failed to generate presigned URL for {key}: {e}")
            raise


class AzureBlobAdapter(StorageAdapter):
    """Azure Blob Storage adapter (future)."""
    
    def __init__(self, zcli: Any, get_config: callable):
        self.logger = zcli.logger
        self.logger.framework.warning(f"{_LOG_PREFIX} AzureBlobAdapter not yet implemented!")
    
    def put(self, key: str, data: Union[bytes, BinaryIO]) -> str:
        raise NotImplementedError("Azure support coming later")
    
    def get(self, key: str) -> bytes:
        raise NotImplementedError("Azure support coming later")
    
    def delete(self, key: str) -> bool:
        raise NotImplementedError("Azure support coming later")
    
    def exists(self, key: str) -> bool:
        raise NotImplementedError("Azure support coming later")
    
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        raise NotImplementedError("Azure support coming later")


class GCSAdapter(StorageAdapter):
    """Google Cloud Storage adapter (future)."""
    
    def __init__(self, zcli: Any, get_config: callable):
        self.logger = zcli.logger
        self.logger.framework.warning(f"{_LOG_PREFIX} GCSAdapter not yet implemented!")
    
    def put(self, key: str, data: Union[bytes, BinaryIO]) -> str:
        raise NotImplementedError("GCS support coming later")
    
    def get(self, key: str) -> bytes:
        raise NotImplementedError("GCS support coming later")
    
    def delete(self, key: str) -> bool:
        raise NotImplementedError("GCS support coming later")
    
    def exists(self, key: str) -> bool:
        raise NotImplementedError("GCS support coming later")
    
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        raise NotImplementedError("GCS support coming later")

