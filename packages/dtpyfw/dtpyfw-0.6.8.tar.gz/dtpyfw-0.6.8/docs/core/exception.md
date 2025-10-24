# Exception Handling

## Overview

The `dtpyfw.core.exception` module provides custom exceptions and helpers for serializing exception objects. This module is essential for consistent error handling across the DealerTower framework, particularly for HTTP request failures and API error responses.

## Module Path

```python
from dtpyfw.core.exception import RequestException, exception_to_dict
```

## Classes

### `RequestException`

Exception raised when a handled HTTP request fails.

**Description:**

Custom exception for HTTP request failures, containing status code, controller context, and optional message. Can be configured to skip footprint logging for specific use cases.

**Constructor Parameters:**

- **status_code** (`int`, optional): HTTP status code of the failed request. Defaults to 500.
- **controller** (`str | None`, optional): Name of the controller/module where the exception occurred. Defaults to None.
- **message** (`str`, optional): Human-readable description of the error. Defaults to empty string.
- **skip_footprint** (`bool`, optional): If True, prevents automatic logging to footprint system. Defaults to True.

**Attributes:**

- **status_code** (`int`): The HTTP status code.
- **controller** (`str | None`): The controller identifier.
- **message** (`str`): The error message.
- **skip_footprint** (`bool`): Whether to skip footprint logging.

**Example:**

```python
from dtpyfw.core.exception import RequestException

# Raise a custom request exception
raise RequestException(
    status_code=404,
    controller="user_service",
    message="User not found",
    skip_footprint=False
)

# Handle the exception
try:
    response = make_api_call()
except RequestException as e:
    print(f"Request failed with status {e.status_code}: {e.message}")
    print(f"Controller: {e.controller}")
```

## Functions

### `exception_to_dict(exc: Exception) -> Dict[str, Any]`

Return a serializable dictionary representing an exception.

**Description:**

Converts an exception object into a dictionary containing type, message, traceback details, and optional arguments. This is useful for logging, API responses, or storing exception information in databases.

**Parameters:**

- **exc** (`Exception`): The exception object to serialize.

**Returns:**

- **`Dict[str, Any]`**: A dictionary with keys:
  - `type` (str): Exception class name
  - `message` (str): Exception message
  - `traceback` (list): List of traceback frame dictionaries
  - `args` (tuple, optional): Exception arguments if present

**Traceback Frame Dictionary:**

Each frame in the traceback list contains:
- `filename` (str): Source file path
- `line` (int): Line number
- `function` (str): Function name
- `text` (str): Source code line

**Example:**

```python
from dtpyfw.core.exception import exception_to_dict

try:
    result = 1 / 0
except ZeroDivisionError as e:
    error_dict = exception_to_dict(e)
    print(error_dict)
    # Output:
    # {
    #     'type': 'ZeroDivisionError',
    #     'message': 'division by zero',
    #     'traceback': [
    #         {
    #             'filename': 'example.py',
    #             'line': 4,
    #             'function': '<module>',
    #             'text': 'result = 1 / 0'
    #         }
    #     ],
    #     'args': ('division by zero',)
    # }
```

## Complete Usage Examples

### 1. API Error Handling

```python
from fastapi import FastAPI, HTTPException
from dtpyfw.core.exception import RequestException, exception_to_dict
from dtpyfw.log import footprint

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    try:
        # Attempt to fetch user from external API
        user = await fetch_user_from_api(user_id)
        return user
    except RequestException as e:
        # Handle custom request exception
        if not e.skip_footprint:
            footprint.leave(
                log_type="error",
                controller=e.controller,
                message=e.message,
                subject=f"Failed to fetch user {user_id}"
            )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        # Handle unexpected exceptions
        error_data = exception_to_dict(e)
        footprint.leave(
            log_type="error",
            controller="get_user",
            message="Unexpected error",
            payload=error_data
        )
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. Service Layer Error Handling

```python
from dtpyfw.core.exception import RequestException
from dtpyfw.core.request import request

class UserService:
    def get_user_by_id(self, user_id: int) -> dict:
        """Fetch user from external service."""
        try:
            response = request(
                method="GET",
                path=f"/users/{user_id}",
                host="https://api.example.com",
                auth_key="Authorization",
                auth_value=f"Bearer {self.api_key}",
                auth_type="headers"
            )
            return response
        except RequestException as e:
            # Re-raise with additional context
            raise RequestException(
                status_code=e.status_code,
                controller="UserService.get_user_by_id",
                message=f"Failed to fetch user {user_id}: {e.message}",
                skip_footprint=False
            )

# Usage
service = UserService()
try:
    user = service.get_user_by_id(123)
except RequestException as e:
    print(f"Error: {e.message} (Status: {e.status_code})")
```

### 3. Middleware Error Logging

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from dtpyfw.core.exception import exception_to_dict, RequestException
from dtpyfw.log import footprint

class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except RequestException as e:
            # Log request exceptions
            if not e.skip_footprint:
                footprint.leave(
                    log_type="warning",
                    controller=e.controller or "unknown",
                    message=e.message,
                    subject=f"Request failed: {request.url}",
                    payload={
                        "status_code": e.status_code,
                        "method": request.method,
                        "path": str(request.url)
                    }
                )
            raise
        except Exception as e:
            # Log unexpected exceptions
            error_data = exception_to_dict(e)
            footprint.leave(
                log_type="error",
                controller="ErrorLoggingMiddleware",
                message="Unhandled exception",
                subject=f"Error processing {request.method} {request.url}",
                payload=error_data
            )
            raise
```

### 4. Database Transaction Error Handling

```python
from sqlalchemy.exc import SQLAlchemyError
from dtpyfw.core.exception import RequestException, exception_to_dict
from dtpyfw.log import footprint

def create_user(db_session, user_data: dict):
    """Create a new user with error handling."""
    try:
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        return user
    except SQLAlchemyError as e:
        db_session.rollback()
        
        # Convert to serializable format
        error_data = exception_to_dict(e)
        
        # Log the error
        footprint.leave(
            log_type="error",
            controller="create_user",
            message="Database error creating user",
            payload={
                "user_data": user_data,
                "error": error_data
            }
        )
        
        # Raise custom exception
        raise RequestException(
            status_code=500,
            controller="create_user",
            message="Failed to create user in database",
            skip_footprint=True  # Already logged above
        )
```

### 5. Async Task Error Tracking

```python
from dtpyfw.core.exception import exception_to_dict
from dtpyfw.worker import task
from dtpyfw.log import footprint

@task
def process_order(order_id: int):
    """Process an order asynchronously."""
    try:
        # Process the order
        order = fetch_order(order_id)
        validate_order(order)
        charge_payment(order)
        ship_order(order)
    except Exception as e:
        # Serialize exception for Celery result backend
        error_data = exception_to_dict(e)
        
        # Log with full context
        footprint.leave(
            log_type="error",
            controller="process_order",
            message=f"Failed to process order {order_id}",
            payload={
                "order_id": order_id,
                "error": error_data
            }
        )
        
        # Store error info in database for retry logic
        store_failed_order(order_id, error_data)
        raise
```

### 6. Custom Exception with Context

```python
from dtpyfw.core.exception import RequestException

class ResourceNotFoundError(RequestException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: any, controller: str = None):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(
            status_code=404,
            controller=controller,
            message=message,
            skip_footprint=False
        )
        self.resource_type = resource_type
        self.resource_id = resource_id

# Usage
try:
    user = get_user(123)
except:
    raise ResourceNotFoundError(
        resource_type="User",
        resource_id=123,
        controller="UserController.get_user"
    )
```

## Error Response Format

When using `exception_to_dict()`, you get a consistent error format:

```json
{
  "type": "ValueError",
  "message": "Invalid user ID",
  "traceback": [
    {
      "filename": "/app/services/user_service.py",
      "line": 42,
      "function": "validate_user_id",
      "text": "raise ValueError('Invalid user ID')"
    },
    {
      "filename": "/app/api/routes/users.py",
      "line": 28,
      "function": "get_user",
      "text": "user_id = validate_user_id(raw_id)"
    }
  ],
  "args": ["Invalid user ID"]
}
```

## Best Practices

1. **Use RequestException for HTTP-related errors:**
   ```python
   # Good
   raise RequestException(status_code=404, message="User not found")
   
   # Avoid for non-HTTP errors
   # raise RequestException(status_code=500, message="Math error")
   ```

2. **Provide meaningful controller names:**
   ```python
   # Good
   raise RequestException(
       controller="UserService.create_user",
       message="Failed to create user"
   )
   
   # Less helpful
   raise RequestException(controller="service", message="Error")
   ```

3. **Use skip_footprint appropriately:**
   ```python
   # Skip if you're logging elsewhere
   footprint.leave(log_type="error", message="Error occurred")
   raise RequestException(skip_footprint=True)
   
   # Don't skip for automatic logging
   raise RequestException(skip_footprint=False)
   ```

4. **Serialize exceptions before storing:**
   ```python
   try:
       risky_operation()
   except Exception as e:
       # Convert to dict before storing in DB or cache
       error_dict = exception_to_dict(e)
       store_error_in_db(error_dict)
   ```

5. **Include context in error messages:**
   ```python
   raise RequestException(
       status_code=400,
       controller="PaymentService",
       message=f"Payment failed for order {order_id}: {reason}"
   )
   ```

## HTTP Status Code Guidelines

Common status codes for `RequestException`:

| Code | Meaning | Use Case |
|------|---------|----------|
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | External service error |
| 503 | Service Unavailable | Service temporarily down |
| 504 | Gateway Timeout | External service timeout |

## Related Modules

- **dtpyfw.core.request** - Uses RequestException for HTTP errors
- **dtpyfw.log.footprint** - Logging system that receives exception data
- **dtpyfw.api.middlewares.http_exception** - FastAPI middleware using these exceptions
- **dtpyfw.core.retry** - Retry logic that handles exceptions

## Dependencies

- `sys` - For exception info
- `traceback` - For traceback extraction

## See Also

- [Python Exception Handling](https://docs.python.org/3/tutorial/errors.html)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
