"""
Storage adapters for EvenAge.
Supports multiple storage backends with local filesystem as default.
"""

from evenage.storage.base import StorageAdapter, StorageConfig
from evenage.storage.factory import create_storage_adapter

__all__ = ["StorageAdapter", "StorageConfig", "create_storage_adapter"]
