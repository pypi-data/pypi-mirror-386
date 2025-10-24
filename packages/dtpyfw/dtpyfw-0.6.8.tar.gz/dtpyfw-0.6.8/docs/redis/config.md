# dtpyfw.redis.config

## Overview

The `config` module provides a fluent builder interface for constructing Redis connection configurations. The `RedisConfig` class allows you to set connection parameters in a chainable, readable manner, supporting various connection types including standard Redis, authenticated connections, SSL/TLS connections, and connection pooling configurations.

## Module Information

- **Module Path**: `dtpyfw.redis.config`
- **Class**: `RedisConfig`
- **Dependencies**: None (uses only Python standard library)
- **Internal Dependencies**: None

## Key Features

- **Fluent Interface**: All setter methods return `self` for method chaining
- **Flexible Configuration**: Supports both full URL and individual parameter configuration
- **Authentication Support**: Username/password authentication including Redis 6+ ACL
- **SSL/TLS Support**: Easy configuration for encrypted connections
- **Connection Pooling**: Configure pool size and timeout settings
- **Type Safety**: Full type annotations for IDE support

## Exported Classes

```python
__all__ = ("RedisConfig",)
```

---

## RedisConfig Class

The `RedisConfig` class provides a fluent builder pattern for constructing Redis connection configurations. All configuration values are stored internally and can be retrieved using the `get()` method.

### Class Signature

```python
class RedisConfig:
    def __init__(self) -> None:
        ...
```

### Constructor

```python
def __init__(self) -> None:
```

Initializes an empty Redis configuration builder with no preset values.

#### Returns

A new `RedisConfig` instance with an empty configuration dictionary.

#### Example

```python
from dtpyfw.redis.config import RedisConfig

# Create a new configuration builder
config = RedisConfig()
```

---

## Configuration Methods

All configuration methods return `self` to enable method chaining.

### Connection URL Configuration

#### `set_redis_url()`

Set the full Redis connection URL.

```python
def set_redis_url(self, redis_url: str) -> "RedisConfig":
    ...
```

##### Parameters

| Parameter   | Type  | Required | Description                                                                     |
|-------------|-------|----------|---------------------------------------------------------------------------------|
| `redis_url` | `str` | Yes      | Full Redis connection URL (e.g., `redis://localhost:6379/0`)                   |

##### Returns

`RedisConfig` - Self for method chaining.

##### Description

Allows specifying a complete connection string instead of individual components. This method takes precedence over individual host/port/db settings when both are provided. The URL should follow the standard Redis URL format.

URL formats:
- Basic: `redis://host:port/database`
- With password: `redis://:password@host:port/database`
- With username and password: `redis://username:password@host:port/database`
- SSL/TLS: `rediss://host:port/database` (note the double 's')

##### Examples

```python
# Basic connection
config = RedisConfig().set_redis_url("redis://localhost:6379/0")

# With authentication
config = RedisConfig().set_redis_url("redis://:mypassword@localhost:6379/0")

# With username and password (Redis 6+)
config = RedisConfig().set_redis_url("redis://admin:secret123@localhost:6379/0")

# SSL connection
config = RedisConfig().set_redis_url("rediss://secure.redis.cloud:6379/0")

# Cloud Redis (e.g., Redis Cloud, AWS ElastiCache)
config = RedisConfig().set_redis_url(
    "rediss://default:password@redis-12345.cloud.redislabs.com:12345/0"
)
```

---

### Individual Connection Parameters

#### `set_redis_host()`

Set the Redis server hostname or IP address.

```python
def set_redis_host(self, host: str) -> "RedisConfig":
    ...
```

##### Parameters

| Parameter | Type  | Required | Description                                      |
|-----------|-------|----------|--------------------------------------------------|
| `host`    | `str` | Yes      | Hostname or IP address of the Redis server       |

##### Returns

`RedisConfig` - Self for method chaining.

##### Description

Sets the hostname or IP address where the Redis server is running. Common values include `"localhost"`, `"127.0.0.1"`, or a remote server address.

##### Examples

```python
# Local development
config = RedisConfig().set_redis_host("localhost")

# Explicit IP address
config = RedisConfig().set_redis_host("127.0.0.1")

# Remote server
config = RedisConfig().set_redis_host("redis.example.com")

# Docker container
config = RedisConfig().set_redis_host("redis")  # Docker service name

# Private network
config = RedisConfig().set_redis_host("10.0.1.50")
```

---

#### `set_redis_port()`

Set the Redis server port number.

```python
def set_redis_port(self, port: int) -> "RedisConfig":
    ...
```

##### Parameters

| Parameter | Type  | Required | Description                                 |
|-----------|-------|----------|---------------------------------------------|
| `port`    | `int` | Yes      | Port number on which Redis is listening     |

##### Returns

`RedisConfig` - Self for method chaining.

##### Description

Sets the port number for connecting to Redis. The default Redis port is `6379`, but this can be customized for different environments or security purposes.

##### Examples

```python
# Standard Redis port
config = RedisConfig().set_redis_port(6379)

# Custom port for security
config = RedisConfig().set_redis_port(6380)

# Docker mapped port
config = RedisConfig().set_redis_port(6380)

# Complete configuration
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379)
```

---

#### `set_redis_db()`

Set the Redis database number to use.

```python
def set_redis_db(self, database: str) -> "RedisConfig":
    ...
```

##### Parameters

| Parameter  | Type  | Required | Description                                      |
|------------|-------|----------|--------------------------------------------------|
| `database` | `str` | Yes      | Database number as a string (typically 0-15)     |

##### Returns

`RedisConfig` - Self for method chaining.

##### Description

Redis supports multiple logical databases on a single server, numbered from 0 to 15 by default. This method sets which database to use. Database 0 is the default in most configurations.

**Important**: The database parameter is passed as a string, not an integer.

##### Examples

```python
# Default database
config = RedisConfig().set_redis_db("0")

# Different database for testing
config = RedisConfig().set_redis_db("1")

# Separate database for caching
config = RedisConfig().set_redis_db("2")

# Complete configuration
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")
```

**Note**: In Redis Cluster mode, only database 0 is available. Multiple databases are only supported in standalone Redis mode.

---

### Authentication Methods

#### `set_redis_password()`

Set the Redis authentication password.

```python
def set_redis_password(self, password: str) -> "RedisConfig":
    ...
```

##### Parameters

| Parameter  | Type  | Required | Description                           |
|------------|-------|----------|---------------------------------------|
| `password` | `str` | Yes      | Password for Redis authentication     |

##### Returns

`RedisConfig` - Self for method chaining.

##### Description

Sets the password for Redis authentication. This is used for:
- Simple password authentication (Redis < 6.0)
- ACL authentication with username (Redis 6.0+)

The password will be automatically URL-encoded when constructing connection URLs, ensuring special characters are properly escaped.

##### Examples

```python
# Basic password authentication
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0") \
    .set_redis_password("mySecretPassword")

# Password with special characters (automatically encoded)
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_password("p@ssw0rd!#$")

# Environment variable for security
import os
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_password(os.getenv("REDIS_PASSWORD"))
```

**Security Best Practice**: Never hardcode passwords. Use environment variables or secret management systems.

---

#### `set_redis_username()`

Set the Redis authentication username.

```python
def set_redis_username(self, username: str) -> "RedisConfig":
    ...
```

##### Parameters

| Parameter  | Type  | Required | Description                                 |
|------------|-------|----------|---------------------------------------------|
| `username` | `str` | Yes      | Username for Redis ACL authentication       |

##### Returns

`RedisConfig` - Self for method chaining.

##### Description

Sets the username for Redis ACL (Access Control List) authentication introduced in Redis 6.0. This allows for fine-grained access control with multiple users having different permissions.

For Redis versions before 6.0, only use `set_redis_password()` without a username.

##### Examples

```python
# Redis 6+ ACL authentication
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0") \
    .set_redis_username("admin") \
    .set_redis_password("adminPassword")

# Different users for different access levels
readonly_config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_username("readonly") \
    .set_redis_password("readonlyPass")

# From environment variables
import os
config = RedisConfig() \
    .set_redis_host(os.getenv("REDIS_HOST")) \
    .set_redis_port(int(os.getenv("REDIS_PORT", "6379"))) \
    .set_redis_username(os.getenv("REDIS_USERNAME")) \
    .set_redis_password(os.getenv("REDIS_PASSWORD"))
```

**Note**: Requires Redis 6.0 or higher. Check your Redis version with `redis-cli --version` or `INFO server` command.

---

### Security Configuration

#### `set_redis_ssl()`

Enable or disable SSL/TLS for Redis connections.

```python
def set_redis_ssl(self, ssl: bool) -> "RedisConfig":
    ...
```

##### Parameters

| Parameter | Type   | Required | Description                                |
|-----------|--------|----------|--------------------------------------------|
| `ssl`     | `bool` | Yes      | `True` to enable SSL/TLS, `False` to disable |

##### Returns

`RedisConfig` - Self for method chaining.

##### Description

Enables or disables SSL/TLS encryption for Redis connections. When enabled, the connection URL will use the `rediss://` protocol instead of `redis://`. SSL/TLS is essential for secure communication over untrusted networks.

**Important**: Your Redis server must be configured to accept SSL/TLS connections for this to work.

##### Examples

```python
# Enable SSL for production
config = RedisConfig() \
    .set_redis_host("redis.production.com") \
    .set_redis_port(6380) \
    .set_redis_ssl(True) \
    .set_redis_password(os.getenv("REDIS_PASSWORD"))

# Disable SSL for local development
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_ssl(False)

# Cloud Redis providers typically require SSL
config = RedisConfig() \
    .set_redis_host("redis-12345.cloud.redislabs.com") \
    .set_redis_port(12345) \
    .set_redis_ssl(True) \
    .set_redis_username("default") \
    .set_redis_password(os.getenv("REDIS_CLOUD_PASSWORD"))
```

---

### Connection Pool Configuration

#### `set_redis_max_connections()`

Set the maximum number of connections in the pool.

```python
def set_redis_max_connections(self, redis_max_connections: int) -> "RedisConfig":
    ...
```

##### Parameters

| Parameter               | Type  | Required | Description                                    |
|-------------------------|-------|----------|------------------------------------------------|
| `redis_max_connections` | `int` | Yes      | Maximum number of concurrent connections       |

##### Returns

`RedisConfig` - Self for method chaining.

##### Description

Sets the maximum number of connections allowed in the Redis connection pool. The connection pool reuses connections across multiple operations, improving performance and resource utilization.

**Considerations**:
- Higher values allow more concurrent operations
- Too many connections can exhaust server resources
- Default is typically 10 connections
- Adjust based on your application's concurrency needs

##### Examples

```python
# Low-traffic application
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_max_connections(5)

# High-traffic API server
config = RedisConfig() \
    .set_redis_host("redis.example.com") \
    .set_redis_port(6379) \
    .set_redis_max_connections(50)

# Celery worker pool (adjust based on worker count)
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_max_connections(20)

# Microservice with many async operations
config = RedisConfig() \
    .set_redis_host("redis") \
    .set_redis_port(6379) \
    .set_redis_max_connections(100)
```

**Recommended Values**:
- Development: 5-10 connections
- Small applications: 10-20 connections
- Medium applications: 20-50 connections
- High-traffic applications: 50-200 connections

---

#### `set_redis_socket_timeout()`

Set the socket timeout in seconds for Redis operations.

```python
def set_redis_socket_timeout(self, redis_socket_timeout: int) -> "RedisConfig":
    ...
```

##### Parameters

| Parameter              | Type  | Required | Description                              |
|------------------------|-------|----------|------------------------------------------|
| `redis_socket_timeout` | `int` | Yes      | Timeout in seconds for socket operations |

##### Returns

`RedisConfig` - Self for method chaining.

##### Description

Sets the timeout for socket operations when communicating with Redis. Operations that exceed this time will raise a timeout error. This prevents indefinite blocking when Redis is unresponsive.

**Considerations**:
- Lower values fail faster but may cause issues with slow networks
- Higher values are more tolerant but may hang longer on issues
- Default is typically 5 seconds
- Adjust based on network latency and operation complexity

##### Examples

```python
# Fast local network (aggressive timeout)
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_socket_timeout(2)

# Standard configuration
config = RedisConfig() \
    .set_redis_host("redis.example.com") \
    .set_redis_port(6379) \
    .set_redis_socket_timeout(5)

# Slow network or complex operations
config = RedisConfig() \
    .set_redis_host("redis.remote.com") \
    .set_redis_port(6379) \
    .set_redis_socket_timeout(10)

# Cloud provider with variable latency
config = RedisConfig() \
    .set_redis_host("redis-cloud.provider.com") \
    .set_redis_port(6379) \
    .set_redis_socket_timeout(15)
```

**Recommended Values**:
- Local network: 2-3 seconds
- Same datacenter: 5 seconds (default)
- Cross-datacenter: 10-15 seconds
- International connections: 15-30 seconds

---

### Retrieval Method

#### `get()`

Retrieve a configuration value by key.

```python
def get(self, key: str, default: Any = None) -> Any:
    ...
```

##### Parameters

| Parameter | Type  | Required | Default | Description                                        |
|-----------|-------|----------|---------|----------------------------------------------------|
| `key`     | `str` | Yes      | -       | Configuration parameter name to retrieve           |
| `default` | `Any` | No       | `None`  | Default value if the key is not found              |

##### Returns

`Any` - The configuration value if it exists, otherwise the default value.

##### Description

Retrieves a configuration value by its key name. If the key doesn't exist in the configuration, returns the provided default value. This method is typically used internally by `RedisInstance` to build connection parameters.

##### Configuration Keys

Available configuration keys:
- `"redis_url"` - Full Redis connection URL
- `"redis_host"` - Redis server hostname
- `"redis_port"` - Redis server port number
- `"redis_db"` - Redis database number
- `"redis_password"` - Authentication password
- `"redis_username"` - Authentication username
- `"redis_ssl"` - SSL/TLS enabled flag
- `"redis_max_connections"` - Maximum connections in pool
- `"redis_socket_timeout"` - Socket timeout in seconds

##### Examples

```python
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

# Retrieve set values
host = config.get("redis_host")  # Returns "localhost"
port = config.get("redis_port")  # Returns 6379
db = config.get("redis_db")      # Returns "0"

# Retrieve unset values with defaults
password = config.get("redis_password", "")  # Returns ""
max_conn = config.get("redis_max_connections", 10)  # Returns 10
timeout = config.get("redis_socket_timeout", 5)  # Returns 5

# Check if SSL is enabled
ssl_enabled = config.get("redis_ssl", False)  # Returns False
```

---

## Complete Configuration Examples

### Example 1: Basic Local Development

```python
from dtpyfw.redis.config import RedisConfig

# Minimal local configuration
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

# Use with RedisInstance
from dtpyfw.redis.connection import RedisInstance
redis = RedisInstance(config)
```

### Example 2: Production with Authentication

```python
import os
from dtpyfw.redis.config import RedisConfig

# Production configuration with environment variables
config = RedisConfig() \
    .set_redis_host(os.getenv("REDIS_HOST", "redis.production.com")) \
    .set_redis_port(int(os.getenv("REDIS_PORT", "6379"))) \
    .set_redis_db(os.getenv("REDIS_DB", "0")) \
    .set_redis_password(os.getenv("REDIS_PASSWORD")) \
    .set_redis_max_connections(50) \
    .set_redis_socket_timeout(5)
```

### Example 3: Secure Cloud Redis

```python
import os
from dtpyfw.redis.config import RedisConfig

# Redis Cloud or AWS ElastiCache with SSL
config = RedisConfig() \
    .set_redis_host(os.getenv("REDIS_HOST")) \
    .set_redis_port(int(os.getenv("REDIS_PORT", "6380"))) \
    .set_redis_db("0") \
    .set_redis_username(os.getenv("REDIS_USERNAME", "default")) \
    .set_redis_password(os.getenv("REDIS_PASSWORD")) \
    .set_redis_ssl(True) \
    .set_redis_max_connections(30) \
    .set_redis_socket_timeout(10)
```

### Example 4: Using Complete URL

```python
import os
from dtpyfw.redis.config import RedisConfig

# Single URL configuration (simplest approach)
redis_url = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

config = RedisConfig() \
    .set_redis_url(redis_url) \
    .set_redis_max_connections(20) \
    .set_redis_socket_timeout(5)
```

### Example 5: Multiple Environments

```python
import os
from dtpyfw.redis.config import RedisConfig

def get_redis_config() -> RedisConfig:
    """Get Redis configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return RedisConfig() \
            .set_redis_host(os.getenv("REDIS_HOST")) \
            .set_redis_port(int(os.getenv("REDIS_PORT", "6379"))) \
            .set_redis_db("0") \
            .set_redis_password(os.getenv("REDIS_PASSWORD")) \
            .set_redis_ssl(True) \
            .set_redis_max_connections(100) \
            .set_redis_socket_timeout(10)
    
    elif env == "staging":
        return RedisConfig() \
            .set_redis_host(os.getenv("REDIS_HOST", "redis-staging")) \
            .set_redis_port(6379) \
            .set_redis_db("0") \
            .set_redis_password(os.getenv("REDIS_PASSWORD")) \
            .set_redis_max_connections(50) \
            .set_redis_socket_timeout(5)
    
    else:  # development
        return RedisConfig() \
            .set_redis_host("localhost") \
            .set_redis_port(6379) \
            .set_redis_db("0") \
            .set_redis_max_connections(10) \
            .set_redis_socket_timeout(3)

# Usage
config = get_redis_config()
```

### Example 6: Docker Compose Setup

```python
from dtpyfw.redis.config import RedisConfig

# Docker service name as host
config = RedisConfig() \
    .set_redis_host("redis")  # Service name from docker-compose.yml
    .set_redis_port(6379) \
    .set_redis_db("0") \
    .set_redis_max_connections(20)

# Corresponding docker-compose.yml:
# services:
#   redis:
#     image: redis:7-alpine
#     ports:
#       - "6379:6379"
#   app:
#     build: .
#     depends_on:
#       - redis
```

### Example 7: Testing Configuration

```python
from dtpyfw.redis.config import RedisConfig
import pytest

@pytest.fixture
def redis_config():
    """Redis configuration for testing."""
    return RedisConfig() \
        .set_redis_host("localhost") \
        .set_redis_port(6379) \
        .set_redis_db("15")  # Use separate DB for tests
        .set_redis_max_connections(5) \
        .set_redis_socket_timeout(2)

def test_with_redis(redis_config):
    from dtpyfw.redis.connection import RedisInstance
    redis = RedisInstance(redis_config)
    
    with redis.get_redis() as client:
        client.set("test_key", "test_value")
        assert client.get("test_key") == b"test_value"
        client.delete("test_key")
```

---

## Best Practices

### 1. Use Environment Variables for Credentials

```python
import os

# Good: Credentials from environment
config = RedisConfig() \
    .set_redis_host(os.getenv("REDIS_HOST")) \
    .set_redis_password(os.getenv("REDIS_PASSWORD"))

# Bad: Hardcoded credentials
config = RedisConfig() \
    .set_redis_host("redis.example.com") \
    .set_redis_password("hardcoded_password")  # Never do this!
```

### 2. Use SSL in Production

```python
# Production should always use SSL
production_config = RedisConfig() \
    .set_redis_host(os.getenv("REDIS_HOST")) \
    .set_redis_port(6380) \
    .set_redis_ssl(True) \
    .set_redis_password(os.getenv("REDIS_PASSWORD"))

# Development can skip SSL for simplicity
dev_config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_ssl(False)
```

### 3. Adjust Connection Pool Size Based on Load

```python
# Low-traffic service
low_traffic = RedisConfig() \
    .set_redis_host("redis") \
    .set_redis_max_connections(10)

# High-traffic API
high_traffic = RedisConfig() \
    .set_redis_host("redis") \
    .set_redis_max_connections(100)

# Rule of thumb: max_connections >= expected concurrent requests
```

### 4. Use Separate Databases for Different Purposes

```python
# Cache database
cache_config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

# Session database
session_config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("1")

# Test database
test_config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("15")  # Use highest DB for tests
```

### 5. Create Configuration Factories

```python
from typing import Literal
import os

def create_redis_config(
    purpose: Literal["cache", "session", "queue"] = "cache"
) -> RedisConfig:
    """Create Redis configuration for different purposes."""
    
    base_config = RedisConfig() \
        .set_redis_host(os.getenv("REDIS_HOST", "localhost")) \
        .set_redis_port(int(os.getenv("REDIS_PORT", "6379")))
    
    if purpose == "cache":
        return base_config \
            .set_redis_db("0") \
            .set_redis_max_connections(50) \
            .set_redis_socket_timeout(5)
    
    elif purpose == "session":
        return base_config \
            .set_redis_db("1") \
            .set_redis_max_connections(30) \
            .set_redis_socket_timeout(10)  # Longer timeout
    
    elif purpose == "queue":
        return base_config \
            .set_redis_db("2") \
            .set_redis_max_connections(100) \
            .set_redis_socket_timeout(30)  # Very long timeout
    
    return base_config

# Usage
cache_config = create_redis_config("cache")
session_config = create_redis_config("session")
queue_config = create_redis_config("queue")
```

### 6. Validate Configuration

```python
def validate_redis_config(config: RedisConfig) -> bool:
    """Validate that required configuration is present."""
    
    # Check for either URL or host+port
    has_url = config.get("redis_url") is not None
    has_host_port = (
        config.get("redis_host") is not None and
        config.get("redis_port") is not None
    )
    
    if not (has_url or has_host_port):
        raise ValueError("Must provide either redis_url or redis_host+redis_port")
    
    # Validate database is set
    if config.get("redis_db") is None:
        raise ValueError("Must provide redis_db")
    
    # Warn about SSL in production
    if os.getenv("ENVIRONMENT") == "production":
        if not config.get("redis_ssl", False):
            import warnings
            warnings.warn("SSL not enabled in production environment")
    
    return True

# Usage
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

validate_redis_config(config)  # Raises if invalid
```

---

## Configuration Patterns

### Pattern 1: 12-Factor App Configuration

```python
import os
from dtpyfw.redis.config import RedisConfig

# All configuration from environment variables
config = RedisConfig() \
    .set_redis_url(os.environ["REDIS_URL"])  # Required
    .set_redis_max_connections(
        int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
    ) \
    .set_redis_socket_timeout(
        int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
    )
```

### Pattern 2: Configuration Class

```python
from dataclasses import dataclass
from dtpyfw.redis.config import RedisConfig
import os

@dataclass
class Settings:
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: str = "0"
    redis_password: str = ""
    redis_ssl: bool = False
    redis_max_connections: int = 10
    redis_socket_timeout: int = 5
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=os.getenv("REDIS_DB", "0"),
            redis_password=os.getenv("REDIS_PASSWORD", ""),
            redis_ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
            redis_max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
            redis_socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
        )
    
    def to_redis_config(self) -> RedisConfig:
        """Convert to RedisConfig."""
        config = RedisConfig() \
            .set_redis_host(self.redis_host) \
            .set_redis_port(self.redis_port) \
            .set_redis_db(self.redis_db) \
            .set_redis_max_connections(self.redis_max_connections) \
            .set_redis_socket_timeout(self.redis_socket_timeout)
        
        if self.redis_password:
            config.set_redis_password(self.redis_password)
        
        if self.redis_ssl:
            config.set_redis_ssl(True)
        
        return config

# Usage
settings = Settings.from_env()
redis_config = settings.to_redis_config()
```

### Pattern 3: Pydantic Settings (Modern Approach)

```python
from pydantic_settings import BaseSettings
from pydantic import Field
from dtpyfw.redis.config import RedisConfig

class RedisSettings(BaseSettings):
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: str = Field(default="0", env="REDIS_DB")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    redis_ssl: bool = Field(default=False, env="REDIS_SSL")
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def to_redis_config(self) -> RedisConfig:
        """Convert to RedisConfig."""
        config = RedisConfig() \
            .set_redis_host(self.redis_host) \
            .set_redis_port(self.redis_port) \
            .set_redis_db(self.redis_db) \
            .set_redis_max_connections(self.redis_max_connections) \
            .set_redis_socket_timeout(self.redis_socket_timeout) \
            .set_redis_ssl(self.redis_ssl)
        
        if self.redis_password:
            config.set_redis_password(self.redis_password)
        
        return config

# Usage
settings = RedisSettings()  # Automatically loads from .env
redis_config = settings.to_redis_config()
```

---

## Related Documentation

- [dtpyfw.redis.connection](connection.md) - Redis connection management using RedisConfig
- [dtpyfw.redis.caching](caching.md) - Redis caching utilities
- [dtpyfw.redis.health](health.md) - Redis health checks

---

## External References

- [Redis Connection Handling](https://redis.io/docs/manual/client-side-caching/)
- [redis-py Connection Pools](https://redis-py.readthedocs.io/en/stable/connections.html)
- [Redis Security Best Practices](https://redis.io/docs/management/security/)
- [Redis ACL Documentation](https://redis.io/docs/manual/security/acl/) (Redis 6+)
- [12-Factor App Configuration](https://12factor.net/config)
