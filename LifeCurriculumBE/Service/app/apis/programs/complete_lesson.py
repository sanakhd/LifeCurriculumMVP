"""
Complete lesson endpoint - marks a lesson as completed and updates timestamps
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...models.responses import BaseResponse
from ...models.enums import LessonStatus
from ...storage.program_store import get_lesson_by_uuid, upsert_program
from ...logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class CompleteLessonRequest(BaseModel):
    """Request model for completing a lesson"""
    time_spent_seconds: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Total time spent on the lesson in seconds"
    )
    completion_method: Optional[str] = Field(
        default="full",
        description="How the lesson was completed (full/skipped/partial)"
    )
    user_rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="User's rating of the lesson (1-5)"
    )


class CompleteLessonResponse(BaseResponse):
    """Response model for completing a lesson"""
    lesson_id: str
    completed_at: datetime
    previous_status: str
    time_spent_seconds: Optional[int]


@router.post(
    "/lessons/{lesson_id}/complete",
    response_model=CompleteLessonResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a lesson as completed",
    description="Updates lesson status to completed and sets completion timestamp"
)
async def complete_lesson(
    lesson_id: str,
    request: CompleteLessonRequest
) -> CompleteLessonResponse:
    """
    Mark a lesson as completed and update its timestamp information.
    
    Args:
        lesson_id: UUID of the lesson to complete
        request: Request body containing optional completion details
        
    Returns:
        CompleteLessonResponse with updated lesson information
        
    Raises:
        HTTPException: If lesson not found or already completed
    """
    logger.info(f"Completing lesson {lesson_id}")
    
    # Find the lesson across all programs
    result = get_lesson_by_uuid(lesson_id)
    if not result:
        logger.warning(f"Lesson {lesson_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID {lesson_id} not found"
        )
    
    program_dict, lesson_dict = result
    previous_status = lesson_dict.get("status", LessonStatus.NOT_STARTED)
    
    # Check if already completed
    if previous_status == LessonStatus.COMPLETED:
        logger.info(f"Lesson {lesson_id} already completed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lesson is already completed"
        )
    
    # Update lesson completion data
    completion_timestamp = datetime.now()
    lesson_dict["status"] = LessonStatus.COMPLETED
    lesson_dict["completed_at"] = completion_timestamp.isoformat()
    
    # Set started_at if not already set
    if not lesson_dict.get("started_at"):
        lesson_dict["started_at"] = completion_timestamp.isoformat()
    
    # Update optional fields if provided
    if request.time_spent_seconds is not None:
        lesson_dict["time_spent_seconds"] = request.time_spent_seconds
    
    if request.completion_method:
        lesson_dict["completion_method"] = request.completion_method
        
    if request.user_rating is not None:
        lesson_dict["user_rating"] = request.user_rating
    
    # Save the updated program back to storage
    try:
        upsert_program(program_dict)
        logger.info(f"Successfully completed lesson {lesson_id}")
    except Exception as e:
        logger.error(f"Failed to save lesson completion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save lesson completion"
        )
    
    return CompleteLessonResponse(
        success=True,
        message=f"Lesson {lesson_id} marked as completed",
        timestamp=completion_timestamp,
        lesson_id=lesson_id,
        completed_at=completion_timestamp,
        previous_status=previous_status,
        time_spent_seconds=request.time_spent_seconds
    )


@router.post(
    "/lessons/{lesson_id}/start",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a lesson as started",
    description="Updates lesson status to in_progress and sets start timestamp"
)
async def start_lesson(lesson_id: str) -> BaseResponse:
    """
    Mark a lesson as started and set the start timestamp.
    
    Args:
        lesson_id: UUID of the lesson to start
        
    Returns:
        BaseResponse confirming the lesson was started
        
    Raises:
        HTTPException: If lesson not found or already started/completed
    """
    logger.info(f"Starting lesson {lesson_id}")
    
    # Find the lesson across all programs
    result = get_lesson_by_uuid(lesson_id)
    if not result:
        logger.warning(f"Lesson {lesson_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID {lesson_id} not found"
        )
    
    program_dict, lesson_dict = result
    current_status = lesson_dict.get("status", LessonStatus.NOT_STARTED)
    
    # Only update if not already started or completed
    if current_status in [LessonStatus.IN_PROGRESS, LessonStatus.COMPLETED]:
        logger.info(f"Lesson {lesson_id} already started or completed")
        return BaseResponse(
            success=True,
            message=f"Lesson {lesson_id} was already started",
            timestamp=datetime.now()
        )
    
    # Update lesson start data
    start_timestamp = datetime.now()
    lesson_dict["status"] = LessonStatus.IN_PROGRESS
    lesson_dict["started_at"] = start_timestamp.isoformat()
    
    # Save the updated program back to storage
    try:
        upsert_program(program_dict)
        logger.info(f"Successfully started lesson {lesson_id}")
    except Exception as e:
        logger.error(f"Failed to save lesson start: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save lesson start"
        )
    
    return BaseResponse(
        success=True,
        message=f"Lesson {lesson_id} marked as started",
        timestamp=start_timestamp
    )
