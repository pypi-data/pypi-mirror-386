# Handlers

## Overview

The `handlers` module provides the `get_handlers_data()` function, which is responsible for creating and configuring log handlers based on a `LogConfig` object. This function is a central piece of the dtpyfw logging system, automatically setting up API handlers, console handlers, and rotating file handlers according to the provided configuration.

## Module Location

```python
from dtpyfw.log.handlers import get_handlers_data
```

## Functions

### `get_handlers_data(config: LogConfig) -> tuple[list[logging.Handler], int]`

Configures and returns a list of log handlers along with the resolved log level based on the provided configuration.

This function examines the `LogConfig` object and creates appropriate handlers for different logging destinations (API, console, file). Each handler is configured with the `CustomFormatter` and the specified log level.

**Parameters:**

- `config` (LogConfig): The LogConfig object containing the logging configuration.

**Returns:**

- `tuple[list[logging.Handler], int]`: A tuple containing:
  - `list[logging.Handler]`: A list of configured logging handlers (may be empty if no handlers are enabled).
  - `int`: The resolved log level as a logging module constant (e.g., `logging.INFO`, `logging.DEBUG`).

**Behavior:**

The function creates handlers based on configuration settings in the following order:

1. **API Handler** (LoggerHandler):
   - Created if both `api_url` and `api_key` are configured
   - Uses `only_footprint_mode` setting (defaults to `True`)
   - Sends logs to remote API endpoint

2. **Console Handler** (StreamHandler):
   - Created if `log_print` is truthy
   - Outputs logs to stdout/stderr

3. **File Handler** (RotatingFileHandler):
   - Created if `log_store` is truthy
   - Writes logs to file with automatic rotation
   - Uses `log_file_name` (defaults to "app.log")
   - Configures `log_file_max_size` (defaults to 10 MB)
   - Configures `log_file_backup_count` (defaults to 1)

All handlers are configured with:
- The `CustomFormatter` for consistent formatting
- The log level from `config.get("log_level", default="INFO")`

**Example:**

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.handlers import get_handlers_data

# Create configuration
config = LogConfig()
config.set_log_level("DEBUG") \
      .set_log_print("true") \
      .set_log_store("true") \
      .set_log_file_name("myapp.log")

# Get configured handlers
handlers, log_level = get_handlers_data(config)

print(f"Number of handlers: {len(handlers)}")  # 2 (console + file)
print(f"Log level: {log_level}")  # 10 (logging.DEBUG)

# Apply handlers to logger
import logging
logger = logging.getLogger()
logger.setLevel(log_level)
for handler in handlers:
    logger.addHandler(handler)
```

## Configuration Options

The function reads the following configuration keys from the `LogConfig` object:

### API Handler Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_url` | str | None | URL of the remote logging API endpoint |
| `api_key` | str | None | Authentication key for the API |
| `only_footprint_mode` | bool | True | If True, only send logs marked as footprints to the API |

### Console Handler Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `log_print` | str/bool | False | Whether to enable console output |

### File Handler Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `log_store` | str/bool | False | Whether to enable file logging |
| `log_file_name` | str | "app.log" | Path and filename for the log file |
| `log_file_max_size` | int | 10485760 | Maximum file size in bytes (default: 10 MB) |
| `log_file_backup_count` | int | 1 | Number of backup files to keep |

### General Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `log_level` | str | "INFO" | Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

## Complete Usage Examples

### Console Output Only

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.handlers import get_handlers_data
import logging

# Configure for console output only
config = LogConfig()
config.set_log_level("INFO").set_log_print("true")

# Get handlers
handlers, log_level = get_handlers_data(config)

# Setup logger
logger = logging.getLogger()
logger.setLevel(log_level)
for handler in handlers:
    logger.addHandler(handler)

# Log messages
logger.info("This appears on console")
logger.debug("This is filtered out (level too low)")
```

### File Logging with Rotation

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.handlers import get_handlers_data
import logging

# Configure file logging with rotation
config = LogConfig()
config.set_log_level("DEBUG") \
      .set_log_store("true") \
      .set_log_file_name("/var/log/myapp/application.log") \
      .set_log_file_max_size(20 * 1024 * 1024) \  # 20 MB
      .set_log_file_backup_count(10)  # Keep 10 backups

# Get handlers
handlers, log_level = get_handlers_data(config)

# Setup logger
logger = logging.getLogger()
logger.setLevel(log_level)
for handler in handlers:
    logger.addHandler(handler)

# Logs are written to file with automatic rotation
logger.debug("Debug information")
logger.info("Application event")
```

### API Logging

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.handlers import get_handlers_data
import logging

# Configure API logging
config = LogConfig()
config.set_api_url("https://logs.example.com/api/v1/logs") \
      .set_api_key("secret-api-key-xyz") \
      .set_log_level("INFO") \
      .set_only_footprint_mode(True)

# Get handlers
handlers, log_level = get_handlers_data(config)

# Setup logger
logger = logging.getLogger()
logger.setLevel(log_level)
for handler in handlers:
    logger.addHandler(handler)

# Only footprint logs are sent to API
from dtpyfw.log.footprint import leave
leave(
    log_type="info",
    controller="myapp.startup",
    subject="Application Started",
    message="Application initialized successfully"
)
```

### Combined Handlers (Console + File + API)

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.handlers import get_handlers_data
import logging

# Configure all handler types
config = LogConfig()
config.set_api_url("https://logs.example.com/api/logs") \
      .set_api_key("my-api-key") \
      .set_log_level("DEBUG") \
      .set_log_print("true") \
      .set_log_store("true") \
      .set_log_file_name("app.log") \
      .set_log_file_max_size(10 * 1024 * 1024) \
      .set_log_file_backup_count(5) \
      .set_only_footprint_mode(True)

# Get handlers (returns list with 3 handlers)
handlers, log_level = get_handlers_data(config)

print(f"Created {len(handlers)} handlers:")
for handler in handlers:
    print(f"  - {type(handler).__name__}")
# Output:
# Created 3 handlers:
#   - LoggerHandler
#   - StreamHandler
#   - RotatingFileHandler

# Setup logger
logger = logging.getLogger()
logger.setLevel(log_level)
for handler in handlers:
    logger.addHandler(handler)

# All logs go to console and file
logger.debug("Debug message - console & file")
logger.info("Info message - console & file")

# Only footprint logs go to API
from dtpyfw.log.footprint import leave
leave(
    log_type="error",
    controller="payment.process",
    subject="Payment Failed",
    message="Payment processing error",
    footprint=True
)
# This goes to: API + console + file
```

### Minimal Configuration (No Handlers)

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.handlers import get_handlers_data

# Configuration with no handlers enabled
config = LogConfig()
config.set_log_level("INFO")
# Don't set log_print, log_store, or api_url

# Get handlers
handlers, log_level = get_handlers_data(config)

print(f"Number of handlers: {len(handlers)}")  # 0
print(f"Log level: {log_level}")  # 20 (logging.INFO)

# Logging will work but output goes nowhere
import logging
logger = logging.getLogger()
logger.setLevel(log_level)
for handler in handlers:
    logger.addHandler(handler)

logger.info("This log is processed but not output anywhere")
```

### Custom Configuration with Defaults

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.handlers import get_handlers_data

# Minimal configuration relying on defaults
config = LogConfig()
config.set_log_store("true")
# Uses default log_level="INFO"
# Uses default log_file_name="app.log"
# Uses default log_file_max_size=10MB
# Uses default log_file_backup_count=1

handlers, log_level = get_handlers_data(config)

# This creates a single RotatingFileHandler with default settings
import logging
logger = logging.getLogger()
logger.setLevel(log_level)
for handler in handlers:
    logger.addHandler(handler)

logger.info("Logged to app.log with default settings")
```

### Inspecting Handler Configuration

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.handlers import get_handlers_data
import logging
from logging.handlers import RotatingFileHandler
from dtpyfw.log.api_handler import LoggerHandler

# Configure multiple handlers
config = LogConfig()
config.set_log_level("WARNING") \
      .set_log_print("true") \
      .set_log_store("true") \
      .set_log_file_name("warnings.log") \
      .set_api_url("https://api.example.com/logs") \
      .set_api_key("key")

handlers, log_level = get_handlers_data(config)

# Inspect handler details
for handler in handlers:
    print(f"Handler: {type(handler).__name__}")
    print(f"  Level: {logging.getLevelName(handler.level)}")
    print(f"  Formatter: {type(handler.formatter).__name__}")
    
    if isinstance(handler, RotatingFileHandler):
        print(f"  File: {handler.baseFilename}")
        print(f"  Max Size: {handler.maxBytes} bytes")
        print(f"  Backup Count: {handler.backupCount}")
    elif isinstance(handler, LoggerHandler):
        print(f"  API URL: {handler.logger.api_url}")
        print(f"  Footprint Mode: {handler.only_footprint_mode}")

# Output:
# Handler: LoggerHandler
#   Level: WARNING
#   Formatter: CustomFormatter
#   API URL: https://api.example.com/logs
#   Footprint Mode: True
# Handler: StreamHandler
#   Level: WARNING
#   Formatter: CustomFormatter
# Handler: RotatingFileHandler
#   Level: WARNING
#   Formatter: CustomFormatter
#   File: warnings.log
#   Max Size: 10485760 bytes
#   Backup Count: 1
```

## Integration with log_initializer

The `get_handlers_data()` function is typically called by `log_initializer()` rather than directly:

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

# The recommended approach
config = LogConfig()
config.set_log_level("INFO") \
      .set_log_print("true") \
      .set_log_store("true")

# log_initializer calls get_handlers_data internally
log_initializer(config)

# Logging is now configured
import logging
logging.info("Ready to log")
```

Behind the scenes, `log_initializer` does this:

```python
def log_initializer(config: LogConfig) -> None:
    # Calls get_handlers_data
    handlers, log_level = get_handlers_data(config=config)
    
    # Configures root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Adds all handlers
    for handle in handlers:
        root_logger.addHandler(handle)
```

## Handler Creation Logic

The internal logic of `get_handlers_data()` can be understood as:

```python
def get_handlers_data(config: LogConfig) -> tuple[list[logging.Handler], int]:
    formatter = CustomFormatter()
    handlers = []
    
    # Get log level
    log_level = getattr(logging, config.get("log_level", default="INFO"))
    
    # 1. API Handler
    if config.get("api_url") and config.get("api_key"):
        api_handler = LoggerHandler(
            logging_api_url=config.get("api_url"),
            logging_api_key=config.get("api_key"),
            only_footprint_mode=config.get("only_footprint_mode", True)
        )
        api_handler.setLevel(log_level)
        api_handler.setFormatter(formatter)
        handlers.append(api_handler)
    
    # 2. Console Handler
    if config.get("log_print", default=False):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
    
    # 3. File Handler
    if config.get("log_store", default=False):
        file_handler = RotatingFileHandler(
            config.get("log_file_name", default="app.log"),
            maxBytes=config.get("log_file_max_size", default=10*1024*1024),
            backupCount=config.get("log_file_backup_count", default=1) or 1
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    return handlers, log_level
```

## Log Levels

The function converts string log levels to Python logging constants:

| String | Constant | Numeric Value | Description |
|--------|----------|---------------|-------------|
| "DEBUG" | logging.DEBUG | 10 | Detailed diagnostic information |
| "INFO" | logging.INFO | 20 | General informational messages |
| "WARNING" | logging.WARNING | 30 | Warning messages |
| "ERROR" | logging.ERROR | 40 | Error messages |
| "CRITICAL" | logging.CRITICAL | 50 | Critical errors |

Example:

```python
config = LogConfig()
config.set_log_level("WARNING")

handlers, log_level = get_handlers_data(config)
print(log_level)  # 30 (logging.WARNING)
```

## Best Practices

1. **Use log_initializer**: Instead of calling `get_handlers_data()` directly, use `log_initializer()` which handles the complete setup:
   ```python
   from dtpyfw.log.initializer import log_initializer
   log_initializer(config)
   ```

2. **Configure Before Initialization**: Set all configuration options before calling `get_handlers_data()` or `log_initializer()`:
   ```python
   config = LogConfig()
   config.set_log_level("INFO")
   config.set_log_print("true")
   # ... all configuration
   log_initializer(config)  # Now initialize
   ```

3. **File Rotation Settings**: Always configure both max size and backup count for file handlers:
   ```python
   config.set_log_file_max_size(20 * 1024 * 1024)  # 20 MB
   config.set_log_file_backup_count(10)  # Keep 10 backups
   ```

4. **Log Level Hierarchy**: Remember that log level affects all handlers. Set it appropriately:
   - Development: "DEBUG"
   - Production: "INFO" or "WARNING"

5. **API Handler with Footprint Mode**: For production API logging, use `only_footprint_mode=True` to reduce API traffic:
   ```python
   config.set_only_footprint_mode(True)
   ```

6. **Check Handler Count**: Verify handlers were created as expected:
   ```python
   handlers, _ = get_handlers_data(config)
   if not handlers:
       print("Warning: No handlers configured")
   ```

## Return Value Details

### Handler List

The returned list can contain 0-3 handlers:

- **0 handlers**: No logging destinations configured
- **1 handler**: Only one destination (API, console, or file)
- **2 handlers**: Two destinations configured
- **3 handlers**: All three destinations configured

### Log Level

The log level is returned as an integer constant from the `logging` module:

```python
handlers, log_level = get_handlers_data(config)

import logging
if log_level == logging.DEBUG:
    print("Debug level enabled")
elif log_level == logging.INFO:
    print("Info level enabled")
# etc.
```

## Troubleshooting

### No Handlers Created

**Problem:** `handlers` list is empty

**Causes:**
- No logging destinations configured (`log_print`, `log_store`, or API settings not set)
- Configuration values are falsy (e.g., `log_print="false"` as string)

**Solution:**
```python
config.set_log_print("true")  # Or set log_store or API settings
```

### API Handler Not Created

**Problem:** API handler missing even though API settings configured

**Cause:** Both `api_url` AND `api_key` must be set

**Solution:**
```python
config.set_api_url("https://api.example.com/logs")
config.set_api_key("your-api-key")  # Both required
```

### File Handler Fails

**Problem:** File handler raises PermissionError or FileNotFoundError

**Causes:**
- Insufficient permissions to write to file location
- Directory doesn't exist
- File path is invalid

**Solution:**
```python
import os
log_dir = "/var/log/myapp"
os.makedirs(log_dir, exist_ok=True)  # Create directory first
config.set_log_file_name(os.path.join(log_dir, "app.log"))
```

### All Logs Filtered Out

**Problem:** Logs not appearing despite handlers configured

**Cause:** Log level set too high

**Solution:**
```python
config.set_log_level("DEBUG")  # Lower the threshold
```

## Performance Considerations

1. **Handler Count**: Each handler adds processing overhead. Use only necessary handlers.

2. **File I/O**: File handlers perform disk I/O which can be slow. Consider using async logging for high-throughput applications.

3. **API Calls**: API handlers make network requests which add latency. Use `only_footprint_mode=True` to minimize API traffic.

4. **Formatter Overhead**: All handlers use `CustomFormatter` which checks for `details` attribute on each log record. This is minimal overhead but worth noting for extremely high-throughput scenarios.

## See Also

- [Config Documentation](./config.md) - For `LogConfig` class and configuration options
- [Initializer Documentation](./initializer.md) - For `log_initializer()` which uses this function
- [API Handler Documentation](./api_handler.md) - For `LoggerHandler` details
- [Formatter Documentation](./formatter.md) - For `CustomFormatter` used by all handlers
- [Footprint Documentation](./footprint.md) - For creating structured logs
