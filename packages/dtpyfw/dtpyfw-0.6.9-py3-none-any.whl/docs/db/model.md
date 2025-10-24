# Model Base Classes and Mixins (`dtpyfw.db.model`)

## Overview

The `model` module provides enhanced base classes and mixins for SQLAlchemy ORM models with common fields, serialization methods, CRUD operations, and utilities. It includes `ModelBase` for standard models, mixins for timestamps and soft deletes, and `ConfigurableMixin` for models with dynamic settings stored in JSONB fields.

## Module Location

```python
from dtpyfw.db.model import (
    ModelBase,
    TimestampMixin,
    SoftDeleteMixin,
    ConfigurableMixin,
    get_modified_keys,
    get_difference_between_dictionaries
)
```

## Classes

### `TimestampMixin`

Mixin that adds automatic timestamp fields to models for tracking creation and modification times.

**Fields:**

- `created_at`: Timestamp when the record was created (auto-set on insert)
- `updated_at`: Timestamp when the record was last updated (auto-updated on modification)

**Usage:**

```python
from dtpyfw.db.model import ModelBase, TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class User(TimestampMixin, db.base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

# User instances automatically have created_at and updated_at fields
user = User(name="John")
# user.created_at = <current timestamp>
# user.updated_at = <current timestamp>
```

**Example:**

```python
with db.get_db_cm_write() as session:
    user = User(name="Alice")
    session.add(user)
    session.commit()
    
    print(user.created_at)  # 2025-10-24 10:30:00
    print(user.updated_at)  # 2025-10-24 10:30:00
    
    # Update the user
    user.name = "Alice Smith"
    session.commit()
    
    print(user.created_at)  # 2025-10-24 10:30:00 (unchanged)
    print(user.updated_at)  # 2025-10-24 10:35:00 (updated)
```

### `SoftDeleteMixin`

Mixin that adds soft delete functionality, marking records as deleted without physically removing them from the database.

**Fields:**

- `is_deleted`: Boolean flag indicating if the record is deleted (default: `False`)
- `deleted_at`: Timestamp when the record was soft-deleted (nullable)

**Methods:**

#### `soft_delete(db: Session) -> None`

Mark the record as deleted without physically removing it.

**Parameters:**
- `db` (Session): SQLAlchemy session for database operations

**Behavior:**
- Sets `is_deleted = True`
- Sets `deleted_at = current timestamp`
- Commits the changes
- Refreshes the instance
- Automatically rolls back on error

**Example:**

```python
from dtpyfw.db.model import ModelBase, SoftDeleteMixin

class Post(ModelBase, SoftDeleteMixin, db.base):
    __tablename__ = 'posts'
    
    title: Mapped[str] = mapped_column(String(200))

with db.get_db_cm_write() as session:
    post = Post.create(session, {"title": "My Post"})
    
    # Soft delete
    post.soft_delete(session)
    
    print(post.is_deleted)  # True
    print(post.deleted_at)  # 2025-10-24 10:30:00
```

#### `restore(db: Session) -> None`

Restore a soft-deleted record.

**Parameters:**
- `db` (Session): SQLAlchemy session for database operations

**Behavior:**
- Sets `is_deleted = False`
- Sets `deleted_at = None`
- Commits the changes
- Refreshes the instance
- Automatically rolls back on error

**Example:**

```python
with db.get_db_cm_write() as session:
    post = Post.get_by_id(session, post_id)
    
    # Restore deleted post
    if post.is_deleted:
        post.restore(session)
        print("Post restored")
```

**Usage Pattern:**

```python
class Article(ModelBase, SoftDeleteMixin, db.base):
    __tablename__ = 'articles'
    title: Mapped[str] = mapped_column(String(200))

# Querying non-deleted records
with db.get_db_cm_read() as session:
    active_articles = session.query(Article).filter(
        Article.is_deleted == False
    ).all()

# Including deleted records
with db.get_db_cm_read() as session:
    all_articles = session.query(Article).all()
```

### `ConfigurableMixin`

Mixin for models that need dynamic configuration through a JSONB settings field. Provides functionality for storing and managing arbitrary key-value settings.

**Class Attributes:**

- `settings`: JSONB (PostgreSQL) or JSON column for storing settings data (automatically provided)
- `combined_settings` (ClassVar[bool]): If `True`, merges settings into the main dict during serialization (default: `True`)
- `need_jsonable_encoder` (ClassVar[bool]): If `True`, uses jsonable_encoder for data processing (default: `True`)
- `valid_settings` (ClassVar[List[str]]): List of valid setting keys allowed for this model (default: `[]`)

**Methods:**

#### `to_dict(excludes=None, includes=None) -> Dict[str, Any]`

Serialize the model instance to a dictionary with settings support.

**Parameters:**
- `excludes` (Optional[set[str]]): Set of field names to exclude
- `includes` (Optional[set[str]]): Set of field names to include (if specified, only these fields will be included)

**Returns:**
- `Dict[str, Any]`: Dictionary representation of the model

**Behavior:**
- If `combined_settings=True`, settings fields are merged into the root dictionary
- If `combined_settings=False`, settings are returned as a list of `{"key": ..., "value": ...}` objects
- Respects includes/excludes filters

**Example:**

```python
from dtpyfw.db.model import ModelBase, ConfigurableMixin

class User(ConfigurableMixin, ModelBase, db.base):
    __tablename__ = 'users'
    
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
    
    # Configure settings behavior
    combined_settings = True
    valid_settings = ['theme', 'notifications', 'language']

with db.get_db_cm_write() as session:
    user = User.create(session, {
        "name": "John",
        "email": "john@example.com",
        "theme": "dark",
        "notifications": True
    })
    
    user_dict = user.to_dict()
    print(user_dict)
    # {
    #     'id': '...',
    #     'name': 'John',
    #     'email': 'john@example.com',
    #     'theme': 'dark',          # Merged from settings
    #     'notifications': True,    # Merged from settings
    #     'created_at': ...,
    #     'updated_at': ...
    # }
```

#### `create(db: Session, data: Dict[str, Any]) -> ConfigurableMixin`

Create a new model instance with settings support.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `data` (Dict[str, Any] | Any): Dictionary or model containing the data

**Returns:**
- New model instance

**Behavior:**
- Separates regular fields from settings fields
- Only stores keys in `valid_settings` list
- Handles both combined and separate settings modes
- Automatically commits and refreshes

**Example:**

```python
class User(ConfigurableMixin, ModelBase, db.base):
    __tablename__ = 'users'
    name: Mapped[str] = mapped_column(String(100))
    valid_settings = ['theme', 'language']

with db.get_db_cm_write() as session:
    user = User.create(session, {
        "name": "Alice",
        "theme": "light",      # Stored in settings
        "language": "en",      # Stored in settings
        "invalid_key": "xyz"   # Ignored (not in valid_settings)
    })
```

#### `update(db: Session, data: Dict[str, Any]) -> ConfigurableMixin`

Update the model instance with settings support.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `data` (Dict[str, Any] | Any): Dictionary containing updated data

**Returns:**
- Updated model instance

**Behavior:**
- Updates regular fields
- Merges new settings with existing settings
- Tracks changes including settings modifications
- Automatically commits and refreshes

**Example:**

```python
with db.get_db_cm_write() as session:
    user = User.get_by_id(session, user_id)
    user.update(session, {
        "name": "Alice Smith",
        "theme": "dark"  # Updates settings
    })
```

**Settings Storage:**

```python
# With combined_settings = True (default)
user.settings = {"theme": "dark", "notifications": True}

# With combined_settings = False
user.settings = {"theme": "dark", "notifications": True}
# Serialized as:
# [
#     {"key": "theme", "value": "dark"},
#     {"key": "notifications", "value": True}
# ]
```

### `ModelBase`

Enhanced base class for SQLAlchemy models with common fields and utilities. Includes timestamp functionality via `TimestampMixin` and provides standard CRUD operations, serialization methods, and query utilities.

**Standard Fields:**

- `id`: UUID primary key column (auto-generated)
- `created_at`: Timestamp when record was created (from TimestampMixin)
- `updated_at`: Timestamp when record was last updated (from TimestampMixin)

**Class Attributes:**

- `need_jsonable_encoder` (ClassVar[bool]): If `True`, uses jsonable_encoder for data processing (default: `True`)

**Usage:**

```python
from dtpyfw.db.model import ModelBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class User(ModelBase, db.base):
    __tablename__ = 'users'
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
```

**Class Methods:**

#### `get_fields() -> List[str]`

Return a list of column names excluding 'settings'.

**Returns:**
- `List[str]`: List of column names defined on the model's table

**Example:**

```python
fields = User.get_fields()
print(fields)
# ['id', 'name', 'email', 'created_at', 'updated_at']
```

#### `get_by_id(db: Session, id: Union[str, UUID]) -> Optional[T]`

Get a model instance by its ID.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `id` (Union[str, UUID]): The UUID or string ID to search for

**Returns:**
- Model instance if found, `None` otherwise

**Example:**

```python
with db.get_db_cm_read() as session:
    user = User.get_by_id(session, "550e8400-e29b-41d4-a716-446655440000")
    if user:
        print(user.name)
```

#### `get_all(db: Session, limit=None, offset=0) -> List[T]`

Get all instances of the model with optional pagination.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `limit` (Optional[int]): Maximum number of records to return
- `offset` (int): Number of records to skip (default: 0)

**Returns:**
- `List[T]`: List of model instances

**Behavior:**
- Automatically excludes soft-deleted records if model has `is_deleted` field
- Supports pagination via limit and offset

**Example:**

```python
with db.get_db_cm_read() as session:
    # Get first 10 users
    users = User.get_all(session, limit=10)
    
    # Get next 10 users
    users_page2 = User.get_all(session, limit=10, offset=10)
    
    # Get all users
    all_users = User.get_all(session)
```

#### `count(db: Session, include_deleted=False) -> int`

Count total number of records.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `include_deleted` (bool): Whether to include soft-deleted records (default: `False`)

**Returns:**
- `int`: Total number of records

**Example:**

```python
with db.get_db_cm_read() as session:
    total_users = User.count(session)
    print(f"Total users: {total_users}")
    
    # Include deleted records
    total_including_deleted = User.count(session, include_deleted=True)
```

#### `exists(db: Session, id: Union[str, UUID]) -> bool`

Check if a record exists by ID.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `id` (Union[str, UUID]): The UUID or string ID to check

**Returns:**
- `bool`: `True` if the record exists, `False` otherwise

**Example:**

```python
with db.get_db_cm_read() as session:
    if User.exists(session, user_id):
        print("User exists")
    else:
        print("User not found")
```

#### `bulk_create(db: Session, data_list: List[Dict]) -> List[T]`

Create multiple model instances in a single transaction.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `data_list` (List[Dict[str, Any]]): List of dictionaries containing data for new instances

**Returns:**
- `List[T]`: List of newly created model instances

**Raises:**
- `IntegrityError`: If constraint violations occur
- `SQLAlchemyError`: If database operation fails

**Example:**

```python
users_data = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"}
]

with db.get_db_cm_write() as session:
    users = User.bulk_create(session, users_data)
    print(f"Created {len(users)} users")
```

#### `get_or_create(db: Session, defaults=None, **kwargs) -> Tuple[T, bool]`

Get an existing instance or create a new one if it doesn't exist.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `defaults` (Optional[Dict[str, Any]]): Default values to use when creating
- `**kwargs`: Filter criteria to find existing instance

**Returns:**
- `Tuple[T, bool]`: Tuple of (instance, created) where created is `True` if new instance was created

**Example:**

```python
with db.get_db_cm_write() as session:
    # Try to get user by email, create if not exists
    user, created = User.get_or_create(
        session,
        email="john@example.com",
        defaults={"name": "John Doe"}
    )
    
    if created:
        print("New user created")
    else:
        print("Existing user found")
```

#### `create(db: Session, data: Dict[str, Any]) -> T`

Create a new model instance and persist it to the database.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `data` (Dict[str, Any] | Any): Dictionary or model containing the data

**Returns:**
- `T`: The newly created and persisted model instance

**Raises:**
- `IntegrityError`: If constraint violations occur
- `SQLAlchemyError`: If database operation fails

**Example:**

```python
with db.get_db_cm_write() as session:
    user = User.create(session, {
        "name": "John Doe",
        "email": "john@example.com"
    })
    print(f"Created user: {user.id}")
```

**Instance Methods:**

#### `update(db: Session, data: Dict[str, Any]) -> T`

Update the model instance with new data and persist changes.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `data` (Dict[str, Any] | Any): Dictionary containing updated data

**Returns:**
- `T`: The updated model instance after refresh from database

**Raises:**
- `IntegrityError`: If constraint violations occur
- `SQLAlchemyError`: If database operation fails

**Example:**

```python
with db.get_db_cm_write() as session:
    user = User.get_by_id(session, user_id)
    user.update(session, {
        "name": "Jane Doe",
        "email": "jane@example.com"
    })
```

#### `delete(db: Session, soft=True) -> None`

Delete the model instance.

**Parameters:**
- `db` (Session): SQLAlchemy session
- `soft` (bool): If `True` and model supports soft delete, perform soft delete; otherwise, hard delete (default: `True`)

**Behavior:**
- If `soft=True` and model has `soft_delete` method: calls `soft_delete()`
- Otherwise: performs hard delete (removes from database)

**Example:**

```python
with db.get_db_cm_write() as session:
    user = User.get_by_id(session, user_id)
    
    # Soft delete (if SoftDeleteMixin is used)
    user.delete(session, soft=True)
    
    # Hard delete
    user.delete(session, soft=False)
```

#### `to_dict(excludes=None, includes=None) -> Dict[str, Any]`

Serialize the model instance to a dictionary with optional field filtering.

**Parameters:**
- `excludes` (Optional[set[str]]): Set of field names to exclude
- `includes` (Optional[set[str]]): Set of field names to include (if specified, only these fields will be included)

**Returns:**
- `Dict[str, Any]`: Dictionary representation of the model, or `None` if instance is `None`

**Example:**

```python
user = User.get_by_id(session, user_id)

# Full serialization
user_dict = user.to_dict()

# Exclude sensitive fields
user_dict = user.to_dict(excludes={'password', 'api_key'})

# Include only specific fields
user_dict = user.to_dict(includes={'id', 'name', 'email'})
```

#### `get(excludes=None, includes=None) -> Dict[str, Any]` (Deprecated)

Alias for `to_dict()` method for backward compatibility.

**⚠️ Deprecated:** Use `to_dict()` instead. This method will be removed in a future version.

**Example:**

```python
# Deprecated - avoid using
user_dict = user.get()

# Use this instead
user_dict = user.to_dict()
```

#### `__repr__() -> str`

Return a string representation of the model instance.

**Returns:**
- `str`: String representation showing class name and ID

**Example:**

```python
user = User.get_by_id(session, user_id)
print(repr(user))
# Output: <User(id=550e8400-e29b-41d4-a716-446655440000)>
```

#### `__str__() -> str`

Return a human-readable string representation.

**Returns:**
- `str`: String showing class name and ID

**Example:**

```python
user = User.get_by_id(session, user_id)
print(str(user))
# Output: User 550e8400-e29b-41d4-a716-446655440000
```

## Helper Functions

### `get_modified_keys(instance: Any) -> List[str]`

Return the list of attribute keys that have been modified on the instance.

Uses SQLAlchemy's inspection API to detect which attributes have changed since the instance was loaded or last committed.

**Parameters:**
- `instance` (Any): A SQLAlchemy model instance to inspect

**Returns:**
- `List[str]`: List of attribute key names that have been modified

**Example:**

```python
from dtpyfw.db.model import get_modified_keys

with db.get_db_cm_write() as session:
    user = User.get_by_id(session, user_id)
    
    user.name = "New Name"
    user.email = "newemail@example.com"
    
    modified = get_modified_keys(user)
    print(modified)
    # Output: ['name', 'email']
```

### `get_difference_between_dictionaries(old_value, new_value, path="") -> List[str]`

Recursively find paths that differ between two dictionary/list structures.

Compares two data structures and returns a list of paths where differences exist. Useful for tracking changes in nested data.

**Parameters:**
- `old_value` (Any): The original data structure
- `new_value` (Any): The new data structure to compare against
- `path` (str): The current path in the structure (used for recursion, default: `""`)

**Returns:**
- `List[str]`: List of string paths indicating where changes occurred

**Example:**

```python
from dtpyfw.db.model import get_difference_between_dictionaries

old_settings = {
    "theme": "light",
    "notifications": {
        "email": True,
        "sms": False
    },
    "tags": ["python", "django"]
}

new_settings = {
    "theme": "dark",
    "notifications": {
        "email": True,
        "sms": True
    },
    "tags": ["python", "fastapi"]
}

changes = get_difference_between_dictionaries(old_settings, new_settings)
print(changes)
# Output: ['theme', 'notifications.sms', 'tags']
```

## Complete Usage Examples

### Basic Model Definition

```python
from dtpyfw.db.model import ModelBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer

class User(ModelBase, db.base):
    __tablename__ = 'users'
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)

# Create tables
db.create_tables()
```

### Model with All Mixins

```python
from dtpyfw.db.model import ModelBase, SoftDeleteMixin, ConfigurableMixin

class Product(ConfigurableMixin, SoftDeleteMixin, ModelBase, db.base):
    __tablename__ = 'products'
    
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column()
    
    # Configure settings
    combined_settings = True
    valid_settings = ['featured', 'discount_eligible', 'max_quantity']

with db.get_db_cm_write() as session:
    product = Product.create(session, {
        "name": "Laptop",
        "price": 999.99,
        "featured": True,
        "discount_eligible": False
    })
```

### CRUD Operations

```python
# Create
with db.get_db_cm_write() as session:
    user = User.create(session, {
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30
    })

# Read
with db.get_db_cm_read() as session:
    user = User.get_by_id(session, user_id)
    print(user.name)

# Update
with db.get_db_cm_write() as session:
    user = User.get_by_id(session, user_id)
    user.update(session, {"age": 31})

# Delete (soft)
with db.get_db_cm_write() as session:
    user = User.get_by_id(session, user_id)
    user.delete(session, soft=True)
```

### Bulk Operations

```python
# Bulk create
users_data = [
    {"name": f"User {i}", "email": f"user{i}@example.com"}
    for i in range(100)
]

with db.get_db_cm_write() as session:
    users = User.bulk_create(session, users_data)
    print(f"Created {len(users)} users")
```

### Get or Create Pattern

```python
with db.get_db_cm_write() as session:
    user, created = User.get_or_create(
        session,
        email="john@example.com",
        defaults={
            "name": "John Doe",
            "age": 25
        }
    )
    
    if created:
        print("Created new user")
    else:
        print(f"Found existing user: {user.name}")
```

### Soft Delete Operations

```python
class Article(ModelBase, SoftDeleteMixin, db.base):
    __tablename__ = 'articles'
    title: Mapped[str] = mapped_column(String(200))

with db.get_db_cm_write() as session:
    article = Article.create(session, {"title": "My Article"})
    
    # Soft delete
    article.soft_delete(session)
    
    # Query excluding deleted
    active_articles = session.query(Article).filter(
        Article.is_deleted == False
    ).all()
    
    # Restore
    article.restore(session)
```

### ConfigurableMixin with Settings

```python
class UserProfile(ConfigurableMixin, ModelBase, db.base):
    __tablename__ = 'user_profiles'
    
    username: Mapped[str] = mapped_column(String(50), unique=True)
    
    combined_settings = True
    valid_settings = ['theme', 'language', 'notifications', 'timezone']

with db.get_db_cm_write() as session:
    profile = UserProfile.create(session, {
        "username": "johndoe",
        "theme": "dark",
        "language": "en",
        "notifications": True,
        "timezone": "UTC"
    })
    
    # Access settings
    profile_dict = profile.to_dict()
    print(profile_dict['theme'])  # 'dark'
    
    # Update settings
    profile.update(session, {
        "theme": "light",
        "language": "fr"
    })
```

### Serialization with Filtering

```python
with db.get_db_cm_read() as session:
    user = User.get_by_id(session, user_id)
    
    # Full serialization
    full_dict = user.to_dict()
    
    # Exclude sensitive data
    public_dict = user.to_dict(excludes={'password', 'api_key', 'secret'})
    
    # Include only specific fields
    minimal_dict = user.to_dict(includes={'id', 'name', 'email'})
```

### Change Tracking

```python
from dtpyfw.db.model import get_modified_keys, get_difference_between_dictionaries

with db.get_db_cm_write() as session:
    user = User.get_by_id(session, user_id)
    
    # Track field changes
    user.name = "New Name"
    user.age = 35
    
    modified_fields = get_modified_keys(user)
    print(f"Modified fields: {modified_fields}")
    
    # Track nested changes (for ConfigurableMixin)
    old_settings = user.settings.copy() if user.settings else {}
    user.update(session, {"theme": "dark", "language": "es"})
    
    changes = get_difference_between_dictionaries(old_settings, user.settings)
    print(f"Settings changes: {changes}")
```

## FastAPI Integration

### Dependency Injection

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

app = FastAPI()

def get_db():
    yield from db.get_db_write()

class UserCreate(BaseModel):
    name: str
    email: str
    age: int

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    age: int | None = None

@app.post("/users")
def create_user(user_data: UserCreate, session: Session = Depends(get_db)):
    user = User.create(session, user_data.model_dump())
    return user.to_dict()

@app.get("/users/{user_id}")
def get_user(user_id: str, session: Session = Depends(get_db)):
    user = User.get_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict(excludes={'password'})

@app.put("/users/{user_id}")
def update_user(
    user_id: str,
    user_data: UserUpdate,
    session: Session = Depends(get_db)
):
    user = User.get_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_data.model_dump(exclude_unset=True)
    user.update(session, update_data)
    return user.to_dict()

@app.delete("/users/{user_id}")
def delete_user(user_id: str, session: Session = Depends(get_db)):
    user = User.get_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.delete(session, soft=True)
    return {"message": "User deleted"}

@app.get("/users")
def list_users(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db)
):
    users = User.get_all(session, limit=limit, offset=offset)
    total = User.count(session)
    
    return {
        "users": [u.to_dict() for u in users],
        "total": total,
        "limit": limit,
        "offset": offset
    }
```

## Best Practices

1. **Always inherit from db.base last** to ensure proper MRO (Method Resolution Order):
   ```python
   class MyModel(ConfigurableMixin, SoftDeleteMixin, ModelBase, db.base):
       pass
   ```

2. **Use type hints** for all model fields:
   ```python
   name: Mapped[str] = mapped_column(String(100))
   ```

3. **Define valid_settings** when using ConfigurableMixin:
   ```python
   valid_settings = ['theme', 'language', 'notifications']
   ```

4. **Use soft deletes** for data retention and audit trails

5. **Filter excludes in to_dict()** to avoid exposing sensitive data:
   ```python
   user.to_dict(excludes={'password', 'api_key'})
   ```

6. **Use get_or_create** to avoid duplicate checks:
   ```python
   user, created = User.get_or_create(session, email=email, defaults={...})
   ```

7. **Leverage bulk_create** for importing large datasets

8. **Query with soft delete awareness**:
   ```python
   # Exclude deleted
   users = session.query(User).filter(User.is_deleted == False).all()
   
   # Or use get_all which does this automatically
   users = User.get_all(session)
   ```

## Related Documentation

- [database.md](./database.md) - Database instance and session management
- [utils.md](./utils.md) - Bulk operations and upsert
- [to_dict.md](./to_dict.md) - Dictionary conversion utilities
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

## Notes

- All create/update/delete operations automatically commit
- Rollback happens automatically on exceptions
- UUID primary keys are automatically generated
- Timestamps are automatically managed
- ConfigurableMixin requires PostgreSQL for JSONB support (falls back to JSON for other databases)
- The `get()` method is deprecated in favor of `to_dict()`
