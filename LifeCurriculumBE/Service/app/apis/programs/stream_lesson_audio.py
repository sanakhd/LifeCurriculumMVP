"""
Stream Lesson Audio API endpoint
"""
import os
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/programs", tags=["Programs"])


class AudioStreamResponse(BaseModel):
    """Response model for audio stream info"""
    lesson_uuid: str = Field(..., description="UUID of the lesson")
    audio_id: str = Field(..., description="UUID of the audio file")
    speaker: str = Field(..., description="Speaker name (Host A, Host B, etc.)")
    voice: str = Field(..., description="OpenAI voice used for TTS")
    duration_seconds: int = Field(..., description="Duration of the audio in seconds")
    chunk_index: int = Field(..., description="Index of the conversation chunk")
    file_size_bytes: int = Field(..., description="Size of the audio file in bytes")


def get_audio_file_info(lesson_uuid: str, audio_id: str) -> dict:
    """
    Get audio file information from the manifest
    
    Args:
        lesson_uuid: UUID of the lesson
        audio_id: UUID of the audio file
        
    Returns:
        Dictionary containing audio file metadata
        
    Raises:
        FileNotFoundError: If lesson directory or manifest doesn't exist
        ValueError: If audio_id not found in manifest
    """
    # Construct paths
    audio_dir = Path("program_audios") / lesson_uuid
    manifest_path = audio_dir / "manifest.json"
    
    # Check if lesson directory exists
    if not audio_dir.exists():
        raise FileNotFoundError(f"Lesson audio directory not found: {lesson_uuid}")
    
    # Check if manifest exists
    if not manifest_path.exists():
        raise FileNotFoundError(f"Audio manifest not found for lesson: {lesson_uuid}")
    
    # Load manifest
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid manifest format for lesson {lesson_uuid}: {str(e)}")
    
    # Find audio file in manifest
    audio_files = manifest.get("audio_files", [])
    for audio_file in audio_files:
        if audio_file.get("audio_id") == audio_id:
            # Construct full file path
            file_path = Path("program_audios") / lesson_uuid / f"{audio_id}.wav"
            if not file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            
            # Add file size info
            audio_file["file_size_bytes"] = file_path.stat().st_size
            audio_file["full_file_path"] = str(file_path)
            return audio_file
    
    raise ValueError(f"Audio ID {audio_id} not found in lesson {lesson_uuid}")


def stream_audio_file(file_path: str, chunk_size: int = 8192):
    """
    Generator function to stream audio file in chunks
    
    Args:
        file_path: Path to the audio file
        chunk_size: Size of each chunk in bytes (default 8KB)
        
    Yields:
        Bytes of audio data
    """
    try:
        with open(file_path, 'rb') as audio_file:
            while True:
                chunk = audio_file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    except IOError as e:
        logger.error(f"Error reading audio file {file_path}: {str(e)}")
        raise


@router.get("/lessons/{lesson_uuid}/audio/{audio_id}/stream", summary="Stream Lesson Audio")
async def stream_lesson_audio(lesson_uuid: str, audio_id: str, chunk_size: Optional[int] = 8192):
    """
    Stream audio for a specific lesson and audio ID.
    
    This endpoint streams the audio file directly to the client with proper
    content headers for audio playback. The audio is streamed in chunks to
    handle large files efficiently.
    
    Args:
        lesson_uuid: UUID of the lesson containing the audio
        audio_id: UUID of the specific audio file to stream
        chunk_size: Size of streaming chunks in bytes (optional, default 8KB)
    
    Returns:
        StreamingResponse: Audio file stream with appropriate headers
        
    Raises:
        404: If lesson, manifest, or audio file not found
        500: If there's an error reading the audio file
    """
    logger.info(f"Streaming audio request for lesson {lesson_uuid}, audio {audio_id}")
    
    try:
        # Get audio file information
        audio_info = get_audio_file_info(lesson_uuid, audio_id)
        file_path = audio_info["full_file_path"]
        
        logger.info(f"Streaming audio file: {file_path} ({audio_info['file_size_bytes']} bytes)")
        
        # Set up streaming headers
        headers = {
            "Content-Type": "audio/wav",
            "Content-Length": str(audio_info["file_size_bytes"]),
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "X-Audio-Lesson-UUID": lesson_uuid,
            "X-Audio-ID": audio_id,
            "X-Audio-Speaker": audio_info.get("speaker", "Unknown"),
            "X-Audio-Voice": audio_info.get("voice", "Unknown"),
            "X-Audio-Duration": str(audio_info.get("duration_seconds", 0)),
            "X-Audio-Chunk-Index": str(audio_info.get("chunk_index", 0))
        }
        
        # Create streaming response
        return StreamingResponse(
            stream_audio_file(file_path, chunk_size),
            media_type="audio/wav",
            headers=headers
        )
        
    except FileNotFoundError as e:
        logger.error(f"Audio file not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"Audio lookup error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error streaming audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stream audio: {str(e)}")


@router.get("/lessons/{lesson_uuid}/audio/{audio_id}/info", response_model=AudioStreamResponse, summary="Get Audio File Info")
async def get_audio_file_metadata(lesson_uuid: str, audio_id: str):
    """
    Get metadata information for a specific audio file without streaming it.
    
    This endpoint returns detailed information about an audio file including
    speaker, voice used, duration, file size, and position in the conversation.
    
    Args:
        lesson_uuid: UUID of the lesson containing the audio
        audio_id: UUID of the specific audio file
    
    Returns:
        AudioStreamResponse: Detailed metadata about the audio file
        
    Raises:
        404: If lesson, manifest, or audio file not found
        500: If there's an error reading the manifest
    """
    logger.info(f"Getting audio info for lesson {lesson_uuid}, audio {audio_id}")
    
    try:
        # Get audio file information
        audio_info = get_audio_file_info(lesson_uuid, audio_id)
        
        return AudioStreamResponse(
            lesson_uuid=lesson_uuid,
            audio_id=audio_id,
            speaker=audio_info.get("speaker", "Unknown"),
            voice=audio_info.get("voice", "Unknown"),
            duration_seconds=audio_info.get("duration_seconds", 0),
            chunk_index=audio_info.get("chunk_index", 0),
            file_size_bytes=audio_info.get("file_size_bytes", 0)
        )
        
    except FileNotFoundError as e:
        logger.error(f"Audio file not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"Audio lookup error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting audio info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audio info: {str(e)}")


@router.get("/lessons/{lesson_uuid}/audio/playlist", summary="Get Audio Playlist for Lesson")
async def get_lesson_audio_playlist(lesson_uuid: str):
    """
    Get a playlist of all audio files for a lesson in conversation order.
    
    This endpoint returns an ordered list of all audio files for a lesson,
    providing URLs to stream each audio chunk in the correct conversation sequence.
    Useful for building audio players that can play the entire lesson conversation.
    
    Args:
        lesson_uuid: UUID of the lesson
    
    Returns:
        Dictionary containing playlist information and streaming URLs
        
    Raises:
        404: If lesson directory or manifest not found
        500: If there's an error reading the manifest
    """
    logger.info(f"Getting audio playlist for lesson {lesson_uuid}")
    
    try:
        # Construct paths
        audio_dir = Path("program_audios") / lesson_uuid
        manifest_path = audio_dir / "manifest.json"
        
        # Check if lesson directory exists
        if not audio_dir.exists():
            raise FileNotFoundError(f"Lesson audio directory not found: {lesson_uuid}")
        
        # Check if manifest exists
        if not manifest_path.exists():
            raise FileNotFoundError(f"Audio manifest not found for lesson: {lesson_uuid}")
        
        # Load manifest
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Sort audio files by chunk_index to ensure correct order
        audio_files = sorted(manifest.get("audio_files", []), key=lambda x: x.get("chunk_index", 0))
        
        # Build playlist with streaming URLs
        playlist = []
        total_duration = 0
        
        for audio_file in audio_files:
            audio_id = audio_file.get("audio_id")
            duration = audio_file.get("duration_seconds", 0)
            total_duration += duration
            
            playlist.append({
                "chunk_index": audio_file.get("chunk_index", 0),
                "audio_id": audio_id,
                "speaker": audio_file.get("speaker", "Unknown"),
                "voice": audio_file.get("voice", "Unknown"),
                "duration_seconds": duration,
                "stream_url": f"/programs/lessons/{lesson_uuid}/audio/{audio_id}/stream",
                "info_url": f"/programs/lessons/{lesson_uuid}/audio/{audio_id}/info"
            })
        
        return {
            "lesson_uuid": lesson_uuid,
            "program_id": manifest.get("program_id"),
            "day_number": manifest.get("day_number"),
            "generated_at": manifest.get("generated_at"),
            "total_chunks": len(playlist),
            "total_duration_seconds": total_duration,
            "voice_mapping": manifest.get("voice_mapping", {}),
            "playlist": playlist
        }
        
    except FileNotFoundError as e:
        logger.error(f"Playlist generation failed: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except json.JSONDecodeError as e:
        logger.error(f"Invalid manifest format for lesson {lesson_uuid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Invalid manifest format: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error generating playlist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate playlist: {str(e)}")
