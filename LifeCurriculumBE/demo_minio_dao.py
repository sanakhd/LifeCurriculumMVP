#!/usr/bin/env python3
"""
Demo script showing how to use the MinIO DAO
"""
import asyncio
import base64
import os
import sys

# Add the Service directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'Service'))

from app.daos.minio_dao import MinioDAO
from app.models.minio_models import (
    AudioBucket,
    MinioUploadRequest,
    MinioDownloadRequest,
    MinioListObjectsRequest,
    MinioDeleteRequest,
    MinioPresignedUrlRequest,
    MinioObjectExistsRequest
)


def create_sample_audio_data():
    """Create sample audio data for testing"""
    # Create a simple WAV header for a 1-second mono 44.1kHz 16-bit audio file
    # This is just sample data for demo purposes
    sample_rate = 44100
    duration = 1
    samples = sample_rate * duration
    
    # WAV header (44 bytes)
    wav_header = bytearray()
    wav_header.extend(b'RIFF')  # Chunk ID
    wav_header.extend((36 + samples * 2).to_bytes(4, 'little'))  # Chunk size
    wav_header.extend(b'WAVE')  # Format
    wav_header.extend(b'fmt ')  # Subchunk1 ID
    wav_header.extend((16).to_bytes(4, 'little'))  # Subchunk1 size
    wav_header.extend((1).to_bytes(2, 'little'))   # Audio format (PCM)
    wav_header.extend((1).to_bytes(2, 'little'))   # Num channels
    wav_header.extend(sample_rate.to_bytes(4, 'little'))  # Sample rate
    wav_header.extend((sample_rate * 2).to_bytes(4, 'little'))  # Byte rate
    wav_header.extend((2).to_bytes(2, 'little'))   # Block align
    wav_header.extend((16).to_bytes(2, 'little'))  # Bits per sample
    wav_header.extend(b'data')  # Subchunk2 ID
    wav_header.extend((samples * 2).to_bytes(4, 'little'))  # Subchunk2 size
    
    # Add some simple audio data (sine wave)
    import math
    audio_data = bytearray()
    for i in range(samples):
        # Generate a 440Hz sine wave
        sample = int(32767 * 0.3 * math.sin(2 * math.pi * 440 * i / sample_rate))
        audio_data.extend(sample.to_bytes(2, 'little', signed=True))
    
    return wav_header + audio_data


async def demo_upload_audio():
    """Demo uploading audio to MinIO buckets"""
    print("=== Audio Upload Demo ===")
    
    try:
        dao = MinioDAO()
        
        # Create sample audio data
        audio_data = create_sample_audio_data()
        print(f"Created sample audio data: {len(audio_data)} bytes")
        
        # Upload to generated audio bucket
        request = MinioUploadRequest(
            object_name="demo_generated_audio.wav",
            audio_data=audio_data,
            bucket=AudioBucket.GENERATED,
            content_type="audio/wav",
            metadata={"source": "demo", "type": "generated"}
        )
        
        result = await dao.upload_audio(request)
        print(f"✓ Uploaded to {result.bucket}: {result.object_name}")
        print(f"  Size: {result.size} bytes")
        print(f"  ETag: {result.etag}")
        print(f"  Upload Time: {result.upload_time}")
        if result.presigned_url:
            print(f"  Presigned URL: {result.presigned_url[:50]}...")
        
        # Upload to recorded audio bucket
        request2 = MinioUploadRequest(
            object_name="demo_recorded_audio.wav",
            audio_data=base64.b64encode(audio_data).decode(),  # Test base64 input
            bucket=AudioBucket.RECORDED,
            content_type="audio/wav",
            metadata={"source": "demo", "type": "recorded", "duration": "1s"}
        )
        
        result2 = await dao.upload_audio(request2)
        print(f"✓ Uploaded to {result2.bucket}: {result2.object_name}")
        print(f"  Size: {result2.size} bytes")
        print(f"  Upload Time: {result2.upload_time}")
        print()
        
    except Exception as e:
        print(f"Error in upload demo: {e}")
        print()


async def demo_list_audio():
    """Demo listing audio files in buckets"""
    print("=== List Audio Files Demo ===")
    
    try:
        dao = MinioDAO()
        
        # List files in generated audio bucket
        request = MinioListObjectsRequest(
            bucket=AudioBucket.GENERATED,
            recursive=True
        )
        
        result = await dao.list_audio_files(request)
        print(f"Files in {result.bucket}:")
        for obj in result.objects:
            print(f"  - {obj.object_name}")
            print(f"    Size: {obj.size} bytes")
            print(f"    Last Modified: {obj.last_modified}")
            print(f"    ETag: {obj.etag}")
            if obj.metadata:
                print(f"    Metadata: {obj.metadata}")
        
        # List files in recorded audio bucket
        request2 = MinioListObjectsRequest(
            bucket=AudioBucket.RECORDED,
            max_objects=10  # Limit results
        )
        
        result2 = await dao.list_audio_files(request2)
        print(f"\nFiles in {result2.bucket} (max 10):")
        for obj in result2.objects:
            print(f"  - {obj.object_name} ({obj.size} bytes)")
        
        print(f"Total objects found: {result2.total_objects}")
        print()
        
    except Exception as e:
        print(f"Error in list demo: {e}")
        print()


async def demo_download_audio():
    """Demo downloading audio files"""
    print("=== Download Audio Demo ===")
    
    try:
        dao = MinioDAO()
        
        # Download from generated audio bucket
        request = MinioDownloadRequest(
            object_name="demo_generated_audio.wav",
            bucket=AudioBucket.GENERATED
        )
        
        result = await dao.download_audio(request)
        print(f"✓ Downloaded {result.object_name} from {result.bucket}")
        print(f"  Size: {result.size} bytes")
        print(f"  Content Type: {result.content_type}")
        print(f"  Last Modified: {result.last_modified}")
        if result.metadata:
            print(f"  Metadata: {result.metadata}")
        
        # Save downloaded audio to local file
        with open("downloaded_demo_audio.wav", "wb") as f:
            f.write(result.audio_data)
        print("  Saved to: downloaded_demo_audio.wav")
        print()
        
    except Exception as e:
        print(f"Error in download demo: {e}")
        print()


async def demo_object_exists():
    """Demo checking if objects exist"""
    print("=== Object Exists Check Demo ===")
    
    try:
        dao = MinioDAO()
        
        # Check if our demo file exists
        request = MinioObjectExistsRequest(
            object_name="demo_generated_audio.wav",
            bucket=AudioBucket.GENERATED
        )
        
        result = await dao.check_object_exists(request)
        print(f"Object {result.object_name} exists: {result.exists}")
        if result.exists:
            print(f"  Size: {result.size} bytes")
            print(f"  Last Modified: {result.last_modified}")
        
        # Check for non-existent file
        request2 = MinioObjectExistsRequest(
            object_name="nonexistent_file.wav",
            bucket=AudioBucket.RECORDED
        )
        
        result2 = await dao.check_object_exists(request2)
        print(f"Object {result2.object_name} exists: {result2.exists}")
        print()
        
    except Exception as e:
        print(f"Error in exists check demo: {e}")
        print()


async def demo_presigned_urls():
    """Demo generating presigned URLs"""
    print("=== Presigned URLs Demo ===")
    
    try:
        dao = MinioDAO()
        
        # Generate GET presigned URL
        request = MinioPresignedUrlRequest(
            object_name="demo_generated_audio.wav",
            bucket=AudioBucket.GENERATED,
            expires_in_seconds=3600,
            method="GET"
        )
        
        result = await dao.get_presigned_url(request)
        print(f"✓ Generated GET presigned URL for {result.object_name}")
        print(f"  Bucket: {result.bucket}")
        print(f"  Method: {result.method}")
        print(f"  Expires in: {result.expires_in_seconds} seconds")
        print(f"  URL: {result.presigned_url[:100]}...")
        
        # Generate PUT presigned URL for uploading
        request2 = MinioPresignedUrlRequest(
            object_name="new_upload_via_presigned.wav",
            bucket=AudioBucket.RECORDED,
            expires_in_seconds=1800,  # 30 minutes
            method="PUT"
        )
        
        result2 = await dao.get_presigned_url(request2)
        print(f"\n✓ Generated PUT presigned URL for {result2.object_name}")
        print(f"  This URL can be used to upload directly to MinIO")
        print(f"  URL: {result2.presigned_url[:100]}...")
        print()
        
    except Exception as e:
        print(f"Error in presigned URL demo: {e}")
        print()


async def demo_bucket_info():
    """Demo getting bucket information"""
    print("=== Bucket Information Demo ===")
    
    try:
        dao = MinioDAO()
        
        # Get info for both buckets
        for bucket in [AudioBucket.GENERATED, AudioBucket.RECORDED]:
            info = await dao.get_bucket_info(bucket)
            print(f"Bucket: {info['bucket_name']} ({info['bucket_type']})")
            print(f"  Exists: {info['exists']}")
            print(f"  Total Objects: {info['total_objects']}")
            print(f"  Total Size: {info['total_size_mb']} MB ({info['total_size_bytes']} bytes)")
            print()
        
    except Exception as e:
        print(f"Error in bucket info demo: {e}")
        print()


async def demo_delete_audio():
    """Demo deleting audio files"""
    print("=== Delete Audio Demo ===")
    
    try:
        dao = MinioDAO()
        
        # Delete demo files
        request = MinioDeleteRequest(
            object_name="demo_generated_audio.wav",
            bucket=AudioBucket.GENERATED
        )
        
        result = await dao.delete_audio(request)
        print(f"Delete {result.object_name}: {result.deleted}")
        print(f"Message: {result.message}")
        
        # Try to delete non-existent file
        request2 = MinioDeleteRequest(
            object_name="nonexistent_file.wav",
            bucket=AudioBucket.RECORDED
        )
        
        result2 = await dao.delete_audio(request2)
        print(f"Delete {result2.object_name}: {result2.deleted}")
        print(f"Message: {result2.message}")
        print()
        
    except Exception as e:
        print(f"Error in delete demo: {e}")
        print()


async def main():
    """Run all demos"""
    print("MinIO DAO Demo")
    print("=" * 50)
    print("Make sure MinIO is running on localhost:9000")
    print("with username 'admin' and password 'password'")
    print("=" * 50)
    print()
    
    # Check if MinIO DAO can be initialized
    try:
        dao = MinioDAO()
        print("✓ MinIO DAO initialized successfully")
        print("✓ Buckets checked/created")
        print()
    except ValueError as e:
        print(f"✗ Configuration Error: {e}")
        print("Please check your MinIO configuration")
        return
    except Exception as e:
        print(f"✗ Initialization Error: {e}")
        print("Please ensure MinIO is running on localhost:9000")
        return
    
    # Run demos in order
    await demo_upload_audio()
    await demo_list_audio()
    await demo_download_audio()
    await demo_object_exists()
    await demo_presigned_urls()
    await demo_bucket_info()
    
    # Cleanup demo (delete uploaded files)
    print("=== Cleanup ===")
    try:
        # Delete demo files
        for bucket in [AudioBucket.GENERATED, AudioBucket.RECORDED]:
            for filename in ["demo_generated_audio.wav", "demo_recorded_audio.wav"]:
                try:
                    request = MinioDeleteRequest(object_name=filename, bucket=bucket)
                    result = await dao.delete_audio(request)
                    if result.deleted:
                        print(f"✓ Cleaned up {filename} from {bucket.value} bucket")
                except:
                    pass  # Ignore errors during cleanup
    except Exception as e:
        print(f"Cleanup warning: {e}")
    
    print("\n" + "=" * 50)
    print("Demo completed! Check the generated files:")
    print("- downloaded_demo_audio.wav")
    print("\nMinIO DAO is ready for use in your applications!")


if __name__ == "__main__":
    asyncio.run(main())
