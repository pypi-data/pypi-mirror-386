# Footprint

## Overview

The `footprint` module provides the `leave()` function, which is a high-level utility for creating structured log entries with detailed metadata. It simplifies the process of creating comprehensive, structured logs by packaging various pieces of information (controller, subject, message, payload, etc.) into a single function call. These "footprint" logs are designed to be processed by handlers that understand structured logging.

## Module Location

```python
from dtpyfw.log.footprint import leave
```

## Functions

### `leave(...) -> None`

Creates a structured log entry with detailed metadata and automatically routes it through the logging system.

#### Full Signature

```python
def leave(
    log_type: str = "info",
    controller: str = "not_specified",
    retention_days: int = 90,
    subject: str = "not_specified",
    message: str = "no_message",
    dealer_id: UUID | None = None,
    user_id: UUID | None = None,
    payload: Any | None = None,
    footprint: bool = True,
) -> None
```

#### Parameters

- **`log_type`** (str, optional): The severity/type of the log. Defaults to `"info"`.
  - Valid values: `"debug"`, `"info"`, `"warning"`, `"error"`, `"critical"`
  - Determines which logging method is called (logger.info, logger.error, etc.)

- **`controller`** (str, optional): The component, module, or function where the log originates. Defaults to `"not_specified"`.
  - Convention: Use dot notation like `"module.class.method"` or `"service.function"`
  - Examples: `"payment.process_card"`, `"user_service.create_user"`

- **`retention_days`** (int, optional): The desired retention period for the log in days. Defaults to `90`.
  - Used by log management systems to determine how long to keep the log
  - Examples: 30 for short-term logs, 365 for long-term audit logs

- **`subject`** (str, optional): A brief summary or title of the log entry. Defaults to `"not_specified"`.
  - Should be concise and descriptive
  - Examples: `"User Registration"`, `"Payment Failed"`, `"Database Connection Error"`

- **`message`** (str, optional): The main log message content providing detailed information. Defaults to `"no_message"`.
  - Can be a detailed description of the event
  - Examples: `"User successfully registered with email verification"`, `"Payment gateway returned error code 401"`

- **`dealer_id`** (UUID | None, optional): The UUID of the associated dealer, if applicable. Defaults to `None`.
  - Used in multi-tenant systems to track which dealer/tenant the log relates to
  - Must be a UUID object or None

- **`user_id`** (UUID | None, optional): The UUID of the associated user, if applicable. Defaults to `None`.
  - Tracks which user triggered or is related to the logged event
  - Must be a UUID object or None

- **`payload`** (Any | None, optional): Additional data to include with the log. Defaults to `None`.
  - Can be any JSON-serializable data structure (dict, list, string, etc.)
  - Typically used for contextual data, error details, or structured information
  - Examples: `{"transaction_id": "txn_123", "amount": 99.99}`, `{"error_code": "E001"}`

- **`footprint`** (bool, optional): A flag to mark this log as a 'footprint' for filtering. Defaults to `True`.
  - When `True`, logs are sent to API handlers configured with `only_footprint_mode=True`
  - When `False`, logs are only processed by console and file handlers
  - Typically keep as `True` for important, structured logs

#### Returns

- `None`: The function doesn't return a value; it creates a log entry.

#### Behavior

1. Creates a structured dictionary (`kwargs`) with all provided parameters
2. Packages the data into the logging system's `extra` parameter format
3. Determines the appropriate logging method based on `log_type`:
   - `"critical"` → `logger.critical()`
   - `"error"` → `logger.error()`
   - `"warning"` → `logger.warning()`
   - `"debug"` → `logger.debug()`
   - All others → `logger.info()`
4. Calls the logging method with the structured data

## Usage Examples

### Basic Usage

```python
from dtpyfw.log.footprint import leave

# Simple info log
leave(
    log_type="info",
    controller="app.startup",
    subject="Application Started",
    message="Application initialized successfully"
)
```

### Complete Example with All Parameters

```python
from dtpyfw.log.footprint import leave
from uuid import UUID

leave(
    log_type="error",
    controller="payment.process_credit_card",
    retention_days=365,
    subject="Payment Processing Failed",
    message="Credit card payment was declined by the payment gateway",
    dealer_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    user_id=UUID("7c9e6679-7425-40de-944b-e07fc1f90ae7"),
    payload={
        "transaction_id": "txn_12345",
        "amount": 99.99,
        "currency": "USD",
        "error_code": "card_declined",
        "gateway_response": "Insufficient funds"
    },
    footprint=True
)
```

### Different Log Types

```python
from dtpyfw.log.footprint import leave

# Debug log
leave(
    log_type="debug",
    controller="data_processor.validate_input",
    subject="Input Validation",
    message="Validating user input data",
    payload={"fields": ["email", "password", "name"]}
)

# Info log
leave(
    log_type="info",
    controller="user_service.register",
    subject="User Registration",
    message="New user registered successfully",
    payload={"user_id": "usr_123", "email": "user@example.com"}
)

# Warning log
leave(
    log_type="warning",
    controller="inventory.check_stock",
    subject="Low Stock Warning",
    message="Product inventory is below minimum threshold",
    payload={"product_id": "prod_789", "current_stock": 5, "min_stock": 10}
)

# Error log
leave(
    log_type="error",
    controller="database.connection",
    subject="Database Connection Failed",
    message="Unable to establish connection to database",
    payload={"host": "db.example.com", "port": 5432, "error": "Connection timeout"}
)

# Critical log
leave(
    log_type="critical",
    controller="system.security",
    subject="Security Breach Detected",
    message="Multiple failed authentication attempts detected",
    payload={"ip_address": "192.168.1.100", "attempts": 10, "timeframe": "5 minutes"}
)
```

### User and Dealer Tracking

```python
from dtpyfw.log.footprint import leave
from uuid import uuid4

dealer_id = uuid4()
user_id = uuid4()

# Track user actions
leave(
    log_type="info",
    controller="order.create",
    subject="Order Created",
    message="New order placed by customer",
    dealer_id=dealer_id,
    user_id=user_id,
    payload={
        "order_id": "ord_456",
        "total_amount": 249.99,
        "items_count": 3
    }
)

# Track dealer-specific events
leave(
    log_type="info",
    controller="dealer.settings_update",
    subject="Dealer Settings Updated",
    message="Dealer updated notification preferences",
    dealer_id=dealer_id,
    payload={
        "changed_settings": ["email_notifications", "sms_alerts"],
        "new_values": {"email_notifications": True, "sms_alerts": False}
    }
)
```

### Custom Retention Periods

```python
from dtpyfw.log.footprint import leave

# Short-term operational log (30 days)
leave(
    log_type="debug",
    controller="cache.cleanup",
    retention_days=30,
    subject="Cache Cleanup",
    message="Routine cache cleanup completed"
)

# Standard log (90 days - default)
leave(
    log_type="info",
    controller="api.request",
    retention_days=90,
    subject="API Request",
    message="API endpoint called successfully"
)

# Long-term audit log (365 days)
leave(
    log_type="info",
    controller="admin.user_delete",
    retention_days=365,
    subject="User Account Deleted",
    message="Administrator deleted user account",
    payload={"deleted_user_id": "usr_789", "admin_id": "usr_001", "reason": "User request"}
)

# Compliance log (2555 days ≈ 7 years)
leave(
    log_type="info",
    controller="payment.transaction",
    retention_days=2555,
    subject="Payment Transaction",
    message="Payment transaction completed",
    payload={"transaction_id": "txn_999", "amount": 1000.00}
)
```

### Complex Payload Examples

```python
from dtpyfw.log.footprint import leave

# Nested dictionary payload
leave(
    log_type="info",
    controller="api.response",
    subject="API Response",
    message="External API call completed",
    payload={
        "endpoint": "https://api.external.com/data",
        "method": "POST",
        "status_code": 200,
        "response_time_ms": 342,
        "request_headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer ***"
        },
        "response_data": {
            "success": True,
            "record_count": 150
        }
    }
)

# List payload
leave(
    log_type="info",
    controller="batch.process",
    subject="Batch Processing Complete",
    message="Batch job processed multiple items",
    payload={
        "batch_id": "batch_001",
        "processed_items": ["item_1", "item_2", "item_3", "item_4"],
        "failed_items": ["item_5"],
        "success_rate": 0.8
    }
)

# Error details payload
leave(
    log_type="error",
    controller="file_processor.parse",
    subject="File Parsing Error",
    message="Failed to parse uploaded file",
    payload={
        "filename": "data.csv",
        "file_size_bytes": 1048576,
        "error_line": 42,
        "error_message": "Invalid CSV format",
        "stack_trace": "..."  # Could include stack trace
    }
)
```

### Non-Footprint Logs

```python
from dtpyfw.log.footprint import leave

# Regular log that won't be sent to API (footprint=False)
leave(
    log_type="debug",
    controller="internal.debug",
    subject="Debug Information",
    message="Internal debugging information",
    payload={"debug_data": "sensitive local information"},
    footprint=False  # Won't be sent to API handlers
)

# Footprint log that WILL be sent to API (footprint=True)
leave(
    log_type="info",
    controller="important.event",
    subject="Important Event",
    message="Important event occurred",
    payload={"event_id": "evt_123"},
    footprint=True  # Will be sent to API handlers
)
```

### Integration with Try-Except Blocks

```python
from dtpyfw.log.footprint import leave
import traceback

def process_payment(amount: float, card_number: str):
    try:
        # Payment processing logic
        result = charge_card(amount, card_number)
        
        # Success footprint
        leave(
            log_type="info",
            controller="payment.process_payment",
            subject="Payment Successful",
            message=f"Payment of ${amount} processed successfully",
            payload={
                "amount": amount,
                "transaction_id": result.transaction_id,
                "card_last_four": card_number[-4:]
            }
        )
        return result
        
    except PaymentError as e:
        # Error footprint
        leave(
            log_type="error",
            controller="payment.process_payment",
            subject="Payment Failed",
            message=f"Payment processing failed: {str(e)}",
            payload={
                "amount": amount,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "card_last_four": card_number[-4:]
            }
        )
        raise
        
    except Exception as e:
        # Critical error footprint
        leave(
            log_type="critical",
            controller="payment.process_payment",
            subject="Unexpected Payment Error",
            message="Unexpected error during payment processing",
            payload={
                "amount": amount,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
        )
        raise
```

### Function Decorator Pattern

```python
from dtpyfw.log.footprint import leave
from functools import wraps
import time

def log_execution(controller: str):
    """Decorator to log function execution with footprints."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log function start
            leave(
                log_type="debug",
                controller=controller,
                subject=f"{func.__name__} Started",
                message=f"Function {func.__name__} execution started",
                payload={"args": str(args), "kwargs": str(kwargs)}
            )
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log success
                leave(
                    log_type="info",
                    controller=controller,
                    subject=f"{func.__name__} Completed",
                    message=f"Function {func.__name__} executed successfully",
                    payload={
                        "execution_time_seconds": execution_time,
                        "result_type": type(result).__name__
                    }
                )
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log error
                leave(
                    log_type="error",
                    controller=controller,
                    subject=f"{func.__name__} Failed",
                    message=f"Function {func.__name__} raised an exception",
                    payload={
                        "execution_time_seconds": execution_time,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise
        
        return wrapper
    return decorator

# Usage
@log_execution("data.process_records")
def process_records(records: list):
    # Processing logic
    return len(records)

# Automatically logs start, completion, and any errors
result = process_records([1, 2, 3, 4, 5])
```

### Context Manager Pattern

```python
from dtpyfw.log.footprint import leave
from contextlib import contextmanager
import time

@contextmanager
def log_operation(controller: str, subject: str):
    """Context manager to log operation start and end."""
    start_time = time.time()
    
    leave(
        log_type="info",
        controller=controller,
        subject=f"{subject} Started",
        message=f"Operation started: {subject}"
    )
    
    try:
        yield
        
        execution_time = time.time() - start_time
        leave(
            log_type="info",
            controller=controller,
            subject=f"{subject} Completed",
            message=f"Operation completed successfully: {subject}",
            payload={"execution_time_seconds": execution_time}
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        leave(
            log_type="error",
            controller=controller,
            subject=f"{subject} Failed",
            message=f"Operation failed: {subject}",
            payload={
                "execution_time_seconds": execution_time,
                "error": str(e)
            }
        )
        raise

# Usage
with log_operation("database.migration", "Database Migration"):
    # Migration logic
    migrate_database()
```

## Log Type Mapping

The `log_type` parameter determines which logging method is called:

| log_type | Logging Method | Log Level | Use Case |
|----------|----------------|-----------|----------|
| "critical" | `logger.critical()` | CRITICAL (50) | System failures, security issues |
| "error" | `logger.error()` | ERROR (40) | Errors that need attention |
| "warning" | `logger.warning()` | WARNING (30) | Warnings, potential issues |
| "debug" | `logger.debug()` | DEBUG (10) | Detailed diagnostic information |
| "info" (default) | `logger.info()` | INFO (20) | General informational messages |
| Any other string | `logger.info()` | INFO (20) | Defaults to info level |

## Generated Log Structure

The `leave()` function creates logs with the following structure:

```python
{
    "msg": message,  # The message parameter
    "extra": {
        "details": {
            "footprint": footprint,
            "retention_days": retention_days,
            "log_type": log_type,
            "controller": controller,
            "subject": subject,
            "message": message,
            "dealer_id": dealer_id,
            "user_id": user_id,
            "payload": payload
        }
    }
}
```

This structure is what handlers like `LoggerHandler` and formatters like `CustomFormatter` process.

## Best Practices

1. **Use Meaningful Controllers**: Follow a consistent naming convention for controllers:
   ```python
   # Good
   leave(controller="user_service.create_user", ...)
   leave(controller="payment.process_card", ...)
   leave(controller="api.v1.orders.create", ...)
   
   # Avoid
   leave(controller="main", ...)
   leave(controller="function1", ...)
   ```

2. **Descriptive Subjects**: Keep subjects concise but descriptive:
   ```python
   # Good
   leave(subject="User Registration Successful", ...)
   leave(subject="Payment Failed - Declined Card", ...)
   
   # Avoid
   leave(subject="Success", ...)
   leave(subject="Error", ...)
   ```

3. **Structured Payloads**: Use dictionaries for payload data:
   ```python
   # Good
   leave(payload={
       "transaction_id": "txn_123",
       "amount": 99.99,
       "currency": "USD"
   }, ...)
   
   # Less useful
   leave(payload="transaction_id: txn_123, amount: 99.99", ...)
   ```

4. **Appropriate Log Types**: Choose the correct log type for the situation:
   ```python
   # Critical: System-level failures
   leave(log_type="critical", subject="Database Server Down", ...)
   
   # Error: Application errors that need attention
   leave(log_type="error", subject="Payment Processing Failed", ...)
   
   # Warning: Potential issues or degraded performance
   leave(log_type="warning", subject="API Response Time Slow", ...)
   
   # Info: Important operational events
   leave(log_type="info", subject="User Login Successful", ...)
   
   # Debug: Detailed diagnostic information
   leave(log_type="debug", subject="Cache Hit", ...)
   ```

5. **Retention Policies**: Set appropriate retention periods:
   ```python
   # Short-term operational logs
   leave(retention_days=30, ...)
   
   # Standard business logs
   leave(retention_days=90, ...)  # Default
   
   # Audit/compliance logs
   leave(retention_days=365, ...)  # Or longer
   ```

6. **Use footprint=True for Important Logs**: Keep the default `footprint=True` for logs you want sent to remote APIs:
   ```python
   # Important business event - send to API
   leave(footprint=True, subject="Order Completed", ...)
   
   # Internal debug info - local only
   leave(footprint=False, log_type="debug", subject="Cache Debug", ...)
   ```

7. **Sanitize Sensitive Data**: Never log sensitive information like passwords or full credit card numbers:
   ```python
   # Good
   leave(payload={
       "card_last_four": card_number[-4:],
       "user_email": email
   }, ...)
   
   # Bad - never do this
   leave(payload={
       "card_number": card_number,
       "password": password
   }, ...)
   ```

## Integration with Logging System

The `leave()` function integrates seamlessly with the dtpyfw logging system:

```python
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer
from dtpyfw.log.footprint import leave

# Setup logging
config = LogConfig()
config.set_api_url("https://logs.example.com/api/logs") \
      .set_api_key("my-api-key") \
      .set_log_level("INFO") \
      .set_log_print("true") \
      .set_only_footprint_mode(True)

log_initializer(config)

# Use footprint logging (automatically processed by all configured handlers)
leave(
    log_type="info",
    controller="app.startup",
    subject="Application Started",
    message="Application initialized successfully"
)
# This log goes to:
# - Console (if log_print is true)
# - File (if log_store is true)
# - API (if API is configured and footprint=True)
```

## Performance Considerations

1. **JSON Serialization**: The `payload` must be JSON-serializable. Complex objects will cause errors:
   ```python
   # Good
   leave(payload={"value": 123, "items": [1, 2, 3]}, ...)
   
   # Bad - will cause serialization error
   leave(payload={"object": SomeClass()}, ...)
   ```

2. **Payload Size**: Large payloads increase logging overhead. Keep payloads reasonably sized:
   ```python
   # Good - concise payload
   leave(payload={"user_id": "123", "action": "login"}, ...)
   
   # Avoid - unnecessarily large payload
   leave(payload={"entire_user_object": huge_dict_with_1000_fields}, ...)
   ```

3. **Footprint Filtering**: Use `footprint=False` for high-frequency debug logs to avoid overwhelming API endpoints:
   ```python
   # High-frequency log - don't send to API
   for item in items:
       leave(
           log_type="debug",
           subject="Processing Item",
           payload={"item_id": item.id},
           footprint=False  # Local only
       )
   ```

## Troubleshooting

### Logs Not Appearing

**Problem:** Footprint logs are not visible

**Possible Causes:**
1. Log level is set too high (e.g., WARNING, but using log_type="info")
2. No handlers configured
3. Logging system not initialized

**Solution:**
```python
# Ensure logging is initialized
from dtpyfw.log.config import LogConfig
from dtpyfw.log.initializer import log_initializer

config = LogConfig()
config.set_log_level("DEBUG").set_log_print("true")
log_initializer(config)

# Now footprint logs will appear
leave(log_type="info", subject="Test", message="Test message")
```

### Logs Not Sent to API

**Problem:** Footprint logs not appearing in remote API

**Possible Causes:**
1. `only_footprint_mode=True` but `footprint=False` in leave()
2. API configuration missing or incorrect
3. Network issues

**Solution:**
```python
# Ensure footprint=True (default)
leave(footprint=True, ...)  # Will be sent to API

# Verify API configuration
config.set_api_url("https://logs.example.com/api/logs")
config.set_api_key("valid-api-key")
```

### UUID Serialization Errors

**Problem:** Error when sending logs with UUID fields to API

**Solution:** The API handler uses `json.dumps(details, default=str)` which automatically converts UUIDs to strings. Ensure you're passing UUID objects, not strings:
```python
from uuid import UUID, uuid4

# Correct
leave(dealer_id=uuid4(), ...)  # UUID object
leave(dealer_id=UUID("550e8400-e29b-41d4-a716-446655440000"), ...)

# Also works
leave(dealer_id=None, ...)  # None is fine
```

## See Also

- [Config Documentation](./config.md) - For `LogConfig` class
- [Initializer Documentation](./initializer.md) - For `log_initializer()` function
- [API Handler Documentation](./api_handler.md) - For understanding how footprint logs are sent to APIs
- [Formatter Documentation](./formatter.md) - For understanding how footprint logs are formatted
- [Handlers Documentation](./handlers.md) - For handler configuration
