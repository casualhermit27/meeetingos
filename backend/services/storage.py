"""
Storage service for handling file uploads to Supabase Storage or S3
"""

import asyncio
import io
import logging
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union, BinaryIO
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from supabase import create_client, Client
from fastapi import UploadFile
import httpx

from ..config import Settings
from ..utils.error_handler import StorageError

logger = logging.getLogger(__name__)


class StorageService:
    """Service for handling file storage operations"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.storage_provider.lower()
        
        # Initialize storage clients
        self.supabase_client: Optional[Client] = None
        self.s3_client = None
        
        # Storage configuration
        self.bucket_name = settings.storage_bucket
        self.max_file_size = settings.max_file_size_bytes
        self.chunk_size = settings.chunk_size_bytes
    
    async def initialize(self):
        """Initialize storage service based on provider"""
        try:
            if self.provider == "supabase":
                await self._initialize_supabase()
            elif self.provider == "s3":
                await self._initialize_s3()
            else:
                raise StorageError(f"Unsupported storage provider: {self.provider}")
            
            logger.info(f"Storage service initialized with provider: {self.provider}")
            
        except Exception as e:
            logger.error(f"Failed to initialize storage service: {str(e)}")
            raise StorageError(f"Storage initialization failed: {str(e)}")
    
    async def _initialize_supabase(self):
        """Initialize Supabase client"""
        try:
            self.supabase_client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_key
            )
            
            # Test connection
            response = self.supabase_client.storage.list_buckets()
            logger.info("Supabase storage connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {str(e)}")
            raise StorageError(f"Supabase initialization failed: {str(e)}")
    
    async def _initialize_s3(self):
        """Initialize S3 client"""
        try:
            if not self.settings.aws_access_key_id or not self.settings.aws_secret_access_key:
                raise StorageError("AWS credentials not configured")
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region
            )
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.settings.s3_bucket or self.bucket_name)
            logger.info("S3 storage connection established")
            
        except NoCredentialsError:
            raise StorageError("AWS credentials not found")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise StorageError(f"S3 bucket not found: {self.bucket_name}")
            else:
                raise StorageError(f"S3 connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to initialize S3: {str(e)}")
            raise StorageError(f"S3 initialization failed: {str(e)}")
    
    async def upload_file(self, file: UploadFile, storage_path: str) -> str:
        """
        Upload a file to storage
        
        Args:
            file: FastAPI UploadFile object
            storage_path: Path in storage (e.g., "recordings/user_id/file.mp4")
            
        Returns:
            URL of the uploaded file
        """
        try:
            # Validate file size
            if file.size and file.size > self.max_file_size:
                raise StorageError(f"File size exceeds maximum allowed ({self.max_file_size} bytes)")
            
            # Read file content
            content = await file.read()
            
            # Reset file pointer for potential reuse
            await file.seek(0)
            
            # Upload based on provider
            if self.provider == "supabase":
                return await self._upload_to_supabase(content, storage_path, file.content_type)
            elif self.provider == "s3":
                return await self._upload_to_s3(content, storage_path, file.content_type)
            else:
                raise StorageError(f"Unsupported storage provider: {self.provider}")
            
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise StorageError(f"Upload failed: {str(e)}")
    
    async def upload_file_stream(self, file_stream: BinaryIO, storage_path: str, 
                               file_size: Optional[int] = None) -> str:
        """
        Upload a file from a stream
        
        Args:
            file_stream: File-like object to read from
            storage_path: Path in storage
            file_size: Optional file size
            
        Returns:
            URL of the uploaded file
        """
        try:
            # Read content from stream
            content = file_stream.read()
            
            # Validate file size
            if file_size and len(content) != file_size:
                logger.warning(f"File size mismatch: expected {file_size}, got {len(content)}")
            
            if len(content) > self.max_file_size:
                raise StorageError(f"File size exceeds maximum allowed ({self.max_file_size} bytes)")
            
            # Determine content type
            content_type = self._get_content_type(storage_path)
            
            # Upload based on provider
            if self.provider == "supabase":
                return await self._upload_to_supabase(content, storage_path, content_type)
            elif self.provider == "s3":
                return await self._upload_to_s3(content, storage_path, content_type)
            else:
                raise StorageError(f"Unsupported storage provider: {self.provider}")
            
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"Stream upload failed: {str(e)}")
            raise StorageError(f"Stream upload failed: {str(e)}")
    
    async def _upload_to_supabase(self, content: bytes, storage_path: str, 
                                content_type: Optional[str] = None) -> str:
        """
        Upload file to Supabase Storage
        
        Args:
            content: File content as bytes
            storage_path: Path in storage
            content_type: MIME type
            
        Returns:
            Public URL of the uploaded file
        """
        try:
            # Upload file
            response = self.supabase_client.storage.from_(self.bucket_name).upload(
                file=content,
                path=storage_path,
                file_options={
                    "content-type": content_type or "application/octet-stream",
                    "cache-control": "3600"
                }
            )
            
            if hasattr(response, 'error') and response.error:
                raise StorageError(f"Supabase upload failed: {response.error}")
            
            # Get public URL
            public_url = self.supabase_client.storage.from_(self.bucket_name).get_public_url(storage_path)
            
            logger.info(f"File uploaded to Supabase: {storage_path}")
            return public_url
            
        except Exception as e:
            logger.error(f"Supabase upload failed: {str(e)}")
            raise StorageError(f"Supabase upload failed: {str(e)}")
    
    async def _upload_to_s3(self, content: bytes, storage_path: str, 
                          content_type: Optional[str] = None) -> str:
        """
        Upload file to S3
        
        Args:
            content: File content as bytes
            storage_path: Path in storage
            content_type: MIME type
            
        Returns:
            Public URL of the uploaded file
        """
        try:
            bucket_name = self.settings.s3_bucket or self.bucket_name
            
            # Upload parameters
            upload_params = {
                'Bucket': bucket_name,
                'Key': storage_path,
                'Body': content,
                'ContentType': content_type or 'application/octet-stream',
                'CacheControl': 'max-age=3600'
            }
            
            # Upload file
            self.s3_client.put_object(**upload_params)
            
            # Generate public URL
            public_url = f"https://{bucket_name}.s3.{self.settings.aws_region}.amazonaws.com/{storage_path}"
            
            logger.info(f"File uploaded to S3: {storage_path}")
            return public_url
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise StorageError(f"S3 upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise StorageError(f"S3 upload error: {str(e)}")
    
    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            storage_path: Path to the file in storage
            
        Returns:
            True if deletion was successful
        """
        try:
            if self.provider == "supabase":
                return await self._delete_from_supabase(storage_path)
            elif self.provider == "s3":
                return await self._delete_from_s3(storage_path)
            else:
                raise StorageError(f"Unsupported storage provider: {self.provider}")
            
        except Exception as e:
            logger.error(f"File deletion failed: {str(e)}")
            raise StorageError(f"Deletion failed: {str(e)}")
    
    async def _delete_from_supabase(self, storage_path: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            response = self.supabase_client.storage.from_(self.bucket_name).remove([storage_path])
            
            if hasattr(response, 'error') and response.error:
                raise StorageError(f"Supabase deletion failed: {response.error}")
            
            logger.info(f"File deleted from Supabase: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Supabase deletion failed: {str(e)}")
            return False
    
    async def _delete_from_s3(self, storage_path: str) -> bool:
        """Delete file from S3"""
        try:
            bucket_name = self.settings.s3_bucket or self.bucket_name
            
            self.s3_client.delete_object(
                Bucket=bucket_name,
                Key=storage_path
            )
            
            logger.info(f"File deleted from S3: {storage_path}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 deletion failed: {str(e)}")
            return False
    
    async def file_exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in storage
        
        Args:
            storage_path: Path to the file in storage
            
        Returns:
            True if file exists
        """
        try:
            if self.provider == "supabase":
                return await self._file_exists_supabase(storage_path)
            elif self.provider == "s3":
                return await self._file_exists_s3(storage_path)
            else:
                return False
            
        except Exception as e:
            logger.error(f"File existence check failed: {str(e)}")
            return False
    
    async def _file_exists_supabase(self, storage_path: str) -> bool:
        """Check if file exists in Supabase Storage"""
        try:
            # Try to get file info
            response = self.supabase_client.storage.from_(self.bucket_name).list(
                path=str(Path(storage_path).parent),
                limit=1000
            )
            
            if hasattr(response, 'error') and response.error:
                return False
            
            # Check if file is in the list
            filename = Path(storage_path).name
            for item in response:
                if item.get('name') == filename:
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def _file_exists_s3(self, storage_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            bucket_name = self.settings.s3_bucket or self.bucket_name
            
            self.s3_client.head_object(
                Bucket=bucket_name,
                Key=storage_path
            )
            
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
        except Exception:
            return False
    
    async def get_download_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Generate a signed download URL
        
        Args:
            storage_path: Path to the file in storage
            expires_in: URL expiration time in seconds
            
        Returns:
            Signed download URL
        """
        try:
            if self.provider == "supabase":
                return await self._get_supabase_download_url(storage_path, expires_in)
            elif self.provider == "s3":
                return await self._get_s3_download_url(storage_path, expires_in)
            else:
                raise StorageError(f"Unsupported storage provider: {self.provider}")
            
        except Exception as e:
            logger.error(f"Download URL generation failed: {str(e)}")
            raise StorageError(f"Download URL generation failed: {str(e)}")
    
    async def _get_supabase_download_url(self, storage_path: str, expires_in: int) -> str:
        """Generate signed download URL for Supabase"""
        try:
            # For Supabase, we can use the signed URL method
            response = self.supabase_client.storage.from_(self.bucket_name).create_signed_url(
                path=storage_path,
                expires_in=expires_in
            )
            
            if hasattr(response, 'error') and response.error:
                raise StorageError(f"Supabase signed URL failed: {response.error}")
            
            return response.get('signedURL', '')
            
        except Exception as e:
            # Fallback to public URL if signed URL fails
            logger.warning(f"Signed URL failed, using public URL: {str(e)}")
            return self.supabase_client.storage.from_(self.bucket_name).get_public_url(storage_path)
    
    async def _get_s3_download_url(self, storage_path: str, expires_in: int) -> str:
        """Generate signed download URL for S3"""
        try:
            bucket_name = self.settings.s3_bucket or self.bucket_name
            
            signed_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': storage_path},
                ExpiresIn=expires_in
            )
            
            return signed_url
            
        except Exception as e:
            logger.error(f"S3 signed URL generation failed: {str(e)}")
            raise StorageError(f"S3 signed URL failed: {str(e)}")
    
    async def get_file_info(self, storage_path: str) -> Optional[dict]:
        """
        Get file information from storage
        
        Args:
            storage_path: Path to the file in storage
            
        Returns:
            Dictionary containing file information or None if not found
        """
        try:
            if self.provider == "supabase":
                return await self._get_supabase_file_info(storage_path)
            elif self.provider == "s3":
                return await self._get_s3_file_info(storage_path)
            else:
                return None
            
        except Exception as e:
            logger.error(f"File info retrieval failed: {str(e)}")
            return None
    
    async def _get_supabase_file_info(self, storage_path: str) -> Optional[dict]:
        """Get file info from Supabase Storage"""
        try:
            # Get file list from parent directory
            parent_path = str(Path(storage_path).parent)
            response = self.supabase_client.storage.from_(self.bucket_name).list(path=parent_path)
            
            if hasattr(response, 'error') and response.error:
                return None
            
            # Find the specific file
            filename = Path(storage_path).name
            for item in response:
                if item.get('name') == filename:
                    return {
                        'name': item.get('name'),
                        'size': item.get('metadata', {}).get('size'),
                        'updated_at': item.get('updated_at'),
                        'content_type': item.get('metadata', {}).get('mimetype')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Supabase file info failed: {str(e)}")
            return None
    
    async def _get_s3_file_info(self, storage_path: str) -> Optional[dict]:
        """Get file info from S3"""
        try:
            bucket_name = self.settings.s3_bucket or self.bucket_name
            
            response = self.s3_client.head_object(
                Bucket=bucket_name,
                Key=storage_path
            )
            
            return {
                'name': Path(storage_path).name,
                'size': response.get('ContentLength'),
                'updated_at': response.get('LastModified'),
                'content_type': response.get('ContentType')
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            logger.error(f"S3 file info failed: {str(e)}")
            return None
    
    def _get_content_type(self, file_path: str) -> str:
        """
        Determine content type from file extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        content_type, _ = mimetypes.guess_type(file_path)
        
        if not content_type:
            # Default content types for common recording formats
            extension = Path(file_path).suffix.lower()
            content_type_map = {
                '.mp4': 'video/mp4',
                '.m4a': 'audio/mp4',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.webm': 'video/webm'
            }
            content_type = content_type_map.get(extension, 'application/octet-stream')
        
        return content_type
    
    async def cleanup(self):
        """Cleanup storage service resources"""
        try:
            if self.s3_client:
                # S3 client doesn't need explicit cleanup
                pass
            
            if self.supabase_client:
                # Supabase client doesn't need explicit cleanup
                pass
            
            logger.info("Storage service cleanup completed")
            
        except Exception as e:
            logger.error(f"Storage cleanup error: {str(e)}")
    
    def get_storage_stats(self) -> dict:
        """Get storage service statistics"""
        return {
            'provider': self.provider,
            'bucket': self.bucket_name,
            'max_file_size_mb': self.max_file_size // (1024 * 1024),
            'chunk_size_kb': self.chunk_size // 1024,
            'initialized': bool(self.supabase_client or self.s3_client)
        } 