from pydantic import Field, field_validator
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.models.lesson import Lesson  # ✅ direct import fixes forward ref issue
from app.models.base import BaseEntity
from app.models.enums import ContextType, ProgramStatus


class Program(BaseEntity):
    # User input from two-step onboarding
    focus_area: str = Field(..., min_length=5, max_length=500, description="What they want to work on (Step 1)")
    target_outcome: str = Field(..., min_length=5, max_length=300, description="Specific measurable goal (Step 2)")
    context: ContextType = Field(..., description="Learning environment chosen")
    
    # Generated program metadata (from AI)
    title: str = Field(..., min_length=1, max_length=100, description="AI-generated program title")
    description: Optional[str] = Field(default=None, max_length=500, description="AI-generated program description")
    total_lessons: int = Field(default=5, ge=1, le=10, description="Number of lessons in program")
    
    # Progress tracking
    status: ProgramStatus = Field(default=ProgramStatus.ACTIVE)
    current_lesson_day: int = Field(default=1, ge=1, description="Which day user is currently on")
    lessons_completed: int = Field(default=0, ge=0, description="Number of lessons completed")
    
    # Timestamps
    started_at: Optional[datetime] = Field(default=None, description="When user started first lesson")
    completed_at: Optional[datetime] = Field(default=None, description="When user completed all lessons")
    last_accessed_at: Optional[datetime] = Field(default=None, description="Last time user opened program")
    
    # Session tracking (for anonymous users)
    session_token: Optional[str] = Field(default=None, description="Anonymous session identifier")

    # Stores the full input and output from the initial outline generation step
    outline: List[Dict[str, Any]] = Field(default_factory=list, description="List of outline items (one per lesson/day)")
    lessons: List[Lesson] = Field(default_factory=list, description="Full lessons generated for this program")

    @field_validator('lessons_completed')
    @classmethod
    def validate_lessons_completed(cls, v: int, info) -> int:
        total_lessons = info.data.get('total_lessons', 5)
        if v > total_lessons:
            raise ValueError('Completed lessons cannot exceed total lessons')
        return v
    
    @property
    def completion_percentage(self) -> float:
        """Returns completion percentage as decimal (0.0 - 1.0)"""
        return self.lessons_completed / self.total_lessons if self.total_lessons > 0 else 0.0
    
    @property
    def is_completed(self) -> bool:
        """Check if program is fully completed"""
        return self.lessons_completed >= self.total_lessons
