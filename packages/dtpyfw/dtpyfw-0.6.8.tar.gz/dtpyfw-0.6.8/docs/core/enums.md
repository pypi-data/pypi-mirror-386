# Enumerations

## Overview

The `dtpyfw.core.enums` module provides common enumeration definitions used across the DealerTower framework. Enums provide type-safe constants and improve code readability.

## Module Path

```python
from dtpyfw.core.enums import OrderingType
```

## Enumerations

### `OrderingType`

A string-based enumeration for generic ascending/descending ordering options.

**Base Classes:**

- `str` - Makes the enum values strings
- `Enum` - Python's base enumeration class

**Values:**

| Value | String Value | Description |
|-------|-------------|-------------|
| `OrderingType.desc` | `"desc"` | Descending order (Z-A, 9-0, newest-oldest) |
| `OrderingType.asc` | `"asc"` | Ascending order (A-Z, 0-9, oldest-newest) |

**Example:**

```python
from dtpyfw.core.enums import OrderingType

# Using in a function
def get_users(order: OrderingType = OrderingType.asc):
    if order == OrderingType.desc:
        return User.query.order_by(User.created_at.desc()).all()
    else:
        return User.query.order_by(User.created_at.asc()).all()

# Calling the function
users = get_users(order=OrderingType.desc)
```

## Use Cases

### 1. Database Query Ordering

```python
from dtpyfw.core.enums import OrderingType
from sqlalchemy import asc, desc

def fetch_products(sort_by: str = "price", order: OrderingType = OrderingType.asc):
    """Fetch products with configurable ordering."""
    query = Product.query
    
    if order == OrderingType.desc:
        query = query.order_by(desc(sort_by))
    else:
        query = query.order_by(asc(sort_by))
    
    return query.all()

# Usage
expensive_first = fetch_products(sort_by="price", order=OrderingType.desc)
cheap_first = fetch_products(sort_by="price", order=OrderingType.asc)
```

### 2. API Query Parameters

```python
from fastapi import FastAPI, Query
from dtpyfw.core.enums import OrderingType

app = FastAPI()

@app.get("/items")
def list_items(
    order: OrderingType = Query(
        default=OrderingType.asc,
        description="Sort order for results"
    )
):
    """List items with optional ordering."""
    items = get_items_from_db()
    
    if order == OrderingType.desc:
        items.reverse()
    
    return {"items": items, "order": order}
```

### 3. Pydantic Model Validation

```python
from pydantic import BaseModel
from dtpyfw.core.enums import OrderingType

class SearchRequest(BaseModel):
    query: str
    order: OrderingType = OrderingType.asc
    limit: int = 10

# Valid request
request = SearchRequest(
    query="laptop",
    order=OrderingType.desc,
    limit=20
)

print(request.order)  # Output: desc
print(type(request.order))  # Output: <enum 'OrderingType'>
```

### 4. Sorting Collections

```python
from dtpyfw.core.enums import OrderingType
from typing import List, Any

def sort_items(items: List[Any], key: str, order: OrderingType) -> List[Any]:
    """Sort a list of dictionaries by a specific key."""
    reverse = (order == OrderingType.desc)
    return sorted(items, key=lambda x: x.get(key), reverse=reverse)

# Usage
products = [
    {"name": "Product A", "price": 100},
    {"name": "Product B", "price": 50},
    {"name": "Product C", "price": 75}
]

# Sort by price descending
sorted_products = sort_items(products, "price", OrderingType.desc)
# Result: [{"name": "Product A", "price": 100}, ...]
```

### 5. Custom List Sorting

```python
from dtpyfw.core.enums import OrderingType
from datetime import datetime

class Event:
    def __init__(self, name: str, date: datetime):
        self.name = name
        self.date = date

def sort_events(events: List[Event], order: OrderingType) -> List[Event]:
    """Sort events by date."""
    return sorted(
        events,
        key=lambda e: e.date,
        reverse=(order == OrderingType.desc)
    )

# Usage
events = [
    Event("Conference", datetime(2024, 6, 1)),
    Event("Workshop", datetime(2024, 5, 15)),
    Event("Webinar", datetime(2024, 7, 10))
]

# Get most recent events first
recent_first = sort_events(events, OrderingType.desc)
```

## Advanced Usage

### Type Hints and Static Analysis

```python
from dtpyfw.core.enums import OrderingType
from typing import Literal

# Strict type hints
def process_data(order: OrderingType) -> None:
    # IDE will autocomplete and type-check
    if order == OrderingType.asc:
        print("Ascending order")
    elif order == OrderingType.desc:
        print("Descending order")

# This will be caught by type checkers
# process_data("ascending")  # Type error!

# This is correct
process_data(OrderingType.asc)  # ✓
```

### Enum Iteration

```python
from dtpyfw.core.enums import OrderingType

# Get all possible values
for order_type in OrderingType:
    print(f"Value: {order_type.value}, Name: {order_type.name}")

# Output:
# Value: desc, Name: desc
# Value: asc, Name: asc

# Check if value exists
if "asc" in [e.value for e in OrderingType]:
    print("Valid ordering type")
```

### String Comparison

```python
from dtpyfw.core.enums import OrderingType

# Since OrderingType inherits from str, you can compare directly
order = OrderingType.asc

if order == "asc":  # This works because of str inheritance
    print("Ascending order")

# But this is more type-safe
if order == OrderingType.asc:
    print("Ascending order")
```

### FastAPI Integration

```python
from fastapi import FastAPI
from dtpyfw.core.enums import OrderingType
from pydantic import BaseModel

app = FastAPI()

class SortConfig(BaseModel):
    field: str
    order: OrderingType

@app.post("/sort")
def configure_sort(config: SortConfig):
    """Configure sorting with type-safe enum."""
    return {
        "field": config.field,
        "order": config.order,
        "reverse": config.order == OrderingType.desc
    }

# Valid request body:
# {"field": "name", "order": "asc"}
# {"field": "price", "order": "desc"}
```

## Benefits of Using Enums

1. **Type Safety:** Prevents invalid values at compile time with type checkers
2. **Autocomplete:** IDEs can provide intelligent code completion
3. **Self-Documenting:** Clear indication of valid options
4. **Refactoring:** Easy to find all usages and update consistently
5. **Validation:** Automatic validation in Pydantic models and FastAPI

## Extending OrderingType

If you need additional ordering options in your application:

```python
from enum import Enum

class ExtendedOrderingType(str, Enum):
    """Extended ordering with additional options."""
    asc = "asc"
    desc = "desc"
    random = "random"
    relevance = "relevance"

def search_items(query: str, order: ExtendedOrderingType):
    if order == ExtendedOrderingType.random:
        return shuffle(search(query))
    elif order == ExtendedOrderingType.relevance:
        return search_by_relevance(query)
    # ... etc
```

## Related Modules

- **dtpyfw.db.search** - Uses OrderingType for database queries
- **dtpyfw.api.schemas.filters** - Filter schemas that use OrderingType

## Best Practices

1. **Always use enum members, not strings:**
   ```python
   # Good
   order = OrderingType.asc
   
   # Avoid
   order = "asc"  # Loses type safety
   ```

2. **Use in type hints:**
   ```python
   def sort_data(order: OrderingType) -> List[Any]:
       pass
   ```

3. **Validate user input:**
   ```python
   from fastapi import HTTPException
   
   def validate_order(order_str: str) -> OrderingType:
       try:
           return OrderingType(order_str)
       except ValueError:
           raise HTTPException(
               status_code=400,
               detail=f"Invalid order: {order_str}. Must be 'asc' or 'desc'"
           )
   ```

## Dependencies

This module has no external dependencies and uses only Python's built-in `enum` module.

## See Also

- [Python Enum Documentation](https://docs.python.org/3/library/enum.html)
- [Pydantic Enums](https://docs.pydantic.dev/latest/concepts/types/#enums-and-choices)
