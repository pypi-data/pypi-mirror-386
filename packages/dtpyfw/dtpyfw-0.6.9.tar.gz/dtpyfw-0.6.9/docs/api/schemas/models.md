# dtpyfw.api.schemas.models

Common request payload and data models for API endpoints.

## Module Overview

The `models` module provides reusable Pydantic models for common API request patterns, including pagination, sorting, filtering, and range queries. These models ensure consistency across list and search endpoints.

## Key Features

- **Pagination Support**: Built-in page and items_per_page handling
- **Sorting Configuration**: Multi-field sorting with direction control
- **Search Integration**: Free-text search query support
- **Range Filters**: Numeric, date, and datetime range models
- **Validation**: Automatic validation of pagination and sorting parameters
- **Enum Serialization**: Configured for automatic enum-to-value conversion

## Classes

### Sorting

```python
class Sorting(BaseModel):
    """Sorting configuration for query results."""
```

Specifies how to sort query results.

**Attributes:**

- **sort_by** (`str`): The field name to sort results by
- **order_by** (`OrderingType`): Sorting direction (ascending or descending). Default: `OrderingType.asc`

**Example:**

```python
sorting = Sorting(sort_by="created_at", order_by=OrderingType.desc)
```

### SearchPayload

```python
class SearchPayload(BaseModel):
    """Common request payload for paginated and searchable list endpoints."""
```

Standard request body for list/search endpoints with pagination, sorting, and search.

**Attributes:**

- **page** (`int | None`): Page number to retrieve (must be >= 1). Default: `1`
- **items_per_page** (`int | None`): Number of items per page (max 30). Default: `20`
- **sorting** (`List[Sorting] | None`): Optional list of sorting rules. Default: `None`
- **search** (`str | None`): Optional search term to filter results. Default: `""`

**Validation:**

- `page` must be >= 1
- `items_per_page` must be <= 30

**Example:**

```python
payload = SearchPayload(
    page=2,
    items_per_page=25,
    sorting=[Sorting(sort_by="name", order_by=OrderingType.asc)],
    search="alice"
)
```

### NumberRange

```python
class NumberRange(BaseModel):
    """Range filter for numeric values."""
```

Defines minimum and maximum bounds for filtering numeric data.

**Attributes:**

- **min** (`int | None`): Minimum value allowed in the range. Default: `None`
- **max** (`int | None`): Maximum value allowed in the range. Default: `None`

**Example:**

```python
price_range = NumberRange(min=10, max=100)
```

### TimeRange

```python
class TimeRange(BaseModel):
    """Range filter for time values."""
```

Defines minimum and maximum datetime bounds for filtering temporal data.

**Attributes:**

- **min** (`datetime | None`): Minimum datetime allowed in the range. Default: `None`
- **max** (`datetime | None`): Maximum datetime allowed in the range. Default: `None`

**Example:**

```python
from datetime import datetime

time_range = TimeRange(
    min=datetime(2025, 1, 1),
    max=datetime(2025, 12, 31)
)
```

### DateRange

```python
class DateRange(BaseModel):
    """Range filter for date values."""
```

Defines minimum and maximum date bounds for filtering date-only data.

**Attributes:**

- **min** (`date | None`): Minimum date allowed in the range. Default: `None`
- **max** (`date | None`): Maximum date allowed in the range. Default: `None`

**Example:**

```python
from datetime import date

date_range = DateRange(
    min=date(2025, 1, 1),
    max=date(2025, 12, 31)
)
```

### BaseModelEnumValue

```python
class BaseModelEnumValue(BaseModel):
    """Base model configured to serialize enums as their values."""
```

Pydantic base class that automatically serializes Enum fields to their values.

**Configuration:**

```python
model_config = ConfigDict(use_enum_values=True)
```

**Example:**

```python
from enum import Enum

class Status(str, Enum):
    active = "active"
    inactive = "inactive"

class MyModel(BaseModelEnumValue):
    status: Status

obj = MyModel(status=Status.active)
# Serialized as: {"status": "active"} not {"status": "Status.active"}
```

### ListPayloadResponse

```python
class ListPayloadResponse(BaseModel):
    """Standard response structure for paginated list endpoints."""
```

Provides pagination metadata alongside list results.

**Attributes:**

- **total_row** (`int | None`): Total number of rows matching the query. Default: `None`
- **last_page** (`int | None`): The index of the last available page. Default: `None`
- **has_next** (`bool | None`): Indicates if there is a next page available. Default: `None`

**Example:**

```python
response = ListPayloadResponse(
    total_row=150,
    last_page=8,
    has_next=True
)
```

## Usage Examples

### Basic Pagination Endpoint

```python
from dtpyfw.api.schemas.models import SearchPayload

@app.post("/users")
def list_users(payload: SearchPayload):
    users = get_users(
        page=payload.page,
        limit=payload.items_per_page,
        search=payload.search
    )
    return {"users": users}

# Request:
# {
#   "page": 1,
#   "items_per_page": 20
# }
```

### Sorted List Endpoint

```python
from dtpyfw.api.schemas.models import SearchPayload, Sorting
from dtpyfw.core.enums import OrderingType

@app.post("/products")
def list_products(payload: SearchPayload):
    query = Product.query
    
    # Apply sorting
    if payload.sorting:
        for sort in payload.sorting:
            field = getattr(Product, sort.sort_by)
            if sort.order_by == OrderingType.desc:
                query = query.order_by(field.desc())
            else:
                query = query.order_by(field.asc())
    
    products = query.paginate(
        page=payload.page,
        per_page=payload.items_per_page
    )
    return {"products": products}

# Request:
# {
#   "page": 1,
#   "items_per_page": 20,
#   "sorting": [
#     {"sort_by": "price", "order_by": "desc"},
#     {"sort_by": "name", "order_by": "asc"}
#   ]
# }
```

### Search with Filters

```python
from dtpyfw.api.schemas.models import SearchPayload

@app.post("/search")
def search_items(payload: SearchPayload):
    query = Item.query
    
    # Apply search
    if payload.search:
        query = query.filter(
            Item.name.ilike(f"%{payload.search}%")
        )
    
    # Paginate
    items = query.paginate(
        page=payload.page,
        per_page=payload.items_per_page
    )
    
    return {"items": items, "total": items.total}

# Request:
# {
#   "page": 1,
#   "items_per_page": 20,
#   "search": "laptop"
# }
```

### Price Range Filter

```python
from dtpyfw.api.schemas.models import NumberRange

@app.post("/products/filter")
def filter_products(price_range: NumberRange):
    query = Product.query
    
    if price_range.min is not None:
        query = query.filter(Product.price >= price_range.min)
    
    if price_range.max is not None:
        query = query.filter(Product.price <= price_range.max)
    
    return {"products": query.all()}

# Request:
# {
#   "min": 100,
#   "max": 500
# }
```

### Date Range Filter

```python
from dtpyfw.api.schemas.models import DateRange

@app.post("/orders/filter")
def filter_orders(date_range: DateRange):
    query = Order.query
    
    if date_range.min:
        query = query.filter(Order.created_date >= date_range.min)
    
    if date_range.max:
        query = query.filter(Order.created_date <= date_range.max)
    
    return {"orders": query.all()}

# Request:
# {
#   "min": "2025-01-01",
#   "max": "2025-12-31"
# }
```

### Paginated Response with Metadata

```python
from dtpyfw.api.schemas.models import SearchPayload, ListPayloadResponse
from pydantic import BaseModel

class PaginatedUsers(ListPayloadResponse):
    users: list[dict]

@app.post("/users", response_model=PaginatedUsers)
def list_users(payload: SearchPayload):
    total = User.count()
    users = get_users(payload.page, payload.items_per_page)
    
    last_page = (total + payload.items_per_page - 1) // payload.items_per_page
    has_next = payload.page < last_page
    
    return {
        "users": users,
        "total_row": total,
        "last_page": last_page,
        "has_next": has_next
    }

# Response:
# {
#   "users": [...],
#   "total_row": 150,
#   "last_page": 8,
#   "has_next": true
# }
```

### Multi-Field Sorting

```python
from dtpyfw.api.schemas.models import SearchPayload

@app.post("/products")
def list_products(payload: SearchPayload):
    products = Product.query
    
    # Default sorting if none provided
    if not payload.sorting:
        products = products.order_by(Product.created_at.desc())
    else:
        # Apply each sort criterion in order
        for sort_rule in payload.sorting:
            field = getattr(Product, sort_rule.sort_by)
            if sort_rule.order_by == OrderingType.desc:
                products = products.order_by(field.desc())
            else:
                products = products.order_by(field.asc())
    
    return {"products": products.all()}

# Request:
# {
#   "sorting": [
#     {"sort_by": "category", "order_by": "asc"},
#     {"sort_by": "price", "order_by": "desc"},
#     {"sort_by": "name", "order_by": "asc"}
#   ]
# }
```

### Complete Search Endpoint

```python
from dtpyfw.api.schemas.models import SearchPayload, ListPayloadResponse
from pydantic import BaseModel

class ProductSearchResponse(ListPayloadResponse):
    products: list[dict]

@app.post("/products/search", response_model=ProductSearchResponse)
def search_products(payload: SearchPayload):
    query = Product.query
    
    # Apply search
    if payload.search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f"%{payload.search}%"),
                Product.description.ilike(f"%{payload.search}%")
            )
        )
    
    # Apply sorting
    if payload.sorting:
        for sort in payload.sorting:
            field = getattr(Product, sort.sort_by)
            if sort.order_by == OrderingType.desc:
                query = query.order_by(field.desc())
            else:
                query = query.order_by(field.asc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    products = query.offset(
        (payload.page - 1) * payload.items_per_page
    ).limit(payload.items_per_page).all()
    
    # Calculate metadata
    last_page = (total + payload.items_per_page - 1) // payload.items_per_page
    has_next = payload.page < last_page
    
    return {
        "products": [p.to_dict() for p in products],
        "total_row": total,
        "last_page": last_page,
        "has_next": has_next
    }
```

## Validation Examples

### Page Validation

```python
# Valid
payload = SearchPayload(page=1)  # OK
payload = SearchPayload(page=10)  # OK

# Invalid
payload = SearchPayload(page=0)  # ValidationError: page must be >= 1
payload = SearchPayload(page=-1)  # ValidationError: page must be >= 1
```

### Items Per Page Validation

```python
# Valid
payload = SearchPayload(items_per_page=10)  # OK
payload = SearchPayload(items_per_page=30)  # OK

# Invalid
payload = SearchPayload(items_per_page=50)  # ValidationError: max 30
payload = SearchPayload(items_per_page=100)  # ValidationError: max 30
```

## Best Practices

1. **Use SearchPayload**: Use `SearchPayload` for all list/search endpoints
2. **Validate Sort Fields**: Check that sort_by fields exist before applying
3. **Default Sorting**: Provide sensible default sorting when none specified
4. **Limit Items Per Page**: The 30-item limit prevents performance issues
5. **Return Metadata**: Always return `total_row`, `last_page`, `has_next` for pagination
6. **Search Optimization**: Index fields commonly used in search queries
7. **Multi-Field Search**: Search across multiple relevant fields

## Common Patterns

### Infinite Scroll Response

```python
@app.post("/feed")
def get_feed(payload: SearchPayload):
    posts = get_posts(payload.page, payload.items_per_page)
    has_more = len(posts) == payload.items_per_page
    
    return {
        "posts": posts,
        "has_next": has_more,
        "next_page": payload.page + 1 if has_more else None
    }
```

### Cursor-Based Pagination

```python
from pydantic import BaseModel

class CursorPayload(BaseModel):
    cursor: str | None = None
    limit: int = 20

@app.post("/items")
def list_items(payload: CursorPayload):
    items, next_cursor = get_items_with_cursor(
        payload.cursor,
        payload.limit
    )
    return {
        "items": items,
        "next_cursor": next_cursor
    }
```

## Testing

```python
from dtpyfw.api.schemas.models import SearchPayload
import pytest

def test_search_payload_validation():
    # Valid payload
    payload = SearchPayload(page=1, items_per_page=20)
    assert payload.page == 1
    assert payload.items_per_page == 20
    
    # Invalid page
    with pytest.raises(ValueError):
        SearchPayload(page=0)
    
    # Invalid items_per_page
    with pytest.raises(ValueError):
        SearchPayload(items_per_page=50)

def test_number_range():
    range_filter = NumberRange(min=10, max=100)
    assert range_filter.min == 10
    assert range_filter.max == 100
    
    # Optional fields
    range_filter = NumberRange()
    assert range_filter.min is None
    assert range_filter.max is None
```

## Related Modules

- [`dtpyfw.api.schemas.response`](response.md): Response schema models
- [`dtpyfw.api.schemas.filters`](filters.md): Advanced filtering schemas
- [`dtpyfw.core.enums`](../../core/enums.md): Enum definitions including OrderingType
- [`dtpyfw.db.search`](../../db/search.md): Database search utilities
- Pydantic Validation: [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
