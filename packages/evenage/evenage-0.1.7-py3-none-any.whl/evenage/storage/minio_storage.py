"""
MinIO/S3 storage layer for EvenAge.

Handles artifact storage for large payloads, results, and intermediate data.
"""

from __future__ import annotations

import json
import logging
from io import BytesIO
from typing import Any

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class StorageService:
    """MinIO/S3 storage service for artifacts and large payloads."""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin123",
        secure: bool = False,
        bucket: str = "evenage",
    ):
        """
        Initialize storage service.

        Args:
            endpoint: MinIO endpoint
            access_key: MinIO access key
            secret_key: MinIO secret key
            secure: Use HTTPS
            bucket: Default bucket name
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.bucket = bucket

        # Create bucket if it doesn't exist
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Failed to create bucket: {e}")

    def upload_json(
        self,
        key: str,
        data: dict[str, Any] | list[Any],
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Upload JSON data to storage.

        Args:
            key: Object key (path in bucket)
            data: JSON-serializable data
            metadata: Optional metadata

        Returns:
            Full reference path (s3://bucket/key)
        """
        try:
            json_bytes = json.dumps(data).encode("utf-8")
            data_stream = BytesIO(json_bytes)

            self.client.put_object(
                self.bucket,
                key,
                data_stream,
                length=len(json_bytes),
                content_type="application/json",
                metadata=metadata or {},
            )

            return f"s3://{self.bucket}/{key}"

        except S3Error as e:
            logger.error(f"Failed to upload JSON: {e}")
            raise

    def download_json(self, key: str) -> dict[str, Any] | list[Any]:
        """
        Download JSON data from storage.

        Args:
            key: Object key (path in bucket)

        Returns:
            Parsed JSON data
        """
        try:
            response = self.client.get_object(self.bucket, key)
            data = response.read()
            response.close()
            response.release_conn()

            return json.loads(data.decode("utf-8"))

        except S3Error as e:
            logger.error(f"Failed to download JSON: {e}")
            raise

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Upload raw bytes to storage.

        Args:
            key: Object key
            data: Raw bytes
            content_type: MIME type
            metadata: Optional metadata

        Returns:
            Full reference path
        """
        try:
            data_stream = BytesIO(data)

            self.client.put_object(
                self.bucket,
                key,
                data_stream,
                length=len(data),
                content_type=content_type,
                metadata=metadata or {},
            )

            return f"s3://{self.bucket}/{key}"

        except S3Error as e:
            logger.error(f"Failed to upload bytes: {e}")
            raise

    def download_bytes(self, key: str) -> bytes:
        """
        Download raw bytes from storage.

        Args:
            key: Object key

        Returns:
            Raw bytes
        """
        try:
            response = self.client.get_object(self.bucket, key)
            data = response.read()
            response.close()
            response.release_conn()

            return data

        except S3Error as e:
            logger.error(f"Failed to download bytes: {e}")
            raise

    def delete(self, key: str) -> None:
        """Delete an object from storage."""
        try:
            self.client.remove_object(self.bucket, key)
        except S3Error as e:
            logger.error(f"Failed to delete object: {e}")
            raise

    def list_objects(self, prefix: str = "") -> list[str]:
        """
        List objects with a given prefix.

        Args:
            prefix: Key prefix to filter by

        Returns:
            List of object keys
        """
        try:
            objects = self.client.list_objects(self.bucket, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Failed to list objects: {e}")
            raise

    def generate_presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access.

        Args:
            key: Object key
            expires_seconds: URL expiration time

        Returns:
            Presigned URL
        """
        try:
            from datetime import timedelta

            url = self.client.presigned_get_object(
                self.bucket, key, expires=timedelta(seconds=expires_seconds)
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
