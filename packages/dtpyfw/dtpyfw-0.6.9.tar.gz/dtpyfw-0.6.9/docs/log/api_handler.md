# API Handler

## Overview

The `api_handler` module provides classes for sending log records to remote API endpoints. It includes a retry mechanism for handling transient network failures and integrates seamlessly with Python's standard logging framework. This module is essential for centralized logging infrastructure where logs need to be aggregated from multiple services.

## Module Location

```python
from dtpyfw.log.api_handler import Logger, LoggerHandler
```

## Classes

### `Logger`

A client class responsible for sending log records to a remote API endpoint via HTTP POST requests.

#### Constructor

##### `__init__(logging_api_url: str, logging_api_key: str) -> None`

Initializes the Logger client with API endpoint and authentication credentials.

**Parameters:**

- `logging_api_url` (str): The URL of the remote logging API endpoint.
- `logging_api_key` (str): The API key for authenticating with the logging API.

**Attributes:**

- `api_url` (str): Stores the logging API endpoint URL.
- `api_key` (str): Stores the authentication key.
- `headers` (dict): Pre-configured HTTP headers including Authorization and Content-Type.

**Example:**

```python
from dtpyfw.log.api_handler import Logger

logger = Logger(
    logging_api_url="https://logs.example.com/api/v1/logs",
    logging_api_key="secret-api-key-12345"
)
```

#### Methods

##### `log(details: dict[str, Any]) -> bool | None`

Sends a log entry to the remote API with automatic retry logic for handling transient failures.

**Parameters:**

- `details` (dict[str, Any]): A dictionary containing the log data to be sent to the API. This typically includes fields like `log_type`, `controller`, `subject`, `message`, `payload`, etc.

**Returns:**

- `bool | None`: Returns `True` if the log was successfully sent, `None` if all retry attempts failed.

**Retry Mechanism:**

- Maximum retries: 5 attempts
- Backoff duration: 3 seconds between attempts
- On final failure: Logs a warning using the footprint system

**Example:**

```python
from dtpyfw.log.api_handler import Logger

logger = Logger(
    logging_api_url="https://logs.example.com/api/v1/logs",
    logging_api_key="my-api-key"
)

log_details = {
    "log_type": "info",
    "controller": "user_service.create_user",
    "subject": "User Created",
    "message": "New user registered successfully",
    "payload": {"user_id": "12345", "email": "user@example.com"}
}

success = logger.log(details=log_details)
if success:
    print("Log sent successfully")
else:
    print("Failed to send log after all retries")
```

**Error Handling:**

The method catches `requests.exceptions.RequestException` which includes:
- Connection errors
- Timeout errors
- HTTP errors (4xx, 5xx status codes)
- Invalid URL errors

If all retry attempts fail, a warning is logged locally using the `footprint.leave()` function with details about the failure.

---

### `LoggerHandler`

A logging handler that integrates with Python's `logging` module to forward log records to a remote API endpoint.

#### Inheritance

Inherits from `logging.Handler`

#### Constructor

##### `__init__(logging_api_url: str, logging_api_key: str, only_footprint_mode: bool) -> None`

Initializes the LoggerHandler with API configuration and filtering options.

**Parameters:**

- `logging_api_url` (str): The URL of the remote logging API endpoint.
- `logging_api_key` (str): The API key for authenticating with the logging API.
- `only_footprint_mode` (bool): If `True`, only logs marked with `footprint=True` will be sent to the API.

**Attributes:**

- `only_footprint_mode` (bool): Determines whether to filter non-footprint logs.
- `logger` (Logger): The Logger instance used to send logs to the API.

**Example:**

```python
from dtpyfw.log.api_handler import LoggerHandler
import logging

# Create handler
api_handler = LoggerHandler(
    logging_api_url="https://logs.example.com/api/v1/logs",
    logging_api_key="secret-key",
    only_footprint_mode=True
)

# Configure handler
api_handler.setLevel(logging.INFO)

# Add to logger
logger = logging.getLogger()
logger.addHandler(api_handler)
```

#### Methods

##### `emit(record: logging.LogRecord) -> None`

Processes a log record and sends it to the remote API.

This method is called automatically by Python's logging framework when a log record needs to be handled. It extracts details from the log record, formats them, and uses the Logger client to send the log to the remote API.

**Parameters:**

- `record` (logging.LogRecord): The log record to be emitted to the remote API.

**Returns:**

- `None`

**Behavior:**

1. Extracts the `details` dictionary from the log record (if present).
2. If `only_footprint_mode` is enabled and the log is not marked as a footprint, the method returns early without sending.
3. Populates default values for required fields:
   - `log_type`: Defaults to the record's level name (e.g., "INFO", "ERROR") in lowercase
   - `subject`: Defaults to "Unnamed" if not provided
   - `controller`: Defaults to the function name from the log record
   - `message`: Defaults to the formatted log message
4. Calls the Logger's `log()` method to send the data to the API.

**Example:**

```python
import logging
from dtpyfw.log.api_handler import LoggerHandler

# Setup handler
api_handler = LoggerHandler(
    logging_api_url="https://logs.example.com/api/logs",
    logging_api_key="my-key",
    only_footprint_mode=False
)

# Configure logging
logger = logging.getLogger()
logger.addHandler(api_handler)
logger.setLevel(logging.INFO)

# This log will be sent to the API
logger.info("Application started", extra={
    "details": {
        "controller": "main.startup",
        "subject": "Startup",
        "footprint": True,
        "payload": {"version": "1.0.0"}
    }
})
```

## Complete Usage Examples

### Basic API Logging Setup

```python
import logging
from dtpyfw.log.api_handler import LoggerHandler
from dtpyfw.log.formatter import CustomFormatter

# Create and configure the API handler
api_handler = LoggerHandler(
    logging_api_url="https://logs.mycompany.com/api/v1/logs",
    logging_api_key="prod-api-key-xyz",
    only_footprint_mode=True
)

# Set log level and formatter
api_handler.setLevel(logging.INFO)
formatter = CustomFormatter()
api_handler.setFormatter(formatter)

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(api_handler)

# Send a log (won't be sent because footprint=False by default)
logger.info("This won't be sent to API")

# Send a footprint log (will be sent to API)
logger.info("Important event", extra={
    "details": {
        "footprint": True,
        "controller": "payment.process",
        "subject": "Payment Processed",
        "message": "Payment completed successfully",
        "payload": {"amount": 100.00, "currency": "USD"}
    }
})
```

### Using with LogConfig and Initializer

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer
import logging

# Configure logging system
config = LogConfig()
config.set_api_url("https://logs.example.com/api/logs") \
      .set_api_key("my-secret-key") \
      .set_log_level("INFO") \
      .set_only_footprint_mode(True) \
      .set_log_print("true")

# Initialize (this creates and configures the LoggerHandler automatically)
log_initializer(config)

# Use standard logging
logger = logging.getLogger(__name__)
logger.info("Standard log - not sent to API")

# Use footprint for important logs
from dtpyfw.log.footprint import leave

leave(
    log_type="info",
    controller="user_service.register",
    subject="User Registration",
    message="New user registered",
    payload={"user_id": "usr_12345", "email": "user@example.com"}
)
```

### Direct Logger Usage (Without Logging Framework)

```python
from dtpyfw.log.api_handler import Logger

# Create logger client
logger = Logger(
    logging_api_url="https://logs.example.com/api/logs",
    logging_api_key="my-api-key"
)

# Send log directly
log_data = {
    "log_type": "error",
    "controller": "payment_processor.charge_card",
    "subject": "Payment Failed",
    "message": "Credit card was declined",
    "retention_days": 90,
    "dealer_id": "550e8400-e29b-41d4-a716-446655440000",
    "payload": {
        "transaction_id": "txn_12345",
        "amount": 99.99,
        "error_code": "card_declined"
    }
}

success = logger.log(details=log_data)
if not success:
    print("Failed to send log to remote API")
```

### Multi-Handler Configuration

```python
import logging
from logging.handlers import RotatingFileHandler
from dtpyfw.log.api_handler import LoggerHandler
from dtpyfw.log.formatter import CustomFormatter

# Create formatter
formatter = CustomFormatter()

# API handler (only footprints)
api_handler = LoggerHandler(
    logging_api_url="https://logs.example.com/api/logs",
    logging_api_key="api-key",
    only_footprint_mode=True
)
api_handler.setLevel(logging.INFO)
api_handler.setFormatter(formatter)

# Console handler (all logs)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# File handler (all logs)
file_handler = RotatingFileHandler(
    "application.log",
    maxBytes=10*1024*1024,
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(api_handler)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# All handlers receive this log
logger.debug("Debug message - console and file only")

# Only API handler receives this (if footprint=True)
logger.error("Critical error", extra={
    "details": {
        "footprint": True,
        "controller": "database.connection",
        "subject": "Database Connection Failed"
    }
})
```

### Filtering with only_footprint_mode

```python
import logging
from dtpyfw.log.api_handler import LoggerHandler

# Handler with footprint filtering enabled
handler = LoggerHandler(
    logging_api_url="https://logs.example.com/api/logs",
    logging_api_key="key",
    only_footprint_mode=True  # Only send footprints
)

logger = logging.getLogger()
logger.addHandler(handler)

# NOT sent to API (no details)
logger.info("Simple log message")

# NOT sent to API (footprint=False)
logger.info("Message", extra={
    "details": {"footprint": False}
})

# SENT to API (footprint=True)
logger.info("Message", extra={
    "details": {
        "footprint": True,
        "controller": "myapp.function",
        "subject": "Important Event"
    }
})

# Disable filtering to send all logs
handler.only_footprint_mode = False

# Now this WILL be sent to API
logger.info("Another message")
```

## Integration with Footprint System

The API handler is designed to work seamlessly with the footprint logging system:

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer
from dtpyfw.log.footprint import leave
from uuid import uuid4

# Setup logging with API handler
config = LogConfig()
config.set_api_url("https://logs.example.com/api/logs") \
      .set_api_key("my-key") \
      .set_only_footprint_mode(True)

log_initializer(config)

# Create footprint log (automatically sent to API)
leave(
    log_type="warning",
    controller="inventory.stock_check",
    retention_days=30,
    subject="Low Stock Alert",
    message="Product stock is below minimum threshold",
    dealer_id=uuid4(),
    payload={
        "product_id": "prod_789",
        "current_stock": 5,
        "minimum_stock": 10
    },
    footprint=True  # This will be sent to API
)
```

## Error Handling and Retry Logic

### Retry Behavior

The `Logger.log()` method implements automatic retry logic:

```python
# Pseudo-code representation of retry logic
max_retries = 5
backoff_seconds = 3

for attempt in range(1, max_retries + 1):
    try:
        response = requests.post(url, data, headers)
        response.raise_for_status()
        return True  # Success
    except RequestException:
        if attempt < max_retries:
            sleep(3)  # Wait before retry
        else:
            # Log warning locally after all retries fail
            footprint.leave(
                log_type="warning",
                controller="Logger.log",
                subject="Log Sending Error",
                message=f"Failed to send log to API: {error}"
            )
return None  # All retries failed
```

### Handling Network Issues

```python
from dtpyfw.log.api_handler import Logger
import logging

# Configure with unreachable API (for testing)
logger = Logger(
    logging_api_url="https://unreachable-api.example.com/logs",
    logging_api_key="key"
)

# This will retry 5 times with 3-second delays
# Total wait time: 12 seconds (3s * 4 retries)
result = logger.log({"message": "test"})

if result is None:
    logging.warning("Failed to send log after 5 attempts")
```

## Best Practices

1. **Use only_footprint_mode for Production**: Enable footprint filtering to reduce API traffic and costs:
   ```python
   handler = LoggerHandler(
       logging_api_url=api_url,
       logging_api_key=api_key,
       only_footprint_mode=True  # Recommended for production
   )
   ```

2. **Set Appropriate Log Levels**: Configure handlers with appropriate log levels:
   ```python
   api_handler.setLevel(logging.WARNING)  # Only send warnings and above to API
   ```

3. **Use with LogConfig**: Prefer using `LogConfig` and `log_initializer()` for easier configuration management.

4. **Include Structured Details**: Always include structured details in important logs:
   ```python
   logger.error("Payment failed", extra={
       "details": {
           "footprint": True,
           "controller": "payment.process",
           "subject": "Payment Processing Error",
           "payload": {"transaction_id": "txn_123", "error": "declined"}
       }
   })
   ```

5. **Monitor API Failures**: The handler logs warnings locally when API calls fail after retries. Monitor these warnings to detect connectivity issues.

6. **API Key Security**: Never hardcode API keys. Use environment variables or secure configuration management:
   ```python
   import os
   
   api_key = os.environ.get("LOG_API_KEY")
   if not api_key:
       raise ValueError("LOG_API_KEY environment variable not set")
   
   handler = LoggerHandler(
       logging_api_url="https://logs.example.com/api/logs",
       logging_api_key=api_key,
       only_footprint_mode=True
   )
   ```

## API Request Format

The Logger sends HTTP POST requests with the following format:

**Headers:**
```
Authorization: <api_key>
Content-Type: application/json
```

**Body:**
```json
{
    "log_type": "info",
    "controller": "module.function",
    "subject": "Event Subject",
    "message": "Detailed message",
    "retention_days": 90,
    "dealer_id": "uuid-string",
    "user_id": "uuid-string",
    "payload": {
        "custom": "data",
        "any": "structure"
    },
    "footprint": true
}
```

All datetime objects and other non-JSON-serializable types are converted to strings using `json.dumps(details, default=str)`.

## Performance Considerations

1. **Non-Blocking**: The handler processes logs synchronously. For high-throughput applications, consider using the handler with a `QueueHandler` to avoid blocking the main thread.

2. **Retry Impact**: Each failed log can take up to 12 seconds (3s × 4 retries) before giving up. This can impact application responsiveness if many logs fail.

3. **Network Latency**: Each API call incurs network latency. Use `only_footprint_mode=True` to minimize the number of API calls.

## Troubleshooting

### Logs Not Appearing in Remote API

1. **Check footprint mode**: Ensure `only_footprint_mode=False` or logs have `footprint=True`
2. **Verify API credentials**: Confirm the API URL and key are correct
3. **Check log level**: Ensure the handler's log level allows the message through
4. **Review local warnings**: Failed API calls generate local warning logs

### Connection Timeouts

The handler uses default `requests` timeout settings. For slow networks, you may need to modify the `Logger.log()` method to include timeout parameters.

## See Also

- [Config Documentation](./config.md) - For `LogConfig` class
- [Initializer Documentation](./initializer.md) - For `log_initializer()` function
- [Footprint Documentation](./footprint.md) - For creating structured footprint logs
- [Formatter Documentation](./formatter.md) - For `CustomFormatter` class
- [Handlers Documentation](./handlers.md) - For understanding handler configuration
