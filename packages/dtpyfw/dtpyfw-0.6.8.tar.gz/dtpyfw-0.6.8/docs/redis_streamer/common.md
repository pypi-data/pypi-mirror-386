# dtpyfw.redis_streamer.common

## Overview

The `common` module provides the `CommonMethods` base class, which serves as the foundation for both synchronous and asynchronous Redis Streams consumer implementations. It encapsulates shared utilities for consumer naming, subscription management, handler registration, deduplication tracking, and maintenance operations. This class ensures consistent behavior across different consumer types while reducing code duplication.

## Module Information

- **Module Path**: `dtpyfw.redis_streamer.common`
- **Class**: `CommonMethods`
- **Dependencies**:
  - `redis` - Redis client library
  - `dtpyfw.redis.connection` - Redis connection management
  - `dtpyfw.log.footprint` - Logging utilities
- **Extended By**: `AsyncRedisStreamer`, `RedisStreamer`

## CommonMethods Class

The `CommonMethods` class provides the shared foundation for Redis Streams consumers with built-in deduplication, subscription tracking, and handler management.

### Class Signature

```python
class CommonMethods:
    """Base class providing shared utilities for Redis Streams consumers.

    Description:
        Provides common methods and state management used by both synchronous
        and asynchronous Redis Streams consumer implementations. Handles
        consumer naming, subscription tracking, handler registration, and
        shared maintenance operations.
    """
```

### Constructor

```python
def __init__(
    self,
    redis_instance: RedisInstance,
    consumer_name: str,
    dedup_window_ms: int = 7 * 24 * 60 * 60 * 1000,
) -> None:
    """Initialize common consumer state and configuration.

    Args:
        redis_instance (RedisInstance): The Redis connection manager.
        consumer_name (str): The logical name of the consumer service.
        dedup_window_ms (int, optional): Time window in milliseconds for
            deduplication tracking. Defaults to 7 days (604800000 ms).
    """
```

#### Parameters

| Parameter         | Type            | Required | Default      | Description                                                                    |
|-------------------|-----------------|----------|--------------|--------------------------------------------------------------------------------|
| `redis_instance`  | `RedisInstance` | Yes      | -            | The Redis connection manager for accessing Redis Streams                       |
| `consumer_name`   | `str`           | Yes      | -            | Logical name of the consumer service (sanitized automatically)                 |
| `dedup_window_ms` | `int`           | No       | `604800000`  | Deduplication window in milliseconds (default: 7 days)                         |

### Instance Attributes

| Attribute                      | Type                                        | Description                                                          |
|--------------------------------|---------------------------------------------|----------------------------------------------------------------------|
| `listener_name`                | `str`                                       | Sanitized logical name of the consumer service                       |
| `consumer_instance_name`       | `str`                                       | Unique instance identifier for this consumer                         |
| `_redis_instance`              | `RedisInstance`                             | Redis connection manager                                             |
| `_subscriptions`               | `List[Tuple[str, str, str]]`                | List of (channel, listener, group) tuples                            |
| `_handlers`                    | `DefaultDict[Tuple[str, str], List[Callable]]` | Map of (channel, listener) to handler functions                      |
| `_dedup_window_ms`             | `int`                                       | Deduplication window in milliseconds                                 |
| `_last_ledger_cleanup`         | `int`                                       | Timestamp of last deduplication cleanup                              |
| `_ledger_cleanup_interval`     | `int`                                       | Cleanup interval in milliseconds (default: 5 minutes)                |
| `_channel_retention`           | `Dict[str, Optional[int]]`                  | Map of channel names to retention periods in milliseconds            |

## Methods

### Consumer Naming Methods

#### `_gen_consumer_name()`

```python
def _gen_consumer_name(self) -> str:
    """Generate unique consumer instance name.

    Returns:
        str: Unique consumer instance identifier.
    """
```

Delegates to the static consumer name generator to create a unique identifier for this consumer instance.

**Returns**: Unique consumer instance name combining listener name, hostname, PID, and random suffix

---

#### `_consumer_name_generator()`

```python
@classmethod
def _consumer_name_generator(cls, listener_name: str) -> str:
    """Generate a globally unique consumer instance identifier.

    Description:
        Creates a unique consumer name by combining the listener name,
        hostname (or pod name in Kubernetes), process ID, and a random
        suffix. This ensures each consumer instance is uniquely
        identifiable in the Redis consumer group.

    Args:
        listener_name (str): The logical consumer service name.

    Returns:
        str: Unique consumer instance identifier.
    """
```

**Format**: `<listener_name>.<hostname>.<pid>.<random_8_chars>`

**Examples**:

```text
order-processor.pod-abc123.12345.a1b2c3d4
user-service.hostname-server01.67890.e5f6g7h8
```

**Environment Variables Used**:

- `POD_NAME`: Kubernetes pod name (preferred)
- `HOSTNAME`: System hostname (fallback)
- Uses `socket.gethostname()` if neither is set

---

#### `_sanitize()`

```python
@staticmethod
def _sanitize(s: str, maxlen: int) -> str:
    """Sanitize and truncate a string for use in Redis keys.

    Description:
        Removes or replaces invalid characters and ensures the string
        does not exceed a specified maximum length. Only alphanumeric
        characters and ._:- are preserved.

    Args:
        s (str): The string to sanitize.
        maxlen (int): Maximum allowed length for the result.

    Returns:
        str: Sanitized and truncated string.
    """
```

**Character Handling**:

- **Allowed**: `a-z`, `A-Z`, `0-9`, `.`, `_`, `:`, `-`
- **Replaced**: All other characters become `-`
- **Truncated**: Result is limited to `maxlen` characters

**Examples**:

```python
CommonMethods._sanitize("my consumer!", 20)
# Returns: "my-consumer-"

CommonMethods._sanitize("user@service#123", 15)
# Returns: "user-service-12"

CommonMethods._sanitize("valid.name_123", 50)
# Returns: "valid.name_123"
```

---

### Redis Key Generation Methods

#### `_group_name()`

```python
@staticmethod
def _group_name(channel: str, listener_name: str) -> str:
    """Generate consumer group name for a channel and listener.

    Description:
        Constructs the Redis consumer group identifier used for
        decoupled fan-out across microservices.

    Args:
        channel (str): The Redis stream channel name.
        listener_name (str): The logical consumer service name.

    Returns:
        str: Consumer group identifier.
    """
```

**Format**: `<channel>:<listener_name>:cg`

**Examples**:

```python
CommonMethods._group_name("orders", "order-processor")
# Returns: "orders:order-processor:cg"

CommonMethods._group_name("notifications", "email-service")
# Returns: "notifications:email-service:cg"
```

---

#### `_processed_zset_key()`

```python
@staticmethod
def _processed_zset_key(channel: str, group: str) -> str:
    """Generate ZSET key for deduplication tracking.

    Description:
        Creates the Redis ZSET key used to track processed message IDs
        for at-most-once delivery guarantees within a consumer group.

    Args:
        channel (str): The Redis stream channel name.
        group (str): The consumer group identifier.

    Returns:
        str: ZSET key for processed messages.
    """
```

**Format**: `stream:<channel>:group:<group>:processed`

**Examples**:

```python
group = CommonMethods._group_name("orders", "order-processor")
CommonMethods._processed_zset_key("orders", group)
# Returns: "stream:orders:group:orders:order-processor:cg:processed"
```

---

### Utility Methods

#### `_server_now_ms()`

```python
@staticmethod
def _server_now_ms() -> int:
    """Get current server time in milliseconds since epoch.

    Description:
        Provides a consistent timestamp for deduplication and cleanup
        operations across the Redis Streams consumer.

    Returns:
        int: Current time in milliseconds.
    """
```

**Examples**:

```python
now = CommonMethods._server_now_ms()
# Returns: 1729768245123 (example timestamp)
```

---

### Handler Registration

#### `register_handler()`

```python
def register_handler(
    self,
    channel_name: str,
    handler_func: Callable,
    listener_name: Optional[str] = None,
) -> "Self":
    """Register a handler function for a specific channel.

    Description:
        Associates a callable handler with a channel and listener pair.
        When messages are consumed from the channel, registered handlers
        are invoked with the message name and payload. Multiple handlers
        can be registered for the same channel.

    Args:
        channel_name (str): The Redis stream channel name to monitor.
        handler_func (Callable): The handler function to invoke for messages.
            Must accept 'name' and 'payload' keyword arguments.
        listener_name (Optional[str], optional): The listener name to associate
            with this handler. If not provided, uses the instance's listener_name.

    Returns:
        CommonMethods: Returns self for method chaining.
    """
```

**Handler Function Signature**:

```python
def my_handler(name: str, payload: Dict[str, Any]) -> None:
    """Handler function for processing messages."""
    pass

# Or async
async def my_async_handler(name: str, payload: Dict[str, Any]) -> None:
    """Async handler function for processing messages."""
    pass
```

**Example**:

```python
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

async def process_order(name: str, payload: Dict[str, Any]) -> None:
    order_id = payload.get("order_id")
    print(f"Processing order: {order_id}")

streamer = AsyncRedisStreamer(redis_instance, "order-processor")
streamer.register_handler("orders", process_order)
```

---

### Channel Management

#### `register_channel()`

```python
def register_channel(
    self,
    channel_name: str,
    retention_ms: int = 24 * 60 * 60 * 1000,
) -> "Self":
    """Register channel metadata with optional retention configuration.

    Description:
        Registers a channel for cleanup operations with a specified
        retention period. Messages older than the retention window
        will be eligible for removal during periodic cleanup tasks.

    Args:
        channel_name (str): The Redis stream channel name to register.
        retention_ms (int, optional): Retention period in milliseconds
            for deduplication tracking. Defaults to 24 hours (86400000 ms).

    Returns:
        CommonMethods: Returns self for method chaining.
    """
```

**Example**:

```python
streamer = AsyncRedisStreamer(redis_instance, "processor")

# Register with default 24-hour retention
streamer.register_channel("orders")

# Register with custom 7-day retention
streamer.register_channel("audit-logs", retention_ms=7*24*60*60*1000)

# Register with 1-hour retention for high-throughput channels
streamer.register_channel("metrics", retention_ms=60*60*1000)
```

---

### Dead Letter Handling

#### `_dead_letter()`

```python
@staticmethod
def _dead_letter(
    channel: str, reason: str, message_id: str, extra: Dict[str, Any]
) -> None:
    """Log a failed message to the dead letter log.

    Description:
        Records information about messages that failed processing due to
        decode errors, schema validation failures, or handler exceptions.
        Uses the footprint logging system to create an audit trail.

    Args:
        channel (str): The Redis stream channel name where the failure occurred.
        reason (str): The failure reason category ('decode/schema' or 'handler').
        message_id (str): The Redis stream message ID that failed.
        extra (Dict[str, Any]): Additional context about the failure.

    Returns:
        None
    """
```

**Failure Reasons**:

- `"decode/schema"`: JSON decoding or schema validation failed
- `"handler"`: Handler function raised an exception

**Logged Information**:

```json
{
  "reason": "handler",
  "channel": "orders",
  "message_id": "1729768245123-0",
  "listener": "order-processor",
  "handler": "process_order",
  "error": "ValueError: Invalid order amount",
  "name": "order.created"
}
```

---

## Usage Examples

### Example 1: Basic Consumer Setup

```python
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis_streamer.synchronize import RedisStreamer

# Initialize Redis connection
redis_instance = RedisInstance(
    host="localhost",
    port=6379,
    db=0
)

# Create consumer (inherits from CommonMethods)
consumer = RedisStreamer(
    redis_instance=redis_instance,
    consumer_name="order-processor",
    dedup_window_ms=7 * 24 * 60 * 60 * 1000  # 7 days
)

print(f"Listener name: {consumer.listener_name}")
print(f"Instance name: {consumer.consumer_instance_name}")
```

### Example 2: Registering Multiple Handlers

```python
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer
from typing import Dict, Any

async def log_event(name: str, payload: Dict[str, Any]) -> None:
    """Log all events for audit purposes."""
    print(f"[AUDIT] Event: {name}, Payload: {payload}")

async def process_event(name: str, payload: Dict[str, Any]) -> None:
    """Process business logic."""
    if name == "order.created":
        print(f"Creating order: {payload['order_id']}")
    elif name == "order.updated":
        print(f"Updating order: {payload['order_id']}")

# Create consumer
streamer = AsyncRedisStreamer(redis_instance, "order-service")

# Register multiple handlers for the same channel
streamer.register_handler("orders", log_event)
streamer.register_handler("orders", process_event)

# Both handlers will be called for each message
```

### Example 3: Channel Retention Configuration

```python
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

streamer = AsyncRedisStreamer(redis_instance, "analytics-service")

# High-volume metrics with short retention
streamer.register_channel(
    "metrics.realtime",
    retention_ms=1 * 60 * 60 * 1000  # 1 hour
)

# Audit logs with long retention
streamer.register_channel(
    "audit.events",
    retention_ms=30 * 24 * 60 * 60 * 1000  # 30 days
)

# User events with medium retention
streamer.register_channel(
    "user.activity",
    retention_ms=7 * 24 * 60 * 60 * 1000  # 7 days
)
```

### Example 4: Consumer Name Generation

```python
import os
from dtpyfw.redis_streamer.common import CommonMethods

# Set environment for Kubernetes
os.environ["POD_NAME"] = "order-processor-abc123"

# Generate consumer instance name
instance_name = CommonMethods._consumer_name_generator("order-service")
print(f"Instance name: {instance_name}")
# Output: "order-service.order-processor-abc123.12345.a1b2c3d4"

# Sanitize a consumer name
sanitized = CommonMethods._sanitize("My Order Service!", 128)
print(f"Sanitized: {sanitized}")
# Output: "My-Order-Service-"
```

### Example 5: Redis Key Generation

```python
from dtpyfw.redis_streamer.common import CommonMethods

channel = "orders"
listener = "order-processor"

# Generate consumer group name
group = CommonMethods._group_name(channel, listener)
print(f"Consumer group: {group}")
# Output: "orders:order-processor:cg"

# Generate deduplication ZSET key
dedup_key = CommonMethods._processed_zset_key(channel, group)
print(f"Dedup key: {dedup_key}")
# Output: "stream:orders:group:orders:order-processor:cg:processed"
```

### Example 6: Method Chaining

```python
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

async def handle_order(name: str, payload: Dict[str, Any]) -> None:
    print(f"Handling order event: {name}")

async def handle_payment(name: str, payload: Dict[str, Any]) -> None:
    print(f"Handling payment event: {name}")

# Create and configure consumer with method chaining
streamer = (
    AsyncRedisStreamer(redis_instance, "payment-processor")
    .register_channel("orders", retention_ms=24*60*60*1000)
    .register_handler("orders", handle_order)
    .register_channel("payments", retention_ms=48*60*60*1000)
    .register_handler("payments", handle_payment)
)
```

### Example 7: Custom Handler Routing

```python
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer
from typing import Dict, Any, Callable

class MessageRouter:
    """Route messages based on name patterns."""
    
    def __init__(self):
        self.routes: Dict[str, Callable] = {}
    
    def register(self, pattern: str, handler: Callable):
        """Register a handler for a message name pattern."""
        self.routes[pattern] = handler
    
    async def route(self, name: str, payload: Dict[str, Any]):
        """Route message to appropriate handler."""
        for pattern, handler in self.routes.items():
            if name.startswith(pattern):
                await handler(name, payload)
                return
        print(f"No handler for message: {name}")

# Create router
router = MessageRouter()

# Register pattern-based handlers
async def handle_user_events(name: str, payload: Dict[str, Any]):
    print(f"User event: {name}")

async def handle_order_events(name: str, payload: Dict[str, Any]):
    print(f"Order event: {name}")

router.register("user.", handle_user_events)
router.register("order.", handle_order_events)

# Register router with streamer
streamer = AsyncRedisStreamer(redis_instance, "event-processor")
streamer.register_handler("events", router.route)
```

### Example 8: Deduplication Window Configuration

```python
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

# Short deduplication window (1 hour) for high-volume streams
high_volume_consumer = AsyncRedisStreamer(
    redis_instance,
    "metrics-processor",
    dedup_window_ms=1 * 60 * 60 * 1000
)

# Standard deduplication window (24 hours)
standard_consumer = AsyncRedisStreamer(
    redis_instance,
    "order-processor",
    dedup_window_ms=24 * 60 * 60 * 1000
)

# Long deduplication window (30 days) for critical operations
critical_consumer = AsyncRedisStreamer(
    redis_instance,
    "payment-processor",
    dedup_window_ms=30 * 24 * 60 * 60 * 1000
)
```

### Example 9: Monitoring Consumer State

```python
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

async def setup_monitoring():
    streamer = AsyncRedisStreamer(redis_instance, "monitor-service")
    
    # Register channels and handlers
    streamer.register_channel("events")
    streamer.register_handler("events", my_handler)
    
    # Access consumer state
    print(f"Listener name: {streamer.listener_name}")
    print(f"Instance name: {streamer.consumer_instance_name}")
    print(f"Dedup window: {streamer._dedup_window_ms}ms")
    print(f"Cleanup interval: {streamer._ledger_cleanup_interval}ms")
    
    # Check subscriptions
    print(f"Subscriptions: {len(streamer._subscriptions)}")
    for channel, listener, group in streamer._subscriptions:
        print(f"  - Channel: {channel}, Group: {group}")
    
    # Check registered handlers
    print(f"Handlers: {len(streamer._handlers)}")
    for (channel, listener), handlers in streamer._handlers.items():
        print(f"  - {channel}/{listener}: {len(handlers)} handlers")
```

## Deduplication System

### How At-Most-Once Delivery Works

The `CommonMethods` class implements at-most-once message delivery using Redis ZSET:

1. **Message Reservation**: When a message arrives, `_reserve_once()` attempts to add the message ID to a ZSET with the current timestamp as the score
2. **Atomic Check**: Redis ZADD with NX flag ensures only one consumer can reserve the message
3. **Processing**: If reservation succeeds, the message is processed
4. **Cleanup**: Expired entries (older than dedup window) are removed periodically

### ZSET Structure

```text
Key: stream:orders:group:orders:order-processor:cg:processed
Score (timestamp)    | Member (message ID)
---------------------|--------------------
1729768245123        | 1729768245123-0
1729768245456        | 1729768245456-0
1729768245789        | 1729768245789-0
```

### Cleanup Process

```python
# Pseudo-code for cleanup
now_ms = _server_now_ms()
cutoff = now_ms - dedup_window_ms

# Remove all entries older than cutoff
ZREMRANGEBYSCORE key -inf (cutoff)
```

## Consumer Group Architecture

### Decoupled Fan-Out

Each listener (microservice) gets its own consumer group:

```text
Stream: orders
├── Consumer Group: orders:order-processor:cg
│   ├── Consumer Instance: order-processor.pod-1.12345.abc
│   └── Consumer Instance: order-processor.pod-2.67890.def
├── Consumer Group: orders:inventory-service:cg
│   └── Consumer Instance: inventory-service.pod-1.11111.xyz
└── Consumer Group: orders:analytics-service:cg
    └── Consumer Instance: analytics-service.pod-1.22222.uvw
```

### Consumer Group Benefits

- **Independent Processing**: Each service processes all messages independently
- **Horizontal Scaling**: Multiple instances can share the workload within a group
- **Resilience**: Failed instances don't affect other groups
- **Message Replay**: Each group tracks its own position in the stream

## Best Practices

### 1. Choose Appropriate Deduplication Windows

```python
# High-volume, non-critical data: Short window
metrics_consumer = AsyncRedisStreamer(
    redis_instance,
    "metrics",
    dedup_window_ms=1 * 60 * 60 * 1000  # 1 hour
)

# Critical operations: Long window
payment_consumer = AsyncRedisStreamer(
    redis_instance,
    "payments",
    dedup_window_ms=30 * 24 * 60 * 60 * 1000  # 30 days
)
```

### 2. Use Descriptive Consumer Names

```python
# Good: Clear, descriptive names
AsyncRedisStreamer(redis_instance, "order-processor")
AsyncRedisStreamer(redis_instance, "email-notification-service")
AsyncRedisStreamer(redis_instance, "inventory-sync-worker")

# Avoid: Generic or unclear names
AsyncRedisStreamer(redis_instance, "consumer1")
AsyncRedisStreamer(redis_instance, "worker")
```

### 3. Register Channels with Appropriate Retention

```python
streamer = AsyncRedisStreamer(redis_instance, "service")

# Match retention to data importance and volume
streamer.register_channel("ephemeral-metrics", retention_ms=1*60*60*1000)  # 1h
streamer.register_channel("user-events", retention_ms=7*24*60*60*1000)     # 7d
streamer.register_channel("audit-logs", retention_ms=90*24*60*60*1000)     # 90d
```

### 4. Implement Proper Error Handling in Handlers

```python
async def safe_handler(name: str, payload: Dict[str, Any]) -> None:
    """Handler with proper error handling."""
    try:
        # Validate payload
        if "required_field" not in payload:
            raise ValueError("Missing required field")
        
        # Process message
        await process_message(payload)
        
    except ValueError as e:
        # Log validation errors
        print(f"Validation error: {e}")
        # Don't re-raise - message will be ACKed
        
    except Exception as e:
        # Log unexpected errors
        print(f"Processing error: {e}")
        # Re-raise to trigger dead letter logging
        raise
```

### 5. Use Method Chaining for Clean Setup

```python
streamer = (
    AsyncRedisStreamer(redis_instance, "service")
    .register_channel("orders", retention_ms=24*60*60*1000)
    .register_handler("orders", handle_order)
    .register_channel("users", retention_ms=7*24*60*60*1000)
    .register_handler("users", handle_user)
)
```

## Performance Considerations

### Memory Usage

The deduplication ZSET grows with message volume:

```text
Memory per message ID ≈ 100 bytes
1M messages = ~100MB

For 1000 msg/sec:
- 1 hour window: 3.6M messages = ~360MB
- 24 hour window: 86.4M messages = ~8.6GB
- 7 day window: 604.8M messages = ~60GB
```

Choose appropriate deduplication windows based on your memory constraints.

### Cleanup Frequency

Default cleanup runs every 5 minutes. Adjust based on needs:

```python
# Adjust cleanup interval in subclass implementation
streamer._ledger_cleanup_interval = 10 * 60 * 1000  # 10 minutes
```

### Handler Efficiency

Multiple handlers on the same channel are called sequentially:

```python
# All handlers must complete before message is ACKed
streamer.register_handler("orders", handler1)  # Fast: 10ms
streamer.register_handler("orders", handler2)  # Slow: 500ms
# Total time per message: 510ms
```

For better performance, use a single handler that coordinates sub-tasks.

## Troubleshooting

### Issue: Consumer Instance Name Conflicts

**Symptom**: Messages are processed by unexpected consumers

**Solution**: Ensure unique hostnames/pod names:

```python
import os

# In Kubernetes, set POD_NAME in deployment
os.environ["POD_NAME"] = "my-service-pod-abc123"

# Verify generated name
instance_name = CommonMethods._consumer_name_generator("my-service")
print(f"Instance: {instance_name}")
```

### Issue: Memory Growth from Deduplication ZSET

**Symptom**: Redis memory usage grows unbounded

**Solution**: Reduce deduplication window or increase cleanup frequency:

```python
# Reduce window
streamer = AsyncRedisStreamer(
    redis_instance,
    "service",
    dedup_window_ms=1 * 60 * 60 * 1000  # 1 hour instead of 7 days
)

# Or monitor ZSET size
# ZCARD stream:channel:group:groupname:processed
```

### Issue: Messages Not Routing to Handlers

**Symptom**: Handlers not being called for received messages

**Solution**: Verify handler registration matches subscription:

```python
# Channel and listener must match
streamer.subscribe("orders")  # Uses default listener_name
streamer.register_handler("orders", my_handler)  # Must use same listener

# Or specify explicitly
streamer.register_handler("orders", my_handler, listener_name=streamer.listener_name)
```

## Related Documentation

- [Message](message.md) - Message data structure
- [AsyncRedisStreamer](asynchronize.md) - Async consumer implementation
- [RedisStreamer](synchronize.md) - Synchronous consumer implementation
- [Redis Connection](../redis/connection.md) - Redis connection management
- [Logging](../log/footprint.md) - Footprint logging system

## External References

- [Redis Streams Documentation](https://redis.io/docs/data-types/streams/)
- [Redis Consumer Groups](https://redis.io/docs/data-types/streams/#consumer-groups)
- [Redis ZADD Command](https://redis.io/commands/zadd/)
- [Redis ZREMRANGEBYSCORE](https://redis.io/commands/zremrangebyscore/)
