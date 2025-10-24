# dtpyfw.api.routes.response

Response helper functions for formatting FastAPI route responses with standardized structure.

## Module Overview

The `response` module provides utility functions for creating standardized API responses in FastAPI applications. It handles success/error wrapping, cache control headers, and supports multiple response types while maintaining consistency across your API.

## Key Features

- **Standardized Response Format**: Consistent success/error response structure
- **Flexible Response Types**: Support for JSON, HTML, and custom response classes
- **Cache Control**: Built-in cache header management
- **Custom Headers**: Per-status-code custom headers support
- **Pydantic Integration**: Automatic serialization of Pydantic models
- **Direct Data Return**: Option to bypass wrapping for specific use cases

## Functions

### return_response

```python
def return_response(
    data: Any,
    status_code: int,
    response_class: Type[Response],
    return_json_directly: bool = False,
    headers: Optional[Dict[int, Dict[Any, Any]]] = None,
    no_cache: bool = True,
) -> Response
```

Builds a FastAPI response with standard success/error wrapping and configurable headers.

**Parameters:**

- **data** (`Any`): The response payload (can be Pydantic model, dict, list, or primitive type)
- **status_code** (`int`): HTTP status code for the response
- **response_class** (`Type[Response]`): The Response class to use (e.g., `JSONResponse`, `HTMLResponse`)
- **return_json_directly** (`bool`, optional): If `True`, skips success/error wrapping and returns data as-is. Defaults to `False`
- **headers** (`Dict[int, Dict[Any, Any]] | None`, optional): Dictionary mapping status codes to header dictionaries. Defaults to `None`
- **no_cache** (`bool`, optional): If `True`, adds cache-control headers to prevent caching. Defaults to `True`

**Returns:**

- `Response`: Configured response object ready to be returned from an endpoint

**Behavior:**

- For status codes < 300: Wraps data in `{"success": true, "data": <data>}`
- For status codes >= 300: Wraps data in `{"success": false, "message": <data>}`
- Automatically serializes Pydantic models using `model_dump(by_alias=True)`
- Non-JSON response classes automatically set `return_json_directly=True`
- Adds no-cache headers by default to prevent unwanted caching

### return_json_response

```python
def return_json_response(
    data: Any,
    status_code: int,
    return_json_directly: bool = False,
    headers: Optional[Dict[int, Dict[Any, Any]]] = None,
    no_cache: bool = True,
) -> Response
```

Convenience wrapper for `return_response` that always returns JSON responses.

**Parameters:**

- **data** (`Any`): The response payload
- **status_code** (`int`): HTTP status code for the response
- **return_json_directly** (`bool`, optional): If `True`, skips success/error wrapping. Defaults to `False`
- **headers** (`Dict[int, Dict[Any, Any]] | None`, optional): Custom headers per status code. Defaults to `None`
- **no_cache** (`bool`, optional): If `True`, adds cache-control headers. Defaults to `True`

**Returns:**

- `Response`: JSON response object

**Purpose:**

Reduces boilerplate by automatically using `JSONResponse` as the response class.

## Usage Examples

### Basic Success Response

```python
from dtpyfw.api.routes.response import return_json_response

@app.get("/users")
def get_users():
    users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    return return_json_response(
        data=users,
        status_code=200
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

### Basic Error Response

```python
from dtpyfw.api.routes.response import return_json_response

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = find_user(user_id)
    if not user:
        return return_json_response(
            data="User not found",
            status_code=404
        )
    
    return return_json_response(
        data=user,
        status_code=200
    )

# Error Response:
# {
#   "success": false,
#   "message": "User not found"
# }
```

### Pydantic Model Response

```python
from pydantic import BaseModel
from dtpyfw.api.routes.response import return_json_response

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = User(id=user_id, name="Alice", email="alice@example.com")
    return return_json_response(
        data=user,
        status_code=200
    )

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

### Direct Data Return (No Wrapping)

```python
from dtpyfw.api.routes.response import return_json_response

@app.get("/health")
def health_check():
    return return_json_response(
        data={"status": "healthy", "version": "1.0.0"},
        status_code=200,
        return_json_directly=True
    )

# Response (no success wrapper):
# {
#   "status": "healthy",
#   "version": "1.0.0"
# }
```

### Custom Headers

```python
from dtpyfw.api.routes.response import return_json_response

@app.get("/download")
def download_file():
    return return_json_response(
        data={"file": "data.csv"},
        status_code=200,
        headers={
            200: {
                "Content-Disposition": "attachment; filename=data.csv",
                "X-Custom-Header": "CustomValue"
            }
        }
    )

# Response includes custom headers:
# Content-Disposition: attachment; filename=data.csv
# X-Custom-Header: CustomValue
```

### Cacheable Response

```python
from dtpyfw.api.routes.response import return_json_response

@app.get("/static-data")
def get_static_data():
    return return_json_response(
        data={"data": "rarely changes"},
        status_code=200,
        no_cache=False,  # Allow caching
        headers={
            200: {
                "Cache-Control": "public, max-age=3600"
            }
        }
    )
```

### HTML Response

```python
from fastapi.responses import HTMLResponse
from dtpyfw.api.routes.response import return_response

@app.get("/page")
def get_page():
    html_content = "<html><body><h1>Hello World</h1></body></html>"
    return return_response(
        data=html_content,
        status_code=200,
        response_class=HTMLResponse
    )

# Returns HTML directly (return_json_directly automatically set to True)
```

### Different Error Status Codes

```python
from dtpyfw.api.routes.response import return_json_response

@app.post("/articles")
def create_article(article: Article):
    if not article.title:
        return return_json_response(
            data="Title is required",
            status_code=400  # Bad Request
        )
    
    if article_exists(article.slug):
        return return_json_response(
            data="Article with this slug already exists",
            status_code=409  # Conflict
        )
    
    if not has_permission():
        return return_json_response(
            data="Insufficient permissions",
            status_code=403  # Forbidden
        )
    
    created = create(article)
    return return_json_response(
        data=created,
        status_code=201  # Created
    )
```

### Per-Status-Code Headers

```python
from dtpyfw.api.routes.response import return_json_response

@app.post("/resources")
def create_resource(resource: dict):
    if not valid(resource):
        return return_json_response(
            data="Invalid resource data",
            status_code=400,
            headers={
                400: {"X-Validation-Failed": "true"}
            }
        )
    
    created = create(resource)
    return return_json_response(
        data=created,
        status_code=201,
        headers={
            201: {
                "Location": f"/resources/{created.id}",
                "X-Resource-Id": str(created.id)
            }
        }
    )
```

## Response Formats

### Success Response (status < 300)

```json
{
  "success": true,
  "data": <your_data>
}
```

**When:**
- Status codes 200-299
- `return_json_directly=False` (default)

### Error Response (status >= 300)

```json
{
  "success": false,
  "message": <error_message>
}
```

**When:**
- Status codes 300+
- `return_json_directly=False` (default)

### Direct Response

```json
<your_data>
```

**When:**
- `return_json_directly=True`
- Non-JSON response classes (HTMLResponse, etc.)

## Default Cache Headers

When `no_cache=True` (default), these headers are added:

```http
Cache-Control: private, no-cache, no-store, must-revalidate, max-age=0, s-maxage=0
Pragma: no-cache
Expires: 0
```

**Purpose:**
- Prevents browser and proxy caching
- Ensures clients always receive fresh data
- Important for authenticated/personalized responses

## Integration with Route Class

The `Route` class automatically uses these functions when `wrapping_handler=True`:

```python
from dtpyfw.api import Route, RouteMethod

def get_users():
    return [{"id": 1, "name": "Alice"}]

route = Route(
    path="/users",
    method=RouteMethod.GET,
    handler=get_users,
    wrapping_handler=True,  # Automatically uses return_response
    status_code=200
)

# Handler returns raw data
# Route wrapper uses return_response to format it
```

## Advanced Patterns

### Conditional Wrapping

```python
from dtpyfw.api.routes.response import return_json_response

@app.get("/data")
def get_data(raw: bool = False):
    data = {"items": [...]}
    
    return return_json_response(
        data=data,
        status_code=200,
        return_json_directly=raw  # Controlled by query param
    )

# GET /data -> {"success": true, "data": {"items": [...]}}
# GET /data?raw=true -> {"items": [...]}
```

### Response Header Mapping

```python
from dtpyfw.api.routes.response import return_json_response

def create_resource(resource: dict):
    # Define headers for different outcomes
    response_headers = {
        201: {
            "Location": f"/resources/{resource['id']}",
            "X-Created": "true"
        },
        400: {
            "X-Validation-Error": "true"
        },
        409: {
            "X-Conflict": "true"
        }
    }
    
    if not valid(resource):
        return return_json_response(
            data="Validation failed",
            status_code=400,
            headers=response_headers
        )
    
    if exists(resource):
        return return_json_response(
            data="Resource already exists",
            status_code=409,
            headers=response_headers
        )
    
    created = create(resource)
    return return_json_response(
        data=created,
        status_code=201,
        headers=response_headers
    )
```

### Custom Response Class

```python
from fastapi.responses import PlainTextResponse
from dtpyfw.api.routes.response import return_response

@app.get("/robots.txt")
def robots():
    content = "User-agent: *\nDisallow: /admin/"
    return return_response(
        data=content,
        status_code=200,
        response_class=PlainTextResponse
    )
```

### Paginated Response

```python
from dtpyfw.api.routes.response import return_json_response

@app.get("/items")
def list_items(page: int = 1, limit: int = 20):
    items = get_items(page, limit)
    total = get_total_count()
    
    return return_json_response(
        data={
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "has_next": (page * limit) < total
        },
        status_code=200
    )

# Response:
# {
#   "success": true,
#   "data": {
#     "items": [...],
#     "page": 1,
#     "limit": 20,
#     "total": 150,
#     "has_next": true
#   }
# }
```

## Testing Response Formatting

```python
from fastapi.testclient import TestClient
from dtpyfw.api.routes.response import return_json_response

def test_success_response_format():
    client = TestClient(app)
    response = client.get("/users")
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "data" in json_data
    assert isinstance(json_data["data"], list)

def test_error_response_format():
    client = TestClient(app)
    response = client.get("/users/999")
    
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert "message" in json_data
    assert json_data["message"] == "User not found"

def test_cache_headers():
    client = TestClient(app)
    response = client.get("/users")
    
    assert "Cache-Control" in response.headers
    assert "no-cache" in response.headers["Cache-Control"]
    assert response.headers["Pragma"] == "no-cache"
```

## Best Practices

1. **Consistent Wrapping**: Use default wrapping for most endpoints to maintain consistency
2. **No-Cache by Default**: Keep `no_cache=True` for dynamic/authenticated endpoints
3. **Direct Return for Standards**: Use `return_json_directly=True` for endpoints following external standards (health checks, webhooks)
4. **Custom Headers Sparingly**: Only add custom headers when necessary (Location, Content-Disposition)
5. **Error Messages**: Provide clear, actionable error messages
6. **Status Codes**: Use appropriate HTTP status codes (200, 201, 400, 404, etc.)
7. **Pydantic Models**: Let the function handle Pydantic serialization automatically

## Common HTTP Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Authenticated but no permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side error |

## Performance Considerations

- **Minimal Overhead**: Response formatting is very fast
- **Pydantic Caching**: Model serialization is optimized by Pydantic
- **Header Generation**: Headers are only added when needed
- **JSON Encoding**: Uses FastAPI's optimized JSON encoding

## Migration Guide

### From Raw Returns

```python
# Before
@app.get("/users")
def get_users():
    return {"users": [...]}

# After
from dtpyfw.api.routes.response import return_json_response

@app.get("/users")
def get_users():
    return return_json_response(
        data={"users": [...]},
        status_code=200
    )
```

### From JSONResponse

```python
# Before
from fastapi.responses import JSONResponse

@app.get("/users")
def get_users():
    return JSONResponse(
        content={"success": True, "data": [...]},
        status_code=200
    )

# After
from dtpyfw.api.routes.response import return_json_response

@app.get("/users")
def get_users():
    return return_json_response(
        data=[...],
        status_code=200
    )
```

## Related Modules

- [`dtpyfw.api.routes.route`](route.md): Route configuration that uses these functions
- [`dtpyfw.api.routes.router`](router.md): Router configuration
- [`dtpyfw.api.schemas.response`](../schemas/response.md): Response schema models
- [`dtpyfw.core.jsonable_encoder`](../../core/jsonable_encoder.md): JSON encoding utilities
- FastAPI Response Models: [FastAPI Response Models](https://fastapi.tiangolo.com/advanced/response-model/)
