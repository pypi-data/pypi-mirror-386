# Filter Values Extraction (`dtpyfw.db.search_utils.filter_values`)

## Overview

The `filter_values` module provides utilities for querying the database to extract available filter options based on actual data. It generates the list of possible values for each filter type (select, number, date) by analyzing the current dataset.

## Module Location

```python
from dtpyfw.db.search_utils.filter_values import get_filters_value
```

**Note:** This module is primarily for internal use by `get_list()`. Most users should not need to import it directly.

## Functions

### `get_filters_value`

```python
get_filters_value(
    db: Session,
    pre_conditions: list[Any],
    joins: list[dict[str, Any]],
    filters: list[dict[str, Any]],
    names_conditions: dict[str, list[Any]],
) -> AvailableFilters
```

Build a list of available filter options from database data.

Queries the database for each defined filter to generate the available options based on actual data, applying pre-conditions and cross-filter conditions.

**Parameters:**

- `db` (Session): SQLAlchemy session for database queries
- `pre_conditions` (list[Any]): List of base WHERE conditions to always apply
- `joins` (list[dict[str, Any]]): List of join configurations for related tables
- `filters` (list[dict[str, Any]]): List of filter definitions
- `names_conditions` (dict[str, list[Any]]): Dictionary mapping filter names to their conditions

**Returns:**

- `AvailableFilters`: List of available filters with their possible values

**Example:**

```python
# This is called internally by get_list()
available_filters = get_filters_value(
    db=session,
    pre_conditions=[User.deleted_at.is_(None)],
    joins=[],
    filters=[
        {
            "name": "status",
            "label": "Status",
            "type": "select",
            "columns": [User.status]
        }
    ],
    names_conditions={"status": []}
)
```

## Filter Type Handling

### Select Filters

For `select` and `select_array` filter types, the function:

1. Queries distinct values from specified columns
2. Applies pre-conditions and cross-filter conditions
3. Converts values to `AvailableFilterSelectItem` with labels
4. Sorts items alphabetically by label

**Example Output:**

```python
AvailableFilterSelect(
    label="User Status",
    name="status",
    type=AvailableFilterType.select,
    value=[
        AvailableFilterSelectItem(label="Active", value="active"),
        AvailableFilterSelectItem(label="Inactive", value="inactive"),
    ]
)
```

### Number Filters

For `number` filter types, the function:

1. Queries MIN and MAX values across specified columns
2. Returns the range boundaries

**Example Output:**

```python
AvailableFilterNumber(
    label="Age",
    name="age",
    type=AvailableFilterType.number,
    value=AvailableFilterNumberItem(min=18, max=65)
)
```

### Date Filters

For `date` filter types, the function:

1. Queries earliest and latest dates across specified columns
2. Returns the date range boundaries

**Example Output:**

```python
AvailableFilterDate(
    label="Registration Date",
    name="registered_at",
    type=AvailableFilterType.date,
    value=AvailableFilterDateItem(
        min=datetime(2020, 1, 1),
        max=datetime(2025, 12, 31)
    )
)
```

## Supporting Function

### `filters_mapper`

```python
filters_mapper(
    db: Session,
    pre_conditions: list[Any],
    joins: list[dict[str, Any]],
    filter_item: dict[str, Any],
    conditions: list[Any],
) -> AvailableFilterValue
```

Internal function that extracts unique values from database columns for a single filter.

## Features

### Cross-Filter Conditions

The function applies other active filters when generating options for each filter, ensuring that:

- Filter options reflect the current filtered dataset
- Users only see relevant options based on their current selections

### Enum Support

Handles enum values automatically:

```python
filter_item = {
    "name": "status",
    "type": "select",
    "columns": [User.status],
    "enum": UserStatus,  # Enum class
    "labels": {
        UserStatus.ACTIVE: "Active Users",
        UserStatus.INACTIVE: "Inactive Users"
    }
}
```

### JSON Array Support

Supports filtering on JSONB array columns:

```python
filter_item = {
    "name": "tags",
    "type": "select_array",
    "columns": [Post.tags],
    "is_json": True  # Indicates JSONB array column
}
```

## Performance Considerations

- Uses database indexes on filtered columns for optimal performance
- Executes one query per filter to generate options
- Applies cross-filter conditions to reduce data scanning
- Uses UNION for multi-column filters

## Use in get_list

This function is automatically called by `get_list()` when `return_available_filters=True`:

```python
result = get_list(
    current_query=query,
    db=session,
    model=User,
    filters=filters,
    return_available_filters=True  # Triggers get_filters_value()
)

# Access available filters
for filter in result.available_filters:
    print(f"{filter.label}: {filter.value}")
```

## Related Documentation

- [../search.md](../search.md) - Main search functionality
- [../schema.md](../schema.md) - Available filter schemas
- [__init__.md](./__init__.md) - Search utilities overview

## Notes

- This is an internal utility primarily used by `get_list()`
- Requires proper database indexes for good performance on large datasets
- Cross-filter logic ensures UI shows only relevant filter options
- Automatically handles NULL values appropriately
