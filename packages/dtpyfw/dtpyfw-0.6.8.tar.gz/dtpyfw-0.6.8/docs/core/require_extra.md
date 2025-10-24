# Dependency Requirement Utilities

## Overview

The `dtpyfw.core.require_extra` module provides utilities to assert that optional dependencies are installed. This module enforces that extras specified in `pyproject.toml` are available before using features that depend on them, providing clear error messages with installation instructions.

## Module Path

```python
from dtpyfw.core.require_extra import require_extra
```

## Functions

### `require_extra(extra_name: str, *modules: str) -> None`

Raise RuntimeError if any of the specified modules cannot be imported.

**Description:**

Validates that optional dependencies are installed. Used throughout dtpyfw to enforce that extras specified in `pyproject.toml` are available before using features that depend on them. Provides helpful error messages with installation commands.

**Parameters:**

- **extra_name** (`str`): Name of the extra group (e.g., 'bucket', 'redis', 'kafka')
- ***modules** (`str`): Module names to check for availability

**Returns:**

- `None`

**Raises:**

- **RuntimeError**: If any module cannot be imported, with installation instructions

**Example:**

```python
from dtpyfw.core.require_extra import require_extra

# Check if Redis dependencies are installed
require_extra("redis", "redis")

# Check multiple dependencies for database features
require_extra("db", "sqlalchemy", "alembic", "psycopg2")

# If not installed, raises:
# RuntimeError: Missing optional dependency `redis`. 
# Install with `pip install dtpyfw[redis]`.
```

## Usage in dtpyfw Modules

### In `__init__.py` Files

```python
# dtpyfw/redis/__init__.py
from ..core.require_extra import require_extra

# Ensure Redis is installed before importing Redis features
require_extra("redis", "redis")

from .connection import RedisConnection
from .caching import cache_get, cache_set
```

### In Module Files

```python
# dtpyfw/bucket/bucket.py
from dtpyfw.core.require_extra import require_extra

# Check for S3 dependencies
require_extra("bucket", "boto3", "botocore")

class BucketClient:
    # Implementation using boto3
    pass
```

## Complete Usage Examples

### 1. Optional Feature Protection

```python
from dtpyfw.core.require_extra import require_extra

class EmailService:
    def __init__(self):
        # Only import if email dependencies are installed
        require_extra("email", "sendgrid", "jinja2")
        
        from sendgrid import SendGridAPIClient
        self.client = SendGridAPIClient(api_key="...")
    
    def send_email(self, to: str, subject: str, body: str):
        # Send email using SendGrid
        pass

# Usage
try:
    service = EmailService()
except RuntimeError as e:
    print(f"Email feature not available: {e}")
    # Fallback to different notification method
```

### 2. Plugin System

```python
from dtpyfw.core.require_extra import require_extra

class PluginManager:
    def load_plugin(self, plugin_name: str, dependencies: list):
        """Load plugin if dependencies are available."""
        try:
            require_extra(plugin_name, *dependencies)
            # Import and initialize plugin
            plugin_module = __import__(f"plugins.{plugin_name}")
            return plugin_module.initialize()
        except RuntimeError as e:
            print(f"Plugin {plugin_name} unavailable: {e}")
            return None

# Usage
manager = PluginManager()
analytics = manager.load_plugin("analytics", ["pandas", "numpy", "matplotlib"])
```

### 3. Feature Flags

```python
from dtpyfw.core.require_extra import require_extra

class FeatureFlags:
    @staticmethod
    def is_feature_available(feature_name: str, modules: list) -> bool:
        """Check if a feature's dependencies are installed."""
        try:
            require_extra(feature_name, *modules)
            return True
        except RuntimeError:
            return False

# Usage
if FeatureFlags.is_feature_available("ml", ["tensorflow", "sklearn"]):
    from .ml import MachineLearningService
    ml_service = MachineLearningService()
else:
    print("ML features not available")
```

### 4. Graceful Degradation

```python
from dtpyfw.core.require_extra import require_extra

class CacheService:
    def __init__(self):
        # Try Redis first, fallback to in-memory
        try:
            require_extra("redis", "redis")
            from .redis_cache import RedisCache
            self.backend = RedisCache()
            print("Using Redis cache")
        except RuntimeError:
            from .memory_cache import MemoryCache
            self.backend = MemoryCache()
            print("Using in-memory cache (Redis not available)")
    
    def get(self, key: str):
        return self.backend.get(key)
    
    def set(self, key: str, value: any, ttl: int = 3600):
        self.backend.set(key, value, ttl)
```

### 5. Development vs Production Dependencies

```python
from dtpyfw.core.require_extra import require_extra
import os

class DevelopmentTools:
    def __init__(self):
        if os.getenv("ENVIRONMENT") == "development":
            # Only require dev dependencies in development
            try:
                require_extra("dev", "pytest", "black", "mypy")
                self.testing_enabled = True
            except RuntimeError:
                self.testing_enabled = False
        else:
            self.testing_enabled = False
    
    def run_tests(self):
        if not self.testing_enabled:
            print("Development dependencies not installed")
            return
        
        import pytest
        pytest.main(["-v"])
```

### 6. Conditional Import Helper

```python
from dtpyfw.core.require_extra import require_extra
from typing import Optional, Any

def try_import(extra_name: str, module_name: str) -> Optional[Any]:
    """Try to import a module, return None if not available."""
    try:
        require_extra(extra_name, module_name)
        return __import__(module_name)
    except RuntimeError:
        return None

# Usage
pandas = try_import("data", "pandas")
if pandas:
    df = pandas.DataFrame(data)
else:
    # Use alternative data structure
    pass
```

## Available Extras in dtpyfw

| Extra Name | Dependencies | Purpose |
|------------|--------------|---------|
| `core` | requests | Core HTTP functionality |
| `api` | fastapi, uvicorn | FastAPI application support |
| `db` | sqlalchemy, alembic, psycopg2-binary | Database operations |
| `redis` | redis | Redis caching and streaming |
| `kafka` | kafka-python | Kafka messaging |
| `bucket` | boto3, botocore | S3-compatible storage |
| `ftp` | paramiko | FTP/SFTP operations |
| `worker` | celery | Task queue workers |
| `encrypt` | cryptography | Encryption utilities |
| `all` | All of the above | Complete installation |

## Installation Commands

```bash
# Install specific extra
pip install dtpyfw[redis]

# Install multiple extras
pip install dtpyfw[redis,kafka,db]

# Install all extras
pip install dtpyfw[all]

# Install for development
pip install dtpyfw[all,dev]
```

## Best Practices

1. **Check at module import time:**
   ```python
   # At the top of your module
   from dtpyfw.core.require_extra import require_extra
   
   require_extra("redis", "redis")
   
   # Rest of imports that depend on redis
   import redis
   ```

2. **Provide clear extra names:**
   ```python
   # Good
   require_extra("ml", "tensorflow", "sklearn")
   
   # Less helpful
   require_extra("deps", "tensorflow", "sklearn")
   ```

3. **Group related dependencies:**
   ```python
   # Check all related dependencies together
   require_extra("data_science", "pandas", "numpy", "matplotlib", "scipy")
   ```

4. **Handle errors appropriately:**
   ```python
   try:
       require_extra("optional_feature", "some_module")
       from some_module import SomeClass
       use_optional_feature = True
   except RuntimeError as e:
       print(f"Optional feature disabled: {e}")
       use_optional_feature = False
   ```

5. **Document required extras:**
   ```python
   def process_data_with_pandas(data):
       """
       Process data using pandas.
       
       Requires:
           dtpyfw[data] extra to be installed
       
       Raises:
           RuntimeError: If pandas is not installed
       """
       require_extra("data", "pandas")
       import pandas as pd
       # Process data
   ```

## Error Messages

When a dependency is missing, users see:

```
RuntimeError: Missing optional dependency `redis`. Install with `pip install dtpyfw[redis]`.
```

This provides:
- Clear indication of what's missing
- Exact command to install it
- Context about which feature group it belongs to

## Related Modules

All dtpyfw modules use `require_extra`:
- **dtpyfw.redis** - Requires 'redis' extra
- **dtpyfw.kafka** - Requires 'kafka' extra
- **dtpyfw.bucket** - Requires 'bucket' extra
- **dtpyfw.db** - Requires 'db' extra
- **dtpyfw.ftp** - Requires 'ftp' extra
- **dtpyfw.worker** - Requires 'worker' extra

## See Also

- [Python importlib.util](https://docs.python.org/3/library/importlib.html#importlib.util.find_spec)
- [Setuptools extras_require](https://setuptools.pypa.io/en/latest/userguide/dependency_management.html#optional-dependencies)
- [Poetry extras](https://python-poetry.org/docs/pyproject/#extras)
