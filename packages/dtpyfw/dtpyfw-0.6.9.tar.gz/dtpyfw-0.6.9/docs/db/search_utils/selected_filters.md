# Selected Filter Formatting (`dtpyfw.db.search_utils.selected_filters`)

## Overview

The `selected_filters` module provides utilities to format currently selected filters into user-friendly representations for display purposes. It converts raw filter values from query parameters into structured filter descriptions suitable for UI rendering.

## Module Location

```python
from dtpyfw.db.search_utils.selected_filters import make_selected_filters
```

**Note:** This module is primarily for internal use by `get_list()`.

## Functions

### `make_selected_filters`

```python
make_selected_filters(
    filters: list[dict[str, Any]] | None = None,
    current_query: dict[str, Any] | None = None,
) -> SelectedFilters
```

Build a list of selected filter descriptions from current query parameters.

Converts the raw filter values from the query into formatted filter descriptions suitable for display, including appropriate labels and value representations.

**Parameters:**

- `filters` (list[dict[str, Any]] | None): List of filter definitions containing metadata like labels, types, and enums
- `current_query` (dict[str, Any] | None): Dictionary containing the current query parameters with selected filter values

**Returns:**

- `SelectedFilters`: List of `SelectedFilter` objects, each representing an active filter

**Example:**

```python
# This is called internally by get_list()
selected_filters = make_selected_filters(
    filters=[
        {
            "name": "status",
            "label": "Status",
            "type": "select"
        },
        {
            "name": "age",
            "label": "Age Range",
            "type": "number"
        }
    ],
    current_query={
        "status": ["active", "pending"],
        "age": {"min": 18, "max": 65}
    }
)

for filter in selected_filters:
    print(f"{filter.label}: {filter.value}")
```

## Filter Type Handling

### Select Filters

For `select` and `select_array` types:

**Input:**

```python
current_query = {"status": ["active", "pending"]}
filter_item = {
    "name": "status",
    "label": "User Status",
    "type": "select"
}
```

**Output:**

```python
[
    SelectedFilterSelect(
        label="Active",
        name="status",
        type=SearchType.select,
        value="active"
    ),
    SelectedFilterSelect(
        label="Pending",
        name="status",
        type=SearchType.select,
        value="pending"
    )
]
```

### Select with Enums

**Input:**

```python
from enum import Enum

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

current_query = {"status": ["active"]}
filter_item = {
    "name": "status",
    "label": "User Status",
    "type": "select",
    "enum": UserStatus,
    "labels": {
        UserStatus.ACTIVE: "Active Users",
        UserStatus.INACTIVE: "Inactive Users"
    }
}
```

**Output:**

```python
[
    SelectedFilterSelect(
        label="Active Users",
        name="status",
        type=SearchType.select,
        value="ACTIVE"  # Enum name
    )
]
```

### Number Filters

For `number` type:

**Input:**

```python
current_query = {"age": {"min": 18, "max": 65}}
filter_item = {
    "name": "age",
    "label": "Age",
    "type": "number"
}
```

**Output:**

```python
[
    SelectedFilterNumber(
        label="Age (between 18 and 65)",
        name="age",
        type=SearchType.number,
        value=SelectedFilterNumberItem(min=18, max=65)
    )
]
```

**Variations:**

```python
# Only minimum
{"age": {"min": 18, "max": None}}
# Output label: "Age (From 18)"

# Only maximum
{"age": {"min": None, "max": 65}}
# Output label: "Age (To 65)"
```

### Date Filters

For `date` type:

**Input:**

```python
from datetime import datetime

current_query = {
    "registered_at": {
        "min": datetime(2024, 1, 1),
        "max": datetime(2024, 12, 31)
    }
}
filter_item = {
    "name": "registered_at",
    "label": "Registration Date",
    "type": "date"
}
```

**Output:**

```python
[
    SelectedFilterDate(
        label="Registration Date (From 2024-01-01 00:00:00 To 2024-12-31 00:00:00)",
        name="registered_at",
        type=SearchType.date,
        value=SelectedFilterDateItem(
            min=datetime(2024, 1, 1),
            max=datetime(2024, 12, 31)
        )
    )
]
```

**Variations:**

```python
# Only start date
{"registered_at": {"min": datetime(2024, 1, 1), "max": None}}
# Output label: "Registration Date (From 2024-01-01 00:00:00)"

# Only end date
{"registered_at": {"min": None, "max": datetime(2024, 12, 31)}}
# Output label: "Registration Date (To 2024-12-31 00:00:00)"
```

### Search Filters

For `search` type:

**Input:**

```python
current_query = {"search": "john doe"}
filter_item = {
    "name": "search",
    "label": "Search",
    "type": "search"
}
```

**Output:**

```python
[
    SelectedFilterSearch(
        label="Search (john doe)",
        name="search",
        type=SearchType.search,
        value="john doe"
    )
]
```

## Label Formatting

The function automatically formats labels based on the filter type and values:

### Select Labels

- Uses custom labels from filter definition if provided
- Uses enum labels if enum is defined
- Falls back to raw value if no label mapping exists

### Number Labels

- Both min/max: `"{label} (between {min} and {max})"`
- Only min: `"{label} (From {min})"`
- Only max: `"{label} (To {max})"`
- Neither: `"{label}"`

### Date Labels

- Both dates: `"{label} (From {min} To {max})"`
- Only min: `"{label} (From {min})"`
- Only max: `"{label} (To {max})"`
- Neither: `"{label}"`

### Search Labels

- Format: `"Search ({query})"`

## Usage in get_list

This function is automatically called by `get_list()` when `return_selected_filters=True`:

```python
result = get_list(
    current_query={
        "search": "john",
        "status": ["active"],
        "age": {"min": 18, "max": 65}
    },
    db=session,
    model=User,
    filters=[...],
    return_selected_filters=True  # Triggers make_selected_filters()
)

# Access selected filters
for filter in result.selected_filters:
    print(f"Active filter: {filter.label}")
    # Output:
    # Active filter: Search (john)
    # Active filter: Active
    # Active filter: Age (between 18 and 65)
```

## UI Integration Examples

### Display Active Filter Tags

```python
def render_active_filters(selected_filters):
    """Render active filters as removable tags."""
    for filter in selected_filters:
        print(f"""
        <div class="filter-tag">
            <span>{filter.label}</span>
            <button onclick="removeFilter('{filter.name}')">×</button>
        </div>
        """)
```

### Generate Clear Filters Links

```python
def generate_clear_links(selected_filters):
    """Generate links to remove each filter."""
    for filter in selected_filters:
        clear_url = build_url_without_param(filter.name)
        print(f'<a href="{clear_url}">Clear {filter.label}</a>')
```

### Filter Summary

```python
def filter_summary(selected_filters):
    """Create a human-readable filter summary."""
    if not selected_filters:
        return "Showing all results"
    
    descriptions = [f.label for f in selected_filters]
    return f"Filtered by: {', '.join(descriptions)}"
```

## Complete Example

```python
from dtpyfw.db.search_utils.selected_filters import make_selected_filters

# Define filters
filters = [
    {
        "name": "status",
        "label": "Status",
        "type": "select",
        "enum": UserStatus,
        "labels": {
            UserStatus.ACTIVE: "Active Users",
            UserStatus.INACTIVE: "Inactive Users"
        }
    },
    {
        "name": "age",
        "label": "Age",
        "type": "number"
    },
    {
        "name": "registered_at",
        "label": "Registration Date",
        "type": "date"
    }
]

# Current query
current_query = {
    "search": "john",
    "status": ["active"],
    "age": {"min": 25, "max": 40},
    "registered_at": {"min": datetime(2024, 1, 1), "max": None}
}

# Generate selected filters
selected = make_selected_filters(filters, current_query)

# Display
for filter in selected:
    print(f"Type: {filter.type}")
    print(f"Label: {filter.label}")
    print(f"Value: {filter.value}")
    print("---")

# Output:
# Type: SearchType.select
# Label: Active Users
# Value: ACTIVE
# ---
# Type: SearchType.number
# Label: Age (between 25 and 40)
# Value: SelectedFilterNumberItem(min=25, max=40)
# ---
# Type: SearchType.date
# Label: Registration Date (From 2024-01-01 00:00:00)
# Value: SelectedFilterDateItem(min=datetime(...), max=None)
```

## Related Documentation

- [../search.md](../search.md) - Main search functionality
- [../schema.md](../schema.md) - Selected filter schemas

## Notes

- This is an internal utility used by `get_list()`
- Skips filters with empty or null values
- Creates one SelectedFilter per selected value for select/select_array
- Creates one SelectedFilter per range filter (number/date)
- Automatically handles enum value extraction and labeling
- Formats labels to be user-friendly for display in UIs
