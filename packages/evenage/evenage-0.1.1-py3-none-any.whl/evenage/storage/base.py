"""
Base storage adapter interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import json
from pydantic import BaseModel


class StorageConfig(BaseModel):
    """Configuration for storage adapters."""
    
    provider: str = "filesystem"  # Default to local filesystem
    base_path: str = "./data/storage"
    bucket: str = "evenage"
    
    # S3/MinIO specific
    endpoint: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    region: str = "us-east-1"
    secure: bool = True


class StorageAdapter(ABC):
    """Base class for storage adapters."""
    
    def __init__(self, config: StorageConfig):
        self.config = config
    
    @abstractmethod
    def upload_bytes(self, key: str, data: bytes, metadata: Optional[Dict[str, str]] = None) -> str:
        """Upload binary data."""
        pass
    
    @abstractmethod
    def download_bytes(self, key: str) -> bytes:
        """Download binary data."""
        pass
    
    @abstractmethod
    def upload_json(self, key: str, data: Dict[str, Any]) -> str:
        """Upload JSON data."""
        pass
    
    @abstractmethod
    def download_json(self, key: str) -> Dict[str, Any]:
        """Download JSON data."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete an object."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if object exists."""
        pass
    
    @abstractmethod
    def list_objects(self, prefix: str = "") -> list[str]:
        """List objects with optional prefix."""
        pass
    
    def upload_text(self, key: str, text: str) -> str:
        """Upload text data."""
        return self.upload_bytes(key, text.encode("utf-8"))
    
    def download_text(self, key: str) -> str:
        """Download text data."""
        return self.download_bytes(key).decode("utf-8")
