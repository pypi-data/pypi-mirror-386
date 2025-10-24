# Retry Mechanisms

## Overview

The `dtpyfw.core.retry` module provides retry utilities for functions with exponential backoff. This module helps handle transient failures in network calls, database operations, or any unreliable operations by automatically retrying with configurable delays and logging.

## Module Path

```python
from dtpyfw.core.retry import retry, retry_async, retry_wrapper
```

## Functions

### `retry_wrapper(...)` (Decorator)

Decorator for retrying functions with exponential backoff.

**Description:**

Returns a decorator that wraps sync or async functions with retry logic. Automatically detects if the decorated function is async and applies the appropriate retry mechanism.

**Parameters:**

- **max_attempts** (`int`, optional): Maximum number of attempts before giving up. Defaults to 3
- **sleep_time** (`int | float`, optional): Initial delay in seconds between retries. Defaults to 2
- **backoff** (`int | float`, optional): Multiplier for increasing delay after each retry. Defaults to 2
- **exceptions** (`Tuple[Type[Exception], ...]`, optional): Tuple of exception types to catch and retry. Defaults to `(Exception,)`
- **log_tries** (`bool`, optional): If True, logs warnings for each retry attempt. Defaults to False

**Returns:**

- Decorator function that wraps callables with retry logic

**Example:**

```python
from dtpyfw.core.retry import retry_wrapper
import requests

@retry_wrapper(max_attempts=3, sleep_time=1, backoff=2)
def fetch_data(url: str):
    """Fetch data with automatic retry."""
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()

# Usage - will retry up to 3 times with exponential backoff
data = fetch_data("https://api.example.com/data")
```

---

### `retry(func, *args, **kwargs)`

Retry a synchronous callable with exponential backoff.

**Description:**

Executes a callable with automatic retry logic. Delegates to `retry_async` if the function is a coroutine. On failure, waits with exponentially increasing delay before retrying.

**Parameters:**

- **func** (`Callable[..., T]`): The callable to execute
- ***args** (`Any`): Positional arguments to pass to func
- **sleep_time** (`int | float`, optional): Initial delay in seconds. Defaults to 2
- **max_attempts** (`int`, optional): Maximum number of attempts. Defaults to 3
- **backoff** (`int | float`, optional): Delay multiplier. Defaults to 2
- **exceptions** (`Tuple[Type[Exception], ...]`, optional): Exceptions to catch. Defaults to `(Exception,)`
- **log_tries** (`bool`, optional): Log retry attempts. Defaults to False
- ****kwargs** (`Any`): Keyword arguments to pass to func

**Returns:**

- The result from the successful function execution

**Raises:**

- The caught exception if all retry attempts fail

**Example:**

```python
from dtpyfw.core.retry import retry
import requests

def fetch_user(user_id: int):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    response.raise_for_status()
    return response.json()

# Execute with retry
user = retry(fetch_user, 123, max_attempts=3, sleep_time=1)
```

---

### `retry_async(func, *args, **kwargs)`

Retry an async function with exponential backoff.

**Description:**

Executes an async callable with automatic retry logic. On failure, waits with exponentially increasing delay before retrying. Logs final failures to footprint.

**Parameters:**

- **func** (`Callable[..., Awaitable[T]]`): The async callable to execute
- ***args** (`Any`): Positional arguments to pass to func
- **sleep_time** (`int | float`, optional): Initial delay in seconds. Defaults to 2
- **max_attempts** (`int`, optional): Maximum number of attempts. Defaults to 3
- **backoff** (`int | float`, optional): Delay multiplier. Defaults to 2
- **exceptions** (`Tuple[Type[Exception], ...]`, optional): Exceptions to catch. Defaults to `(Exception,)`
- **log_tries** (`bool`, optional): Log retry attempts. Defaults to False
- ****kwargs** (`Any`): Keyword arguments to pass to func

**Returns:**

- The result from the successful function execution

**Raises:**

- The caught exception if all retry attempts fail

**Example:**

```python
from dtpyfw.core.retry import retry_async
import httpx

async def fetch_data_async(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

# Execute with retry
data = await retry_async(
    fetch_data_async,
    "https://api.example.com/data",
    max_attempts=3,
    sleep_time=1
)
```

## Complete Usage Examples

### 1. HTTP Request with Retry

```python
from dtpyfw.core.retry import retry_wrapper
from dtpyfw.core.request import request
from dtpyfw.core.exception import RequestException

@retry_wrapper(
    max_attempts=3,
    sleep_time=2,
    backoff=2,
    exceptions=(RequestException,),
    log_tries=True
)
def fetch_user_data(user_id: int):
    """Fetch user with retry on failure."""
    return request(
        method="GET",
        path=f"/api/users/{user_id}",
        host="https://api.example.com",
        timeout=10
    )

# Usage - retries on RequestException
try:
    user = fetch_user_data(123)
except RequestException as e:
    print(f"Failed after 3 attempts: {e.message}")
```

### 2. Database Connection with Retry

```python
from dtpyfw.core.retry import retry_wrapper
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

@retry_wrapper(
    max_attempts=5,
    sleep_time=1,
    backoff=2,
    exceptions=(OperationalError,)
)
def connect_to_database(db_url: str):
    """Connect to database with retry."""
    engine = create_engine(db_url)
    connection = engine.connect()
    return connection

# Usage - retries on connection failures
try:
    conn = connect_to_database("postgresql://localhost/mydb")
except OperationalError as e:
    print("Could not connect to database after 5 attempts")
```

### 3. Async API Calls

```python
from dtpyfw.core.retry import retry_wrapper
import httpx

@retry_wrapper(max_attempts=3, sleep_time=1, log_tries=True)
async def fetch_multiple_users(user_ids: list):
    """Fetch multiple users concurrently with retry."""
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"https://api.example.com/users/{uid}")
            for uid in user_ids
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

# Usage
users = await fetch_multiple_users([1, 2, 3, 4, 5])
```

### 4. File Processing with Retry

```python
from dtpyfw.core.retry import retry_wrapper
import os

@retry_wrapper(
    max_attempts=3,
    sleep_time=0.5,
    exceptions=(IOError, OSError)
)
def read_file_with_retry(filepath: str):
    """Read file with retry on IO errors."""
    with open(filepath, 'r') as f:
        return f.read()

# Usage - retries on file access errors
try:
    content = read_file_with_retry("/path/to/file.txt")
except (IOError, OSError) as e:
    print(f"Could not read file after retries: {e}")
```

### 5. Custom Retry Logic

```python
from dtpyfw.core.retry import retry
from requests.exceptions import Timeout, ConnectionError

def custom_api_call(endpoint: str):
    response = requests.get(endpoint, timeout=5)
    if response.status_code == 429:  # Rate limited
        raise ConnectionError("Rate limited")
    response.raise_for_status()
    return response.json()

# Retry only on specific errors with custom delays
result = retry(
    custom_api_call,
    "https://api.example.com/data",
    max_attempts=5,
    sleep_time=5,
    backoff=1.5,
    exceptions=(Timeout, ConnectionError),
    log_tries=True
)
```

### 6. Conditional Retry

```python
from dtpyfw.core.retry import retry_wrapper

class RetryableError(Exception):
    """Custom exception for retryable errors."""
    pass

@retry_wrapper(
    max_attempts=3,
    sleep_time=1,
    exceptions=(RetryableError,)
)
def process_data(data):
    """Process data with selective retry."""
    result = perform_operation(data)
    
    if result is None:
        # Retry this error
        raise RetryableError("Operation returned None")
    
    if result < 0:
        # Don't retry this error
        raise ValueError("Invalid result")
    
    return result

# Retries on RetryableError, but not on ValueError
```

### 7. Redis Connection Pool

```python
from dtpyfw.core.retry import retry_wrapper
import redis

class RedisClient:
    def __init__(self, host: str, port: int = 6379):
        self.host = host
        self.port = port
        self.client = None
    
    @retry_wrapper(
        max_attempts=3,
        sleep_time=1,
        backoff=2,
        exceptions=(redis.ConnectionError,)
    )
    def connect(self):
        """Connect to Redis with retry."""
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True
        )
        self.client.ping()  # Test connection
        return self.client
    
    @retry_wrapper(max_attempts=2, sleep_time=0.5)
    def get(self, key: str):
        """Get value with retry."""
        if not self.client:
            self.connect()
        return self.client.get(key)

# Usage
client = RedisClient("localhost")
client.connect()
value = client.get("mykey")
```

## Exponential Backoff Explained

With default settings (`sleep_time=2`, `backoff=2`):

- **Attempt 1**: Executes immediately
- **Attempt 2**: Waits 2 seconds (2 * 2^0)
- **Attempt 3**: Waits 4 seconds (2 * 2^1)
- **Attempt 4**: Waits 8 seconds (2 * 2^2)

```python
# Custom backoff progression
@retry_wrapper(
    max_attempts=4,
    sleep_time=1,
    backoff=1.5
)
def my_function():
    pass

# Progression: 0s, 1s, 1.5s, 2.25s
```

## Error Logging

When `log_tries=True`, the module logs to footprint:

**Warning on retry:**

```python
{
    "log_type": "warning",
    "message": "An error happened while we retry to run my_function at the 1 attempt.",
    "controller": "dtpyfw.core.retry.retry_async",
    "subject": "Warning at retrying my_function",
    "payload": {
        "type": "ConnectionError",
        "message": "Connection refused",
        "traceback": [...],
        "kwargs": {...},
        "args": (...)
    }
}
```

**Error on final failure:**

```python
{
    "log_type": "error",
    "message": "We could not finish the current job in the function my_function.",
    "controller": "dtpyfw.core.retry.retry_async",
    "subject": "Error at my_function",
    "payload": {exception_details}
}
```

## Best Practices

1. **Choose appropriate max_attempts:**
   ```python
   # For critical operations
   @retry_wrapper(max_attempts=5)
   
   # For non-critical operations
   @retry_wrapper(max_attempts=2)
   
   # For very unreliable services
   @retry_wrapper(max_attempts=10)
   ```

2. **Specify exact exceptions:**
   ```python
   # Good - only retry expected failures
   @retry_wrapper(exceptions=(ConnectionError, Timeout))
   
   # Risky - might retry programming errors
   @retry_wrapper(exceptions=(Exception,))
   ```

3. **Use reasonable delays:**
   ```python
   # Fast retry for quick operations
   @retry_wrapper(sleep_time=0.1, backoff=1.5)
   
   # Slower retry for rate-limited APIs
   @retry_wrapper(sleep_time=5, backoff=2)
   ```

4. **Enable logging for debugging:**
   ```python
   # During development
   @retry_wrapper(log_tries=True)
   
   # In production (only log final failures)
   @retry_wrapper(log_tries=False)
   ```

5. **Set maximum delays:**
   ```python
   # Prevent extremely long waits
   import time
   
   def limited_retry(func, max_wait=30):
       total_wait = 0
       for attempt in range(3):
           try:
               return func()
           except Exception:
               wait = min(2 ** attempt, max_wait - total_wait)
               time.sleep(wait)
               total_wait += wait
       raise
   ```

## Performance Considerations

- **Network Operations**: Use longer `sleep_time` (2-5 seconds)
- **Database Operations**: Use moderate `sleep_time` (1-2 seconds)
- **File Operations**: Use short `sleep_time` (0.1-0.5 seconds)
- **Rate-Limited APIs**: Match `sleep_time` to rate limit reset time

## Related Modules

- **dtpyfw.core.request** - HTTP requests that benefit from retry
- **dtpyfw.core.exception** - Exception handling and serialization
- **dtpyfw.log.footprint** - Error and warning logging
- **dtpyfw.db** - Database operations with retry
- **dtpyfw.redis** - Redis operations with retry

## Dependencies

- `asyncio` - For async retry support
- `time` - For sleep delays
- `functools.wraps` - For decorator preservation

## See Also

- [Exponential Backoff Algorithm](https://en.wikipedia.org/wiki/Exponential_backoff)
- [Retry Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
