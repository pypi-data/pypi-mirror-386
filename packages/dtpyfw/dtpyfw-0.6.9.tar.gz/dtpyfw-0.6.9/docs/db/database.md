# Database Instance (`dtpyfw.db.database`)

## Overview

The `database` module provides the `DatabaseInstance` class, which manages SQLAlchemy engines and sessions for both synchronous and asynchronous database operations. It handles connection orchestration, session management, health checks, and provides convenient context managers and dependency injection patterns for use with frameworks like FastAPI.

## Module Location

```python
from dtpyfw.db.database import DatabaseInstance
```

## Classes

### `DatabaseInstance`

The central class for managing database connections, engines, and sessions. It supports:
- Synchronous and asynchronous operations
- Read/write connection splitting
- Connection pooling
- SSL/TLS connections
- Isolated declarative bases per instance
- Health check utilities
- Context managers for session management

#### Constructor

```python
DatabaseInstance(config: DatabaseConfig, base_name: Optional[str] = None)
```

**Parameters:**
- `config` (DatabaseConfig): A configured `DatabaseConfig` instance containing all connection parameters
- `base_name` (Optional[str]): Custom name for the declarative base. If not provided, defaults to `"DatabaseBase_{db_name}"`

**Returns:**
- `DatabaseInstance`: A new database instance with configured engines and sessions

**Example:**

```python
from dtpyfw.db import DatabaseConfig, DatabaseInstance

config = (
    DatabaseConfig()
    .set_db_backend("postgresql")
    .set_db_user("myuser")
    .set_db_password("mypassword")
    .set_db_host("localhost")
    .set_db_port(5432)
    .set_db_name("mydatabase")
)

db = DatabaseInstance(config)
```

**Attributes:**

The `DatabaseInstance` creates and maintains the following attributes:

- `base`: A unique `DeclarativeBase` class for this database instance
- `engine_write`: Synchronous engine for write operations
- `engine_read`: Synchronous engine for read operations
- `async_engine_write`: Asynchronous engine for write operations
- `async_engine_read`: Asynchronous engine for read operations
- `write_session`: Session factory for synchronous write sessions
- `read_session`: Session factory for synchronous read sessions
- `async_write_session`: Session factory for asynchronous write sessions
- `async_read_session`: Session factory for asynchronous read sessions

## Instance Attributes

### Declarative Base

#### `base`

A unique `DeclarativeBase` class with isolated metadata for this database instance.

**Usage:**

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from dtpyfw.db.model import ModelBase

class User(ModelBase, db.base):
    __tablename__ = 'users'
    
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
```

## Synchronous Session Methods

### Session Factories

#### `session_local() -> Session`

Create a new synchronous write session.

**Returns:**
- `Session`: A new SQLAlchemy Session instance configured for write operations

**Example:**

```python
session = db.session_local()
try:
    # Perform database operations
    user = User(name="John", email="john@example.com")
    session.add(user)
    session.commit()
finally:
    session.close()
```

#### `session_local_read() -> Session`

Create a new synchronous read session.

**Returns:**
- `Session`: A new SQLAlchemy Session instance configured for read-only operations

**Example:**

```python
session = db.session_local_read()
try:
    users = session.query(User).all()
finally:
    session.close()
```

### Session Generators

#### `get_db(force: Optional[str] = None) -> Generator[Session, None, None]`

Yield a synchronous database session with automatic cleanup.

**Parameters:**
- `force` (Optional[str]): If `"read"`, yields a read-only session; otherwise, a write session

**Yields:**
- `Session`: A SQLAlchemy Session object

**Behavior:**
- Automatically rolls back on exception
- Always closes the session in the finally block
- Logs warnings if session closure fails

**Example:**

```python
# Write session (default)
for session in db.get_db():
    user = User.create(session, {"name": "Alice", "email": "alice@example.com"})
    break

# Read session
for session in db.get_db(force="read"):
    users = session.query(User).all()
    break
```

#### `get_db_read() -> Generator[Session, None, None]`

Yield a synchronous read-only database session.

**Yields:**
- `Session`: A SQLAlchemy Session configured for read-only operations

**Example:**

```python
for session in db.get_db_read():
    users = User.get_all(session)
    break
```

#### `get_db_write() -> Generator[Session, None, None]`

Yield a synchronous write-enabled database session.

**Yields:**
- `Session`: A SQLAlchemy Session configured for write operations

**Example:**

```python
for session in db.get_db_write():
    user = User.create(session, {"name": "Bob"})
    break
```

### Context Managers

#### `get_db_cm(force: Optional[str] = None) -> ContextManager[Session]`

Provide a synchronous database session as a context manager.

**Parameters:**
- `force` (Optional[str]): If `"read"`, provides a read-only session; otherwise, a write session

**Yields:**
- `Session`: A SQLAlchemy Session object

**Example:**

```python
# Write session (default)
with db.get_db_cm() as session:
    user = User.create(session, {"name": "Charlie"})

# Read session
with db.get_db_cm(force="read") as session:
    users = User.get_all(session)
```

#### `get_db_cm_read() -> ContextManager[Session]`

Provide a synchronous read-only session via a context manager.

**Yields:**
- `Session`: A SQLAlchemy Session configured for read-only operations

**Example:**

```python
with db.get_db_cm_read() as session:
    users = session.query(User).filter(User.active == True).all()
    for user in users:
        print(user.name)
```

#### `get_db_cm_write() -> ContextManager[Session]`

Provide a synchronous write-enabled session via a context manager.

**Yields:**
- `Session`: A SQLAlchemy Session configured for write operations

**Example:**

```python
with db.get_db_cm_write() as session:
    user = User(name="David", email="david@example.com")
    session.add(user)
    session.commit()
```

## Asynchronous Session Methods

### Async Session Factories

#### `async_session_local() -> AsyncSession`

Create a new asynchronous write session.

**Returns:**
- `AsyncSession`: A new AsyncSession instance configured for write operations

**Example:**

```python
async def create_user():
    session = db.async_session_local()
    try:
        user = await session.run_sync(
            lambda s: User.create(s, {"name": "Eve"})
        )
        return user
    finally:
        await session.close()
```

#### `async_session_local_read() -> AsyncSession`

Create a new asynchronous read session.

**Returns:**
- `AsyncSession`: A new AsyncSession instance configured for read-only operations

**Example:**

```python
async def get_users():
    session = db.async_session_local_read()
    try:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return users
    finally:
        await session.close()
```

### Async Session Generators

#### `async_get_db(force: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]`

Async generator yielding a session with safe cleanup on errors.

**Parameters:**
- `force` (Optional[str]): If `"read"`, yields a read-only session; otherwise, a write session

**Yields:**
- `AsyncSession`: An AsyncSession object

**Example:**

```python
async def create_user():
    async for session in db.async_get_db():
        user = await session.run_sync(
            lambda s: User.create(s, {"name": "Frank"})
        )
        return user
```

#### `async_get_db_read() -> AsyncGenerator[AsyncSession, None]`

Yield async read sessions.

**Yields:**
- `AsyncSession`: An AsyncSession configured for read-only operations

**Example:**

```python
async def get_users():
    async for session in db.async_get_db_read():
        result = await session.execute(select(User))
        return result.scalars().all()
```

#### `async_get_db_write() -> AsyncGenerator[AsyncSession, None]`

Yield async write sessions.

**Yields:**
- `AsyncSession`: An AsyncSession configured for write operations

**Example:**

```python
async def update_user(user_id: str, data: dict):
    async for session in db.async_get_db_write():
        user = await session.get(User, user_id)
        if user:
            await session.run_sync(lambda s: user.update(s, data))
        return user
```

### Async Context Managers

#### `async_get_db_cm(force: Optional[str] = None) -> AsyncContextManager[AsyncSession]`

Async context manager yielding an async session.

**Parameters:**
- `force` (Optional[str]): If `"read"`, provides a read-only session; otherwise, a write session

**Yields:**
- `AsyncSession`: An AsyncSession object

**Example:**

```python
async def create_user(name: str, email: str):
    async with db.async_get_db_cm() as session:
        user = await session.run_sync(
            lambda s: User.create(s, {"name": name, "email": email})
        )
        return user
```

#### `async_get_db_cm_read() -> AsyncContextManager[AsyncSession]`

Async context manager for a read session.

**Yields:**
- `AsyncSession`: An AsyncSession configured for read-only operations

**Example:**

```python
async def get_users():
    async with db.async_get_db_cm_read() as session:
        result = await session.execute(select(User))
        return result.scalars().all()
```

#### `async_get_db_cm_write() -> AsyncContextManager[AsyncSession]`

Async context manager for a write session.

**Yields:**
- `AsyncSession`: An AsyncSession configured for write operations

**Example:**

```python
async def delete_user(user_id: str):
    async with db.async_get_db_cm_write() as session:
        user = await session.get(User, user_id)
        if user:
            await session.delete(user)
            await session.commit()
```

## Database Operations

### `create_tables() -> None`

Create all tables defined on the declarative base.

This method uses the write engine to create tables in the database based on all models that inherit from the declarative base. The operation is idempotent - existing tables will not be modified.

**Returns:**
- `None`

**Example:**

```python
# Define models first
class User(ModelBase, db.base):
    __tablename__ = 'users'
    name: Mapped[str] = mapped_column(String(100))

class Post(ModelBase, db.base):
    __tablename__ = 'posts'
    title: Mapped[str] = mapped_column(String(200))

# Create all tables
db.create_tables()
```

**Note:** This is typically called once during application initialization or in migration scripts.

### `close_all_connections() -> None`

Dispose of all engine connection pools.

Closes all database connections and cleans up connection pool resources for both read and write engines (sync and async).

**Returns:**
- `None`

**Example:**

```python
# During application shutdown
db.close_all_connections()
```

**Use Cases:**
- Application shutdown
- Before forking processes
- During testing cleanup

### `check_database_health() -> bool`

Ping both write and read databases to verify they are operational.

Executes a simple `SELECT 1` query on both write and read database connections to verify connectivity and operational status.

**Returns:**
- `bool`: `True` if both databases respond successfully, `False` otherwise

**Example:**

```python
if db.check_database_health():
    print("Database is healthy")
else:
    print("Database health check failed")
```

**Use Cases:**
- Health check endpoints in web applications
- Monitoring and alerting
- Pre-flight checks before critical operations

## Usage Patterns

### FastAPI Integration

#### Using Dependency Injection

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()

def get_read_db():
    """Dependency for read operations."""
    yield from db.get_db_read()

def get_write_db():
    """Dependency for write operations."""
    yield from db.get_db_write()

@app.get("/users/{user_id}")
def read_user(user_id: str, session: Session = Depends(get_read_db)):
    user = User.get_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()

@app.post("/users")
def create_user(user_data: dict, session: Session = Depends(get_write_db)):
    user = User.create(session, user_data)
    return user.to_dict()

@app.put("/users/{user_id}")
def update_user(
    user_id: str,
    user_data: dict,
    session: Session = Depends(get_write_db)
):
    user = User.get_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.update(session, user_data)
    return user.to_dict()

@app.delete("/users/{user_id}")
def delete_user(user_id: str, session: Session = Depends(get_write_db)):
    user = User.get_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.delete(session)
    return {"message": "User deleted"}
```

#### Health Check Endpoint

```python
@app.get("/health")
def health_check():
    if db.check_database_health():
        return {"status": "healthy", "database": "connected"}
    return {"status": "unhealthy", "database": "disconnected"}
```

### Async FastAPI

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

app = FastAPI()

async def get_async_read_db():
    """Async dependency for read operations."""
    async for session in db.async_get_db_read():
        yield session

async def get_async_write_db():
    """Async dependency for write operations."""
    async for session in db.async_get_db_write():
        yield session

@app.get("/users/{user_id}")
async def read_user(user_id: str, session: AsyncSession = Depends(get_async_read_db)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()

@app.post("/users")
async def create_user(
    user_data: dict,
    session: AsyncSession = Depends(get_async_write_db)
):
    user = await session.run_sync(lambda s: User.create(s, user_data))
    return user.to_dict()
```

### Context Manager Pattern

```python
def process_users():
    """Process users with automatic session management."""
    with db.get_db_cm_read() as session:
        users = User.get_all(session, limit=100)
    
    for user in users:
        with db.get_db_cm_write() as session:
            user.update(session, {"processed": True})
```

### Transaction Management

```python
def transfer_credits(from_user_id: str, to_user_id: str, amount: int):
    """Transfer credits between users in a transaction."""
    with db.get_db_cm_write() as session:
        try:
            from_user = User.get_by_id(session, from_user_id)
            to_user = User.get_by_id(session, to_user_id)
            
            if not from_user or not to_user:
                raise ValueError("User not found")
            
            if from_user.credits < amount:
                raise ValueError("Insufficient credits")
            
            from_user.update(session, {"credits": from_user.credits - amount})
            to_user.update(session, {"credits": to_user.credits + amount})
            
            # Commit happens automatically if no exception
        except Exception as e:
            # Rollback happens automatically on exception
            raise
```

### Read/Write Splitting

```python
class UserService:
    """Service class demonstrating read/write splitting."""
    
    @staticmethod
    def get_user(user_id: str):
        """Read from read replica."""
        with db.get_db_cm_read() as session:
            return User.get_by_id(session, user_id)
    
    @staticmethod
    def create_user(data: dict):
        """Write to primary database."""
        with db.get_db_cm_write() as session:
            return User.create(session, data)
    
    @staticmethod
    def update_user(user_id: str, data: dict):
        """Write to primary database."""
        with db.get_db_cm_write() as session:
            user = User.get_by_id(session, user_id)
            if user:
                return user.update(session, data)
    
    @staticmethod
    def list_users(limit: int = 100):
        """Read from read replica."""
        with db.get_db_cm_read() as session:
            return User.get_all(session, limit=limit)
```

### Multiple Database Instances

```python
# Application database
app_config = DatabaseConfig().set_db_name("app_db")
app_db = DatabaseInstance(app_config, base_name="AppBase")

# Analytics database
analytics_config = DatabaseConfig().set_db_name("analytics_db")
analytics_db = DatabaseInstance(analytics_config, base_name="AnalyticsBase")

# Define models for each database
class User(ModelBase, app_db.base):
    __tablename__ = 'users'
    name: Mapped[str] = mapped_column(String(100))

class Event(ModelBase, analytics_db.base):
    __tablename__ = 'events'
    event_type: Mapped[str] = mapped_column(String(50))

# Use separate instances
def log_user_action(user_id: str, action: str):
    # Read from app database
    with app_db.get_db_cm_read() as session:
        user = User.get_by_id(session, user_id)
    
    # Write to analytics database
    with analytics_db.get_db_cm_write() as session:
        event = Event.create(session, {
            "user_id": user_id,
            "event_type": action
        })
```

## Best Practices

1. **Always use context managers or generators** for session management to ensure proper cleanup

2. **Use read sessions for queries** to distribute load to read replicas:
   ```python
   with db.get_db_cm_read() as session:
       users = User.get_all(session)
   ```

3. **Use write sessions for modifications**:
   ```python
   with db.get_db_cm_write() as session:
       user = User.create(session, data)
   ```

4. **Leverage dependency injection** in FastAPI for cleaner code

5. **Check database health** before critical operations or in health endpoints

6. **Close connections on shutdown**:
   ```python
   @app.on_event("shutdown")
   def shutdown_event():
       db.close_all_connections()
   ```

7. **Use separate database instances** for different databases to maintain isolation

8. **Handle exceptions properly** - sessions automatically rollback on exceptions

## Error Handling

The `DatabaseInstance` automatically handles common error scenarios:

### Automatic Rollback

```python
with db.get_db_cm_write() as session:
    try:
        user = User.create(session, {"email": "duplicate@example.com"})
    except IntegrityError:
        # Session is automatically rolled back
        print("Duplicate email address")
```

### Session Cleanup

```python
# Session is automatically closed even if an exception occurs
with db.get_db_cm_read() as session:
    users = session.query(User).filter(User.invalid_column == "value").all()
    # Even if this raises an exception, session.close() is called
```

### Failed Session Closure Logging

If session closure fails, the database instance logs a warning with details about the error using the `footprint` logger.

## Performance Considerations

1. **Connection Pooling**: Configure appropriate pool sizes in `DatabaseConfig`
2. **Read Replicas**: Use `set_db_host_read()` to distribute read load
3. **Session Lifecycle**: Keep sessions short-lived - acquire, use, close
4. **Batch Operations**: Use bulk operations from `dtpyfw.db.utils` for large datasets
5. **Eager Loading**: Use `options` parameter in queries to avoid N+1 problems

## Related Documentation

- [config.md](./config.md) - Database configuration
- [model.md](./model.md) - Model base classes and CRUD operations
- [health.md](./health.md) - Health check utilities
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)

## Notes

- Each `DatabaseInstance` has its own isolated declarative base to prevent metadata conflicts
- Async and sync engines are created independently and can be used simultaneously
- Read and write sessions use separate engines, enabling read/write splitting at the database level
- All session methods handle cleanup and rollback automatically
- The instance maintains connection pools for efficient connection reuse
