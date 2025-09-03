import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.storage.program_store import get_program, upsert_program
from app.models.program import Program
from app.models.lesson import Lesson, ConversationTurn, InteractionSpec
from app.models.openai_models import TextGenerationRequest
from app.daos.openai_dao import OpenAIDAO
from app.logger import get_logger

router = APIRouter(prefix="/programs", tags=["Programs"])
dao = OpenAIDAO()
logger = get_logger(__name__)

# =========================
# Request / Response Models
# =========================

class GenerateLessonIn(BaseModel):
    program_id: str = Field(..., description="Existing Program ID returned by setup-lesson")
    day_number: int = Field(..., ge=1, description="Which day to generate (1-based)")
    model: Optional[str] = Field(None, description="Optional model override")

class GenerateLessonOut(BaseModel):
    success: bool
    program_id: str
    day_number: int
    lesson_id: str

Mode = Literal["knowledge", "skill", "self_insight"]
InteractionKind = Literal["reflection_prompt", "multiple_choice", "teach_back", "self_explanation", "ordering_interaction", "matching_interaction"]

# =========================
# Helpers (history + mode)
# =========================

def collect_history(raw_program: Dict[str, Any]):
    """Return: (used_opening_styles, banned_phrases, used_interaction_types) from existing lessons."""
    used_styles: List[str] = []
    banned_openers: List[str] = []
    used_interaction_types: List[str] = []

    for l in raw_program.get("lessons", []):
        snap = l.get("outline_snapshot") or {}
        style = snap.get("_opening_style")
        if isinstance(style, str):
            used_styles.append(style)

        chunks = l.get("conversation_chunks") or []
        if chunks:
            first_line = chunks[0].get("text", "")
            if first_line:
                banned_openers.append(first_line.strip()[:140])

        pi = l.get("primary_interaction") or {}
        t = pi.get("type")
        if isinstance(t, str):
            used_interaction_types.append(t)

    return used_styles, banned_openers, used_interaction_types


async def classify_mode_with_llm(text: str, model_override: Optional[str] = None) -> Mode:
    """
    Map any user/topic text → {knowledge|skill|self_insight}.
    """
    prompt = f"""
Classify the user's request into exactly one category:

knowledge = understand a topic (facts, concepts, events, history, science).
skill = get better at a practical capability (writing, investing, negotiation, etc.).
self_insight = understand oneself (habits, weaknesses, motivations, patterns).

Text: "{text}"

Respond with ONLY one token: knowledge OR skill OR self_insight.
""".strip()

    req = TextGenerationRequest(
        messages=[{"role": "user", "content": prompt}],
        model=model_override
    )
    resp = await dao.generate_text(req)
    label = (resp.text or "").strip().lower()
    if label not in ("knowledge", "skill", "self_insight"):
        return "knowledge"
    return label  # type: ignore[return-value]


def build_conversation_prompt(program: Program, outline_item: Dict[str, Any]) -> str:
    return f"""
You are generating an organic conversation between two knowledgeable hosts.
Return STRICT JSON ONLY. No prose, no markdown fences.

GOAL
- Create a short, engaging dialogue that feels like overhearing two experts think out loud.
- Focus on ONE clear idea that builds naturally within the 5-day program arc.
- Conversation should feel thoughtful, not rapid-fire.

HOSTS
- Host A (expert): explains mechanisms and trade-offs with concrete, minimal examples.
- Host B (user proxy): asks the questions a thoughtful ChatGPT user would ask — probing "why/how/what-if/contrast/edge-case" and pushing for clarity. Avoid filler like "got it" or "that makes sense".

TOPIC CONTEXT
- Program: {program.title}
- Focus Area: {program.focus_area}
- Listening Context: {program.context}
- Today's Outline Item: {json.dumps(outline_item, ensure_ascii=False)}

CONVERSATION REQUIREMENTS
- 7–10 turns total. Choose the number that best fits the idea (do not pad).
- Target 270–465 words overall (≈ 2:00–3:00 spoken at typical pace).
- Host A generally longer turns (40–80 words); Host B shorter (12–28 words) but probing and specific.
- Include exactly ONE actionable insight that emerges naturally (a concrete instruction or decision rule).
- ENDING: finish the thought (no trailing or mid-sentence). Final turn should signal closure (actionable or decisive acceptance).
- Every turn ends with ., ?, or !  No ellipses.

STYLE DO / DON'T
- DO: Sound spontaneous; build naturally on what was just said.
- DO: Use concrete, relatable examples instead of abstract jargon.
- DON'T: Invent personal stories or fake experiences.
- DON'T: Pad with generic summaries or phatic filler.

OUTPUT EXACTLY THIS JSON:
{{
  "conversation_chunks": [
    {{"speaker": "Host A", "text": "Natural opening thought…"}},
    {{"speaker": "Host B", "text": "Curious follow-up question…"}}
  ]
}}
""".strip()


def choose_interaction_type(
    *, mode: Mode, context: str, day_number: int, used_interaction_types: List[str]
) -> InteractionKind:
    ctx = (context or "").lower()
    last_used = used_interaction_types[-1] if used_interaction_types else None

    if ctx == "driving":
        # Route short-circuits; keep a harmless fallback
        pri = ["multiple_choice"]
    elif ctx == "workout":
        # Tap-only, quick
        pri = ["multiple_choice", "ordering_interaction", "matching_interaction"]
    else:  # home/other
        if mode == "self_insight":
            pri = ["reflection_prompt"]
        elif mode == "skill":
            pri = ["reflection_prompt"]
        else:  # knowledge
            pri = ["teach_back", "self_explanation", "multiple_choice"]

    # rotate by day, avoid repeating last if possible
    for i in range(len(pri)):
        cand = pri[(day_number - 1 + i) % len(pri)]
        if cand != last_used:
            return cand  # type: ignore[return-value]
    return pri[0]  # type: ignore[return-value]



# =========================
# Interaction Prompt (reflection/slider/multiple_choice)
# =========================

# def build_interaction_prompt(
#     *,
#     conversation_chunks: List[Dict[str, Any]],
#     program: Program,
#     outline_item: Dict[str, Any],
#     mode: Mode,
#     context: str,
#     day_number: int,
#     used_interaction_types: List[str],
# ) -> str:
#     """
#     Ask the LLM to return ONE of:
#     - reflection_prompt
#     - slider_scale
#     - multiple_choice

#     The choice is determined by (mode + context + rotation).
#     """
#     conversation_text = "\n".join(f"{c['speaker']}: {c['text']}" for c in conversation_chunks)

#     chosen_type = choose_interaction_type(
#         mode=mode,
#         context=context,
#         day_number=day_number,
#         used_interaction_types=used_interaction_types,
#     )

#     if chosen_type == "reflection_prompt":
#         template = '''{
#   "primary_interaction": {
#     "type": "reflection_prompt",
#     "prompt": "A thoughtful question tied to a specific point the hosts just made",
#     "placeholder": "Write 3–5 sentences...",
#     "min_words": 50,
#     "instructions": "Keep it short (≈2 minutes). Ground your answer in the example from the conversation."
#   }
# }'''
#     elif chosen_type == "slider_scale":
#         template = '''{
#   "primary_interaction": {
#     "type": "slider_scale",
#     "prompt": "Quick self-check anchored to the pattern the hosts named",
#     "scale_min": 1,
#     "scale_max": 10,
#     "min_label": "Not true",
#     "max_label": "Very true",
#     "instructions": "Takes 5–10 seconds; answer instinctively based on the example discussed."
#   }
# }'''
#     else:  # multiple_choice
#         # options: 3–5 strings; correct_option must equal one of options
#         template = '''{
#   "primary_interaction": {
#     "type": "multiple_choice",
#     "prompt": "A quick knowledge check based on a concrete fact or example from the dialogue",
#     "options": ["Option A", "Option B", "Option C"],
#     "correct_option": "Option B",
#     "instructions": "Pick the single best answer."
#   }
# }'''

#     return f"""
# Create ONE short next-step interaction that helps the user apply or check understanding of THIS conversation.
# Return STRICT JSON ONLY. No prose, no markdown.

# CHOSEN_INTERACTION_TYPE: {chosen_type}

# CONVERSATION
# {conversation_text}

# PROGRAM
# - Focus: {program.focus_area}
# - Context: {program.context}
# - Day: {day_number}
# - Outline Item: {json.dumps(outline_item, ensure_ascii=False)}

# GUIDELINES
# - Anchor to ONE specific phrase/mechanism/example from the dialogue (quote or name it).
# - Keep it lightweight (≤ 2 minutes total effort).
# - Make the success signal legible (what the user should notice/decide).

# CRITICAL JSON RULES
# - Return EXACTLY the JSON structure shown in the template below.
# - For multiple_choice: include 3–5 concise options; set "correct_option" to EXACTLY one of the strings in "options".
# - For slider_scale: include all required fields (scale_min, scale_max, min_label, max_label).
# - For reflection_prompt: include placeholder and min_words.

# OUTPUT TEMPLATE (fill with specifics from THIS dialogue)
# {template}

# VALIDATION CHECKLIST
# ✓ JSON matches the template (keys, types)
# ✓ References a concrete detail from the conversation
# ✓ Short, clear, and doable now
# ✓ multiple_choice: 3–5 options; correct_option ∈ options
# ✓ slider_scale: bounds + labels present
# ✓ reflection: placeholder + min_words present
# """.strip()
def build_interaction_prompt(
    *, conversation_chunks, program, outline_item, mode, context, day_number, used_interaction_types
) -> str:
    """
    Return ONE of:
    - multiple_choice
    - reflection_prompt
    - teach_back
    - self_explanation
    - ordering_interaction
    - matching_interaction
    """
    conversation_text = "\n".join(f"{c['speaker']}: {c['text']}" for c in conversation_chunks)
    chosen_type = choose_interaction_type(
        mode=mode, context=context, day_number=day_number, used_interaction_types=used_interaction_types
    )

    tmpl_reflection = '''{
  "primary_interaction": {
    "type": "reflection_prompt",
    "prompt": "A thoughtful question tied to a specific point the hosts just made",
    "placeholder": "Write 3–5 sentences...",
    "min_words": 50,
    "instructions": "Keep it short (≈2 minutes). Ground your answer in the example from the conversation."
  }
}'''

    tmpl_mc = '''{
  "primary_interaction": {
    "type": "multiple_choice",
    "prompt": "A quick check based on a concrete phrase or example from the dialogue",
    "options": ["Option A", "Option B", "Option C"],
    "correct_option": "Option B",
    "instructions": "Tap the single best answer."
  }
}'''

    tmpl_teach_back = '''{
  "primary_interaction": {
    "type": "teach_back",
    "prompt": "Explain today’s concept so a beginner could act on it—then name one common misunderstanding and correct it.",
    "instructions": "Plain language. Prioritize what to do and what to avoid.",
    "config": {
      "variant": "teach_back",
      "fields": [
        {"id":"summary_200","label":"One-message explain (≤200 chars)","max_chars":200},
        {"id":"misconception","label":"Common misunderstanding + fix","max_chars":140}
      ]
    }
  }
}'''

    tmpl_self_expl = '''{
  "primary_interaction": {
    "type": "self_explanation",
    "prompt": "Using a tiny example from the conversation, explain why each step makes sense—one sentence per step.",
    "instructions": "Justify each step briefly to check your understanding.",
    "config": {
      "variant": "self_explanation",
      "fields": [
        {"id":"step1","label":"Why Step 1 works","max_chars":160},
        {"id":"step2","label":"Why Step 2 works","max_chars":160},
        {"id":"step3","label":"Why Step 3 works (optional)","max_chars":160}
      ]
    }
  }
}'''

    tmpl_ordering = '''{
  "primary_interaction": {
    "type": "ordering_interaction",
    "prompt": "Put these steps in the correct order based on the dialogue",
    "instructions": "Tap each item in order from first to last.",
    "options": ["Step A", "Step B", "Step C"],
    "correct_order": ["Step A", "Step B", "Step C"]
  }
}'''

    tmpl_matching = '''{
  "primary_interaction": {
    "type": "matching_interaction",
    "prompt": "Match each concept to its example from the conversation",
    "instructions": "Tap pairs to connect them.",
    "pairs": {
      "Concept A": "Example A",
      "Concept B": "Example B",
      "Concept C": "Example C"
    }
  }
}'''

    template_by_type = {
        "multiple_choice": tmpl_mc,
        "reflection_prompt": tmpl_reflection,
        "teach_back": tmpl_teach_back,
        "self_explanation": tmpl_self_expl,
        "ordering_interaction": tmpl_ordering,
        "matching_interaction": tmpl_matching,
    }
    template = template_by_type[chosen_type]

    workout_rules = (
        "- Must be completable in ≤ 30 seconds.\n"
        "- No free-text inputs; taps only.\n"
        "- Use at most 3 options or 3 steps/pairs."
        if (context or "").lower() == "workout"
        else ""
    )

    return f"""
Create ONE short next-step interaction that helps the user apply or check understanding of THIS conversation.
Return STRICT JSON ONLY. No prose, no markdown.

CHOSEN_INTERACTION_TYPE: {chosen_type}

CONVERSATION
{conversation_text}

PROGRAM
- Focus: {program.focus_area}
- Context: {program.context}
- Day: {day_number}
- Outline Item: {json.dumps(outline_item, ensure_ascii=False)}

GUIDELINES
- Anchor to ONE specific phrase/mechanism/example from the dialogue (quote or name it).
- Keep it lightweight (≤ 2 minutes total effort).
- Make the success signal legible (what the user should notice/decide).
{workout_rules}

CRITICAL JSON RULES
- Return EXACTLY the JSON structure shown in the template below.
- multiple_choice: include 3–4 concise options; set "correct_option" to EXACTLY one of the strings in "options".
- ordering_interaction: "options" and "correct_order" must contain the same items and casing.
- matching_interaction: "pairs" is a dict with 2–4 entries of short strings.
- teach_back / self_explanation: include the "config.fields" as shown.

OUTPUT TEMPLATE (fill with specifics from THIS dialogue)
{template}

VALIDATION CHECKLIST
✓ JSON parses and matches the template
✓ Anchored to a specific detail from the conversation
✓ Workout: taps only; 3 items max
""".strip()


# =========================
# SOFT CHECK
# =========================
def _soft_check_convo(chunks: List[Dict[str, Any]]) -> None:
    text = " ".join(c.get("text", "") for c in chunks)
    wc = len(text.split())
    # Made more lenient - warn but don't fail for word count
    if wc < 200 or wc > 600:
        logger.warning(f"Conversation length {wc} outside recommended 270–465 range")
    
    # Made more lenient - check for any reasonable ending punctuation
    last = chunks[-1].get("text", "") if chunks else ""
    if last:
        last_clean = last.strip()
        # Allow more ending punctuation and don't be so strict
        if last_clean and last_clean[-1:] not in ".?!:":
            logger.warning(f"Conversation doesn't end with clear punctuation: '{last_clean[-20:]}'")

# =========================
# Route: Generate Lesson
# =========================

@router.post("/generate-lesson", response_model=GenerateLessonOut, summary="Generate Lesson")
async def generate_lesson(body: GenerateLessonIn):
    raw = get_program(body.program_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Program not found")

    program = Program(**raw)
    idx = body.day_number - 1
    if idx < 0 or idx >= len(program.outline or []):
        raise HTTPException(status_code=400, detail="day_number out of range")

    outline_item: Dict[str, Any] = program.outline[idx]

    # History for rotation/anti-repeat
    used_styles, banned_openers, used_interaction_types = collect_history(raw)

    # Classify mode using the most user-like text available
    user_text = outline_item.get("title") or outline_item.get("summary") or program.title
    mode = await classify_mode_with_llm(user_text, body.model)

    # STEP 1: Conversation
    convo_prompt = build_conversation_prompt(program, outline_item)
    convo_req = TextGenerationRequest(messages=[{"role": "user", "content": convo_prompt}], model=body.model)
    convo_resp = await dao.generate_text(convo_req)
    convo_text = (convo_resp.text or "").strip()

    # More robust JSON cleaning
    def clean_json_response(text: str) -> str:
        """Clean and extract JSON from LLM response"""
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        
        if text.startswith("```json"):
            text = text[7:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        
        # Find JSON object boundaries
        json_start = text.find('{')
        json_end = text.rfind('}')
        if json_start != -1 and json_end != -1 and json_end > json_start:
            text = text[json_start:json_end+1]
        
        # Clean common JSON issues
        text = text.strip()
        
        # Remove trailing commas before closing brackets/braces
        import re
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix incomplete strings (add closing quotes if needed)
        # Count quotes to see if we have unmatched ones
        quote_count = text.count('"')
        if quote_count % 2 == 1:
            # Odd number of quotes, might need to close the last string
            last_quote_pos = text.rfind('"')
            # Check if there's content after the last quote that looks like incomplete text
            after_quote = text[last_quote_pos + 1:].strip()
            if after_quote and not after_quote.startswith(',') and not after_quote.startswith('}') and not after_quote.startswith(']'):
                # Looks like incomplete text, try to close it properly
                # Find where to insert the closing quote
                closing_pos = len(text)
                for i, char in enumerate(reversed(text)):
                    if char in '}],':
                        closing_pos = len(text) - i
                        break
                if closing_pos > last_quote_pos:
                    text = text[:closing_pos-1] + '"' + text[closing_pos-1:]
        
        return text

    convo_text = clean_json_response(convo_text)

    try:
        convo_data = json.loads(convo_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse conversation JSON. Raw response length: {len(convo_text)}")
        logger.error(f"Raw response preview: {convo_text[:200]}...")
        logger.error(f"JSON parse error at position {e.pos}: {str(e)}")
        
        # Additional debugging - show content around the error position
        if hasattr(e, 'pos') and e.pos:
            start_pos = max(0, e.pos - 50)
            end_pos = min(len(convo_text), e.pos + 50)
            logger.error(f"Content around error position: ...{convo_text[start_pos:end_pos]}...")
        
        raise HTTPException(status_code=502, detail=f"LLM did not return valid JSON for conversation generation: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error parsing conversation JSON: {str(e)}")
        logger.error(f"Raw response length: {len(convo_text)}")
        logger.error(f"Raw response preview: {convo_text[:200]}...")
        raise HTTPException(status_code=502, detail=f"LLM did not return valid JSON for conversation generation: {str(e)}")

    conversation_chunks = [ConversationTurn(**t) for t in convo_data.get("conversation_chunks", [])]
    if not conversation_chunks:
        raise HTTPException(status_code=502, detail="Conversation JSON missing 'conversation_chunks'")

    # Sanity check: length + closure (runs on every valid conversation)
    _soft_check_convo([c.model_dump() for c in conversation_chunks])

    # STEP 2: Interaction (varied) with DRIVING short-circuit
    context_lower = (program.context or "").lower()
    primary_interaction = None

    if context_lower != "driving":
        inter_prompt = build_interaction_prompt(
            conversation_chunks=convo_data.get("conversation_chunks", []),
            program=program,
            outline_item=outline_item,
            mode=mode,
            context=program.context or "home",
            day_number=body.day_number,
            used_interaction_types=used_interaction_types,
        )
        inter_req = TextGenerationRequest(messages=[{"role": "user", "content": inter_prompt}], model=body.model)
        inter_resp = await dao.generate_text(inter_req)
        inter_text = (inter_resp.text or "").strip()
        inter_text = clean_json_response(inter_text)

        try:
            inter_data = json.loads(inter_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse interaction JSON. Raw response length: {len(inter_text)}")
            logger.error(f"Raw response preview: {inter_text[:200]}...")
            logger.error(f"JSON parse error at position {e.pos}: {str(e)}")
            
            if hasattr(e, 'pos') and e.pos:
                start_pos = max(0, e.pos - 50)
                end_pos = min(len(inter_text), e.pos + 50)
                logger.error(f"Content around error position: ...{inter_text[start_pos:end_pos]}...")
            
            raise HTTPException(status_code=502, detail=f"LLM did not return valid JSON for interaction generation: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error parsing interaction JSON: {str(e)}")
            logger.error(f"Raw response length: {len(inter_text)}")
            logger.error(f"Raw response preview: {inter_text[:200]}...")
            raise HTTPException(status_code=502, detail=f"LLM did not return valid JSON for interaction generation: {str(e)}")

        primary_interaction_raw = inter_data.get("primary_interaction")
        primary_interaction = InteractionSpec(**primary_interaction_raw) if primary_interaction_raw else None
    else:
        # Driving = audio-only; explicitly store None so frontend can skip question
        primary_interaction = None

    # Persist
    lesson = Lesson(
        program_id=program.id,
        day_number=body.day_number,
        title=outline_item.get("title", f"Lesson {body.day_number}"),
        description=outline_item.get("summary", "Generated from outline"),
        audio_section_title=outline_item.get("title", f"Lesson {body.day_number}"),
        conversation_chunks=conversation_chunks,
        primary_interaction=primary_interaction,
        secondary_interaction=None,
        generation_prompt=(
            f"(mode={mode})\n\nConversation Prompt:\n{convo_prompt}\n\n"
            + ("" if context_lower == "driving" else f"Interaction Prompt:\n{inter_prompt}")
        ),
        outline_snapshot=outline_item,
        context=program.context
    )

    raw_lessons: List[Dict[str, Any]] = raw.get("lessons", [])
    raw_lessons = [l for l in raw_lessons if l.get("day_number") != body.day_number]
    raw_lessons.append(lesson.model_dump(mode="json"))
    raw["lessons"] = raw_lessons
    raw["updated_at"] = datetime.utcnow().isoformat()
    upsert_program(raw)

    return GenerateLessonOut(
        success=True,
        program_id=program.id,
        day_number=body.day_number,
        lesson_id=lesson.id
    )
