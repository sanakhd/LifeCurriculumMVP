"""
Pydantic models for OpenAI API requests and responses
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union


class TextGenerationRequest(BaseModel):
    """Request model for text generation"""
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class TTSRequest(BaseModel):
    """Request model for Text-to-Speech"""
    text: str
    voice: Optional[str] = None
    model: Optional[str] = None
    response_format: Optional[str] = None


class AudioTextGenerationRequest(BaseModel):
    """Request model for text generation with audio response"""
    messages: List[Dict[str, str]]
    voice: Optional[str] = None
    audio_format: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class AudioTranscriptionRequest(BaseModel):
    """Request model for audio transcription"""
    audio_data: str  # base64 encoded audio
    audio_format: str  # wav, mp3, etc.
    model: Optional[str] = None
    language: Optional[str] = None


class TextGenerationResponse(BaseModel):
    """Response model for text generation"""
    text: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class TTSResponse(BaseModel):
    """Response model for TTS"""
    audio_data: bytes
    format: str


class AudioTextGenerationResponse(BaseModel):
    """Response model for text generation with audio"""
    text: str
    audio_data: Optional[bytes] = None
    audio_format: Optional[str] = None
    model: str
    usage: Optional[Dict[str, Any]] = None


class AudioTranscriptionResponse(BaseModel):
    """Response model for audio transcription"""
    text: str
    language: Optional[str] = None
    model: str
