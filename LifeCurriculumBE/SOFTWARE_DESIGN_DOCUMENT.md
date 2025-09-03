# LifeCurriculum Backend - Software Design Document (MVP-lite)

## 1. Overview

LifeCurriculum Backend is an AI-powered learning platform that transforms any learning request into a structured, 5-lesson curriculum. The system acts as a personal learning architect, leveraging OpenAI's intelligence to create organized pathways for knowledge acquisition. Each program is tailored to specific learning contexts (home, driving, workout) and delivers bite-sized, conversation-driven lessons with interactive practice elements.

**Core User Flows:**
- **Onboarding**: User provides focus area, target outcome, and learning context → System generates program outline
- **Program Generation**: AI creates structured 5-day curriculum with title, description, and daily lesson outlines  
- **Daily Lesson Flow**: User accesses lesson → Listens to Host A/B conversation → Completes context-specific practice activities → Lesson marked complete

## 2. Tech & Repo Map

**Stack:**
- **Backend Framework**: FastAPI (Python)
- **AI Integration**: OpenAI GPT models, TTS, Whisper
- **Storage**: File-based JSON storage + MinIO for audio files
- **Models**: Pydantic for data validation and serialization
- **Config**: Environment-based settings management

**Folder Structure:**
```
Service/
├── app/
│   ├── main.py                 # FastAPI app entry point & CORS setup
│   ├── config.py              # Environment configuration
│   ├── logger.py              # Logging setup
│   ├── apis/
│   │   ├── health.py          # Health check endpoint
│   │   └── programs/
│   │       ├── router.py      # Programs API router aggregator
│   │       ├── generate_program.py    # Create program outline
│   │       ├── generate_lesson.py     # Generate individual lesson content
│   │       ├── generate_full_program.py   # Generate all lessons at once
│   │       ├── read_program.py        # Retrieve program data
│   │       ├── get_all_lessons.py     # Get all lesson IDs across programs
│   │       ├── complete_lesson.py     # Mark lesson as completed
│   │       ├── evaluate_lesson_answer.py  # Evaluate user responses
│   │       ├── generate_lesson_audio.py   # Generate TTS audio
│   │       └── stream_lesson_audio.py     # Stream audio files
│   ├── daos/
│   │   ├── openai_dao.py      # OpenAI API client (text, TTS, transcription)
│   │   └── minio_dao.py       # MinIO file storage operations
│   ├── models/
│   │   ├── base.py            # Base entity with ID/timestamps
│   │   ├── program.py         # Program model with outline & lessons
│   │   ├── lesson.py          # Lesson with conversation turns & interactions
│   │   ├── enums.py           # ContextType, ProgramStatus, ResponseType
│   │   └── responses.py       # API response models
│   ├── services/
│   │   └── audio_generator.py # Audio generation orchestration
│   └── storage/
│       └── program_store.py   # File-based program persistence
├── data/
│   └── programs.jsonl         # Program data storage (JSONL format)
├── program_audios/            # Generated audio files by program ID
├── managers/
│   └── SessionManager.py     # OpenAI session management
└── run.py                     # Development server runner
```

## 3. Architecture

### Component Hierarchy
```
FastAPI App (main.py)
├── API Layer
│   ├── Health Router (/health)
│   └── Programs Router (/api/v1/programs/*)
│       ├── generate-program
│       ├── generate-lesson
│       ├── generate-full-program
│       ├── read-program/{id}
│       ├── lessons/ids
│       ├── complete-lesson
│       ├── evaluate-lesson-answer
│       ├── generate-lesson-audio
│       └── stream-lesson-audio/{id}
├── Service Layer
│   ├── SessionManager (OpenAI orchestration)
│   └── AudioGenerator (TTS workflow)
├── Data Access Layer
│   ├── OpenAIDAO (API integration)
│   ├── MinIODAO (file storage)
│   └── ProgramStore (JSON persistence)
└── Models Layer
    ├── Program (curriculum container)
    ├── Lesson (content + interactions)
    └── Supporting Models (requests/responses)
```

### Routing Map
- `GET /health` - Service health check
- `POST /api/v1/programs/generate-program` - Create program outline
- `POST /api/v1/programs/generate-lesson` - Generate single lesson content
- `POST /api/v1/programs/generate-full-program` - Generate all program lessons
- `GET /api/v1/programs/read-program/{program_id}` - Retrieve program data
- `GET /api/v1/programs/lessons/ids` - Get all lesson IDs across programs
- `POST /api/v1/programs/complete-lesson` - Mark lesson completed
- `POST /api/v1/programs/evaluate-lesson-answer` - Evaluate user response
- `POST /api/v1/programs/generate-lesson-audio` - Generate TTS audio
- `GET /api/v1/programs/stream-lesson-audio/{program_id}/{lesson_day}` - Stream audio

### State Management
**Global State:**
- Program data persisted in `Service/data/programs.jsonl`
- Audio files stored in `Service/program_audios/{program_id}/`
- Configuration managed via environment variables

**Local State:**
- Request/response models validated via Pydantic
- Session state managed by SessionManager for OpenAI calls
- Audio generation state tracked per lesson

**Data Fetching/Caching:**
- Programs loaded from JSONL file on demand
- No explicit caching layer (file system acts as persistence)
- OpenAI responses not cached (fresh generation each time)

### API Client Patterns
**OpenAI Integration:**
- `OpenAIDAO` handles all AI operations (text generation, TTS, transcription)
- Error handling with HTTP status code mapping
- Logging for debugging and monitoring
- Request/response models with proper typing

**Error/Loading Patterns:**
- Structured error responses with detail messages
- HTTP status codes: 400 (validation), 404 (not found), 500 (server errors)
- Async/await throughout for non-blocking operations

**Types Used:**
- `TextGenerationRequest/Response` for curriculum generation
- `TTSRequest/Response` for audio generation  
- `Program` and `Lesson` models for data structure
- Enum types for context, status, and response types

## 4. Contract Types (Current)

### Core Program Interface
```python
class Program(BaseEntity):
    # User input from onboarding
    focus_area: str              # User's learning goal (5-500 chars)
    target_outcome: str          # Specific measurable outcome (5-300 chars)
    context: ContextType         # home | driving | workout
    
    # AI-generated program metadata
    title: str                   # AI-generated program title
    description: Optional[str]   # AI-generated description (nullable)
    total_lessons: int          # Number of lessons (1-10, default 5)
    
    # Progress tracking
    status: ProgramStatus       # active | completed | paused | abandoned
    current_lesson_day: int     # Current progress (1-based)
    lessons_completed: int      # Completed lesson count
    
    # Timestamps & session tracking
    started_at: Optional[datetime]        # When user started first lesson
    completed_at: Optional[datetime]      # When user completed all lessons
    last_accessed_at: Optional[datetime]  # Last access timestamp
    session_token: Optional[str]          # Anonymous session identifier
    
    # Program structure
    outline: List[Dict[str, Any]]  # Lesson outline structure
    lessons: List[Lesson]         # Full lesson content
    
    # Computed properties
    @property
    def completion_percentage(self) -> float  # Returns 0.0-1.0
    def is_completed(self) -> bool           # True if all lessons done
```

### Lesson Structure
```python
class Lesson(BaseEntity):
    # Core relationships & identifiers
    program_id: str             # Parent program reference
    day_number: int             # Lesson sequence (1-10)
    
    # Content structure
    title: str                  # Lesson title
    description: str            # Lesson description/subtitle
    audio_section_title: str    # Title for audio section
    conversation_chunks: List[ConversationTurn]  # Host A/B dialogue turns
    conversation_script: Optional[str]           # Auto-generated flat transcript
    
    # Interactive practice elements
    primary_interaction: Optional[InteractionSpec]    # First practice activity
    secondary_interaction: Optional[InteractionSpec]  # Second practice activity
    
    # Legacy single-practice support (backwards compatibility)
    practice_type: Optional[ResponseType]
    practice_prompt: Optional[str]
    practice_data: Optional[Dict[str, Any]]
    
    # Metadata & generation tracking
    generation_prompt: Optional[str]         # AI prompt used for generation
    outline_snapshot: Optional[Dict]         # Original outline item
    estimated_conversation_duration: int     # Conversation length (minutes)
    estimated_total_duration: int           # Total lesson time (minutes)
    context: ContextType                    # Optimized learning context
    learning_objectives: Optional[List[str]] # What user will learn
    
    # Progress & completion tracking
    status: LessonStatus        # not_started | in_progress | completed | skipped
    started_at: Optional[datetime]          # When first opened
    completed_at: Optional[datetime]        # When finished
    time_spent_seconds: Optional[int]       # Total engagement time
    
    # Audio file management
    audio_file_path: Optional[str]          # Path to generated TTS audio
    audio_file_size_bytes: Optional[int]    # File size
    audio_duration_seconds: Optional[int]   # Audio length
    
    # User feedback & analytics
    user_rating: Optional[int]              # 1-5 star rating
    completion_method: Optional[str]        # How completed (full/skipped/partial)
    
    # Computed properties & convenience methods
    @property
    def interactions(self) -> List[InteractionSpec]  # All interactions in order
    def is_completed(self) -> bool                   # True if completed
    def duration_minutes(self) -> float              # Time spent in minutes
```

### Practice Modes & Interaction Types
```python
class ResponseType(str, Enum):
    TEXT = "text"                        # Written reflection (home context)
    AUDIO = "audio"                      # Voice response (driving context)  
    SCENARIO_CHOICE = "scenario_choice"  # Multiple choice scenarios
    SLIDER_SCALE = "slider_scale"        # Rating scale (workout context)
    REFLECTION_PROMPT = "reflection_prompt"  # Guided reflection

class ConversationTurn(BaseModel):
    speaker: Literal["Host A", "Host B"] # Enforced speaker identities
    text: str                           # Speaker dialogue content
    media: Optional[Dict[str, Any]]     # Optional per-turn metadata

class InteractionSpec(BaseModel):
    type: ResponseType                  # Practice activity type
    prompt: str                         # Instructions/question for learner
    
    # Choice-based interactions
    options: Optional[List[str]]        # Multiple choice options
    correct_option: Optional[str]       # Correct answer (must match options)
    
    # Scale/slider interactions  
    scale_min: Optional[int]            # Minimum scale value
    scale_max: Optional[int]            # Maximum scale value
    min_label: Optional[str]            # Label for scale minimum
    max_label: Optional[str]            # Label for scale maximum
    
    # Text/reflection interactions (HOME context)
    placeholder: Optional[str]          # Input placeholder text
    min_words: Optional[int]            # Minimum word count requirement
    instructions: Optional[str]         # Additional exercise instructions
    
    # Audio interactions (DRIVING context)
    duration_seconds: Optional[int]     # Target audio response length
    guidance: Optional[str]             # Audio exercise guidance
    
    # Future extensibility
    flashcards: Optional[List[Dict[str, str]]]  # Flashcard pairs
    config: Optional[Dict[str, Any]]    # Per-type configuration
```

**Fallback UI Patterns:**
- Missing `description` → Display title only
- No `secondary_interaction` → Single practice activity
- Empty `conversation_chunks` → Use `conversation_script` fallback
- Null `audio_file_path` → Text-only lesson mode

## 5. Key Features (Implemented)

### Host A/B Conversation Rendering
- **Structure**: Lessons contain `conversation_chunks` with alternating "Host A" and "Host B" speakers
- **Rendering**: Each `ConversationTurn` has `speaker` and `text` fields for direct UI display
- **Pause Behavior**: No automatic timing implemented - UI controls playback flow
- **Audio Integration**: TTS generates audio from conversation script, stored as WAV files
- **Fallback**: `conversation_script` provides flat transcript if chunks unavailable

### Context-Aware Practice Blocks
- **Context Types**: `home` (reflective), `driving` (audio-focused), `workout` (silent/quick)
- **Swapping Logic**: `InteractionSpec` adapts based on program's `context` field
- **Home Context**: Text reflection prompts, scenario practice, self-assessment tools
- **Driving Context**: Audio responses, hands-free verbal exercises, mental rehearsal  
- **Workout Context**: Silent reflection, quick rating scales, movement-compatible activities
- **Implementation**: Context determines available `ResponseType` options during lesson generation

### Reflection Input & Storage
- **Text Input**: `TEXT` response type with optional `min_words` and `placeholder`
- **Voice Input**: `AUDIO` response type with `duration_seconds` guidance
- **Storage**: User responses handled by `evaluate_lesson_answer` endpoint
- **Persistence**: Response evaluation results stored (implementation details in endpoint)
- **Integration**: Responses can influence lesson completion and progress tracking

## 6. Run/Build (Today)

### Local Development
```bash
# Navigate to Service directory
cd Service

# Install dependencies  
pip install -r requirements.txt

# Set required environment variables
OPENAI_API_KEY=your_api_key_here
MINIO_ENDPOINT=your_minio_endpoint
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key

# Run development server
python run.py
# OR
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Required Environment Variables
- `OPENAI_API_KEY` - OpenAI API authentication
- `MINIO_ENDPOINT` - MinIO server URL for file storage
- `MINIO_ACCESS_KEY` - MinIO access credentials
- `MINIO_SECRET_KEY` - MinIO secret credentials
- `LOG_LEVEL` (optional) - Logging verbosity
- `LOG_FILE` (optional) - Log file path

### Scripts & Commands
- `python run.py` - Start development server with auto-reload
- `python -m pytest Service/tests/` - Run test suite  
- Audio files generated to `Service/program_audios/{program_id}/`
- Program data stored in `Service/data/programs.jsonl`

## 7. Known Gaps / TODO (MVP)

### Current Limitations
- **Mid-lesson Context Switching**: Cannot change context after program creation - requires new program
- **Minimal Error States**: Basic HTTP error responses, no detailed user-facing error messages
- **No Progress Analytics**: Completion tracking exists but no aggregated insights or learning analytics
- **Audio Playback Control**: No pause/resume/speed control in generated audio files
- **Session Management**: Basic session tokens but no robust user authentication or multi-device sync
- **Lesson Dependency**: Cannot skip ahead or access lessons out of sequence
- **Limited Interaction Types**: Only 5 response types implemented, no rich media or advanced interactions

### Incomplete Features
- **Real-time Audio Processing**: Voice input evaluation is placeholder implementation
- **Content Personalization**: No adaptation based on user performance or preferences  
- **Offline Support**: Requires internet connection for all operations
- **Mobile Optimization**: API designed for web, no mobile-specific optimizations
- **Backup/Recovery**: No data backup or program recovery mechanisms
- **Rate Limiting**: No API rate limiting or usage quotas implemented
