from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.storage.program_store import get_program, list_programs

router = APIRouter(prefix="/programs", tags=["Programs"])  # ✅ Capital P

class ProgramListResponse(BaseModel):
    items: List[Dict[str, Any]]
    offset: int
    limit: int

@router.get("/{program_id}", response_model=Dict[str, Any], summary="Get Program By Id")
def get_program_by_id(program_id: str):  # ← Keep as regular function
    """Fetch a single Program by its ID"""
    p = get_program(program_id)
    if not p:
        raise HTTPException(status_code=404, detail="Program not found")
    return p

@router.get("/{program_id}/lessons/{day_number}", summary="Get Single Lesson")
def get_lesson(program_id: str, day_number: int):  # ← Remove async
    program_data = get_program(program_id)
    if not program_data:
        raise HTTPException(status_code=404, detail="Program not found")
    
    lessons = program_data.get("lessons", [])
    lesson = next((l for l in lessons if l.get("day_number") == day_number), None)
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return lesson

@router.get("", response_model=ProgramListResponse, summary="List All Programs")
def list_all_programs(offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):  # ← Keep as regular function
    """List saved Programs"""
    return {"items": list_programs(offset, limit), "offset": offset, "limit": limit}