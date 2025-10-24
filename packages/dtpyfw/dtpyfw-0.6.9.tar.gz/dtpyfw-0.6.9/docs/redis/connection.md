# dtpyfw.redis.connection

## Overview

The `connection` module provides the `RedisInstance` class for managing both synchronous and asynchronous Redis connections with connection pooling, automatic URL construction, and context managers for safe resource handling. This class serves as the central interface for all Redis operations in the dtpyfw framework, offering lazy initialization of connection pools and unified access patterns for different use cases.

## Module Information

- **Module Path**: `dtpyfw.redis.connection`
- **Class**: `RedisInstance`
- **Dependencies**:
  - `redis` - Synchronous Redis client library
  - `redis.asyncio` - Asynchronous Redis client library
  - `urllib.parse` - URL encoding (standard library)
- **Internal Dependencies**:
  - `dtpyfw.redis.config.RedisConfig` - Configuration builder

## Key Features

- **Dual Mode Operation**: Supports both synchronous and asynchronous Redis operations
- **Connection Pooling**: Automatic connection pool management for efficient resource usage
- **Lazy Initialization**: Connection pools created only when first accessed
- **Context Managers**: Safe resource handling with automatic cleanup
- **URL Construction**: Automatic Redis URL building from configuration parameters
- **Authentication Support**: Username/password and SSL/TLS support
- **Pool Management**: Methods to reset and reconfigure connection pools

## Exported Classes

```python
__all__ = ("RedisInstance",)
```

---

## RedisInstance Class

The `RedisInstance` class manages Redis connection pools for both synchronous and asynchronous operations, providing a unified interface for Redis connectivity.

### Class Signature

```python
class RedisInstance:
    def __init__(self, redis_config: RedisConfig) -> None:
        ...
```

### Constructor

```python
def __init__(self, redis_config: RedisConfig) -> None:
```

Initialize Redis instance from configuration.

#### Parameters

| Parameter      | Type          | Required | Description                                                              |
|----------------|---------------|----------|--------------------------------------------------------------------------|
| `redis_config` | `RedisConfig` | Yes      | RedisConfig object containing connection parameters                      |

#### Attributes

| Attribute     | Type                     | Description                                            |
|---------------|--------------------------|--------------------------------------------------------|
| `config`      | `RedisConfig`            | Configuration object passed during initialization      |
| `redis_url`   | `str`                    | Constructed Redis connection URL                       |
| `_sync_pool`  | `Optional[ConnectionPool]` | Lazily initialized synchronous connection pool       |
| `_async_pool` | `Optional[AsyncConnectionPool]` | Lazily initialized asynchronous connection pool |

#### Description

Creates a new `RedisInstance` with the provided configuration. The constructor builds the Redis connection URL immediately but defers connection pool creation until the first connection request. This lazy initialization pattern improves application startup time and resource usage.

#### Example

```python
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.connection import RedisInstance

# Create configuration
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0") \
    .set_redis_password("secret") \
    .set_redis_max_connections(20)

# Create Redis instance
redis_instance = RedisInstance(config)

# Connection pools not yet created
print(redis_instance.redis_url)  # redis://:secret@localhost:6379/0
```

---

## URL Construction

### `_set_redis_url()`

Construct the Redis connection URL from configuration (internal method).

```python
def _set_redis_url(self) -> str:
    ...
```

#### Returns

`str` - A complete Redis connection URL.

#### Description

Builds a Redis connection URL from individual configuration parameters if a full URL is not provided in the configuration. Handles:
- SSL/TLS protocol selection (`redis://` vs `rediss://`)
- URL encoding of username and password for special characters
- Various authentication patterns (password-only, username-only, both)
- Proper URL formatting

URL format: `redis[s]://[username:password@]host:port/database`

#### Examples

```python
# Password-only authentication
# Config: host="localhost", port=6379, db="0", password="secret"
# Result: "redis://:secret@localhost:6379/0"

# Username and password
# Config: host="redis.example.com", port=6379, db="0", 
#         username="admin", password="pass"
# Result: "redis://admin:pass@redis.example.com:6379/0"

# SSL connection
# Config: host="secure.redis.com", port=6380, db="0", ssl=True
# Result: "rediss://secure.redis.com:6380/0"

# Special characters in password (automatically encoded)
# Config: password="p@ss:w0rd!"
# Result: "redis://:p%40ss%3Aw0rd%21@localhost:6379/0"
```

---

### `get_redis_url()`

Get the Redis connection URL.

```python
def get_redis_url(self) -> str:
    ...
```

#### Returns

`str` - The constructed or configured Redis connection URL.

#### Description

Returns the Redis connection URL that will be used for creating connections. This can be useful for debugging connection issues or logging configuration details.

#### Example

```python
redis_instance = RedisInstance(config)
print(f"Connecting to: {redis_instance.get_redis_url()}")
# Output: Connecting to: redis://localhost:6379/0
```

---

## Connection Pool Management

### `_get_sync_pool()`

Get or create a synchronous connection pool (internal method).

```python
def _get_sync_pool(self) -> ConnectionPool:
    ...
```

#### Returns

`ConnectionPool` - A synchronous Redis connection pool instance.

#### Description

Creates a synchronous connection pool on first access and caches it for subsequent calls. The pool is configured with `max_connections` and `socket_timeout` from the RedisConfig. Default values are 10 connections and 5-second timeout if not specified.

Connection pooling improves performance by reusing existing connections instead of creating new ones for each operation.

---

### `_get_async_pool()`

Get or create an asynchronous connection pool (internal method).

```python
def _get_async_pool(self) -> AsyncConnectionPool:
    ...
```

#### Returns

`AsyncConnectionPool` - An asynchronous Redis connection pool instance.

#### Description

Creates an asynchronous connection pool on first access and caches it for subsequent calls. Similar to the synchronous pool but designed for async/await patterns. Uses the same configuration parameters for max connections and timeout.

---

### `reset_sync_pool()`

Reset and disconnect the synchronous connection pool.

```python
def reset_sync_pool(self) -> None:
    ...
```

#### Description

Disconnects all connections in the synchronous pool and clears the pool reference. The pool will be recreated on the next access. Useful for:
- Cleanup during application shutdown
- Reconfiguration scenarios
- Testing teardown
- Recovering from connection errors

#### Example

```python
redis_instance = RedisInstance(config)

# Use Redis
with redis_instance.get_redis() as client:
    client.set("key", "value")

# Reset pool (disconnect all connections)
redis_instance.reset_sync_pool()

# Next access will create a new pool
with redis_instance.get_redis() as client:
    value = client.get("key")
```

---

### `reset_async_pool()`

Reset and disconnect the asynchronous connection pool.

```python
async def reset_async_pool(self) -> None:
    ...
```

#### Description

Asynchronously disconnects all connections in the async pool and clears the pool reference. Must be called with `await`. The pool will be recreated on the next access.

#### Example

```python
redis_instance = RedisInstance(config)

# Use async Redis
async with redis_instance.get_async_redis() as client:
    await client.set("key", "value")

# Reset pool (disconnect all connections)
await redis_instance.reset_async_pool()

# Next access will create a new pool
async with redis_instance.get_async_redis() as client:
    value = await client.get("key")
```

---

## Client Creation Methods

### `get_redis_client()`

Create a synchronous Redis client using the connection pool.

```python
def get_redis_client(self) -> redis.Redis:
    ...
```

#### Returns

`redis.Redis` - A synchronous Redis client instance.

#### Description

Creates a new Redis client that uses the managed connection pool. The client can be used for any redis-py synchronous operations. While you can use this method directly, it's recommended to use the `get_redis()` context manager for automatic resource management.

**Note**: When using this method directly, you're responsible for closing the client when done.

#### Example

```python
redis_instance = RedisInstance(config)

# Direct client creation
client = redis_instance.get_redis_client()
try:
    client.set("key", "value")
    value = client.get("key")
    print(value)
finally:
    client.close()  # Must close manually

# Better: Use context manager instead
with redis_instance.get_redis() as client:
    client.set("key", "value")
    value = client.get("key")
# Automatic cleanup
```

---

### `get_async_redis_client()`

Create an asynchronous Redis client using the connection pool.

```python
async def get_async_redis_client(self) -> AsyncRedis:
    ...
```

#### Returns

`AsyncRedis` - An asynchronous Redis client instance.

#### Description

Creates a new async Redis client that uses the managed connection pool. The client supports all redis-py async operations. Like the sync version, it's recommended to use the `get_async_redis()` context manager for proper resource management.

**Note**: Must be called with `await`. When using directly, close the client when done.

#### Example

```python
redis_instance = RedisInstance(config)

# Direct client creation
client = await redis_instance.get_async_redis_client()
try:
    await client.set("key", "value")
    value = await client.get("key")
    print(value)
finally:
    await client.close()  # Must close manually

# Better: Use async context manager instead
async with redis_instance.get_async_redis() as client:
    await client.set("key", "value")
    value = await client.get("key")
# Automatic cleanup
```

---

## Context Manager Methods (Recommended)

### `get_redis()`

Create a context manager for a synchronous Redis client.

```python
@contextmanager
def get_redis(self) -> Generator[redis.Redis, None, None]:
    ...
```

#### Yields

`redis.Redis` - A synchronous Redis client instance.

#### Description

Provides a Redis client within a context manager that handles cleanup automatically. This is the **recommended way** to get a synchronous Redis client as it ensures proper resource management even if exceptions occur.

The connection itself is managed by the connection pool, so the context manager primarily provides a clean interface for getting and using a client.

#### Examples

##### Basic Usage

```python
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig

config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

redis_instance = RedisInstance(config)

# Simple key-value operations
with redis_instance.get_redis() as client:
    client.set("user:1:name", "John Doe")
    name = client.get("user:1:name")
    print(name)  # b'John Doe'
```

##### Error Handling

```python
try:
    with redis_instance.get_redis() as client:
        client.set("key", "value")
        # Raise an error
        raise ValueError("Something went wrong")
except ValueError:
    # Context manager still ensures proper cleanup
    print("Error handled, Redis connection cleaned up")
```

##### Multiple Operations

```python
with redis_instance.get_redis() as client:
    # String operations
    client.set("counter", 0)
    client.incr("counter")
    client.incrby("counter", 5)
    
    # Hash operations
    client.hset("user:1", "name", "John")
    client.hset("user:1", "email", "john@example.com")
    
    # List operations
    client.lpush("tasks", "task1", "task2", "task3")
    
    # Set operations
    client.sadd("tags", "python", "redis", "cache")
    
    # Get data
    counter = client.get("counter")
    user = client.hgetall("user:1")
    tasks = client.lrange("tasks", 0, -1)
    tags = client.smembers("tags")
```

##### Pipeline for Bulk Operations

```python
with redis_instance.get_redis() as client:
    # Use pipeline for multiple operations
    pipe = client.pipeline()
    for i in range(100):
        pipe.set(f"key:{i}", f"value:{i}")
    pipe.execute()
    
    print("100 keys set efficiently")
```

---

### `get_async_redis()`

Create a context manager for an asynchronous Redis client.

```python
@asynccontextmanager
async def get_async_redis(self) -> AsyncGenerator[AsyncRedis, None]:
    ...
```

#### Yields

`AsyncRedis` - An asynchronous Redis client instance.

#### Description

Provides an async Redis client within an async context manager. This is the **recommended way** to get an asynchronous Redis client. Must be used with `async with` statement.

#### Examples

##### Basic Async Usage

```python
import asyncio
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig

async def main():
    config = RedisConfig() \
        .set_redis_host("localhost") \
        .set_redis_port(6379) \
        .set_redis_db("0")
    
    redis_instance = RedisInstance(config)
    
    async with redis_instance.get_async_redis() as client:
        await client.set("user:1:name", "Jane Doe")
        name = await client.get("user:1:name")
        print(name)  # b'Jane Doe'

asyncio.run(main())
```

##### Concurrent Operations

```python
async def fetch_user_data(redis_instance: RedisInstance, user_id: int):
    async with redis_instance.get_async_redis() as client:
        name = await client.get(f"user:{user_id}:name")
        email = await client.get(f"user:{user_id}:email")
        return {"name": name, "email": email}

async def main():
    redis_instance = RedisInstance(config)
    
    # Fetch multiple users concurrently
    users = await asyncio.gather(
        fetch_user_data(redis_instance, 1),
        fetch_user_data(redis_instance, 2),
        fetch_user_data(redis_instance, 3)
    )
    
    print(users)

asyncio.run(main())
```

##### Async Pipeline

```python
async def bulk_insert(redis_instance: RedisInstance, data: dict):
    async with redis_instance.get_async_redis() as client:
        pipe = client.pipeline()
        for key, value in data.items():
            await pipe.set(key, value)
        await pipe.execute()

async def main():
    redis_instance = RedisInstance(config)
    
    data = {f"key:{i}": f"value:{i}" for i in range(100)}
    await bulk_insert(redis_instance, data)
    print("100 keys inserted")

asyncio.run(main())
```

##### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig

app = FastAPI()

# Global Redis instance
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")
redis_instance = RedisInstance(config)

@app.get("/user/{user_id}")
async def get_user(user_id: int):
    async with redis_instance.get_async_redis() as client:
        name = await client.get(f"user:{user_id}:name")
        if name:
            return {"user_id": user_id, "name": name.decode()}
        return {"error": "User not found"}

@app.post("/user/{user_id}")
async def create_user(user_id: int, name: str):
    async with redis_instance.get_async_redis() as client:
        await client.set(f"user:{user_id}:name", name)
        return {"user_id": user_id, "name": name}
```

---

## Complete Usage Examples

### Example 1: Basic Synchronous Operations

```python
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.connection import RedisInstance

# Setup
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

redis_instance = RedisInstance(config)

# String operations
with redis_instance.get_redis() as client:
    # Set and get
    client.set("greeting", "Hello, Redis!")
    greeting = client.get("greeting")
    print(greeting.decode())  # Hello, Redis!
    
    # Increment counter
    client.set("visitors", 0)
    client.incr("visitors")
    client.incrby("visitors", 10)
    visitors = client.get("visitors")
    print(f"Visitors: {visitors.decode()}")  # Visitors: 11
    
    # Expiration
    client.setex("session:abc", 3600, "user_data")
    ttl = client.ttl("session:abc")
    print(f"Session expires in {ttl} seconds")
```

### Example 2: Hash Operations

```python
with redis_instance.get_redis() as client:
    # Store user profile
    client.hset("user:123", mapping={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "age": "30",
        "city": "New York"
    })
    
    # Get specific field
    name = client.hget("user:123", "name")
    print(f"Name: {name.decode()}")
    
    # Get all fields
    user = client.hgetall("user:123")
    for key, value in user.items():
        print(f"{key.decode()}: {value.decode()}")
    
    # Update field
    client.hset("user:123", "age", "31")
    
    # Check if field exists
    has_phone = client.hexists("user:123", "phone")
    print(f"Has phone: {has_phone}")  # False
```

### Example 3: List Operations (Queue/Stack)

```python
with redis_instance.get_redis() as client:
    # Task queue (FIFO)
    client.lpush("tasks", "task1", "task2", "task3")
    
    # Process tasks
    while client.llen("tasks") > 0:
        task = client.rpop("tasks")
        print(f"Processing: {task.decode()}")
    
    # Stack (LIFO)
    client.rpush("history", "page1", "page2", "page3")
    last_page = client.rpop("history")
    print(f"Last visited: {last_page.decode()}")
    
    # Get range
    client.rpush("logs", "log1", "log2", "log3")
    recent_logs = client.lrange("logs", 0, 2)
    for log in recent_logs:
        print(log.decode())
```

### Example 4: Set Operations

```python
with redis_instance.get_redis() as client:
    # Add members
    client.sadd("languages:python", "django", "flask", "fastapi")
    client.sadd("languages:javascript", "react", "vue", "express")
    
    # Check membership
    has_django = client.sismember("languages:python", "django")
    print(f"Python has Django: {has_django}")  # True
    
    # Get all members
    python_frameworks = client.smembers("languages:python")
    print("Python frameworks:")
    for fw in python_frameworks:
        print(f"  - {fw.decode()}")
    
    # Set operations
    client.sadd("set1", "a", "b", "c")
    client.sadd("set2", "b", "c", "d")
    
    # Union
    union = client.sunion("set1", "set2")
    print(f"Union: {[x.decode() for x in union]}")
    
    # Intersection
    intersection = client.sinter("set1", "set2")
    print(f"Intersection: {[x.decode() for x in intersection]}")
    
    # Difference
    diff = client.sdiff("set1", "set2")
    print(f"Difference: {[x.decode() for x in diff]}")
```

### Example 5: Sorted Sets

```python
with redis_instance.get_redis() as client:
    # Leaderboard
    client.zadd("leaderboard", {
        "player1": 100,
        "player2": 250,
        "player3": 175,
        "player4": 300
    })
    
    # Get top players
    top_3 = client.zrevrange("leaderboard", 0, 2, withscores=True)
    print("Top 3 players:")
    for player, score in top_3:
        print(f"  {player.decode()}: {int(score)} points")
    
    # Get rank
    rank = client.zrevrank("leaderboard", "player2")
    print(f"player2 rank: {rank + 1}")
    
    # Increment score
    client.zincrby("leaderboard", 50, "player1")
    
    # Get score
    score = client.zscore("leaderboard", "player1")
    print(f"player1 score: {int(score)}")
```

### Example 6: Async Web Scraper with Caching

```python
import asyncio
import httpx
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig

async def fetch_url_cached(
    redis_instance: RedisInstance,
    url: str,
    ttl: int = 3600
) -> str:
    """Fetch URL with Redis caching."""
    cache_key = f"cache:url:{url}"
    
    # Try cache first
    async with redis_instance.get_async_redis() as client:
        cached = await client.get(cache_key)
        if cached:
            print(f"Cache hit: {url}")
            return cached.decode()
    
    # Fetch from web
    print(f"Fetching: {url}")
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(url)
        content = response.text
    
    # Cache result
    async with redis_instance.get_async_redis() as client:
        await client.setex(cache_key, ttl, content)
    
    return content

async def main():
    config = RedisConfig() \
        .set_redis_host("localhost") \
        .set_redis_port(6379) \
        .set_redis_db("0")
    
    redis_instance = RedisInstance(config)
    
    urls = [
        "https://example.com",
        "https://example.org",
        "https://example.net"
    ]
    
    # Fetch concurrently
    results = await asyncio.gather(*[
        fetch_url_cached(redis_instance, url) for url in urls
    ])
    
    print(f"Fetched {len(results)} pages")

asyncio.run(main())
```

### Example 7: Session Management

```python
import json
import uuid
from datetime import datetime
from typing import Dict, Optional

class SessionManager:
    def __init__(self, redis_instance: RedisInstance):
        self.redis = redis_instance
        self.session_ttl = 3600  # 1 hour
    
    def create_session(self, user_id: int) -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        
        with self.redis.get_redis() as client:
            client.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_data)
            )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        with self.redis.get_redis() as client:
            data = client.get(f"session:{session_id}")
            if data:
                # Refresh TTL
                client.expire(f"session:{session_id}", self.session_ttl)
                return json.loads(data)
        return None
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        with self.redis.get_redis() as client:
            client.delete(f"session:{session_id}")

# Usage
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("1")  # Separate DB for sessions

redis_instance = RedisInstance(config)
session_mgr = SessionManager(redis_instance)

# Create session
session_id = session_mgr.create_session(user_id=123)
print(f"Created session: {session_id}")

# Get session
session = session_mgr.get_session(session_id)
print(f"Session data: {session}")

# Delete session
session_mgr.delete_session(session_id)
```

### Example 8: Rate Limiting

```python
from datetime import datetime

class RateLimiter:
    def __init__(self, redis_instance: RedisInstance):
        self.redis = redis_instance
    
    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """Check if request is allowed under rate limit."""
        with self.redis.get_redis() as client:
            current = client.get(key)
            
            if current is None:
                # First request in window
                pipe = client.pipeline()
                pipe.set(key, 1)
                pipe.expire(key, window_seconds)
                pipe.execute()
                return True
            
            count = int(current)
            if count < max_requests:
                client.incr(key)
                return True
            
            return False

# Usage
redis_instance = RedisInstance(config)
limiter = RateLimiter(redis_instance)

# Allow 10 requests per minute per IP
ip_address = "192.168.1.1"
allowed = limiter.is_allowed(
    key=f"rate_limit:{ip_address}",
    max_requests=10,
    window_seconds=60
)

if allowed:
    print("Request allowed")
else:
    print("Rate limit exceeded")
```

---

## Best Practices

### 1. Use Context Managers

Always use `get_redis()` or `get_async_redis()` context managers instead of directly creating clients:

```python
# Good: Automatic cleanup
with redis_instance.get_redis() as client:
    client.set("key", "value")

# Bad: Manual cleanup required
client = redis_instance.get_redis_client()
client.set("key", "value")
client.close()  # Easy to forget
```

### 2. Reuse RedisInstance

Create one `RedisInstance` per configuration and reuse it throughout your application:

```python
# Good: Single instance
redis_instance = RedisInstance(config)

def func1():
    with redis_instance.get_redis() as client:
        pass

def func2():
    with redis_instance.get_redis() as client:
        pass

# Bad: Creating new instances
def func1():
    redis_instance = RedisInstance(config)  # Don't do this
    with redis_instance.get_redis() as client:
        pass
```

### 3. Use Appropriate Database Numbers

Separate different data types or purposes into different databases:

```python
# Cache database
cache_config = RedisConfig().set_redis_db("0")
cache_redis = RedisInstance(cache_config)

# Session database
session_config = RedisConfig().set_redis_db("1")
session_redis = RedisInstance(session_config)

# Queue database
queue_config = RedisConfig().set_redis_db("2")
queue_redis = RedisInstance(queue_config)
```

### 4. Handle Connection Errors

```python
from redis.exceptions import ConnectionError, TimeoutError

try:
    with redis_instance.get_redis() as client:
        client.set("key", "value")
except (ConnectionError, TimeoutError) as e:
    print(f"Redis connection failed: {e}")
    # Fallback logic or retry
```

### 5. Use Pipelines for Bulk Operations

```python
# Good: Pipeline for bulk operations
with redis_instance.get_redis() as client:
    pipe = client.pipeline()
    for i in range(1000):
        pipe.set(f"key:{i}", f"value:{i}")
    pipe.execute()

# Bad: Individual operations (slow)
with redis_instance.get_redis() as client:
    for i in range(1000):
        client.set(f"key:{i}", f"value:{i}")
```

### 6. Async for I/O-Bound Operations

```python
# Good: Async for web services
async def fetch_user_data(user_id: int):
    async with redis_instance.get_async_redis() as client:
        return await client.hgetall(f"user:{user_id}")

# Good: Sync for simple scripts
def backup_data():
    with redis_instance.get_redis() as client:
        return client.keys("*")
```

### 7. Implement Health Checks

```python
from dtpyfw.redis.health import is_redis_connected

# Check connection health
is_healthy, error = is_redis_connected(redis_instance)
if not is_healthy:
    print(f"Redis health check failed: {error}")
    # Alert or failover
```

---

## Performance Considerations

### Connection Pooling Benefits

Connection pools significantly improve performance by reusing connections:

```python
# Without pool: ~10ms per operation (creating connection)
# With pool: ~1ms per operation (reusing connection)

config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_max_connections(50)  # Adjust based on load
```

### Lazy Initialization

Pools are created only when first accessed, improving startup time:

```python
redis_instance = RedisInstance(config)  # Fast: no connection yet
# ... application initialization ...
with redis_instance.get_redis() as client:  # First access: creates pool
    client.set("key", "value")
```

### Async Performance

Async operations prevent blocking the event loop:

```python
# Multiple concurrent operations don't block each other
async def concurrent_operations():
    async with redis_instance.get_async_redis() as client:
        results = await asyncio.gather(
            client.get("key1"),
            client.get("key2"),
            client.get("key3")
        )
    return results
```

---

## Related Documentation

- [dtpyfw.redis.config](config.md) - Redis configuration builder
- [dtpyfw.redis.caching](caching.md) - Redis caching utilities that use RedisInstance
- [dtpyfw.redis.health](health.md) - Redis health check functions

---

## External References

- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Redis Connection Pooling](https://redis-py.readthedocs.io/en/stable/connections.html)
- [Redis Commands](https://redis.io/commands/)
- [Async Redis Client](https://redis-py.readthedocs.io/en/stable/examples/asyncio_examples.html)
