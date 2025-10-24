# dtpyfw.api.routes.authentication

API route authentication configuration and validation utilities for FastAPI applications.

## Module Overview

The `authentication` module provides a flexible authentication system for securing API routes. It supports multiple authentication transport mechanisms (headers and query parameters) and includes built-in validators for API key authentication.

## Key Features

- **Multiple Transport Types**: Support for header-based and query parameter authentication
- **Runtime Validation**: Validates credentials on every request
- **OpenAPI Integration**: Automatically documents authentication requirements in Swagger/ReDoc
- **Flexible Configuration**: Easy-to-configure authentication schemes
- **Type Safety**: Uses dataclasses and enums for configuration
- **FastAPI Dependencies**: Integrates seamlessly with FastAPI's dependency injection

## Enumerations

### AuthType

```python
class AuthType(Enum):
    """Authentication transport mechanisms supported by the framework."""
```

**Values:**

- **HEADER**: `"header"` - Authentication credentials transmitted via HTTP headers
- **QUERY**: `"query"` - Authentication credentials transmitted via query parameters

## Classes

### Auth

```python
@dataclass
class Auth:
    """Configuration for API route authentication requirements."""
```

A dataclass that specifies the authentication mechanism, credential location, and expected value for validating API requests.

**Attributes:**

- **auth_type** (`AuthType`): The authentication transport mechanism (HEADER or QUERY)
- **header_key** (`str | None`): The name of the header or query parameter containing the authentication token. Defaults to `None`
- **real_value** (`str | None`): The expected value of the authentication credential. Defaults to `None`

**Example:**

```python
from dtpyfw.api.routes.authentication import Auth, AuthType

# Header-based authentication
api_key_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value="secret-api-key-12345"
)

# Query parameter authentication
query_auth = Auth(
    auth_type=AuthType.QUERY,
    header_key="api_key",
    real_value="secret-api-key-12345"
)
```

### HeaderAuthChecker

```python
class HeaderAuthChecker:
    """FastAPI dependency that validates authentication via request headers."""
```

A callable class that validates incoming requests contain the correct authentication header with the expected value.

#### Constructor

```python
def __init__(self, key: str, real_value: str)
```

**Parameters:**

- **key** (`str`): The name of the HTTP header containing the authentication token
- **real_value** (`str`): The expected value of the authentication header

#### \_\_call\_\_

```python
def __call__(self, request: Request) -> None
```

Validates that the request contains the correct authentication header.

**Parameters:**

- **request** (`Request`): The incoming FastAPI request

**Returns:**

- `None`

**Raises:**

- `RequestException` (403): If the header is missing or incorrect with message "Wrong credential."

### QueryAuthChecker

```python
class QueryAuthChecker:
    """FastAPI dependency that validates authentication via query parameters."""
```

A callable class that validates incoming requests contain the correct authentication query parameter with the expected value.

#### Constructor

```python
def __init__(self, key: str, real_value: str)
```

**Parameters:**

- **key** (`str`): The name of the query parameter containing the authentication token
- **real_value** (`str`): The expected value of the authentication parameter

#### \_\_call\_\_

```python
def __call__(self, request: Request) -> None
```

Validates that the request contains the correct authentication query parameter.

**Parameters:**

- **request** (`Request`): The incoming FastAPI request

**Returns:**

- `None`

**Raises:**

- `RequestException` (403): If the parameter is missing or incorrect with message "Wrong credential."

## Functions

### auth_data_class_to_dependency

```python
def auth_data_class_to_dependency(authentication: Auth) -> list[Any]
```

Converts an `Auth` configuration into a list of FastAPI dependencies that enforce authentication and document it in OpenAPI.

**Parameters:**

- **authentication** (`Auth`): Authentication configuration object

**Returns:**

- `list[Any]`: List of FastAPI dependency objects for endpoint signatures

**Behavior:**

- **For AuthType.HEADER**: Returns two dependencies:
  1. `Depends(HeaderAuthChecker(...))` - Runtime validator for header value
  2. `Depends(APIKeyHeader(name=...))` - OpenAPI documentation integration
  
- **For AuthType.QUERY**: Returns two dependencies:
  1. `Depends(QueryAuthChecker(...))` - Runtime validator for query parameter
  2. `Depends(APIKeyQuery(name=...))` - OpenAPI documentation integration
  
- **For other types**: Returns empty list

**Raises:**

- `ValueError`: If `header_key` or `real_value` is `None` when auth_type is HEADER or QUERY. This ensures misconfigured authentication fails at startup rather than leaving routes unprotected.

**Why Two Dependencies?**

The function returns both a checker and an APIKey dependency to achieve:
1. **Runtime Validation**: The checker enforces credential validation
2. **OpenAPI Documentation**: The APIKey dependency registers the requirement in Swagger/ReDoc, showing developers what credentials are needed

## Usage Examples

### Basic Header Authentication

```python
from dtpyfw.api import Router, Route, RouteMethod
from dtpyfw.api.routes.authentication import Auth, AuthType

# Define authentication
api_key_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value="my-secret-key"
)

# Create protected route
def get_protected_data():
    return {"data": "sensitive information"}

# Apply authentication to route
protected_route = Route(
    path="/protected",
    method=RouteMethod.GET,
    handler=get_protected_data,
    authentications=[api_key_auth]
)

# Create router with the route
router = Router(
    prefix="/api",
    routes=[protected_route]
)
```

**Request Example:**

```bash
# Correct authentication
curl -X GET "https://api.example.com/api/protected" \
  -H "X-API-Key: my-secret-key"

# Response: 200 OK
{"success": true, "data": {"data": "sensitive information"}}

# Wrong or missing authentication
curl -X GET "https://api.example.com/api/protected" \
  -H "X-API-Key: wrong-key"

# Response: 403 Forbidden
{"success": false, "message": "Wrong credential."}
```

### Query Parameter Authentication

```python
from dtpyfw.api.routes.authentication import Auth, AuthType

# Define query authentication
query_auth = Auth(
    auth_type=AuthType.QUERY,
    header_key="api_key",
    real_value="secret-key-12345"
)

def get_data():
    return {"data": "information"}

route = Route(
    path="/data",
    method=RouteMethod.GET,
    handler=get_data,
    authentications=[query_auth]
)
```

**Request Example:**

```bash
# Correct authentication
curl -X GET "https://api.example.com/data?api_key=secret-key-12345"

# Response: 200 OK
{"success": true, "data": {"data": "information"}}

# Wrong authentication
curl -X GET "https://api.example.com/data?api_key=wrong-key"

# Response: 403 Forbidden
{"success": false, "message": "Wrong credential."}
```

### Router-Level Authentication

Apply authentication to all routes in a router:

```python
from dtpyfw.api import Router, Route, RouteMethod
from dtpyfw.api.routes.authentication import Auth, AuthType

# Authentication config
api_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="Authorization",
    real_value="Bearer secret-token"
)

# All routes in this router require authentication
secure_router = Router(
    prefix="/secure",
    tags=["Secure API"],
    authentications=[api_auth],
    routes=[
        Route(path="/users", method=RouteMethod.GET, handler=get_users),
        Route(path="/orders", method=RouteMethod.GET, handler=get_orders),
        Route(path="/reports", method=RouteMethod.GET, handler=get_reports),
    ]
)
```

### Environment-Based Authentication

```python
import os
from dtpyfw.api.routes.authentication import Auth, AuthType

# Load API key from environment variable
API_KEY = os.getenv("API_KEY", "default-key-for-dev")

auth_config = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value=API_KEY
)

# Use in routes...
```

### Multiple Authentication Methods

```python
from dtpyfw.api.routes.authentication import Auth, AuthType

# Define multiple auth methods
header_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value="key-123"
)

backup_auth = Auth(
    auth_type=AuthType.QUERY,
    header_key="token",
    real_value="token-456"
)

# Route with multiple authentication options
# Note: Both will be checked (AND logic, not OR)
route = Route(
    path="/data",
    method=RouteMethod.GET,
    handler=get_data,
    authentications=[header_auth, backup_auth]
)
```

### Using with Manual Dependencies

```python
from fastapi import Depends
from dtpyfw.api.routes.authentication import auth_data_class_to_dependency, Auth, AuthType

auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value="secret"
)

# Get authentication dependencies
auth_deps = auth_data_class_to_dependency(auth)

@app.get("/manual-auth", dependencies=auth_deps)
def protected_endpoint():
    return {"status": "authenticated"}
```

## OpenAPI/Swagger Integration

Authentication requirements are automatically documented in your API documentation:

### Swagger UI Display

When you define authentication:

```python
auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value="secret"
)
```

Swagger UI will display:
- A lock icon on protected endpoints
- Required header: `X-API-Key` (string)
- Description: "API key header 'X-API-Key' required for access."
- An "Authorize" button to enter credentials for testing

### Testing in Swagger UI

1. Click the "Authorize" button in Swagger UI
2. Enter your API key in the `X-API-Key` field
3. Click "Authorize"
4. Test protected endpoints directly from the documentation

## Error Responses

### Wrong Credential

```json
{
  "success": false,
  "message": "Wrong credential."
}
```

**HTTP Status:** 403 Forbidden

**Triggered When:**
- Authentication header/parameter is missing
- Authentication value doesn't match expected value

## Configuration Validation

The module includes startup validation to prevent misconfiguration:

```python
# This will raise ValueError at startup
invalid_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key=None,  # Missing!
    real_value="secret"
)

# Error message:
# ValueError: Authentication misconfiguration: header_key cannot be None
# for AuthType.HEADER. This usually indicates a missing environment variable
# or incorrect Auth object initialization. Routes with incomplete
# authentication would be left unprotected.
```

**Benefits:**
- Fails fast at application startup
- Prevents accidentally deploying unprotected routes
- Clear error messages about what's missing

## Security Best Practices

### 1. Use Environment Variables

```python
import os

auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value=os.environ["API_KEY"]  # Never hardcode!
)
```

### 2. Rotate Keys Regularly

```python
# Implement key rotation
current_keys = [
    os.getenv("API_KEY_CURRENT"),
    os.getenv("API_KEY_PREVIOUS")  # Grace period for old key
]

# Check against multiple keys
def validate_api_key(api_key: str) -> bool:
    return api_key in current_keys
```

### 3. Use HTTPS Only

```python
# API keys should only be transmitted over HTTPS
# Configure your deployment to enforce SSL/TLS
```

### 4. Different Keys per Environment

```python
# Development
DEV_KEY = "dev-key-easy-to-remember"

# Staging
STAGING_KEY = os.getenv("STAGING_API_KEY")

# Production
PROD_KEY = os.getenv("PROD_API_KEY")  # Strong, random key

auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value=PROD_KEY if is_production else DEV_KEY
)
```

### 5. Rate Limiting

Combine authentication with rate limiting to prevent brute force:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/protected")
@limiter.limit("5/minute")
def protected_endpoint():
    return {"data": "sensitive"}
```

## Advanced Patterns

### Per-Route Authentication

```python
# Public routes
public_router = Router(
    prefix="/public",
    authentications=[],  # No authentication
    routes=[...]
)

# Protected routes
protected_router = Router(
    prefix="/protected",
    authentications=[api_key_auth],  # Require API key
    routes=[...]
)
```

### Custom Authentication Logic

For more complex authentication (JWT, OAuth, etc.), use FastAPI's native security:

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Custom JWT validation logic
    token = credentials.credentials
    # Validate token...
    return user_from_token(token)

@app.get("/jwt-protected")
def protected(user = Depends(verify_token)):
    return {"user": user}
```

### Conditional Authentication

```python
from typing import Optional

def optional_auth(api_key: Optional[str] = Header(None, alias="X-API-Key")):
    if api_key == "secret":
        return {"authenticated": True, "level": "full"}
    else:
        return {"authenticated": False, "level": "limited"}

@app.get("/flexible")
def flexible_endpoint(auth = Depends(optional_auth)):
    if auth["authenticated"]:
        return {"data": "full dataset"}
    else:
        return {"data": "limited dataset"}
```

## Testing Authentication

```python
from fastapi.testclient import TestClient

def test_protected_endpoint_with_auth():
    client = TestClient(app)
    
    # With correct authentication
    response = client.get(
        "/protected",
        headers={"X-API-Key": "secret-key"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_protected_endpoint_without_auth():
    client = TestClient(app)
    
    # Without authentication
    response = client.get("/protected")
    assert response.status_code == 403
    assert response.json()["success"] is False
    assert "credential" in response.json()["message"].lower()

def test_protected_endpoint_wrong_auth():
    client = TestClient(app)
    
    # With wrong authentication
    response = client.get(
        "/protected",
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 403
```

## Migration from Other Auth Systems

### From Basic Auth

```python
# Before (Basic Auth)
from fastapi.security import HTTPBasic

# After (dtpyfw Auth)
from dtpyfw.api.routes.authentication import Auth, AuthType

auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="Authorization",
    real_value="Basic base64encodedcredentials"
)
```

### From Custom Middleware

```python
# Before (Custom middleware)
@app.middleware("http")
async def auth_middleware(request, call_next):
    if request.headers.get("X-API-Key") != "secret":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)

# After (dtpyfw Auth)
auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value="secret"
)
# Apply to routers/routes
```

## Performance Considerations

- **Minimal Overhead**: Header/query parameter validation is extremely fast
- **No Database Calls**: Simple string comparison, no external lookups
- **Caching**: Consider caching complex authentication logic
- **Connection Pooling**: For database-backed auth, use connection pools

## Related Modules

- [`dtpyfw.api.routes.route`](route.md): Route configuration
- [`dtpyfw.api.routes.router`](router.md): Router configuration
- [`dtpyfw.api.middlewares.user`](../middlewares/user.md): User authentication
- [`dtpyfw.api.middlewares.permission`](../middlewares/permission.md): Permission checking
- [`dtpyfw.core.exception`](../../core/exception.md): RequestException
