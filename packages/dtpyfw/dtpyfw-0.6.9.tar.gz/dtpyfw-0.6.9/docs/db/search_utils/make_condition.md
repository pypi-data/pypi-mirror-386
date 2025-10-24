# SQL Condition Builders (`dtpyfw.db.search_utils.make_condition`)

## Overview

The `make_condition` module provides functions to construct SQLAlchemy WHERE conditions from filter definitions and user-selected values. It supports select, number, and date filter types with various matching strategies.

## Module Location

```python
from dtpyfw.db.search_utils.make_condition import make_condition
```

**Note:** This module is primarily for internal use by `get_list()`.

## Functions

### `make_condition`

```python
make_condition(
    filter_item: dict[str, Any],
    values: Any
) -> ColumnElement[bool] | None
```

Build SQL WHERE conditions from filter definitions and selected values.

Routes to the appropriate condition builder based on filter type, creating SQLAlchemy boolean expressions for filtering queries.

**Parameters:**

- `filter_item` (dict[str, Any]): Dictionary defining the filter including type and configuration
- `values` (Any): The selected filter values (list for select, dict for ranges)

**Returns:**

- `ColumnElement[bool] | None`: A SQLAlchemy boolean expression representing the filter condition, or `None` if the filter type is not supported

**Example:**

```python
# This is called internally by get_list()
condition = make_condition(
    filter_item={
        "name": "status",
        "type": "select",
        "columns": [User.status],
        "case_insensitive": True
    },
    values=["active", "pending"]
)

# Use in query
query = query.where(condition)
```

## Filter Type Handlers

### Select Conditions (`select_condition_maker`)

```python
select_condition_maker(
    filter_item: dict[str, Any],
    values: list[Any],
    array_mode: bool
) -> ColumnElement[bool]
```

Build SQL conditions for select-based filters with optional similarity search.

**Filter Configuration:**

```python
{
    "type": "select" or "select_array",
    "columns": [User.status, User.type],
    "columns_logic": "or",  # or "and_"
    "case_insensitive": True,
    "use_similarity": False,
    "similarity_threshold": 0.3
}
```

**Examples:**

```python
# Simple select
condition = make_condition(
    {"type": "select", "columns": [User.status]},
    ["active", "pending"]
)
# Generates: User.status IN ('active', 'pending')

# Case-insensitive select
condition = make_condition(
    {"type": "select", "columns": [User.name], "case_insensitive": True},
    ["John"]
)
# Generates: LOWER(User.name) IN ('john')

# Multi-column OR
condition = make_condition(
    {
        "type": "select",
        "columns": [User.status, User.type],
        "columns_logic": "or"
    },
    ["active"]
)
# Generates: (User.status IN ('active')) OR (User.type IN ('active'))

# Array overlap
condition = make_condition(
    {"type": "select_array", "columns": [Post.tags]},
    ["python", "tutorial"]
)
# Generates: Post.tags && ARRAY['python', 'tutorial']

# Similarity search
condition = make_condition(
    {
        "type": "select",
        "columns": [User.name],
        "use_similarity": True,
        "similarity_threshold": 0.3
    },
    ["John"]
)
# Generates: similarity(User.name, 'John') >= 0.3
```

### Number Conditions (`number_condition_maker`)

```python
number_condition_maker(
    filter_item: dict[str, Any],
    values: dict[str, Any]
) -> ColumnElement[bool] | None
```

Build SQL conditions for numeric range filters.

**Filter Configuration:**

```python
{
    "type": "number",
    "columns": [User.age, User.score],
    "columns_logic": "or"  # or "and"
}
```

**Examples:**

```python
# Both min and max
condition = make_condition(
    {"type": "number", "columns": [User.age]},
    {"min": 18, "max": 65}
)
# Generates: User.age BETWEEN 18 AND 65

# Only minimum
condition = make_condition(
    {"type": "number", "columns": [User.age]},
    {"min": 18, "max": None}
)
# Generates: User.age >= 18

# Only maximum
condition = make_condition(
    {"type": "number", "columns": [Product.price]},
    {"min": None, "max": 100}
)
# Generates: Product.price <= 100

# Multi-column OR
condition = make_condition(
    {
        "type": "number",
        "columns": [User.age, User.years_experience],
        "columns_logic": "or"
    },
    {"min": 5, "max": 10}
)
# Generates: (User.age BETWEEN 5 AND 10) OR (User.years_experience BETWEEN 5 AND 10)
```

### Date Conditions (`date_condition_maker`)

```python
date_condition_maker(
    filter_item: dict[str, Any],
    values: dict[str, datetime]
) -> ColumnElement[bool] | None
```

Build SQL conditions for date range filters.

**Filter Configuration:**

```python
{
    "type": "date",
    "columns": [User.created_at, User.updated_at],
    "columns_logic": "or"  # or "and"
}
```

**Examples:**

```python
from datetime import datetime

# Both min and max
condition = make_condition(
    {"type": "date", "columns": [User.created_at]},
    {
        "min": datetime(2024, 1, 1),
        "max": datetime(2024, 12, 31)
    }
)
# Generates: User.created_at BETWEEN '2024-01-01' AND '2024-12-31'

# Only start date
condition = make_condition(
    {"type": "date", "columns": [User.registered_at]},
    {"min": datetime(2024, 1, 1), "max": None}
)
# Generates: User.registered_at >= '2024-01-01'

# Only end date (allows NULL)
condition = make_condition(
    {"type": "date", "columns": [User.last_login]},
    {"min": None, "max": datetime(2024, 12, 31)}
)
# Generates: (User.last_login <= '2024-12-31') OR (User.last_login IS NULL)
```

## Advanced Features

### Case-Insensitive Matching

```python
filter_item = {
    "type": "select",
    "columns": [User.email],
    "case_insensitive": True
}
values = ["John@Example.COM"]

condition = make_condition(filter_item, values)
# Generates: LOWER(User.email) IN ('john@example.com')
```

### Enum Support

```python
from enum import Enum

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

filter_item = {
    "type": "select",
    "columns": [User.status]
}
values = [UserStatus.ACTIVE, UserStatus.INACTIVE]

condition = make_condition(filter_item, values)
# Automatically extracts enum values
# Generates: User.status IN ('active', 'inactive')
```

### Similarity Matching

```python
filter_item = {
    "type": "select",
    "columns": [User.name],
    "use_similarity": True,
    "similarity_threshold": 0.3
}
values = ["Jonh"]  # Misspelled

condition = make_condition(filter_item, values)
# Uses fuzzy matching
# Generates: similarity(User.name, 'Jonh') >= 0.3
```

### Multi-Column Logic

```python
# OR logic (default)
filter_item = {
    "type": "select",
    "columns": [User.first_name, User.last_name],
    "columns_logic": "or"
}
values = ["John"]

condition = make_condition(filter_item, values)
# Generates: (User.first_name IN ('John')) OR (User.last_name IN ('John'))

# AND logic
filter_item = {
    "type": "select",
    "columns": [User.first_name, User.last_name],
    "columns_logic": "and_"
}
values = ["John"]

condition = make_condition(filter_item, values)
# Generates: (User.first_name IN ('John')) AND (User.last_name IN ('John'))
```

### Array Operations

```python
filter_item = {
    "type": "select_array",
    "columns": [Post.tags]
}
values = ["python", "tutorial", "beginner"]

condition = make_condition(filter_item, values)
# Generates: Post.tags && ARRAY['python', 'tutorial', 'beginner']
# (checks if arrays have any overlapping elements)
```

## Usage in get_list

This function is automatically called by `get_list()` for each active filter:

```python
result = get_list(
    current_query={
        "status": ["active", "pending"],  # Triggers make_condition for status
        "age": {"min": 18, "max": 65},    # Triggers make_condition for age
    },
    db=session,
    model=User,
    filters=[
        {
            "name": "status",
            "type": "select",
            "columns": [User.status]
        },
        {
            "name": "age",
            "type": "number",
            "columns": [User.age]
        }
    ]
)
```

## Error Handling

### Invalid Filter Type

```python
condition = make_condition(
    {"type": "invalid_type", "columns": [User.name]},
    ["value"]
)
# Returns: None
```

### Missing Required Values

```python
# Empty range
condition = make_condition(
    {"type": "number", "columns": [User.age]},
    {"min": None, "max": None}
)
# Returns: None
```

## Performance Considerations

### Indexes

Ensure appropriate indexes exist:

```sql
-- For select filters
CREATE INDEX idx_user_status ON users(status);

-- For case-insensitive select
CREATE INDEX idx_user_email_lower ON users(LOWER(email));

-- For number ranges
CREATE INDEX idx_user_age ON users(age);

-- For date ranges
CREATE INDEX idx_user_created_at ON users(created_at);

-- For similarity search
CREATE INDEX idx_user_name_trgm ON users USING GIN (name gin_trgm_ops);

-- For array overlap
CREATE INDEX idx_post_tags ON posts USING GIN (tags);
```

### Query Optimization

- Multi-column filters use OR/AND as specified
- Date filters with NULL handling add OR clauses
- Similarity searches require trigram indexes
- Array operations use GIN indexes

## Related Documentation

- [../search.md](../search.md) - Main search functionality
- [../schema.md](../schema.md) - Filter schemas
- [PostgreSQL Array Functions](https://www.postgresql.org/docs/current/functions-array.html)

## Notes

- This is an internal utility used by `get_list()`
- Optimized for PostgreSQL
- Handles NULL values appropriately for date filters
- Supports complex multi-column and multi-value conditions
- Automatic enum value extraction
