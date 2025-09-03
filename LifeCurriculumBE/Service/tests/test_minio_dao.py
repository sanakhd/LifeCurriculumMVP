"""
Tests for MinIO DAO
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Import the classes we want to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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


class TestMinioDAO:
    """Test cases for MinIO DAO"""
    
    @pytest.fixture
    def mock_minio_client(self):
        """Create a mock MinIO client"""
        with patch('app.daos.minio_dao.Minio') as mock_minio:
            client = MagicMock()
            mock_minio.return_value = client
            
            # Mock bucket operations
            client.bucket_exists.return_value = True
            client.make_bucket.return_value = None
            client.list_objects.return_value = []
            
            yield client
    
    @pytest.fixture
    def dao(self, mock_minio_client):
        """Create MinIO DAO instance with mocked client"""
        with patch('app.daos.minio_dao.get_settings') as mock_settings:
            settings = MagicMock()
            settings.minio_endpoint = "localhost:9000"
            settings.minio_access_key = "admin"
            settings.minio_secret_key = "password"
            settings.minio_secure = False
            settings.minio_generated_audio_bucket = "lc-generated-audio"
            settings.minio_recorded_audio_bucket = "lc-recorded-user-audio"
            mock_settings.return_value = settings
            
            return MinioDAO()
    
    def test_get_bucket_name(self, dao):
        """Test bucket name mapping"""
        assert dao._get_bucket_name(AudioBucket.GENERATED) == "lc-generated-audio"
        assert dao._get_bucket_name(AudioBucket.RECORDED) == "lc-recorded-user-audio"
    
    def test_prepare_audio_data_bytes(self, dao):
        """Test audio data preparation with bytes"""
        test_bytes = b"test audio data"
        result = dao._prepare_audio_data(test_bytes)
        assert result == test_bytes
    
    def test_prepare_audio_data_base64(self, dao):
        """Test audio data preparation with base64 string"""
        import base64
        test_bytes = b"test audio data"
        test_b64 = base64.b64encode(test_bytes).decode()
        
        result = dao._prepare_audio_data(test_b64)
        assert result == test_bytes
    
    @pytest.mark.asyncio
    async def test_upload_audio(self, dao, mock_minio_client):
        """Test audio upload functionality"""
        # Mock upload result
        mock_result = MagicMock()
        mock_result.etag = "test-etag"
        mock_minio_client.put_object.return_value = mock_result
        mock_minio_client.presigned_get_object.return_value = "http://presigned-url"
        
        # Create upload request
        request = MinioUploadRequest(
            object_name="test_audio.wav",
            audio_data=b"test audio data",
            bucket=AudioBucket.GENERATED,
            content_type="audio/wav",
            metadata={"test": "metadata"}
        )
        
        # Test upload
        result = await dao.upload_audio(request)
        
        assert result.object_name == "test_audio.wav"
        assert result.bucket == "lc-generated-audio"
        assert result.size == len(b"test audio data")
        assert result.etag == "test-etag"
        assert result.presigned_url == "http://presigned-url"
        
        # Verify client was called correctly
        mock_minio_client.put_object.assert_called_once()
        mock_minio_client.presigned_get_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_audio(self, dao, mock_minio_client):
        """Test audio download functionality"""
        # Mock stat and get_object
        mock_stat = MagicMock()
        mock_stat.size = 100
        mock_stat.content_type = "audio/wav"
        mock_stat.last_modified = "2024-01-15"
        mock_stat.metadata = {"test": "metadata"}
        mock_minio_client.stat_object.return_value = mock_stat
        
        mock_response = MagicMock()
        mock_response.read.return_value = b"test audio data"
        mock_minio_client.get_object.return_value = mock_response
        
        # Create download request
        request = MinioDownloadRequest(
            object_name="test_audio.wav",
            bucket=AudioBucket.GENERATED
        )
        
        # Test download
        result = await dao.download_audio(request)
        
        assert result.object_name == "test_audio.wav"
        assert result.bucket == "lc-generated-audio"
        assert result.audio_data == b"test audio data"
        assert result.size == 100
        assert result.content_type == "audio/wav"
        
        # Verify client was called correctly
        mock_minio_client.stat_object.assert_called_once()
        mock_minio_client.get_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_audio_files(self, dao, mock_minio_client):
        """Test listing audio files"""
        # Mock list objects
        mock_obj = MagicMock()
        mock_obj.object_name = "test_audio.wav"
        mock_obj.size = 100
        mock_obj.last_modified = "2024-01-15"
        mock_obj.etag = "test-etag"
        mock_minio_client.list_objects.return_value = [mock_obj]
        
        # Mock stat for metadata
        mock_stat = MagicMock()
        mock_stat.metadata = {"test": "metadata"}
        mock_stat.content_type = "audio/wav"
        mock_minio_client.stat_object.return_value = mock_stat
        
        # Create list request
        request = MinioListObjectsRequest(
            bucket=AudioBucket.GENERATED,
            recursive=True
        )
        
        # Test listing
        result = await dao.list_audio_files(request)
        
        assert result.bucket == "lc-generated-audio"
        assert len(result.objects) == 1
        assert result.objects[0].object_name == "test_audio.wav"
        assert result.total_objects == 1
    
    @pytest.mark.asyncio
    async def test_delete_audio(self, dao, mock_minio_client):
        """Test audio deletion"""
        # Mock stat (file exists)
        mock_minio_client.stat_object.return_value = MagicMock()
        mock_minio_client.remove_object.return_value = None
        
        # Create delete request
        request = MinioDeleteRequest(
            object_name="test_audio.wav",
            bucket=AudioBucket.GENERATED
        )
        
        # Test deletion
        result = await dao.delete_audio(request)
        
        assert result.object_name == "test_audio.wav"
        assert result.bucket == "lc-generated-audio"
        assert result.deleted == True
        assert "successfully" in result.message
        
        # Verify client was called correctly
        mock_minio_client.stat_object.assert_called_once()
        mock_minio_client.remove_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_object_exists_true(self, dao, mock_minio_client):
        """Test object existence check when object exists"""
        # Mock stat (file exists)
        mock_stat = MagicMock()
        mock_stat.size = 100
        mock_stat.last_modified = "2024-01-15"
        mock_minio_client.stat_object.return_value = mock_stat
        
        # Create exists request
        request = MinioObjectExistsRequest(
            object_name="test_audio.wav",
            bucket=AudioBucket.GENERATED
        )
        
        # Test existence check
        result = await dao.check_object_exists(request)
        
        assert result.object_name == "test_audio.wav"
        assert result.bucket == "lc-generated-audio"
        assert result.exists == True
        assert result.size == 100
        assert result.last_modified == "2024-01-15"
    
    @pytest.mark.asyncio
    async def test_get_presigned_url_get(self, dao, mock_minio_client):
        """Test presigned URL generation for GET"""
        # Mock presigned URL generation
        mock_minio_client.presigned_get_object.return_value = "http://presigned-get-url"
        
        # Create presigned URL request
        request = MinioPresignedUrlRequest(
            object_name="test_audio.wav",
            bucket=AudioBucket.GENERATED,
            expires_in_seconds=3600,
            method="GET"
        )
        
        # Test presigned URL generation
        result = await dao.get_presigned_url(request)
        
        assert result.object_name == "test_audio.wav"
        assert result.bucket == "lc-generated-audio"
        assert result.presigned_url == "http://presigned-get-url"
        assert result.expires_in_seconds == 3600
        assert result.method == "GET"
    
    @pytest.mark.asyncio
    async def test_get_bucket_info(self, dao, mock_minio_client):
        """Test bucket information retrieval"""
        # Mock list objects for bucket info
        mock_obj = MagicMock()
        mock_obj.size = 100
        mock_minio_client.list_objects.return_value = [mock_obj, mock_obj]  # 2 objects
        mock_minio_client.bucket_exists.return_value = True
        
        # Test bucket info
        result = await dao.get_bucket_info(AudioBucket.GENERATED)
        
        assert result["bucket_name"] == "lc-generated-audio"
        assert result["bucket_type"] == "generated"
        assert result["total_objects"] == 2
        assert result["total_size_bytes"] == 200
        assert result["total_size_mb"] == 0.0  # Small size rounds to 0
        assert result["exists"] == True


if __name__ == "__main__":
    # Simple test runner
    print("Running MinIO DAO tests...")
    print("Note: Install pytest to run full test suite: pip install pytest pytest-asyncio")
    print("Then run: pytest Service/tests/test_minio_dao.py -v")
