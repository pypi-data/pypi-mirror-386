# dtpyfw.api.routes.route

Single FastAPI route configuration and wrapping system.

## Module Overview

The `route` module provides the `Route` class for defining individual API endpoints with comprehensive configuration options. It encapsulates path, method, handler function, authentication, response models, and OpenAPI metadata in a clean, declarative interface.

## Key Features

- **Declarative Configuration**: Define routes using a clear, object-oriented API
- **Automatic Response Wrapping**: Optional automatic formatting of handler return values
- **Authentication Integration**: Built-in support for authentication requirements
- **Response Model Generation**: Automatic creation of success/error response models
- **OpenAPI Integration**: Full support for Swagger/ReDoc documentation
- **Flexible Handler Support**: Works with both sync and async handlers
- **Type Safety**: Strong typing for all configuration options

## Enumerations

### RouteMethod

```python
class RouteMethod(Enum):
    """HTTP methods supported for route definitions."""
```

**Values:**

- **GET**: `"GET"` - Retrieve resources
- **POST**: `"POST"` - Create resources
- **PUT**: `"PUT"` - Update/replace resources
- **DELETE**: `"DELETE"` - Delete resources
- **PATCH**: `"PATCH"` - Partial update resources
- **HEAD**: `"HEAD"` - Retrieve headers only
- **OPTIONS**: `"OPTIONS"` - Describe communication options
- **TRACE**: `"TRACE"` - Message loop-back test
- **CONNECT**: `"CONNECT"` - Establish tunnel

## Classes

### Route

```python
class Route:
    """Single FastAPI route configuration."""
```

Encapsulates all configuration for a single API endpoint, including path, method, handler function, authentication, response models, and OpenAPI metadata.

#### Constructor

```python
def __init__(
    self,
    path: str,
    method: RouteMethod,
    handler: Callable,
    wrapping_handler: bool = True,
    authentications: Optional[List[Auth]] = None,
    response_model: Optional[Type[BaseModel]] = None,
    default_response_model: Optional[Any] = None,
    wrapping_response_model: bool = True,
    status_code: int = 200,
    errors: Optional[Dict[int, str]] = None,
    dependencies: Optional[List[Any]] = None,
    wrapper_kwargs: Optional[Dict[str, Any]] = None,
    name: Optional[str] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    response_description: str = "Successful Response",
    responses: Optional[Dict[int, Dict[str, Any]]] = None,
    deprecated: bool = False,
    operation_id: Optional[str] = None,
    include_in_schema: bool = True,
    response_class: Optional[Type[Response]] = JSONResponse,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    response_model_by_alias: bool = True,
    response_return_json_directly: bool = False,
    response_headers: Optional[Dict[int, Dict[Any, Any]]] = None,
    response_no_cache_headers: bool = True,
)
```

**Core Parameters:**

- **path** (`str`): URL path for the route (e.g., `"/users/{user_id}"`)
- **method** (`RouteMethod`): HTTP method for the route
- **handler** (`Callable`): The function that handles requests to this route

**Handler Wrapping:**

- **wrapping_handler** (`bool`): If `True`, automatically wraps handler responses using `return_response`. Defaults to `True`

**Authentication:**

- **authentications** (`List[Auth] | None`): List of Auth configurations for this route. Defaults to `None`

**Response Model:**

- **response_model** (`Type[BaseModel] | None`): Pydantic model for the successful response data. Defaults to `None`
- **default_response_model** (`Any | None`): Default value for the response model. Defaults to `None`
- **wrapping_response_model** (`bool`): If `True`, wraps response_model in SuccessResponse. Defaults to `True`

**Status Code:**

- **status_code** (`int`): Default HTTP status code for successful responses. Defaults to `200`

**Error Handling:**

- **errors** (`Dict[int, str] | None`): Dict mapping error status codes to error messages. Defaults to `None`
- **responses** (`Dict[int, Dict[str, Any]] | None`): Custom response definitions for OpenAPI. Defaults to `None`

**Dependencies:**

- **dependencies** (`List[Any] | None`): Additional FastAPI dependencies for this route. Defaults to `None`

**OpenAPI Documentation:**

- **name** (`str | None`): Name for the route (used in URL reversing). Defaults to `None`
- **summary** (`str | None`): Short summary shown in OpenAPI docs. Defaults to `None`
- **description** (`str | None`): Detailed description shown in OpenAPI docs. Defaults to `None`
- **tags** (`List[str] | None`): List of tags for grouping in OpenAPI docs. Defaults to `None`
- **response_description** (`str`): Description of the successful response. Defaults to `"Successful Response"`
- **deprecated** (`bool`): If `True`, marks the route as deprecated. Defaults to `False`
- **operation_id** (`str | None`): Custom operation ID for OpenAPI. Defaults to `None`
- **include_in_schema** (`bool`): If `False`, excludes route from OpenAPI schema. Defaults to `True`

**Response Configuration:**

- **response_class** (`Type[Response] | None`): Response class to use. Defaults to `JSONResponse`
- **response_model_exclude_unset** (`bool`): Exclude unset fields from response. Defaults to `False`
- **response_model_exclude_defaults** (`bool`): Exclude default values from response. Defaults to `False`
- **response_model_exclude_none** (`bool`): Exclude None values from response. Defaults to `False`
- **response_model_by_alias** (`bool`): Use field aliases in response. Defaults to `True`
- **response_return_json_directly** (`bool`): Skip success/error wrapping. Defaults to `False`
- **response_headers** (`Dict[int, Dict[Any, Any]] | None`): Custom headers per status code. Defaults to `None`
- **response_no_cache_headers** (`bool`): If `True`, adds no-cache headers. Defaults to `True`

**Other:**

- **wrapper_kwargs** (`Dict[str, Any] | None`): Additional kwargs passed to the response wrapper. Defaults to `None`

#### Methods

##### wrapped_handler

```python
def wrapped_handler(self) -> Callable
```

Returns a handler that automatically formats the response using `return_response`.

**Returns:**

- `Callable`: Wrapped handler function (async or sync based on original)

**Behavior:**

- Preserves the async/sync nature of the original handler
- Applies response wrapping if `wrapping_handler=True`
- Uses the configured status code, response class, and other options

## Usage Examples

### Basic GET Route

```python
from dtpyfw.api import Route, RouteMethod

def get_users():
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]

route = Route(
    path="/users",
    method=RouteMethod.GET,
    handler=get_users,
    summary="List all users",
    description="Returns a list of all users in the system",
    tags=["Users"]
)
```

### POST Route with Response Model

```python
from pydantic import BaseModel
from dtpyfw.api import Route, RouteMethod

class User(BaseModel):
    id: int
    name: str
    email: str

class UserCreate(BaseModel):
    name: str
    email: str

def create_user(user: UserCreate):
    # Create user logic
    return User(id=1, name=user.name, email=user.email)

route = Route(
    path="/users",
    method=RouteMethod.POST,
    handler=create_user,
    response_model=User,
    status_code=201,
    summary="Create a new user",
    tags=["Users"]
)
```

### Authenticated Route

```python
from dtpyfw.api import Route, RouteMethod
from dtpyfw.api.routes.authentication import Auth, AuthType

api_key_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value="secret-key"
)

def get_sensitive_data():
    return {"data": "sensitive"}

route = Route(
    path="/sensitive",
    method=RouteMethod.GET,
    handler=get_sensitive_data,
    authentications=[api_key_auth],
    summary="Get sensitive data",
    tags=["Sensitive"]
)
```

### Route with Path Parameters

```python
from dtpyfw.api import Route, RouteMethod

def get_user(user_id: int):
    user = find_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

route = Route(
    path="/users/{user_id}",
    method=RouteMethod.GET,
    handler=get_user,
    summary="Get user by ID",
    tags=["Users"]
)
```

### Route with Error Definitions

```python
from dtpyfw.api import Route, RouteMethod

def delete_user(user_id: int):
    # Delete logic
    return {"deleted": True}

route = Route(
    path="/users/{user_id}",
    method=RouteMethod.DELETE,
    handler=delete_user,
    status_code=204,
    errors={
        404: "User not found",
        403: "Insufficient permissions to delete user",
        409: "User has active dependencies"
    },
    summary="Delete a user",
    tags=["Users"]
)
```

### Async Handler Route

```python
from dtpyfw.api import Route, RouteMethod

async def get_user_async(user_id: int):
    user = await fetch_user_from_db(user_id)
    return user

route = Route(
    path="/users/{user_id}",
    method=RouteMethod.GET,
    handler=get_user_async,  # Async handler automatically detected
    summary="Get user (async)",
    tags=["Users"]
)
```

### Route Without Response Wrapping

```python
from dtpyfw.api import Route, RouteMethod

def health_check():
    return {"status": "healthy", "version": "1.0.0"}

route = Route(
    path="/health",
    method=RouteMethod.GET,
    handler=health_check,
    response_return_json_directly=True,  # No success wrapper
    summary="Health check endpoint",
    tags=["System"]
)
```

### Route with Custom Dependencies

```python
from fastapi import Depends
from dtpyfw.api import Route, RouteMethod

def verify_token(token: str = Header(...)):
    if token != "valid-token":
        raise HTTPException(status_code=401)
    return token

def protected_endpoint(token: str = Depends(verify_token)):
    return {"message": "authenticated"}

route = Route(
    path="/protected",
    method=RouteMethod.GET,
    handler=protected_endpoint,
    dependencies=[Depends(verify_token)],  # Additional dependency
    summary="Protected endpoint",
    tags=["Auth"]
)
```

### Route with Custom Headers

```python
from dtpyfw.api import Route, RouteMethod

def create_resource(resource: dict):
    created = save_resource(resource)
    return created

route = Route(
    path="/resources",
    method=RouteMethod.POST,
    handler=create_resource,
    status_code=201,
    response_headers={
        201: {
            "Location": "/resources/{id}",
            "X-Resource-Type": "document"
        }
    },
    summary="Create a new resource",
    tags=["Resources"]
)
```

### Deprecated Route

```python
from dtpyfw.api import Route, RouteMethod

def old_endpoint():
    return {"message": "Use /api/v2/endpoint instead"}

route = Route(
    path="/old-endpoint",
    method=RouteMethod.GET,
    handler=old_endpoint,
    deprecated=True,  # Marked as deprecated in OpenAPI
    summary="Old endpoint (deprecated)",
    description="This endpoint is deprecated. Please use /api/v2/endpoint instead.",
    tags=["Legacy"]
)
```

### Route with Complex Response Model

```python
from pydantic import BaseModel
from typing import List
from dtpyfw.api import Route, RouteMethod

class Item(BaseModel):
    id: int
    name: str

class PaginatedResponse(BaseModel):
    items: List[Item]
    total: int
    page: int
    has_next: bool

def list_items(page: int = 1, limit: int = 20):
    items = get_items(page, limit)
    return PaginatedResponse(
        items=items,
        total=get_total(),
        page=page,
        has_next=(page * limit) < get_total()
    )

route = Route(
    path="/items",
    method=RouteMethod.GET,
    handler=list_items,
    response_model=PaginatedResponse,
    summary="List items with pagination",
    tags=["Items"]
)
```

### Route Excluding None Values

```python
from pydantic import BaseModel
from dtpyfw.api import Route, RouteMethod

class User(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None

def get_user(user_id: int):
    return User(id=user_id, name="Alice", email=None, phone=None)

route = Route(
    path="/users/{user_id}",
    method=RouteMethod.GET,
    handler=get_user,
    response_model=User,
    response_model_exclude_none=True,  # Exclude None values from response
    summary="Get user",
    tags=["Users"]
)

# Response will only include: {"id": 1, "name": "Alice"}
```

## Response Model Wrapping

When `wrapping_response_model=True` (default), the route automatically creates a response model like:

```python
class SuccessResponse(BaseModel):
    success: bool = True
    data: YourResponseModel
```

This ensures all successful responses follow the pattern:

```json
{
  "success": true,
  "data": <your_response_data>
}
```

To disable wrapping:

```python
route = Route(
    path="/endpoint",
    method=RouteMethod.GET,
    handler=handler,
    response_model=YourModel,
    wrapping_response_model=False  # Don't wrap in SuccessResponse
)
```

## Error Response Models

The route automatically generates error response models based on the `errors` parameter:

```python
route = Route(
    path="/users/{user_id}",
    method=RouteMethod.GET,
    handler=get_user,
    errors={
        404: "User not found",
        403: "Access denied"
    }
)
```

This generates OpenAPI schemas for:

```json
// 404 Response
{
  "success": false,
  "message": "User not found"
}

// 403 Response
{
  "success": false,
  "message": "Access denied"
}
```

## OpenAPI Integration

The Route class fully integrates with FastAPI's OpenAPI generation:

- **Summary & Description**: Shown in Swagger UI
- **Tags**: Group routes in documentation
- **Response Models**: Document response structure
- **Error Responses**: Document possible error responses
- **Authentication**: Show required authentication
- **Deprecated Flag**: Mark old endpoints
- **Custom Operation ID**: Control operation naming

## Best Practices

1. **Always Set Summary**: Provide clear summaries for documentation
2. **Use Tags**: Group related endpoints together
3. **Define Error Responses**: Document expected error conditions
4. **Response Models**: Use Pydantic models for type safety
5. **Async When Possible**: Use async handlers for I/O operations
6. **Authentication**: Apply authentication at route or router level
7. **Status Codes**: Use appropriate HTTP status codes
8. **Deprecation**: Mark old endpoints as deprecated instead of removing them

## Testing Routes

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

# Add route to app
route = Route(...)
app.add_api_route(
    path=route.path,
    endpoint=route.wrapped_handler(),
    methods=[route.method.value],
    ...
)

client = TestClient(app)

def test_route():
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json()["success"] is True
```

## Related Modules

- [`dtpyfw.api.routes.router`](router.md): Router for grouping routes
- [`dtpyfw.api.routes.response`](response.md): Response formatting utilities
- [`dtpyfw.api.routes.authentication`](authentication.md): Authentication configuration
- [`dtpyfw.api.schemas.response`](../schemas/response.md): Response schema models
- [`dtpyfw.api.application`](../application.md): Application configuration
