# Initializer

## Overview

The `initializer` module provides functions for initializing and configuring the dtpyfw logging system. It contains `log_initializer()` for setting up standard application logging and `celery_logger_handler()` for configuring logging in Celery worker contexts. These functions serve as the primary entry points for activating the logging system with configured handlers.

## Module Location

```python
from dtpyfw.log.initializer import log_initializer, celery_logger_handler
```

## Functions

### `log_initializer(config: LogConfig) -> None`

Initializes the root logger and optionally the Celery logger based on the provided configuration.

This is the primary function for setting up the dtpyfw logging system. It creates handlers from the configuration, sets the appropriate log level, and attaches all handlers to the root logger. When `celery_mode` is enabled, it also configures the Celery logger with the same settings.

**Parameters:**

- `config` (LogConfig): The LogConfig object containing the logging configuration.

**Returns:**

- `None`: The function configures the logging system but doesn't return a value.

**Behavior:**

1. Retrieves the `celery_mode` setting from the configuration (defaults to `True`)
2. Calls `get_handlers_data(config)` to create handlers and determine log level
3. Configures the root logger:
   - Sets the log level
   - Adds all configured handlers
4. If `celery_mode` is enabled:
   - Configures the `celery` logger with the same log level
   - Adds all handlers to the `celery` logger

**Example:**

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

# Create configuration
config = LogConfig()
config.set_log_level("INFO") \
      .set_log_print("true") \
      .set_log_store("true") \
      .set_log_file_name("myapp.log")

# Initialize logging system
log_initializer(config)

# Logging is now configured and ready to use
import logging
logging.info("Application started")
```

---

### `celery_logger_handler(config: LogConfig, logger: Any, propagate: bool) -> None`

Configures a Celery logger with handlers from the provided configuration.

This function is designed to be used within Celery applications, typically in response to Celery's `setup_logging` signal. It configures the provided Celery logger instance with the handlers and log level from the configuration, but only if `celery_mode` is enabled.

**Parameters:**

- `config` (LogConfig): The LogConfig object containing the logging configuration.
- `logger` (Any): The Celery logger instance to configure (typically obtained from Celery signals).
- `propagate` (bool): Whether the logger should propagate messages to its parent logger.

**Returns:**

- `None`: The function configures the logger but doesn't return a value.

**Behavior:**

1. Checks if `celery_mode` is enabled in the configuration (defaults to `True`)
2. If `celery_mode` is enabled:
   - Calls `get_handlers_data(config)` to create handlers and determine log level
   - Sets the logger's log level
   - Sets the logger's `propagate` attribute
   - Adds all handlers to the logger

**Example:**

```python
from celery import Celery
from celery.signals import setup_logging
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import celery_logger_handler

app = Celery('myapp')

# Create logging configuration
config = LogConfig()
config.set_log_level("INFO") \
      .set_log_print("true") \
      .set_celery_mode(True) \
      .set_api_url("https://logs.example.com/api/logs") \
      .set_api_key("celery-api-key")

# Configure Celery logging when workers start
@setup_logging.connect
def configure_celery_logging(logger, **kwargs):
    celery_logger_handler(config, logger, propagate=True)
```

## Complete Usage Examples

### Basic Application Setup

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer
import logging

# Configure logging
config = LogConfig()
config.set_log_level("DEBUG") \
      .set_log_print("true")

# Initialize logging system
log_initializer(config)

# Use Python's standard logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Production Configuration

```python
import os
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

# Load configuration from environment variables
config = LogConfig()
config.set_api_url(os.environ["LOG_API_URL"]) \
      .set_api_key(os.environ["LOG_API_KEY"]) \
      .set_log_level(os.environ.get("LOG_LEVEL", "INFO")) \
      .set_log_print("false") \  # No console in production
      .set_log_store("true") \
      .set_log_file_name("/var/log/myapp/application.log") \
      .set_log_file_max_size(50 * 1024 * 1024) \  # 50 MB
      .set_log_file_backup_count(10) \
      .set_only_footprint_mode(True)

# Initialize logging
log_initializer(config)

# Application code
import logging
logger = logging.getLogger(__name__)
logger.info("Production application started")
```

### Development Configuration

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer
import logging

# Developer-friendly configuration
config = LogConfig()
config.set_log_level("DEBUG") \  # See everything
      .set_log_print("true") \    # Console output
      .set_log_store("false") \   # No file storage
      .set_celery_mode(False)     # Not using Celery in dev

log_initializer(config)

# Development logging
logger = logging.getLogger(__name__)
logger.debug("Detailed debug information for development")
```

### Multi-Environment Configuration

```python
import os
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

def setup_logging():
    """Configure logging based on environment."""
    env = os.environ.get("ENVIRONMENT", "development")
    
    config = LogConfig()
    
    if env == "production":
        config.set_log_level("WARNING") \
              .set_log_print("false") \
              .set_log_store("true") \
              .set_log_file_name("/var/log/app/prod.log") \
              .set_api_url(os.environ["LOG_API_URL"]) \
              .set_api_key(os.environ["LOG_API_KEY"])
    
    elif env == "staging":
        config.set_log_level("INFO") \
              .set_log_print("true") \
              .set_log_store("true") \
              .set_log_file_name("/var/log/app/staging.log") \
              .set_api_url(os.environ["LOG_API_URL"]) \
              .set_api_key(os.environ["LOG_API_KEY"])
    
    else:  # development
        config.set_log_level("DEBUG") \
              .set_log_print("true") \
              .set_log_store("false")
    
    log_initializer(config)

# Initialize based on environment
setup_logging()

import logging
logging.info(f"Logging configured for {os.environ.get('ENVIRONMENT', 'development')}")
```

### Celery Application Setup

```python
from celery import Celery
from celery.signals import setup_logging, after_setup_task_logger
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer, celery_logger_handler

# Create Celery app
app = Celery('myapp', broker='redis://localhost:6379/0')

# Create logging configuration
config = LogConfig()
config.set_log_level("INFO") \
      .set_log_print("true") \
      .set_log_store("true") \
      .set_log_file_name("celery_worker.log") \
      .set_celery_mode(True) \
      .set_api_url("https://logs.example.com/api/logs") \
      .set_api_key("celery-api-key") \
      .set_only_footprint_mode(True)

# Configure main logger at worker startup
@setup_logging.connect
def configure_main_logging(**kwargs):
    """Configure main Celery logger."""
    log_initializer(config)

# Configure task logger
@after_setup_task_logger.connect
def configure_task_logger(logger, **kwargs):
    """Configure task-specific logger."""
    celery_logger_handler(config, logger, propagate=False)

# Define tasks
@app.task
def my_task(x, y):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Task executing with {x} and {y}")
    return x + y
```

### Complete Celery Integration

```python
import os
from celery import Celery
from celery.signals import setup_logging
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import celery_logger_handler
from dtpyfw.log.footprint import leave

# Celery app configuration
app = Celery('myapp')
app.config_from_object('celeryconfig')

# Logging configuration
LOG_CONFIG = LogConfig()
LOG_CONFIG.set_log_level("INFO") \
         .set_log_print("true") \
         .set_log_store("true") \
         .set_log_file_name(os.path.join("logs", "celery.log")) \
         .set_celery_mode(True) \
         .set_api_url(os.environ.get("LOG_API_URL")) \
         .set_api_key(os.environ.get("LOG_API_KEY")) \
         .set_only_footprint_mode(True)

@setup_logging.connect
def setup_celery_logging(logger, **kwargs):
    """Configure Celery logging on worker startup."""
    celery_logger_handler(LOG_CONFIG, logger, propagate=True)
    
    # Log worker startup
    leave(
        log_type="info",
        controller="celery.worker.startup",
        subject="Celery Worker Started",
        message="Celery worker initialized and ready to process tasks"
    )

@app.task(bind=True)
def process_order(self, order_id: str):
    """Process an order with logging."""
    leave(
        log_type="info",
        controller="tasks.process_order",
        subject="Order Processing Started",
        message=f"Starting to process order {order_id}",
        payload={"order_id": order_id, "task_id": self.request.id}
    )
    
    try:
        # Order processing logic
        result = do_process_order(order_id)
        
        leave(
            log_type="info",
            controller="tasks.process_order",
            subject="Order Processed Successfully",
            message=f"Order {order_id} processed",
            payload={"order_id": order_id, "result": result}
        )
        return result
        
    except Exception as e:
        leave(
            log_type="error",
            controller="tasks.process_order",
            subject="Order Processing Failed",
            message=f"Failed to process order {order_id}: {str(e)}",
            payload={"order_id": order_id, "error": str(e)}
        )
        raise
```

### Flask Application Integration

```python
from flask import Flask
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer
import logging

def create_app():
    """Flask application factory with logging."""
    app = Flask(__name__)
    
    # Configure logging
    config = LogConfig()
    config.set_log_level(app.config.get("LOG_LEVEL", "INFO")) \
          .set_log_print("true") \
          .set_log_store("true") \
          .set_log_file_name("flask_app.log") \
          .set_api_url(app.config.get("LOG_API_URL")) \
          .set_api_key(app.config.get("LOG_API_KEY"))
    
    log_initializer(config)
    
    # Use Flask's logger
    app.logger.info("Flask application initialized")
    
    @app.route("/")
    def index():
        app.logger.info("Index page accessed")
        return "Hello, World!"
    
    return app

app = create_app()
```

### FastAPI Application Integration

```python
from fastapi import FastAPI
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer
from dtpyfw.log.footprint import leave
import logging

# Initialize logging before app creation
config = LogConfig()
config.set_log_level("INFO") \
      .set_log_print("true") \
      .set_api_url("https://logs.example.com/api/logs") \
      .set_api_key("fastapi-key")

log_initializer(config)

# Create FastAPI app
app = FastAPI(title="My API")
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    leave(
        log_type="info",
        controller="fastapi.startup",
        subject="API Server Started",
        message="FastAPI application started successfully"
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    leave(
        log_type="info",
        controller="fastapi.shutdown",
        subject="API Server Stopped",
        message="FastAPI application shutting down"
    )

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}
```

### Testing Configuration

```python
import pytest
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """Configure logging for test suite."""
    config = LogConfig()
    config.set_log_level("DEBUG") \  # Verbose for tests
          .set_log_print("false") \  # Don't clutter test output
          .set_log_store("true") \   # Save to file for review
          .set_log_file_name("test_logs.log")
    
    log_initializer(config)
    
    import logging
    logging.info("Test logging configured")

def test_something():
    """Test with logging configured."""
    import logging
    logger = logging.getLogger(__name__)
    logger.debug("Running test")
    # Test code...
```

## Configuration Flow

Understanding how `log_initializer()` works internally:

```python
def log_initializer(config: LogConfig) -> None:
    # 1. Check celery mode
    celery_mode = config.get("celery_mode", True)
    
    # 2. Get handlers and log level from configuration
    handlers, log_level = get_handlers_data(config=config)
    
    # 3. Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 4. Get celery logger
    celery_logger = logging.getLogger("celery")
    
    # 5. If celery mode, configure celery logger
    if celery_mode:
        celery_logger.setLevel(log_level)
    
    # 6. Add handlers to loggers
    for handle in handlers:
        root_logger.addHandler(handle)
        if celery_mode:
            celery_logger.addHandler(handle)
```

## Best Practices

1. **Call log_initializer Early**: Initialize logging as early as possible in your application:
   ```python
   # Good - at application startup
   from dtpyfw.log.initializer import log_initializer
   from dtpyfw.log.config import LogConfig
   
   config = LogConfig()
   config.set_log_level("INFO").set_log_print("true")
   log_initializer(config)
   
   # Rest of application code
   import logging
   logging.info("Application starting")
   ```

2. **Single Initialization**: Call `log_initializer()` only once per application:
   ```python
   # Good - single initialization
   if __name__ == "__main__":
       log_initializer(config)
       run_application()
   
   # Avoid - multiple initializations
   # Don't call log_initializer() multiple times
   ```

3. **Celery Mode**: Always enable `celery_mode` when running Celery workers:
   ```python
   config.set_celery_mode(True)  # For Celery workers
   config.set_celery_mode(False) # For non-Celery apps
   ```

4. **Use celery_logger_handler for Celery Signals**: In Celery applications, use `celery_logger_handler()` with the `setup_logging` signal:
   ```python
   @setup_logging.connect
   def configure_logging(logger, **kwargs):
       celery_logger_handler(config, logger, propagate=True)
   ```

5. **Configuration Management**: Centralize configuration creation:
   ```python
   # config.py
   def get_log_config():
       config = LogConfig()
       # ... configuration
       return config
   
   # main.py
   from config import get_log_config
   from dtpyfw.log.initializer import log_initializer
   
   log_initializer(get_log_config())
   ```

6. **Environment-Based Setup**: Use environment variables for different environments:
   ```python
   import os
   
   config = LogConfig()
   config.set_log_level(os.getenv("LOG_LEVEL", "INFO"))
   config.set_log_print(os.getenv("LOG_PRINT", "true"))
   ```

## Celery Mode Details

### When celery_mode is True

- Both root logger and `celery` logger are configured
- All handlers are attached to both loggers
- Celery task logs are captured and processed
- Default setting: `True`

### When celery_mode is False

- Only root logger is configured
- `celery` logger is not touched
- Use for non-Celery applications
- Reduces overhead if Celery is not used

Example:

```python
# Celery application
config = LogConfig()
config.set_celery_mode(True)  # Configure Celery logger
log_initializer(config)

# Non-Celery application
config = LogConfig()
config.set_celery_mode(False)  # Skip Celery logger
log_initializer(config)
```

## Propagate Parameter in celery_logger_handler

The `propagate` parameter controls whether the Celery logger propagates messages to its parent:

```python
# propagate=True: Messages propagate to parent logger
celery_logger_handler(config, logger, propagate=True)
# Celery logs appear in both Celery logger and root logger

# propagate=False: Messages don't propagate
celery_logger_handler(config, logger, propagate=False)
# Celery logs only appear in Celery logger
```

**When to use:**
- `propagate=True`: Most common case, allows full logging integration
- `propagate=False`: When you want separate Celery log handling

## Troubleshooting

### Logs Not Appearing After Initialization

**Problem:** No logs appear after calling `log_initializer()`

**Possible Causes:**

1. No handlers configured
2. Log level set too high
3. Configuration not applied

**Solution:**

```python
# Ensure at least one handler is configured
config = LogConfig()
config.set_log_level("DEBUG")  # Lower threshold
config.set_log_print("true")   # Enable console output
log_initializer(config)

import logging
logging.debug("Test message")
```

### Duplicate Log Messages

**Problem:** Each log message appears multiple times

**Possible Causes:**

1. `log_initializer()` called multiple times
2. Handlers added multiple times

**Solution:**

```python
# Remove existing handlers before initialization
import logging
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Now initialize
log_initializer(config)
```

### Celery Logs Not Captured

**Problem:** Celery task logs not appearing

**Solutions:**

1. Enable `celery_mode`:
   ```python
   config.set_celery_mode(True)
   ```

2. Use `celery_logger_handler()` with signals:
   ```python
   @setup_logging.connect
   def configure_logging(logger, **kwargs):
       celery_logger_handler(config, logger, propagate=True)
   ```

### API Logs Not Sent

**Problem:** Logs not reaching remote API

**Solution:**

```python
# Verify API configuration
config = LogConfig()
config.set_api_url("https://valid-url.com/api/logs")  # Valid URL
config.set_api_key("valid-key")  # Valid key
config.set_only_footprint_mode(True)  # Or False for all logs
log_initializer(config)

# Use footprint logs
from dtpyfw.log.footprint import leave
leave(
    log_type="info",
    subject="Test",
    message="Test message",
    footprint=True  # Required if only_footprint_mode=True
)
```

## See Also

- [Config Documentation](./config.md) - For `LogConfig` class and configuration options
- [Handlers Documentation](./handlers.md) - For `get_handlers_data()` used internally
- [API Handler Documentation](./api_handler.md) - For remote API logging
- [Footprint Documentation](./footprint.md) - For creating structured logs
- [Formatter Documentation](./formatter.md) - For log formatting
