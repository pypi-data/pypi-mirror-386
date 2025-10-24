# Worker

## Overview

The `Worker` class is a fluent builder for configuring and creating Celery applications within the DealerTower framework. It provides a comprehensive, builder pattern interface for constructing Celery workers with advanced configuration options including Redis integration, task routing, SSL/TLS support, and integration with RedBeat scheduling and celery-once task locking.

## Module Location

```python
from dtpyfw.worker import Worker
```

## Class Definition

### Worker

A builder class that simplifies the configuration and instantiation of Celery applications with enterprise-grade features.

#### Attributes

- **`_celery`** (`dict[str, Any]`): Core Celery application configuration parameters including name, serializers, timezone, and broker/backend settings.
- **`_celery_conf`** (`dict[str, Any]`): Additional Celery configuration settings for transport options, routing, scheduling, and extensions.
- **`_discovered_task`** (`list[str]`): List of task module paths for Celery's autodiscovery mechanism.

#### Default Configuration

The Worker class initializes with sensible defaults:

```python
{
    "name": "dt_celery_app",
    "task_serializer": "json",
    "result_serializer": "json",
    "timezone": "America/Los_Angeles",
    "task_track_started": True,
    "result_persistent": True,
    "worker_prefetch_multiplier": 1,
    "broker": None,
    "backend": None,
}
```

## Methods

### Task Configuration

#### `set_task(task: Task) -> Worker`

Attach a Task registry containing routes, schedules, and modules for autodiscovery.

**Parameters:**
- `task` (`Task`): A Task instance containing registered task routes, periodic schedules, and module paths.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures the worker with task routing, periodic schedules, and autodiscovery modules from a Task instance. This method extracts:
- Task routes for queue routing
- Beat schedules for periodic execution
- Task module paths for Celery's autodiscovery mechanism

**Example:**

```python
from dtpyfw.worker import Worker, Task
from celery.schedules import crontab

# Create and configure task registry
task = Task()
task.register("myapp.tasks.process_order", queue="orders")
task.register_periodic_task(
    "myapp.tasks.cleanup",
    schedule=crontab(hour=2, minute=0),
    queue="maintenance"
)

# Attach to worker
worker = Worker()
worker.set_task(task)
```

---

### Redis Configuration

#### `set_redis(redis_instance: RedisInstance, retry_on_timeout: bool = True, socket_keepalive: bool = True) -> Worker`

Configure Redis as both message broker and result backend with comprehensive connection settings.

**Parameters:**
- `redis_instance` (`RedisInstance`): The Redis connection instance containing configuration and URL.
- `retry_on_timeout` (`bool`, optional): Whether to retry Redis operations that timeout. Defaults to `True`.
- `socket_keepalive` (`bool`, optional): Whether to enable TCP keepalive on Redis sockets to detect dead connections. Defaults to `True`.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures Redis as both the message broker and result backend for Celery. Automatically:
- Extracts Redis URL from the RedisInstance
- Applies connection parameters (max connections, timeouts, retry behavior)
- Enables SSL/TLS configuration when `rediss://` URL is detected
- Configures RedBeat and celery-once to use the same Redis instance

**Example:**

```python
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.worker import Worker

# Create Redis instance
redis = RedisInstance(
    redis_host="localhost",
    redis_port=6379,
    redis_db=0,
    redis_max_connections=20
)

# Configure worker with Redis
worker = Worker()
worker.set_redis(
    redis_instance=redis,
    retry_on_timeout=True,
    socket_keepalive=True
)
```

**SSL/TLS Support:**

When using `rediss://` URLs, the worker automatically configures SSL settings:

```python
redis = RedisInstance(
    redis_host="secure.redis.example.com",
    redis_port=6380,
    redis_ssl=True  # This will create rediss:// URL
)

worker = Worker()
worker.set_redis(redis)  # Automatically configures SSL with CERT_NONE
```

---

### Application Settings

#### `set_name(name: str) -> Worker`

Set the main application name for the Celery instance.

**Parameters:**
- `name` (`str`): The application name for the Celery instance.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures the Celery application's main name identifier, used in logs, monitoring tools, and process identification.

**Example:**

```python
worker = Worker()
worker.set_name("order_processing_service")
```

---

#### `set_timezone(timezone: str) -> Worker`

Set the timezone for Celery task scheduling and execution.

**Parameters:**
- `timezone` (`str`): The timezone identifier (e.g., "UTC", "America/New_York", "Europe/London").

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures the timezone used by Celery for task scheduling, particularly affecting when scheduled periodic tasks execute.

**Example:**

```python
worker = Worker()
worker.set_timezone("America/New_York")
```

---

### Serialization Configuration

#### `set_task_serializer(task_serializer: str) -> Worker`

Set the serialization format for task messages sent to the broker.

**Parameters:**
- `task_serializer` (`str`): The serializer name ("json", "pickle", "yaml", "msgpack").

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures how task messages are serialized when sent to the broker. JSON is recommended for security and interoperability.

**Example:**

```python
worker = Worker()
worker.set_task_serializer("json")  # Default and recommended
```

---

#### `set_result_serializer(result_serializer: str) -> Worker`

Set the serialization format for task results stored in the backend.

**Parameters:**
- `result_serializer` (`str`): The serializer name ("json", "pickle", "yaml", "msgpack").

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures how task results are serialized when stored in the result backend.

**Example:**

```python
worker = Worker()
worker.set_result_serializer("json")  # Default and recommended
```

---

### Task Tracking and Results

#### `set_track_started(value: bool) -> Worker`

Enable or disable tracking of task started state.

**Parameters:**
- `value` (`bool`): `True` to enable task started tracking, `False` to disable.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures whether Celery tracks when a task transitions to the "started" state. Enabling provides more detailed task lifecycle information but adds overhead.

**Example:**

```python
worker = Worker()
worker.set_track_started(True)  # Track when tasks begin execution
```

---

#### `set_result_persistent(value: bool) -> Worker`

Enable or disable persistent storage of task results.

**Parameters:**
- `value` (`bool`): `True` to persist results, `False` to disable persistence.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures whether task results are persisted in the result backend. When enabled, results are stored and can be retrieved later.

**Example:**

```python
worker = Worker()
worker.set_result_persistent(True)  # Store results in backend
```

---

#### `set_result_expires(result_expires: int) -> Worker`

Set the expiration time for task results in seconds.

**Parameters:**
- `result_expires` (`int`): The result expiration time in seconds.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures how long task results are retained in the result backend before being automatically deleted. Helps manage storage and prevents indefinite growth.

**Example:**

```python
worker = Worker()
worker.set_result_expires(7200)  # Results expire after 2 hours
```

---

### Worker Performance

#### `set_worker_prefetch_multiplier(number: int) -> Worker`

Set the number of tasks each worker prefetches from the broker.

**Parameters:**
- `number` (`int`): The prefetch multiplier value (typically 1-4).

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures how many tasks a worker will prefetch and reserve from the broker. A value of 1 ensures fair distribution but may reduce throughput. Higher values increase throughput but may cause uneven task distribution.

**Example:**

```python
worker = Worker()
worker.set_worker_prefetch_multiplier(1)  # Fair distribution (default)
# or
worker.set_worker_prefetch_multiplier(4)  # Higher throughput
```

---

### Redis Key Prefixes

#### `set_broker_prefix(prefix: str) -> Worker`

Set the Redis key prefix for broker transport options.

**Parameters:**
- `prefix` (`str`): The key prefix string (will be suffixed with ":").

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures the global key prefix for broker messages in Redis. Allows multiple Celery applications to share a Redis instance without key collisions.

**Example:**

```python
worker = Worker()
worker.set_broker_prefix("myapp-celery-broker")
# Keys will be stored as "myapp-celery-broker:*"
```

---

#### `set_backend_prefix(prefix: str) -> Worker`

Set the Redis key prefix for result backend transport options.

**Parameters:**
- `prefix` (`str`): The key prefix string (will be suffixed with ":").

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures the global key prefix for task results in Redis. Allows multiple Celery applications to share a Redis instance without key collisions.

**Example:**

```python
worker = Worker()
worker.set_backend_prefix("myapp-celery-backend")
# Keys will be stored as "myapp-celery-backend:*"
```

---

#### `set_redbeat_key_prefix(prefix: str) -> Worker`

Set the Redis key prefix for RedBeat schedule storage.

**Parameters:**
- `prefix` (`str`): The key prefix string (will be suffixed with ":").

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures the key prefix for RedBeat periodic task schedules in Redis. Allows multiple Celery applications to share a Redis instance without schedule collisions.

**Example:**

```python
worker = Worker()
worker.set_redbeat_key_prefix("myapp-celery-beat")
# Beat schedules stored as "myapp-celery-beat:*"
```

---

#### `set_redbeat_lock_key(redbeat_lock_key: str) -> Worker`

Set the Redis key name for the RedBeat scheduler lock.

**Parameters:**
- `redbeat_lock_key` (`str`): The Redis key name for the RedBeat lock.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures the lock key used by RedBeat to ensure only one beat scheduler runs at a time across multiple worker instances. Prevents duplicate execution of periodic tasks.

**Example:**

```python
worker = Worker()
worker.set_redbeat_lock_key("myapp-redbeat-lock")
```

---

### Connection Management

#### `set_enable_utc(value: bool) -> Worker`

Enable or disable UTC mode for all Celery timestamps.

**Parameters:**
- `value` (`bool`): `True` to enable UTC mode, `False` to use configured timezone.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures whether Celery uses UTC for all internal timestamps and scheduling. When disabled, the configured timezone is used instead.

**Example:**

```python
worker = Worker()
worker.set_enable_utc(False)  # Use configured timezone instead of UTC
```

---

#### `set_broker_connection_max_retries(value: Optional[int]) -> Worker`

Set the maximum number of broker connection retry attempts.

**Parameters:**
- `value` (`Optional[int]`): Maximum retry attempts, or `None` for unlimited retries.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures how many times Celery will attempt to reconnect to the broker when a connection is lost.

**Example:**

```python
worker = Worker()
worker.set_broker_connection_max_retries(10)  # Retry up to 10 times
# or
worker.set_broker_connection_max_retries(None)  # Unlimited retries (default)
```

---

#### `set_broker_connection_retry_on_startup(value: bool) -> Worker`

Enable or disable broker connection retry during worker startup.

**Parameters:**
- `value` (`bool`): `True` to retry connections on startup, `False` to fail fast.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures whether the worker will retry connecting to the broker during startup if the initial connection fails.

**Example:**

```python
worker = Worker()
worker.set_broker_connection_retry_on_startup(True)  # Retry on startup (default)
```

---

### Celery-Once Configuration

#### `set_once_default_timeout(default_timeout: int) -> Worker`

Set the default lock timeout for celery-once task deduplication.

**Parameters:**
- `default_timeout` (`int`): The lock timeout in seconds.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures the default timeout for celery-once locks, which prevent duplicate execution of tasks. When a task is running, subsequent invocations are blocked until the lock expires or is released.

**Example:**

```python
worker = Worker()
worker.set_once_default_timeout(300)  # 5-minute lock timeout
```

---

#### `set_once_blocking(blocking: bool) -> Worker`

Enable or disable blocking behavior for celery-once locks.

**Parameters:**
- `blocking` (`bool`): `True` to enable blocking wait, `False` to fail immediately.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures whether tasks should block and wait when a celery-once lock is already held. When enabled, tasks wait for lock release. When disabled, tasks fail immediately if locked.

**Example:**

```python
worker = Worker()
worker.set_once_blocking(True)  # Wait for lock to be released
```

---

#### `set_once_blocking_timeout(blocking_timeout: int) -> Worker`

Set the blocking timeout for celery-once lock acquisition.

**Parameters:**
- `blocking_timeout` (`int`): The blocking timeout in seconds.

**Returns:**
- `Worker`: The current Worker instance for method chaining.

**Description:**

Configures how long a task will wait to acquire a celery-once lock when blocking is enabled. If the lock cannot be acquired within this timeout, the task fails.

**Example:**

```python
worker = Worker()
worker.set_once_blocking(True)
worker.set_once_blocking_timeout(60)  # Wait up to 60 seconds for lock
```

---

### Creating the Celery Application

#### `create() -> Celery`

Create and return a fully configured Celery application instance.

**Returns:**
- `Celery`: A fully configured Celery application instance.

**Description:**

Instantiates a Celery application with all configured settings, including broker, backend, serializers, task routing, periodic schedules, and autodiscovery of task modules. This method should be called after all configuration methods to produce the final Celery app.

**Example:**

```python
worker = Worker()
worker.set_name("my_app")
worker.set_redis(redis_instance)
worker.set_task(task_registry)

celery_app = worker.create()  # Returns configured Celery instance
```

---

## Complete Usage Examples

### Basic Worker Setup

```python
from dtpyfw.worker import Worker, Task
from dtpyfw.redis.connection import RedisInstance

# Configure Redis
redis = RedisInstance(
    redis_host="localhost",
    redis_port=6379,
    redis_db=0
)

# Configure tasks
task = Task()
task.register("myapp.tasks.send_email", queue="emails")
task.register("myapp.tasks.process_payment", queue="payments")

# Create worker
worker = Worker()
worker.set_name("myapp_worker")
worker.set_redis(redis)
worker.set_task(task)
worker.set_timezone("America/New_York")

# Create Celery app
celery_app = worker.create()
```

---

### Advanced Worker with Periodic Tasks

```python
from dtpyfw.worker import Worker, Task
from dtpyfw.redis.connection import RedisInstance
from celery.schedules import crontab
from datetime import timedelta

# Configure Redis with SSL
redis = RedisInstance(
    redis_host="secure.redis.example.com",
    redis_port=6380,
    redis_ssl=True,
    redis_max_connections=50
)

# Configure tasks with periodic schedules
task = Task()

# Regular tasks
task.register("myapp.tasks.process_order", queue="orders")
task.register("myapp.tasks.send_notification", queue="notifications")

# Periodic tasks
task.register_periodic_task(
    route="myapp.tasks.daily_report",
    schedule=crontab(hour=8, minute=0),  # Every day at 8 AM
    queue="reports"
)

task.register_periodic_task(
    route="myapp.tasks.cleanup_old_data",
    schedule=crontab(hour=2, minute=0, day_of_week=0),  # Sundays at 2 AM
    queue="maintenance"
)

task.register_periodic_task(
    route="myapp.tasks.health_check",
    schedule=timedelta(minutes=5),  # Every 5 minutes
    queue="monitoring"
)

# Create worker with advanced configuration
worker = Worker()
worker.set_name("myapp_production_worker")
worker.set_redis(redis, retry_on_timeout=True, socket_keepalive=True)
worker.set_task(task)
worker.set_timezone("UTC")
worker.set_enable_utc(True)

# Performance tuning
worker.set_worker_prefetch_multiplier(2)
worker.set_result_expires(86400)  # 24 hours

# Key prefixes for multi-tenant setup
worker.set_broker_prefix("myapp-prod-broker")
worker.set_backend_prefix("myapp-prod-backend")
worker.set_redbeat_key_prefix("myapp-prod-beat")
worker.set_redbeat_lock_key("myapp-prod-beat-lock")

# Celery-once configuration
worker.set_once_default_timeout(600)  # 10 minutes
worker.set_once_blocking(True)
worker.set_once_blocking_timeout(120)  # Wait up to 2 minutes

# Connection retry configuration
worker.set_broker_connection_max_retries(10)
worker.set_broker_connection_retry_on_startup(True)

# Create Celery app
celery_app = worker.create()
```

---

### Multi-Environment Configuration

```python
import os
from dtpyfw.worker import Worker, Task
from dtpyfw.redis.connection import RedisInstance

# Environment-aware configuration
env = os.getenv("ENVIRONMENT", "development")

redis = RedisInstance(
    redis_host=os.getenv("REDIS_HOST", "localhost"),
    redis_port=int(os.getenv("REDIS_PORT", 6379)),
    redis_db=int(os.getenv("REDIS_DB", 0))
)

task = Task()
task.register("myapp.tasks.process_data", queue="default")

worker = Worker()
worker.set_name(f"myapp_{env}_worker")
worker.set_redis(redis)
worker.set_task(task)

# Environment-specific settings
if env == "production":
    worker.set_worker_prefetch_multiplier(4)
    worker.set_result_expires(86400)
    worker.set_broker_prefix(f"myapp-{env}-broker")
    worker.set_backend_prefix(f"myapp-{env}-backend")
else:
    worker.set_worker_prefetch_multiplier(1)
    worker.set_result_expires(3600)

celery_app = worker.create()
```

---

## Integration with Task Module

The Worker class is designed to work seamlessly with the `Task` class for task registration and scheduling. See the [Task documentation](task.md) for details on task registration patterns.

---

## Best Practices

1. **Builder Pattern**: Use method chaining for clean, readable configuration:
   ```python
   celery_app = (
       Worker()
       .set_name("myapp")
       .set_redis(redis)
       .set_task(task)
       .set_timezone("UTC")
       .create()
   )
   ```

2. **Prefetch Multiplier**: Use `1` for fair distribution in queues with mixed task durations. Use higher values (2-4) for uniform, short tasks.

3. **Result Expiration**: Set appropriate result expiration to prevent Redis from growing indefinitely:
   ```python
   worker.set_result_expires(86400)  # 24 hours for most use cases
   ```

4. **Key Prefixes**: Always set key prefixes when multiple applications share a Redis instance:
   ```python
   worker.set_broker_prefix("myapp-broker")
   worker.set_backend_prefix("myapp-backend")
   worker.set_redbeat_key_prefix("myapp-beat")
   ```

5. **SSL/TLS**: Use `rediss://` URLs for secure Redis connections in production.

6. **Timezone**: Use UTC in production for consistency:
   ```python
   worker.set_timezone("UTC")
   worker.set_enable_utc(True)
   ```

7. **Celery-Once**: Configure appropriate timeouts based on task duration to prevent duplicate execution.

---

## Dependencies

- **celery**: The Celery distributed task queue
- **redis**: Redis Python client (installed via RedisInstance dependency)
- **redbeat**: RedBeat scheduler for Celery beat with Redis
- **celery-once**: Task deduplication extension for Celery

Install with extras:
```bash
poetry install -E worker
```

---

## Related Documentation

- [Task Registration](task.md) - Task registry and scheduling
- [Redis Connection](../redis/connection.md) - Redis configuration
- [Redis Caching](../redis/caching.md) - Redis caching utilities

---

## Notes

- The Worker class uses class-level dictionaries for default configuration. Each instance starts with these defaults and can override them via setter methods.
- SSL/TLS is automatically configured when `rediss://` URLs are detected, using `ssl.CERT_NONE` for certificate verification.
- RedBeat is the default scheduler, storing schedules in Redis for distributed beat scheduling.
- Celery-once is pre-configured for task deduplication using Redis as the locking backend.
