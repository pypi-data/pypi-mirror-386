# dtpyfw.api.middlewares.validation_exception

Validation exception handler middleware for FastAPI applications.

## Module Overview

The `validation_exception` module provides a centralized handler for request validation errors in FastAPI applications. It processes Pydantic validation errors, formats them into readable messages, logs them with detailed context, and returns standardized 422 error responses to clients.

## Key Features

- **Validation Error Handling**: Processes FastAPI/Pydantic validation errors
- **User-Friendly Messages**: Converts technical validation errors into readable format
- **Detailed Logging**: Logs validation errors with request context and error details
- **First Error Reporting**: Returns the first validation error to avoid overwhelming clients
- **Input Data Logging**: Includes the invalid input value in error messages when possible
- **Integration with dtpyfw.log**: Uses the framework's logging system

## Functions

### validation_exception_handler

```python
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> Response
```

Asynchronous exception handler that processes request validation errors, extracts error details, logs them, and returns standardized error responses.

**Parameters:**

- **request** (`Request`): The incoming FastAPI request that failed validation
- **exc** (`RequestValidationError`): The validation error exception containing error details

**Returns:**

- `Response`: Formatted JSON error response with status code 422 (Unprocessable Entity)

**Behavior:**

- Extracts the first validation error from the exception
- Formats error location (field path) into readable format
- Includes input data in error message when available
- Logs error with full request context
- Returns standardized error response

## Usage Examples

### Automatic Registration with Application

The validation exception handler is automatically registered when using the `Application` class:

```python
from dtpyfw.api import Application

app = Application(
    title="My API",
    version="1.0.0"
).get_app()

# validation_exception_handler is automatically registered
# No additional configuration needed
```

### Manual Registration

If using FastAPI directly without the `Application` wrapper:

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from dtpyfw.api.middlewares.validation_exception import validation_exception_handler

app = FastAPI()

# Register the validation exception handler
app.add_exception_handler(RequestValidationError, validation_exception_handler)

@app.post("/users")
def create_user(user: UserCreate):
    return {"user": user}
```

### Common Validation Errors

#### Missing Required Field

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    age: int

@app.post("/users")
def create_user(user: UserCreate):
    return {"user": user}

# Request: POST /users with body: {"username": "john"}
# Response:
# Status: 422
# Body: {
#   "success": false,
#   "message": "Error [location: 'body -> email'; message: 'Field required']."
# }
```

#### Type Validation Error

```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    quantity: int

@app.post("/products")
def create_product(product: Product):
    return {"product": product}

# Request: POST /products with body: {"name": "Widget", "price": "invalid", "quantity": 10}
# Response:
# Status: 422
# Body: {
#   "success": false,
#   "message": "Error [location: 'body -> price'; message: 'Input should be a valid number', input: 'invalid']."
# }
```

#### Query Parameter Validation

```python
from fastapi import Query

@app.get("/items")
def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100)
):
    return {"page": page, "limit": limit}

# Request: GET /items?page=0&limit=200
# Response:
# Status: 422
# Body: {
#   "success": false,
#   "message": "Error [location: 'query -> page'; message: 'Input should be greater than or equal to 1', input: '0']."
# }
```

#### Path Parameter Validation

```python
from uuid import UUID

@app.get("/users/{user_id}")
def get_user(user_id: UUID):
    return {"user_id": user_id}

# Request: GET /users/invalid-uuid
# Response:
# Status: 422
# Body: {
#   "success": false,
#   "message": "Error [location: 'path -> user_id'; message: 'Input should be a valid UUID', input: 'invalid-uuid']."
# }
```

#### Email Validation

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str

@app.post("/users")
def create_user(user: UserCreate):
    return {"user": user}

# Request: POST /users with body: {"email": "not-an-email", "name": "John"}
# Response:
# Status: 422
# Body: {
#   "success": false,
#   "message": "Error [location: 'body -> email'; message: 'value is not a valid email address', input: 'not-an-email']."
# }
```

#### Custom Validator Error

```python
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    username: str
    age: int
    
    @field_validator('age')
    def validate_age(cls, v):
        if v < 18:
            raise ValueError('Must be 18 or older')
        return v

@app.post("/users")
def create_user(user: UserCreate):
    return {"user": user}

# Request: POST /users with body: {"username": "john", "age": 15}
# Response:
# Status: 422
# Body: {
#   "success": false,
#   "message": "Error [location: 'body -> age'; message: 'Value error, Must be 18 or older', input: '15']."
# }
```

## Error Message Format

### Standard Format

```
Error [location: '<field_path>'; message: '<error_message>', input: '<input_value>'].
```

### Without Input (when input cannot be serialized)

```
Error [location: '<field_path>'; message: '<error_message>'].
```

### Location Format

The location is formatted as a readable path using `->` as separator:

- `body -> email` - Email field in request body
- `query -> page` - Page parameter in query string
- `path -> user_id` - User ID in URL path
- `header -> authorization` - Authorization header
- `body -> address -> city` - Nested field in request body

## Response Format

All validation errors return the same standardized format:

```json
{
  "success": false,
  "message": "Error [location: 'body -> email'; message: 'Field required']."
}
```

**HTTP Status:** 422 Unprocessable Entity

## Logging Details

The handler logs validation errors with the following structure:

```python
{
    "log_type": "debug",
    "controller": "validation_exception_handler",
    "subject": "validation_exception",
    "message": "Error [location: 'body -> email'; message: 'Field required'].",
    "payload": {
        "url": "/api/v1/users",
        "method": "POST",
        "headers": {
            "host": "api.example.com",
            "content-type": "application/json",
            ...
        },
        "errors": [
            {
                "type": "missing",
                "loc": ["body", "email"],
                "msg": "Field required",
                "input": {...}
            }
        ]
    }
}
```

## Integration with Pydantic Models

### Basic Model Validation

```python
from pydantic import BaseModel, Field

class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    published: bool = False
    tags: list[str] = []

@app.post("/articles")
def create_article(article: ArticleCreate):
    return {"article": article}

# Various validation errors will be caught and formatted
```

### Complex Nested Validation

```python
from pydantic import BaseModel
from typing import List

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class UserProfile(BaseModel):
    name: str
    email: EmailStr
    addresses: List[Address]

@app.post("/profiles")
def create_profile(profile: UserProfile):
    return {"profile": profile}

# Request: POST /profiles with invalid nested data
# Response includes full field path: "body -> addresses -> 0 -> city"
```

## Multiple Validation Errors

**Note:** The handler returns only the **first** validation error to avoid overwhelming clients with multiple error messages. If multiple fields are invalid, the client will receive feedback about the first error encountered.

```python
# Request with multiple invalid fields:
{
  "username": "",  # Too short
  "email": "invalid",  # Invalid email
  "age": -5  # Negative number
}

# Response contains only the first error:
{
  "success": false,
  "message": "Error [location: 'body -> username'; message: 'String should have at least 1 character']."
}
```

## Testing Validation Handling

```python
from fastapi.testclient import TestClient

def test_validation_error_response():
    client = TestClient(app)
    
    # Invalid request body
    response = client.post("/users", json={"username": "john"})
    
    assert response.status_code == 422
    assert response.json()["success"] is False
    assert "email" in response.json()["message"]
    assert "Field required" in response.json()["message"]

def test_query_param_validation():
    client = TestClient(app)
    
    # Invalid query parameter
    response = client.get("/items?page=-1")
    
    assert response.status_code == 422
    assert "page" in response.json()["message"]
    assert "greater than or equal to" in response.json()["message"]
```

## Custom Error Messages

### Using Field Descriptions

```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Username must be between 3 and 20 characters"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address required"
    )
```

### Using Custom Validators

```python
from pydantic import BaseModel, field_validator

class PasswordReset(BaseModel):
    password: str
    password_confirm: str
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @field_validator('password_confirm')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
```

## Best Practices

1. **Clear Field Names**: Use descriptive field names that make validation errors self-explanatory
2. **Helpful Error Messages**: Provide custom validation messages that guide users
3. **Validate Early**: Use Pydantic models to validate input as early as possible
4. **Appropriate Constraints**: Use Field constraints (min_length, max_length, ge, le) for validation
5. **Test Validation**: Write tests for validation scenarios to ensure proper error handling
6. **Document Requirements**: Document validation requirements in OpenAPI/Swagger
7. **Client-Friendly**: Ensure error messages are actionable for API consumers

## Common Validation Patterns

### Optional Fields with Defaults

```python
from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    query: str
    page: int = 1
    limit: int = 20
    sort_by: Optional[str] = None
```

### Enum Validation

```python
from enum import Enum
from pydantic import BaseModel

class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"

class OrderUpdate(BaseModel):
    order_id: int
    status: OrderStatus

# Invalid status will trigger validation error
```

### Date and DateTime Validation

```python
from datetime import date, datetime
from pydantic import BaseModel

class EventCreate(BaseModel):
    title: str
    start_date: datetime
    end_date: datetime
    
    @field_validator('end_date')
    def end_after_start(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v
```

### List Validation

```python
from pydantic import BaseModel, Field
from typing import List

class BatchCreate(BaseModel):
    items: List[str] = Field(..., min_length=1, max_length=100)
    
    @field_validator('items')
    def unique_items(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('Items must be unique')
        return v
```

## Security Considerations

1. **Input Sanitization**: Validation helps prevent injection attacks
2. **Size Limits**: Use max_length to prevent large payloads
3. **Type Safety**: Strict typing prevents type confusion attacks
4. **Error Information**: Validation errors don't expose internal system details
5. **Rate Limiting**: Combine with rate limiting to prevent validation flood attacks

## Performance Considerations

1. **Early Validation**: Pydantic validates before entering route handlers
2. **Efficient Parsing**: Validation is fast for properly formatted requests
3. **First Error Only**: Returning only the first error reduces response size
4. **Caching**: Pydantic models are compiled and cached for performance

## Related Modules

- [`dtpyfw.api.middlewares.http_exception`](http_exception.md): HTTP exception handler
- [`dtpyfw.api.middlewares.runtime`](runtime.md): Runtime exception handler
- [`dtpyfw.api.routes.response`](../routes/response.md): Response formatting utilities
- [`dtpyfw.log.footprint`](../../log/footprint.md): Logging system
- [`dtpyfw.api.application`](../application.md): Application configuration
- [Pydantic Documentation](https://docs.pydantic.dev/): Pydantic validation library
