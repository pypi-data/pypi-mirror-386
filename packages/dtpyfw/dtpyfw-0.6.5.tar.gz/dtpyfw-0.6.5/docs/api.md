# API Sub-Package

**DealerTower Python Framework** — FastAPI helpers for building lightweight microservices with consistent conventions.

## Overview

The `api` package wraps common FastAPI patterns:

- **Application Factory**: The `Application` class for configuring middleware, CORS, documentation routes, and mounting sub-applications or routers.
- **Declarative Routing**: `Route` and `Router` classes to define endpoints with optional authentication and automatic response formatting.
- **Authentication Utilities**: Integration with `APIKeyHeader` and `APIKeyQuery` for easy and secure endpoint protection.
- **Built-in Middleware**: A suite of middleware for runtime logging, standardized exception handling, and optional user-agent restrictions.
- **Response Helpers**: Utilities for returning standardized JSON payloads with cache control headers.
- **Pydantic Schemas**: A collection of reusable schemas for common API patterns like sorting, pagination, and filtering.

## Installation

To use the API utilities, install `dtpyfw` with the `api` extra:

```bash
pip install dtpyfw[api]
```

---

## `application.py` — Application Factory

The `Application` class is a high-level wrapper around `FastAPI` that simplifies the setup of a new service.

```python
from dtpyfw.api.application import Application
from dtpyfw.api.routes.router import Router
from .my_routes import my_route

# Create a router
my_router = Router(prefix="/api", routes=[my_route])

# Create the main application
main_app = Application(
    title="My DealerTower Service",
    version="1.0.0",
    routers=[my_router],
    cors_settings={"allow_origins": ["https://my-frontend.dealertower.com"]},
    only_internal_user_agent=True,  # Optional: Restrict to internal services
)

# Get the configured FastAPI app instance
app = main_app.get_app()
```

### Key Parameters

- `title`, `version`, `docs_url`, `redoc_url`: Standard FastAPI metadata.
- `routers`: A list of `Router` objects to include in the application.
- `applications`: A list of other `Application` instances to mount as sub-apps.
- `middlewares`: A list of additional custom middleware to apply.
- `cors_settings`: A dictionary to configure CORS behavior.
- `only_internal_user_agent`: If `True`, enables a middleware that restricts access to clients with the `DealerTower-Service/1.0` user agent.
- `hide_error_messages`: If `True` (default), generic error messages are shown in production to avoid leaking implementation details.

---

## `middlewares` — Built-in Middleware

The `api` package includes several pre-built middlewares that are automatically configured by the `Application` class.

- **`runtime.py`**: Catches all unhandled exceptions, logs them using `dtpyfw.log.footprint`, and returns a standardized 500 error response.
- **`http_exception.py`**: Handles FastAPI's `HTTPException` and formats it into a consistent JSON error response.
- **`validation_exception.py`**: Catches `RequestValidationError` (from Pydantic) and transforms complex validation errors into a single, readable error message.
- **`timer.py`**: Adds a `X-Process-Time` header to every response, indicating the request processing time.
- **`user_agent.py`**: Provides the `InternalUserAgentRestriction` middleware to lock down endpoints for internal service-to-service communication.

---

## `routes` — Routing and Authentication

### `Route`

The `Route` class defines a single endpoint with its handler, method, authentication requirements, and other metadata.

```python
from dtpyfw.api.routes.route import Route, RouteMethod
from dtpyfw.api.routes.authentication import Auth, AuthType

# Define an authentication requirement
api_key_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-KEY",
    real_value="my-secret-key"
)

# Define a route
get_items_route = Route(
    path="/items",
    method=RouteMethod.GET,
    handler=my_items_handler,
    authentications=[api_key_auth],
    tags=["Items"],
    summary="Get a list of items",
)
```

- `handler`: The function (sync or async) that processes the request.
- `authentications`: A list of `Auth` objects that protect the endpoint.
- `response_model`: The Pydantic model for the response.
- `errors`: A dictionary to define expected error responses for the OpenAPI schema.

### `Router`

The `Router` class groups multiple `Route` objects under a common prefix and can apply shared settings like tags or authentication.

```python
from dtpyfw.api.routes.router import Router

items_router = Router(
    prefix="/items",
    routes=[get_items_route, create_item_route],
    tags=["Items"],
    # This authentication will apply to all routes in this router
    authentications=[admin_only_auth],
)
```

### Authentication Configuration

The `Auth` class provides a fail-fast approach to authentication configuration, ensuring that misconfigured routes are detected at application startup rather than silently leaving endpoints unprotected.

#### Configuration Requirements

When using `Auth` with either `AuthType.HEADER` or `AuthType.QUERY`, both `header_key` and `real_value` **must be non-None values**. If either is `None`, a `ValueError` will be raised immediately when the route is being configured.

```python
from dtpyfw.api.routes.authentication import Auth, AuthType
from dtpyfw.core.env import Env

# ❌ INCORRECT - Will raise ValueError if API_KEY is missing
api_key = Env.get("API_KEY")  # Returns None if not set
bad_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value=api_key,  # None value!
)
# ValueError: Authentication misconfiguration: real_value cannot be None...

# ✅ CORRECT - Provide a default or validate before use
api_key = Env.get("API_KEY", "default-dev-key")
good_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value=api_key,
)

# ✅ CORRECT - Explicitly check and fail early
api_key = Env.get("API_KEY")
if not api_key:
    raise RuntimeError("API_KEY environment variable is required")
good_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value=api_key,
)
```

#### Why Fail-Fast?

Previously, if `header_key` or `real_value` was `None`, the authentication would silently be skipped, leaving the endpoint **publicly accessible without any error message**. This was dangerous because:

- Missing environment variables would go unnoticed
- Typos in configuration wouldn't be caught
- Protected routes could accidentally become public

The current implementation raises a `ValueError` with a descriptive message indicating:
- Which fields are `None`
- That this likely indicates a missing environment variable
- That the route would otherwise be left unprotected

#### Common Scenarios

**Using Environment Variables:**
```python
import os
from dtpyfw.api.routes.authentication import Auth, AuthType

# Load from environment with validation
api_key = os.getenv("ADMIN_API_KEY")
if not api_key:
    raise ValueError("ADMIN_API_KEY must be set in environment")

admin_auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-Admin-Key",
    real_value=api_key,
)
```

**Different Keys per Environment:**
```python
from dtpyfw.core.env import Env

# Register and load environment variables
Env.register(["API_KEY_PROD", "API_KEY_DEV", "ENVIRONMENT"])
Env.load_file(".env")

environment = Env.get("ENVIRONMENT", "development")
api_key = Env.get("API_KEY_PROD" if environment == "production" else "API_KEY_DEV")

if not api_key:
    raise RuntimeError(f"API key not configured for {environment} environment")

auth = Auth(
    auth_type=AuthType.HEADER,
    header_key="X-API-Key",
    real_value=api_key,
)
```

---

## `schemas` — Pydantic Models

The `schemas` module provides a set of reusable Pydantic models for common API patterns.

### Request Schemas

- **`models.py`**:
  - `Sorting`: Defines a sorting rule with `sort_by` and `order_by` fields.
  - `SearchPayload`: A base model for search requests, including pagination (`page`, `items_per_page`) and a list of `Sorting` rules.
- **`filters.py`**:
  - `NumberRange`, `TimeRange`, `DateRange`: Models for defining min/max filters for numerical, time, and date values.

### Response Schemas

- **`response.py`**:
  - `SuccessResponse[T]`: A generic model that wraps successful data payloads in a `{"success": True, "data": ...}` structure.
  - `FailedResponse`: A model for error responses, providing `{"success": False, "message": "..."}`.
  - `ResponseBase`: The base for both success and failed responses, containing only the `success` field.

### Example Usage

You can extend these base schemas to create specific request payloads for your application.

```python
from enum import Enum
from dtpyfw.api.schemas.models import SearchPayload, Sorting
from dtpyfw.api.schemas.filters import DateRange

class UserSortBy(str, Enum):
    NAME = "name"
    CREATED_AT = "created_at"

class UserSorting(Sorting):
    sort_by: UserSortBy = UserSortBy.NAME

class UserSearchPayload(SearchPayload):
    sorting: list[UserSorting] = [UserSorting()]
    status: list[str] = []
    registration_date: DateRange | None = None
```

---

*This documentation covers the `api` sub-package of the DealerTower Python Framework.*

---
