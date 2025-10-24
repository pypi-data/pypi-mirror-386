# dtpyfw.api.application

High-level FastAPI application wrapper and configuration helpers for building production-ready microservices.

## Module Overview

The `application` module provides the `Application` class, a comprehensive wrapper around FastAPI that simplifies the configuration and initialization of API applications. It automatically handles middleware setup, CORS configuration, exception handling, sub-application mounting, and router registration using a clean object-oriented interface.

## Key Features

- **Automatic Middleware Configuration**: Pre-configured timer, runtime error handling, and custom middleware support
- **CORS Management**: Built-in CORS configuration with sensible defaults
- **Exception Handling**: Standardized HTTP and validation exception handling
- **Modular Architecture**: Support for nested sub-applications and router groups
- **Session Management**: Optional session middleware integration
- **Compression**: Configurable gzip compression for responses
- **OpenAPI Integration**: Automatic Swagger UI and ReDoc documentation generation

## Classes

### Application

```python
class Application:
    """Wrapper for configuring a FastAPI app using clean OOP structure."""
```

#### Constructor

```python
def __init__(
    self,
    title: str,
    version: str = "*",
    redoc_url: Optional[str] = "/",
    docs_url: Optional[str] = "/swagger",
    applications: Optional[Sequence[Tuple[str, "Application"]]] = None,
    routers: Optional[Union[Sequence[Tuple[str, Sequence[Router]]], Sequence[Router]]] = None,
    gzip_min_size: Optional[int] = None,
    session_middleware_settings: Optional[Dict[str, Any]] = None,
    middlewares: Optional[Sequence[Any]] = None,
    lifespan: Optional[Any] = None,
    cors_settings: Optional[Dict[str, Any]] = None,
    hide_error_messages: bool = True,
) -> None
```

**Parameters:**

- **title** (`str`): Application title displayed in API documentation
- **version** (`str`, optional): Application version string. Defaults to `"*"`
- **redoc_url** (`str | None`, optional): URL path for ReDoc documentation. Defaults to `"/"`
- **docs_url** (`str | None`, optional): URL path for Swagger UI documentation. Defaults to `"/swagger"`
- **applications** (`Sequence[Tuple[str, Application]] | None`, optional): Sequence of (prefix, Application) tuples for mounting sub-applications
- **routers** (`Sequence[Tuple[str, Sequence[Router]]] | Sequence[Router] | None`, optional): Router instances or (prefix, routers) tuples to include
- **gzip_min_size** (`int | None`, optional): Minimum response size in bytes for gzip compression. If `None`, compression is disabled
- **session_middleware_settings** (`Dict[str, Any] | None`, optional): Settings dict for Starlette SessionMiddleware (e.g., `{"secret_key": "...", "max_age": 3600}`)
- **middlewares** (`Sequence[Any] | None`, optional): Additional custom middlewares to register
- **lifespan** (`Any | None`, optional): Lifespan context manager for startup/shutdown events
- **cors_settings** (`Dict[str, Any] | None`, optional): CORS configuration overrides (merged with defaults)
- **hide_error_messages** (`bool`, optional): If `True`, hides detailed error messages in production. Defaults to `True`

**CORS Default Settings:**

The application includes sensible CORS defaults that can be overridden via `cors_settings`:

```python
{
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": [],
    "allow_origin_regex": None,
    "max_age": 600,
}
```

#### Methods

##### get_app()

```python
def get_app(self) -> FastAPI
```

Returns the fully configured FastAPI application instance ready to be served by an ASGI server like Uvicorn or Gunicorn.

**Returns:**
- `FastAPI`: The configured FastAPI application instance

**Example:**
```python
app_wrapper = Application(title="My API", version="1.0.0")
app = app_wrapper.get_app()
```

## Usage Examples

### Basic Application

```python
from dtpyfw.api import Application

# Create a minimal application
app = Application(
    title="My Microservice",
    version="1.0.0"
).get_app()

# Run with: uvicorn main:app --reload
```

### Application with Routers

```python
from dtpyfw.api import Application, Router, Route, RouteMethod

# Define routes
def get_users():
    return {"users": ["Alice", "Bob"]}

def get_user(user_id: int):
    return {"user_id": user_id, "name": "Alice"}

# Create router with routes
user_router = Router(
    prefix="/users",
    tags=["Users"],
    routes=[
        Route(
            path="/",
            method=RouteMethod.GET,
            handler=get_users,
        ),
        Route(
            path="/{user_id}",
            method=RouteMethod.GET,
            handler=get_user,
        ),
    ],
)

# Create application
app = Application(
    title="User Service",
    version="1.0.0",
    routers=[user_router],
).get_app()
```

### Application with Custom Middleware

```python
from dtpyfw.api import Application
from fastapi import Request

# Custom middleware
async def custom_middleware(request: Request, call_next):
    # Add custom header to all responses
    response = await call_next(request)
    response.headers["X-Custom-Header"] = "MyValue"
    return response

# Create application with middleware
app = Application(
    title="My API",
    version="1.0.0",
    middlewares=[custom_middleware],
).get_app()
```

### Application with Nested Sub-Applications

```python
from dtpyfw.api import Application

# Create sub-applications
admin_app = Application(
    title="Admin API",
    version="1.0.0",
)

public_app = Application(
    title="Public API",
    version="1.0.0",
)

# Mount sub-applications
main_app = Application(
    title="Main API",
    version="1.0.0",
    applications=[
        ("/admin", admin_app),
        ("/public", public_app),
    ],
).get_app()
```

### Application with CORS Configuration

```python
from dtpyfw.api import Application

app = Application(
    title="CORS-Enabled API",
    version="1.0.0",
    cors_settings={
        "allow_origins": ["https://example.com", "https://app.example.com"],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Authorization", "Content-Type"],
        "max_age": 3600,
    },
).get_app()
```

### Application with Gzip Compression

```python
from dtpyfw.api import Application

# Enable gzip compression for responses larger than 1KB
app = Application(
    title="Compressed API",
    version="1.0.0",
    gzip_min_size=1024,
).get_app()
```

### Application with Session Management

```python
from dtpyfw.api import Application

app = Application(
    title="Session-Enabled API",
    version="1.0.0",
    session_middleware_settings={
        "secret_key": "your-secret-key-here",
        "session_cookie": "session_id",
        "max_age": 3600,  # 1 hour
        "https_only": True,
    },
).get_app()
```

### Application with Lifespan Events

```python
from contextlib import asynccontextmanager
from dtpyfw.api import Application

@asynccontextmanager
async def lifespan(app):
    # Startup: initialize database connection
    print("Starting up...")
    db_connection = await connect_to_database()
    yield
    # Shutdown: close database connection
    print("Shutting down...")
    await db_connection.close()

app = Application(
    title="Lifecycle API",
    version="1.0.0",
    lifespan=lifespan,
).get_app()
```

### Complex Multi-Module Application

```python
from dtpyfw.api import Application, Router, Route, RouteMethod
from dtpyfw.api.routes.authentication import Auth, AuthType

# Define authentication
api_key_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value="secret-api-key",
)

# Define routers for different modules
user_router = Router(
    prefix="/users",
    tags=["Users"],
    authentications=[api_key_auth],
    routes=[...],
)

product_router = Router(
    prefix="/products",
    tags=["Products"],
    authentications=[api_key_auth],
    routes=[...],
)

# Group routers under /api/v1 prefix
app = Application(
    title="E-Commerce API",
    version="1.0.0",
    routers=[
        ("/api/v1", [user_router, product_router]),
    ],
    cors_settings={
        "allow_origins": ["https://shop.example.com"],
        "allow_credentials": True,
    },
    gzip_min_size=1024,
    hide_error_messages=True,
).get_app()
```

## Automatic Middleware Registration

The `Application` class automatically registers the following middlewares in order:

1. **GZipMiddleware** (if `gzip_min_size` is specified): Compresses responses
2. **Custom Middlewares** (if provided): User-defined middlewares
3. **Timer Middleware**: Adds `X-Process-Time` header with request processing time
4. **Runtime Middleware**: Catches and handles all exceptions with logging
5. **SessionMiddleware** (if `session_middleware_settings` is provided): Manages user sessions
6. **CORSMiddleware** (if `cors_settings` is provided): Handles CORS requests

## Exception Handling

The application automatically registers handlers for:

- **HTTP Exceptions** (`StarletteHTTPException`): Returns formatted JSON error responses with proper status codes
- **Validation Errors** (`RequestValidationError`): Returns detailed validation error information with 422 status code

All exceptions are logged using the framework's logging system for monitoring and debugging.

## OpenAPI Documentation

By default, the application exposes:

- **Swagger UI**: Available at `/swagger` (configurable via `docs_url`)
- **ReDoc**: Available at `/` (configurable via `redoc_url`)

To disable documentation in production:

```python
app = Application(
    title="Production API",
    version="1.0.0",
    docs_url=None,  # Disable Swagger UI
    redoc_url=None,  # Disable ReDoc
).get_app()
```

## Best Practices

1. **Version Your API**: Always specify a version for your application
2. **Hide Errors in Production**: Keep `hide_error_messages=True` in production environments
3. **Use Environment Variables**: Load sensitive configuration (API keys, secrets) from environment variables
4. **Configure CORS Properly**: Restrict `allow_origins` to specific domains in production
5. **Enable Compression**: Use `gzip_min_size` for APIs serving large responses
6. **Organize with Routers**: Group related endpoints using `Router` objects
7. **Document Everything**: Use route descriptions, summaries, and tags for clear API documentation

## Integration with Other Framework Components

The `Application` class integrates seamlessly with other dtpyfw components:

- **Routers**: Use `dtpyfw.api.routes.Router` to organize endpoints
- **Routes**: Use `dtpyfw.api.routes.Route` to define individual endpoints
- **Authentication**: Use `dtpyfw.api.routes.authentication.Auth` for API key validation
- **Middlewares**: Use built-in middlewares from `dtpyfw.api.middlewares`
- **Schemas**: Use response schemas from `dtpyfw.api.schemas`
- **Logging**: Automatic integration with `dtpyfw.log` for error tracking

## Related Modules

- [`dtpyfw.api.routes.router`](routes/router.md): Router configuration
- [`dtpyfw.api.routes.route`](routes/route.md): Individual route definition
- [`dtpyfw.api.middlewares`](middlewares/): Middleware components
- [`dtpyfw.api.schemas`](schemas/): Response and request schemas
