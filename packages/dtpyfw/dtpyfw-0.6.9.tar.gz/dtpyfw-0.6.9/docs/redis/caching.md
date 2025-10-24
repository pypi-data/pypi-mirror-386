# dtpyfw.redis.caching

## Overview

The `caching` module provides comprehensive Redis-based caching utilities for Python functions and data with support for both synchronous and asynchronous operations. This module enables automatic memoization of function results, conditional caching based on argument values, and efficient data compression using zlib. It seamlessly integrates with the dtpyfw logging system and handles errors gracefully.

## Module Information

- **Module Path**: `dtpyfw.redis.caching`
- **Dependencies**:
  - `redis` - Redis client library
  - `zlib` - Data compression (standard library)
  - `hashlib` - Cache key generation (standard library)
  - `json` - Data serialization (standard library)
- **Internal Dependencies**:
  - `dtpyfw.core.exception` - Exception handling utilities
  - `dtpyfw.core.jsonable_encoder` - JSON serialization for complex types
  - `dtpyfw.log.footprint` - Logging integration
  - `dtpyfw.redis.connection` - Redis connection management

## Key Features

- **Automatic Cache Key Generation**: Deterministic key generation from function arguments using SHA-256 hashing
- **Data Compression**: Uses zlib compression to minimize Redis memory usage
- **Flexible Expiration**: Configurable TTL (time-to-live) for cached values
- **Conditional Caching**: Cache only when specific argument conditions are met
- **Sync & Async Support**: Works with both synchronous and asynchronous functions
- **Error Resilience**: Continues operation even if caching fails, with comprehensive logging
- **Type Safety**: Full type annotations for IDE support and type checking

## Exported Functions

```python
__all__ = (
    "cache_data",
    "cache_function",
    "cache_wrapper",
)
```

---

## Public API Functions

### `cache_data()`

Cache a dictionary in Redis with optional compression and expiration.

```python
def cache_data(
    response: Dict[str, Any],
    cache_key: str,
    redis_instance: Redis,
    expire: Optional[int] = None,
) -> Dict[str, Any]:
    ...
```

#### Parameters

| Parameter        | Type                | Required | Default | Description                                                                          |
|------------------|---------------------|----------|---------|--------------------------------------------------------------------------------------|
| `response`       | `Dict[str, Any]`    | Yes      | -       | The dictionary data to cache                                                         |
| `cache_key`      | `str`               | Yes      | -       | The Redis key under which to store the data                                          |
| `redis_instance` | `Redis`             | Yes      | -       | An active Redis client instance for cache operations                                 |
| `expire`         | `Optional[int]`     | No       | `None`  | Expiration time in seconds. If None, the key persists indefinitely                   |

#### Returns

`Dict[str, Any]` - The original response dictionary, unchanged (enables pass-through pattern).

#### Description

Serializes a dictionary using `jsonable_encoder` (which handles datetime, UUID, and other complex types), compresses it with zlib, and stores it in Redis. The function deletes any existing value at the cache key before writing the new value. If caching fails, the error is logged but the original response is still returned, making the caching transparent to the caller.

#### Error Handling

Catches all exceptions during caching operations and logs them using the footprint logger with detailed error information. Never raises exceptions, ensuring cache failures don't break application flow.

#### Examples

**Basic Caching**

```python
from dtpyfw.redis.caching import cache_data
from redis import Redis

redis_client = Redis(host="localhost", port=6379)

# Cache user data for 1 hour
user_data = {
    "user_id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": datetime.now()
}

cached_data = cache_data(
    response=user_data,
    cache_key="user:123",
    redis_instance=redis_client,
    expire=3600
)

# Returns the same data, but it's now cached in Redis
print(cached_data)  # {"user_id": 123, "name": "John Doe", ...}
```

**Caching API Responses**

```python
import requests
from dtpyfw.redis.caching import cache_data

def fetch_weather_data(city: str) -> dict:
    response = requests.get(f"https://api.weather.com/{city}")
    weather_data = response.json()
    
    # Cache for 30 minutes (1800 seconds)
    return cache_data(
        response=weather_data,
        cache_key=f"weather:{city}",
        redis_instance=redis_client,
        expire=1800
    )

weather = fetch_weather_data("London")
```

**Permanent Caching (No Expiration)**

```python
# Cache configuration data without expiration
config_data = {"version": "1.0", "features": ["api", "cache"]}

cache_data(
    response=config_data,
    cache_key="app:config",
    redis_instance=redis_client,
    expire=None  # No expiration
)
```

---

### `cache_function()`

Execute a synchronous function with Redis caching support.

```python
def cache_function(
    func: Callable[..., Any],
    redis: RedisInstance,
    namespace: str,
    expire: Optional[int] = None,
    cache_only_for: Optional[List[Dict[str, Any]]] = None,
    skip_cache_keys: Optional[Set[str]] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    ...
```

#### Parameters

| Parameter         | Type                                | Required | Default | Description                                                                 |
|-------------------|-------------------------------------|----------|---------|-----------------------------------------------------------------------------|
| `func`            | `Callable[..., Any]`                | Yes      | -       | The synchronous function to execute and cache                               |
| `redis`           | `RedisInstance`                     | Yes      | -       | RedisInstance providing Redis connectivity                                  |
| `namespace`       | `str`                               | Yes      | -       | Cache key namespace prefix                                                  |
| `expire`          | `Optional[int]`                     | No       | `None`  | Optional cache expiration time in seconds                                   |
| `cache_only_for`  | `Optional[List[Dict[str, Any]]]`    | No       | `None`  | Optional conditions determining when to cache (see details below)           |
| `skip_cache_keys` | `Optional[Set[str]]`                | No       | `None`  | Optional set of kwarg names to exclude from cache key generation            |
| `*args`           | `Any`                               | No       | -       | Positional arguments to pass to the function                                |
| `**kwargs`        | `Any`                               | No       | -       | Keyword arguments to pass to the function                                   |

#### Returns

`Any` - The function's return value, either from cache or fresh execution.

#### Description

Checks Redis for a cached result before executing the function. If a cache hit occurs, returns the cached value immediately. On a cache miss, executes the function, caches the result (if caching conditions are met), and returns the result. Uses synchronous Redis I/O operations.

The cache key is automatically generated from the namespace, positional arguments, and keyword arguments (excluding those in `skip_cache_keys`).

#### Conditional Caching (`cache_only_for`)

The `cache_only_for` parameter allows fine-grained control over when results are cached. It accepts a list of condition dictionaries with the following structure:

```python
cache_only_for = [
    {
        "kwarg": "status",        # Keyword argument name to check
        "operator": "in",         # Currently only "in" operator is supported
        "value": ["active", "pending"]  # List of values to match
    }
]
```

When conditions are specified, caching only occurs when at least one condition is satisfied. If `cache_only_for` is `None`, all function calls are cached.

#### Examples

**Basic Function Caching**

```python
from dtpyfw.redis.caching import cache_function
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig

# Setup Redis
config = RedisConfig().set_redis_host("localhost").set_redis_port(6379).set_redis_db("0")
redis = RedisInstance(config)

# Define an expensive function
def calculate_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)

# Cache the result for 1 hour
result = cache_function(
    func=calculate_fibonacci,
    redis=redis,
    namespace="math:fibonacci",
    expire=3600,
    n=35
)

print(f"Fibonacci(35) = {result}")
# First call: computed and cached
# Subsequent calls with n=35: returned from cache instantly
```

**Caching with Multiple Arguments**

```python
def get_user_orders(user_id: int, status: str, limit: int = 10) -> list:
    # Expensive database query
    return fetch_orders_from_db(user_id, status, limit)

# Cache completed orders for 1 hour
orders = cache_function(
    func=get_user_orders,
    redis=redis,
    namespace="orders:user",
    expire=3600,
    user_id=123,
    status="completed",
    limit=20
)
```

**Conditional Caching**

```python
def fetch_product_data(product_id: int, include_reviews: bool = False) -> dict:
    # Fetch product data from API
    return api_call(product_id, include_reviews)

# Only cache when include_reviews is False (product data is more stable)
product = cache_function(
    func=fetch_product_data,
    redis=redis,
    namespace="product:data",
    expire=1800,
    cache_only_for=[
        {"kwarg": "include_reviews", "operator": "in", "value": [False]}
    ],
    product_id=456,
    include_reviews=False
)
```

**Skipping Arguments from Cache Key**

```python
def log_and_fetch_data(user_id: int, request_id: str, timestamp: str) -> dict:
    # request_id and timestamp change on every call but shouldn't affect caching
    return get_user_profile(user_id)

# Exclude request_id and timestamp from cache key generation
data = cache_function(
    func=log_and_fetch_data,
    redis=redis,
    namespace="user:profile",
    expire=600,
    skip_cache_keys={"request_id", "timestamp"},
    user_id=789,
    request_id="abc-123-def",
    timestamp="2025-10-24T10:30:00"
)

# Different request_id/timestamp values will still hit the same cache
```

**Caching Database Queries**

```python
def get_active_users_by_role(role: str, limit: int = 100) -> list:
    query = "SELECT * FROM users WHERE role = %s AND status = 'active' LIMIT %s"
    return db.execute(query, (role, limit))

# Cache for 5 minutes
users = cache_function(
    func=get_active_users_by_role,
    redis=redis,
    namespace="db:users:active",
    expire=300,
    role="admin",
    limit=50
)
```

---

### `acache_function()`

Execute a function asynchronously with Redis caching support.

```python
async def acache_function(
    func: Callable[..., Any],
    redis: RedisInstance,
    namespace: str,
    expire: Optional[int] = None,
    cache_only_for: Optional[List[Dict[str, Any]]] = None,
    skip_cache_keys: Optional[Set[str]] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    ...
```

#### Parameters

Same as `cache_function()`. See above for detailed parameter descriptions.

#### Returns

`Any` - The function's return value, either from cache or fresh execution.

#### Description

Asynchronous version of `cache_function()`. Checks Redis for a cached result before executing the function. Redis operations are offloaded to threads using `asyncio.to_thread()` to avoid blocking the event loop. Supports both synchronous and asynchronous functions—if the provided function is a coroutine, it will be awaited; otherwise, it will be called normally.

#### Examples

**Caching Async Functions**

```python
import asyncio
from dtpyfw.redis.caching import acache_function
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig

config = RedisConfig().set_redis_host("localhost").set_redis_port(6379).set_redis_db("0")
redis = RedisInstance(config)

async def fetch_user_from_api(user_id: int) -> dict:
    # Simulate async API call
    await asyncio.sleep(1)
    return {"user_id": user_id, "name": f"User {user_id}"}

async def main():
    # Cache for 30 minutes
    user = await acache_function(
        func=fetch_user_from_api,
        redis=redis,
        namespace="api:user",
        expire=1800,
        user_id=123
    )
    print(user)
    # First call: takes 1 second
    # Subsequent calls: instant from cache

asyncio.run(main())
```

**Caching Async Database Queries**

```python
async def get_posts_by_author(author_id: int, published: bool = True) -> list:
    # Async database query
    query = "SELECT * FROM posts WHERE author_id = $1 AND published = $2"
    return await db.fetch(query, author_id, published)

async def main():
    posts = await acache_function(
        func=get_posts_by_author,
        redis=redis,
        namespace="posts:author",
        expire=600,
        author_id=456,
        published=True
    )
```

**Caching with Conditional Logic**

```python
async def fetch_analytics(
    metric: str,
    date_range: str,
    cache_mode: str = "enabled"
) -> dict:
    # Expensive analytics calculation
    return await calculate_metrics(metric, date_range)

async def main():
    # Only cache when cache_mode is "enabled"
    analytics = await acache_function(
        func=fetch_analytics,
        redis=redis,
        namespace="analytics",
        expire=3600,
        cache_only_for=[
            {"kwarg": "cache_mode", "operator": "in", "value": ["enabled"]}
        ],
        metric="page_views",
        date_range="last_7_days",
        cache_mode="enabled"
    )
```

**Mixed Sync/Async Functions**

```python
# Synchronous function
def calculate_stats(data: list) -> dict:
    return {"mean": sum(data) / len(data), "count": len(data)}

async def main():
    # acache_function works with both sync and async functions
    stats = await acache_function(
        func=calculate_stats,
        redis=redis,
        namespace="stats",
        expire=1200,
        data=[1, 2, 3, 4, 5]
    )
    print(stats)  # {"mean": 3.0, "count": 5}
```

---

### `cache_wrapper()`

Create a decorator that adds Redis caching to a function.

```python
def cache_wrapper(
    redis: RedisInstance,
    namespace: str,
    expire: Optional[int] = None,
    cache_only_for: Optional[List[Dict[str, Any]]] = None,
    skip_cache_keys: Optional[Set[str]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    ...
```

#### Parameters

| Parameter         | Type                                | Required | Default | Description                                                                 |
|-------------------|-------------------------------------|----------|---------|-----------------------------------------------------------------------------|
| `redis`           | `RedisInstance`                     | Yes      | -       | RedisInstance providing Redis connectivity                                  |
| `namespace`       | `str`                               | Yes      | -       | Cache key namespace prefix for all cached calls                             |
| `expire`          | `Optional[int]`                     | No       | `None`  | Optional cache expiration time in seconds                                   |
| `cache_only_for`  | `Optional[List[Dict[str, Any]]]`    | No       | `None`  | Optional conditions determining when to cache results                       |
| `skip_cache_keys` | `Optional[Set[str]]`                | No       | `None`  | Optional set of kwarg names to exclude from cache key generation            |

#### Returns

`Callable` - A decorator function that wraps the target function with caching logic.

#### Description

Returns a decorator that automatically adds Redis caching to any function. Automatically detects whether the decorated function is synchronous or asynchronous and applies the appropriate caching strategy. This is the most convenient way to add caching to functions, using Python's decorator syntax.

The decorator preserves function metadata using `functools.wraps`, ensuring that the wrapped function's name, docstring, and annotations are maintained.

#### Examples

**Basic Decorator Usage**

```python
from dtpyfw.redis.caching import cache_wrapper
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig

config = RedisConfig().set_redis_host("localhost").set_redis_port(6379).set_redis_db("0")
redis = RedisInstance(config)

@cache_wrapper(
    redis=redis,
    namespace="user:data",
    expire=3600  # 1 hour
)
def get_user_profile(user_id: int) -> dict:
    """Fetch user profile from database."""
    return db.query("SELECT * FROM users WHERE id = %s", user_id)

# Usage is transparent
profile = get_user_profile(123)
# First call: hits database and caches result
# Subsequent calls with user_id=123: instant from cache
```

**Decorating Async Functions**

```python
@cache_wrapper(
    redis=redis,
    namespace="api:weather",
    expire=1800  # 30 minutes
)
async def fetch_weather(city: str, units: str = "metric") -> dict:
    """Fetch weather data from external API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.weather.com/{city}?units={units}")
        return response.json()

# Async usage
weather = await fetch_weather("London", units="metric")
```

**Conditional Caching with Decorator**

```python
@cache_wrapper(
    redis=redis,
    namespace="orders",
    expire=600,
    cache_only_for=[
        {
            "kwarg": "status",
            "operator": "in",
            "value": ["completed", "shipped"]
        }
    ]
)
def get_orders(user_id: int, status: str) -> list:
    """Get user orders by status."""
    return db.query("SELECT * FROM orders WHERE user_id = %s AND status = %s",
                    user_id, status)

# Only caches when status is "completed" or "shipped"
completed_orders = get_orders(123, "completed")  # Cached
pending_orders = get_orders(123, "pending")      # Not cached
```

**Excluding Arguments from Cache Key**

```python
@cache_wrapper(
    redis=redis,
    namespace="product:details",
    expire=7200,
    skip_cache_keys={"request_id", "user_agent", "timestamp"}
)
def get_product_details(
    product_id: int,
    request_id: str = None,
    user_agent: str = None,
    timestamp: str = None
) -> dict:
    """Fetch product details with request tracking."""
    log_request(request_id, user_agent, timestamp)
    return db.query("SELECT * FROM products WHERE id = %s", product_id)

# request_id, user_agent, and timestamp don't affect cache key
product = get_product_details(
    product_id=456,
    request_id="abc-123",
    user_agent="Mozilla/5.0",
    timestamp="2025-10-24T10:30:00"
)
```

**Class Method Caching**

```python
class UserService:
    def __init__(self, redis_instance: RedisInstance):
        self.redis = redis_instance
    
    @cache_wrapper(
        redis=redis,
        namespace="user:permissions",
        expire=900  # 15 minutes
    )
    def get_user_permissions(self, user_id: int) -> list:
        """Fetch user permissions from database."""
        return db.query("SELECT permission FROM user_permissions WHERE user_id = %s",
                       user_id)
    
    @cache_wrapper(
        redis=redis,
        namespace="user:roles",
        expire=1800
    )
    async def get_user_roles(self, user_id: int) -> list:
        """Async fetch user roles."""
        return await db.fetch("SELECT role FROM user_roles WHERE user_id = $1", user_id)

# Usage
service = UserService(redis)
permissions = service.get_user_permissions(123)
roles = await service.get_user_roles(123)
```

**Multiple Decorators**

```python
from functools import wraps
import time

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"Execution time: {time.time() - start:.2f}s")
        return result
    return wrapper

@timing_decorator
@cache_wrapper(redis=redis, namespace="reports", expire=3600)
def generate_sales_report(month: str, year: int) -> dict:
    """Generate monthly sales report."""
    # Expensive computation
    time.sleep(2)
    return {"month": month, "year": year, "total": 50000}

# First call: ~2 seconds (computed)
# Second call: ~0 seconds (cached)
report = generate_sales_report("October", 2025)
```

**Short Expiration for Real-time Data**

```python
@cache_wrapper(
    redis=redis,
    namespace="stock:price",
    expire=30  # 30 seconds
)
def get_stock_price(symbol: str) -> float:
    """Fetch current stock price."""
    return external_api.get_price(symbol)

# Cache very briefly to reduce API calls while keeping data fresh
price = get_stock_price("AAPL")
```

---

## Internal Helper Functions

These functions are used internally by the public API and are not exported. They are documented here for completeness and for developers who may need to understand the internal workings.

### `_cache_key_generator()`

Generate a unique cache key from function namespace and arguments.

```python
def _cache_key_generator(
    namespace: str,
    args: tuple,
    kwargs: Dict[str, Any],
    skip_cache_keys: Set[str],
) -> str:
    ...
```

#### Description

Creates a deterministic cache key by hashing function arguments using SHA-256. The key format is:

```
namespace:args_hash:kwargs_hash
```

Arguments specified in `skip_cache_keys` are excluded from the hash computation, allowing certain parameters (like request IDs or timestamps) to be ignored for caching purposes.

#### Example Key Generation

```python
# namespace="user", args=(123,), kwargs={"status": "active"}
# Result: "user:abc123def:xyz789fed"

# namespace="product", args=(), kwargs={"id": 456, "request_id": "xxx"}
# with skip_cache_keys={"request_id"}
# Result: "product:789abcdef"  (request_id excluded)
```

---

### `_should_cache()`

Determine whether a function call should be cached based on conditions.

```python
def _should_cache(
    cache_only_for: List[Dict[str, Any]] | None,
    kwargs: Dict[str, Any]
) -> bool:
    ...
```

#### Description

Evaluates caching conditions against function keyword arguments. Returns `True` if no conditions are specified (cache everything) or if at least one condition matches.

Currently supports only the `"in"` operator, which checks if the kwarg value is in a list of allowed values.

---

### `_decode_cached_value()`

Decompress and deserialize a cached value from Redis.

```python
def _decode_cached_value(
    cache_compressed: bytes,
    controller: str
) -> Optional[Any]:
    ...
```

#### Description

Reverses the compression and serialization applied during caching:
1. Decompresses zlib-compressed bytes
2. Decodes UTF-8 bytes to string
3. Deserializes JSON string to Python object

Returns `None` if any step fails, with error logging.

---

### `_encode_result()`

Encode and compress a result value for Redis storage.

```python
def _encode_result(result: Any) -> bytes:
    ...
```

#### Description

Prepares a result for Redis storage:
1. Serializes using `jsonable_encoder` (handles datetime, UUID, etc.)
2. Converts to JSON string
3. Encodes to UTF-8 bytes
4. Compresses with zlib

---

### `_redis_get_sync()`

Retrieve a value from Redis synchronously with error handling.

```python
def _redis_get_sync(
    redis_client: Redis,
    key: str,
    controller: str
) -> Optional[bytes]:
    ...
```

#### Description

Wrapper around `redis_client.get()` with error handling and logging. Returns `None` on any error instead of raising exceptions.

---

### `_redis_get_async()`

Retrieve a value from Redis asynchronously with error handling.

```python
async def _redis_get_async(
    redis_client: Redis,
    key: str,
    controller: str
) -> Optional[bytes]:
    ...
```

#### Description

Async version of `_redis_get_sync()`. Uses `asyncio.to_thread()` to offload the blocking Redis operation to a thread pool, preventing event loop blocking.

---

### `_redis_write_sync()`

Write a value to Redis synchronously with error handling.

```python
def _redis_write_sync(
    redis_client: Redis,
    key: str,
    value: bytes,
    expire: Optional[int],
    controller: str,
) -> None:
    ...
```

#### Description

Writes a value to Redis with optional expiration. Deletes any existing value at the key before writing. Uses `setex` for expiring keys or `set` for permanent keys.

---

### `_redis_write_async()`

Write a value to Redis asynchronously with error handling.

```python
async def _redis_write_async(
    redis_client: Redis,
    key: str,
    value: bytes,
    expire: Optional[int],
    controller: str,
) -> None:
    ...
```

#### Description

Async version of `_redis_write_sync()`. Uses `asyncio.to_thread()` to offload Redis operations to prevent event loop blocking.

---

## Complete Usage Examples

### Example 1: E-commerce Product Cache

```python
from dtpyfw.redis.caching import cache_wrapper
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig
from typing import Optional

# Setup
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")
redis = RedisInstance(config)

class ProductService:
    @cache_wrapper(
        redis=redis,
        namespace="product:details",
        expire=3600  # 1 hour
    )
    def get_product(self, product_id: int) -> dict:
        """Fetch product details."""
        return self.db.query(
            "SELECT * FROM products WHERE id = %s",
            product_id
        )
    
    @cache_wrapper(
        redis=redis,
        namespace="product:inventory",
        expire=60  # 1 minute (fresher data needed)
    )
    def get_inventory(self, product_id: int) -> int:
        """Get current inventory count."""
        return self.db.scalar(
            "SELECT quantity FROM inventory WHERE product_id = %s",
            product_id
        )
    
    @cache_wrapper(
        redis=redis,
        namespace="product:reviews",
        expire=1800,  # 30 minutes
        skip_cache_keys={"page"}  # Don't cache per-page
    )
    def get_reviews(
        self,
        product_id: int,
        rating: Optional[int] = None,
        page: int = 1
    ) -> list:
        """Get product reviews with optional filtering."""
        query = "SELECT * FROM reviews WHERE product_id = %s"
        params = [product_id]
        
        if rating:
            query += " AND rating = %s"
            params.append(rating)
        
        return self.db.query(query, *params)

# Usage
service = ProductService()
product = service.get_product(123)  # Cached for 1 hour
inventory = service.get_inventory(123)  # Cached for 1 minute
reviews = service.get_reviews(123, rating=5)  # Cached for 30 minutes
```

### Example 2: API Response Caching

```python
import httpx
from dtpyfw.redis.caching import cache_wrapper

@cache_wrapper(
    redis=redis,
    namespace="api:github:user",
    expire=1800  # 30 minutes
)
async def fetch_github_user(username: str) -> dict:
    """Fetch user data from GitHub API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.github.com/users/{username}")
        response.raise_for_status()
        return response.json()

@cache_wrapper(
    redis=redis,
    namespace="api:github:repos",
    expire=600,  # 10 minutes
    cache_only_for=[
        {"kwarg": "type", "operator": "in", "value": ["public", "private"]}
    ]
)
async def fetch_user_repos(username: str, type: str = "all") -> list:
    """Fetch user repositories."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/users/{username}/repos",
            params={"type": type}
        )
        response.raise_for_status()
        return response.json()

# Usage
async def main():
    user = await fetch_github_user("torvalds")
    repos = await fetch_user_repos("torvalds", type="public")
    
    print(f"User: {user['name']}")
    print(f"Public repos: {len(repos)}")
```

### Example 3: Database Query Caching

```python
from dtpyfw.redis.caching import cache_function
from datetime import datetime, timedelta

def get_sales_summary(
    start_date: datetime,
    end_date: datetime,
    category: str = None
) -> dict:
    """Generate sales summary report."""
    query = """
        SELECT
            COUNT(*) as order_count,
            SUM(total) as revenue,
            AVG(total) as avg_order_value
        FROM orders
        WHERE created_at BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    
    if category:
        query += " AND category = %s"
        params.append(category)
    
    return db.query_one(query, *params)

# Cache for 1 hour
last_month_start = datetime.now() - timedelta(days=30)
last_month_end = datetime.now()

summary = cache_function(
    func=get_sales_summary,
    redis=redis,
    namespace="reports:sales:summary",
    expire=3600,
    start_date=last_month_start,
    end_date=last_month_end,
    category="electronics"
)

print(f"Revenue: ${summary['revenue']:,.2f}")
print(f"Orders: {summary['order_count']}")
```

### Example 4: Conditional Caching for User Roles

```python
@cache_wrapper(
    redis=redis,
    namespace="user:data",
    expire=1800,
    cache_only_for=[
        {
            "kwarg": "role",
            "operator": "in",
            "value": ["customer", "subscriber"]  # Only cache regular users
        }
    ]
)
def get_user_dashboard(user_id: int, role: str) -> dict:
    """Get user dashboard data."""
    # Admin dashboards change frequently, don't cache them
    # Customer/subscriber dashboards are more stable, cache them
    
    return {
        "user_id": user_id,
        "widgets": fetch_widgets(user_id, role),
        "notifications": fetch_notifications(user_id),
        "stats": calculate_stats(user_id)
    }

# Cached
customer_dash = get_user_dashboard(123, role="customer")

# Not cached (admin data changes frequently)
admin_dash = get_user_dashboard(456, role="admin")
```

### Example 5: Cache Invalidation Pattern

```python
from dtpyfw.redis.caching import cache_wrapper
from redis import Redis

redis_client = Redis(host="localhost", port=6379)

@cache_wrapper(redis=redis, namespace="post:content", expire=7200)
def get_post(post_id: int) -> dict:
    """Fetch blog post."""
    return db.query("SELECT * FROM posts WHERE id = %s", post_id)

def update_post(post_id: int, title: str, content: str) -> None:
    """Update blog post and invalidate cache."""
    db.execute(
        "UPDATE posts SET title = %s, content = %s WHERE id = %s",
        title, content, post_id
    )
    
    # Manually invalidate cache
    # Cache key format: namespace:args_hash:kwargs_hash
    import hashlib, json
    args_hash = hashlib.sha256(json.dumps((post_id,), default=str).encode()).hexdigest()
    cache_key = f"post:content:{args_hash}:"
    redis_client.delete(cache_key)

# Usage
post = get_post(1)  # Cached
update_post(1, "New Title", "New Content")  # Invalidates cache
post = get_post(1)  # Fresh data from database
```

### Example 6: Multi-layer Caching

```python
from dtpyfw.redis.caching import cache_data, cache_wrapper

# Level 1: Function-level caching with short TTL
@cache_wrapper(redis=redis, namespace="user:profile:fast", expire=60)
def get_user_profile_fast(user_id: int) -> dict:
    """Get user profile with 1-minute cache."""
    return fetch_from_database(user_id)

# Level 2: Data-level caching with longer TTL
def get_user_profile_stable(user_id: int) -> dict:
    """Get user profile with 1-hour cache for stable data."""
    profile = fetch_from_database(user_id)
    
    # Cache stable fields longer
    stable_data = {
        "user_id": profile["user_id"],
        "username": profile["username"],
        "created_at": profile["created_at"]
    }
    
    cache_data(
        response=stable_data,
        cache_key=f"user:profile:stable:{user_id}",
        redis_instance=redis.get_redis_client(),
        expire=3600
    )
    
    return profile

# Different caching strategies for different data volatility
fast_profile = get_user_profile_fast(123)  # 1 minute cache
stable_profile = get_user_profile_stable(123)  # Hybrid caching
```

---

## Best Practices

### 1. Choose Appropriate Expiration Times

```python
# Fast-changing data: short TTL
@cache_wrapper(redis=redis, namespace="stock:price", expire=30)
def get_stock_price(symbol: str):
    pass

# Stable data: long TTL
@cache_wrapper(redis=redis, namespace="user:profile", expire=3600)
def get_user_profile(user_id: int):
    pass

# Configuration data: very long TTL or no expiration
cache_data(config, "app:config", redis_client, expire=86400)  # 24 hours
```

### 2. Use Meaningful Namespaces

```python
# Good: Clear hierarchy
@cache_wrapper(redis=redis, namespace="api:external:weather")
@cache_wrapper(redis=redis, namespace="db:users:profile")
@cache_wrapper(redis=redis, namespace="reports:sales:monthly")

# Bad: Generic namespaces
@cache_wrapper(redis=redis, namespace="data")
@cache_wrapper(redis=redis, namespace="cache1")
```

### 3. Exclude Volatile Arguments

```python
# Request metadata shouldn't affect caching
@cache_wrapper(
    redis=redis,
    namespace="products",
    expire=1800,
    skip_cache_keys={"request_id", "user_agent", "timestamp", "correlation_id"}
)
def get_product(product_id: int, request_id: str = None):
    pass
```

### 4. Use Conditional Caching Wisely

```python
# Cache only successful status codes
@cache_wrapper(
    redis=redis,
    namespace="orders",
    expire=600,
    cache_only_for=[
        {"kwarg": "status", "operator": "in", "value": ["completed", "shipped"]}
    ]
)
def get_orders(user_id: int, status: str):
    pass
```

### 5. Handle Cache Failures Gracefully

The caching functions already handle failures internally and log errors. Your application code doesn't need additional error handling:

```python
# No try-catch needed - caching failures are transparent
@cache_wrapper(redis=redis, namespace="data", expire=3600)
def fetch_data(id: int):
    return database_query(id)

# If Redis is down, the function still executes normally
data = fetch_data(123)  # Always returns data, cached or fresh
```

### 6. Monitor Cache Hit Rates

```python
from dtpyfw.redis.caching import cache_function
import logging

logger = logging.getLogger(__name__)

def monitored_cache_function(func, *args, **kwargs):
    """Wrapper to monitor cache hits."""
    cache_key = _cache_key_generator(namespace, args, kwargs, set())
    
    with redis.get_redis_client() as client:
        hit = client.exists(cache_key)
        logger.info(f"Cache {'HIT' if hit else 'MISS'} for key: {cache_key}")
    
    return cache_function(func=func, redis=redis, *args, **kwargs)
```

### 7. Use Async for I/O-bound Operations

```python
# Good: Async function with async caching
@cache_wrapper(redis=redis, namespace="api:data", expire=1800)
async def fetch_from_api(endpoint: str):
    async with httpx.AsyncClient() as client:
        return await client.get(endpoint)

# Less optimal: Sync function for I/O
@cache_wrapper(redis=redis, namespace="api:data", expire=1800)
def fetch_from_api_sync(endpoint: str):
    return requests.get(endpoint)  # Blocks thread
```

---

## Performance Considerations

### Compression Benefits

The module uses zlib compression for all cached values. This significantly reduces memory usage in Redis:

```python
import json

# Example data
data = {"users": [{"id": i, "name": f"User {i}"} for i in range(1000)]}

# Uncompressed: ~50KB
uncompressed_size = len(json.dumps(data))

# Compressed: ~5KB (10x reduction)
compressed_size = len(zlib.compress(json.dumps(data).encode()))

# Compression is automatic and transparent
cache_data(data, "users:list", redis_client, expire=3600)
```

### Cache Key Generation

Cache keys are generated using SHA-256 hashing of function arguments. This ensures:
- Deterministic keys (same arguments → same key)
- Fixed key length regardless of argument complexity
- No special character issues in Redis keys

### Async Operation Overhead

Async caching uses `asyncio.to_thread()` for Redis operations, which has slight overhead but prevents event loop blocking:

```python
# ~1-2ms overhead per operation
# Worth it to keep event loop responsive

async def fast_operation():
    # Without caching: 100ms
    # With async caching: 101-102ms (cache miss) or 1-2ms (cache hit)
    return await acache_function(...)
```

---

## Error Handling and Logging

All caching functions include comprehensive error handling and logging via `dtpyfw.log.footprint`:

### Error Categories

1. **Cache Read Errors**: Logged but don't prevent function execution
2. **Cache Write Errors**: Logged but don't prevent return of computed results
3. **Compression/Decompression Errors**: Logged and treated as cache miss

### Log Format

```python
footprint.leave(
    log_type="error",
    message="Error message",
    controller="dtpyfw.redis.caching.function_name",
    subject="Error category",
    payload={
        "redis_key": "the:cache:key",
        "error": {
            "type": "ConnectionError",
            "message": "Connection refused",
            "traceback": "..."
        }
    }
)
```

### Example Error Scenarios

```python
# Redis connection lost
@cache_wrapper(redis=redis, namespace="data", expire=3600)
def get_data(id: int):
    return fetch_from_db(id)

# If Redis is down:
# 1. Error logged: "Error while trying to retrieve data from cache"
# 2. Function executes normally: fetch_from_db(id)
# 3. Result returned to caller
# 4. Cache write attempted and logged if fails
# Result: Seamless degradation to non-cached operation
```

---

## Testing Strategies

### Unit Testing with Mock Redis

```python
from unittest.mock import Mock, patch
from dtpyfw.redis.caching import cache_function

def test_cache_function():
    # Mock Redis
    mock_redis = Mock()
    mock_redis.get_redis_client.return_value.__enter__.return_value.get.return_value = None
    
    def expensive_func(x):
        return x * 2
    
    result = cache_function(
        func=expensive_func,
        redis=mock_redis,
        namespace="test",
        expire=60,
        x=5
    )
    
    assert result == 10
```

### Integration Testing

```python
import pytest
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.caching import cache_wrapper

@pytest.fixture
def redis_instance():
    config = RedisConfig() \
        .set_redis_host("localhost") \
        .set_redis_port(6379) \
        .set_redis_db("15")  # Test database
    return RedisInstance(config)

def test_cache_decorator(redis_instance):
    call_count = 0
    
    @cache_wrapper(redis=redis_instance, namespace="test:counter", expire=60)
    def increment():
        nonlocal call_count
        call_count += 1
        return call_count
    
    # First call
    result1 = increment()
    assert result1 == 1
    
    # Second call (cached)
    result2 = increment()
    assert result2 == 1  # Same result from cache
    assert call_count == 1  # Function only called once
```

---

## Related Documentation

- [dtpyfw.redis.connection](connection.md) - Redis connection management
- [dtpyfw.redis.config](config.md) - Redis configuration builder
- [dtpyfw.redis.health](health.md) - Redis health checks
- [dtpyfw.core.jsonable_encoder](../core/jsonable_encoder.md) - JSON serialization for complex types
- [dtpyfw.log.footprint](../log/footprint.md) - Logging utilities

---

## External References

- [Redis Commands Documentation](https://redis.io/commands/)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Zlib Compression](https://docs.python.org/3/library/zlib.html)
