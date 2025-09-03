# LifeCurriculum Backend - Project Brief

## Project Overview
LifeCurriculum is a FastAPI-based backend service designed to generate and manage personalized 5-day microlearning programs using AI. The system creates context-aware learning programs that adapt to different learning environments (home, driving, workout) and generates sophisticated, mentor-quality educational content.

## Core Purpose
Transform learning goals into structured, context-aware 5-day microlearning programs that provide personalized, high-quality educational experiences with specific practice goals tailored to the learner's environment and lifestyle.

## Key Requirements

### Functional Requirements
1. **5-Day Program Generation**: Create comprehensive microlearning programs with focus areas, target outcomes, and context-specific approaches
2. **Context-Aware Learning**: Adapt programs for home, driving, and workout learning scenarios
3. **Program Persistence**: Store and retrieve generated programs using JSONL file-based storage
4. **Sophisticated AI Prompting**: Generate mentor-quality content with detailed system prompts
5. **Program Management**: Full CRUD operations for program lifecycle management
6. **Health Monitoring**: Comprehensive health check endpoints

### Technical Requirements
1. **Framework**: FastAPI for high-performance async API development
2. **AI Integration**: OpenAI API for curriculum generation
3. **Storage**: MinIO for distributed file storage
4. **Architecture**: Clean separation with DAOs, models, and managers
5. **Testing**: Comprehensive test coverage using pytest
6. **Documentation**: Auto-generated API docs via FastAPI

## Success Criteria
- Users can submit learning topics and receive structured curricula
- System handles concurrent requests efficiently
- Integration with external services (OpenAI, MinIO) is reliable
- API responses are fast and well-structured
- System is maintainable and extensible

## Current Status
- Core FastAPI application structure implemented
- OpenAI integration functional for curriculum generation
- MinIO DAO implemented for file operations
- Health check endpoints operational
- Session management system working
- Basic activity endpoints as placeholders

## Scope
- **In Scope**: Curriculum generation, session management, basic activity management, file storage
- **Out of Scope**: User authentication, payment processing, advanced analytics, mobile app development

## Technology Stack
- **Backend**: FastAPI, Python 3.8+
- **AI Services**: OpenAI API (GPT models)
- **Storage**: MinIO (S3-compatible object storage)
- **Testing**: pytest
- **Deployment**: uvicorn server
