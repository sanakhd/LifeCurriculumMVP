"""
Audio Generator Service for Lesson TTS Generation
"""
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from app.logger import get_logger
from app.models.openai_models import TTSRequest
from app.daos.openai_dao import OpenAIDAO
from app.models.lesson import Lesson, ConversationTurn
from app.models.program import Program
from app.storage.program_store import get_program, upsert_program, get_lesson_by_uuid

logger = get_logger(__name__)

# Audio storage directory
AUDIO_BASE_DIR = Path("program_audios")
AUDIO_BASE_DIR.mkdir(exist_ok=True)

class AudioGeneratorService:
    """Service for generating TTS audio from lesson conversations"""
    
    # Default voice mapping for different hosts
    DEFAULT_VOICE_MAPPING = {
        "Host A": "alloy",     # Neutral, informative
        "Host B": "echo",      # Warm, conversational  
        "Host C": "fable",     # British accent
        "Host D": "onyx",      # Deep, authoritative
        "Host E": "nova",      # Friendly
        "Host F": "shimmer"    # Expressive
    }
    
    def __init__(self):
        """Initialize the audio generator service"""
        logger.debug("Initializing Audio Generator Service")
        self.dao = OpenAIDAO()
        logger.info("Audio Generator Service initialized successfully")
    
    async def generate_lesson_audio(
        self, 
        lesson_uuid: str,
        voice_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate TTS audio for all conversation chunks in a lesson
        
        Args:
            lesson_uuid: UUID of the lesson to generate audio for
            voice_mapping: Optional custom voice assignments per host
            
        Returns:
            Dict containing success status and audio metadata
            
        Raises:
            ValueError: If lesson not found
            Exception: If TTS generation fails
        """
        logger.info(f"Starting audio generation for lesson {lesson_uuid}")
        
        # Fetch program and lesson data
        result = get_lesson_by_uuid(lesson_uuid)
        if not result:
            raise ValueError(f"Lesson not found: {lesson_uuid}")
        
        raw_program, raw_lesson = result
        program = Program(**raw_program)
        lesson = Lesson(**raw_lesson)
        
        if not lesson.conversation_chunks:
            raise ValueError(f"No conversation chunks found in lesson {lesson.id}")
        
        logger.info(f"Found lesson {lesson.id} with {len(lesson.conversation_chunks)} conversation chunks")
        
        # Use custom voice mapping or defaults
        voices = voice_mapping or self.DEFAULT_VOICE_MAPPING
        
        # Create lesson audio directory
        lesson_audio_dir = AUDIO_BASE_DIR / lesson.id
        lesson_audio_dir.mkdir(exist_ok=True)
        logger.debug(f"Created audio directory: {lesson_audio_dir}")
        
        # Generate audio for each conversation chunk
        audio_metadata = []
        updated_chunks = []
        
        for index, chunk in enumerate(lesson.conversation_chunks):
            try:
                logger.debug(f"Processing chunk {index + 1}/{len(lesson.conversation_chunks)} - Speaker: {chunk.speaker}")
                
                # Get voice for this speaker
                voice = voices.get(chunk.speaker, self.DEFAULT_VOICE_MAPPING.get("Host A", "alloy"))
                
                # Check if audio already exists for this chunk
                existing_audio_id = chunk.media.get("audio_id") if chunk.media else None
                if existing_audio_id:
                    audio_file_path = lesson_audio_dir / f"{existing_audio_id}.wav"
                    if audio_file_path.exists():
                        logger.info(f"Audio already exists for chunk {index + 1}, skipping generation")
                        audio_metadata.append({
                            "chunk_index": index,
                            "audio_id": existing_audio_id,
                            "speaker": chunk.speaker,
                            "file_path": str(audio_file_path),
                            "regenerated": False
                        })
                        updated_chunks.append(chunk)
                        continue
                
                # Generate new audio
                audio_id, file_path, duration = await self._generate_chunk_audio(
                    chunk.text, voice, lesson_audio_dir, index
                )
                
                # Update chunk with audio metadata
                updated_chunk = ConversationTurn(
                    speaker=chunk.speaker,
                    text=chunk.text,
                    media={
                        "audio_id": audio_id,
                        "file_path": str(file_path),
                        "duration_seconds": duration,
                        "voice": voice,
                        "generated_at": datetime.utcnow().isoformat()
                    }
                )
                updated_chunks.append(updated_chunk)
                
                audio_metadata.append({
                    "chunk_index": index,
                    "audio_id": audio_id,
                    "speaker": chunk.speaker,
                    "voice": voice,
                    "file_path": str(file_path),
                    "duration_seconds": duration,
                    "regenerated": True
                })
                
                logger.info(f"Generated audio for chunk {index + 1} - Audio ID: {audio_id}")
                
            except Exception as e:
                logger.error(f"Failed to generate audio for chunk {index + 1}: {str(e)}")
                # Keep original chunk without audio
                updated_chunks.append(chunk)
                audio_metadata.append({
                    "chunk_index": index,
                    "speaker": chunk.speaker,
                    "error": str(e),
                    "regenerated": False
                })
        
        # Create manifest file
        manifest_path = lesson_audio_dir / "manifest.json"
        manifest_data = {
            "lesson_id": lesson.id,
            "program_id": program.id,
            "day_number": lesson.day_number,
            "generated_at": datetime.utcnow().isoformat(),
            "voice_mapping": voices,
            "audio_files": audio_metadata
        }
        
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
        # Update lesson in program store
        lesson.conversation_chunks = updated_chunks
        self._update_lesson_in_program(program, lesson)
        
        # Calculate totals
        total_duration = sum(
            meta.get("duration_seconds", 0) 
            for meta in audio_metadata 
            if "duration_seconds" in meta
        )
        generated_count = sum(1 for meta in audio_metadata if meta.get("regenerated", False))
        
        logger.info(f"Audio generation completed - {generated_count}/{len(lesson.conversation_chunks)} files generated")
        
        return {
            "success": True,
            "lesson_id": lesson.id,
            "audio_files": audio_metadata,
            "total_duration_seconds": total_duration,
            "files_generated": generated_count,
            "files_total": len(lesson.conversation_chunks),
            "manifest_path": str(manifest_path)
        }
    
    async def _generate_chunk_audio(
        self, 
        text: str, 
        voice: str, 
        output_dir: Path,
        chunk_index: int
    ) -> Tuple[str, Path, int]:
        """
        Generate TTS audio for a single conversation chunk
        
        Args:
            text: Text to convert to speech
            voice: OpenAI voice to use
            output_dir: Directory to save audio file
            chunk_index: Index of the chunk (for logging)
            
        Returns:
            Tuple of (audio_id, file_path, duration_seconds)
        """
        logger.debug(f"Generating TTS for chunk {chunk_index + 1} with voice '{voice}', text length: {len(text)}")
        
        # Generate unique audio ID
        audio_id = str(uuid.uuid4())
        
        # Create TTS request
        tts_request = TTSRequest(
            text=text,
            voice=voice,
            model="tts-1",  # Use the standard TTS model
            response_format="wav"
        )
        
        # Generate audio
        tts_response = await self.dao.generate_audio_tts(tts_request)
        
        # Save audio file
        file_path = output_dir / f"{audio_id}.wav"
        with file_path.open("wb") as f:
            f.write(tts_response.audio_data)
        
        # Estimate duration (rough calculation: ~150 words per minute, ~5 characters per word)
        estimated_duration = max(1, len(text) // 750)  # Very rough estimate
        
        logger.debug(f"Saved audio file: {file_path}, estimated duration: {estimated_duration}s")
        
        return audio_id, file_path, estimated_duration
    
    def _get_lesson_by_day(self, program: Program, day_number: int) -> Optional[Lesson]:
        """Get lesson from program by day number"""
        for lesson_data in program.lessons:
            if isinstance(lesson_data, dict):
                lesson = Lesson(**lesson_data)
            else:
                lesson = lesson_data
            
            if lesson.day_number == day_number:
                return lesson
        return None
    
    def _update_lesson_in_program(self, program: Program, updated_lesson: Lesson) -> None:
        """Update lesson in program store"""
        logger.debug(f"Updating lesson {updated_lesson.id} in program store")
        
        # Get raw program data
        raw_program = get_program(program.id)
        if not raw_program:
            raise ValueError(f"Program not found: {program.id}")
        
        # Update lesson in lessons array
        raw_lessons = raw_program.get("lessons", [])
        for i, lesson_data in enumerate(raw_lessons):
            if lesson_data.get("id") == updated_lesson.id:
                raw_lessons[i] = updated_lesson.model_dump(mode="json")
                break
        else:
            # If lesson not found, append it
            raw_lessons.append(updated_lesson.model_dump(mode="json"))
        
        raw_program["lessons"] = raw_lessons
        raw_program["updated_at"] = datetime.utcnow().isoformat()
        
        # Save updated program
        upsert_program(raw_program)
        logger.info(f"Updated program {program.id} with audio metadata for lesson {updated_lesson.id}")
    
    def get_lesson_audio_status(self, lesson_uuid: str) -> Dict[str, Any]:
        """
        Get audio generation status for a lesson
        
        Args:
            lesson_uuid: UUID of the lesson
            
        Returns:
            Dict containing audio status information
        """
        logger.debug(f"Checking audio status for lesson {lesson_uuid}")
        
        # Get program and lesson
        result = get_lesson_by_uuid(lesson_uuid)
        if not result:
            return {"exists": False, "error": "Lesson not found"}
        
        raw_program, raw_lesson = result
        program = Program(**raw_program)
        lesson = Lesson(**raw_lesson)
        
        # Check if audio directory exists
        lesson_audio_dir = AUDIO_BASE_DIR / lesson.id
        manifest_path = lesson_audio_dir / "manifest.json"
        
        if not manifest_path.exists():
            return {
                "exists": False,
                "lesson_id": lesson.id,
                "has_conversation_chunks": len(lesson.conversation_chunks) > 0,
                "total_chunks": len(lesson.conversation_chunks)
            }
        
        # Load manifest
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            return {
                "exists": True,
                "lesson_id": lesson.id,
                "manifest": manifest,
                "audio_directory": str(lesson_audio_dir)
            }
        except Exception as e:
            logger.error(f"Failed to load manifest for lesson {lesson.id}: {str(e)}")
            return {"exists": False, "error": f"Failed to load manifest: {str(e)}"}
    
    def delete_lesson_audio(self, lesson_uuid: str) -> Dict[str, Any]:
        """
        Delete generated audio files for a lesson
        
        Args:
            lesson_uuid: UUID of the lesson
            
        Returns:
            Dict containing deletion status
        """
        logger.info(f"Deleting audio for lesson {lesson_uuid}")
        
        # Get program and lesson
        result = get_lesson_by_uuid(lesson_uuid)
        if not result:
            return {"success": False, "error": "Lesson not found"}
        
        raw_program, raw_lesson = result
        program = Program(**raw_program)
        lesson = Lesson(**raw_lesson)
        
        # Check audio directory
        lesson_audio_dir = AUDIO_BASE_DIR / lesson.id
        if not lesson_audio_dir.exists():
            return {"success": True, "message": "No audio files to delete"}
        
        # Delete audio files
        deleted_files = []
        for audio_file in lesson_audio_dir.glob("*.wav"):
            try:
                audio_file.unlink()
                deleted_files.append(str(audio_file))
            except Exception as e:
                logger.error(f"Failed to delete audio file {audio_file}: {str(e)}")
        
        # Delete manifest
        manifest_path = lesson_audio_dir / "manifest.json"
        if manifest_path.exists():
            try:
                manifest_path.unlink()
                deleted_files.append(str(manifest_path))
            except Exception as e:
                logger.error(f"Failed to delete manifest {manifest_path}: {str(e)}")
        
        # Remove directory if empty
        try:
            lesson_audio_dir.rmdir()
            logger.info(f"Removed empty audio directory: {lesson_audio_dir}")
        except OSError:
            logger.debug(f"Audio directory not empty or could not be removed: {lesson_audio_dir}")
        
        # Clear audio metadata from lesson chunks
        updated_chunks = []
        for chunk in lesson.conversation_chunks:
            updated_chunk = ConversationTurn(
                speaker=chunk.speaker,
                text=chunk.text,
                media=None  # Clear media metadata
            )
            updated_chunks.append(updated_chunk)
        
        lesson.conversation_chunks = updated_chunks
        self._update_lesson_in_program(program, lesson)
        
        logger.info(f"Deleted {len(deleted_files)} audio files for lesson {lesson.id}")
        
        return {
            "success": True,
            "lesson_id": lesson.id,
            "deleted_files": deleted_files,
            "files_deleted": len(deleted_files)
        }
