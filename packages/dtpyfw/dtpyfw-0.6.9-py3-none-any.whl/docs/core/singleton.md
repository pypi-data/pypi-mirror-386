# Singleton Pattern

## Overview

The `dtpyfw.core.singleton` module provides singleton pattern decorators for class instantiation. Singletons ensure that only one instance of a class exists, which is useful for managing shared resources like database connections, configuration objects, or cache managers.

## Module Path

```python
from dtpyfw.core.singleton import singleton_class, singleton_class_by_args
```

## Decorators

### `@singleton_class`

Decorator ensuring a class has only one instance regardless of arguments.

**Description:**

Creates a singleton pattern where only one instance of the class exists, even if instantiated with different arguments. Subsequent calls return the same instance created by the first call.

**Parameters:**

- **cls** (`Type[T]`): The class to convert to a singleton

**Returns:**

- A function that returns the singleton instance

**Example:**

```python
from dtpyfw.core.singleton import singleton_class

@singleton_class
class DatabaseConnection:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        print(f"Connected to {host}:{port}")

# First call creates instance
db1 = DatabaseConnection("localhost", 5432)
# Output: Connected to localhost:5432

# Second call returns same instance (different args ignored)
db2 = DatabaseConnection("remotehost", 3306)
# No output - returns existing instance

assert db1 is db2  # True
print(db1.host)  # Output: localhost (from first instantiation)
```

---

### `@singleton_class_by_args`

Decorator ensuring one instance per unique set of constructor arguments.

**Description:**

Creates a singleton-like pattern where instances are cached based on their constructor arguments. Each unique combination of arguments results in one cached instance that is reused for matching calls.

**Parameters:**

- **cls** (`Type[T]`): The class to apply argument-based singleton behavior to

**Returns:**

- A function that returns instances cached by arguments

**Example:**

```python
from dtpyfw.core.singleton import singleton_class_by_args

@singleton_class_by_args
class APIClient:
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint
        print(f"Created client for {endpoint}")

# Different arguments create different instances
client1 = APIClient("key1", "https://api1.com")
# Output: Created client for https://api1.com

client2 = APIClient("key2", "https://api2.com")
# Output: Created client for https://api2.com

# Same arguments return cached instance
client3 = APIClient("key1", "https://api1.com")
# No output - returns cached instance

assert client1 is client3  # True
assert client1 is not client2  # True
```

## Complete Usage Examples

### 1. Database Connection Pool

```python
from dtpyfw.core.singleton import singleton_class
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@singleton_class
class DatabaseManager:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)
        print("Database connection pool initialized")
    
    def get_session(self):
        return self.SessionLocal()
    
    def close(self):
        self.engine.dispose()

# Usage - only one connection pool for entire application
db = DatabaseManager("postgresql://localhost/mydb")
session1 = db.get_session()

# Returns same instance
db2 = DatabaseManager("postgresql://localhost/mydb")
assert db is db2
```

### 2. Configuration Manager

```python
from dtpyfw.core.singleton import singleton_class
from dtpyfw.core.env import Env
import json

@singleton_class
class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        self.config[key] = value
    
    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

# Usage - shared configuration across application
config = ConfigManager()
config.set("api_url", "https://api.example.com")

# Different module
config2 = ConfigManager()
assert config is config2
print(config2.get("api_url"))  # https://api.example.com
```

### 3. Cache Manager with Multiple Backends

```python
from dtpyfw.core.singleton import singleton_class_by_args
import redis

@singleton_class_by_args
class CacheBackend:
    def __init__(self, backend_type: str, host: str = "localhost"):
        self.backend_type = backend_type
        self.host = host
        
        if backend_type == "redis":
            self.client = redis.Redis(host=host)
        elif backend_type == "memory":
            self.client = {}
        
        print(f"Initialized {backend_type} cache at {host}")
    
    def get(self, key: str):
        if isinstance(self.client, dict):
            return self.client.get(key)
        return self.client.get(key)
    
    def set(self, key: str, value, ttl: int = 3600):
        if isinstance(self.client, dict):
            self.client[key] = value
        else:
            self.client.setex(key, ttl, value)

# Different backends are different singletons
redis_cache = CacheBackend("redis", "localhost")
memory_cache = CacheBackend("memory", "localhost")

# Same backend returns same instance
redis_cache2 = CacheBackend("redis", "localhost")
assert redis_cache is redis_cache2
assert redis_cache is not memory_cache
```

### 4. Logger Instance

```python
from dtpyfw.core.singleton import singleton_class
import logging

@singleton_class
class AppLogger:
    def __init__(self, name: str = "app", level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)

# Usage - single logger instance across application
logger = AppLogger()
logger.info("Application started")

# Different module
logger2 = AppLogger()
logger2.info("Processing request")  # Uses same logger
```

### 5. API Client Pool

```python
from dtpyfw.core.singleton import singleton_class_by_args
import requests

@singleton_class_by_args
class HTTPClient:
    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        
        if auth_token:
            self.session.headers.update({
                "Authorization": f"Bearer {auth_token}"
            })
        
        print(f"Created HTTP client for {base_url}")
    
    def get(self, path: str):
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self.session.get(url)
    
    def post(self, path: str, data: dict):
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self.session.post(url, json=data)

# Multiple API endpoints
api1_client = HTTPClient("https://api1.example.com", "token1")
api2_client = HTTPClient("https://api2.example.com", "token2")

# Reuse existing client
api1_client2 = HTTPClient("https://api1.example.com", "token1")
assert api1_client is api1_client2
```

### 6. Feature Flag Manager

```python
from dtpyfw.core.singleton import singleton_class
from typing import Dict

@singleton_class
class FeatureFlags:
    def __init__(self):
        self.flags: Dict[str, bool] = {}
        self._load_flags()
    
    def _load_flags(self):
        # Load from environment or config file
        self.flags = {
            "new_ui": True,
            "beta_features": False,
            "analytics": True
        }
    
    def is_enabled(self, feature: str) -> bool:
        return self.flags.get(feature, False)
    
    def enable(self, feature: str):
        self.flags[feature] = True
    
    def disable(self, feature: str):
        self.flags[feature] = False

# Usage - shared feature flags
flags = FeatureFlags()
if flags.is_enabled("new_ui"):
    render_new_ui()

# Different module
flags2 = FeatureFlags()
flags2.enable("beta_features")

# Changes reflect across all references
assert flags.is_enabled("beta_features")  # True
```

### 7. Thread-Safe Singleton (Manual Implementation)

```python
from dtpyfw.core.singleton import singleton_class
import threading

@singleton_class
class ThreadSafeCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.value += 1
            return self.value
    
    def get_value(self):
        with self.lock:
            return self.value

# Usage - thread-safe singleton
counter = ThreadSafeCounter()

def worker():
    for _ in range(1000):
        counter.increment()

threads = [threading.Thread(target=worker) for _ in range(10)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print(counter.get_value())  # 10000
```

## Comparison: singleton_class vs singleton_class_by_args

```python
from dtpyfw.core.singleton import singleton_class, singleton_class_by_args

# singleton_class - ONE instance total
@singleton_class
class GlobalCache:
    def __init__(self, size: int):
        self.size = size

cache1 = GlobalCache(100)
cache2 = GlobalCache(200)  # Same instance, size still 100
assert cache1 is cache2
print(cache1.size)  # 100

# singleton_class_by_args - ONE instance per unique args
@singleton_class_by_args
class RegionalCache:
    def __init__(self, region: str, size: int):
        self.region = region
        self.size = size

us_cache = RegionalCache("US", 100)
eu_cache = RegionalCache("EU", 200)  # Different instance
us_cache2 = RegionalCache("US", 100)  # Same as first

assert us_cache is not eu_cache
assert us_cache is us_cache2
```

## Best Practices

1. **Use for truly global resources:**
   ```python
   # Good use cases
   @singleton_class
   class DatabasePool: pass
   
   @singleton_class
   class ConfigManager: pass
   
   # Questionable
   @singleton_class
   class User: pass  # Users should not be singletons
   ```

2. **Be careful with mutable state:**
   ```python
   @singleton_class
   class DataStore:
       def __init__(self):
           self.data = []  # Shared across entire app
       
       def add(self, item):
           self.data.append(item)  # All instances see this
   ```

3. **Consider lazy initialization:**
   ```python
   @singleton_class
   class ExpensiveResource:
       def __init__(self):
           self._connection = None
       
       @property
       def connection(self):
           if self._connection is None:
               self._connection = create_expensive_connection()
           return self._connection
   ```

4. **Use singleton_class_by_args for multi-tenancy:**
   ```python
   @singleton_class_by_args
   class TenantDatabase:
       def __init__(self, tenant_id: str):
           self.tenant_id = tenant_id
           self.connection = create_tenant_connection(tenant_id)
   ```

## Limitations

1. **Testing Challenges:**
   - Singletons persist between tests
   - May need to reset state manually
   - Consider dependency injection for better testability

2. **Thread Safety:**
   - The decorators don't provide thread-safe initialization
   - Add your own locking if needed

3. **Memory:**
   - Singleton instances are never garbage collected
   - Use sparingly for long-lived applications

## Related Modules

- **dtpyfw.redis.connection** - Uses singleton for Redis connections
- **dtpyfw.db.database** - Database connections as singletons
- **dtpyfw.log** - Logger instances

## Dependencies

No external dependencies - uses only Python built-ins.

## See Also

- [Singleton Pattern](https://en.wikipedia.org/wiki/Singleton_pattern)
- [Python Design Patterns](https://refactoring.guru/design-patterns/singleton/python/example)
