"""
LifeCurriculum FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apis.health import router as health_router
from app.apis.programs.router import router as programs_router

from app.config import get_settings
from app.logger import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    settings = get_settings()
    
    # Initialize logging system
    setup_logging(log_level=settings.log_level, log_file=settings.log_file)
    logger = get_logger(__name__)
    
    # Startup
    logger.info("Starting LifeCurriculum service...")
    logger.info(f"Log level set to: {settings.log_level}")
    if settings.log_file:
        logger.info(f"Logging to file: {settings.log_file}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down LifeCurriculum service...")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="LifeCurriculum",
        description="Backend service for managing life curriculum activities",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(health_router, tags=["Health"])
    app.include_router(programs_router, prefix="/api/v1", tags=["Programs"])

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
