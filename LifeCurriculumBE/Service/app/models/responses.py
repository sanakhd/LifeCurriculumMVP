"""
Response models for LifeCurriculum API
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = "healthy"
    timestamp: datetime
    service: str = "LifeCurriculum"
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    timestamp: datetime
    path: Optional[str] = None


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    timestamp: datetime
