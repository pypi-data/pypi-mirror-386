# dtpyfw.api.middlewares.runtime

Runtime error handling middleware for FastAPI applications.

## Module Overview

The `runtime` module provides the `Runtime` middleware class that intercepts and handles all runtime exceptions during request processing. It logs errors with detailed context and returns standardized error responses to clients while optionally hiding sensitive error details in production.

## Key Features

- **Global Exception Handling**: Catches all unhandled exceptions during request processing
- **Detailed Error Logging**: Logs exceptions with request context (headers, body, path, method)
- **RequestException Support**: Special handling for framework-specific exceptions
- **Production Mode**: Option to hide error details from clients for security
- **Large Body Handling**: Safely handles requests with large payloads
- **JSON Serialization**: Properly serializes exception details for logging

## Classes

### Runtime

```python
class Runtime:
    """Middleware for catching and handling runtime exceptions in FastAPI apps."""
```

#### Constructor

```python
def __init__(self, hide_error_messages: bool = True) -> None
```

Initializes the runtime error handler with configuration for error message visibility.

**Parameters:**

- **hide_error_messages** (`bool`, optional): If `True`, returns generic error messages to clients for security. Defaults to `True`

**Behavior:**

- When `True`: Clients receive a generic error message for unhandled exceptions
- When `False`: Clients receive the actual exception message (useful for development)

#### Methods

##### \_\_call\_\_

```python
async def __call__(self, request: Request, call_next: Callable) -> Response
```

Starlette middleware dispatch method that processes requests and handles exceptions.

**Parameters:**

- **request** (`Request`): The incoming FastAPI request
- **call_next** (`Callable`): The next middleware or route handler in the chain

**Returns:**

- `Response`: Either the successful response from `call_next` or an error response

**Exception Handling:**

1. **RequestException**: Returns the exception's custom status code and message
2. **General Exception**: Returns status 500 with appropriate error message

##### get_request_body (static)

```python
@staticmethod
async def get_request_body(request: Request) -> Dict[str, Any]
```

Extracts and serializes the request body for logging, with size limits for safety.

**Parameters:**

- **request** (`Request`): The incoming FastAPI request

**Returns:**

- `Dict[str, Any]`: Dictionary containing content metadata and body JSON

**Behavior:**

- Skips bodies larger than 1MB to prevent memory issues
- Returns content-length, content-type, and decoded JSON body
- Gracefully handles decode failures

##### create_payload (static)

```python
@staticmethod
async def create_payload(request: Request, exception: Exception) -> Dict[str, Any]
```

Builds a comprehensive payload for logging exceptions with full request context.

**Parameters:**

- **request** (`Request`): The incoming FastAPI request that triggered the exception
- **exception** (`Exception`): The exception instance that was raised

**Returns:**

- `Dict[str, Any]`: JSON-serializable payload containing request details and exception information

**Payload Contents:**

- Request path, method, query parameters, path parameters
- Request headers and body
- Exception type, message, traceback

## Usage Examples

### Automatic Registration with Application

The Runtime middleware is automatically registered when using the `Application` class:

```python
from dtpyfw.api import Application

# Development mode - show error details
dev_app = Application(
    title="Dev API",
    version="1.0.0",
    hide_error_messages=False
).get_app()

# Production mode - hide error details (default)
prod_app = Application(
    title="Production API",
    version="1.0.0",
    hide_error_messages=True  # Default
).get_app()
```

### Manual Registration

If using FastAPI directly without the `Application` wrapper:

```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from dtpyfw.api.middlewares.runtime import Runtime

app = FastAPI()

# Register runtime middleware
runtime_middleware = Runtime(hide_error_messages=True)
app.add_middleware(BaseHTTPMiddleware, dispatch=runtime_middleware)

@app.get("/items/{item_id}")
def get_item(item_id: int):
    # Any unhandled exception will be caught by runtime middleware
    return {"item_id": item_id}
```

### Handling RequestException

```python
from fastapi import Request
from dtpyfw.core.exception import RequestException

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = find_user(user_id)
    
    if not user:
        # Runtime middleware will catch this and return 404
        raise RequestException(
            status_code=404,
            controller="get_user",
            message="User not found"
        )
    
    return user

# Response when user not found:
# Status: 404
# Body: {"success": false, "message": "User not found"}
```

### Handling General Exceptions

```python
@app.post("/calculate")
def calculate(a: int, b: int):
    # Division by zero will be caught by runtime middleware
    result = a / b
    return {"result": result}

# Request: POST /calculate with b=0
# 
# In development (hide_error_messages=False):
# Status: 500
# Body: {"success": false, "message": "division by zero"}
#
# In production (hide_error_messages=True):
# Status: 500
# Body: {"success": false, "message": "An unexpected issue has occurred; our team has been notified..."}
```

### Custom Error Handling

```python
from dtpyfw.core.exception import RequestException

@app.get("/protected-resource")
def protected_resource(user: User):
    if not user.is_verified:
        raise RequestException(
            status_code=403,
            controller="protected_resource",
            message="Email verification required",
            skip_footprint=False  # Will log this error
        )
    
    return {"resource": "data"}
```

### Skipping Error Logging

```python
from dtpyfw.core.exception import RequestException

@app.get("/check-availability")
def check_availability(username: str):
    if username_exists(username):
        # Don't log this as it's expected behavior
        raise RequestException(
            status_code=409,
            controller="check_availability",
            message="Username already taken",
            skip_footprint=True  # Skip logging
        )
    
    return {"available": True}
```

## Error Response Format

### RequestException Response

```json
{
  "success": false,
  "message": "User-friendly error message"
}
```

**HTTP Status:** As specified in the RequestException

### General Exception Response (Production)

```json
{
  "success": false,
  "message": "An unexpected issue has occurred; our team has been notified and is working diligently to resolve it promptly."
}
```

**HTTP Status:** 500

### General Exception Response (Development)

```json
{
  "success": false,
  "message": "Actual exception message: division by zero"
}
```

**HTTP Status:** 500

## Logging Details

### RequestException Logging

```python
{
    "log_type": "warning",
    "controller": "get_user",
    "subject": "Request Error",
    "message": "User not found",
    "payload": {
        "path": "/api/v1/users/123",
        "method": "GET",
        "query_parameters": {},
        "path_parameters": {"user_id": "123"},
        "headers": {...},
        "body": {...}
    }
}
```

### General Exception Logging

```python
{
    "log_type": "error",
    "controller": "dtpyfw.api.middlewares.runtime.Runtime.__call__",
    "subject": "Unrecognized Error",
    "message": "division by zero",
    "payload": {
        "path": "/calculate",
        "method": "POST",
        "query_parameters": {},
        "path_parameters": {},
        "headers": {...},
        "body": {
            "content_length": "25",
            "content_type": "application/json",
            "json": "{\"a\": 10, \"b\": 0}"
        },
        "exception_type": "ZeroDivisionError",
        "exception_message": "division by zero",
        "traceback": [...]
    }
}
```

## Request Body Handling

The middleware intelligently handles request bodies:

### Small Bodies (< 1MB)

```python
# Request body is logged for debugging
{
    "content_length": "150",
    "content_type": "application/json",
    "json": "{\"user_id\": 123, \"action\": \"update\"}"
}
```

### Large Bodies (>= 1MB)

```python
# Body is skipped to prevent memory issues
{
    "content_length": "2097152",
    "content_type": "application/json"
    # No 'json' field - body not logged
}
```

### Non-JSON Bodies

```python
# Body decode failure handled gracefully
{
    "content_length": "1024",
    "content_type": "application/octet-stream"
    # No 'json' field - couldn't decode
}
```

## Integration with Other Middlewares

The Runtime middleware is typically registered early in the middleware chain:

```python
from dtpyfw.api.middlewares import Timer, Runtime

app = FastAPI()

# Order matters: Timer -> Runtime -> Other middlewares
app.add_middleware(BaseHTTPMiddleware, dispatch=Timer())
app.add_middleware(BaseHTTPMiddleware, dispatch=Runtime(hide_error_messages=True))
app.add_middleware(BaseHTTPMiddleware, dispatch=CustomMiddleware())
```

## Testing Error Handling

```python
from fastapi.testclient import TestClient
from dtpyfw.core.exception import RequestException

def test_runtime_handles_request_exception():
    client = TestClient(app)
    
    # Endpoint that raises RequestException
    response = client.get("/users/999")
    
    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "message": "User not found"
    }

def test_runtime_handles_general_exception():
    client = TestClient(app)
    
    # Endpoint that raises ValueError
    response = client.post("/calculate", json={"a": 10, "b": 0})
    
    assert response.status_code == 500
    assert "success" in response.json()
    assert response.json()["success"] is False
```

## Best Practices

1. **Use RequestException**: For expected errors, use `RequestException` with appropriate status codes
2. **Production Mode**: Always enable `hide_error_messages=True` in production
3. **Skip Logging**: Use `skip_footprint=True` for expected errors that don't need logging
4. **Monitor Logs**: Set up alerts for error-level logs from the runtime middleware
5. **Descriptive Messages**: Provide clear, actionable error messages in RequestException
6. **Don't Expose Internals**: Never include sensitive data or implementation details in error messages
7. **Test Error Paths**: Write tests for both success and error scenarios

## Security Considerations

1. **Hide Stack Traces**: Enable `hide_error_messages=True` to prevent stack trace exposure
2. **Sanitize Error Messages**: Ensure error messages don't contain sensitive information
3. **Rate Limiting**: Implement rate limiting to prevent error-based attacks
4. **Monitor Patterns**: Watch for unusual error patterns that might indicate attacks
5. **Secure Logging**: Ensure logs containing request bodies are stored securely
6. **PII Protection**: Be careful about logging personally identifiable information in request bodies

## Performance Considerations

1. **Body Size Limit**: The middleware automatically skips logging bodies > 1MB
2. **Async Operations**: All I/O operations are asynchronous for better performance
3. **Exception Handling**: Catching all exceptions has minimal performance impact
4. **Logging**: Use efficient logging backends for high-traffic applications

## Environment-Specific Configuration

### Development

```python
app = Application(
    title="Dev API",
    version="1.0.0",
    hide_error_messages=False,  # Show detailed errors
).get_app()
```

**Benefits:**
- See actual error messages
- Easier debugging
- Faster development

### Staging

```python
app = Application(
    title="Staging API",
    version="1.0.0",
    hide_error_messages=True,  # Hide errors but log everything
).get_app()
```

**Benefits:**
- Test production-like behavior
- Validate error handling
- Check logging configuration

### Production

```python
app = Application(
    title="Production API",
    version="1.0.0",
    hide_error_messages=True,  # Always hide errors
).get_app()
```

**Benefits:**
- Secure error messages
- Professional user experience
- Prevent information disclosure

## Related Modules

- [`dtpyfw.core.exception`](../../core/exception.md): RequestException and exception utilities
- [`dtpyfw.api.middlewares.http_exception`](http_exception.md): HTTP exception handler
- [`dtpyfw.api.middlewares.validation_exception`](validation_exception.md): Validation error handler
- [`dtpyfw.log.footprint`](../../log/footprint.md): Logging system
- [`dtpyfw.api.routes.response`](../routes/response.md): Response formatting utilities
- [`dtpyfw.api.application`](../application.md): Application configuration
