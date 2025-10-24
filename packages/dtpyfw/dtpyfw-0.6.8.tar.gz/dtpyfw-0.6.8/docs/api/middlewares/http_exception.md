# dtpyfw.api.middlewares.http_exception

HTTP exception handler middleware for FastAPI applications.

## Module Overview

The `http_exception` module provides a centralized exception handler for HTTP errors in FastAPI applications. It processes Starlette HTTP exceptions, logs them with detailed context, and returns standardized error responses to clients.

## Key Features

- **Centralized Error Handling**: Single handler for all HTTP exceptions
- **Detailed Logging**: Logs exceptions with request context (URL, method, headers)
- **Standardized Responses**: Returns consistent error response format
- **404 Special Handling**: Returns the requested path for 404 errors
- **Integration with dtpyfw.log**: Uses the framework's logging system for error tracking

## Functions

### http_exception_handler

```python
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> Response
```

Asynchronous exception handler that processes HTTP errors, logs them with detailed context, and returns standardized error responses.

**Parameters:**

- **request** (`Request`): The incoming FastAPI request that triggered the exception
- **exc** (`StarletteHTTPException`): The HTTP exception instance containing status code and error details

**Returns:**

- `Response`: Formatted JSON error response with appropriate status code

**Behavior:**

- For 404 errors: Returns the requested path as the error detail
- For other errors: Returns the exception's detail message
- Logs all exceptions with request metadata for debugging
- Uses `return_response` for consistent response formatting

## Usage Examples

### Automatic Registration with Application

The exception handler is automatically registered when using the `Application` class:

```python
from dtpyfw.api import Application

app = Application(
    title="My API",
    version="1.0.0"
).get_app()

# http_exception_handler is automatically registered
# No additional configuration needed
```

### Manual Registration

If you're using FastAPI directly without the `Application` wrapper:

```python
from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException
from dtpyfw.api.middlewares.http_exception import http_exception_handler

app = FastAPI()

# Register the exception handler
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id == 0:
        raise StarletteHTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}
```

### Triggering HTTP Exceptions

```python
from fastapi import HTTPException

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id < 0:
        raise HTTPException(
            status_code=400,
            detail="User ID must be positive"
        )
    
    user = find_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return user

# Responses:
# GET /users/-1  -> 400: "User ID must be positive"
# GET /users/999 -> 404: "User not found"
```

### Custom 404 Handling

```python
from fastapi import HTTPException

@app.get("/files/{file_path:path}")
def get_file(file_path: str):
    if not file_exists(file_path):
        # For 404s, the handler will log and return the requested path
        raise HTTPException(status_code=404)
    
    return {"file": file_path}

# GET /files/missing/document.pdf
# Response: {"success": false, "message": "/files/missing/document.pdf"}
```

### Various HTTP Status Codes

```python
from fastapi import HTTPException

@app.post("/articles")
def create_article(article: Article, user: User):
    if not user.is_authenticated:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not user.can_create_articles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if article_exists(article.slug):
        raise HTTPException(status_code=409, detail="Article already exists")
    
    if len(article.content) > 10000:
        raise HTTPException(
            status_code=413,
            detail="Article content too large"
        )
    
    return create(article)
```

## Response Format

All HTTP exceptions are formatted using the `return_response` utility:

### Success Response Format (status < 300)

```json
{
  "success": true,
  "data": <response_data>
}
```

### Error Response Format (status >= 300)

```json
{
  "success": false,
  "message": "Error description"
}
```

### Example Error Responses

**404 Not Found:**

```json
{
  "success": false,
  "message": "/api/v1/users/123"
}
```

**403 Forbidden:**

```json
{
  "success": false,
  "message": "Insufficient permissions"
}
```

**400 Bad Request:**

```json
{
  "success": false,
  "message": "Invalid input data"
}
```

## Logging Details

The handler logs exceptions with the following payload structure:

```python
{
    "status_code": 404,
    "url": "/api/v1/users/123",
    "method": "GET",
    "headers": {
        "host": "api.example.com",
        "user-agent": "Mozilla/5.0...",
        "authorization": "Bearer ...",
        ...
    }
}
```

**Log Levels:**

- All HTTP exceptions are logged at `debug` level
- Controller: `"http_exception_handler"`
- Subject: `"http_exception"`

## Common HTTP Status Codes

| Status Code | Meaning | Common Use Case |
|-------------|---------|-----------------|
| 400 | Bad Request | Invalid input data or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 405 | Method Not Allowed | HTTP method not supported for endpoint |
| 409 | Conflict | Resource already exists or state conflict |
| 413 | Payload Too Large | Request body exceeds size limit |
| 415 | Unsupported Media Type | Wrong Content-Type header |
| 422 | Unprocessable Entity | Validation errors (handled separately) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Server temporarily unavailable |

## Integration with Other Handlers

The HTTP exception handler works alongside other exception handlers:

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from dtpyfw.api.middlewares import http_exception, validation_exception

app = FastAPI()

# HTTP exception handler (4xx, 5xx errors)
app.add_exception_handler(
    StarletteHTTPException,
    http_exception.http_exception_handler
)

# Validation exception handler (422 errors)
app.add_exception_handler(
    RequestValidationError,
    validation_exception.validation_exception_handler
)

# Custom exception handler
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": str(exc)}
    )
```

## Best Practices

1. **Use Descriptive Messages**: Provide clear error messages that help users understand what went wrong
2. **Don't Expose Internals**: Avoid leaking internal implementation details in error messages
3. **Use Appropriate Status Codes**: Choose the correct HTTP status code for each error type
4. **Log for Debugging**: The handler automatically logs errors; use these logs for debugging
5. **Client-Friendly Errors**: Error messages should be actionable for API consumers
6. **Consistent Format**: The handler ensures all errors follow the same response structure

## Security Considerations

1. **Sensitive Information**: Don't include sensitive data (passwords, tokens) in error messages
2. **Stack Traces**: The handler doesn't expose stack traces to clients (use `hide_error_messages=True` in production)
3. **Error Details**: Balance between helpful error messages and security
4. **Rate Limiting**: Implement rate limiting to prevent error-based attacks
5. **Monitoring**: Monitor error rates for potential security issues

## Testing Exception Handling

```python
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

def test_http_exception_handler():
    client = TestClient(app)
    
    # Test 404
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "message": "/nonexistent"
    }
    
    # Test 403
    response = client.get("/admin/users")
    assert response.status_code == 403
    assert response.json()["success"] is False
    assert "permission" in response.json()["message"].lower()
```

## Custom Error Messages

```python
from fastapi import HTTPException

# Simple error
raise HTTPException(status_code=404, detail="User not found")

# Detailed error
raise HTTPException(
    status_code=400,
    detail="Invalid email format. Expected format: user@example.com"
)

# Resource-specific error
raise HTTPException(
    status_code=409,
    detail=f"A user with email '{email}' already exists"
)
```

## Related Modules

- [`dtpyfw.api.middlewares.validation_exception`](validation_exception.md): Validation error handler
- [`dtpyfw.api.middlewares.runtime`](runtime.md): Runtime exception handler
- [`dtpyfw.api.routes.response`](../routes/response.md): Response formatting utilities
- [`dtpyfw.log.footprint`](../../log/footprint.md): Logging system
- [`dtpyfw.api.application`](../application.md): Application configuration
