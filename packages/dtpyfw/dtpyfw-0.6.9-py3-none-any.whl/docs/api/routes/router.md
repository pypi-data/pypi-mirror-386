# dtpyfw.api.routes.router

Collection of routes with shared configuration for FastAPI applications.

## Module Overview

The `router` module provides the `Router` class for grouping related routes together with common settings like URL prefix, tags, authentication requirements, and dependencies. It creates configured FastAPI APIRouter instances for modular application organization.

## Key Features

- **Route Grouping**: Organize related routes with shared configuration
- **URL Prefixes**: Apply common path prefixes to all routes
- **Shared Authentication**: Apply authentication to all routes in the group
- **Common Dependencies**: Share dependencies across multiple routes
- **Tag Management**: Automatically tag routes for OpenAPI organization
- **Deprecation Support**: Mark entire router as deprecated
- **OpenAPI Integration**: Full Swagger/ReDoc documentation support

## Classes

### Router

```python
class Router:
    """Collection of routes with shared configuration and authentication."""
```

Groups related routes together with common settings, then creates a configured FastAPI APIRouter instance.

#### Constructor

```python
def __init__(
    self,
    prefix: str = "",
    tags: Optional[List[str]] = None,
    authentications: Optional[List[Auth]] = None,
    dependencies: Optional[List[Any]] = None,
    routes: Optional[List[Route]] = None,
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
    default_response_class: Optional[Type[Any]] = JSONResponse,
    include_in_schema: bool = True,
    deprecated: bool = False,
)
```

**Parameters:**

- **prefix** (`str`): URL prefix for all routes in this router (e.g., `"/api/v1"`). Defaults to `""`
- **tags** (`List[str] | None`): List of tags for grouping routes in OpenAPI documentation. Defaults to `None`
- **authentications** (`List[Auth] | None`): List of Auth configurations applied to all routes. Defaults to `None`
- **dependencies** (`List[Any] | None`): Additional FastAPI dependencies for all routes. Defaults to `None`
- **routes** (`List[Route] | None`): List of Route objects to include in this router. Defaults to `None`
- **responses** (`Dict[Union[int, str], Dict[str, Any]] | None`): Common response definitions for OpenAPI schema. Defaults to `None`
- **default_response_class** (`Type[Any] | None`): Default response class for all routes. Defaults to `JSONResponse`
- **include_in_schema** (`bool`): If `False`, excludes all routes from OpenAPI schema. Defaults to `True`
- **deprecated** (`bool`): If `True`, marks all routes as deprecated in OpenAPI. Defaults to `False`

#### Methods

##### get_router

```python
def get_router(self) -> APIRouter
```

Returns the underlying configured FastAPI APIRouter instance.

**Returns:**

- `APIRouter`: The configured FastAPI APIRouter instance ready for inclusion in an Application

## Usage Examples

### Basic Router

```python
from dtpyfw.api import Router, Route, RouteMethod

def get_users():
    return [{"id": 1, "name": "Alice"}]

def get_user(user_id: int):
    return {"id": user_id, "name": "Alice"}

def create_user(user: dict):
    return {"id": 1, **user}

# Create router with multiple routes
user_router = Router(
    prefix="/users",
    tags=["Users"],
    routes=[
        Route(path="/", method=RouteMethod.GET, handler=get_users),
        Route(path="/{user_id}", method=RouteMethod.GET, handler=get_user),
        Route(path="/", method=RouteMethod.POST, handler=create_user),
    ]
)
```

### Router with Authentication

```python
from dtpyfw.api import Router, Route, RouteMethod
from dtpyfw.api.routes.authentication import Auth, AuthType

# Define authentication
api_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value="secret-key"
)

# All routes in this router require authentication
admin_router = Router(
    prefix="/admin",
    tags=["Admin"],
    authentications=[api_auth],
    routes=[
        Route(path="/users", method=RouteMethod.GET, handler=get_all_users),
        Route(path="/settings", method=RouteMethod.GET, handler=get_settings),
        Route(path="/logs", method=RouteMethod.GET, handler=get_logs),
    ]
)
```

### Router with Shared Dependencies

```python
from fastapi import Depends
from dtpyfw.api import Router, Route, RouteMethod
from dtpyfw.api.middlewares.user import UserData, get_user_data

# All routes require user authentication
authenticated_router = Router(
    prefix="/api",
    tags=["API"],
    dependencies=[Depends(get_user_data)],
    routes=[
        Route(path="/profile", method=RouteMethod.GET, handler=get_profile),
        Route(path="/settings", method=RouteMethod.GET, handler=get_settings),
    ]
)
```

### Nested Router Structure

```python
from dtpyfw.api import Application, Router, Route, RouteMethod

# Create routers for different resources
user_router = Router(
    prefix="/users",
    tags=["Users"],
    routes=[...]
)

product_router = Router(
    prefix="/products",
    tags=["Products"],
    routes=[...]
)

order_router = Router(
    prefix="/orders",
    tags=["Orders"],
    routes=[...]
)

# Group routers under /api/v1 prefix
app = Application(
    title="E-Commerce API",
    version="1.0.0",
    routers=[
        ("/api/v1", [user_router, product_router, order_router])
    ]
)
```

### Router with Multiple Tags

```python
from dtpyfw.api import Router, Route, RouteMethod

# Routes will appear under both "Admin" and "Users" in documentation
admin_user_router = Router(
    prefix="/admin/users",
    tags=["Admin", "Users"],
    routes=[...]
)
```

### Deprecated Router

```python
from dtpyfw.api import Router, Route, RouteMethod

# Mark entire router as deprecated
legacy_router = Router(
    prefix="/api/v1",
    tags=["Legacy API (v1)"],
    deprecated=True,  # All routes marked as deprecated
    routes=[...]
)
```

### Router Without OpenAPI Documentation

```python
from dtpyfw.api import Router, Route, RouteMethod

# Internal routes not shown in Swagger/ReDoc
internal_router = Router(
    prefix="/internal",
    tags=["Internal"],
    include_in_schema=False,  # Hidden from OpenAPI docs
    routes=[...]
)
```

### Router with Common Error Responses

```python
from dtpyfw.api import Router, Route, RouteMethod

# Define common error responses for all routes
api_router = Router(
    prefix="/api",
    tags=["API"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing API key"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal Server Error"},
    },
    routes=[...]
)
```

### CRUD Router Pattern

```python
from dtpyfw.api import Router, Route, RouteMethod

def list_items():
    return {"items": [...]}

def get_item(item_id: int):
    return {"id": item_id}

def create_item(item: dict):
    return {"id": 1, **item}

def update_item(item_id: int, item: dict):
    return {"id": item_id, **item}

def delete_item(item_id: int):
    return {"deleted": True}

# Complete CRUD router
crud_router = Router(
    prefix="/items",
    tags=["Items"],
    routes=[
        Route(path="/", method=RouteMethod.GET, handler=list_items, summary="List items"),
        Route(path="/{item_id}", method=RouteMethod.GET, handler=get_item, summary="Get item"),
        Route(path="/", method=RouteMethod.POST, handler=create_item, summary="Create item"),
        Route(path="/{item_id}", method=RouteMethod.PUT, handler=update_item, summary="Update item"),
        Route(path="/{item_id}", method=RouteMethod.DELETE, handler=delete_item, summary="Delete item"),
    ]
)
```

### Versioned API Routers

```python
from dtpyfw.api import Router, Route, RouteMethod

# V1 API
v1_router = Router(
    prefix="/api/v1",
    tags=["API v1"],
    routes=[
        Route(path="/users", method=RouteMethod.GET, handler=get_users_v1),
    ]
)

# V2 API with improved features
v2_router = Router(
    prefix="/api/v2",
    tags=["API v2"],
    routes=[
        Route(path="/users", method=RouteMethod.GET, handler=get_users_v2),
    ]
)

# Include both versions
app = Application(
    title="Multi-Version API",
    version="2.0.0",
    routers=[v1_router, v2_router]
)
```

## Integration with Application

### Direct Router Registration

```python
from dtpyfw.api import Application, Router

router = Router(prefix="/api", routes=[...])

app = Application(
    title="My API",
    version="1.0.0",
    routers=[router]  # Register router directly
)
```

### Router with Prefix Override

```python
from dtpyfw.api import Application, Router

# Router has its own prefix
user_router = Router(prefix="/users", routes=[...])

# Application can add additional prefix
app = Application(
    title="My API",
    version="1.0.0",
    routers=[
        ("/api/v1", [user_router])  # Full path: /api/v1/users
    ]
)
```

### Multiple Routers

```python
from dtpyfw.api import Application, Router

public_router = Router(prefix="/public", routes=[...])
auth_router = Router(prefix="/auth", routes=[...])
admin_router = Router(prefix="/admin", routes=[...])

app = Application(
    title="Multi-Module API",
    version="1.0.0",
    routers=[public_router, auth_router, admin_router]
)
```

## Router Organization Patterns

### By Feature

```python
# Organize routers by business feature
authentication_router = Router(prefix="/auth", tags=["Authentication"], routes=[...])
user_management_router = Router(prefix="/users", tags=["User Management"], routes=[...])
billing_router = Router(prefix="/billing", tags=["Billing"], routes=[...])
```

### By Access Level

```python
# Organize by who can access
public_router = Router(prefix="/public", tags=["Public API"], routes=[...])
authenticated_router = Router(prefix="/api", tags=["Authenticated API"], authentications=[auth], routes=[...])
admin_router = Router(prefix="/admin", tags=["Admin API"], authentications=[admin_auth], routes=[...])
```

### By Resource

```python
# Organize by resource type (RESTful style)
users_router = Router(prefix="/users", tags=["Users"], routes=[...])
posts_router = Router(prefix="/posts", tags=["Posts"], routes=[...])
comments_router = Router(prefix="/comments", tags=["Comments"], routes=[...])
```

## Best Practices

1. **Logical Grouping**: Group routes by feature, resource, or access level
2. **Consistent Prefixes**: Use clear, hierarchical URL prefixes
3. **Descriptive Tags**: Use meaningful tags for OpenAPI organization
4. **Shared Auth**: Apply authentication at router level when possible
5. **Version APIs**: Use router prefixes for API versioning
6. **Document Errors**: Define common error responses at router level
7. **Single Responsibility**: Each router should handle one feature/resource
8. **Consistent Naming**: Use consistent naming conventions across routers

## Testing Routers

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

# Create and add router
router = Router(prefix="/api", routes=[...])
app.include_router(router.get_router())

# Test router endpoints
client = TestClient(app)

def test_router_prefix():
    response = client.get("/api/users")
    assert response.status_code == 200

def test_router_authentication():
    # Test without auth
    response = client.get("/api/protected")
    assert response.status_code == 403
    
    # Test with auth
    response = client.get("/api/protected", headers={"X-API-Key": "secret"})
    assert response.status_code == 200
```

## Common Patterns

### Health Check Router

```python
def health():
    return {"status": "healthy"}

def readiness():
    return {"ready": True}

health_router = Router(
    prefix="/health",
    tags=["System"],
    include_in_schema=False,  # Don't show in API docs
    routes=[
        Route(path="/", method=RouteMethod.GET, handler=health),
        Route(path="/ready", method=RouteMethod.GET, handler=readiness),
    ]
)
```

### Documentation Router

```python
def get_api_info():
    return {"version": "1.0.0", "name": "My API"}

def get_changelog():
    return {"changes": [...]}

docs_router = Router(
    prefix="/docs",
    tags=["Documentation"],
    routes=[
        Route(path="/info", method=RouteMethod.GET, handler=get_api_info),
        Route(path="/changelog", method=RouteMethod.GET, handler=get_changelog),
    ]
)
```

## Performance Considerations

- **Minimal Overhead**: Router configuration is done at startup
- **Route Registration**: Routes are registered once when creating the APIRouter
- **Dependency Injection**: FastAPI's dependency injection is highly optimized
- **Authentication**: Shared authentication reduces configuration duplication

## Migration from FastAPI APIRouter

```python
# Before (FastAPI APIRouter)
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
def get_users():
    return []

@router.get("/{user_id}")
def get_user(user_id: int):
    return {}

# After (dtpyfw Router)
from dtpyfw.api import Router, Route, RouteMethod

router = Router(
    prefix="/users",
    tags=["Users"],
    routes=[
        Route(path="/", method=RouteMethod.GET, handler=get_users),
        Route(path="/{user_id}", method=RouteMethod.GET, handler=get_user),
    ]
)
```

## Related Modules

- [`dtpyfw.api.routes.route`](route.md): Individual route configuration
- [`dtpyfw.api.routes.authentication`](authentication.md): Authentication configuration
- [`dtpyfw.api.application`](../application.md): Application configuration
- [`dtpyfw.api.middlewares`](../middlewares/): Middleware components
- FastAPI APIRouter: [FastAPI Router Documentation](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
