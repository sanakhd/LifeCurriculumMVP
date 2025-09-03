# LifeCurriculum Backend - System Patterns

## Architecture Overview
The system follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────┐
│           API Layer                 │
│    (FastAPI Routers & Endpoints)    │
│    - Health  - Programs             │
└─────────────────────────────────────┘
                   │
┌─────────────────────────────────────┐
│    Manager & Storage Layer          │
│      (Business Logic)               │
│ - SessionManager  - ProgramStore    │
└─────────────────────────────────────┘
                   │
┌─────────────────────────────────────┐
│           DAO Layer                 │
│    (Data Access Objects)            │
│  - OpenAIDAO  - MinIODAO            │
└─────────────────────────────────────┘
                   │
┌─────────────────────────────────────┐
│      External Services & Storage    │
│ - OpenAI API  - MinIO  - JSONL Files│
└─────────────────────────────────────┘
```

## Key Design Patterns

### 1. DAO Pattern (Data Access Object)
**Purpose**: Abstracts external service interactions
**Implementation**:
- Base DAO class with common HTTP operations
- Service-specific DAOs inherit from base
- Standardized error handling and logging
- Configuration-driven service URLs

**Files**:
- `app/daos/minio_dao.py` - MinIO storage operations
- `app/daos/openai_dao.py` - OpenAI API interactions

### 2. Manager Pattern
**Purpose**: Orchestrates business logic and coordinates between services
**Implementation**:
- SessionManager handles curriculum generation workflow
- Combines multiple DAO operations
- Implements business rules and validation

**Files**:
- `managers/SessionManager.py` - Core session management logic

### 3. Router Pattern (FastAPI)
**Purpose**: Organizes API endpoints by domain
**Implementation**:
- Domain-specific routers (health, activities)
- Consistent response models
- Proper HTTP status codes and error handling

**Files**:
- `app/apis/health.py` - System health endpoints
- `app/apis/activities/router.py` - Learning activity endpoints

### 4. Configuration Pattern
**Purpose**: Centralized, environment-based configuration
**Implementation**:
- Pydantic Settings for type-safe config
- Environment variable support
- Default values with override capability

**Files**:
- `app/config.py` - Application configuration

## Component Relationships

### Core Flow: Curriculum Generation
1. **API Request** → `/api/v1/activities/setup-lesson`
2. **Router** → Validates request, calls SessionManager
3. **SessionManager** → Orchestrates curriculum generation
4. **OpenAIDAO** → Makes API call to OpenAI
5. **Response** → Structured curriculum returned to user

### Error Handling Strategy
- **API Level**: HTTP exceptions with structured error responses
- **Manager Level**: Business logic validation and error propagation
- **DAO Level**: External service error handling and retries
- **Logging**: Comprehensive logging at all levels

## Critical Implementation Paths

### 1. Curriculum Generation Path
```
POST /api/v1/activities/setup-lesson
├── Request validation (Pydantic)
├── SessionManager.create_session()
│   ├── OpenAI message preparation
│   ├── OpenAIDAO.generate_text()
│   └── Console output of curriculum
└── Success/Error response
```

### 2. File Operations Path
```
MinIODAO operations
├── Bucket management
├── File upload/download
├── Error handling for S3 operations
└── Logging and monitoring
```

### 3. Health Check Path
```
GET /ping, /health
├── Basic connectivity checks
├── Service availability validation
└── Status response generation
```

## Data Models Structure

### Request/Response Models
- **BaseResponse**: Standard API response format
- **SetupLessonRequest**: Curriculum generation input
- **SetupLessonResponse**: Generation acknowledgment
- **OpenAI Models**: Structured OpenAI API interactions
- **MinIO Models**: File operation data structures

### Model Validation
- Pydantic validators for input sanitization
- Type hints for IDE support and runtime checking
- Custom validation methods for business rules

## Security Patterns

### API Security
- CORS middleware configuration
- Input validation and sanitization
- Error message sanitization to prevent information leakage

### External Service Security
- API key management through environment variables
- Request timeout configurations
- Secure credential handling

## Scalability Considerations

### Async Operations
- FastAPI async/await throughout
- Non-blocking external API calls
- Proper exception handling in async context

### Resource Management
- Connection pooling for external services
- Configurable timeout values
- Graceful service degradation

## Testing Architecture

### Test Organization
- Unit tests for individual components
- Integration tests for DAO operations
- API endpoint testing
- Mock external service dependencies

### Test Patterns
- pytest fixtures for common setup
- Proper mocking of external services
- Environment-specific test configurations
