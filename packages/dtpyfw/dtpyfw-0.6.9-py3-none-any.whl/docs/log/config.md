# LogConfig

## Overview

`LogConfig` is a builder class that provides a fluent interface for configuring the dtpyfw logging system. It enables developers to set up comprehensive logging configurations including API endpoints, log levels, file storage, console output, and specialized modes for Celery workers.

## Module Location

```python
from dtpyfw.log.config import LogConfig
```

## Class Definition

### `LogConfig`

A configuration builder for the logging system that uses method chaining to provide an intuitive configuration experience.

#### Attributes

- **`_config_data`** (`dict[str, Any]`): Internal dictionary storing all configuration key-value pairs.

## Constructor

### `__init__() -> None`

Initializes a new LogConfig instance with an empty configuration dictionary.

**Example:**
```python
config = LogConfig()
```

## Configuration Methods

All configuration methods return `self` to enable method chaining, allowing you to chain multiple configuration calls together.

### `set_api_url(api_url: str) -> Self`

Sets the URL endpoint for the remote logging API where logs will be sent.

**Parameters:**
- `api_url` (str): The full URL of the remote logging API endpoint.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config = LogConfig()
config.set_api_url("https://api.example.com/logs")
```

---

### `set_api_key(api_key: str) -> Self`

Sets the authentication key for the remote logging API.

**Parameters:**
- `api_key` (str): The API key or bearer token for authenticating with the remote logging API.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config.set_api_key("your-secret-api-key-here")
```

---

### `set_log_print(log_print: str) -> Self`

Enables or disables console (stdout) logging output.

**Parameters:**
- `log_print` (str): A string value indicating if console logging is enabled. Typically "true" or "false", or any truthy value.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config.set_log_print("true")  # Enable console output
```

---

### `set_log_store(log_store: str) -> Self`

Enables or disables log file storage with rotation.

**Parameters:**
- `log_store` (str): A string value indicating if file-based log storage is enabled.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config.set_log_store("true")  # Enable file storage
```

---

### `set_log_level(log_level: str) -> Self`

Sets the minimum logging level for filtering log messages.

**Parameters:**
- `log_level` (str): The logging level as a string (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"). The value is automatically converted to uppercase.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config.set_log_level("DEBUG")  # Log everything from DEBUG and above
config.set_log_level("info")   # Case-insensitive, converted to "INFO"
```

**Standard Log Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially problematic situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical errors that may cause application failure

---

### `set_log_file_name(log_file_name: str) -> Self`

Sets the filename for log file storage.

**Parameters:**
- `log_file_name` (str): The path and filename for storing log output.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config.set_log_file_name("application.log")
config.set_log_file_name("/var/log/myapp/app.log")  # Absolute path
```

---

### `set_log_file_backup_count(log_file_backup_count: int) -> Self`

Sets the number of rotated backup log files to retain.

**Parameters:**
- `log_file_backup_count` (int): The number of backup files to keep when log rotation occurs.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config.set_log_file_backup_count(5)  # Keep 5 backup files
```

**Note:** When the main log file reaches its maximum size, it will be rotated and renamed with a numeric suffix (e.g., `app.log.1`, `app.log.2`), keeping only the specified number of backups.

---

### `set_log_file_max_size(log_file_max_size: int) -> Self`

Sets the maximum size in bytes for a log file before rotation occurs.

**Parameters:**
- `log_file_max_size` (int): The maximum log file size in bytes before triggering rotation.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config.set_log_file_max_size(10 * 1024 * 1024)  # 10 MB
config.set_log_file_max_size(50_000_000)         # 50 MB
```

---

### `set_only_footprint_mode(only_footprint_mode: bool) -> Self`

Configures whether the API handler should only send logs explicitly marked as "footprints".

**Parameters:**
- `only_footprint_mode` (bool): If True, only logs created with `footprint=True` will be sent to the remote API.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config.set_only_footprint_mode(True)   # Only send footprint logs to API
config.set_only_footprint_mode(False)  # Send all logs to API
```

**Use Case:** This is useful when you want to reduce API traffic by only sending important, structured logs to your remote logging service while still maintaining local logging for all events.

---

### `set_celery_mode(celery_mode: bool) -> Self`

Enables specialized logging configuration for Celery worker contexts.

**Parameters:**
- `celery_mode` (bool): If True, configures logging to work properly with Celery's process model.

**Returns:**
- `Self`: The LogConfig instance for method chaining.

**Example:**
```python
config.set_celery_mode(True)   # Enable Celery-specific logging
config.set_celery_mode(False)  # Standard logging mode
```

**Note:** When enabled, this ensures that both the root logger and the Celery logger receive the same handlers and configuration, allowing proper log capturing from Celery tasks.

---

### `get(key: str, default: Any = None) -> Any`

Retrieves a configuration value by its key.

**Parameters:**
- `key` (str): The configuration key to retrieve.
- `default` (Any, optional): The default value to return if the key is not found. Defaults to None.

**Returns:**
- `Any`: The configuration value associated with the key, or the default value if not found.

**Example:**
```python
config = LogConfig()
config.set_log_level("DEBUG")

level = config.get("log_level")         # Returns "DEBUG"
api_url = config.get("api_url", None)   # Returns None (not set)
print_logs = config.get("log_print", False)  # Returns False (default)
```

## Complete Usage Examples

### Basic Console Logging

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

# Create and configure
config = LogConfig()
config.set_log_level("INFO").set_log_print("true")

# Initialize logging system
log_initializer(config)

# Now you can use standard Python logging
import logging
logging.info("Application started")
```

### File-Based Logging with Rotation

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

config = LogConfig()
config.set_log_level("DEBUG") \
      .set_log_store("true") \
      .set_log_file_name("myapp.log") \
      .set_log_file_max_size(5 * 1024 * 1024) \
      .set_log_file_backup_count(3)

log_initializer(config)
```

### Remote API Logging

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

config = LogConfig()
config.set_api_url("https://logs.example.com/api/v1/logs") \
      .set_api_key("secret-api-key-12345") \
      .set_log_level("INFO") \
      .set_only_footprint_mode(True)

log_initializer(config)
```

### Complete Multi-Handler Setup

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

# Configure all logging features
config = LogConfig()
config.set_api_url("https://api.example.com/logs") \
      .set_api_key("your-api-key") \
      .set_log_level("DEBUG") \
      .set_log_print("true") \
      .set_log_store("true") \
      .set_log_file_name("/var/log/app/application.log") \
      .set_log_file_max_size(10 * 1024 * 1024) \
      .set_log_file_backup_count(5) \
      .set_only_footprint_mode(True) \
      .set_celery_mode(False)

# Initialize the logging system
log_initializer(config)
```

### Celery Worker Configuration

```python
from celery import Celery
from celery.signals import setup_logging
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import celery_logger_handler

app = Celery('myapp')

config = LogConfig()
config.set_log_level("INFO") \
      .set_log_print("true") \
      .set_celery_mode(True) \
      .set_api_url("https://logs.example.com/api/logs") \
      .set_api_key("celery-api-key")

@setup_logging.connect
def configure_logging(logger, **kwargs):
    celery_logger_handler(config, logger, propagate=True)
```

### Environment-Based Configuration

```python
import os
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

# Build configuration from environment variables
config = LogConfig()

if os.getenv("LOG_API_URL"):
    config.set_api_url(os.getenv("LOG_API_URL"))
if os.getenv("LOG_API_KEY"):
    config.set_api_key(os.getenv("LOG_API_KEY"))

config.set_log_level(os.getenv("LOG_LEVEL", "INFO")) \
      .set_log_print(os.getenv("LOG_PRINT", "true")) \
      .set_log_store(os.getenv("LOG_STORE", "false"))

if os.getenv("LOG_STORE") == "true":
    config.set_log_file_name(os.getenv("LOG_FILE", "app.log")) \
          .set_log_file_max_size(int(os.getenv("LOG_MAX_SIZE", 10485760))) \
          .set_log_file_backup_count(int(os.getenv("LOG_BACKUP_COUNT", 3)))

log_initializer(config)
```

## Configuration Keys Reference

When using the `get()` method, these are the available configuration keys:

| Key | Type | Description | Set By Method |
|-----|------|-------------|---------------|
| `api_url` | str | Remote logging API URL | `set_api_url()` |
| `api_key` | str | API authentication key | `set_api_key()` |
| `log_print` | str | Enable console output | `set_log_print()` |
| `log_store` | str | Enable file storage | `set_log_store()` |
| `log_level` | str | Minimum log level (uppercase) | `set_log_level()` |
| `log_file_name` | str | Log file path | `set_log_file_name()` |
| `log_file_backup_count` | int | Number of backup files | `set_log_file_backup_count()` |
| `log_file_max_size` | int | Max file size in bytes | `set_log_file_max_size()` |
| `only_footprint_mode` | bool | Filter API logs to footprints only | `set_only_footprint_mode()` |
| `celery_mode` | bool | Enable Celery worker mode | `set_celery_mode()` |

## Best Practices

1. **Method Chaining**: Take advantage of the fluent interface by chaining configuration methods:
   ```python
   config = LogConfig().set_log_level("INFO").set_log_print("true")
   ```

2. **Always Initialize**: After configuring, always call `log_initializer(config)` to activate the logging system.

3. **Log Levels**: Start with "INFO" for production and "DEBUG" for development environments.

4. **File Rotation**: Always set both `log_file_max_size` and `log_file_backup_count` when enabling file storage to prevent disk space issues.

5. **Footprint Mode**: Use `only_footprint_mode=True` for API logging to reduce costs and API traffic by only sending important structured logs.

6. **Celery Configuration**: Always set `celery_mode=True` when configuring logging for Celery workers to ensure proper log capture.

## See Also

- [Initializer Documentation](./initializer.md) - For `log_initializer()` and `celery_logger_handler()` functions
- [Footprint Documentation](./footprint.md) - For creating structured footprint logs
- [Handlers Documentation](./handlers.md) - For understanding how handlers are configured
- [API Handler Documentation](./api_handler.md) - For remote API logging details
