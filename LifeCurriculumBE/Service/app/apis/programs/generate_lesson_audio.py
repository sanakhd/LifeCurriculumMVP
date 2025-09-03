"""
Generate Lesson Audio API endpoint
"""
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.audio_generator import AudioGeneratorService
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/programs", tags=["Programs"])

# Initialize audio generator service
audio_service = AudioGeneratorService()


class GenerateLessonAudioRequest(BaseModel):
    """Request model for generating lesson audio"""
    lesson_uuid: str = Field(..., description="UUID of the lesson to generate audio for")
    voice_mapping: Optional[Dict[str, str]] = Field(
        default=None, 
        description="Custom voice assignments per host (e.g. {'Host A': 'alloy', 'Host B': 'echo'})"
    )


class AudioFileMetadata(BaseModel):
    """Metadata for a generated audio file"""
    chunk_index: int = Field(..., description="Index of the conversation chunk")
    audio_id: Optional[str] = Field(None, description="Unique identifier for the audio file")
    speaker: str = Field(..., description="Speaker name (Host A, Host B, etc.)")
    voice: Optional[str] = Field(None, description="OpenAI voice used for TTS")
    file_path: Optional[str] = Field(None, description="Path to the generated audio file")
    duration_seconds: Optional[int] = Field(None, description="Duration of the audio in seconds")
    regenerated: bool = Field(..., description="Whether this audio file was newly generated")
    error: Optional[str] = Field(None, description="Error message if generation failed")


class GenerateLessonAudioResponse(BaseModel):
    """Response model for lesson audio generation"""
    success: bool = Field(..., description="Whether the audio generation was successful")
    lesson_id: str = Field(..., description="ID of the lesson that had audio generated")
    audio_files: List[AudioFileMetadata] = Field(..., description="Metadata for all audio files")
    total_duration_seconds: int = Field(..., description="Total duration of all audio files")
    files_generated: int = Field(..., description="Number of audio files newly generated")
    files_total: int = Field(..., description="Total number of conversation chunks")
    manifest_path: str = Field(..., description="Path to the manifest file")


class AudioStatusResponse(BaseModel):
    """Response model for audio status check"""
    exists: bool = Field(..., description="Whether audio files exist for this lesson")
    lesson_id: Optional[str] = Field(None, description="ID of the lesson")
    has_conversation_chunks: Optional[bool] = Field(None, description="Whether lesson has conversation chunks")
    total_chunks: Optional[int] = Field(None, description="Total number of conversation chunks")
    manifest: Optional[Dict] = Field(None, description="Manifest data if audio exists")
    audio_directory: Optional[str] = Field(None, description="Path to audio directory")
    error: Optional[str] = Field(None, description="Error message if any")


class DeleteAudioResponse(BaseModel):
    """Response model for audio deletion"""
    success: bool = Field(..., description="Whether the audio deletion was successful")
    lesson_id: Optional[str] = Field(None, description="ID of the lesson")
    deleted_files: Optional[List[str]] = Field(None, description="List of deleted file paths")
    files_deleted: Optional[int] = Field(None, description="Number of files deleted")
    message: Optional[str] = Field(None, description="Success message")
    error: Optional[str] = Field(None, description="Error message if deletion failed")


@router.post("/generate-lesson-audio", response_model=GenerateLessonAudioResponse, summary="Generate Lesson Audio")
async def generate_lesson_audio(request: GenerateLessonAudioRequest):
    """
    Generate TTS audio for all conversation chunks in a lesson.
    
    This endpoint will:
    1. Fetch the lesson data from the program store
    2. Generate TTS audio for each conversation chunk using different voices
    3. Save audio files in program_audios/{lesson_id}/ with UUID filenames
    4. Update lesson metadata with audio references
    5. Create a manifest.json file to track all generated audio
    
    Audio files are saved as WAV format and organized by lesson ID.
    If audio already exists for a chunk, it will be skipped unless regeneration is forced.
    """
    logger.info(f"Processing audio generation request for lesson {request.lesson_uuid}")
    
    try:
        # Generate audio using the service
        result = await audio_service.generate_lesson_audio(
            lesson_uuid=request.lesson_uuid,
            voice_mapping=request.voice_mapping
        )
        
        # Convert result to response model
        audio_files = [AudioFileMetadata(**file_data) for file_data in result["audio_files"]]
        
        response = GenerateLessonAudioResponse(
            success=result["success"],
            lesson_id=result["lesson_id"],
            audio_files=audio_files,
            total_duration_seconds=result["total_duration_seconds"],
            files_generated=result["files_generated"],
            files_total=result["files_total"],
            manifest_path=result["manifest_path"]
        )
        
        logger.info(f"Successfully generated audio for lesson {result['lesson_id']} - {result['files_generated']}/{result['files_total']} files")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in audio generation: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in audio generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")


@router.get("/lessons/{lesson_uuid}/audio-status", response_model=AudioStatusResponse, summary="Check Lesson Audio Status")
async def get_lesson_audio_status(lesson_uuid: str):
    """
    Check the audio generation status for a specific lesson.
    
    This endpoint returns information about whether audio has been generated
    for the lesson, including file paths, manifest data, and generation metadata.
    """
    logger.info(f"Checking audio status for lesson {lesson_uuid}")
    
    try:
        result = audio_service.get_lesson_audio_status(lesson_uuid)
        return AudioStatusResponse(**result)
        
    except Exception as e:
        logger.error(f"Error checking audio status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check audio status: {str(e)}")


@router.delete("/lessons/{lesson_uuid}/audio", response_model=DeleteAudioResponse, summary="Delete Lesson Audio")
async def delete_lesson_audio(lesson_uuid: str):
    """
    Delete all generated audio files for a specific lesson.
    
    This endpoint will:
    1. Delete all audio files from the lesson directory
    2. Remove the manifest.json file
    3. Clear audio metadata from the lesson chunks
    4. Remove the lesson audio directory if empty
    """
    logger.info(f"Processing audio deletion request for lesson {lesson_uuid}")
    
    try:
        result = audio_service.delete_lesson_audio(lesson_uuid)
        return DeleteAudioResponse(**result)
        
    except Exception as e:
        logger.error(f"Error deleting audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete audio: {str(e)}")


@router.post("/regenerate-lesson-audio", response_model=GenerateLessonAudioResponse, summary="Regenerate Lesson Audio")
async def regenerate_lesson_audio(request: GenerateLessonAudioRequest):
    """
    Force regeneration of audio for a lesson, even if audio already exists.
    
    This endpoint first deletes any existing audio files, then generates new ones.
    Useful when you want to update voices or regenerate with different settings.
    """
    logger.info(f"Processing audio regeneration request for lesson {request.lesson_uuid}")
    
    try:
        # First delete existing audio
        delete_result = audio_service.delete_lesson_audio(request.lesson_uuid)
        if delete_result["success"]:
            logger.info(f"Deleted existing audio files: {delete_result.get('files_deleted', 0)} files")
        
        # Then generate new audio
        result = await audio_service.generate_lesson_audio(
            lesson_uuid=request.lesson_uuid,
            voice_mapping=request.voice_mapping
        )
        
        # Convert result to response model
        audio_files = [AudioFileMetadata(**file_data) for file_data in result["audio_files"]]
        
        response = GenerateLessonAudioResponse(
            success=result["success"],
            lesson_id=result["lesson_id"],
            audio_files=audio_files,
            total_duration_seconds=result["total_duration_seconds"],
            files_generated=result["files_generated"],
            files_total=result["files_total"],
            manifest_path=result["manifest_path"]
        )
        
        logger.info(f"Successfully regenerated audio for lesson {result['lesson_id']}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in audio regeneration: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in audio regeneration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio regeneration failed: {str(e)}")


@router.get("/available-voices", summary="Get Available TTS Voices")
async def get_available_voices():
    """
    Get the list of available OpenAI TTS voices and default mappings.
    
    This endpoint returns the voices that can be used for TTS generation
    and the default voice assignments for different hosts.
    """
    logger.debug("Returning available TTS voices")
    
    return {
        "available_voices": [
            {
                "name": "alloy",
                "description": "Neutral, informative voice"
            },
            {
                "name": "echo", 
                "description": "Warm, conversational voice"
            },
            {
                "name": "fable",
                "description": "British accent, expressive"
            },
            {
                "name": "onyx",
                "description": "Deep, authoritative voice"
            },
            {
                "name": "nova",
                "description": "Friendly, approachable voice"
            },
            {
                "name": "shimmer",
                "description": "Expressive, dynamic voice"
            }
        ],
        "default_voice_mapping": audio_service.DEFAULT_VOICE_MAPPING,
        "usage_example": {
            "voice_mapping": {
                "Host A": "alloy",
                "Host B": "echo"
            }
        }
    }
