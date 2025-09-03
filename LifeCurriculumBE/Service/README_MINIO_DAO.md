# MinIO DAO Documentation

The MinIO DAO provides a comprehensive interface for managing audio files in MinIO object storage, specifically designed for the LifeCurriculum service's audio handling needs.

## Overview

The `MinioDAO` class handles all interactions with MinIO object storage for audio file management. It supports two predefined buckets:
- `lc-generated-audio` - For AI-generated audio files
- `lc-recorded-user-audio` - For user-recorded audio files

## Features

- **Upload Audio**: Store audio files with metadata and automatic content-type detection
- **Download Audio**: Retrieve audio files with full metadata
- **List Objects**: Browse and filter audio files in buckets
- **Delete Audio**: Remove audio files from storage
- **Presigned URLs**: Generate secure URLs for direct access/upload
- **Object Existence Check**: Verify if files exist before operations
- **Bucket Management**: Automatic bucket creation and information retrieval
- **Multiple Data Formats**: Support for both raw bytes and base64 encoded audio

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password
MINIO_SECURE=false
MINIO_GENERATED_AUDIO_BUCKET=lc-generated-audio
MINIO_RECORDED_AUDIO_BUCKET=lc-recorded-user-audio
```

### Prerequisites

1. **MinIO Server**: Ensure MinIO is running and accessible
2. **Python Dependencies**: Install the minio package
   ```bash
   pip install minio>=7.2.0
   ```

## Quick Start

```python
import asyncio
from app.daos.minio_dao import MinioDAO
from app.models.minio_models import (
    AudioBucket,
    MinioUploadRequest,
    MinioDownloadRequest
)

async def main():
    # Initialize DAO
    dao = MinioDAO()
    
    # Upload audio
    with open("audio.wav", "rb") as f:
        audio_data = f.read()
    
    upload_request = MinioUploadRequest(
        object_name="my_audio.wav",
        audio_data=audio_data,
        bucket=AudioBucket.GENERATED,
        content_type="audio/wav",
        metadata={"source": "tts", "duration": "10s"}
    )
    
    result = await dao.upload_audio(upload_request)
    print(f"Uploaded: {result.object_name}")
    
    # Download audio
    download_request = MinioDownloadRequest(
        object_name="my_audio.wav",
        bucket=AudioBucket.GENERATED
    )
    
    audio_result = await dao.download_audio(download_request)
    
    # Save downloaded audio
    with open("downloaded_audio.wav", "wb") as f:
        f.write(audio_result.audio_data)

asyncio.run(main())
```

## API Reference

### Core Methods

#### `upload_audio(request: MinioUploadRequest) -> MinioUploadResponse`

Upload audio files to MinIO buckets.

**Parameters:**
- `object_name`: Unique name for the audio file
- `audio_data`: Raw bytes or base64 encoded string
- `bucket`: `AudioBucket.GENERATED` or `AudioBucket.RECORDED`
- `content_type`: MIME type (default: "audio/wav")
- `metadata`: Optional dictionary of custom metadata

**Returns:**
- Upload confirmation with object details and optional presigned URL

**Example:**
```python
request = MinioUploadRequest(
    object_name="speech_2024_01_15.wav",
    audio_data=audio_bytes,
    bucket=AudioBucket.GENERATED,
    content_type="audio/wav",
    metadata={
        "speaker": "assistant",
        "language": "en",
        "duration_seconds": "30"
    }
)
result = await dao.upload_audio(request)
```

#### `download_audio(request: MinioDownloadRequest) -> MinioDownloadResponse`

Download audio files from MinIO buckets.

**Parameters:**
- `object_name`: Name of the audio file to download
- `bucket`: Target bucket

**Returns:**
- Audio data, metadata, and file information

**Example:**
```python
request = MinioDownloadRequest(
    object_name="speech_2024_01_15.wav",
    bucket=AudioBucket.GENERATED
)
result = await dao.download_audio(request)

# Access audio data
audio_data = result.audio_data
metadata = result.metadata
```

#### `list_audio_files(request: MinioListObjectsRequest) -> MinioListObjectsResponse`

List and filter audio files in buckets.

**Parameters:**
- `bucket`: Target bucket
- `prefix`: Optional filter by object name prefix
- `recursive`: Include subdirectories (default: True)
- `max_objects`: Limit number of results

**Returns:**
- List of objects with metadata

**Example:**
```python
request = MinioListObjectsRequest(
    bucket=AudioBucket.RECORDED,
    prefix="user_123/",
    max_objects=50
)
result = await dao.list_audio_files(request)

for obj in result.objects:
    print(f"{obj.object_name}: {obj.size} bytes")
```

#### `delete_audio(request: MinioDeleteRequest) -> MinioDeleteResponse`

Delete audio files from MinIO buckets.

**Parameters:**
- `object_name`: Name of the file to delete
- `bucket`: Target bucket

**Returns:**
- Deletion status and confirmation message

#### `get_presigned_url(request: MinioPresignedUrlRequest) -> MinioPresignedUrlResponse`

Generate presigned URLs for secure direct access.

**Parameters:**
- `object_name`: Target object name
- `bucket`: Target bucket
- `expires_in_seconds`: URL expiration time (default: 3600)
- `method`: "GET" for download, "PUT" for upload

**Returns:**
- Presigned URL and expiration details

**Example:**
```python
# Generate download URL
request = MinioPresignedUrlRequest(
    object_name="public_speech.wav",
    bucket=AudioBucket.GENERATED,
    expires_in_seconds=7200,  # 2 hours
    method="GET"
)
result = await dao.get_presigned_url(request)

# URL can be shared for direct download
download_url = result.presigned_url
```

### Utility Methods

#### `check_object_exists(request: MinioObjectExistsRequest) -> MinioObjectExistsResponse`

Verify if an audio file exists before performing operations.

#### `get_bucket_info(bucket: AudioBucket) -> Dict[str, Any]`

Get comprehensive bucket statistics and information.

**Returns:**
```python
{
    "bucket_name": "lc-generated-audio",
    "bucket_type": "generated",
    "total_objects": 150,
    "total_size_bytes": 52428800,
    "total_size_mb": 50.0,
    "exists": True
}
```

## Data Models

### AudioBucket Enum
- `AudioBucket.GENERATED`: For AI-generated audio
- `AudioBucket.RECORDED`: For user-recorded audio

### Request Models
- `MinioUploadRequest`: Upload parameters
- `MinioDownloadRequest`: Download parameters  
- `MinioListObjectsRequest`: List/filter parameters
- `MinioDeleteRequest`: Delete parameters
- `MinioPresignedUrlRequest`: URL generation parameters
- `MinioObjectExistsRequest`: Existence check parameters

### Response Models
- `MinioUploadResponse`: Upload results and metadata
- `MinioDownloadResponse`: Audio data and file information
- `MinioListObjectsResponse`: Object listings
- `MinioDeleteResponse`: Deletion confirmation
- `MinioPresignedUrlResponse`: Generated URL details
- `MinioObjectExistsResponse`: Existence status

## Error Handling

The DAO provides comprehensive error handling:

- **Configuration Errors**: Missing MinIO credentials or endpoint
- **Connection Errors**: MinIO server unavailable
- **Not Found**: Object or bucket doesn't exist (404)
- **Permission Errors**: Access denied
- **Storage Errors**: Insufficient space or quota exceeded
- **Data Validation**: Invalid audio data or parameters

All errors are wrapped in FastAPI `HTTPException` with appropriate status codes.

## Best Practices

### File Naming
Use descriptive, unique names with proper extensions:
```python
# Good
"user_123_recording_2024_01_15_14_30.wav"
"tts_response_session_456.mp3"

# Avoid
"audio1.wav"
"temp.mp3"
```

### Metadata Usage
Include useful metadata for better file management:
```python
metadata = {
    "user_id": "123",
    "session_id": "session_456",
    "source": "microphone",
    "duration_seconds": "45",
    "sample_rate": "44100",
    "channels": "1",
    "created_by": "user_upload_api"
}
```

### Security Considerations

1. **Presigned URLs**: Use short expiration times for sensitive content
2. **Access Control**: Validate user permissions before operations
3. **File Validation**: Verify file types and sizes before upload
4. **Metadata Sanitization**: Clean user-provided metadata

### Performance Tips

1. **Batch Operations**: Use listing with pagination for large buckets
2. **Streaming**: For large files, consider streaming uploads/downloads
3. **Caching**: Cache frequently accessed small files
4. **Presigned URLs**: Use for client-side uploads to reduce server load

## Testing

Run the demo script to test all functionality:

```bash
python demo_minio_dao.py
```

The demo covers:
- Upload/download operations
- File listing and filtering
- Object existence checks
- Presigned URL generation
- Bucket information retrieval
- Cleanup operations

## Integration Examples

### With FastAPI Endpoints

```python
from fastapi import APIRouter, UploadFile, HTTPException
from app.daos.minio_dao import MinioDAO

router = APIRouter()
dao = MinioDAO()

@router.post("/upload-audio/")
async def upload_user_audio(file: UploadFile):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(400, "Invalid audio file")
    
    audio_data = await file.read()
    
    request = MinioUploadRequest(
        object_name=f"user_upload_{file.filename}",
        audio_data=audio_data,
        bucket=AudioBucket.RECORDED,
        content_type=file.content_type
    )
    
    result = await dao.upload_audio(request)
    return {"object_name": result.object_name, "size": result.size}
```

### With OpenAI DAO Integration

```python
# Generate speech with OpenAI, store in MinIO
async def generate_and_store_speech(text: str, filename: str):
    # Generate audio with OpenAI
    openai_dao = OpenAIDAO()
    tts_request = TTSRequest(text=text)
    tts_result = await openai_dao.generate_audio_tts(tts_request)
    
    # Store in MinIO
    minio_dao = MinioDAO()
    upload_request = MinioUploadRequest(
        object_name=filename,
        audio_data=tts_result.audio_data,
        bucket=AudioBucket.GENERATED,
        content_type="audio/wav",
        metadata={"source": "openai_tts", "text_length": str(len(text))}
    )
    
    return await minio_dao.upload_audio(upload_request)
```

## Troubleshooting

### Common Issues

1. **Connection Failed**: Verify MinIO server is running on correct port
2. **Authentication Error**: Check access key and secret key
3. **Bucket Not Found**: Ensure buckets exist or enable auto-creation
4. **Upload Failed**: Check file size limits and available storage

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('app.daos.minio_dao').setLevel(logging.DEBUG)
```

### Health Check

```python
async def check_minio_health():
    try:
        dao = MinioDAO()
        info = await dao.get_bucket_info(AudioBucket.GENERATED)
        return {"status": "healthy", "buckets": info}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
