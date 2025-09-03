# LifeCurriculum Logging Guide

This guide explains how to use the centralized logging system that has been set up for the LifeCurriculum service.

## Features

- **EST Timestamps**: All log entries are automatically formatted with Eastern Standard Time timestamps
- **File Information**: Each log entry includes the filename, line number, and function name where the log was generated
- **Log Levels**: Supports DEBUG, INFO, WARN, and ERROR levels
- **Flexible Configuration**: Can log to console only or both console and file
- **Third-party Library Filtering**: Reduces noise from uvicorn and fastapi logs

## Configuration

Logging is configured through the application settings in `app/config.py`:

```python
# Logging configuration
log_level: str = "INFO"  # DEBUG, INFO, WARN, ERROR
log_file: Optional[str] = None  # Set to file path if you want to log to file
```

You can also set these via environment variables:
- `LOG_LEVEL=DEBUG`
- `LOG_FILE=logs/app.log`

## Usage

### Basic Usage

```python
from app.logger import get_logger

# Get logger for your module (recommended)
logger = get_logger(__name__)

# Log at different levels
logger.debug("Detailed debugging information")
logger.info("General information about application flow")
logger.warning("Something unexpected happened but application continues")
logger.error("An error occurred that needs attention")
```

### Example Log Output

```
2025-08-13 21:54:36 EST | INFO  | router.py:25 | get_activities() | Fetching activities for user: user123
2025-08-13 21:54:37 EST | WARN  | create_activity.py:45 | validate_activity() | Activity validation warning: missing optional field
2025-08-13 21:54:38 EST | ERROR | openai_dao.py:78 | generate_response() | OpenAI API request failed: rate limit exceeded
2025-08-13 21:54:39 EST | DEBUG | minio_dao.py:102 | upload_file() | Uploading file to bucket: lc-generated-audio
```

## Log Format

Each log entry contains:
- **Timestamp**: EST timezone with format `YYYY-MM-DD HH:MM:SS EST`
- **Level**: DEBUG, INFO, WARN, ERROR (padded to 5 characters)
- **File**: The source filename where the log was generated
- **Line**: Line number in the source file
- **Function**: Function name where the log was generated
- **Message**: Your log message

## Best Practices

### 1. Use Module-Specific Loggers
Always pass `__name__` to get_logger to create module-specific loggers:

```python
logger = get_logger(__name__)
```

### 2. Choose Appropriate Log Levels

- **DEBUG**: Detailed information for diagnosing problems, typically only of interest when diagnosing problems
- **INFO**: General information about what the application is doing (user actions, system state changes)
- **WARNING**: Something unexpected happened, but the application can continue
- **ERROR**: A serious problem occurred that prevented a function from completing

### 3. Include Context in Log Messages

```python
# Good
logger.info(f"Processing activity creation for user: {user_id}")
logger.error(f"Failed to connect to database: {str(error)}")

# Less helpful
logger.info("Processing activity")
logger.error("Database error")
```

### 4. Log Structured Information

```python
# For complex operations, log the start and end
logger.info(f"Starting curriculum generation for topic: {topic}")
try:
    # ... processing ...
    logger.info(f"Successfully generated curriculum with {len(lessons)} lessons")
except Exception as e:
    logger.error(f"Curriculum generation failed: {str(e)}")
```

## Runtime Log Level Changes

You can change the log level at runtime:

```python
from app.logger import set_log_level

# Change to DEBUG for more detailed logging
set_log_level("DEBUG")

# Change back to INFO
set_log_level("INFO")
```

## File Logging

To enable file logging, set the `LOG_FILE` environment variable or update the config:

```bash
export LOG_FILE="logs/lifecurriculum.log"
```

The logger will automatically create the directory if it doesn't exist.

## Integration with FastAPI

The logging system is automatically initialized when the FastAPI application starts up. You'll see initialization messages like:

```
2025-08-13 21:54:35 EST | INFO  | main.py:23 | lifespan() | Starting LifeCurriculum service...
2025-08-13 21:54:35 EST | INFO  | main.py:24 | lifespan() | Log level set to: INFO
```

## Dependencies

The logging system requires the `pytz` package for EST timezone handling. This has been added to `requirements.txt`.

## Example Implementation

Here's how you would typically add logging to a new module:

```python
from app.logger import get_logger

# Get logger at module level
logger = get_logger(__name__)

async def create_new_activity(activity_data: dict):
    """Create a new activity with proper logging"""
    logger.info(f"Creating new activity: {activity_data.get('title', 'Unknown')}")
    
    try:
        # Validate input
        if not activity_data.get('title'):
            logger.warning("Activity creation attempted without title")
            raise ValueError("Activity title is required")
        
        # Process activity
        logger.debug(f"Processing activity data: {activity_data}")
        
        # ... business logic ...
        
        logger.info(f"Successfully created activity with ID: {activity_id}")
        return activity_id
        
    except ValueError as e:
        logger.error(f"Activity validation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating activity: {str(e)}")
        raise
```

This logging system provides comprehensive visibility into your application's behavior while maintaining clean, readable logs with proper timezone handling and contextual information.
