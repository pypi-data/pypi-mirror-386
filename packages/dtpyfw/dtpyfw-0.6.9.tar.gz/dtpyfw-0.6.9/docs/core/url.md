# URL Manipulation Utilities

## Overview

The `dtpyfw.core.url` module provides small URL manipulation helpers for working with query parameters. This module makes it easy to add or update query parameters in existing URLs while preserving the original URL structure.

## Module Path

```python
from dtpyfw.core.url import add_query_param
```

## Functions

### `add_query_param(url: str, params: Dict[str, Any]) -> str`

Add or update query parameters in a URL.

**Description:**

Takes a URL and a dictionary of parameters, then adds the parameters to the URL's query string. If a parameter already exists, its value is updated. The function preserves the URL's scheme, domain, path, and fragment while manipulating only the query string.

**Parameters:**

- **url** (`str`): The original URL
- **params** (`Dict[str, Any]`): A dictionary of query parameters to add or update

**Returns:**

- **`str`**: The new URL with the updated query parameters

**Example:**

```python
from dtpyfw.core.url import add_query_param

# Add parameters to URL without query string
url = "https://api.example.com/users"
new_url = add_query_param(url, {"page": 1, "limit": 20})
print(new_url)
# Output: https://api.example.com/users?page=1&limit=20

# Add parameters to URL with existing query string
url = "https://api.example.com/search?q=python"
new_url = add_query_param(url, {"page": 2, "sort": "date"})
print(new_url)
# Output: https://api.example.com/search?q=python&page=2&sort=date

# Update existing parameter
url = "https://api.example.com/users?page=1"
new_url = add_query_param(url, {"page": 2})
print(new_url)
# Output: https://api.example.com/users?page=2
```

## Complete Usage Examples

### 1. Pagination Helper

```python
from dtpyfw.core.url import add_query_param

class PaginationHelper:
    @staticmethod
    def get_next_page_url(current_url: str, current_page: int) -> str:
        """Generate URL for next page."""
        return add_query_param(current_url, {"page": current_page + 1})
    
    @staticmethod
    def get_previous_page_url(current_url: str, current_page: int) -> str:
        """Generate URL for previous page."""
        if current_page > 1:
            return add_query_param(current_url, {"page": current_page - 1})
        return current_url
    
    @staticmethod
    def get_page_url(base_url: str, page: int, per_page: int = 20) -> str:
        """Generate URL for specific page."""
        return add_query_param(base_url, {"page": page, "per_page": per_page})

# Usage
helper = PaginationHelper()
next_url = helper.get_next_page_url("https://api.example.com/products", 1)
print(next_url)  # https://api.example.com/products?page=2

page_url = helper.get_page_url("https://api.example.com/products", 3, 50)
print(page_url)  # https://api.example.com/products?page=3&per_page=50
```

### 2. Search Filter Builder

```python
from dtpyfw.core.url import add_query_param
from typing import Dict, Any, Optional

class SearchURLBuilder:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def add_filters(self, **filters) -> str:
        """Add search filters to URL."""
        # Remove None values
        valid_filters = {k: v for k, v in filters.items() if v is not None}
        return add_query_param(self.base_url, valid_filters)
    
    def build_search_url(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort: str = "relevance"
    ) -> str:
        """Build complete search URL with filters."""
        params = {"q": query, "sort": sort}
        
        if category:
            params["category"] = category
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        
        return add_query_param(self.base_url, params)

# Usage
builder = SearchURLBuilder("https://shop.example.com/search")
url = builder.build_search_url(
    query="laptop",
    category="electronics",
    min_price=500,
    max_price=1500,
    sort="price_asc"
)
print(url)
# https://shop.example.com/search?q=laptop&sort=price_asc&category=electronics&min_price=500&max_price=1500
```

### 3. Analytics Tracking Parameters

```python
from dtpyfw.core.url import add_query_param

class TrackingURLGenerator:
    @staticmethod
    def add_utm_params(
        url: str,
        source: str,
        medium: str,
        campaign: str,
        content: str = None
    ) -> str:
        """Add UTM tracking parameters to URL."""
        params = {
            "utm_source": source,
            "utm_medium": medium,
            "utm_campaign": campaign
        }
        
        if content:
            params["utm_content"] = content
        
        return add_query_param(url, params)
    
    @staticmethod
    def add_referral_code(url: str, referral_code: str) -> str:
        """Add referral code to URL."""
        return add_query_param(url, {"ref": referral_code})

# Usage
tracker = TrackingURLGenerator()

# Email campaign tracking
email_url = tracker.add_utm_params(
    "https://example.com/product",
    source="newsletter",
    medium="email",
    campaign="spring_sale",
    content="cta_button"
)
print(email_url)
# https://example.com/product?utm_source=newsletter&utm_medium=email&utm_campaign=spring_sale&utm_content=cta_button

# Referral link
referral_url = tracker.add_referral_code("https://example.com/signup", "USER123")
print(referral_url)
# https://example.com/signup?ref=USER123
```

### 4. API Client with Query Parameters

```python
from dtpyfw.core.url import add_query_param
import requests

class APIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
    
    def _build_url(self, endpoint: str, params: dict = None) -> str:
        """Build complete API URL with parameters."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add API key
        all_params = {"api_key": self.api_key}
        if params:
            all_params.update(params)
        
        return add_query_param(url, all_params)
    
    def get(self, endpoint: str, **kwargs) -> dict:
        """Make GET request with query parameters."""
        url = self._build_url(endpoint, kwargs)
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Usage
client = APIClient("https://api.example.com/v1", "your-api-key")
users = client.get("/users", page=1, limit=50, role="admin")
# Calls: https://api.example.com/v1/users?api_key=your-api-key&page=1&limit=50&role=admin
```

### 5. Dynamic Report URL Generator

```python
from dtpyfw.core.url import add_query_param
from datetime import datetime, timedelta

class ReportURLGenerator:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def generate_report_url(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        filters: dict = None
    ) -> str:
        """Generate URL for downloading reports."""
        params = {
            "type": report_type,
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "format": "pdf"
        }
        
        if filters:
            params.update(filters)
        
        return add_query_param(self.base_url, params)
    
    def generate_daily_report_url(self, date: datetime = None) -> str:
        """Generate URL for daily report."""
        if date is None:
            date = datetime.now()
        
        return self.generate_report_url(
            "daily",
            date,
            date
        )
    
    def generate_monthly_report_url(self, year: int, month: int) -> str:
        """Generate URL for monthly report."""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        return self.generate_report_url("monthly", start_date, end_date)

# Usage
generator = ReportURLGenerator("https://reports.example.com/generate")
url = generator.generate_monthly_report_url(2024, 10)
print(url)
# https://reports.example.com/generate?type=monthly&start=2024-10-01&end=2024-10-31&format=pdf
```

### 6. Share Link Generator

```python
from dtpyfw.core.url import add_query_param

class ShareLinkGenerator:
    @staticmethod
    def create_share_link(content_url: str, platform: str, title: str = None) -> str:
        """Create social media share link."""
        if platform == "twitter":
            params = {"url": content_url}
            if title:
                params["text"] = title
            return add_query_param("https://twitter.com/intent/tweet", params)
        
        elif platform == "facebook":
            return add_query_param("https://www.facebook.com/sharer/sharer.php", {
                "u": content_url
            })
        
        elif platform == "linkedin":
            params = {"url": content_url}
            if title:
                params["title"] = title
            return add_query_param("https://www.linkedin.com/sharing/share-offsite", params)
        
        elif platform == "email":
            params = {"body": content_url}
            if title:
                params["subject"] = title
            return add_query_param("mailto:", params)
        
        return content_url

# Usage
generator = ShareLinkGenerator()
article_url = "https://blog.example.com/article"

twitter_link = generator.create_share_link(article_url, "twitter", "Check this out!")
print(twitter_link)
# https://twitter.com/intent/tweet?url=https%3A//blog.example.com/article&text=Check+this+out%21

facebook_link = generator.create_share_link(article_url, "facebook")
print(facebook_link)
# https://www.facebook.com/sharer/sharer.php?u=https%3A//blog.example.com/article
```

### 7. API Version Management

```python
from dtpyfw.core.url import add_query_param

class VersionedAPIClient:
    def __init__(self, base_url: str, api_version: str = "v1"):
        self.base_url = base_url
        self.api_version = api_version
    
    def build_endpoint(self, path: str, **params) -> str:
        """Build versioned API endpoint."""
        # Add version to all requests
        params["version"] = self.api_version
        
        url = f"{self.base_url}/{path.lstrip('/')}"
        return add_query_param(url, params)

# Usage
client = VersionedAPIClient("https://api.example.com", "v2")
url = client.build_endpoint("/users/123", include="profile,settings")
print(url)
# https://api.example.com/users/123?version=v2&include=profile%2Csettings
```

### 8. OAuth Redirect URL Builder

```python
from dtpyfw.core.url import add_query_param

class OAuthHelper:
    @staticmethod
    def build_authorization_url(
        auth_endpoint: str,
        client_id: str,
        redirect_uri: str,
        scope: str,
        state: str = None
    ) -> str:
        """Build OAuth authorization URL."""
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope
        }
        
        if state:
            params["state"] = state
        
        return add_query_param(auth_endpoint, params)

# Usage
oauth = OAuthHelper()
auth_url = oauth.build_authorization_url(
    "https://accounts.google.com/o/oauth2/v2/auth",
    client_id="YOUR_CLIENT_ID",
    redirect_uri="https://yourapp.com/callback",
    scope="email profile",
    state="random_state_string"
)
print(auth_url)
# https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=https%3A//yourapp.com/callback&response_type=code&scope=email+profile&state=random_state_string
```

## Working with URL Components

The function preserves all URL components:

```python
from dtpyfw.core.url import add_query_param

# With port
url = add_query_param("http://localhost:8000/api", {"key": "value"})
# http://localhost:8000/api?key=value

# With path
url = add_query_param("https://example.com/api/v1/users", {"limit": 10})
# https://example.com/api/v1/users?limit=10

# With fragment
url = add_query_param("https://example.com/page#section", {"ref": "link"})
# https://example.com/page?ref=link#section

# With existing params
url = add_query_param("https://example.com?a=1&b=2", {"c": 3})
# https://example.com?a=1&b=2&c=3
```

## Best Practices

1. **URL encode is automatic:**
   ```python
   # Special characters are automatically encoded
   url = add_query_param("https://api.com", {"search": "hello world"})
   # https://api.com?search=hello+world
   ```

2. **Handle list parameters:**
   ```python
   # For repeated parameters
   url = add_query_param("https://api.com", {"tags": ["python", "fastapi"]})
   # https://api.com?tags=python&tags=fastapi
   ```

3. **Remove None values:**
   ```python
   params = {"page": 1, "filter": None, "sort": "date"}
   clean_params = {k: v for k, v in params.items() if v is not None}
   url = add_query_param(base_url, clean_params)
   ```

4. **Chain multiple updates:**
   ```python
   url = "https://api.example.com/search"
   url = add_query_param(url, {"q": "python"})
   url = add_query_param(url, {"page": 2})
   url = add_query_param(url, {"sort": "date"})
   ```

## Related Modules

- **dtpyfw.core.request** - HTTP requests using URLs
- **dtpyfw.api.routes** - API routing with query parameters

## Dependencies

- `urllib.parse` - URL parsing and manipulation

## See Also

- [Python urllib.parse](https://docs.python.org/3/library/urllib.parse.html)
- [URL Standard](https://url.spec.whatwg.org/)
- [Query String Parameters](https://en.wikipedia.org/wiki/Query_string)
