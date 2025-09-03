"""
Health check API endpoints
"""
from datetime import datetime

from fastapi import APIRouter

from app.logger import get_logger
from app.models.responses import HealthResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/ping", response_model=HealthResponse, summary="Health Check")
@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check() -> HealthResponse:
    """
    Check if the LifeCurriculum service is running and healthy.
    
    Returns:
        HealthResponse: Service status information
    """
    logger.debug("Processing health check request")
    
    response = HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        service="LifeCurriculum",
        version="1.0.0"
    )
    
    logger.info("Health check completed successfully")
    return response
