"""
Generate Full Program API endpoint
Creates a complete 5-day program with all lessons generated in one request.
Orchestrates generate_program and generate_lesson to maintain consistency.
Now includes automatic audio generation for all lessons with conversation chunks.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.logger import get_logger
from app.storage.program_store import get_program, delete_program
from app.models.program import Program
from app.models.enums import ContextType, ProgramStatus
from app.services.audio_generator import AudioGeneratorService

# Import existing functions to maintain consistency
from .generate_program import GenerateProgramRequest, generate_program
from .generate_lesson import GenerateLessonIn, generate_lesson

logger = get_logger(__name__)
router = APIRouter(tags=["Programs"])


# ---------- Request / Response ----------

class GenerateFullProgramRequest(BaseModel):
    # Same as GenerateProgramRequest for consistency
    focus_area: str = Field(..., min_length=5, description="User's one-sentence focus/goal area")
    target_outcome: str = Field(..., min_length=5, description="Concrete outcome for the week")
    context: ContextType
    prompt: Optional[str] = None
    
    # Additional options for full program generation
    model: Optional[str] = Field(None, description="Optional model override for all generations")
    
    # Audio generation options
    generate_audio: bool = Field(True, description="Whether to generate audio for lessons with conversation chunks")
    voice_mapping: Optional[Dict[str, str]] = Field(
        None, 
        description="Custom voice assignments per host (e.g. {'Host A': 'alloy', 'Host B': 'echo'})"
    )

    @field_validator("focus_area", "target_outcome")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v


class AudioGenerationStats(BaseModel):
    audio_generation_enabled: bool = Field(..., description="Whether audio generation was requested")
    lessons_with_audio: int = Field(default=0, description="Number of lessons that had audio generated")
    audio_files_generated: int = Field(default=0, description="Total number of audio files generated")
    audio_generation_time_seconds: float = Field(default=0.0, description="Total time spent generating audio")
    audio_errors: List[str] = Field(default_factory=list, description="Audio generation errors")


class GenerationStats(BaseModel):
    program_generation_time_seconds: float
    lesson_generation_times_seconds: List[float]
    total_time_seconds: float
    lessons_generated: int
    errors_encountered: List[str] = Field(default_factory=list)
    audio_stats: AudioGenerationStats


class GenerateFullProgramResponse(BaseModel):
    status: str
    program_id: str
    title: str
    description: str
    outline: List[Dict[str, Any]]
    lessons: List[Dict[str, Any]]
    generation_stats: GenerationStats
    timestamp: datetime


# ---------- Route ----------

@router.post("/generate-full-program", summary="Generate Full Program", response_model=GenerateFullProgramResponse)
async def generate_full_program(body: GenerateFullProgramRequest) -> GenerateFullProgramResponse:
    """
    Generates a complete program with all lessons in one request.
    
    This endpoint will:
    1. Create the program skeleton using generate_program
    2. Generate all lessons using generate_lesson
    3. Optionally generate TTS audio for lessons with conversation chunks
    4. Return the complete program with all lessons and audio metadata
    
    Audio generation is enabled by default and will create TTS audio files
    for any lessons that contain conversation chunks. Audio files are saved
    in the program_audios directory and organized by lesson ID.
    
    Uses existing generate_program and generate_lesson functions for consistency.
    """
    start_time = datetime.now()
    lesson_times: List[float] = []
    errors: List[str] = []
    program_id: Optional[str] = None
    
    try:
        # Step 1: Generate program skeleton using existing function
        logger.info("Starting full program generation - creating program skeleton")
        program_start = datetime.now()
        
        program_request = GenerateProgramRequest(
            focus_area=body.focus_area,
            target_outcome=body.target_outcome,
            context=body.context,
        )
        
        program_response = await generate_program(program_request)
        program_generation_time = (datetime.now() - program_start).total_seconds()
        program_id = program_response.program_id
        
        logger.info(f"Program skeleton generated successfully: {program_id}")
        
        # Step 2: Generate all lessons using existing function
        generated_lessons: List[Dict[str, Any]] = []
        total_lessons = len(program_response.outline)
        
        for day_number in range(1, total_lessons + 1):
            lesson_start = datetime.now()
            
            try:
                logger.info(f"Generating lesson {day_number}/{total_lessons} for program {program_id}")
                
                lesson_request = GenerateLessonIn(
                    program_id=program_id,
                    day_number=day_number,
                    model=body.model
                )
                
                lesson_response = await generate_lesson(lesson_request)
                lesson_time = (datetime.now() - lesson_start).total_seconds()
                lesson_times.append(lesson_time)
                
                # Get the full lesson data from storage
                updated_program_data = get_program(program_id)
                if updated_program_data:
                    program_lessons = updated_program_data.get("lessons", [])
                    day_lesson = next((l for l in program_lessons if l.get("day_number") == day_number), None)
                    if day_lesson:
                        generated_lessons.append(day_lesson)
                        logger.info(f"Lesson {day_number} generated successfully in {lesson_time:.2f}s")
                    else:
                        error_msg = f"Lesson {day_number} generated but not found in storage"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        lesson_times[-1] = 0.0  # Mark as failed
                else:
                    error_msg = f"Program data not found after generating lesson {day_number}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    lesson_times[-1] = 0.0  # Mark as failed
                
            except HTTPException as http_e:
                error_msg = f"HTTP error generating lesson {day_number}: status={http_e.status_code}, detail={http_e.detail}"
                errors.append(error_msg)
                logger.error(error_msg)
                lesson_times.append(0.0)
                continue
                
            except Exception as e:
                error_msg = f"Unexpected error generating lesson {day_number}: {type(e).__name__}: {str(e)}"
                errors.append(error_msg)
                logger.exception(f"Full exception details for lesson {day_number}: {e}")
                lesson_times.append(0.0)
                continue
        
        # Step 3: Generate audio for lessons with conversation chunks (if requested)
        audio_stats = AudioGenerationStats(audio_generation_enabled=body.generate_audio)
        
        if body.generate_audio and generated_lessons:
            logger.info("Starting audio generation for lessons with conversation chunks")
            audio_start = datetime.now()
            audio_service = AudioGeneratorService()
            
            for lesson_data in generated_lessons:
                lesson_id = lesson_data.get("id")
                if not lesson_id:
                    continue
                    
                # Check if lesson has conversation chunks
                conversation_chunks = lesson_data.get("conversation_chunks", [])
                if not conversation_chunks:
                    logger.debug(f"Lesson {lesson_id} has no conversation chunks, skipping audio generation")
                    continue
                
                try:
                    logger.info(f"Generating audio for lesson {lesson_id}")
                    
                    audio_result = await audio_service.generate_lesson_audio(
                        lesson_uuid=lesson_id,
                        voice_mapping=body.voice_mapping
                    )
                    
                    if audio_result.get("success"):
                        audio_stats.lessons_with_audio += 1
                        audio_stats.audio_files_generated += audio_result.get("files_generated", 0)
                        logger.info(f"Successfully generated audio for lesson {lesson_id}: {audio_result.get('files_generated', 0)} files")
                    else:
                        error_msg = f"Audio generation failed for lesson {lesson_id}: {audio_result.get('error', 'Unknown error')}"
                        audio_stats.audio_errors.append(error_msg)
                        logger.warning(error_msg)
                
                except Exception as e:
                    error_msg = f"Audio generation error for lesson {lesson_id}: {str(e)}"
                    audio_stats.audio_errors.append(error_msg)
                    logger.error(error_msg)
                    continue
            
            audio_stats.audio_generation_time_seconds = (datetime.now() - audio_start).total_seconds()
            logger.info(f"Audio generation completed: {audio_stats.lessons_with_audio} lessons, {audio_stats.audio_files_generated} files in {audio_stats.audio_generation_time_seconds:.2f}s")
        else:
            logger.info("Audio generation disabled or no lessons generated")
        
        # Step 4: Get final program state and prepare response
        final_program_data = get_program(program_id)
        if not final_program_data:
            raise HTTPException(status_code=500, detail="Program data lost during generation")
        
        # Update lessons from final program state (in case audio metadata was added)
        if body.generate_audio:
            final_lessons = final_program_data.get("lessons", [])
            generated_lessons = [
                lesson for lesson in final_lessons 
                if lesson.get("day_number") and lesson.get("day_number") <= total_lessons
            ]
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Determine status based on errors (including audio errors)
        all_errors = errors + audio_stats.audio_errors
        status = "completed" if not all_errors else "partial_completion"
        if len(generated_lessons) == 0:
            status = "failed"
            raise HTTPException(status_code=500, detail="No lessons were generated successfully")
        
        # Build generation stats
        generation_stats = GenerationStats(
            program_generation_time_seconds=program_generation_time,
            lesson_generation_times_seconds=lesson_times,
            total_time_seconds=total_time,
            lessons_generated=len(generated_lessons),
            errors_encountered=errors,
            audio_stats=audio_stats
        )
        
        logger.info(f"Full program generation completed: {status}, {len(generated_lessons)}/{total_lessons} lessons")
        
        return GenerateFullProgramResponse(
            status=status,
            program_id=program_id,
            title=program_response.title,
            description=program_response.description,
            outline=program_response.outline,
            lessons=generated_lessons,
            generation_stats=generation_stats,
            timestamp=datetime.now(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to generate full program: {e}")
        
        # Rollback: Delete program if it was created but generation failed
        if program_id:
            try:
                delete_program(program_id)
                logger.info(f"Rolled back program {program_id} due to generation failure")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup program {program_id}: {cleanup_error}")
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "failed_to_generate_full_program",
                "message": str(e),
                "errors_encountered": errors
            }
        )
