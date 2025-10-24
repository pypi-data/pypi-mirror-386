# Custom Formatter

## Overview

The `formatter` module provides a custom log formatter (`CustomFormatter`) that intelligently adapts to structured logging. It checks whether log records contain structured `details` and formats them accordingly, making it ideal for use with the dtpyfw logging system that supports both traditional and structured logging patterns.

## Module Location

```python
from dtpyfw.log.formatter import CustomFormatter
```

## Class Definition

### `CustomFormatter`

A custom logging formatter that extends Python's standard `logging.Formatter` to provide dynamic formatting based on log record content.

#### Inheritance

Inherits from `logging.Formatter`

#### Constructor

##### `__init__() -> None`

Initializes the CustomFormatter with a default date format.

**Parameters:**

None

**Default Date Format:**

`%Y-%m-%d %H:%M:%S` (e.g., "2025-10-24 14:30:45")

**Example:**

```python
from dtpyfw.log.formatter import CustomFormatter

formatter = CustomFormatter()
```

## Methods

### `format(record: logging.LogRecord) -> str`

Formats the specified log record as text with dynamic format string selection.

This method dynamically adjusts the format string based on whether the log record contains a structured `details` attribute. This allows structured logs (typically created with the `footprint.leave()` function) to display their full details dictionary, while standard logs use the basic message format.

**Parameters:**

- `record` (logging.LogRecord): The log record to format.

**Returns:**

- `str`: The formatted log string with timestamp, level, and message or details.

**Behavior:**

1. Checks if the record has a `details` attribute (set via `extra={"details": {...}}`)
2. If `details` exists:
   - Format: `YYYY-MM-DD HH:MM:SS - LEVEL - {details dictionary}`
3. If no `details`:
   - Format: `YYYY-MM-DD HH:MM:SS - LEVEL - message`
4. Calls the parent `format()` method with the appropriate format string

**Example:**

```python
import logging
from dtpyfw.log.formatter import CustomFormatter

# Create and configure formatter
formatter = CustomFormatter()
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Standard log (no details)
logger.info("Application started")
# Output: 2025-10-24 14:30:45 - INFO - Application started

# Structured log (with details)
logger.info("User logged in", extra={
    "details": {
        "user_id": "12345",
        "controller": "auth.login",
        "subject": "User Login"
    }
})
# Output: 2025-10-24 14:30:45 - INFO - {'user_id': '12345', 'controller': 'auth.login', 'subject': 'User Login'}
```

## Complete Usage Examples

### Basic Console Logging

```python
import logging
from dtpyfw.log.formatter import CustomFormatter

# Create formatter
formatter = CustomFormatter()

# Create and configure console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.DEBUG)

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

# Standard logging
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# Output:
# 2025-10-24 14:30:45 - DEBUG - Debug message
# 2025-10-24 14:30:45 - INFO - Info message
# 2025-10-24 14:30:45 - WARNING - Warning message
# 2025-10-24 14:30:45 - ERROR - Error message
# 2025-10-24 14:30:45 - CRITICAL - Critical message
```

### File Logging with Rotation

```python
import logging
from logging.handlers import RotatingFileHandler
from dtpyfw.log.formatter import CustomFormatter

# Create formatter
formatter = CustomFormatter()

# Create rotating file handler
file_handler = RotatingFileHandler(
    filename="application.log",
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Configure logger
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Log messages
logger.info("Application started")
logger.error("An error occurred", extra={
    "details": {
        "error_code": "ERR_001",
        "controller": "main.startup"
    }
})
```

### Structured Logging with Details

```python
import logging
from dtpyfw.log.formatter import CustomFormatter

# Setup logging
formatter = CustomFormatter()
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Log with structured details
logger.info("Payment processed", extra={
    "details": {
        "log_type": "info",
        "controller": "payment.process",
        "subject": "Payment Successful",
        "message": "Credit card payment completed",
        "payload": {
            "transaction_id": "txn_12345",
            "amount": 99.99,
            "currency": "USD"
        },
        "footprint": True
    }
})

# Output:
# 2025-10-24 14:30:45 - INFO - {'log_type': 'info', 'controller': 'payment.process', ...}
```

### Multi-Handler Configuration

```python
import logging
from logging.handlers import RotatingFileHandler
from dtpyfw.log.formatter import CustomFormatter

# Create single formatter instance (can be reused)
formatter = CustomFormatter()

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# File handler
file_handler = RotatingFileHandler(
    "app.log",
    maxBytes=5*1024*1024,
    backupCount=3
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Error file handler
error_handler = RotatingFileHandler(
    "errors.log",
    maxBytes=5*1024*1024,
    backupCount=3
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.addHandler(error_handler)

# All handlers use the same formatter
logger.debug("Debug - only console")
logger.info("Info - console and app.log")
logger.error("Error - all three handlers")
```

### Integration with dtpyfw LogConfig

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer
import logging

# Configure logging system (CustomFormatter is used automatically)
config = LogConfig()
config.set_log_level("DEBUG") \
      .set_log_print("true") \
      .set_log_store("true") \
      .set_log_file_name("myapp.log")

# Initialize (CustomFormatter is applied to all handlers)
log_initializer(config)

# Use logging normally
logger = logging.getLogger(__name__)
logger.info("Standard message")
logger.info("Structured message", extra={
    "details": {"controller": "mymodule", "subject": "Event"}
})
```

### Using with Footprint Logging

```python
import logging
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer
from dtpyfw.log.footprint import leave

# Setup logging (CustomFormatter is configured automatically)
config = LogConfig()
config.set_log_level("INFO").set_log_print("true")
log_initializer(config)

# Create footprint log (automatically formatted with CustomFormatter)
leave(
    log_type="warning",
    controller="inventory.check_stock",
    subject="Low Stock Warning",
    message="Product inventory is running low",
    payload={"product_id": "prod_789", "current_stock": 5}
)

# Output (formatted by CustomFormatter):
# 2025-10-24 14:30:45 - WARNING - {'footprint': True, 'retention_days': 90, ...}
```

### Custom Handler with CustomFormatter

```python
import logging
from dtpyfw.log.formatter import CustomFormatter
from dtpyfw.log.api_handler import LoggerHandler

# Create formatter
formatter = CustomFormatter()

# API handler with formatter
api_handler = LoggerHandler(
    logging_api_url="https://logs.example.com/api/logs",
    logging_api_key="my-api-key",
    only_footprint_mode=True
)
api_handler.setLevel(logging.INFO)
api_handler.setFormatter(formatter)

# Console handler with same formatter
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(api_handler)
logger.addHandler(console_handler)

# Both handlers use CustomFormatter
logger.info("Event occurred", extra={
    "details": {
        "footprint": True,
        "controller": "app.event_handler",
        "subject": "Important Event"
    }
})
```

## Format Output Examples

### Standard Log Format

**Input:**
```python
logger.info("User logged in successfully")
```

**Output:**
```
2025-10-24 14:30:45 - INFO - User logged in successfully
```

### Structured Log Format

**Input:**
```python
logger.info("Payment processed", extra={
    "details": {
        "log_type": "info",
        "controller": "payment.process",
        "subject": "Payment Complete",
        "message": "Payment of $99.99 processed",
        "footprint": True,
        "payload": {"transaction_id": "txn_12345"}
    }
})
```

**Output:**
```
2025-10-24 14:30:45 - INFO - {'log_type': 'info', 'controller': 'payment.process', 'subject': 'Payment Complete', 'message': 'Payment of $99.99 processed', 'footprint': True, 'payload': {'transaction_id': 'txn_12345'}}
```

### Different Log Levels

**Input:**
```python
logger.debug("Debugging info")
logger.info("Information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")
```

**Output:**
```
2025-10-24 14:30:45 - DEBUG - Debugging info
2025-10-24 14:30:45 - INFO - Information
2025-10-24 14:30:45 - WARNING - Warning message
2025-10-24 14:30:45 - ERROR - Error occurred
2025-10-24 14:30:45 - CRITICAL - Critical failure
```

## Technical Details

### Dynamic Format String

The formatter dynamically switches between two format strings:

**With Details:**
```python
"%(asctime)s - %(levelname)s - %(details)s"
```

**Without Details:**
```python
"%(asctime)s - %(levelname)s - %(message)s"
```

### How It Works

```python
def format(self, record: logging.LogRecord) -> str:
    if hasattr(record, "details"):
        # Use details format
        self._style._fmt = "%(asctime)s - %(levelname)s - %(details)s"
    else:
        # Use standard message format
        self._style._fmt = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Call parent formatter
    return super().format(record)
```

### Adding Details to Log Records

Details are added to log records using the `extra` parameter:

```python
logger.info("Message text", extra={
    "details": {
        "key": "value",
        # ... more fields
    }
})
```

The `details` dictionary becomes an attribute of the `LogRecord` object, which the formatter can then access and display.

## Best Practices

1. **Reuse Formatter Instances**: Create one formatter instance and share it across multiple handlers:
   ```python
   formatter = CustomFormatter()
   handler1.setFormatter(formatter)
   handler2.setFormatter(formatter)
   ```

2. **Consistent Structured Logging**: When using structured logging, maintain consistent field names in your `details` dictionaries:
   ```python
   # Good - consistent structure
   logger.info("Event", extra={"details": {
       "controller": "module.function",
       "subject": "Event Subject",
       "payload": {...}
   }})
   ```

3. **Use with Footprint System**: The formatter works best with the `footprint.leave()` function which automatically creates properly structured logs.

4. **Standard Logging for Simple Cases**: Use standard logging (without `extra`) for simple, unstructured messages:
   ```python
   logger.debug("Simple debug message")  # No need for extra parameter
   ```

5. **Structured Logging for Important Events**: Use structured logging for important events that need to be tracked, analyzed, or sent to remote APIs:
   ```python
   logger.error("Critical error", extra={
       "details": {
           "footprint": True,
           "controller": "critical.function",
           "error_code": "ERR_001"
       }
   })
   ```

## Integration Points

### Works With

- **LogConfig**: Automatically applied by `log_initializer()`
- **LoggerHandler**: Used for formatting API-bound logs
- **RotatingFileHandler**: Standard Python handler for file rotation
- **StreamHandler**: Standard Python handler for console output
- **Footprint System**: Formats footprint logs created with `leave()`

### Compatible Handlers

The `CustomFormatter` works with any Python logging handler:

- `logging.StreamHandler` - Console output
- `logging.FileHandler` - Simple file output
- `logging.handlers.RotatingFileHandler` - File with rotation
- `logging.handlers.TimedRotatingFileHandler` - Time-based rotation
- `dtpyfw.log.api_handler.LoggerHandler` - Remote API logging
- Custom handlers extending `logging.Handler`

## Troubleshooting

### Details Not Displaying

**Problem:** Details dictionary not showing in log output

**Solution:** Ensure you're using the `extra` parameter correctly:
```python
# Wrong
logger.info({"details": {...}})

# Correct
logger.info("Message", extra={"details": {...}})
```

### Timestamp Format

**Problem:** Need different timestamp format

**Solution:** Subclass `CustomFormatter` and override the date format:
```python
class MyFormatter(CustomFormatter):
    def __init__(self):
        super().__init__()
        self.datefmt = "%Y/%m/%d %I:%M:%S %p"  # Custom format
```

### Dictionary String Representation

The formatter uses Python's default dictionary string representation. For JSON output, consider creating a custom formatter:

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, "details"):
            record.details = json.dumps(record.details)
        return super().format(record)
```

## See Also

- [Config Documentation](./config.md) - For `LogConfig` class
- [Initializer Documentation](./initializer.md) - For `log_initializer()` which applies this formatter
- [API Handler Documentation](./api_handler.md) - For remote API logging that uses this formatter
- [Footprint Documentation](./footprint.md) - For creating structured logs that work with this formatter
- [Handlers Documentation](./handlers.md) - For understanding handler configuration
