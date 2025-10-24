# dtpyfw.api.schemas.filters

Advanced filtering schemas for search and query endpoints.

## Module Overview

The `filters` module provides comprehensive Pydantic models for building sophisticated filtering systems in API endpoints. It supports multiple filter types (select, date, number, search), available filter definitions, and selected filter tracking for complex search interfaces.

## Key Features

- **Multiple Filter Types**: Select, date/datetime, numeric range, and free-text search
- **Type Discrimination**: Uses Pydantic discriminated unions for type-safe filter handling
- **Available Filters**: Define what filters users can apply
- **Selected Filters**: Track which filters are currently active
- **UUID Support**: Built-in support for UUID-based filtering
- **Flexible Values**: Support for boolean, string, and UUID select options

## Classes

### FilterOptionBase

```python
class FilterOptionBase(BaseModel):
    """Base model for describing a filter option exposed by the API."""
```

Common fields shared by all filter option types.

**Attributes:**

- **label** (`str`): Human-readable label of the filter
- **name** (`str`): Unique key or identifier of the filter

### FilterSelectValue

```python
class FilterSelectValue(BaseModel):
    """Possible selectable value for a 'select' filter option."""
```

Represents a single option within a select-type filter.

**Attributes:**

- **label** (`str`): Human-readable label for the option
- **value** (`UUID | bool | str | None`): Underlying value associated with the option. Default: `None`

**Example:**

```python
option = FilterSelectValue(
    label="Active",
    value=True
)
```

### FilterOptionSelect

```python
class FilterOptionSelect(FilterOptionBase):
    """Filter option representing a selectable list of values."""
```

Defines a filter with predefined selectable values (dropdown, checkboxes).

**Attributes:**

- **type** (`Literal["select"]`): Type identifier, always `"select"`
- **label** (`str`): Human-readable label
- **name** (`str`): Unique identifier
- **value** (`list[FilterSelectValue]`): List of available values

**Example:**

```python
status_filter = FilterOptionSelect(
    type="select",
    label="Status",
    name="status",
    value=[
        FilterSelectValue(label="Active", value="active"),
        FilterSelectValue(label="Inactive", value="inactive"),
    ]
)
```

### FilterOptionDate

```python
class FilterOptionDate(FilterOptionBase):
    """Filter option representing a date or datetime range."""
```

Defines a filter for date/datetime range selection.

**Attributes:**

- **type** (`Literal["date"]`): Type identifier, always `"date"`
- **label** (`str`): Human-readable label
- **name** (`str`): Unique identifier
- **value** (`TimeRange`): Range of datetime values allowed

**Example:**

```python
from dtpyfw.api.schemas.models import TimeRange
from datetime import datetime

date_filter = FilterOptionDate(
    type="date",
    label="Created Date",
    name="created_date",
    value=TimeRange(
        min=datetime(2025, 1, 1),
        max=datetime(2025, 12, 31)
    )
)
```

### FilterOptionNumber

```python
class FilterOptionNumber(FilterOptionBase):
    """Filter option representing a numeric range."""
```

Defines a filter for numeric range selection.

**Attributes:**

- **type** (`Literal["number"]`): Type identifier, always `"number"`
- **label** (`str`): Human-readable label
- **name** (`str`): Unique identifier
- **value** (`NumberRange`): Range of numeric values allowed

**Example:**

```python
from dtpyfw.api.schemas.models import NumberRange

price_filter = FilterOptionNumber(
    type="number",
    label="Price",
    name="price",
    value=NumberRange(min=0, max=10000)
)
```

### FilterOption

```python
FilterOption = Annotated[
    Union[FilterOptionSelect, FilterOptionDate, FilterOptionNumber],
    Field(discriminator="type"),
]
```

Discriminated union of all available filter option types. FastAPI/Pydantic automatically routes to the correct type based on the `type` field.

### SearchResponseAvailableFilters

```python
class SearchResponseAvailableFilters(BaseModel):
    """Response payload listing all available filters for a search."""
```

Contains the list of filter definitions that users can apply.

**Attributes:**

- **available_filters** (`list[FilterOption]`): List of filter definitions

**Example:**

```json
{
  "available_filters": [
    {
      "type": "select",
      "label": "Status",
      "name": "status",
      "value": [
        {"label": "Active", "value": "active"},
        {"label": "Inactive", "value": "inactive"}
      ]
    },
    {
      "type": "number",
      "label": "Price",
      "name": "price",
      "value": {"min": 0, "max": 1000}
    }
  ]
}
```

### SelectedFilterBase

```python
class SelectedFilterBase(BaseModel):
    """Base model for describing a filter that has been applied by the user."""
```

Common fields shared by all selected filter types.

**Attributes:**

- **label** (`str`): Human-readable label
- **name** (`str`): Unique identifier

### SelectedFilterSelect

```python
class SelectedFilterSelect(SelectedFilterBase):
    """Applied 'select' filter chosen by the user."""
```

Represents a select-type filter with a specific value selected.

**Attributes:**

- **type** (`Literal["select"]`): Type identifier, always `"select"`
- **label** (`str`): Human-readable label
- **name** (`str`): Unique identifier
- **value** (`UUID | bool | str | None`): Selected value. Default: `None`

### SelectedFilterDate

```python
class SelectedFilterDate(SelectedFilterBase):
    """Applied 'date' filter chosen by the user."""
```

Represents a date-type filter with a specific range selected.

**Attributes:**

- **type** (`Literal["date"]`): Type identifier, always `"date"`
- **label** (`str`): Human-readable label
- **name** (`str`): Unique identifier
- **value** (`TimeRange`): Date/datetime range selected

### SelectedFilterNumber

```python
class SelectedFilterNumber(SelectedFilterBase):
    """Applied 'number' filter chosen by the user."""
```

Represents a number-type filter with a specific range selected.

**Attributes:**

- **type** (`Literal["number"]`): Type identifier, always `"number"`
- **label** (`str`): Human-readable label
- **name** (`str`): Unique identifier
- **value** (`NumberRange`): Numeric range selected

### SelectedFilterSearch

```python
class SelectedFilterSearch(SelectedFilterBase):
    """Applied 'search' filter containing a free-text query."""
```

Represents a search-type filter with a free-text query.

**Attributes:**

- **type** (`Literal["search"]`): Type identifier, always `"search"`
- **label** (`str`): Human-readable label
- **name** (`str`): Unique identifier
- **value** (`str`): Free-text query string

### SelectedFilter

```python
SelectedFilter = Annotated[
    Union[
        SelectedFilterSelect,
        SelectedFilterDate,
        SelectedFilterNumber,
        SelectedFilterSearch,
    ],
    Field(discriminator="type"),
]
```

Discriminated union of all possible selected filter types.

### SearchResponseSelectedFilters

```python
class SearchResponseSelectedFilters(BaseModel):
    """Response payload listing all filters applied by the user."""
```

Contains the list of filters currently active in the user's search.

**Attributes:**

- **selected_filters** (`list[SelectedFilter]`): List of currently applied filters

## Usage Examples

### Available Filters Endpoint

```python
from dtpyfw.api.schemas.filters import (
    SearchResponseAvailableFilters,
    FilterOptionSelect,
    FilterOptionDate,
    FilterOptionNumber,
    FilterSelectValue
)
from dtpyfw.api.schemas.models import TimeRange, NumberRange
from datetime import datetime

@app.get("/products/filters", response_model=SearchResponseAvailableFilters)
def get_available_filters():
    return {
        "available_filters": [
            FilterOptionSelect(
                type="select",
                label="Category",
                name="category",
                value=[
                    FilterSelectValue(label="Electronics", value="electronics"),
                    FilterSelectValue(label="Clothing", value="clothing"),
                    FilterSelectValue(label="Books", value="books"),
                ]
            ),
            FilterOptionSelect(
                type="select",
                label="In Stock",
                name="in_stock",
                value=[
                    FilterSelectValue(label="Yes", value=True),
                    FilterSelectValue(label="No", value=False),
                ]
            ),
            FilterOptionNumber(
                type="number",
                label="Price Range",
                name="price",
                value=NumberRange(min=0, max=1000)
            ),
            FilterOptionDate(
                type="date",
                label="Added Date",
                name="created_date",
                value=TimeRange(
                    min=datetime(2024, 1, 1),
                    max=datetime(2025, 12, 31)
                )
            ),
        ]
    }
```

### Apply Filters Endpoint

```python
from dtpyfw.api.schemas.filters import SelectedFilter
from pydantic import BaseModel

class SearchRequest(BaseModel):
    filters: list[SelectedFilter]
    page: int = 1
    limit: int = 20

@app.post("/products/search")
def search_products(request: SearchRequest):
    query = Product.query
    
    # Apply each filter
    for filter in request.filters:
        if filter.type == "select":
            query = query.filter(
                getattr(Product, filter.name) == filter.value
            )
        elif filter.type == "number":
            if filter.value.min is not None:
                query = query.filter(
                    getattr(Product, filter.name) >= filter.value.min
                )
            if filter.value.max is not None:
                query = query.filter(
                    getattr(Product, filter.name) <= filter.value.max
                )
        elif filter.type == "date":
            if filter.value.min:
                query = query.filter(
                    getattr(Product, filter.name) >= filter.value.min
                )
            if filter.value.max:
                query = query.filter(
                    getattr(Product, filter.name) <= filter.value.max
                )
        elif filter.type == "search":
            query = query.filter(
                Product.name.ilike(f"%{filter.value}%")
            )
    
    products = query.paginate(page=request.page, per_page=request.limit)
    return {"products": products}

# Request:
# {
#   "filters": [
#     {
#       "type": "select",
#       "label": "Category",
#       "name": "category",
#       "value": "electronics"
#     },
#     {
#       "type": "number",
#       "label": "Price",
#       "name": "price",
#       "value": {"min": 100, "max": 500}
#     }
#   ],
#   "page": 1,
#   "limit": 20
# }
```

### Selected Filters Response

```python
from dtpyfw.api.schemas.filters import (
    SearchResponseSelectedFilters,
    SelectedFilterSelect,
    SelectedFilterNumber
)

@app.get("/products/current-filters", response_model=SearchResponseSelectedFilters)
def get_selected_filters(session_id: str):
    # Retrieve user's current filter selection
    user_filters = get_user_filters(session_id)
    
    return {
        "selected_filters": [
            SelectedFilterSelect(
                type="select",
                label="Category",
                name="category",
                value="electronics"
            ),
            SelectedFilterNumber(
                type="number",
                label="Price",
                name="price",
                value=NumberRange(min=100, max=500)
            ),
        ]
    }
```

### Dynamic Filter Generation

```python
from dtpyfw.api.schemas.filters import FilterOptionSelect, FilterSelectValue

@app.get("/users/filters")
def get_user_filters():
    # Get unique roles from database
    roles = db.session.query(User.role).distinct().all()
    
    role_filter = FilterOptionSelect(
        type="select",
        label="User Role",
        name="role",
        value=[
            FilterSelectValue(label=role[0].title(), value=role[0])
            for role in roles
        ]
    )
    
    return {"available_filters": [role_filter]}
```

### UUID-Based Filters

```python
from uuid import UUID
from dtpyfw.api.schemas.filters import FilterOptionSelect, FilterSelectValue

@app.get("/items/filters")
def get_item_filters():
    # Get dealers for filter
    dealers = Dealer.query.all()
    
    dealer_filter = FilterOptionSelect(
        type="select",
        label="Dealer",
        name="dealer_id",
        value=[
            FilterSelectValue(
                label=dealer.name,
                value=dealer.id  # UUID
            )
            for dealer in dealers
        ]
    )
    
    return {"available_filters": [dealer_filter]}
```

### Multi-Select Filters

```python
from pydantic import BaseModel

class MultiSelectFilter(BaseModel):
    type: str = "select"
    label: str
    name: str
    values: list[str | UUID | bool]  # Multiple selected values

@app.post("/products/search")
def search_with_multi_select(filters: list[MultiSelectFilter]):
    query = Product.query
    
    for filter in filters:
        if filter.values:
            query = query.filter(
                getattr(Product, filter.name).in_(filter.values)
            )
    
    return {"products": query.all()}
```

### Complex Filter Combination

```python
from dtpyfw.api.schemas.filters import SelectedFilter
from dtpyfw.api.schemas.models import SearchPayload

class AdvancedSearchRequest(SearchPayload):
    filters: list[SelectedFilter] = []

@app.post("/advanced-search")
def advanced_search(request: AdvancedSearchRequest):
    query = Product.query
    
    # Apply free-text search
    if request.search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f"%{request.search}%"),
                Product.description.ilike(f"%{request.search}%")
            )
        )
    
    # Apply filters
    for filter in request.filters:
        query = apply_filter(query, filter)
    
    # Apply sorting
    if request.sorting:
        for sort in request.sorting:
            field = getattr(Product, sort.sort_by)
            query = query.order_by(
                field.desc() if sort.order_by == "desc" else field.asc()
            )
    
    # Paginate
    products = query.paginate(
        page=request.page,
        per_page=request.items_per_page
    )
    
    return {
        "products": products,
        "total": products.total,
        "page": request.page
    }
```

## Best Practices

1. **Expose Available Filters**: Always provide an endpoint showing available filters
2. **Type Safety**: Use discriminated unions for automatic type routing
3. **Clear Labels**: Use descriptive, user-friendly filter labels
4. **Validate Values**: Ensure selected filter values match available options
5. **Index Filtered Fields**: Database index fields commonly used in filters
6. **Dynamic Options**: Generate select options dynamically from database
7. **Persist Selections**: Store user's filter selections for better UX

## Common Patterns

### Faceted Search

```python
@app.post("/faceted-search")
def faceted_search(filters: list[SelectedFilter]):
    # Apply filters to get matching products
    products = apply_filters(Product.query, filters).all()
    
    # Calculate facet counts
    facets = {
        "categories": count_by_field(products, "category"),
        "brands": count_by_field(products, "brand"),
        "price_ranges": calculate_price_ranges(products)
    }
    
    return {
        "products": products,
        "facets": facets
    }
```

### Filter Validation

```python
def validate_filter(filter: SelectedFilter, available: list[FilterOption]) -> bool:
    """Validate that selected filter matches available options."""
    available_filter = next(
        (f for f in available if f.name == filter.name),
        None
    )
    
    if not available_filter:
        return False
    
    if filter.type != available_filter.type:
        return False
    
    # Additional validation based on type
    if filter.type == "select":
        valid_values = [v.value for v in available_filter.value]
        return filter.value in valid_values
    
    return True
```

## Testing

```python
from dtpyfw.api.schemas.filters import FilterOptionSelect, FilterSelectValue

def test_filter_option_select():
    filter = FilterOptionSelect(
        type="select",
        label="Status",
        name="status",
        value=[
            FilterSelectValue(label="Active", value="active"),
            FilterSelectValue(label="Inactive", value="inactive"),
        ]
    )
    
    assert filter.type == "select"
    assert filter.label == "Status"
    assert len(filter.value) == 2

def test_selected_filter_discriminator():
    # Test that discriminator correctly routes to type
    data = {
        "type": "select",
        "label": "Category",
        "name": "category",
        "value": "electronics"
    }
    
    filter = SelectedFilter.model_validate(data)
    assert isinstance(filter, SelectedFilterSelect)
```

## Related Modules

- [`dtpyfw.api.schemas.models`](models.md): Common request/response models
- [`dtpyfw.api.schemas.response`](response.md): Response schemas
- [`dtpyfw.db.search`](../../db/search.md): Database search utilities
- [`dtpyfw.db.search_utils`](../../db/search_utils/): Advanced search utilities
- Pydantic Discriminated Unions: [Pydantic Documentation](https://docs.pydantic.dev/latest/concepts/unions/)
