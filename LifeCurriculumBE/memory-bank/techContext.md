# LifeCurriculum Backend - Technical Context

## Technology Stack

### Core Framework
- **FastAPI**: High-performance async web framework
- **Python 3.8+**: Modern Python with async/await support
- **Pydantic**: Data validation and settings management
- **uvicorn**: ASGI server for production deployment

### External Service Integration
- **OpenAI API**: GPT models for curriculum generation
- **MinIO**: S3-compatible object storage for file management
- **HTTP Client**: aiohttp for async external API calls

### Development Tools
- **pytest**: Testing framework with fixtures and async support
- **logging**: Structured logging throughout the application
- **python-dotenv**: Environment variable management

## Development Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)
- OpenAI API key
- MinIO server (for file storage features)

### Installation Steps
```bash
# Clone repository
git clone https://github.com/PSSK-Projects/LifeCurriculumBE.git
cd LifeCurriculumBE

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp Service/.env.example Service/.env
# Edit Service/.env with your API keys and configuration

# Run the application
cd Service
python run.py
```

### Project Structure
```
LifeCurriculum/
├── Service/                    # Main application directory
│   ├── app/                   # FastAPI application
│   │   ├── config.py          # Configuration settings
│   │   ├── main.py            # Application entry point
│   │   ├── apis/              # API route handlers
│   │   ├── daos/              # Data access objects
│   │   └── models/            # Pydantic models
│   ├── managers/              # Business logic layer
│   ├── tests/                 # Test files
│   ├── .env.example          # Environment template
│   └── run.py                # Application launcher
├── demo_*.py                 # Example/demo scripts
├── requirements.txt          # Python dependencies
└── README.md                # Project documentation
```

## Dependencies Analysis

### Core Dependencies
```python
fastapi>=0.104.1           # Web framework
uvicorn[standard]>=0.24.0  # ASGI server
pydantic>=2.5.0           # Data validation
pydantic-settings>=2.1.0  # Configuration management
python-dotenv>=1.0.0      # Environment variables
```

### External Service Dependencies
```python
openai>=1.3.0             # OpenAI API client
minio>=7.2.0              # MinIO client for object storage
aiohttp>=3.9.0            # Async HTTP client
```

### Development Dependencies
```python
pytest>=7.4.0            # Testing framework
pytest-asyncio>=0.21.0   # Async test support
```

## Configuration Management

### Environment Variables
The application uses environment-based configuration with sensible defaults:

```python
# Core Application Settings
HOST=0.0.0.0                    # Server host
PORT=8000                       # Server port
DEBUG=true                      # Debug mode
LOG_LEVEL=INFO                  # Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_FILE=optional               # Log file path (optional, defaults to console)

# CORS Settings
ALLOWED_ORIGINS=["*"]           # Cross-origin permissions

# External Service Configuration
OPENAI_API_KEY=your_key_here    # OpenAI API authentication
OPENAI_BASE_URL=https://api.openai.ai/v1  # OpenAI API endpoint
EXTERNAL_SERVICE_TIMEOUT=30     # Request timeout in seconds

# MinIO Configuration
MINIO_ENDPOINT=localhost:9000   # MinIO server endpoint
MINIO_ACCESS_KEY=minioadmin    # MinIO access key
MINIO_SECRET_KEY=minioadmin    # MinIO secret key
MINIO_SECURE=false             # Use HTTPS (true/false)

# System Prompts
CURRICULUM_SYSTEM_PROMPT=You are an expert curriculum designer...
```

### Configuration Pattern
- Uses Pydantic Settings for type-safe configuration
- Automatic environment variable loading
- Validation and default value handling
- Configuration injection via dependency injection

## Technical Constraints

### Performance Constraints
- OpenAI API rate limits (varies by plan)
- Request timeout limitations (30s default)
- Memory usage for large curriculum generation
- Concurrent request handling capacity

### Integration Constraints
- OpenAI API availability dependency
- MinIO server connectivity requirements
- Network latency for external service calls
- API key security and rotation requirements

### Development Constraints
- Python 3.8+ requirement for async features
- FastAPI framework limitations
- Pydantic model validation overhead
- Test environment setup complexity

## Tool Usage Patterns

### API Development
- FastAPI automatic documentation generation
- Pydantic model validation and serialization
- Async request handling throughout
- Structured error responses

### Testing Strategy
- pytest for unit and integration testing
- Mock external service dependencies
- Async test support with pytest-asyncio
- Environment-specific test configurations

### Logging and Monitoring
- Python logging module with structured output
- Request/response logging for debugging
- Error tracking with stack traces
- Performance monitoring for external API calls

## Security Considerations

### API Security
- Input validation via Pydantic models
- CORS configuration for cross-origin requests
- Error message sanitization
- Request timeout protection

### Credential Management
- Environment variable storage for API keys
- No hardcoded secrets in codebase
- Secure credential handling in DAOs
- Rotation-ready configuration pattern

## Deployment Considerations

### Local Development
- uvicorn with hot reload
- Environment-based configuration
- Console output for curriculum display
- Development-friendly error messages

### Production Readiness
- Configurable CORS origins
- Structured logging output
- Error handling without information leakage
- Health check endpoints for monitoring

### Scalability Factors
- Async/await throughout for high concurrency
- Stateless application design
- External service timeout configurations
- Resource-efficient request handling
