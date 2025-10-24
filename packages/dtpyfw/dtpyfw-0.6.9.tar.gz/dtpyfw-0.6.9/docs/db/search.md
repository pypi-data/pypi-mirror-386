# Advanced Search Function (`dtpyfw.db.search`)

## Overview

The `search` module provides the powerful `get_list` function for advanced querying, filtering, sorting, and pagination of SQLAlchemy models. It supports select filters, numeric ranges, date ranges, free-text search, dynamic sorting, eager loading of relationships, and metadata generation for available filters.

## Module Location

```python
from dtpyfw.db.search import get_list
from dtpyfw.db.schema import (
    Payload,
    SearchResult,
    AvailableFilterType,
    SearchType
)
```

## Functions

### `get_list`

Advanced search function with extensive filtering, sorting, and pagination capabilities. The function has three overloaded signatures depending on the `export_mode` and `return_as_dict` parameters.

**Signatures:**

```python
# Overload 1: Export mode (returns List[Dict])
def get_list(
    db: Session,
    model: Type[DeclarativeBase],
    *,
    export_mode: Literal[True],
    return_as_dict: bool = True,
    payload: Payload | None = None,
    available_filters: Dict[str, Dict[str, Any]] | None = None,
    pre_conditions: List[ColumnElement[bool]] | None = None,
    free_search_columns: List[str] | None = None,
    joins: List[Any] | None = None,
    joinedload_relationships: List[str] | None = None
) -> List[Dict[str, Any]]: ...

# Overload 2: Dictionary mode (returns SearchResult[RowsListDict])
def get_list(
    db: Session,
    model: Type[DeclarativeBase],
    *,
    export_mode: Literal[False] = False,
    return_as_dict: Literal[True],
    payload: Payload | None = None,
    available_filters: Dict[str, Dict[str, Any]] | None = None,
    pre_conditions: List[ColumnElement[bool]] | None = None,
    free_search_columns: List[str] | None = None,
    joins: List[Any] | None = None,
    joinedload_relationships: List[str] | None = None
) -> SearchResult[RowsListDict]: ...

# Overload 3: Model mode (returns SearchResult[RowsListModelType])
def get_list(
    db: Session,
    model: Type[DeclarativeBase],
    *,
    export_mode: Literal[False] = False,
    return_as_dict: Literal[False] = False,
    payload: Payload | None = None,
    available_filters: Dict[str, Dict[str, Any]] | None = None,
    pre_conditions: List[ColumnElement[bool]] | None = None,
    free_search_columns: List[str] | None = None,
    joins: List[Any] | None = None,
    joinedload_relationships: List[str] | None = None
) -> SearchResult[RowsListModelType]: ...
```

**Parameters:**

- `db` (Session): SQLAlchemy session for database operations
- `model` (Type[DeclarativeBase]): The SQLAlchemy model class to query

**Keyword-Only Parameters:**

- `export_mode` (bool): If `True`, returns only rows as a list (no metadata). Default: `False`
- `return_as_dict` (bool): If `True`, rows are dictionaries; otherwise model instances. Default: `False`
- `payload` (Payload | None): Search payload containing filters, pagination, and sorting. Default: `None`
- `available_filters` (Dict[str, Dict[str, Any]] | None): Filter metadata definitions. Default: `None`
- `pre_conditions` (List[ColumnElement[bool]] | None): Additional WHERE conditions applied before filters. Default: `None`
- `free_search_columns` (List[str] | None): Column names to include in free-text search. Default: `None`
- `joins` (List[Any] | None): Additional joins to apply to the query. Default: `None`
- `joinedload_relationships` (List[str] | None): Relationship names to eager load. Default: `None`

**Returns:**

- If `export_mode=True`: `List[Dict[str, Any]]` - Raw list of dictionaries
- If `return_as_dict=True`: `SearchResult[RowsListDict]` - Result with dict rows and metadata
- If `return_as_dict=False`: `SearchResult[RowsListModelType]` - Result with model rows and metadata

**Raises:**

- `SQLAlchemyError`: If database query fails
- `ValidationError`: If payload contains invalid filter data

## Basic Usage

### Simple Query

```python
from dtpyfw.db.search import get_list
from dtpyfw.db.schema import Payload

with db.get_db_cm_read() as session:
    # Basic query with pagination
    result = get_list(
        session,
        User,
        payload=Payload(limit=20, offset=0)
    )
    
    print(f"Total users: {result.total}")
    for user in result.rows:
        print(user.name)
```

### Dictionary Mode

```python
# Return rows as dictionaries
result = get_list(
    session,
    User,
    return_as_dict=True,
    payload=Payload(limit=20, offset=0)
)

for user_dict in result.rows:
    print(f"ID: {user_dict['id']}, Name: {user_dict['name']}")
```

### Export Mode

```python
# Get only rows without metadata
rows = get_list(
    session,
    User,
    export_mode=True,
    payload=Payload(limit=100, offset=0)
)

# rows is List[Dict[str, Any]]
for row in rows:
    print(row['name'])
```

## Filter Types

### Select Filters (Single Value)

Filter by exact match on a column.

**Available Filter Definition:**

```python
from dtpyfw.db.schema import AvailableFilterType

available_filters = {
    "status": {
        "type": AvailableFilterType.SELECT,
        "label": "Status",
        "values": ["active", "inactive", "pending"]
    }
}
```

**Selected Filter:**

```python
from dtpyfw.db.schema import Payload, SelectedFilterSelect

payload = Payload(
    selected_filters=[
        SelectedFilterSelect(type="select", field="status", value="active")
    ]
)

result = get_list(
    session,
    User,
    available_filters=available_filters,
    payload=payload
)
```

**Generated SQL:**

```sql
WHERE users.status = 'active'
```

### Select Array Filters (Multiple Values)

Filter by matching any of multiple values (IN clause).

**Available Filter Definition:**

```python
available_filters = {
    "category": {
        "type": AvailableFilterType.SELECT_ARRAY,
        "label": "Category",
        "values": ["electronics", "computers", "accessories"]
    }
}
```

**Selected Filters:**

```python
# Pass multiple filters with same field for SELECT_ARRAY
payload = Payload(
    selected_filters=[
        SelectedFilterSelect(type="select", field="category", value="electronics"),
        SelectedFilterSelect(type="select", field="category", value="computers")
    ]
)

result = get_list(session, Product, payload=payload)
```

**Generated SQL:**

```sql
WHERE products.category IN ('electronics', 'computers')
```

### Number Filters (Numeric Ranges)

Filter by numeric range with optional min and/or max bounds.

**Available Filter Definition:**

```python
available_filters = {
    "price": {
        "type": AvailableFilterType.NUMBER,
        "label": "Price",
        "values": {"min": 0, "max": 9999.99}
    }
}
```

**Selected Filter:**

```python
from dtpyfw.db.schema import SelectedFilterNumber

payload = Payload(
    selected_filters=[
        SelectedFilterNumber(type="number", field="price", min=100, max=500)
    ]
)

result = get_list(session, Product, payload=payload)
```

**Generated SQL:**

```sql
WHERE products.price >= 100 AND products.price <= 500
```

**Variations:**

```python
# Only minimum
SelectedFilterNumber(type="number", field="price", min=100)
# SQL: WHERE products.price >= 100

# Only maximum
SelectedFilterNumber(type="number", field="price", max=500)
# SQL: WHERE products.price <= 500
```

### Date Filters (Date/DateTime Ranges)

Filter by date or datetime range with optional min and/or max bounds.

**Available Filter Definition:**

```python
from datetime import datetime

available_filters = {
    "created_at": {
        "type": AvailableFilterType.DATE,
        "label": "Created Date",
        "values": {
            "min": datetime(2020, 1, 1),
            "max": datetime.now()
        }
    }
}
```

**Selected Filter:**

```python
from datetime import datetime, timedelta
from dtpyfw.db.schema import SelectedFilterDate

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
    ]
)

result = get_list(session, Order, payload=payload)
```

**Generated SQL:**

```sql
WHERE orders.created_at >= '2024-09-24 10:00:00' 
  AND orders.created_at <= '2024-10-24 10:00:00'
```

### Search Filters (Free-Text Search)

Full-text search or substring matching across specified columns.

**Available Filter Definition:**

```python
available_filters = {
    "search": {
        "type": AvailableFilterType.SEARCH,
        "label": "Search",
        "values": []
    }
}
```

**Selected Filter (ICONTAINS):**

```python
from dtpyfw.db.schema import SelectedFilterSearch, SearchType

payload = Payload(
    selected_filters=[
        SelectedFilterSearch(
            type="search",
            field="name",
            value="laptop",
            search_type=SearchType.ICONTAINS
        )
    ]
)

result = get_list(session, Product, payload=payload)
```

**Generated SQL:**

```sql
WHERE LOWER(products.name) LIKE LOWER('%laptop%')
```

**Selected Filter (FREE_SEARCH - PostgreSQL Full-Text):**

```python
payload = Payload(
    selected_filters=[
        SelectedFilterSearch(
            type="search",
            field="description_search",  # Must be a tsvector column
            value="laptop computer",
            search_type=SearchType.FREE_SEARCH
        )
    ]
)

result = get_list(session, Product, payload=payload)
```

**Generated SQL:**

```sql
WHERE products.description_search @@ to_tsquery('simple', 'laptop:* & computer:*')
```

**Multi-Column Search:**

```python
# Search across multiple columns using free_search_columns
payload = Payload(
    selected_filters=[
        SelectedFilterSearch(
            type="search",
            field="search",  # Generic field name
            value="john",
            search_type=SearchType.ICONTAINS
        )
    ]
)

result = get_list(
    session,
    User,
    payload=payload,
    free_search_columns=["name", "email", "username"]
)
```

**Generated SQL:**

```sql
WHERE (
    LOWER(users.name) LIKE LOWER('%john%')
    OR LOWER(users.email) LIKE LOWER('%john%')
    OR LOWER(users.username) LIKE LOWER('%john%')
)
```

## Sorting

### Basic Sorting

```python
from dtpyfw.db.schema import Payload, PayloadSorting

payload = Payload(
    sorting=PayloadSorting(field="created_at", direction="desc"),
    limit=20,
    offset=0
)

result = get_list(session, User, payload=payload)
```

**Generated SQL:**

```sql
ORDER BY users.created_at DESC
```

### Ascending Sort

```python
payload = Payload(
    sorting=PayloadSorting(field="name", direction="asc")
)

result = get_list(session, User, payload=payload)
```

**Generated SQL:**

```sql
ORDER BY users.name ASC
```

### Default Sorting

If no sorting is specified, results are ordered by the primary key:

```python
payload = Payload(limit=20, offset=0)  # No sorting

result = get_list(session, User, payload=payload)
# SQL: ORDER BY users.id ASC
```

## Pagination

### Basic Pagination

```python
from dtpyfw.db.schema import Payload

# Page 1 (first 20 records)
payload = Payload(limit=20, offset=0)
result = get_list(session, User, payload=payload)

print(f"Total: {result.total}")
print(f"Showing: {len(result.rows)}")
```

### Page Navigation

```python
def get_page(session, model, page: int, page_size: int = 20):
    offset = (page - 1) * page_size
    payload = Payload(limit=page_size, offset=offset)
    return get_list(session, model, payload=payload)

# Get different pages
page1 = get_page(session, User, page=1)
page2 = get_page(session, User, page=2)
page3 = get_page(session, User, page=3)

# Calculate total pages
total_pages = (page1.total + page1.limit - 1) // page1.limit
```

### Unlimited Results

```python
# Get all records (use with caution)
payload = Payload(limit=999999, offset=0)
result = get_list(session, User, payload=payload)
```

## Pre-Conditions

Apply additional WHERE conditions before filters are applied.

### Simple Pre-Condition

```python
from sqlalchemy import and_

# Only query active users
pre_conditions = [User.is_active == True]

result = get_list(
    session,
    User,
    pre_conditions=pre_conditions,
    payload=Payload(limit=20, offset=0)
)
```

**Generated SQL:**

```sql
WHERE users.is_active = true
  AND ... (other filters)
```

### Multiple Pre-Conditions

```python
from datetime import datetime, timedelta

# Users created in last year and email verified
one_year_ago = datetime.now() - timedelta(days=365)
pre_conditions = [
    User.created_at >= one_year_ago,
    User.email_verified == True,
    User.status != "banned"
]

result = get_list(
    session,
    User,
    pre_conditions=pre_conditions,
    payload=Payload(limit=50, offset=0)
)
```

**Generated SQL:**

```sql
WHERE users.created_at >= '2023-10-24 10:00:00'
  AND users.email_verified = true
  AND users.status != 'banned'
  AND ... (other filters)
```

### Pre-Conditions with Relationships

```python
from sqlalchemy.orm import aliased

# Users with at least one order
pre_conditions = [
    User.orders.any()  # Relationship existence check
]

result = get_list(
    session,
    User,
    pre_conditions=pre_conditions,
    payload=Payload(limit=20, offset=0)
)
```

## Joins and Relationships

### Basic Joins

```python
from sqlalchemy import join

# Join with related table
joins = [
    join(User, Address, User.id == Address.user_id)
]

result = get_list(
    session,
    User,
    joins=joins,
    payload=Payload(limit=20, offset=0)
)
```

### Eager Loading (Joinedload)

Efficiently load related objects to avoid N+1 queries.

```python
# Eager load relationships
result = get_list(
    session,
    User,
    joinedload_relationships=["profile", "orders"],
    payload=Payload(limit=20, offset=0)
)

# Access relationships without additional queries
for user in result.rows:
    print(user.profile.bio)  # No additional query
    print(f"Orders: {len(user.orders)}")  # No additional query
```

### Filtering on Joined Tables

```python
from sqlalchemy import join

# Filter users by their address city
pre_conditions = [
    Address.city == "New York"
]

joins = [
    join(User, Address, User.id == Address.user_id)
]

result = get_list(
    session,
    User,
    joins=joins,
    pre_conditions=pre_conditions,
    payload=Payload(limit=20, offset=0)
)
```

## Available Filters Metadata

Generate metadata about available filters for UI rendering.

### Complete Example

```python
from dtpyfw.db.schema import AvailableFilterType
from datetime import datetime

available_filters = {
    "status": {
        "type": AvailableFilterType.SELECT,
        "label": "Status",
        "values": ["active", "inactive", "pending"]
    },
    "category": {
        "type": AvailableFilterType.SELECT_ARRAY,
        "label": "Categories",
        "values": ["electronics", "computers", "accessories", "software"]
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
            "min": datetime(2020, 1, 1),
            "max": datetime.now()
        }
    },
    "search": {
        "type": AvailableFilterType.SEARCH,
        "label": "Search",
        "values": []
    }
}

result = get_list(
    session,
    Product,
    available_filters=available_filters,
    payload=Payload(limit=20, offset=0)
)

# result.available_filters contains metadata for UI
for filter_def in result.available_filters:
    print(f"Filter: {filter_def.label}")
    print(f"Type: {filter_def.type}")
    if hasattr(filter_def, 'values'):
        print(f"Options: {filter_def.values}")
```

### Dynamic Filter Values

Generate filter values dynamically from database:

```python
from sqlalchemy import select, func

# Get distinct status values
distinct_statuses = session.execute(
    select(Product.status).distinct()
).scalars().all()

# Get price range
min_price, max_price = session.execute(
    select(func.min(Product.price), func.max(Product.price))
).first()

available_filters = {
    "status": {
        "type": AvailableFilterType.SELECT,
        "label": "Status",
        "values": list(distinct_statuses)
    },
    "price": {
        "type": AvailableFilterType.NUMBER,
        "label": "Price",
        "values": {"min": min_price, "max": max_price}
    }
}

result = get_list(
    session,
    Product,
    available_filters=available_filters,
    payload=Payload(limit=20, offset=0)
)
```

## Complete Examples

### E-Commerce Product Search

```python
from dtpyfw.db.search import get_list
from dtpyfw.db.schema import (
    Payload,
    SelectedFilterSelect,
    SelectedFilterNumber,
    SelectedFilterDate,
    SelectedFilterSearch,
    PayloadSorting,
    AvailableFilterType,
    SearchType
)
from datetime import datetime, timedelta

# Define available filters
available_filters = {
    "category": {
        "type": AvailableFilterType.SELECT_ARRAY,
        "label": "Category",
        "values": ["Electronics", "Computers", "Accessories", "Software"]
    },
    "price": {
        "type": AvailableFilterType.NUMBER,
        "label": "Price",
        "values": {"min": 0, "max": 10000}
    },
    "in_stock": {
        "type": AvailableFilterType.SELECT,
        "label": "Availability",
        "values": [True, False]
    },
    "created_at": {
        "type": AvailableFilterType.DATE,
        "label": "Added Date",
        "values": {
            "min": datetime(2020, 1, 1),
            "max": datetime.now()
        }
    },
    "search": {
        "type": AvailableFilterType.SEARCH,
        "label": "Search Products",
        "values": []
    }
}

# User search: "laptop" in Electronics, price 500-1500, in stock
thirty_days_ago = datetime.now() - timedelta(days=30)

payload = Payload(
    selected_filters=[
        SelectedFilterSearch(
            type="search",
            field="search",
            value="laptop",
            search_type=SearchType.ICONTAINS
        ),
        SelectedFilterSelect(type="select", field="category", value="Electronics"),
        SelectedFilterNumber(type="number", field="price", min=500, max=1500),
        SelectedFilterSelect(type="select", field="in_stock", value=True),
        SelectedFilterDate(
            type="date",
            field="created_at",
            min=thirty_days_ago,
            max=datetime.now()
        )
    ],
    sorting=PayloadSorting(field="price", direction="asc"),
    limit=50,
    offset=0
)

with db.get_db_cm_read() as session:
    result = get_list(
        session,
        Product,
        available_filters=available_filters,
        payload=payload,
        free_search_columns=["name", "description", "sku"],
        return_as_dict=True
    )
    
    print(f"Found {result.total} products")
    print(f"Showing {len(result.rows)} results")
    
    for product in result.rows:
        print(f"{product['name']}: ${product['price']}")
```

### User Management with Soft Deletes

```python
# Query active users only (exclude soft-deleted)
pre_conditions = [
    User.is_deleted == False,
    User.email_verified == True
]

payload = Payload(
    selected_filters=[
        SelectedFilterSelect(type="select", field="role", value="admin")
    ],
    sorting=PayloadSorting(field="created_at", direction="desc"),
    limit=100,
    offset=0
)

result = get_list(
    session,
    User,
    pre_conditions=pre_conditions,
    payload=payload,
    joinedload_relationships=["profile", "permissions"]
)

for user in result.rows:
    print(f"{user.name} - {user.email}")
    print(f"  Permissions: {[p.name for p in user.permissions]}")
```

### Orders with Customer Information

```python
from sqlalchemy import join
from sqlalchemy.orm import joinedload

# Join orders with customers
joins = [
    join(Order, Customer, Order.customer_id == Customer.id)
]

# Filter: high-value orders from last month
one_month_ago = datetime.now() - timedelta(days=30)
pre_conditions = [
    Order.total >= 1000,
    Order.created_at >= one_month_ago
]

payload = Payload(
    sorting=PayloadSorting(field="total", direction="desc"),
    limit=50,
    offset=0
)

result = get_list(
    session,
    Order,
    joins=joins,
    pre_conditions=pre_conditions,
    payload=payload,
    joinedload_relationships=["customer", "items"],
    return_as_dict=True
)

for order in result.rows:
    print(f"Order #{order['id']}: ${order['total']}")
    print(f"Customer: {order['customer']['name']}")
```

### Export Mode for Reports

```python
# Generate CSV data for all active products
pre_conditions = [Product.is_active == True]

payload = Payload(
    sorting=PayloadSorting(field="name", direction="asc"),
    limit=999999,  # Get all
    offset=0
)

rows = get_list(
    session,
    Product,
    export_mode=True,  # Returns List[Dict] without metadata
    pre_conditions=pre_conditions,
    payload=payload
)

# Convert to CSV
import csv
with open('products.csv', 'w', newline='') as f:
    if rows:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
```

## FastAPI Integration

### Complete Search Endpoint

```python
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from dtpyfw.db.search import get_list
from dtpyfw.db.schema import Payload, AvailableFilterType
from datetime import datetime
from typing import Optional

app = FastAPI()

def get_db():
    yield from db.get_db_read()

@app.post("/api/products/search")
def search_products(
    payload: Payload,
    session: Session = Depends(get_db)
):
    """
    Search products with filters, pagination, and sorting.
    
    Example request body:
    {
        "selected_filters": [
            {"type": "select", "field": "category", "value": "electronics"},
            {"type": "number", "field": "price", "min": 100, "max": 500}
        ],
        "sorting": {"field": "price", "direction": "asc"},
        "limit": 20,
        "offset": 0
    }
    """
    available_filters = {
        "category": {
            "type": AvailableFilterType.SELECT_ARRAY,
            "label": "Category",
            "values": ["electronics", "computers", "accessories"]
        },
        "price": {
            "type": AvailableFilterType.NUMBER,
            "label": "Price",
            "values": {"min": 0, "max": 9999.99}
        },
        "in_stock": {
            "type": AvailableFilterType.SELECT,
            "label": "In Stock",
            "values": [True, False]
        }
    }
    
    result = get_list(
        session,
        Product,
        available_filters=available_filters,
        payload=payload,
        free_search_columns=["name", "description"],
        return_as_dict=True
    )
    
    return {
        "products": result.rows,
        "pagination": {
            "total": result.total,
            "limit": result.limit,
            "offset": result.offset,
            "pages": (result.total + result.limit - 1) // result.limit,
            "current_page": (result.offset // result.limit) + 1
        },
        "filters": {
            "available": result.available_filters,
            "selected": result.selected_filters
        }
    }

@app.get("/api/products")
def list_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_db)
):
    """Simplified query parameter API"""
    from dtpyfw.db.schema import (
        SelectedFilterSelect,
        SelectedFilterNumber,
        SelectedFilterSearch,
        PayloadSorting,
        SearchType
    )
    
    selected_filters = []
    
    if category:
        selected_filters.append(
            SelectedFilterSelect(type="select", field="category", value=category)
        )
    
    if min_price is not None or max_price is not None:
        selected_filters.append(
            SelectedFilterNumber(
                type="number",
                field="price",
                min=min_price,
                max=max_price
            )
        )
    
    if search:
        selected_filters.append(
            SelectedFilterSearch(
                type="search",
                field="search",
                value=search,
                search_type=SearchType.ICONTAINS
            )
        )
    
    offset = (page - 1) * page_size
    payload = Payload(
        selected_filters=selected_filters,
        sorting=PayloadSorting(field=sort_by, direction=sort_dir),
        limit=page_size,
        offset=offset
    )
    
    result = get_list(
        session,
        Product,
        payload=payload,
        free_search_columns=["name", "description"],
        return_as_dict=True
    )
    
    return result
```

## Performance Optimization

### Use Indexes

Ensure filtered and sorted columns have database indexes:

```python
class Product(ModelBase, db.base):
    __tablename__ = 'products'
    
    name: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    price: Mapped[float] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(index=True)
```

### Use Joinedload for Relationships

Avoid N+1 queries by eager loading:

```python
# Bad: N+1 queries
result = get_list(session, User, payload=payload)
for user in result.rows:
    print(user.profile.bio)  # Additional query per user

# Good: Single query with join
result = get_list(
    session,
    User,
    joinedload_relationships=["profile"],
    payload=payload
)
for user in result.rows:
    print(user.profile.bio)  # No additional query
```

### Use Read Replicas

```python
# Use read session for searches
with db.get_db_cm_read() as session:
    result = get_list(session, Product, payload=payload)
```

### Limit Result Size

```python
# Set reasonable limits
payload = Payload(
    limit=100,  # Don't fetch thousands of records at once
    offset=0
)
```

### Use Export Mode for Large Exports

```python
# Export mode is more memory-efficient
rows = get_list(
    session,
    Product,
    export_mode=True,
    payload=Payload(limit=10000, offset=0)
)
```

## Best Practices

1. **Always use pagination**: Don't fetch all records at once
   ```python
   payload = Payload(limit=20, offset=0)  # Good
   payload = Payload(limit=999999, offset=0)  # Bad
   ```

2. **Use appropriate filter types**: Match filter type to column type
   ```python
   # Good
   SelectedFilterNumber(type="number", field="price", min=100)
   
   # Bad - using string for numeric field
   SelectedFilterSelect(type="select", field="price", value="100")
   ```

3. **Eager load relationships**: Prevent N+1 queries
   ```python
   joinedload_relationships=["profile", "orders"]
   ```

4. **Use pre_conditions for security**: Filter by ownership/permissions
   ```python
   pre_conditions=[Product.user_id == current_user_id]
   ```

5. **Index filtered columns**: Ensure good query performance

6. **Use return_as_dict for APIs**: Serialization is automatic
   ```python
   result = get_list(session, Model, return_as_dict=True, payload=payload)
   ```

7. **Provide available_filters**: Help frontend build filter UI
   ```python
   result = get_list(
       session,
       Model,
       available_filters=filters_def,
       payload=payload
   )
   ```

8. **Use FREE_SEARCH for text columns**: Requires tsvector column but much faster
   ```python
   SearchType.FREE_SEARCH  # Faster, PostgreSQL-specific
   SearchType.ICONTAINS    # Slower, works on any column
   ```

## Related Documentation

- [schema.md](./schema.md) - Pydantic schemas for filters and results
- [database.md](./database.md) - Database instance and session management
- [model.md](./model.md) - Model base classes and CRUD operations
- [search_utils/](./search_utils/) - Internal search implementation

## Notes

- Function is overloaded with 3 signatures for type safety
- Pre-conditions are applied before selected filters
- Soft-deleted records are automatically excluded if model has `is_deleted` field
- Free-text search uses PostgreSQL `to_tsquery` for FREE_SEARCH type
- All filter types support discriminated unions via Pydantic
- Available filters metadata is only generated if `available_filters` parameter is provided
- The function automatically handles model-to-dict conversion when `return_as_dict=True`
