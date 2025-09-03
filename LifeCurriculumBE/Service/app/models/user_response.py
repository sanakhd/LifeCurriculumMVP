from pydantic import Field, field_validator
from typing import Optional, List, Dict, Any
from .base import BaseEntity
from .enums import ResponseType

class UserResponse(BaseEntity):
    # Relationships
    lesson_id: str = Field(..., description="Lesson this response belongs to")
    program_id: str = Field(..., description="Program this response belongs to")
    
    # Response metadata
    response_type: ResponseType = Field(..., description="Type of interaction response")
    prompt_text: str = Field(..., description="The original prompt/question")
    
    # Response content (flexible - different fields used based on response_type)
    text_content: Optional[str] = Field(default=None, max_length=1000, description="Text response content")
    audio_file_path: Optional[str] = Field(default=None, description="Path to audio response file")
    selected_option_id: Optional[str] = Field(default=None, description="Selected choice ID for choice-based responses")
    scale_value: Optional[int] = Field(default=None, ge=1, le=10, description="Rating/scale value")
    structured_data: Optional[Dict[str, Any]] = Field(default=None, description="Complex response data")
    
    # Response quality and engagement
    response_time_seconds: Optional[int] = Field(default=None, ge=1, description="Time taken to respond")
    confidence_level: Optional[int] = Field(default=None, ge=1, le=5, description="User's confidence in response")
    is_thoughtful: Optional[bool] = Field(default=None, description="Indicates if response seems thoughtful vs rushed")
    
    # Audio metadata (if applicable)
    audio_duration_seconds: Optional[int] = Field(default=None, ge=1)
    audio_file_size_bytes: Optional[int] = Field(default=None, ge=0)
    audio_transcription: Optional[str] = Field(default=None, description="AI transcription of audio response")
    
    # Feedback and learning
    ai_insight_shown: Optional[str] = Field(default=None, description="Insight shown to user after response")
    user_found_helpful: Optional[bool] = Field(default=None, description="Whether user found the insight helpful")
    
    @field_validator('response_time_seconds')
    @classmethod
    def validate_reasonable_response_time(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v > 3600:  # More than 1 hour seems unreasonable
            raise ValueError('Response time seems unreasonably long')
        return v
    
    @property
    def has_content(self) -> bool:
        """Check if response has any actual content"""
        return any([
            self.text_content,
            self.audio_file_path,
            self.selected_option_id,
            self.scale_value is not None,
            self.structured_data
        ])