# Dictionary Conversion Utility (`dtpyfw.db.to_dict`)

## Overview

The `to_dict` module provides a simple utility function for converting SQLAlchemy model instances to dictionary representations. It extracts all mapped column attributes from a model and returns them as a Python dictionary.

## Module Location

```python
from dtpyfw.db.to_dict import to_dict
```

## Functions

### `to_dict(obj: Any) -> dict[str, Any]`

Convert a SQLAlchemy model instance to a dictionary of column values.

This function uses SQLAlchemy's inspection API to extract all mapped column attributes from a model instance and return them as a dictionary. It only includes actual database columns, not relationships or other non-column attributes.

**Parameters:**

- `obj` (Any): A SQLAlchemy model instance to convert

**Returns:**

- `dict[str, Any]`: Dictionary mapping column names to their values from the instance

**Example:**

```python
from dtpyfw.db.to_dict import to_dict
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class User(ModelBase, db.base):
    __tablename__ = 'users'
    
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
    age: Mapped[int] = mapped_column()

# Create a user instance
user = User(name="John Doe", email="john@example.com", age=30)

# Convert to dictionary
user_dict = to_dict(user)
print(user_dict)
# Output: {
#     'id': UUID('...'),
#     'name': 'John Doe',
#     'email': 'john@example.com',
#     'age': 30,
#     'created_at': datetime(...),
#     'updated_at': datetime(...)
# }
```

## Behavior

The `to_dict` function:

1. **Inspects the model**: Uses `sqlalchemy.inspect()` to access the model's mapper
2. **Extracts columns**: Iterates through all column attributes
3. **Gets values**: Retrieves the current value of each column from the instance
4. **Returns dictionary**: Creates a dictionary mapping column names to values

### What's Included

- All database columns defined on the model
- Primary keys (e.g., `id`)
- Regular columns (e.g., `name`, `email`)
- Timestamp columns (e.g., `created_at`, `updated_at`)
- Foreign key columns

### What's Excluded

- Relationships (e.g., `user.posts`)
- Hybrid properties
- Python-only attributes not mapped to columns
- Private attributes (starting with `_`)

## Usage Examples

### Basic Usage

```python
from dtpyfw.db.to_dict import to_dict

with db.get_db_cm_read() as session:
    user = session.query(User).first()
    user_dict = to_dict(user)
    print(user_dict)
```

### Converting Query Results

```python
from dtpyfw.db.to_dict import to_dict

with db.get_db_cm_read() as session:
    users = session.query(User).limit(10).all()
    users_list = [to_dict(user) for user in users]
    
# users_list is now a list of dictionaries
for user_dict in users_list:
    print(f"{user_dict['name']}: {user_dict['email']}")
```

### API Response

```python
from fastapi import FastAPI
from dtpyfw.db.to_dict import to_dict

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: str):
    with db.get_db_cm_read() as session:
        user = User.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return to_dict(user)
```

### JSON Serialization

```python
import json
from datetime import datetime
from dtpyfw.db.to_dict import to_dict

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

with db.get_db_cm_read() as session:
    user = User.get_by_id(session, user_id)
    user_dict = to_dict(user)
    json_str = json.dumps(user_dict, cls=DateTimeEncoder)
```

### Data Export

```python
import csv
from dtpyfw.db.to_dict import to_dict

def export_users_to_csv(filename: str):
    """Export all users to a CSV file."""
    with db.get_db_cm_read() as session:
        users = session.query(User).all()
        users_dicts = [to_dict(user) for user in users]
        
        if not users_dicts:
            return
        
        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = users_dicts[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(users_dicts)

export_users_to_csv('users.csv')
```

## Comparison with ModelBase.to_dict()

The `dtpyfw.db.model.ModelBase` class provides its own `to_dict()` method with more features. Here's when to use each:

### Use `to_dict` function when:

- You need a simple column-only conversion
- Working with models that don't inherit from `ModelBase`
- You want to avoid any custom serialization logic
- You need consistent behavior across different model types

```python
from dtpyfw.db.to_dict import to_dict

user_dict = to_dict(user)  # Simple column extraction
```

### Use `ModelBase.to_dict()` method when:

- You need field filtering (includes/excludes)
- Working with models that inherit from `ModelBase`
- You need settings field handling (ConfigurableMixin)
- You want custom serialization behavior

```python
# Method on ModelBase instances
user_dict = user.to_dict(excludes={'password'})
```

## Example: Both Approaches

```python
from dtpyfw.db.to_dict import to_dict
from dtpyfw.db.model import ModelBase

class User(ModelBase, db.base):
    __tablename__ = 'users'
    name: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(200))

user = User(name="John", password="hashed_password")

# Using standalone function
dict1 = to_dict(user)
# {'id': ..., 'name': 'John', 'password': 'hashed_password', ...}

# Using ModelBase method with exclusion
dict2 = user.to_dict(excludes={'password'})
# {'id': ..., 'name': 'John', ...}  # password excluded
```

## Handling Special Types

### UUID Fields

```python
from dtpyfw.db.to_dict import to_dict
import uuid

user_dict = to_dict(user)
# UUID is included as UUID object
print(user_dict['id'])  # UUID('...')

# Convert UUID to string if needed
user_dict['id'] = str(user_dict['id'])
```

### DateTime Fields

```python
from dtpyfw.db.to_dict import to_dict
from datetime import datetime

user_dict = to_dict(user)
# datetime objects are included as-is
print(user_dict['created_at'])  # datetime(...)

# Convert to ISO format if needed
user_dict['created_at'] = user_dict['created_at'].isoformat()
```

### Enum Fields

```python
from enum import Enum
from dtpyfw.db.to_dict import to_dict

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class User(ModelBase, db.base):
    __tablename__ = 'users'
    status: Mapped[UserStatus] = mapped_column()

user = User(status=UserStatus.ACTIVE)
user_dict = to_dict(user)
# Enum value is preserved
print(user_dict['status'])  # UserStatus.ACTIVE

# Convert to string if needed
if isinstance(user_dict['status'], Enum):
    user_dict['status'] = user_dict['status'].value
```

## Use Cases

### 1. Quick Debugging

```python
from dtpyfw.db.to_dict import to_dict

# Quick inspection of model data
user = User.get_by_id(session, user_id)
print("User data:", to_dict(user))
```

### 2. Testing

```python
from dtpyfw.db.to_dict import to_dict

def test_user_creation():
    user = User.create(session, {"name": "Test User", "email": "test@example.com"})
    user_dict = to_dict(user)
    
    assert user_dict['name'] == "Test User"
    assert user_dict['email'] == "test@example.com"
    assert 'id' in user_dict
```

### 3. Data Migration

```python
from dtpyfw.db.to_dict import to_dict

def migrate_users_to_new_system():
    """Migrate users from old database to new system."""
    with old_db.get_db_cm_read() as session:
        users = session.query(User).all()
        users_data = [to_dict(user) for user in users]
    
    # Send to new system
    for user_data in users_data:
        new_system_api.create_user(user_data)
```

### 4. Caching

```python
import json
from dtpyfw.db.to_dict import to_dict

def cache_user(user_id: str):
    """Cache user data in Redis."""
    with db.get_db_cm_read() as session:
        user = User.get_by_id(session, user_id)
        if user:
            user_dict = to_dict(user)
            # Convert special types
            user_dict['id'] = str(user_dict['id'])
            user_dict['created_at'] = user_dict['created_at'].isoformat()
            
            redis_client.setex(
                f"user:{user_id}",
                3600,  # 1 hour TTL
                json.dumps(user_dict)
            )
```

## Performance Considerations

- **Lightweight**: Only extracts column data, no relationship loading
- **No N+1**: Doesn't trigger lazy-loaded relationships
- **Fast**: Uses SQLAlchemy's internal inspection, no additional queries
- **Memory Efficient**: Creates a simple dictionary without heavy objects

## Limitations

1. **No Relationships**: Does not include related objects
   ```python
   # user.posts relationship is NOT included
   user_dict = to_dict(user)  # Only columns, no 'posts' key
   ```

2. **No Hybrid Properties**: Custom properties are excluded
   ```python
   class User(ModelBase, db.base):
       @hybrid_property
       def full_name(self):
           return f"{self.first_name} {self.last_name}"
   
   user_dict = to_dict(user)  # 'full_name' is NOT included
   ```

3. **No Type Conversion**: Returns values as-is from SQLAlchemy
   ```python
   user_dict = to_dict(user)
   # UUIDs remain as UUID objects
   # Datetimes remain as datetime objects
   # Enums remain as Enum members
   ```

## Workarounds for Limitations

### Including Relationships

```python
from dtpyfw.db.to_dict import to_dict

user = User.get_by_id(session, user_id)
user_dict = to_dict(user)

# Manually add relationships if needed
user_dict['posts'] = [to_dict(post) for post in user.posts]
```

### Including Hybrid Properties

```python
from dtpyfw.db.to_dict import to_dict

user = User.get_by_id(session, user_id)
user_dict = to_dict(user)

# Manually add hybrid properties
user_dict['full_name'] = user.full_name
```

### Type Conversion

```python
from dtpyfw.db.to_dict import to_dict
from dtpyfw.core.jsonable_encoder import jsonable_encoder

user = User.get_by_id(session, user_id)
user_dict = to_dict(user)

# Use jsonable_encoder for type conversion
user_dict = jsonable_encoder(user_dict)
```

## Best Practices

1. **Use for column-only data** when you don't need relationships or custom serialization

2. **Prefer ModelBase.to_dict()** when working with models that inherit from ModelBase and need filtering

3. **Handle special types** explicitly when needed for JSON serialization

4. **Document behavior** when using in APIs to clarify what's included/excluded

5. **Consider caching** the results if conversion is done frequently

## Related Documentation

- [model.md](./model.md) - ModelBase.to_dict() method with more features
- [SQLAlchemy Inspection](https://docs.sqlalchemy.org/en/20/core/inspection.html)

## Notes

- The function is straightforward and has minimal overhead
- It's suitable for simple use cases where you need just the column data
- For more complex serialization needs, use `ModelBase.to_dict()` or `jsonable_encoder`
- The function does not modify the model instance
