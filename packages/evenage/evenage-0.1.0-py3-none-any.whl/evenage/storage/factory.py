"""
Storage adapter factory.
"""

from evenage.storage.base import StorageAdapter, StorageConfig
from evenage.storage.filesystem import FilesystemAdapter


def create_storage_adapter(config: StorageConfig) -> StorageAdapter:
    """
    Create a storage adapter based on config.
    
    Supported providers:
    - filesystem (default, local-first)
    - minio
    - s3
    """
    
    provider = config.provider.lower()
    
    if provider == "filesystem":
        return FilesystemAdapter(config)
    elif provider == "minio":
        from evenage.storage.minio_storage import MinIOAdapter
        return MinIOAdapter(config)
    elif provider == "s3":
        from evenage.storage.s3 import S3Adapter
        return S3Adapter(config)
    else:
        raise ValueError(
            f"Unknown storage provider: {config.provider}. "
            f"Supported: filesystem, minio, s3"
        )
