# HTTP Request Utilities

## Overview

The `dtpyfw.core.request` module provides HTTP request utilities with standardized error handling, authentication, caching control, and logging. This module wraps the `requests` library with DealerTower-specific conventions for making reliable HTTP calls to internal and external services.

## Module Path

```python
from dtpyfw.core.request import request
```

## Dependencies

This module requires the `requests` library, which is automatically installed with `dtpyfw[core]`.

## Functions

### `request(...) -> Union[requests.Response, Any, str, None]`

Send an HTTP request with standardized headers, authentication, and error handling.

**Description:**

Makes HTTP requests with configurable authentication, caching headers, and response handling. Supports internal service response format with 'success' and 'data' fields. Automatically logs errors to footprint for debugging and monitoring.

**Parameters:**

- **method** (`str`): HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
- **path** (`str`): Endpoint path relative to host
- **host** (`Optional[str]`, optional): Base URL of the service. Returns None if not provided
- **auth_key** (`Optional[str]`, optional): Key for authentication header or parameter
- **auth_value** (`Optional[str]`, optional): Value for authentication
- **auth_type** (`Optional[str]`, optional): Where to place auth - 'headers' or 'params'
- **disable_caching** (`bool`, optional): If True, sets no-cache headers. Defaults to True
- **full_return** (`bool`, optional): If True, returns the raw Response object. Defaults to False
- **json_return** (`bool`, optional): If True, attempts to parse JSON response. Defaults to True
- **internal_service** (`bool`, optional): If True, expects response format with 'success' and 'data'. Defaults to True
- **add_dt_user_agent** (`bool`, optional): If True, includes DealerTower user-agent header. Defaults to True
- **push_logs** (`bool`, optional): If True, sends errors to footprint logging system. Defaults to True
- ****kwargs** (`Any`): Additional arguments passed directly to `requests.request()` (e.g., `data`, `json`, `params`, `headers`, `timeout`, etc.)

**Returns:**

- **`requests.Response`**: If `full_return=True`
- **`Any`**: If `internal_service=True` and successful, returns the `data` field
- **`dict`**: If `json_return=True` and `internal_service=False`, returns parsed JSON
- **`str`**: If `json_return=False`, returns response text
- **`None`**: If host is not provided

**Raises:**

- **`RequestException`**: On network errors, JSON parsing failures, or service errors

**Example:**

```python
from dtpyfw.core.request import request

# Simple GET request
response = request(
    method="GET",
    path="/api/users/123",
    host="https://api.example.com"
)

# POST request with authentication
response = request(
    method="POST",
    path="/api/users",
    host="https://api.example.com",
    auth_key="Authorization",
    auth_value="Bearer YOUR_TOKEN",
    auth_type="headers",
    json={"name": "John Doe", "email": "john@example.com"}
)

# Get full response object
response = request(
    method="GET",
    path="/health",
    host="https://api.example.com",
    full_return=True
)
print(response.status_code, response.headers)
```

## Complete Usage Examples

### 1. External API Integration

```python
from dtpyfw.core.request import request
from dtpyfw.core.exception import RequestException

class ExternalAPIClient:
    def __init__(self, api_key: str):
        self.base_url = "https://api.external-service.com"
        self.api_key = api_key
    
    def get_user(self, user_id: int) -> dict:
        """Fetch user from external API."""
        try:
            return request(
                method="GET",
                path=f"/v1/users/{user_id}",
                host=self.base_url,
                auth_key="X-API-Key",
                auth_value=self.api_key,
                auth_type="headers",
                internal_service=False,  # External service doesn't use our format
                timeout=10
            )
        except RequestException as e:
            print(f"Failed to fetch user: {e.message}")
            raise
    
    def create_user(self, user_data: dict) -> dict:
        """Create user in external API."""
        return request(
            method="POST",
            path="/v1/users",
            host=self.base_url,
            auth_key="X-API-Key",
            auth_value=self.api_key,
            auth_type="headers",
            json=user_data,
            internal_service=False
        )

# Usage
client = ExternalAPIClient(api_key="your-api-key")
user = client.get_user(123)
new_user = client.create_user({"name": "Alice", "email": "alice@example.com"})
```

### 2. Internal Microservice Communication

```python
from dtpyfw.core.request import request
from dtpyfw.core.env import Env

class UserService:
    def __init__(self):
        self.service_url = Env.get("USER_SERVICE_URL", "http://user-service:8000")
        self.service_token = Env.get("SERVICE_TOKEN")
    
    def get_user_profile(self, user_id: int) -> dict:
        """Fetch user profile from internal service."""
        # internal_service=True expects {success: bool, data: any} format
        return request(
            method="GET",
            path=f"/internal/users/{user_id}/profile",
            host=self.service_url,
            auth_key="X-Service-Token",
            auth_value=self.service_token,
            auth_type="headers",
            internal_service=True  # Extracts 'data' field automatically
        )
    
    def update_user_profile(self, user_id: int, updates: dict) -> dict:
        """Update user profile."""
        return request(
            method="PATCH",
            path=f"/internal/users/{user_id}/profile",
            host=self.service_url,
            auth_key="X-Service-Token",
            auth_value=self.service_token,
            auth_type="headers",
            json=updates,
            internal_service=True
        )

# Usage
service = UserService()
profile = service.get_user_profile(123)
updated = service.update_user_profile(123, {"bio": "New bio"})
```

### 3. File Upload

```python
from dtpyfw.core.request import request

def upload_file(file_path: str, upload_url: str, auth_token: str):
    """Upload file to server."""
    with open(file_path, 'rb') as f:
        files = {'file': f}
        
        response = request(
            method="POST",
            path="/upload",
            host=upload_url,
            auth_key="Authorization",
            auth_value=f"Bearer {auth_token}",
            auth_type="headers",
            files=files,
            internal_service=False,
            json_return=True
        )
    
    return response

# Usage
result = upload_file("/path/to/file.pdf", "https://upload.example.com", "token")
```

### 4. Retry Logic with Request

```python
from dtpyfw.core.request import request
from dtpyfw.core.retry import retry_wrapper
from dtpyfw.core.exception import RequestException

@retry_wrapper(max_attempts=3, sleep_time=2, backoff=2)
def fetch_with_retry(url: str, path: str) -> dict:
    """Fetch data with automatic retry on failure."""
    return request(
        method="GET",
        path=path,
        host=url,
        internal_service=False,
        timeout=5
    )

# Usage - will retry up to 3 times on failure
try:
    data = fetch_with_retry("https://api.example.com", "/data")
except RequestException as e:
    print(f"Failed after retries: {e.message}")
```

### 5. Query Parameters

```python
from dtpyfw.core.request import request

def search_products(query: str, category: str = None, page: int = 1):
    """Search products with query parameters."""
    params = {"q": query, "page": page}
    if category:
        params["category"] = category
    
    return request(
        method="GET",
        path="/api/products/search",
        host="https://api.example.com",
        params=params,
        internal_service=False
    )

# Usage
products = search_products("laptop", category="electronics", page=2)
```

### 6. Custom Headers

```python
from dtpyfw.core.request import request

def api_call_with_headers():
    """Make API call with custom headers."""
    return request(
        method="POST",
        path="/api/data",
        host="https://api.example.com",
        headers={
            "X-Request-ID": "unique-request-id",
            "X-Client-Version": "1.0.0",
            "Accept-Language": "en-US"
        },
        json={"data": "value"},
        internal_service=False
    )
```

### 7. Handling Different Response Types

```python
from dtpyfw.core.request import request

# Get JSON response
json_data = request(
    method="GET",
    path="/api/data",
    host="https://api.example.com",
    json_return=True,
    internal_service=False
)

# Get text response (HTML, XML, etc.)
html_content = request(
    method="GET",
    path="/page.html",
    host="https://example.com",
    json_return=False
)

# Get full Response object
response = request(
    method="GET",
    path="/api/data",
    host="https://api.example.com",
    full_return=True
)
print(response.status_code)
print(response.headers)
print(response.content)
```

## Internal Service Response Format

When `internal_service=True` (default), the function expects responses in this format:

```python
# Successful response
{
    "success": True,
    "data": {
        "user_id": 123,
        "name": "John Doe"
    }
}

# Error response
{
    "success": False,
    "message": "User not found"
}
```

The function automatically extracts the `data` field on success or raises `RequestException` on failure.

## Caching Control

By default, `disable_caching=True` adds these headers:

```python
{
    "Cache-Control": "private, no-cache, no-store, must-revalidate, max-age=0, s-maxage=0",
    "Pragma": "no-cache",
    "Expires": "0"
}
```

To allow caching:

```python
response = request(
    method="GET",
    path="/api/data",
    host="https://api.example.com",
    disable_caching=False
)
```

## Error Handling

The function logs errors to footprint with detailed context:

```python
{
    "subject": "Error sending request",
    "controller": "dtpyfw.core.request.request",
    "payload": {
        "method": "POST",
        "url": "https://api.example.com/api/users",
        "disable_caching": True,
        "json_return": True,
        "internal_service": True,
        "error": {exception_details}
    }
}
```

To disable logging:

```python
response = request(
    method="GET",
    path="/api/data",
    host="https://api.example.com",
    push_logs=False
)
```

## Best Practices

1. **Always set timeout:**
   ```python
   response = request(
       method="GET",
       path="/api/data",
       host="https://api.example.com",
       timeout=10  # Prevent hanging requests
   )
   ```

2. **Handle exceptions appropriately:**
   ```python
   from dtpyfw.core.exception import RequestException
   
   try:
       data = request(...)
   except RequestException as e:
       if e.status_code == 404:
           return None
       elif e.status_code >= 500:
           # Retry or alert
           pass
       raise
   ```

3. **Use environment variables for URLs:**
   ```python
   from dtpyfw.core.env import Env
   
   API_URL = Env.get("API_URL", "https://api.example.com")
   response = request(method="GET", path="/data", host=API_URL)
   ```

4. **Specify internal_service correctly:**
   ```python
   # For internal DealerTower services
   data = request(..., internal_service=True)
   
   # For external APIs
   data = request(..., internal_service=False)
   ```

## Related Modules

- **dtpyfw.core.exception** - RequestException class
- **dtpyfw.core.retry** - Retry logic for requests
- **dtpyfw.log.footprint** - Error logging
- **dtpyfw.core.env** - Environment configuration

## See Also

- [requests documentation](https://requests.readthedocs.io/)
- [HTTP Methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
