from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

from .base import BaseEntity
from .enums import ContextType, ResponseType, LessonStatus

# ---- Structured pieces to match the UI ----

class ConversationTurn(BaseModel):
    # Strictly enforce only these two speakers for simpler front-end rendering
    speaker: Literal["Host A", "Host B"] = Field(
        ..., description="Who is speaking in this turn"
    )
    text: str = Field(..., min_length=1, description="What the speaker says")
    # Optional: attach media per turn in future (images, audio snippets, etc.)
    media: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional per-turn media or metadata"
    )

class InteractionSpec(BaseModel):
    """
    MVP interaction spec supporting your response types.
    Keep fields generic so the frontend can render by type.
    """
    type: ResponseType = Field(..., description="Type of learner interaction")
    prompt: str = Field(..., min_length=1, description="Instruction or question for the learner")

    # Choice-based (multiple_choice)
    options: Optional[List[str]] = Field(default=None, description="Options for choice-based interactions")
    # IMPORTANT: string label, not index (aligned with evaluate endpoint & frontend)
    correct_option: Optional[str] = Field(default=None, description="The correct option string (must be one of 'options')")

    # Scale/slider
    scale_min: Optional[int] = Field(default=None, description="Min value for scale/slider")
    scale_max: Optional[int] = Field(default=None, description="Max value for scale/slider")
    min_label: Optional[str] = Field(default=None, description="Label for minimum scale value")
    max_label: Optional[str] = Field(default=None, description="Label for maximum scale value")

    # Text/Reflection (HOME context)
    placeholder: Optional[str] = Field(default=None, description="Placeholder text for text inputs")
    min_words: Optional[int] = Field(default=None, description="Minimum word count for text responses")
    instructions: Optional[str] = Field(default=None, description="Additional instructions for the exercise")

    # Audio (DRIVING context)
    duration_seconds: Optional[int] = Field(default=None, description="Duration for audio responses")
    guidance: Optional[str] = Field(default=None, description="Additional guidance for audio exercises")

    # Flashcards (optional future)
    flashcards: Optional[List[Dict[str, str]]] = Field(
        default=None, description='Flashcards: [{"front": "...", "back": "..."}]'
    )

    # Extra per-type settings
    config: Optional[Dict[str, Any]] = Field(default=None, description="Extra per-type config")

class Lesson(BaseEntity):
    # Relationships
    program_id: str = Field(..., description="Parent program ID")
    day_number: int = Field(..., ge=1, le=10, description="Day number in program sequence")
    
    # Core lesson content (AI generated)
    title: str = Field(..., min_length=1, max_length=100, description="Lesson title")
    description: str = Field(..., min_length=1, max_length=500, description="Lesson description/subtitle")
    audio_section_title: str = Field(..., min_length=1, max_length=100, description="Title for audio section")

    # Conversation-first structure for your UI
    conversation_chunks: List[ConversationTurn] = Field(
        default_factory=list,
        description="Turn-by-turn conversation between hosts (render directly in UI)"
    )

    # Back-compat / convenience: concatenated transcript.
    # If not provided, we auto-generate it from conversation_chunks.
    conversation_script: Optional[str] = Field(
        default=None,
        description="Full transcript (auto-derived from conversation_chunks if omitted)"
    )
    estimated_conversation_duration: int = Field(
        default=3, ge=1, le=10, description="Conversation length in minutes"
    )
    
    # MVP: at most two interactions for simpler rendering
    primary_interaction: Optional[InteractionSpec] = Field(
        default=None, description="First learner interaction after the conversation"
    )
    secondary_interaction: Optional[InteractionSpec] = Field(
        default=None, description="Second (optional) learner interaction"
    )

    # For reproducibility & traceability
    generation_prompt: Optional[str] = Field(
        default=None,
        description="Exact per-lesson prompt used to generate conversation + interactions"
    )
    outline_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Copy of the outline item used when generating this lesson"
    )
    
    # Legacy single-practice fields (optional; kept if other code expects them)
    practice_type: Optional[ResponseType] = Field(
        default=None, description="[Legacy] Single practice type; prefer primary/secondary interactions"
    )
    practice_prompt: Optional[str] = Field(
        default=None, description="[Legacy] Single practice prompt; prefer primary/secondary interactions"
    )
    practice_data: Optional[Dict[str, Any]] = Field(
        default=None, description="[Legacy] Arbitrary practice payload; prefer primary/secondary interactions"
    )
    
    # Lesson metadata
    estimated_total_duration: int = Field(default=5, ge=3, le=15, description="Total lesson time in minutes")
    context: ContextType = Field(..., description="Optimized for this learning context")
    learning_objectives: Optional[List[str]] = Field(default=None, description="What user will learn")
    
    # Progress and completion
    status: LessonStatus = Field(default=LessonStatus.NOT_STARTED)
    started_at: Optional[datetime] = Field(default=None, description="When user first opened lesson")
    completed_at: Optional[datetime] = Field(default=None, description="When user finished lesson")
    time_spent_seconds: Optional[int] = Field(default=None, ge=0, description="Total time user spent")
    
    # Audio file (if generated)
    audio_file_path: Optional[str] = Field(default=None, description="Path to generated audio file")
    audio_file_size_bytes: Optional[int] = Field(default=None, ge=0)
    audio_duration_seconds: Optional[int] = Field(default=None, ge=0)
    
    # User engagement
    user_rating: Optional[int] = Field(default=None, ge=1, le=5, description="User's rating of lesson")
    completion_method: Optional[str] = Field(default=None, description="How lesson was completed (full/skipped/partial)")
    
    @field_validator('day_number')
    @classmethod
    def validate_day_number_sequence(cls, v: int) -> int:
        if v < 1:
            raise ValueError('Day number must be at least 1')
        return v

    @model_validator(mode="after")
    def _ensure_transcript(self):
        """
        If conversation_script is missing, derive it from conversation_chunks so callers relying
        on a flat string still work. Format: "Speaker: text" per line.
        """
        if not self.conversation_script and self.conversation_chunks:
            lines = [f"{t.speaker}: {t.text}".strip() for t in self.conversation_chunks]
            self.conversation_script = "\n".join(lines)
        return self

    @property
    def interactions(self) -> List[InteractionSpec]:
        """Convenience accessor to iterate interactions in order."""
        out: List[InteractionSpec] = []
        if self.primary_interaction:
            out.append(self.primary_interaction)
        if self.secondary_interaction:
            out.append(self.secondary_interaction)
        return out
    
    @property
    def is_completed(self) -> bool:
        """Check if lesson is completed"""
        return self.status == LessonStatus.COMPLETED
    
    @property
    def duration_minutes(self) -> float:
        """Convert time spent to minutes"""
        return (self.time_spent_seconds / 60) if self.time_spent_seconds else 0.0