"""
S3 storage adapter.
"""

import json
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

from evenage.storage.base import StorageAdapter, StorageConfig


class S3Adapter(StorageAdapter):
    """AWS S3 storage adapter."""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        
        self.client = boto3.client(
            's3',
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region,
            endpoint_url=config.endpoint
        )
        
        self.bucket_name = config.bucket
        self._ensure_bucket()
    
    def _ensure_bucket(self) -> None:
        """Ensure the bucket exists."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket_name)
    
    def upload_bytes(self, key: str, data: bytes, metadata: Optional[Dict[str, str]] = None) -> str:
        """Upload binary data to S3."""
        extra_args = {}
        if metadata:
            extra_args['Metadata'] = metadata
        
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            **extra_args
        )
        
        return f"s3://{self.bucket_name}/{key}"
    
    def download_bytes(self, key: str) -> bytes:
        """Download binary data from S3."""
        response = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return response['Body'].read()
    
    def upload_json(self, key: str, data: Dict[str, Any]) -> str:
        """Upload JSON data to S3."""
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        return self.upload_bytes(key, json_bytes, {"Content-Type": "application/json"})
    
    def download_json(self, key: str) -> Dict[str, Any]:
        """Download JSON data from S3."""
        data = self.download_bytes(key)
        return json.loads(data.decode("utf-8"))
    
    def delete(self, key: str) -> bool:
        """Delete an object from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except:
            return False
    
    def exists(self, key: str) -> bool:
        """Check if object exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except:
            return False
    
    def list_objects(self, prefix: str = "") -> list[str]:
        """List objects with optional prefix."""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except:
            return []
