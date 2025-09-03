# LifeCurriculum Backend Service

A FastAPI-based backend service for managing life curriculum activities.

## Project Structure

```
LifeCurriculum/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Main FastAPI application
│   ├── config.py               # Configuration settings
│   ├── apis/
│   │   ├── __init__.py
│   │   ├── health.py           # Health check endpoints
│   │   └── activities/
│   │       ├── __init__.py
│   │       └── router.py       # Activities API routes
│   ├── daos/
│   │   ├── __init__.py
│   │   └── base_dao.py         # Base DAO for external services
│   └── models/
│       ├── __init__.py
│       └── responses.py        # Response models
├── tests/
│   ├── __init__.py
│   ├── test_health.py          # Health endpoint tests
│   └── test_activities.py      # Activities endpoint tests
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── run.py                      # Service startup script
└── README.md                   # This file
```

## Features

- **Health Check API**: `/ping` and `/health` endpoints for service monitoring
- **Activities API**: Ready-to-expand endpoints for activity management
- **DAO Pattern**: Base class for standardized external service communication
- **Configuration Management**: Environment-based configuration with pydantic-settings
- **CORS Support**: Cross-origin resource sharing middleware
- **Unit Tests**: Comprehensive test suite using pytest
- **Auto-documentation**: Swagger UI and ReDoc integration via FastAPI

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the Server**:
   
   **Option A - Using the startup script (recommended):**
   ```bash
   python run.py
   ```
   
   **Option B - Using uvicorn directly:**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   The server will start on `http://localhost:8000` by default.

4. **Access the Interactive API Test Page**:
   
   Once the server is running, open your browser and navigate to:
   - **Swagger UI (Interactive API testing)**: `http://localhost:8000/docs`
   - **ReDoc (Alternative documentation)**: `http://localhost:8000/redoc`
   
   The Swagger UI page allows you to test all API endpoints directly from your browser.

5. **Verify the Service**:
   ```bash
   # Run unit tests
   pytest
   
   # Test the ping endpoint via curl
   curl http://localhost:8000/ping
   
   # Or test via browser
   # Visit: http://localhost:8000/ping
   ```

## API Endpoints

### Health Check
- `GET /ping` - Simple health check
- `GET /health` - Detailed health information

### Activities (v1)
- `GET /api/v1/activities` - Get all activities (placeholder)
- `POST /api/v1/activities` - Create new activity (placeholder)

### Interactive API Testing & Documentation
- `GET /docs` - **Swagger UI** - Interactive API testing interface (recommended for testing APIs)
- `GET /redoc` - **ReDoc** - Alternative documentation format

## Configuration

The service can be configured via environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| HOST | 0.0.0.0 | Server host |
| PORT | 8000 | Server port |
| DEBUG | true | Debug mode |
| ALLOWED_ORIGINS | ["*"] | CORS allowed origins |
| DATABASE_URL | sqlite:///./lifecurriculum.db | Database connection |
| EXTERNAL_SERVICE_TIMEOUT | 30 | Timeout for external API calls |

## Development

### Running Tests
```bash
pytest
```

### Code Structure

- **APIs**: Route handlers organized by domain (health, activities)
- **DAOs**: Data access objects for external service communication
- **Models**: Pydantic models for request/response validation
- **Config**: Centralized configuration management

### Adding New APIs

1. Create a new router in `app/apis/`
2. Add route handlers with appropriate models
3. Include the router in `app/main.py`
4. Add corresponding tests in `tests/`

### Adding External Service Integration

1. Create a new DAO class inheriting from `BaseDAO`
2. Implement the `get_service_name()` method
3. Add service-specific methods using the base HTTP methods
4. Configure service URL and credentials in settings

## License

This project is licensed under the MIT License.
