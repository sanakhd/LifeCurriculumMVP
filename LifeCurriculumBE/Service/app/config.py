"""
Configuration settings for LifeCurriculum service
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS settings
    allowed_origins: List[str] = ["*"]
    
    # Database configuration (for future use)
    database_url: str = "sqlite:///./lifecurriculum.db"
    
    # External service configurations (for DAOs)
    external_service_timeout: int = 30
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None  # Set to file path if you want to log to file
    
    # OpenAI Configuration
    openai_api_key: str = "INPUTYOURAPIKEY"
    openai_default_model: str = "gpt-4o-audio-preview"
    openai_text_model: str = "gpt-4o"
    openai_tts_model: str = "tts-1"
    openai_default_voice: str = "alloy"
    openai_default_audio_format: str = "wav"
    openai_temperature: float = 1
    openai_max_tokens: Optional[int] = None
    
    # MinIO Configuration
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "password"
    minio_secure: bool = False
    minio_generated_audio_bucket: str = "lc-generated-audio"
    minio_recorded_audio_bucket: str = "lc-recorded-user-audio"
    
    # Curriculum Generation System Prompt
    curriculum_system_prompt: str = """You are an expert educational curriculum designer. Your task is to create comprehensive, structured learning curricula based on user requests.

When a user asks to learn about a topic, you should:

1. Create exactly 5 lessons that progressively build upon each other
2. Each lesson should have:
   - A clear, descriptive title
   - Learning objectives (2-3 bullet points)
   - Key concepts to be covered
   - Practical activities or exercises
   - Estimated time duration

3. Structure the curriculum to go from foundational concepts to more advanced applications
4. Ensure each lesson connects logically to the next
5. Include hands-on activities where appropriate
6. Make the content engaging and practical

Format your response as a well-structured curriculum with clear sections for each lesson. Use proper formatting with headers, bullet points, and clear organization."""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
