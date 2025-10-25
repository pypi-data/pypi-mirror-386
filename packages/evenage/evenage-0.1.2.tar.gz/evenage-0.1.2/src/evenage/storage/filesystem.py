"""
Local filesystem storage adapter - Default.
"""

import os
import json
import shutil
from typing import Optional, Dict, Any
from pathlib import Path

from evenage.storage.base import StorageAdapter, StorageConfig


class FilesystemAdapter(StorageAdapter):
    """Local filesystem storage adapter."""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.base_path = Path(config.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_full_path(self, key: str) -> Path:
        """Get full path for a key."""
        return self.base_path / key
    
    def upload_bytes(self, key: str, data: bytes, metadata: Optional[Dict[str, str]] = None) -> str:
        """Upload binary data to filesystem."""
        path = self._get_full_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "wb") as f:
            f.write(data)
        
        # Store metadata if provided
        if metadata:
            meta_path = path.with_suffix(path.suffix + ".meta")
            with open(meta_path, "w") as f:
                json.dump(metadata, f)
        
        return str(path)
    
    def download_bytes(self, key: str) -> bytes:
        """Download binary data from filesystem."""
        path = self._get_full_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Object not found: {key}")
        
        with open(path, "rb") as f:
            return f.read()
    
    def upload_json(self, key: str, data: Dict[str, Any]) -> str:
        """Upload JSON data to filesystem."""
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        return self.upload_bytes(key, json_bytes)
    
    def download_json(self, key: str) -> Dict[str, Any]:
        """Download JSON data from filesystem."""
        data = self.download_bytes(key)
        return json.loads(data.decode("utf-8"))
    
    def delete(self, key: str) -> bool:
        """Delete an object from filesystem."""
        path = self._get_full_path(key)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            
            # Delete metadata if exists
            meta_path = path.with_suffix(path.suffix + ".meta")
            if meta_path.exists():
                meta_path.unlink()
            
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if object exists in filesystem."""
        return self._get_full_path(key).exists()
    
    def list_objects(self, prefix: str = "") -> list[str]:
        """List objects with optional prefix."""
        search_path = self.base_path / prefix if prefix else self.base_path
        
        if not search_path.exists():
            return []
        
        objects = []
        for path in search_path.rglob("*"):
            if path.is_file() and not path.suffix == ".meta":
                relative = path.relative_to(self.base_path)
                objects.append(str(relative))
        
        return sorted(objects)
