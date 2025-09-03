"""
Generate Program API endpoint
Creates program structure with outline and metadata.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.logger import get_logger
from app.storage.program_store import upsert_program
from app.models.program import Program
from app.models.enums import ProgramStatus
from app.models.enums import ContextType
from app.models.openai_models import TextGenerationRequest
from app.daos.openai_dao import OpenAIDAO

logger = get_logger(__name__)
router = APIRouter(prefix="/programs", tags=["Programs"])
dao = OpenAIDAO()


# ---------- Request / Response ----------

class GenerateProgramRequest(BaseModel):
    focus_area: str = Field(..., min_length=5, description="User's one-sentence focus/goal area")
    target_outcome: str = Field(..., min_length=5, description="Concrete outcome for the week")
    context: ContextType
    prompt: Optional[str] = None

    @field_validator("focus_area", "target_outcome")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v


class GenerateProgramResponse(BaseModel):
    program_id: str
    title: str
    description: str
    outline: List[Dict[str, Any]]
    timestamp: datetime


# ---------- Helper Functions ----------

def build_program_prompt(focus_area: str, target_outcome: str, context: ContextType) -> str:
    """Build prompt for generating program structure and outline."""
    context_descriptions = {
        ContextType.HOME: "listening at home with full attention and ability to take notes",
        ContextType.DRIVING: "listening while driving, needing audio-only content that's safe for the road",
        ContextType.WORKOUT: "listening during exercise, preferring shorter segments that fit workout timing"
    }
    
    context_desc = context_descriptions.get(context, "general listening context")
    
    return f"""
You are creating a 5-day learning program structure. Return STRICT JSON ONLY.

USER INPUT:
- Focus Area: {focus_area}
- Target Outcome: {target_outcome}
- Listening Context: {context_desc}

PROGRAM REQUIREMENTS:
- Create exactly 5 days of structured learning
- Each day should build logically toward the target outcome
- Content should be appropriate for the listening context
- Generate a compelling program title and description
- Create detailed daily outlines with clear learning objectives

DAILY STRUCTURE:
Each day should have:
- A specific title that indicates the day's focus
- A summary of what will be covered (2-3 sentences)
- Clear learning objectives
- Estimated time commitment
- How this day contributes to the overall target outcome

PROGRESSION LOGIC:
Day 1: Foundation/Context - establish key concepts and why they matter
Day 2: Core Mechanism - dive into the fundamental "how" or "why" 
Day 3: Application - practical implementation and real-world use
Day 4: Advanced/Nuanced - handling complexity and edge cases
Day 5: Integration - putting it all together and sustainable practice

OUTPUT EXACTLY THIS JSON:
{{
  "title": "Engaging program title",
  "description": "2-3 sentence program overview explaining the journey and outcome",
  "outline": [
    {{
      "day_number": 1,
      "title": "Day 1 specific focus title",
      "summary": "What this day covers and why it's important",
      "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
      "estimated_duration_minutes": 15,
      "key_concepts": ["Concept 1", "Concept 2"]
    }},
    {{
      "day_number": 2,
      "title": "Day 2 specific focus title", 
      "summary": "What this day covers and why it's important",
      "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
      "estimated_duration_minutes": 15,
      "key_concepts": ["Concept 1", "Concept 2"]
    }},
    {{
      "day_number": 3,
      "title": "Day 3 specific focus title",
      "summary": "What this day covers and why it's important", 
      "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
      "estimated_duration_minutes": 15,
      "key_concepts": ["Concept 1", "Concept 2"]
    }},
    {{
      "day_number": 4,
      "title": "Day 4 specific focus title",
      "summary": "What this day covers and why it's important",
      "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"], 
      "estimated_duration_minutes": 15,
      "key_concepts": ["Concept 1", "Concept 2"]
    }},
    {{
      "day_number": 5,
      "title": "Day 5 specific focus title",
      "summary": "What this day covers and why it's important",
      "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
      "estimated_duration_minutes": 15,
      "key_concepts": ["Concept 1", "Concept 2"]
    }}
  ]
}}

QUALITY CRITERIA:
✓ Logical progression from foundation to integration
✓ Each day has distinct focus and clear value
✓ Learning objectives are specific and measurable  
✓ Content appropriate for {context_desc}
✓ Title is engaging and outcome-focused
✓ Description clearly explains the program journey
✓ All 5 days work together toward the target outcome
""".strip()


# ---------- Route ----------

@router.post("/generate-program", summary="Generate Program Structure", response_model=GenerateProgramResponse)
async def generate_program(body: GenerateProgramRequest) -> GenerateProgramResponse:
    """
    Generate a 5-day learning program structure with outline and metadata.
    
    This endpoint creates the program skeleton including:
    - Program title and description
    - 5-day structured outline with learning objectives
    - Logical progression toward the target outcome
    - Context-appropriate content planning
    
    The generated program can then be used with generate_lesson to create
    individual lesson content, or generate_full_program for complete generation.
    """
    try:
        logger.info(f"Generating program structure for focus area: {body.focus_area}")
        
        # Generate program structure using LLM
        program_prompt = build_program_prompt(
            focus_area=body.focus_area,
            target_outcome=body.target_outcome,
            context=body.context
        )
        
        program_request = TextGenerationRequest(
            messages=[{"role": "user", "content": program_prompt}],
            model=None  # Use default model
        )
        
        program_response = await dao.generate_text(program_request)
        program_text = program_response.text.strip()
        
        # Clean up response if it has markdown code fences
        if program_text.startswith("```"):
            program_text = program_text.strip("`")
            if program_text.lower().startswith("json"):
                program_text = program_text[4:].lstrip()
        
        try:
            program_data = json.loads(program_text)
        except Exception as e:
            logger.error(f"Failed to parse program JSON: {e}")
            raise HTTPException(
                status_code=502, 
                detail="LLM did not return valid JSON for program generation"
            )
        
        # Create Program object
        program = Program(
            title=program_data.get("title", "Generated Program"),
            description=program_data.get("description", "A 5-day learning program"),
            focus_area=body.focus_area,
            target_outcome=body.target_outcome,
            context=body.context,
            outline=program_data.get("outline", []),
            status=ProgramStatus.ACTIVE,
            lessons=[],
            generation_prompt=program_prompt
        )
        
        # Validate outline structure
        outline = program_data.get("outline", [])
        if len(outline) != 5:
            raise HTTPException(
                status_code=502,
                detail=f"Program must have exactly 5 days, got {len(outline)}"
            )
        
        for i, day in enumerate(outline, 1):
            if day.get("day_number") != i:
                logger.warning(f"Day number mismatch: expected {i}, got {day.get('day_number')}")
        
        # Store program
        program_dict = program.model_dump(mode="json")
        upsert_program(program_dict)
        
        logger.info(f"Successfully generated program: {program.id}")
        
        return GenerateProgramResponse(
            program_id=program.id,
            title=program.title,
            description=program.description,
            outline=outline,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to generate program: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "failed_to_generate_program",
                "message": str(e)
            }
        )
