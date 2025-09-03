from enum import Enum

class ContextType(str, Enum):
    HOME = "home"
    DRIVING = "driving"
    WORKOUT = "workout"

class ProgramStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"

class ResponseType(str, Enum):
    # Basic Responses
    TEXT = "text"
    AUDIO = "audio"

    # Interactive Responses (supported)
    MULTIPLE_CHOICE = "multiple_choice"
    REFLECTION_PROMPT = "reflection_prompt"

    # NEW: evidence-backed interactions
    TEACH_BACK = "teach_back"
    SELF_EXPLANATION = "self_explanation"

    # Workout tap-only (new)
    ORDERING_INTERACTION = "ordering_interaction"
    MATCHING_INTERACTION = "matching_interaction"

class LessonStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"