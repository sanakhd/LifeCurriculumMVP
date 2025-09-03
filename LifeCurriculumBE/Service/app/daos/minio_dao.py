"""
MinIO Data Access Object for audio file management
"""
import base64
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from io import BytesIO
from minio import Minio
from minio.error import S3Error
from fastapi import HTTPException

from app.config import get_settings
from app.logger import get_logger
from app.models.minio_models import (
    AudioBucket,
    MinioUploadRequest,
    MinioUploadResponse,
    MinioDownloadRequest,
    MinioDownloadResponse,
    MinioListObjectsRequest,
    MinioListObjectsResponse,
    MinioObjectInfo,
    MinioDeleteRequest,
    MinioDeleteResponse,
    MinioPresignedUrlRequest,
    MinioPresignedUrlResponse,
    MinioObjectExistsRequest,
    MinioObjectExistsResponse
)

logger = get_logger(__name__)


class MinioDAO:
    """Standalone DAO for MinIO audio file operations"""
    
    def __init__(self):
        """Initialize MinIO DAO with configuration"""
        logger.debug("Initializing MinIO DAO")
        self.settings = get_settings()
        
        # Validate MinIO configuration
        if not self.settings.minio_endpoint:
            logger.error("MinIO endpoint not configured")
            raise ValueError("MinIO endpoint not configured. Please set MINIO_ENDPOINT environment variable.")
        
        if not self.settings.minio_access_key or not self.settings.minio_secret_key:
            logger.error("MinIO credentials not configured")
            raise ValueError("MinIO credentials not configured. Please set MINIO_ACCESS_KEY and MINIO_SECRET_KEY environment variables.")
        
        logger.debug(f"MinIO configuration found - endpoint: {self.settings.minio_endpoint}, secure: {self.settings.minio_secure}")
        
        try:
            # Initialize MinIO client
            self.client = Minio(
                endpoint=self.settings.minio_endpoint,
                access_key=self.settings.minio_access_key,
                secret_key=self.settings.minio_secret_key,
                secure=self.settings.minio_secure
            )
            
            logger.debug("MinIO client initialized, ensuring buckets exist")
            # Initialize buckets
            self._ensure_buckets_exist()
            logger.info("MinIO DAO initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to initialize MinIO client")
    
    def _get_bucket_name(self, bucket: AudioBucket) -> str:
        """Get the actual bucket name from AudioBucket enum"""
        if bucket == AudioBucket.GENERATED:
            return self.settings.minio_generated_audio_bucket
        elif bucket == AudioBucket.RECORDED:
            return self.settings.minio_recorded_audio_bucket
        else:
            raise ValueError(f"Unknown bucket type: {bucket}")
    
    def _ensure_buckets_exist(self):
        """Ensure both audio buckets exist, create if they don't"""
        try:
            for bucket_enum in AudioBucket:
                bucket_name = self._get_bucket_name(bucket_enum)
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    logger.info(f"Created MinIO bucket: {bucket_name}")
                else:
                    logger.info(f"MinIO bucket already exists: {bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to ensure buckets exist: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to initialize MinIO buckets")
    
    def _prepare_audio_data(self, audio_data: Union[bytes, str]) -> bytes:
        """Prepare audio data for upload"""
        if isinstance(audio_data, str):
            # Assume base64 encoded string
            try:
                return base64.b64decode(audio_data)
            except Exception as e:
                logger.error(f"Failed to decode base64 audio data: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid base64 audio data")
        elif isinstance(audio_data, bytes):
            return audio_data
        else:
            raise HTTPException(status_code=400, detail="Audio data must be bytes or base64 string")

    async def upload_audio(
        self,
        request: MinioUploadRequest
    ) -> MinioUploadResponse:
        """
        Upload audio file to MinIO bucket
        
        Args:
            request: MinioUploadRequest with audio data and metadata
            
        Returns:
            MinioUploadResponse with upload details
            
        Raises:
            HTTPException: On MinIO errors or configuration issues
        """
        logger.info(f"Processing audio upload to bucket: {request.bucket.value}, object: {request.object_name}")
        
        try:
            bucket_name = self._get_bucket_name(request.bucket)
            logger.debug(f"Resolved bucket name: {bucket_name}")
            
            audio_bytes = self._prepare_audio_data(request.audio_data)
            logger.debug(f"Prepared audio data, size: {len(audio_bytes)} bytes")
            
            # Create BytesIO object from audio data
            audio_stream = BytesIO(audio_bytes)
            data_size = len(audio_bytes)
            
            logger.debug(f"Uploading to MinIO - bucket: {bucket_name}, object: {request.object_name}, content_type: {request.content_type}")
            
            # Upload to MinIO
            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=request.object_name,
                data=audio_stream,
                length=data_size,
                content_type=request.content_type,
                metadata=request.metadata or {}
            )
            
            logger.info(f"Successfully uploaded audio file, etag: {result.etag}")
            
            # Generate presigned URL for quick access
            presigned_url = None
            try:
                logger.debug("Generating presigned URL for uploaded file")
                presigned_url = self.client.presigned_get_object(
                    bucket_name=bucket_name,
                    object_name=request.object_name,
                    expires=timedelta(hours=1)
                )
                logger.debug("Successfully generated presigned URL")
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for {request.object_name}: {str(e)}")
            
            response = MinioUploadResponse(
                object_name=request.object_name,
                bucket=bucket_name,
                size=data_size,
                etag=result.etag,
                content_type=request.content_type,
                upload_time=datetime.utcnow(),
                presigned_url=presigned_url
            )
            
            logger.info(f"Audio upload completed successfully for {request.object_name}")
            return response
            
        except S3Error as e:
            logger.error(f"MinIO upload error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO upload error: {str(e)}")
        except Exception as e:
            logger.error(f"Audio upload error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio upload error: {str(e)}")

    async def download_audio(
        self,
        request: MinioDownloadRequest
    ) -> MinioDownloadResponse:
        """
        Download audio file from MinIO bucket
        
        Args:
            request: MinioDownloadRequest with object name and bucket
            
        Returns:
            MinioDownloadResponse with audio data and metadata
            
        Raises:
            HTTPException: On MinIO errors or if object doesn't exist
        """
        logger.info(f"Processing audio download from bucket: {request.bucket.value}, object: {request.object_name}")
        
        try:
            bucket_name = self._get_bucket_name(request.bucket)
            logger.debug(f"Resolved bucket name: {bucket_name}")
            
            # Get object stat for metadata
            logger.debug(f"Checking object existence and getting metadata for {request.object_name}")
            try:
                stat = self.client.stat_object(bucket_name, request.object_name)
                logger.debug(f"Object found - size: {stat.size} bytes, content_type: {stat.content_type}")
            except S3Error as e:
                if e.code == "NoSuchKey":
                    logger.warning(f"Audio file not found: {request.object_name}")
                    raise HTTPException(status_code=404, detail=f"Audio file not found: {request.object_name}")
                raise
            
            # Download object
            logger.debug(f"Downloading object data from MinIO")
            response = self.client.get_object(bucket_name, request.object_name)
            audio_data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Successfully downloaded audio file, size: {len(audio_data)} bytes")
            
            download_response = MinioDownloadResponse(
                object_name=request.object_name,
                bucket=bucket_name,
                audio_data=audio_data,
                content_type=stat.content_type or "application/octet-stream",
                size=stat.size,
                last_modified=stat.last_modified,
                metadata=stat.metadata
            )
            
            logger.info(f"Audio download completed successfully for {request.object_name}")
            return download_response
            
        except HTTPException:
            raise
        except S3Error as e:
            logger.error(f"MinIO download error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO download error: {str(e)}")
        except Exception as e:
            logger.error(f"Audio download error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio download error: {str(e)}")

    async def list_audio_files(
        self,
        request: MinioListObjectsRequest
    ) -> MinioListObjectsResponse:
        """
        List audio files in MinIO bucket
        
        Args:
            request: MinioListObjectsRequest with bucket and optional filters
            
        Returns:
            MinioListObjectsResponse with list of objects
            
        Raises:
            HTTPException: On MinIO errors
        """
        logger.info(f"Processing list audio files request for bucket: {request.bucket.value}")
        
        try:
            bucket_name = self._get_bucket_name(request.bucket)
            logger.debug(f"Resolved bucket name: {bucket_name}")
            logger.debug(f"List parameters - prefix: {request.prefix}, recursive: {request.recursive}, max_objects: {request.max_objects}")
            
            # List objects
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=request.prefix,
                recursive=request.recursive
            )
            
            object_info_list = []
            count = 0
            
            for obj in objects:
                if request.max_objects and count >= request.max_objects:
                    logger.debug(f"Reached max objects limit: {request.max_objects}")
                    break
                
                # Get additional object metadata
                try:
                    stat = self.client.stat_object(bucket_name, obj.object_name)
                    metadata = stat.metadata
                    content_type = stat.content_type
                    logger.debug(f"Got metadata for object {obj.object_name}: size={stat.size}, type={content_type}")
                except Exception as e:
                    logger.warning(f"Failed to get metadata for {obj.object_name}: {str(e)}")
                    metadata = None
                    content_type = None
                
                object_info_list.append(MinioObjectInfo(
                    object_name=obj.object_name,
                    size=obj.size or 0,
                    last_modified=obj.last_modified,
                    etag=obj.etag or "",
                    content_type=content_type,
                    metadata=metadata
                ))
                count += 1
            
            logger.info(f"Successfully listed {len(object_info_list)} audio files from bucket {request.bucket.value}")
            
            return MinioListObjectsResponse(
                bucket=bucket_name,
                objects=object_info_list,
                total_objects=len(object_info_list),
                prefix=request.prefix
            )
            
        except S3Error as e:
            logger.error(f"MinIO list objects error for bucket {request.bucket.value}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO list objects error: {str(e)}")
        except Exception as e:
            logger.error(f"Audio list error for bucket {request.bucket.value}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio list error: {str(e)}")

    async def delete_audio(
        self,
        request: MinioDeleteRequest
    ) -> MinioDeleteResponse:
        """
        Delete audio file from MinIO bucket
        
        Args:
            request: MinioDeleteRequest with object name and bucket
            
        Returns:
            MinioDeleteResponse with deletion status
            
        Raises:
            HTTPException: On MinIO errors
        """
        logger.info(f"Processing audio deletion from bucket: {request.bucket.value}, object: {request.object_name}")
        
        try:
            bucket_name = self._get_bucket_name(request.bucket)
            logger.debug(f"Resolved bucket name: {bucket_name}")
            
            # Check if object exists first
            logger.debug(f"Checking if object exists before deletion: {request.object_name}")
            try:
                self.client.stat_object(bucket_name, request.object_name)
                logger.debug("Object exists, proceeding with deletion")
            except S3Error as e:
                if e.code == "NoSuchKey":
                    logger.warning(f"Audio file not found for deletion: {request.object_name}")
                    return MinioDeleteResponse(
                        object_name=request.object_name,
                        bucket=bucket_name,
                        deleted=False,
                        message="Audio file not found"
                    )
                raise
            
            # Delete object
            logger.debug(f"Deleting object from MinIO: {request.object_name}")
            self.client.remove_object(bucket_name, request.object_name)
            
            logger.info(f"Successfully deleted audio file: {request.object_name}")
            
            return MinioDeleteResponse(
                object_name=request.object_name,
                bucket=bucket_name,
                deleted=True,
                message="Audio file deleted successfully"
            )
            
        except S3Error as e:
            logger.error(f"MinIO delete error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO delete error: {str(e)}")
        except Exception as e:
            logger.error(f"Audio delete error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio delete error: {str(e)}")

    async def get_presigned_url(
        self,
        request: MinioPresignedUrlRequest
    ) -> MinioPresignedUrlResponse:
        """
        Generate presigned URL for direct object access
        
        Args:
            request: MinioPresignedUrlRequest with object details
            
        Returns:
            MinioPresignedUrlResponse with presigned URL
            
        Raises:
            HTTPException: On MinIO errors
        """
        logger.info(f"Generating presigned URL for bucket: {request.bucket.value}, object: {request.object_name}, method: {request.method}")
        
        try:
            bucket_name = self._get_bucket_name(request.bucket)
            expires = timedelta(seconds=request.expires_in_seconds)
            
            logger.debug(f"Presigned URL parameters - bucket: {bucket_name}, expires: {request.expires_in_seconds}s")
            
            if request.method.upper() == "GET":
                logger.debug("Generating GET presigned URL")
                presigned_url = self.client.presigned_get_object(
                    bucket_name=bucket_name,
                    object_name=request.object_name,
                    expires=expires
                )
            elif request.method.upper() == "PUT":
                logger.debug("Generating PUT presigned URL")
                presigned_url = self.client.presigned_put_object(
                    bucket_name=bucket_name,
                    object_name=request.object_name,
                    expires=expires
                )
            else:
                logger.error(f"Invalid presigned URL method: {request.method}")
                raise HTTPException(status_code=400, detail="Method must be GET or PUT")
            
            logger.info(f"Successfully generated presigned URL for {request.object_name}")
            
            return MinioPresignedUrlResponse(
                object_name=request.object_name,
                bucket=bucket_name,
                presigned_url=presigned_url,
                expires_in_seconds=request.expires_in_seconds,
                method=request.method.upper()
            )
            
        except S3Error as e:
            logger.error(f"MinIO presigned URL error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO presigned URL error: {str(e)}")
        except Exception as e:
            logger.error(f"Presigned URL error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Presigned URL error: {str(e)}")

    async def check_object_exists(
        self,
        request: MinioObjectExistsRequest
    ) -> MinioObjectExistsResponse:
        """
        Check if audio file exists in MinIO bucket
        
        Args:
            request: MinioObjectExistsRequest with object name and bucket
            
        Returns:
            MinioObjectExistsResponse with existence status
            
        Raises:
            HTTPException: On MinIO errors
        """
        logger.info(f"Checking object existence in bucket: {request.bucket.value}, object: {request.object_name}")
        
        try:
            bucket_name = self._get_bucket_name(request.bucket)
            logger.debug(f"Resolved bucket name: {bucket_name}")
            
            try:
                stat = self.client.stat_object(bucket_name, request.object_name)
                logger.info(f"Object exists - size: {stat.size} bytes, last_modified: {stat.last_modified}")
                return MinioObjectExistsResponse(
                    object_name=request.object_name,
                    bucket=bucket_name,
                    exists=True,
                    size=stat.size,
                    last_modified=stat.last_modified
                )
            except S3Error as e:
                if e.code == "NoSuchKey":
                    logger.info(f"Object does not exist: {request.object_name}")
                    return MinioObjectExistsResponse(
                        object_name=request.object_name,
                        bucket=bucket_name,
                        exists=False
                    )
                raise
            
        except S3Error as e:
            logger.error(f"MinIO object exists check error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO object exists check error: {str(e)}")
        except Exception as e:
            logger.error(f"Object exists check error for object {request.object_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Object exists check error: {str(e)}")

    async def get_bucket_info(self, bucket: AudioBucket) -> Dict[str, Any]:
        """
        Get information about a bucket
        
        Args:
            bucket: AudioBucket enum value
            
        Returns:
            Dictionary with bucket information
            
        Raises:
            HTTPException: On MinIO errors
        """
        logger.info(f"Getting bucket information for: {bucket.value}")
        
        try:
            bucket_name = self._get_bucket_name(bucket)
            logger.debug(f"Resolved bucket name: {bucket_name}")
            
            # Count objects and calculate total size
            logger.debug("Scanning bucket objects to calculate statistics")
            objects = self.client.list_objects(bucket_name, recursive=True)
            total_objects = 0
            total_size = 0
            
            for obj in objects:
                total_objects += 1
                total_size += obj.size or 0
            
            bucket_exists = self.client.bucket_exists(bucket_name)
            
            logger.info(f"Bucket info collected - objects: {total_objects}, size: {round(total_size / (1024 * 1024), 2)} MB, exists: {bucket_exists}")
            
            return {
                "bucket_name": bucket_name,
                "bucket_type": bucket.value,
                "total_objects": total_objects,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "exists": bucket_exists
            }
            
        except S3Error as e:
            logger.error(f"MinIO bucket info error for bucket {bucket.value}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MinIO bucket info error: {str(e)}")
        except Exception as e:
            logger.error(f"Bucket info error for bucket {bucket.value}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Bucket info error: {str(e)}")
