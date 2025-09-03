"""
Programs API router - combines all program endpoints 
"""
from fastapi import APIRouter

from .generate_program import router as generate_program_router  # ← Fix this name
from .read_program import router as read_program_router  
from .generate_lesson import router as generate_lesson_router
from .generate_full_program import router as generate_full_program_router
from .generate_lesson_audio import router as generate_lesson_audio_router
from .get_all_lessons import router as get_all_lessons_router
from .stream_lesson_audio import router as stream_lesson_audio_router
from .complete_lesson import router as complete_lesson_router
from .evaluate_lesson_answer import router as evaluate_lesson_answer_router

# Create main router
router = APIRouter()

# Include all endpoint routers
router.include_router(generate_program_router)  # ← And this one
router.include_router(read_program_router)
router.include_router(generate_lesson_router)
router.include_router(generate_full_program_router)
router.include_router(generate_lesson_audio_router)
router.include_router(get_all_lessons_router)
router.include_router(stream_lesson_audio_router)
router.include_router(complete_lesson_router)
router.include_router(evaluate_lesson_answer_router)
