from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from app.storage.program_store import get_all_lesson_ids

router = APIRouter(prefix="/programs", tags=["Programs"])

class LessonIdsResponse(BaseModel):
    lesson_ids: List[str]
    count: int

@router.get("/lessons/ids", response_model=LessonIdsResponse, summary="Get All Lesson IDs")
def get_all_lesson_ids_endpoint():
    """Get all lesson IDs from all programs in programs.jsonl"""
    lesson_ids = get_all_lesson_ids()
    return LessonIdsResponse(lesson_ids=lesson_ids, count=len(lesson_ids))
