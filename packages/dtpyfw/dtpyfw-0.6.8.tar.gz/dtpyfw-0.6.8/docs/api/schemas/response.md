# dtpyfw.api.schemas.response

Common response schemas for API endpoints.

## Module Overview

The `response` module provides standardized Pydantic models for API responses, ensuring consistency across all endpoints. It includes base response structures, success/error wrappers, and simple response models for common data types.

## Key Features

- **Standardized Structure**: Consistent response format across all endpoints
- **Success/Error Differentiation**: Clear distinction between successful and failed requests
- **Type Safety**: Strong typing with Pydantic models
- **Generic Support**: Generic types for flexible data payloads
- **Root Models**: Simplified models for primitive responses
- **OpenAPI Integration**: Automatic API documentation generation

## Classes

### ResponseBase

```python
class ResponseBase(BaseModel):
    """Base structure returned by every API endpoint."""
```

Foundation for all API responses, providing a consistent success indicator.

**Attributes:**

- **success** (`bool`): Indicates whether the request was processed successfully

### SuccessResponse

```python
class SuccessResponse(ResponseBase, Generic[T]):
    """Successful API response wrapper."""
```

Wraps successful API responses with standardized structure.

**Attributes:**

- **success** (`bool`): Always `True` for successful responses. Default: `True`
- **data** (`Any`): Payload returned by the API. Content depends on the endpoint

**Type Parameters:**

- **T**: The type of data contained in the response payload

**Example:**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Alice"
  }
}
```

### FailedResponse

```python
class FailedResponse(ResponseBase):
    """Error response wrapper."""
```

Wraps failed API responses with standardized error structure.

**Attributes:**

- **success** (`bool`): Always `False` for failed responses. Default: `False`
- **message** (`str`): Error message explaining why the request failed

**Example:**

```json
{
  "success": false,
  "message": "User not found"
}
```

### BoolResponse

```python
class BoolResponse(RootModel[bool]):
    """Simple boolean response model."""
```

A root model for direct boolean responses without wrapper objects.

**Example:**

```json
true
```

### StrResponse

```python
class StrResponse(RootModel[str]):
    """Simple string response model."""
```

A root model for direct string responses without wrapper objects.

**Example:**

```json
"Operation completed successfully"
```

### UUIDResponse

```python
class UUIDResponse(RootModel[UUID]):
    """Simple UUID response model."""
```

A root model for direct UUID responses without wrapper objects.

**Example:**

```json
"550e8400-e29b-41d4-a716-446655440000"
```

### ListResponse

```python
class ListResponse(RootModel[list]):
    """Simple list response model."""
```

A root model for direct list responses without wrapper objects.

**Example:**

```json
[1, 2, 3, 4, 5]
```

### ListOfDictResponse

```python
class ListOfDictResponse(RootModel[list[dict[str, Any]]]):
    """Response model for a list of dictionaries."""
```

A root model for lists of dictionaries without wrapper objects.

**Example:**

```json
[
  {"id": 1, "name": "Alice"},
  {"id": 2, "name": "Bob"}
]
```

### DictResponse

```python
class DictResponse(RootModel[dict[str, Any]]):
    """Simple dictionary response model."""
```

A root model for direct dictionary responses without wrapper objects.

**Example:**

```json
{
  "key1": "value1",
  "key2": "value2"
}
```

## Usage Examples

### Success Response with Custom Model

```python
from pydantic import BaseModel
from dtpyfw.api.schemas.response import SuccessResponse

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{user_id}", response_model=SuccessResponse[User])
def get_user(user_id: int):
    user = User(id=user_id, name="Alice", email="alice@example.com")
    return {"success": True, "data": user}

# Response:
# {
#   "success": true,
#   "data": {
#     "id": 1,
#     "name": "Alice",
#     "email": "alice@example.com"
#   }
# }
```

### Error Response

```python
from dtpyfw.api.schemas.response import FailedResponse
from fastapi import HTTPException

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = find_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

# Error Response (handled by exception middleware):
# {
#   "success": false,
#   "message": "User not found"
# }
```

### Boolean Response

```python
from dtpyfw.api.schemas.response import BoolResponse

@app.delete("/users/{user_id}", response_model=BoolResponse)
def delete_user(user_id: int):
    success = delete(user_id)
    return success

# Response: true
```

### String Response

```python
from dtpyfw.api.schemas.response import StrResponse

@app.get("/version", response_model=StrResponse)
def get_version():
    return "1.0.0"

# Response: "1.0.0"
```

### UUID Response

```python
from uuid import uuid4
from dtpyfw.api.schemas.response import UUIDResponse

@app.post("/resources", response_model=UUIDResponse)
def create_resource(resource: dict):
    resource_id = uuid4()
    save_resource(resource_id, resource)
    return resource_id

# Response: "550e8400-e29b-41d4-a716-446655440000"
```

### List Response

```python
from dtpyfw.api.schemas.response import ListOfDictResponse

@app.get("/users", response_model=ListOfDictResponse)
def get_users():
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]

# Response:
# [
#   {"id": 1, "name": "Alice"},
#   {"id": 2, "name": "Bob"}
# ]
```

### Dictionary Response

```python
from dtpyfw.api.schemas.response import DictResponse

@app.get("/config", response_model=DictResponse)
def get_config():
    return {
        "debug": False,
        "version": "1.0.0",
        "features": ["api", "auth"]
    }

# Response:
# {
#   "debug": false,
#   "version": "1.0.0",
#   "features": ["api", "auth"]
# }
```

### Using with Route Class

```python
from dtpyfw.api import Route, RouteMethod
from dtpyfw.api.schemas.response import SuccessResponse
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

def get_users():
    return [User(id=1, name="Alice"), User(id=2, name="Bob")]

route = Route(
    path="/users",
    method=RouteMethod.GET,
    handler=get_users,
    response_model=list[User],  # Automatically wrapped in SuccessResponse
    wrapping_response_model=True
)

# Response:
# {
#   "success": true,
#   "data": [
#     {"id": 1, "name": "Alice"},
#     {"id": 2, "name": "Bob"}
#   ]
# }
```

## OpenAPI Documentation

These response models integrate automatically with FastAPI's OpenAPI generation:

### Success Response Schema

```yaml
SuccessResponse:
  type: object
  required:
    - success
    - data
  properties:
    success:
      type: boolean
      default: true
    data:
      type: object
```

### Failed Response Schema

```yaml
FailedResponse:
  type: object
  required:
    - success
    - message
  properties:
    success:
      type: boolean
      default: false
    message:
      type: string
```

## Best Practices

1. **Consistent Success Wrapper**: Use `SuccessResponse` for all successful responses
2. **Clear Error Messages**: Provide actionable error messages in `FailedResponse`
3. **Type Parameters**: Use generic types with `SuccessResponse[YourModel]` for type safety
4. **Root Models for Simple Data**: Use `BoolResponse`, `StrResponse`, etc. for simple primitive responses
5. **Document Response Models**: Always specify `response_model` in route definitions
6. **HTTP Status Codes**: Use appropriate status codes with different response types

## Common Response Patterns

### Paginated Response

```python
from pydantic import BaseModel
from typing import List
from dtpyfw.api.schemas.response import SuccessResponse

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    has_next: bool

@app.get("/items", response_model=SuccessResponse[PaginatedResponse])
def list_items(page: int = 1, limit: int = 20):
    items = get_items(page, limit)
    total = get_total_count()
    
    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "has_next": (page * limit) < total
        }
    }
```

### Create Response with ID

```python
from pydantic import BaseModel
from dtpyfw.api.schemas.response import SuccessResponse

class CreateResponse(BaseModel):
    id: int
    created_at: str

@app.post("/resources", response_model=SuccessResponse[CreateResponse])
def create_resource(resource: dict):
    result = create(resource)
    return {
        "success": True,
        "data": {
            "id": result.id,
            "created_at": result.created_at.isoformat()
        }
    }
```

### Bulk Operation Response

```python
from pydantic import BaseModel
from dtpyfw.api.schemas.response import SuccessResponse

class BulkResponse(BaseModel):
    success_count: int
    error_count: int
    errors: list[str]

@app.post("/bulk-create", response_model=SuccessResponse[BulkResponse])
def bulk_create(items: list[dict]):
    results = process_bulk(items)
    return {
        "success": True,
        "data": {
            "success_count": results.success,
            "error_count": results.errors,
            "errors": results.error_messages
        }
    }
```

## Testing Response Models

```python
from fastapi.testclient import TestClient

def test_success_response():
    client = TestClient(app)
    response = client.get("/users/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["id"] == 1

def test_error_response():
    client = TestClient(app)
    response = client.get("/users/999")
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "message" in data
```

## Related Modules

- [`dtpyfw.api.routes.response`](../routes/response.md): Response formatting utilities
- [`dtpyfw.api.routes.route`](../routes/route.md): Route configuration
- [`dtpyfw.api.schemas.models`](models.md): Request/response data models
- Pydantic Models: [Pydantic Documentation](https://docs.pydantic.dev/)
