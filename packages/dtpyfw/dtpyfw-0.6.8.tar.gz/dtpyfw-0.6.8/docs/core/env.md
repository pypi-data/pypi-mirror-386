# Environment Variable Utilities

## Overview

The `dtpyfw.core.env` module provides a lightweight wrapper around Python's `os.environ` with allow-list support. This module enables controlled access to environment variables, preventing unauthorized reading of sensitive configuration and supporting `.env` file loading with security controls.

## Module Path

```python
from dtpyfw.core.env import Env
```

## Class: `Env`

A static utility class for managing environment variables with security controls.

### Class Methods

#### `register(variables: List[str] | Set[str]) -> None`

Register environment variable names that are allowed to be loaded.

**Description:**

Adds variable names to the internal allow-list. Only registered variables can be loaded from files via `load_file()`. Variable names are automatically converted to uppercase.

**Parameters:**

- **variables** (`List[str] | Set[str]`): A list or set of environment variable names to register.

**Returns:**

- `None`

**Example:**

```python
from dtpyfw.core.env import Env

# Register allowed environment variables
Env.register(["database_url", "api_key", "debug"])

# Variables are stored as uppercase
# Now DATABASE_URL, API_KEY, and DEBUG are allowed
```

---

#### `load_file(file_path: str, override: bool = False, fail_on_missing: bool = False) -> None`

Load key/value pairs from a `.env` style file.

**Description:**

Reads environment variables from a file and loads them into `os.environ`. Only variables that have been registered via `register()` are loaded. Lines without '=' are ignored. Provides control over whether to override existing variables and how to handle missing files.

**Parameters:**

- **file_path** (`str`): Path to the file containing environment variables.
- **override** (`bool`, optional): When True, existing environment variables will be overwritten. Defaults to False.
- **fail_on_missing** (`bool`, optional): If True, raises FileNotFoundError when the file is missing. Defaults to False.

**Returns:**

- `None`

**Raises:**

- **FileNotFoundError**: If `fail_on_missing` is True and the file doesn't exist.

**Example:**

```python
from dtpyfw.core.env import Env

# Register variables first
Env.register(["DATABASE_URL", "API_KEY", "SECRET_KEY"])

# Load from .env file
Env.load_file(".env")

# Load with override (replaces existing values)
Env.load_file(".env.production", override=True)

# Fail if file doesn't exist
try:
    Env.load_file("required.env", fail_on_missing=True)
except FileNotFoundError:
    print("Required environment file not found!")
```

---

#### `get(key: str, default: Any = None) -> Any`

Retrieve a variable from `os.environ` with optional default.

**Description:**

Gets an environment variable value. The key is automatically converted to uppercase. Returns the default if the variable is not set. Results are cached using `@lru_cache` for performance.

**Parameters:**

- **key** (`str`): The environment variable name to retrieve.
- **default** (`Any`, optional): Value to return if the variable is not set. Defaults to None.

**Returns:**

- **`Any`**: The value of the environment variable, or the default value if not found.

**Example:**

```python
from dtpyfw.core.env import Env

# Get environment variable with default
db_url = Env.get("DATABASE_URL", "sqlite:///default.db")

# Get without default (returns None if not set)
api_key = Env.get("API_KEY")

# Keys are automatically uppercased
debug = Env.get("debug", "false")  # Looks for DEBUG
```

## Complete Usage Example

### Basic Setup

```python
from dtpyfw.core.env import Env

# Step 1: Register allowed variables
Env.register([
    "DATABASE_URL",
    "REDIS_HOST",
    "REDIS_PORT",
    "API_KEY",
    "SECRET_KEY",
    "DEBUG",
    "LOG_LEVEL"
])

# Step 2: Load from .env file
Env.load_file(".env")

# Step 3: Access variables
database_url = Env.get("DATABASE_URL", "postgresql://localhost/mydb")
redis_host = Env.get("REDIS_HOST", "localhost")
redis_port = Env.get("REDIS_PORT", "6379")
debug = Env.get("DEBUG", "false").lower() == "true"
```

### .env File Format

```env
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb

# Redis Configuration
REDIS_HOST=redis.example.com
REDIS_PORT=6379

# API Keys
API_KEY=your-api-key-here
SECRET_KEY=your-secret-key-here

# Application Settings
DEBUG=true
LOG_LEVEL=info
```

### Application Configuration

```python
from dtpyfw.core.env import Env
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    def __init__(self):
        # Register and load environment variables
        Env.register([
            "DATABASE_URL",
            "REDIS_HOST",
            "REDIS_PORT",
            "SECRET_KEY",
            "DEBUG"
        ])
        Env.load_file(".env")
        
        # Load settings
        self.database_url = Env.get("DATABASE_URL")
        self.redis_host = Env.get("REDIS_HOST", "localhost")
        self.redis_port = int(Env.get("REDIS_PORT", "6379"))
        self.secret_key = Env.get("SECRET_KEY")
        self.debug = Env.get("DEBUG", "false").lower() == "true"

# Initialize settings
settings = Settings()
```

### Multiple Environment Files

```python
from dtpyfw.core.env import Env
import os

# Register variables
Env.register(["DATABASE_URL", "API_KEY", "DEBUG"])

# Load base configuration
Env.load_file(".env.base")

# Load environment-specific overrides
environment = os.getenv("APP_ENV", "development")
Env.load_file(f".env.{environment}", override=True)

# Load local overrides (not in version control)
Env.load_file(".env.local", override=True)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from dtpyfw.core.env import Env

# Configure environment
Env.register(["DATABASE_URL", "SECRET_KEY", "DEBUG"])
Env.load_file(".env")

app = FastAPI(
    debug=Env.get("DEBUG", "false").lower() == "true"
)

@app.on_event("startup")
async def startup():
    # Use environment variables
    database_url = Env.get("DATABASE_URL")
    # Initialize database connection
    pass
```

### Type Conversion Helpers

```python
from dtpyfw.core.env import Env

def get_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = Env.get(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")

def get_int(key: str, default: int = 0) -> int:
    """Get integer environment variable."""
    try:
        return int(Env.get(key, str(default)))
    except ValueError:
        return default

def get_list(key: str, separator: str = ",", default: list = None) -> list:
    """Get list from comma-separated environment variable."""
    value = Env.get(key)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(separator)]

# Usage
DEBUG = get_bool("DEBUG")
MAX_CONNECTIONS = get_int("MAX_CONNECTIONS", 100)
ALLOWED_HOSTS = get_list("ALLOWED_HOSTS", default=["localhost"])
```

## Security Features

### 1. Allow-List Protection

Only registered variables can be loaded from files, preventing accidental exposure of system environment variables:

```python
from dtpyfw.core.env import Env

# Only register what you need
Env.register(["API_KEY", "DATABASE_URL"])

# Even if .env contains other variables, only registered ones are loaded
Env.load_file(".env")
```

### 2. Warning on Unallowed Variables

When `load_file()` encounters an unregistered variable, it logs a warning via the footprint system:

```python
# If .env contains UNREGISTERED_VAR but it's not registered:
# Warning: Skipping unallowed environment variable UNREGISTERED_VAR.
```

### 3. Prevent Override by Default

Existing environment variables are not overwritten unless explicitly requested:

```python
import os
from dtpyfw.core.env import Env

# Set environment variable
os.environ["API_KEY"] = "production-key"

# This won't override the existing value
Env.load_file(".env")

# This WILL override
Env.load_file(".env", override=True)
```

## Performance Optimization

The `get()` method uses `@lru_cache(maxsize=128)` to cache results:

```python
# First call reads from os.environ
value1 = Env.get("DATABASE_URL")

# Second call returns cached value (faster)
value2 = Env.get("DATABASE_URL")
```

**Note:** If you modify environment variables at runtime, the cache may return stale values. Clear the cache if needed:

```python
import os
from dtpyfw.core.env import Env

# Clear the cache
Env.get.cache_clear()

# Now get() will read fresh values
```

## Best Practices

1. **Register variables early:**
   ```python
   # At application startup
   Env.register(["DATABASE_URL", "API_KEY", "SECRET_KEY"])
   ```

2. **Use consistent naming:**
   ```python
   # Good: Uppercase with underscores
   Env.register(["DATABASE_URL", "REDIS_HOST"])
   
   # Avoid: Mixed case
   # Env.register(["databaseUrl", "RedisHost"])
   ```

3. **Provide sensible defaults:**
   ```python
   # Always provide defaults for optional config
   debug = Env.get("DEBUG", "false")
   max_workers = Env.get("MAX_WORKERS", "4")
   ```

4. **Separate concerns:**
   ```python
   # .env.base - shared configuration
   # .env.development - dev overrides
   # .env.production - prod overrides
   # .env.local - local machine overrides (gitignored)
   ```

5. **Never commit secrets:**
   ```gitignore
   # .gitignore
   .env
   .env.local
   .env.*.local
   ```

6. **Document required variables:**
   ```python
   # Create .env.example
   """
   # Required Variables
   DATABASE_URL=postgresql://localhost/mydb
   API_KEY=your-api-key
   SECRET_KEY=your-secret-key
   
   # Optional Variables
   DEBUG=false
   LOG_LEVEL=info
   """
   ```

## Comparison with Alternatives

### vs `os.getenv()`

```python
# os.getenv - No protection
import os
value = os.getenv("ANY_VARIABLE")  # Can access any variable

# Env.get() - Protected
from dtpyfw.core.env import Env
Env.register(["ALLOWED_VAR"])
value = Env.get("ALLOWED_VAR")  # Only registered variables
```

### vs `python-dotenv`

```python
# python-dotenv - Loads all variables
from dotenv import load_dotenv
load_dotenv()  # Loads everything from .env

# Env - Selective loading
from dtpyfw.core.env import Env
Env.register(["SPECIFIC_VARS"])
Env.load_file(".env")  # Only loads registered variables
```

## Related Modules

- **dtpyfw.log.footprint** - Used for logging warnings about unallowed variables
- **dtpyfw.db.config** - Database configuration using environment variables
- **dtpyfw.redis.config** - Redis configuration using environment variables

## Dependencies

- `os` - Python's built-in os module
- `functools.lru_cache` - For caching
- `dtpyfw.log.footprint` - For logging

## See Also

- [12-Factor App: Config](https://12factor.net/config)
- [Python os.environ](https://docs.python.org/3/library/os.html#os.environ)
- [Environment Variables Best Practices](https://12factor.net/config)
