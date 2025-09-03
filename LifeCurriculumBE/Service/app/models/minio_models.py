"""
Pydantic models for MinIO API requests and responses
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime


class AudioBucket(str, Enum):
    """Enum for audio bucket selection"""
    GENERATED = "generated"
    RECORDED = "recorded"


class MinioUploadRequest(BaseModel):
    """Request model for uploading audio to MinIO"""
    object_name: str
    audio_data: Union[bytes, str]  # bytes or base64 encoded string
    bucket: AudioBucket
    content_type: Optional[str] = "audio/wav"
    metadata: Optional[Dict[str, str]] = None


class MinioUploadResponse(BaseModel):
    """Response model for MinIO upload"""
    object_name: str
    bucket: str
    size: int
    etag: str
    content_type: str
    upload_time: datetime
    presigned_url: Optional[str] = None


class MinioDownloadRequest(BaseModel):
    """Request model for downloading audio from MinIO"""
    object_name: str
    bucket: AudioBucket


class MinioDownloadResponse(BaseModel):
    """Response model for MinIO download"""
    object_name: str
    bucket: str
    audio_data: bytes
    content_type: str
    size: int
    last_modified: datetime
    metadata: Optional[Dict[str, str]] = None


class MinioListObjectsRequest(BaseModel):
    """Request model for listing objects in MinIO bucket"""
    bucket: AudioBucket
    prefix: Optional[str] = None
    recursive: bool = True
    max_objects: Optional[int] = None


class MinioObjectInfo(BaseModel):
    """Model for object information in MinIO"""
    object_name: str
    size: int
    last_modified: datetime
    etag: str
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class MinioListObjectsResponse(BaseModel):
    """Response model for MinIO list objects"""
    bucket: str
    objects: List[MinioObjectInfo]
    total_objects: int
    prefix: Optional[str] = None


class MinioDeleteRequest(BaseModel):
    """Request model for deleting audio from MinIO"""
    object_name: str
    bucket: AudioBucket


class MinioDeleteResponse(BaseModel):
    """Response model for MinIO delete"""
    object_name: str
    bucket: str
    deleted: bool
    message: str


class MinioPresignedUrlRequest(BaseModel):
    """Request model for generating presigned URL"""
    object_name: str
    bucket: AudioBucket
    expires_in_seconds: Optional[int] = 3600  # 1 hour default
    method: Optional[str] = "GET"  # GET or PUT


class MinioPresignedUrlResponse(BaseModel):
    """Response model for presigned URL"""
    object_name: str
    bucket: str
    presigned_url: str
    expires_in_seconds: int
    method: str


class MinioObjectExistsRequest(BaseModel):
    """Request model for checking object existence"""
    object_name: str
    bucket: AudioBucket


class MinioObjectExistsResponse(BaseModel):
    """Response model for object existence check"""
    object_name: str
    bucket: str
    exists: bool
    size: Optional[int] = None
    last_modified: Optional[datetime] = None
