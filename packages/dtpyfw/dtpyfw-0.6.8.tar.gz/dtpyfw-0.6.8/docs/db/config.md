# Database Configuration (`dtpyfw.db.config`)

## Overview

The `config` module provides the `DatabaseConfig` class, a fluent builder for constructing database connection configurations. It offers a clean, chainable API for setting up database connections with support for read/write splitting, connection pooling, SSL/TLS, and multiple database backends.

## Module Location

```python
from dtpyfw.db.config import DatabaseConfig
```

## Classes

### `DatabaseConfig`

A configuration builder class that uses the builder pattern to construct database connection settings. All setter methods return `self` to enable method chaining.

#### Constructor

```python
DatabaseConfig()
```

Creates a new `DatabaseConfig` instance with default settings:

- `db_backend`: `"postgresql"`
- `db_driver_async`: `"asyncpg"`
- `connect_args`: `None`

**Example:**

```python
config = DatabaseConfig()
```

## Configuration Methods

All configuration methods follow the pattern `set_<parameter_name>(value)` and return `self` for chaining.

### Backend and Driver Configuration

#### `set_db_backend(db_backend: str) -> DatabaseConfig`

Set the database backend type.

**Parameters:**
- `db_backend` (str): Database backend identifier (e.g., `"postgresql"`, `"mysql"`, `"sqlite"`)

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_backend("postgresql")
config.set_db_backend("mysql")
```

#### `set_db_driver_sync(db_driver_sync: str) -> DatabaseConfig`

Set the synchronous database driver.

**Parameters:**
- `db_driver_sync` (str): Synchronous driver name (e.g., `"psycopg2"`, `"pymysql"`)

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_driver_sync("psycopg2")
config.set_db_driver_sync("pymysql")
```

#### `set_db_driver_async(db_driver_async: str) -> DatabaseConfig`

Set the asynchronous database driver.

**Parameters:**
- `db_driver_async` (str): Asynchronous driver name (e.g., `"asyncpg"`, `"aiomysql"`)

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_driver_async("asyncpg")
config.set_db_driver_async("aiomysql")
```

### Connection Parameters

#### `set_connect_args(connect_args: dict) -> DatabaseConfig`

Set extra connection arguments for the database driver.

**Parameters:**
- `connect_args` (dict): Dictionary of driver-specific connection arguments

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
# PostgreSQL-specific settings
config.set_connect_args({
    "connect_timeout": 10,
    "keepalives": 1,
    "keepalives_idle": 30
})

# MySQL-specific settings
config.set_connect_args({
    "charset": "utf8mb4",
    "connect_timeout": 10
})
```

### URL Configuration

#### `set_db_url(db_url: str) -> DatabaseConfig`

Set a complete database URL for both read and write operations.

**Parameters:**
- `db_url` (str): Complete database connection URL string

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_url("postgresql://user:password@localhost:5432/mydb")
config.set_db_url("mysql+pymysql://user:password@localhost:3306/mydb")
```

**Note:** When using `set_db_url()`, individual connection parameters (user, password, host, etc.) are not required.

#### `set_db_url_read(db_url_read: str) -> DatabaseConfig`

Set a separate database URL for read-only operations (read replica).

**Parameters:**
- `db_url_read` (str): Database URL for read-only operations

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_url("postgresql://user:pwd@primary:5432/db")
config.set_db_url_read("postgresql://user:pwd@replica:5432/db")
```

**Use Case:** Set this when you have read replicas to distribute read load.

### Authentication

#### `set_db_user(db_user: str) -> DatabaseConfig`

Set the database username for authentication.

**Parameters:**
- `db_user` (str): Database username

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_user("myappuser")
```

#### `set_db_password(db_password: str) -> DatabaseConfig`

Set the database password for authentication.

**Parameters:**
- `db_password` (str): Database password

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_password("secure_password_123")
```

**Security Note:** Never hardcode passwords. Use environment variables:

```python
import os
config.set_db_password(os.getenv("DB_PASSWORD"))
```

### Host and Port

#### `set_db_host(db_host: str) -> DatabaseConfig`

Set the database host for write operations.

**Parameters:**
- `db_host` (str): Hostname or IP address of the database server

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_host("localhost")
config.set_db_host("db.example.com")
config.set_db_host("10.0.1.50")
```

#### `set_db_host_read(db_host_read: str) -> DatabaseConfig`

Set a separate database host for read-only operations (read replica).

**Parameters:**
- `db_host_read` (str): Hostname or IP address for read replicas

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_host("primary.db.example.com")
config.set_db_host_read("replica.db.example.com")
```

**Use Case:** Configure read replicas to offload read traffic from the primary database.

#### `set_db_port(db_port: int) -> DatabaseConfig`

Set the database port number.

**Parameters:**
- `db_port` (int): Port number for database connections

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_port(5432)  # PostgreSQL default
config.set_db_port(3306)  # MySQL default
```

### Database Name

#### `set_db_name(db_name: str) -> DatabaseConfig`

Set the name of the database to connect to.

**Parameters:**
- `db_name` (str): Database name

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_name("production_db")
config.set_db_name("test_db")
```

### Security

#### `set_db_ssl(db_ssl: bool) -> DatabaseConfig`

Enable or disable SSL/TLS for the database connection.

**Parameters:**
- `db_ssl` (bool): `True` to enable SSL/TLS, `False` to disable

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_ssl(True)   # Enable SSL
config.set_db_ssl(False)  # Disable SSL
```

**Note:** When enabled, the appropriate SSL parameters are automatically added to the connection URL based on the database backend.

### Connection Pooling

#### `set_db_pool_size(db_pool_size: int) -> DatabaseConfig`

Set the database connection pool size.

**Parameters:**
- `db_pool_size` (int): Maximum number of connections to maintain in the pool

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_pool_size(20)  # Maintain 20 connections
```

**Guidance:**
- Low traffic: 5-10 connections
- Medium traffic: 20-30 connections
- High traffic: 50-100 connections

#### `set_db_max_overflow(db_max_overflow: int) -> DatabaseConfig`

Set the database connection pool overflow limit.

**Parameters:**
- `db_max_overflow` (int): Maximum number of connections beyond `pool_size` that can be temporarily created

**Returns:**
- `DatabaseConfig`: Self for method chaining

**Example:**

```python
config.set_db_pool_size(20)
config.set_db_max_overflow(10)  # Allow up to 30 total connections (20 + 10)
```

**Use Case:** Handles traffic spikes without exhausting available connections.

### Retrieving Configuration

#### `get(key: str, default: Any = None) -> Any`

Retrieve a configuration value by key.

**Parameters:**
- `key` (str): The configuration key to retrieve
- `default` (Any, optional): Default value if key is not found. Default: `None`

**Returns:**
- `Any`: The configuration value, or default if not found

**Example:**

```python
db_host = config.get("db_host")
pool_size = config.get("db_pool_size", 10)
```

## Complete Usage Examples

### Basic Configuration

```python
from dtpyfw.db.config import DatabaseConfig

config = (
    DatabaseConfig()
    .set_db_backend("postgresql")
    .set_db_driver_async("asyncpg")
    .set_db_user("myuser")
    .set_db_password("mypassword")
    .set_db_host("localhost")
    .set_db_port(5432)
    .set_db_name("mydatabase")
)
```

### Configuration with Connection Pooling

```python
config = (
    DatabaseConfig()
    .set_db_backend("postgresql")
    .set_db_user("myuser")
    .set_db_password("mypassword")
    .set_db_host("localhost")
    .set_db_port(5432)
    .set_db_name("mydatabase")
    .set_db_pool_size(20)
    .set_db_max_overflow(10)
)
```

### Configuration with Read Replica

```python
config = (
    DatabaseConfig()
    .set_db_backend("postgresql")
    .set_db_driver_async("asyncpg")
    .set_db_user("appuser")
    .set_db_password("secure_pass")
    .set_db_host("primary.db.internal")
    .set_db_host_read("replica.db.internal")
    .set_db_port(5432)
    .set_db_name("production")
    .set_db_ssl(True)
    .set_db_pool_size(30)
    .set_db_max_overflow(15)
)
```

### Configuration with Full URL

```python
config = (
    DatabaseConfig()
    .set_db_url("postgresql+asyncpg://user:pass@host:5432/dbname?ssl=require")
)

# With separate read replica URL
config = (
    DatabaseConfig()
    .set_db_url("postgresql://user:pass@primary:5432/db")
    .set_db_url_read("postgresql://user:pass@replica:5432/db")
)
```

### Configuration from Environment Variables

```python
import os

config = (
    DatabaseConfig()
    .set_db_backend(os.getenv("DB_BACKEND", "postgresql"))
    .set_db_user(os.getenv("DB_USER"))
    .set_db_password(os.getenv("DB_PASSWORD"))
    .set_db_host(os.getenv("DB_HOST", "localhost"))
    .set_db_port(int(os.getenv("DB_PORT", "5432")))
    .set_db_name(os.getenv("DB_NAME"))
    .set_db_ssl(os.getenv("DB_SSL", "false").lower() == "true")
    .set_db_pool_size(int(os.getenv("DB_POOL_SIZE", "20")))
)
```

### MySQL Configuration

```python
config = (
    DatabaseConfig()
    .set_db_backend("mysql")
    .set_db_driver_sync("pymysql")
    .set_db_driver_async("aiomysql")
    .set_db_user("mysql_user")
    .set_db_password("mysql_pass")
    .set_db_host("mysql.internal")
    .set_db_port(3306)
    .set_db_name("application_db")
    .set_db_ssl(True)
    .set_connect_args({
        "charset": "utf8mb4",
        "connect_timeout": 10
    })
)
```

### PostgreSQL with Custom Connection Args

```python
config = (
    DatabaseConfig()
    .set_db_backend("postgresql")
    .set_db_driver_async("asyncpg")
    .set_db_user("pguser")
    .set_db_password("pgpass")
    .set_db_host("pg.internal")
    .set_db_port(5432)
    .set_db_name("myapp")
    .set_connect_args({
        "command_timeout": 60,
        "server_settings": {
            "jit": "off",
            "application_name": "my_application"
        }
    })
)
```

## Configuration Patterns

### Development vs Production

```python
import os

def get_config():
    env = os.getenv("ENVIRONMENT", "development")
    
    config = DatabaseConfig()
    
    if env == "production":
        config = (
            config
            .set_db_host(os.getenv("DB_HOST_PRIMARY"))
            .set_db_host_read(os.getenv("DB_HOST_REPLICA"))
            .set_db_ssl(True)
            .set_db_pool_size(50)
            .set_db_max_overflow(20)
        )
    else:
        config = (
            config
            .set_db_host("localhost")
            .set_db_ssl(False)
            .set_db_pool_size(5)
        )
    
    return (
        config
        .set_db_backend("postgresql")
        .set_db_user(os.getenv("DB_USER"))
        .set_db_password(os.getenv("DB_PASSWORD"))
        .set_db_name(os.getenv("DB_NAME"))
        .set_db_port(int(os.getenv("DB_PORT", "5432")))
    )
```

### Multiple Database Configurations

```python
# Primary application database
app_config = (
    DatabaseConfig()
    .set_db_backend("postgresql")
    .set_db_user("app_user")
    .set_db_password("app_pass")
    .set_db_host("app-db.internal")
    .set_db_name("application")
    .set_db_port(5432)
)

# Analytics database
analytics_config = (
    DatabaseConfig()
    .set_db_backend("postgresql")
    .set_db_user("analytics_user")
    .set_db_password("analytics_pass")
    .set_db_host("analytics-db.internal")
    .set_db_name("analytics")
    .set_db_port(5432)
)
```

## Best Practices

1. **Use environment variables** for sensitive information like passwords:
   ```python
   config.set_db_password(os.getenv("DB_PASSWORD"))
   ```

2. **Enable SSL in production** for secure connections:
   ```python
   config.set_db_ssl(True)
   ```

3. **Configure read replicas** to distribute read load:
   ```python
   config.set_db_host("primary").set_db_host_read("replica")
   ```

4. **Set appropriate pool sizes** based on your application's concurrency:
   ```python
   config.set_db_pool_size(20).set_db_max_overflow(10)
   ```

5. **Use method chaining** for cleaner configuration:
   ```python
   config = (
       DatabaseConfig()
       .set_db_backend("postgresql")
       .set_db_user(user)
       .set_db_password(password)
   )
   ```

6. **Keep configuration separate** from business logic using factory functions

## Related Documentation

- [database.md](./database.md) - Using DatabaseConfig with DatabaseInstance
- [SQLAlchemy Engine Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html)

## Notes

- When `db_url` is set, it takes precedence over individual connection parameters
- If `db_host_read` or `db_url_read` is not set, read operations will use the write connection
- Connection pooling is disabled if `db_pool_size` is not set (uses NullPool)
- The builder pattern allows for flexible, readable configuration without complex constructors
