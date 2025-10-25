"""
Storage integration for large responses.

Automatically stores large LLM responses and task results in MinIO.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ResponseStorage:
    """
    Manages storage of large responses in MinIO.

    Automatically determines if a response should be stored based on size,
    and replaces the response with a reference pointer.
    """

    def __init__(
        self,
        storage_service: Any = None,
        enabled: bool = True,
        default_threshold_kb: int = 100,
    ):
        """
        Initialize response storage.

        Args:
            storage_service: StorageService instance (MinIO client)
            enabled: Enable storage (can be disabled via config)
            default_threshold_kb: Default size threshold in KB
        """
        self.storage_service = storage_service
        self.enabled = enabled
        self.default_threshold_kb = default_threshold_kb

    def store_if_large(
        self,
        data: Any,
        agent_name: str,
        operation: str,
        size_threshold_kb: int | None = None,
    ) -> dict[str, Any]:
        """
        Store data in MinIO if it exceeds size threshold.

        Args:
            data: Data to potentially store
            agent_name: Agent that produced the data
            operation: Operation name
            size_threshold_kb: Size threshold in KB (uses default if None)

        Returns:
            Either the original data or a reference dict with storage location
        """
        if not self.enabled or not self.storage_service:
            return data

        threshold = size_threshold_kb or self.default_threshold_kb

        # Estimate size
        try:
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data)
            elif isinstance(data, str):
                data_str = data
            else:
                data_str = str(data)

            size_kb = sys.getsizeof(data_str) / 1024

            # If under threshold, return as-is
            if size_kb < threshold:
                return data

            # Store in MinIO
            key = self._generate_key(agent_name, operation)
            ref = self.storage_service.upload_json(
                key=key,
                data=data if isinstance(data, (dict, list)) else {"content": data_str},
                metadata={
                    "agent": agent_name,
                    "operation": operation,
                    "size_kb": str(int(size_kb)),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(
                f"Stored large response ({size_kb:.1f}KB) in MinIO: {ref}"
            )

            # Return reference
            return {
                "_stored_in_minio": True,
                "_storage_ref": ref,
                "_storage_key": key,
                "_size_kb": size_kb,
                "_agent": agent_name,
                "_operation": operation,
                "_summary": self._create_summary(data),
            }

        except Exception as e:
            logger.error(f"Failed to store large response: {e}")
            # Return original data on error
            return data

    def retrieve(self, storage_ref: dict[str, Any]) -> Any:
        """
        Retrieve data from MinIO using a storage reference.

        Args:
            storage_ref: Reference dict returned by store_if_large

        Returns:
            Original data
        """
        if not storage_ref.get("_stored_in_minio"):
            return storage_ref

        try:
            key = storage_ref["_storage_key"]
            data = self.storage_service.download_json(key)

            # Unwrap if we wrapped a string
            if isinstance(data, dict) and "content" in data and len(data) == 1:
                return data["content"]

            return data

        except Exception as e:
            logger.error(f"Failed to retrieve from MinIO: {e}")
            raise

    def _generate_key(self, agent_name: str, operation: str) -> str:
        """Generate a unique key for storage."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"responses/{agent_name}/{operation}/{timestamp}_{unique_id}.json"

    def _create_summary(self, data: Any) -> str:
        """Create a brief summary of stored data for the reference."""
        if isinstance(data, dict):
            keys = list(data.keys())[:5]
            return f"Dict with keys: {', '.join(keys)}"
        elif isinstance(data, list):
            return f"List with {len(data)} items"
        elif isinstance(data, str):
            return f"String ({len(data)} chars): {data[:100]}..."
        else:
            return f"Data of type {type(data).__name__}"


# Global instance
_response_storage: ResponseStorage | None = None


def init_response_storage(
    storage_service: Any,
    enabled: bool = True,
    default_threshold_kb: int = 100,
) -> ResponseStorage:
    """
    Initialize global response storage.

    Args:
        storage_service: StorageService instance
        enabled: Enable storage
        default_threshold_kb: Default size threshold

    Returns:
        ResponseStorage instance
    """
    global _response_storage
    _response_storage = ResponseStorage(
        storage_service=storage_service,
        enabled=enabled,
        default_threshold_kb=default_threshold_kb,
    )
    return _response_storage


def get_response_storage() -> ResponseStorage:
    """Get global response storage instance."""
    if _response_storage is None:
        # Return disabled instance if not initialized
        return ResponseStorage(storage_service=None, enabled=False)
    return _response_storage
