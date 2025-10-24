# Search and Filter Schemas (`dtpyfw.db.schema`)

## Overview

The `schema` module provides Pydantic v2 schemas for defining search filters, pagination, sorting, and results in the `get_list` function. These schemas enable type-safe, validated search requests with support for various filter types (select, number, date), free-text search, and metadata about available filters.

## Module Location

```python
from dtpyfw.db.schema import (
    # Enums
    AvailableFilterType,
    SearchType,
    
    # Available Filter Items
    AvailableFilterSelectItem,
    AvailableFilterNumberItem,
    AvailableFilterDateItem,
    
    # Available Filters
    AvailableFilterSelect,
    AvailableFilterNumber,
    AvailableFilterDate,
    
    # Selected Filters
    SelectedFilterSelect,
    SelectedFilterNumber,
    SelectedFilterDate,
    SelectedFilterSearch,
    
    # Search Payload
    PayloadSorting,
    Payload,
    
    # Results
    SearchResult,
    RowsListModelType,
    RowsListDict
)
```

## Enumerations

### `AvailableFilterType`

Enum defining supported filter types for metadata generation.

**Values:**

- `SELECT = "select"`: Single-select filter (select from dropdown)
- `SELECT_ARRAY = "select-array"`: Multi-select filter (select multiple values)
- `NUMBER = "number"`: Numeric range filter
- `DATE = "date"`: Date/datetime range filter
- `SEARCH = "search"`: Free-text search filter

**Usage:**

```python
from dtpyfw.db.schema import AvailableFilterType

filter_type = AvailableFilterType.SELECT
print(filter_type.value)  # "select"
```

### `SearchType`

Enum defining the type of search operation for free-text search.

**Values:**

- `FREE_SEARCH = "free_search"`: Full-text search using PostgreSQL `to_tsquery`
- `ICONTAINS = "icontains"`: Case-insensitive substring matching (LIKE %term%)

**Usage:**

```python
from dtpyfw.db.schema import SearchType

search_type = SearchType.FREE_SEARCH
print(search_type.value)  # "free_search"
```

## Available Filter Items

These classes represent individual filter options displayed to users in the UI.

### `AvailableFilterSelectItem`

Represents a single option in a select/dropdown filter.

**Fields:**

- `label` (str): Display text for the option
- `value` (str | int): The value used in the query

**Example:**

```python
from dtpyfw.db.schema import AvailableFilterSelectItem

option = AvailableFilterSelectItem(
    label="Active",
    value="active"
)
```

### `AvailableFilterNumberItem`

Represents numeric range boundaries for a number filter.

**Fields:**

- `min` (int | float): Minimum value in the range
- `max` (int | float): Maximum value in the range

**Example:**

```python
from dtpyfw.db.schema import AvailableFilterNumberItem

price_range = AvailableFilterNumberItem(
    min=0,
    max=9999.99
)
```

### `AvailableFilterDateItem`

Represents date/time range boundaries for a date filter.

**Fields:**

- `min` (datetime): Earliest date in the range
- `max` (datetime): Latest date in the range

**Example:**

```python
from datetime import datetime
from dtpyfw.db.schema import AvailableFilterDateItem

date_range = AvailableFilterDateItem(
    min=datetime(2024, 1, 1),
    max=datetime(2024, 12, 31)
)
```

## Available Filter Definitions

These classes define filter metadata returned by `get_list` to inform the UI about available filtering options.

### `AvailableFilterSelect`

Metadata for a select filter (single or multi-select).

**Fields:**

- `type` (Literal["select"] | Literal["select-array"]): Filter type identifier
- `label` (str): Human-readable filter name
- `field` (str): Database column or field name
- `values` (List[AvailableFilterSelectItem]): Available options

**Example:**

```python
from dtpyfw.db.schema import AvailableFilterSelect, AvailableFilterSelectItem

status_filter = AvailableFilterSelect(
    type="select",
    label="Status",
    field="status",
    values=[
        AvailableFilterSelectItem(label="Active", value="active"),
        AvailableFilterSelectItem(label="Inactive", value="inactive"),
        AvailableFilterSelectItem(label="Pending", value="pending")
    ]
)
```

**Used by `get_list`:**

```python
available_filters = {
    "status": {
        "type": AvailableFilterType.SELECT,
        "label": "Status",
        "values": ["active", "inactive", "pending"]
    }
}

result = get_list(session, Model, available_filters=available_filters)
# result.available_filters will contain AvailableFilterSelect instances
```

### `AvailableFilterNumber`

Metadata for a numeric range filter.

**Fields:**

- `type` (Literal["number"]): Filter type identifier
- `label` (str): Human-readable filter name
- `field` (str): Database column or field name
- `values` (AvailableFilterNumberItem): Min/max range

**Example:**

```python
from dtpyfw.db.schema import AvailableFilterNumber, AvailableFilterNumberItem

price_filter = AvailableFilterNumber(
    type="number",
    label="Price",
    field="price",
    values=AvailableFilterNumberItem(min=0, max=9999.99)
)
```

**Used by `get_list`:**

```python
available_filters = {
    "price": {
        "type": AvailableFilterType.NUMBER,
        "label": "Price",
        "values": {"min": 0, "max": 9999.99}
    }
}

result = get_list(session, Model, available_filters=available_filters)
```

### `AvailableFilterDate`

Metadata for a date/datetime range filter.

**Fields:**

- `type` (Literal["date"]): Filter type identifier
- `label` (str): Human-readable filter name
- `field` (str): Database column or field name
- `values` (AvailableFilterDateItem): Min/max date range

**Example:**

```python
from datetime import datetime
from dtpyfw.db.schema import AvailableFilterDate, AvailableFilterDateItem

created_filter = AvailableFilterDate(
    type="date",
    label="Created Date",
    field="created_at",
    values=AvailableFilterDateItem(
        min=datetime(2024, 1, 1),
        max=datetime(2024, 12, 31)
    )
)
```

**Used by `get_list`:**

```python
available_filters = {
    "created_at": {
        "type": AvailableFilterType.DATE,
        "label": "Created Date",
        "values": {
            "min": datetime(2024, 1, 1),
            "max": datetime(2024, 12, 31)
        }
    }
}

result = get_list(session, Model, available_filters=available_filters)
```

## Selected Filter Definitions

These classes represent active filters selected by the user, passed as part of the search payload.

### `SelectedFilterSelect`

Active filter for single-select filtering.

**Fields:**

- `type` (Literal["select"]): Filter type identifier
- `field` (str): Database column or field name
- `value` (str | int): Selected value

**Example:**

```python
from dtpyfw.db.schema import SelectedFilterSelect

status_filter = SelectedFilterSelect(
    type="select",
    field="status",
    value="active"
)
```

**Usage in Payload:**

```python
from dtpyfw.db.schema import Payload, SelectedFilterSelect

payload = Payload(
    selected_filters=[
        SelectedFilterSelect(type="select", field="status", value="active")
    ],
    limit=20,
    offset=0
)

result = get_list(session, Model, payload=payload)
```

### `SelectedFilterNumber`

Active filter for numeric range filtering.

**Fields:**

- `type` (Literal["number"]): Filter type identifier
- `field` (str): Database column or field name
- `min` (int | float | None): Minimum value (optional)
- `max` (int | float | None): Maximum value (optional)

**Example:**

```python
from dtpyfw.db.schema import SelectedFilterNumber

price_filter = SelectedFilterNumber(
    type="number",
    field="price",
    min=100,
    max=500
)
```

**Usage in Payload:**

```python
payload = Payload(
    selected_filters=[
        SelectedFilterNumber(type="number", field="price", min=100, max=500)
    ],
    limit=20,
    offset=0
)

result = get_list(session, Model, payload=payload)
```

### `SelectedFilterDate`

Active filter for date/datetime range filtering.

**Fields:**

- `type` (Literal["date"]): Filter type identifier
- `field` (str): Database column or field name
- `min` (datetime | None): Earliest date (optional)
- `max` (datetime | None): Latest date (optional)

**Example:**

```python
from datetime import datetime
from dtpyfw.db.schema import SelectedFilterDate

date_filter = SelectedFilterDate(
    type="date",
    field="created_at",
    min=datetime(2024, 1, 1),
    max=datetime(2024, 12, 31)
)
```

**Usage in Payload:**

```python
from datetime import datetime

payload = Payload(
    selected_filters=[
        SelectedFilterDate(
            type="date",
            field="created_at",
            min=datetime(2024, 1, 1),
            max=datetime(2024, 12, 31)
        )
    ],
    limit=20,
    offset=0
)

result = get_list(session, Model, payload=payload)
```

### `SelectedFilterSearch`

Active filter for free-text search.

**Fields:**

- `type` (Literal["search"]): Filter type identifier
- `field` (str): Database column or field name
- `value` (str): Search query text
- `search_type` (SearchType): Type of search operation (FREE_SEARCH or ICONTAINS)

**Example:**

```python
from dtpyfw.db.schema import SelectedFilterSearch, SearchType

search_filter = SelectedFilterSearch(
    type="search",
    field="name",
    value="john",
    search_type=SearchType.ICONTAINS
)
```

**Usage in Payload:**

```python
payload = Payload(
    selected_filters=[
        SelectedFilterSearch(
            type="search",
            field="name",
            value="john",
            search_type=SearchType.ICONTAINS
        )
    ],
    limit=20,
    offset=0
)

result = get_list(session, Model, payload=payload)
```

## Search Payload

### `PayloadSorting`

Defines sorting criteria for search results.

**Fields:**

- `field` (str): Database column or field name to sort by
- `direction` (Literal["asc"] | Literal["desc"]): Sort direction (ascending or descending)

**Example:**

```python
from dtpyfw.db.schema import PayloadSorting

sorting = PayloadSorting(
    field="created_at",
    direction="desc"
)
```

### `Payload`

Complete search request payload with filters, pagination, and sorting.

**Fields:**

- `selected_filters` (List[SelectedFilterSelect | SelectedFilterNumber | SelectedFilterDate | SelectedFilterSearch]): Active filters (default: `[]`)
- `limit` (int): Maximum number of records to return (default: `20`)
- `offset` (int): Number of records to skip for pagination (default: `0`)
- `sorting` (PayloadSorting | None): Sorting criteria (optional)

**Example:**

```python
from dtpyfw.db.schema import (
    Payload,
    PayloadSorting,
    SelectedFilterSelect,
    SelectedFilterNumber,
    SearchType
)

payload = Payload(
    selected_filters=[
        SelectedFilterSelect(type="select", field="status", value="active"),
        SelectedFilterNumber(type="number", field="price", min=100, max=500)
    ],
    limit=50,
    offset=0,
    sorting=PayloadSorting(field="created_at", direction="desc")
)

result = get_list(session, Model, payload=payload)
```

**Usage with FastAPI:**

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from dtpyfw.db.schema import Payload

app = FastAPI()

@app.post("/api/products/search")
def search_products(
    payload: Payload,
    session: Session = Depends(get_db)
):
    result = get_list(session, Product, payload=payload)
    return result
```

## Search Results

### `RowsListModelType`

Type variable for generic model list results.

**Usage:**

Used internally by `get_list` to type the rows when returning model instances.

```python
# When return_as_dict=False (default)
result: SearchResult[RowsListModelType]
rows: List[ModelType] = result.rows
```

### `RowsListDict`

Type alias for dictionary list results.

**Definition:**

```python
RowsListDict = List[Dict[str, Any]]
```

**Usage:**

Used internally by `get_list` to type the rows when returning dictionaries.

```python
# When return_as_dict=True
result: SearchResult[RowsListDict]
rows: List[Dict[str, Any]] = result.rows
```

### `SearchResult`

Generic result container for search operations.

**Type Parameters:**

- `T`: Type of rows returned (either `RowsListModelType` or `RowsListDict`)

**Fields:**

- `rows` (T): List of result records (models or dictionaries)
- `total` (int): Total number of records matching filters (before pagination)
- `limit` (int): Maximum records per page
- `offset` (int): Number of records skipped
- `available_filters` (List[AvailableFilterSelect | AvailableFilterNumber | AvailableFilterDate] | None): Available filter metadata (only if `available_filters` parameter was provided to `get_list`)
- `selected_filters` (List[Dict[str, Any]] | None): Human-readable representation of active filters

**Example:**

```python
from dtpyfw.db.schema import SearchResult, Payload

result = get_list(session, User, payload=Payload(limit=20, offset=0))

print(f"Total users: {result.total}")
print(f"Returned: {len(result.rows)} users")
print(f"Page: {result.offset // result.limit + 1}")

for user in result.rows:
    print(user.name)
```

**Dictionary Mode:**

```python
result = get_list(
    session,
    User,
    payload=Payload(limit=20, offset=0),
    return_as_dict=True
)

for user_dict in result.rows:
    print(user_dict['name'])
```

**With Available Filters:**

```python
available_filters = {
    "status": {
        "type": AvailableFilterType.SELECT,
        "label": "Status",
        "values": ["active", "inactive"]
    },
    "price": {
        "type": AvailableFilterType.NUMBER,
        "label": "Price",
        "values": {"min": 0, "max": 1000}
    }
}

result = get_list(
    session,
    Product,
    available_filters=available_filters,
    payload=Payload(limit=20, offset=0)
)

print(result.available_filters)
# [
#     AvailableFilterSelect(type="select", label="Status", field="status", ...),
#     AvailableFilterNumber(type="number", label="Price", field="price", ...)
# ]
```

**Selected Filters Display:**

```python
from dtpyfw.db.schema import Payload, SelectedFilterSelect

payload = Payload(
    selected_filters=[
        SelectedFilterSelect(type="select", field="status", value="active")
    ]
)

result = get_list(session, User, payload=payload)

print(result.selected_filters)
# [
#     {
#         "label": "Status",
#         "value": "Active"
#     }
# ]
```

## Complete Usage Examples

### Basic Search with Filters

```python
from dtpyfw.db.schema import (
    Payload,
    SelectedFilterSelect,
    SelectedFilterNumber,
    PayloadSorting
)

# Create search payload
payload = Payload(
    selected_filters=[
        SelectedFilterSelect(type="select", field="status", value="active"),
        SelectedFilterNumber(type="number", field="price", min=100, max=500)
    ],
    limit=20,
    offset=0,
    sorting=PayloadSorting(field="created_at", direction="desc")
)

# Execute search
result = get_list(session, Product, payload=payload)

print(f"Found {result.total} products")
for product in result.rows:
    print(f"{product.name}: ${product.price}")
```

### Date Range Filtering

```python
from datetime import datetime, timedelta
from dtpyfw.db.schema import Payload, SelectedFilterDate

# Last 30 days
thirty_days_ago = datetime.now() - timedelta(days=30)

payload = Payload(
    selected_filters=[
        SelectedFilterDate(
            type="date",
            field="created_at",
            min=thirty_days_ago,
            max=datetime.now()
        )
    ],
    limit=100,
    offset=0
)

result = get_list(session, Order, payload=payload)
print(f"Orders in last 30 days: {result.total}")
```

### Multi-Select Array Filter

```python
from dtpyfw.db.schema import Payload, SelectedFilterSelect

# Note: For select-array filters, pass multiple filters with same field
payload = Payload(
    selected_filters=[
        SelectedFilterSelect(type="select", field="category", value="electronics"),
        SelectedFilterSelect(type="select", field="category", value="computers")
    ],
    limit=50,
    offset=0
)

result = get_list(session, Product, payload=payload)
```

### Free-Text Search

```python
from dtpyfw.db.schema import Payload, SelectedFilterSearch, SearchType

# Full-text search
payload = Payload(
    selected_filters=[
        SelectedFilterSearch(
            type="search",
            field="name",
            value="laptop computer",
            search_type=SearchType.FREE_SEARCH
        )
    ],
    limit=20,
    offset=0
)

result = get_list(session, Product, payload=payload)
```

### Pagination Example

```python
from dtpyfw.db.schema import Payload

def get_page(page: int, page_size: int = 20):
    offset = (page - 1) * page_size
    payload = Payload(
        selected_filters=[],
        limit=page_size,
        offset=offset
    )
    return get_list(session, Product, payload=payload)

# Get page 1
page1 = get_page(1)
print(f"Page 1: {len(page1.rows)} of {page1.total}")

# Get page 2
page2 = get_page(2)
print(f"Page 2: {len(page2.rows)} of {page2.total}")

# Calculate total pages
total_pages = (page1.total + page1.limit - 1) // page1.limit
print(f"Total pages: {total_pages}")
```

### Available Filters Metadata

```python
from dtpyfw.db.schema import AvailableFilterType

available_filters = {
    "status": {
        "type": AvailableFilterType.SELECT,
        "label": "Status",
        "values": ["active", "inactive", "pending"]
    },
    "price": {
        "type": AvailableFilterType.NUMBER,
        "label": "Price Range",
        "values": {"min": 0, "max": 9999.99}
    },
    "created_at": {
        "type": AvailableFilterType.DATE,
        "label": "Created Date",
        "values": {
            "min": datetime(2024, 1, 1),
            "max": datetime.now()
        }
    }
}

result = get_list(
    session,
    Product,
    available_filters=available_filters,
    payload=Payload(limit=20, offset=0)
)

# Frontend can use result.available_filters to render filter UI
for filter_def in result.available_filters:
    print(f"Filter: {filter_def.label} ({filter_def.type})")
    if filter_def.type == "select":
        for option in filter_def.values:
            print(f"  - {option.label}: {option.value}")
```

## FastAPI Integration

### Complete Search Endpoint

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dtpyfw.db.schema import Payload, AvailableFilterType
from datetime import datetime

app = FastAPI()

def get_db():
    yield from db.get_db_read()

@app.post("/api/products/search")
def search_products(
    payload: Payload,
    session: Session = Depends(get_db)
):
    available_filters = {
        "status": {
            "type": AvailableFilterType.SELECT,
            "label": "Status",
            "values": ["active", "inactive", "discontinued"]
        },
        "price": {
            "type": AvailableFilterType.NUMBER,
            "label": "Price",
            "values": {"min": 0, "max": 9999.99}
        },
        "created_at": {
            "type": AvailableFilterType.DATE,
            "label": "Created Date",
            "values": {
                "min": datetime(2020, 1, 1),
                "max": datetime.now()
            }
        }
    }
    
    result = get_list(
        session,
        Product,
        available_filters=available_filters,
        payload=payload,
        return_as_dict=True
    )
    
    return {
        "data": result.rows,
        "pagination": {
            "total": result.total,
            "limit": result.limit,
            "offset": result.offset,
            "pages": (result.total + result.limit - 1) // result.limit
        },
        "filters": {
            "available": result.available_filters,
            "selected": result.selected_filters
        }
    }
```

### Type-Safe Request Models

```python
from pydantic import BaseModel
from dtpyfw.db.schema import Payload, SelectedFilterSelect

class ProductSearchRequest(BaseModel):
    status: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    search_term: str | None = None
    page: int = 1
    page_size: int = 20

@app.post("/api/products/search-simple")
def search_products_simple(
    request: ProductSearchRequest,
    session: Session = Depends(get_db)
):
    # Convert to Payload
    selected_filters = []
    
    if request.status:
        selected_filters.append(
            SelectedFilterSelect(type="select", field="status", value=request.status)
        )
    
    if request.min_price is not None or request.max_price is not None:
        selected_filters.append(
            SelectedFilterNumber(
                type="number",
                field="price",
                min=request.min_price,
                max=request.max_price
            )
        )
    
    if request.search_term:
        selected_filters.append(
            SelectedFilterSearch(
                type="search",
                field="name",
                value=request.search_term,
                search_type=SearchType.ICONTAINS
            )
        )
    
    offset = (request.page - 1) * request.page_size
    payload = Payload(
        selected_filters=selected_filters,
        limit=request.page_size,
        offset=offset
    )
    
    result = get_list(session, Product, payload=payload, return_as_dict=True)
    
    return result
```

## Best Practices

1. **Use discriminated unions**: The schemas use Pydantic's discriminated unions for type safety with the `type` field.

2. **Validate filter fields**: Ensure filter field names match actual database columns:
   ```python
   # Good
   SelectedFilterSelect(type="select", field="status", value="active")
   
   # Bad - typo in field name
   SelectedFilterSelect(type="select", field="statuss", value="active")
   ```

3. **Handle optional ranges**: Number and date filters support optional min/max:
   ```python
   # Only max
   SelectedFilterNumber(type="number", field="price", max=500)
   
   # Only min
   SelectedFilterNumber(type="number", field="price", min=100)
   ```

4. **Use appropriate search types**: Choose between FREE_SEARCH (faster, PostgreSQL-specific) and ICONTAINS (works on any column):
   ```python
   # For indexed text search columns
   SearchType.FREE_SEARCH
   
   # For any text column
   SearchType.ICONTAINS
   ```

5. **Provide available_filters metadata**: When building UI, return available filters to guide users:
   ```python
   result = get_list(
       session,
       Model,
       available_filters=filters_definition,
       payload=payload
   )
   ```

6. **Calculate pagination properly**:
   ```python
   total_pages = (result.total + result.limit - 1) // result.limit
   current_page = (result.offset // result.limit) + 1
   ```

7. **Use return_as_dict for APIs**: When building REST APIs, use dictionaries instead of model instances:
   ```python
   result = get_list(session, Model, payload=payload, return_as_dict=True)
   ```

## Related Documentation

- [search.md](./search.md) - Complete get_list function documentation
- [search_utils/](./search_utils/) - Internal search implementation details
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)

## Notes

- All schemas use Pydantic v2 features
- Discriminated unions enable type-safe filter handling
- The `type` field is the discriminator for all filter unions
- SearchResult is generic and typed based on return_as_dict parameter
- selected_filters in SearchResult provides human-readable filter descriptions
