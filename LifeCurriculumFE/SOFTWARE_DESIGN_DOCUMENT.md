# Life Curriculum Frontend - MVP-lite Software Design Document

## 1. Overview

### Purpose of the Service
Life Curriculum is a personal development platform that enables users to create personalized 5-day growth programs through AI-powered conversational learning. This frontend application serves as the user interface for:

- **Program Generation**: User-driven creation of personalized learning curricula via AI orchestration (backend API integration)
- **AI-Powered Content Delivery**: Conversational lesson format with audio generation capabilities  
- **Progress Tracking**: Lesson completion, user engagement, and learning analytics
- **Micro-Learning Experience**: 5-minute daily sessions optimized for busy lifestyles

### Current Stack
- **Frontend Framework**: React 19.1.1 with TypeScript 5.8.3
- **Build Tool**: Vite 7.1.2 with Hot Module Replacement (HMR)
- **Routing**: React Router DOM 7.8.1  
- **UI Components**: Custom CSS with Lucide React icons (0.542.0)
- **State Management**: React Hooks (useState, useEffect, custom hooks)
- **Data Persistence**: LocalStorage for user sessions
- **HTTP Client**: Native Fetch API with custom error handling
- **Development**: ESLint 9.33.0 with TypeScript integration
- **Backend Integration**: RESTful API client connecting to Python/FastAPI backend service

## 2. Repo Map

```
LifeCurriculumFE/
├── src/
│   ├── components/           # React UI components
│   │   ├── AppLayout.tsx        # Main layout wrapper with navbar
│   │   ├── CreateProgram.tsx    # Multi-step program creation form
│   │   ├── Dashboard.tsx        # User dashboard with program overview
│   │   ├── DashboardRouter.tsx  # Dashboard routing logic
│   │   ├── HeroPage.tsx        # Landing page for new users
│   │   ├── LandingPage.tsx     # Alternative landing page
│   │   ├── LessonPage.tsx      # Individual lesson viewer
│   │   ├── MyPrograms.tsx      # Program list and management
│   │   ├── NameEntry.tsx       # User onboarding name capture
│   │   └── Navbar.tsx          # Navigation component
│   ├── hooks/                # Custom React hooks
│   │   ├── useApi.ts           # API interaction hook
│   │   └── useLessonProgress.ts # Lesson progress tracking
│   ├── services/             # External service integrations
│   │   ├── api.ts              # Main API client with error handling
│   │   └── README.md           # Service documentation
│   ├── styles/               # Component-specific CSS
│   │   ├── CreateProgram.css   # Program creation styling
│   │   ├── Dashboard.css       # Dashboard layout styling
│   │   ├── HeroPage.css       # Landing page styling
│   │   └── [other].css        # Additional component styles
│   ├── types/                # TypeScript definitions
│   │   ├── api.ts              # API request/response types
│   │   ├── index.ts           # Shared type exports
│   │   └── program.ts         # Program-specific types
│   ├── assets/               # Static assets
│   │   └── openapi.json       # API specification
│   └── main.tsx              # React app entry point
├── memory-bank/              # Project documentation
│   ├── projectbrief.md        # Core project requirements
│   ├── productContext.md      # Product context and vision
│   └── [other].md            # Additional documentation
└── package.json              # Dependencies and scripts
```

## 3. API (Current)

### Base Configuration
- **Backend URL**: `http://localhost:8000`
- **Error Handling**: Custom `ApiError` class with status codes
- **Authentication**: None (MVP focuses on functionality)

### Core Endpoints

#### Health & Status
- `GET /health` → `HealthResponse` - Service health check
- `GET /ping` → `HealthResponse` - Basic connectivity test

#### Program Management
- `POST /api/v1/generate-program` → `GenerateProgramRequest` → `GenerateProgramResponse`
- `POST /api/v1/generate-full-program` → `GenerateFullProgramRequest` → `GenerateFullProgramResponse`
- `GET /api/v1/programs` → `ProgramListResponse` - List all programs with pagination
- `GET /api/v1/programs/{id}` → `Program` - Retrieve specific program details

#### Lesson Operations
- `POST /api/v1/programs/generate-lesson` → `GenerateLessonIn` → `GenerateLessonOut`
- `GET /api/v1/programs/{id}/lessons/{day}` → `Lesson` - Get specific lesson content
- `GET /api/v1/programs/lessons/ids` → `LessonIdsResponse` - All lesson identifiers

#### Audio Generation
- `POST /api/v1/programs/generate-lesson-audio` → `GenerateLessonAudioRequest` → `GenerateLessonAudioResponse`
- `GET /api/v1/programs/lessons/{uuid}/audio-status` → `AudioStatusResponse`
- `GET /api/v1/programs/lessons/{uuid}/audio/playlist` → `AudioPlaylistResponse`
- `DELETE /api/v1/programs/lessons/{uuid}/audio` → `DeleteAudioResponse`

#### Lesson Progress
- `POST /api/v1/lessons/{id}/complete` → `CompleteLessonRequest` → `CompleteLessonResponse`
- `POST /api/v1/lessons/{id}/start` → `BaseResponse`
- `POST /api/v1/programs/lessons/{id}/evaluate-answer` → `EvaluateAnswerRequest` → `EvaluateAnswerResponse`

### Key Request/Response Models

#### ProgramRequest (Generate Full Program)
```typescript
{
  focus_area: string;        // min 5 chars - what to learn
  target_outcome: string;    // min 5 chars - desired result  
  context: 'home' | 'driving' | 'workout'; // learning environment
  prompt?: string;           // optional custom instructions
  model?: string;           // AI model selection
  generate_audio?: boolean; // enable audio generation
  voice_mapping?: Record<string, string>; // speaker voice assignments
}
```

#### ProgramResponse (Generate Full Program)
```typescript
{
  status: string;
  program_id: string;
  title: string;
  description: string;
  outline: Record<string, any>[];
  lessons: Record<string, any>[];
  generation_stats: GenerationStats;
  timestamp: string;
}
```

## 4. Data/Control Flow (Today)

### Program Creation Flow
```
User Input (CreateProgram.tsx)
  ↓ focus_area + target_outcome + context
API Call (lifeCurriculumApi.generateFullProgram)
  ↓ GenerateFullProgramRequest
Backend AI Processing
  ↓ AI model generates structured content
Response Normalization  
  ↓ GenerateFullProgramResponse
Frontend State Update
  ↓ Navigate to /programs
Program List Display (MyPrograms.tsx)
```

### Lesson Access Flow
```
Program Selection (MyPrograms.tsx)
  ↓ programId + dayNumber
Route Navigation (/programs/{id}/lesson/{day})
API Call (lifeCurriculumApi.getSingleLesson)
  ↓ Lesson content retrieval
Lesson Rendering (LessonPage.tsx)
  ↓ Display lesson + progress tracking
Audio Generation (if enabled)
  ↓ Conversational audio content
Progress Updates (lesson completion)
```

### Current Templates/Prompts Location
- **AI Prompt Engineering**: Handled server-side (not visible in frontend)
- **User Input Templates**: Hardcoded placeholder text in CreateProgram.tsx
- **Context Options**: Defined in `CONTEXT_OPTIONS` array (home/workout/driving)

### Simple Guardrails (MVP)
- **Input Validation**: 5-character minimum for focus_area and target_outcome
- **Character Limits**: 500 characters max on text inputs  
- **Context Restriction**: Only 'home' context currently enabled (workout/driving locked)
- **Error Boundaries**: Basic try/catch with user-friendly error messages
- **Loading States**: UI feedback during API calls

## 5. Performance/Operational Notes (MVP)

### Timeout Configuration
- **Default Fetch Timeout**: Browser default (no custom timeout implemented)
- **Loading States**: UI spinners for user feedback during API calls
- **Error Recovery**: Basic retry logic through user re-submission

### Concurrency Model
- **Single-threaded React**: Standard React concurrent features
- **API Calls**: Sequential processing (no parallel API orchestration)
- **State Management**: Local component state with React hooks

### Logging
- **Console Logging**: Development-focused console.log statements
- **API Logging**: Request/response logging in api.ts service
- **Error Tracking**: Console.error for failed API calls
- **User Actions**: Basic navigation and form submission logging

### Basic Performance Considerations
- **Code Splitting**: None implemented (single bundle)
- **Caching**: Browser-level caching for static assets
- **Lazy Loading**: None implemented
- **Memory Management**: React's automatic garbage collection

## 6. Run (Today)

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/PSSK-Projects/LifeCurriculumFE.git
cd LifeCurriculumFE

# Install dependencies
npm install

# Start development server
npm run dev
# Server runs at http://localhost:5173

# Additional commands
npm run build    # Production build
npm run lint     # ESLint code quality
npm run preview  # Preview production build
```

### Environment Configuration (.env.example)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Development Settings  
VITE_NODE_ENV=development

# Feature Flags (Future)
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_AUDIO_FEATURES=true
VITE_DEBUG_MODE=true

# Third-party Services (Placeholders)
VITE_OPENAI_API_KEY=your_openai_key_here
VITE_ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### Browser Requirements
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Features Used**: ES2020 modules, Fetch API, LocalStorage
- **Mobile Support**: Responsive design (not optimized for mobile-first)

## 7. Known Gaps / TODO (MVP)

### Storage & Persistence
- ❌ **No Database Integration**: All data managed server-side
- ❌ **Session Management**: Basic localStorage, no secure session handling  
- ❌ **Offline Capabilities**: No offline lesson access or caching
- ❌ **Data Backup**: No user data export/import functionality

### Reliability & Error Handling
- ❌ **Retry Logic**: Minimal API retry mechanisms
- ❌ **Circuit Breakers**: No fault tolerance for service failures
- ❌ **Request Queuing**: No background sync or queued operations
- ❌ **Graceful Degradation**: Limited fallback for missing features

### Analytics & Monitoring
- ❌ **User Analytics**: No user behavior tracking implementation
- ❌ **Performance Monitoring**: No real-time performance metrics
- ❌ **Error Reporting**: No automated error reporting (Sentry, etc.)
- ❌ **Usage Statistics**: No program completion rate tracking

### Security & Compliance
- ❌ **Authentication System**: No user login or account management
- ❌ **Authorization**: No role-based access control
- ❌ **Data Privacy**: No GDPR compliance measures
- ❌ **Input Sanitization**: Basic validation, no XSS protection

### User Experience
- ❌ **Mobile Optimization**: Not mobile-first responsive design
- ❌ **Accessibility**: Limited ARIA labels and screen reader support
- ❌ **Internationalization**: English-only, no i18n framework
- ❌ **Progressive Web App**: No PWA capabilities or app-like features

### Testing & Quality
- ❌ **Unit Tests**: No test suite implementation
- ❌ **Integration Tests**: No API integration testing
- ❌ **E2E Tests**: No user journey testing
- ❌ **Code Coverage**: No coverage tracking or requirements

### Operational Readiness
- ❌ **CI/CD Pipeline**: No automated deployment process
- ❌ **Environment Management**: No staging/production environment setup  
- ❌ **Health Checks**: No frontend health monitoring
- ❌ **Documentation**: Limited API documentation and user guides

---

*This document reflects the current state of the Life Curriculum Frontend as of the MVP phase. Updates should be made as features are implemented and architecture evolves.*
