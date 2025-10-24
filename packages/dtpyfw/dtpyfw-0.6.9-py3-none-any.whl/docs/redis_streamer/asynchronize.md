# dtpyfw.redis_streamer.asynchronize

## Overview

The `asynchronize` module provides the `AsyncRedisStreamer` class, an asynchronous Redis Streams consumer with comprehensive features for distributed message processing. It implements decoupled fan-out across microservices, bounded at-most-once delivery guarantees, connection pooling, automatic reconnection, and adaptive sleeping to reduce network load. This class is designed for high-performance async applications using Python's `asyncio` framework.

## Module Information

- **Module Path**: `dtpyfw.redis_streamer.asynchronize`
- **Class**: `AsyncRedisStreamer`
- **Dependencies**:
  - `redis.asyncio` - Async Redis client
  - `asyncio` - Python async framework
  - `dtpyfw.redis.connection` - Redis connection management
  - `dtpyfw.log.footprint` - Logging utilities
  - `dtpyfw.core.retry` - Retry wrapper utilities
  - `dtpyfw.core.exception` - Exception handling utilities
- **Base Class**: `CommonMethods`
- **Async/Await**: Full async support with context manager

## AsyncRedisStreamer Class

The `AsyncRedisStreamer` class provides a complete asynchronous Redis Streams consumer with enterprise-grade features.

### Key Features

- ✅ **Async/Await Support**: Non-blocking I/O operations using Python asyncio
- ✅ **Consumer Groups**: Decoupled fan-out across multiple microservices
- ✅ **At-Most-Once Delivery**: ZSET-based deduplication within configurable time windows
- ✅ **Automatic Reconnection**: Exponential backoff retry on connection failures
- ✅ **Connection Pooling**: Efficient connection reuse via Redis connection pools
- ✅ **Adaptive Sleeping**: Reduces network load during idle periods
- ✅ **Background Maintenance**: Automatic cleanup of expired deduplication entries
- ✅ **Channel Retention**: Configurable message retention policies per channel
- ✅ **Dead Letter Logging**: Comprehensive error tracking for failed messages
- ✅ **Context Manager**: Automatic resource cleanup with async context manager

### Class Signature

```python
class AsyncRedisStreamer(CommonMethods):
    """
    Asynchronous Redis Streams consumer with:
      - Decoupled fan-out across microservices (one group per service).
      - Bounded at-most-once (per group) via a ZSET de-dup window.
      - Lower network load using adaptive sleeping.
      - Connection pooling for efficient connection reuse.
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
    """Initialize asynchronous Redis Streams consumer.

    Args:
        redis_instance (RedisInstance): The Redis connection manager.
        consumer_name (str): The logical name of the consumer service.
        dedup_window_ms (int, optional): Time window in milliseconds for
            deduplication tracking. Defaults to 7 days (604800000 ms).
    """
```

#### Parameters

| Parameter         | Type            | Required | Default      | Description                                                    |
|-------------------|-----------------|----------|--------------|----------------------------------------------------------------|
| `redis_instance`  | `RedisInstance` | Yes      | -            | Redis connection manager for accessing Redis Streams           |
| `consumer_name`   | `str`           | Yes      | -            | Logical name of the consumer service (auto-sanitized)          |
| `dedup_window_ms` | `int`           | No       | `604800000`  | Deduplication window in milliseconds (default: 7 days)         |

### Instance Attributes

In addition to inherited attributes from `CommonMethods`:

| Attribute                   | Type                    | Description                                                    |
|-----------------------------|-------------------------|----------------------------------------------------------------|
| `_redis_client`             | `Optional[AsyncRedis]`  | Async Redis client instance (lazily initialized)               |
| `_maintenance_task`         | `Optional[asyncio.Task]`| Background task for deduplication cleanup                      |
| `_cleanup_channels_task`    | `Optional[asyncio.Task]`| Background task for channel retention cleanup                  |

## Methods

### Connection Management

#### `_get_client()`

```python
async def _get_client(self) -> AsyncRedis:
    """Lazily initialize and return the async Redis client.

    Description:
        Retrieves the async Redis client, initializing it on first access.
        Subsequent calls return the existing client instance.

    Returns:
        AsyncRedis: The async Redis client instance.
    """
```

**Usage**:

```python
client = await streamer._get_client()
await client.ping()  # Use Redis client directly
```

---

#### `_reconnect()`

```python
async def _reconnect(self) -> None:
    """Attempt to reconnect to Redis with exponential backoff retries.

    Description:
        Handles Redis connection failures by closing the existing client,
        resetting the connection pool, and attempting to reconnect up to
        3 times with exponential backoff delays between attempts.

    Raises:
        ConnectionError: If reconnection fails after 3 attempts.
    """
```

**Retry Logic**:

- Attempt 1: Immediate
- Attempt 2: After 2^0 = 1 second
- Attempt 3: After 2^1 = 2 seconds
- Failure: Raises `ConnectionError` after 2^2 = 4 seconds

---

### Subscription Management

#### `subscribe()`

```python
async def subscribe(
    self, channel_name: str, start_from_latest: bool = True
) -> "AsyncRedisStreamer":
    """Subscribe to a Redis stream channel asynchronously.

    Description:
        Creates a consumer group for the channel if it doesn't exist and
        registers the subscription for later message consumption. The
        consumer group enables decoupled fan-out across microservices.

    Args:
        channel_name (str): The Redis stream channel name to subscribe to.
        start_from_latest (bool, optional): If True, start consuming from
            new messages only ($). If False, consume from beginning (0-0).
            Defaults to True.

    Returns:
        AsyncRedisStreamer: Returns self for method chaining.

    Raises:
        Exception: Re-raises Redis exceptions after reconnection attempt.
    """
```

**Example**:

```python
streamer = AsyncRedisStreamer(redis_instance, "order-processor")

# Subscribe to new messages only
await streamer.subscribe("orders", start_from_latest=True)

# Subscribe and process all historical messages
await streamer.subscribe("audit-logs", start_from_latest=False)

# Chain multiple subscriptions
await (streamer
    .subscribe("orders")
    .subscribe("payments")
    .subscribe("notifications"))
```

---

#### `_consumer_group_exists()`

```python
async def _consumer_group_exists(
    self, channel_name: str, consumer_group: str
) -> bool:
    """Check if a consumer group exists for a channel.

    Args:
        channel_name (str): The Redis stream channel name.
        consumer_group (str): The consumer group identifier.

    Returns:
        bool: True if the consumer group exists, False otherwise.
    """
```

---

### Message Publishing

#### `send_message()`

```python
async def send_message(self, channel: str, message: Message) -> None:
    """Send a message to a Redis stream channel asynchronously.

    Description:
        Publishes a message to the specified channel using Redis XADD.
        The message is JSON-encoded before transmission. This method
        supports async/await patterns for non-blocking I/O operations.

    Args:
        channel (str): The Redis stream channel name where the message
            will be published.
        message (Message): The message object to send containing the
            event name and payload data.

    Raises:
        Exception: Re-raises Redis exceptions after reconnection attempt.
    """
```

**Example**:

```python
from dtpyfw.redis_streamer.message import Message

async def publish_order():
    streamer = AsyncRedisStreamer(redis_instance, "publisher")
    
    message = Message(
        name="order.created",
        body={
            "order_id": "ORD-123",
            "customer_id": 456,
            "total": 99.99
        }
    )
    
    await streamer.send_message("orders", message)
    print("Order message published!")

await publish_order()
```

---

### Message Consumption

#### `persist_consume()`

```python
async def persist_consume(
    self,
    rest_time: float = 0.1,
    block_time: float = 5.0,
    count: int = 32,
    cleanup_interval: float = 300.0,
) -> None:
    """Continuously consume messages from all subscribed channels.

    Description:
        Launches consumer tasks for each subscribed channel, starts
        background maintenance tasks for deduplication cleanup and
        channel retention, and monitors task health. Automatically
        restarts crashed tasks to ensure continuous operation.

    Args:
        rest_time (float, optional): Base sleep duration in seconds between
            consume cycles during idle periods. Defaults to 0.1.
        block_time (float, optional): Maximum seconds to block waiting for
            messages in each XREADGROUP call. Defaults to 5.0.
        count (int, optional): Maximum messages to read per batch from
            each channel. Defaults to 32.
        cleanup_interval (float, optional): Seconds between channel cleanup
            runs for retention management. Defaults to 300.0 (5 minutes).
    """
```

**Parameters Explained**:

- **`rest_time`**: Base sleep between consume cycles. Doubled during idle periods up to 2.0s max
- **`block_time`**: Redis XREADGROUP blocking timeout. Lower = more responsive, higher = less network overhead
- **`count`**: Batch size for message consumption. Higher = more throughput but longer processing time
- **`cleanup_interval`**: How often to trim old messages based on retention policies

**Example**:

```python
async def run_consumer():
    streamer = AsyncRedisStreamer(redis_instance, "order-processor")
    
    # Register handler
    async def process_order(name: str, payload: Dict[str, Any]):
        print(f"Processing: {name}")
        # Business logic here
    
    # Setup
    await streamer.subscribe("orders")
    streamer.register_handler("orders", process_order)
    
    # Start consuming (runs forever)
    await streamer.persist_consume(
        rest_time=0.1,        # 100ms base sleep
        block_time=5.0,       # 5s blocking wait
        count=32,             # 32 messages per batch
        cleanup_interval=300  # Cleanup every 5 minutes
    )

asyncio.run(run_consumer())
```

---

#### `_consume_one()`

```python
async def _consume_one(
    self,
    channel: str,
    consumer_group: str,
    listener_name: str,
    block_time: float,
    count: int = 32,
) -> None:
    """Consume and process a batch of messages from a Redis stream.

    Description:
        Reads a batch of messages from the stream using XREADGROUP,
        deduplicates them using ZSET-based tracking, decodes their payloads,
        invokes registered handlers, and acknowledges successful processing.
        Handles errors by logging to dead letter and re-subscribing if needed.

    Args:
        channel (str): The Redis stream channel name to consume from.
        consumer_group (str): The consumer group identifier for this consumer.
        listener_name (str): The logical consumer service name for routing.
        block_time (float): Maximum seconds to block waiting for messages.
        count (int, optional): Maximum messages to read per batch. Defaults to 32.
    """
```

**Processing Flow**:

1. **Read**: `XREADGROUP` fetches up to `count` messages
2. **Deduplicate**: Each message ID checked against ZSET
3. **Decode**: JSON decode message name and body
4. **Route**: Call all registered handlers for the channel
5. **Acknowledge**: `XACK` marks message as processed
6. **Error Handling**: Failed messages logged to dead letter

---

#### `_consume_loop()`

```python
async def _consume_loop(
    self,
    channel: str,
    listener: str,
    group: str,
    block_time: float,
    count: int,
    rest_time: float,
) -> None:
    """Dedicated async loop for consuming messages from a channel.

    Description:
        Continuously polls the channel for new messages, processes them,
        and implements adaptive sleep with exponential backoff during
        idle periods to reduce network load. Handles reconnections on errors.
        Runs indefinitely until the task is cancelled or the application exits.

    Args:
        channel (str): The Redis stream channel name to monitor.
        listener (str): The logical consumer service name for this consumer.
        group (str): The consumer group identifier for coordination.
        block_time (float): Maximum seconds to block waiting for messages.
        count (int): Maximum messages to read per batch.
        rest_time (float): Base sleep duration in seconds between consume cycles.
    """
```

**Adaptive Sleep Logic**:

```python
# If message batch took less than block_time (quick return = no messages)
if elapsed < block_time:
    idle_backoff = min(idle_backoff * 2, 2.0)  # Double up to 2s max
else:
    idle_backoff = rest_time  # Reset to base
```

---

### Deduplication

#### `_reserve_once()`

```python
async def _reserve_once(
    self, processed_key: str, message_id: str, now_ms: int
) -> bool:
    """Attempt to reserve a message ID for processing using ZSET.

    Description:
        Uses Redis ZADD with NX flag to atomically reserve a message ID
        for processing. This ensures at-most-once delivery within the
        consumer group by preventing duplicate processing.

    Args:
        processed_key (str): The Redis ZSET key for tracking processed messages.
        message_id (str): The Redis stream message ID to reserve.
        now_ms (int): Current timestamp in milliseconds for the ZSET score.

    Returns:
        bool: True if the message was successfully reserved, False if already processed.
    """
```

**Redis Command**:

```redis
ZADD stream:channel:group:groupname:processed NX 1729768245123 "1729768245123-0"
```

**Returns**:

- `1` (True): Message reserved, proceed with processing
- `0` (False): Message already processed, skip

---

#### `_ack_message()`

```python
async def _ack_message(self, channel: str, group: str, message_id: str) -> None:
    """Acknowledge a message as processed in Redis stream.

    Description:
        Sends an XACK command to Redis to mark the message as successfully
        processed by the consumer group. This prevents the message from
        being redelivered to other consumers in the group.

    Args:
        channel (str): The Redis stream channel name containing the message.
        group (str): The consumer group identifier that processed the message.
        message_id (str): The Redis stream message ID to acknowledge.
    """
```

---

### Maintenance Tasks

#### `maintain_ledgers()`

```python
async def maintain_ledgers(self) -> None:
    """Clean up expired deduplication ZSET entries asynchronously.

    Description:
        Removes message IDs from the deduplication ZSETs that have
        exceeded the configured deduplication window. This prevents
        unbounded memory growth while maintaining at-most-once guarantees
        within the window.
    """
```

**Example Redis Command**:

```redis
ZREMRANGEBYSCORE stream:orders:group:orders:processor:cg:processed -inf (1729168245123)
```

---

#### `_maintenance_loop()`

```python
async def _maintenance_loop(self) -> None:
    """Background async task for periodic deduplication maintenance.

    Description:
        Runs continuously, sleeping for the configured interval and
        then triggering ledger cleanup to remove expired deduplication
        entries. Handles errors gracefully with reconnection attempts.
    """
```

---

#### `cleanup_channels()`

```python
async def cleanup_channels(self) -> None:
    """Clean up old messages from channels based on retention period.

    Description:
        For each registered channel with a retention configuration,
        removes messages older than the retention window using XTRIM.
        This helps manage memory usage for high-throughput channels.
    """
```

**Example Redis Command**:

```redis
XTRIM orders MINID 1729168245123 APPROXIMATE
```

---

#### `_cleanup_channels_loop()`

```python
async def _cleanup_channels_loop(self, cleanup_interval: float = 300.0) -> None:
    """Background async task for periodic channel cleanup.

    Args:
        cleanup_interval (float, optional): Seconds between cleanup runs.
            Defaults to 300.0 (5 minutes).
    """
```

---

### Resource Management

#### `stop_consuming()`

```python
async def stop_consuming(self) -> None:
    """Stop all consuming tasks and clean up async resources.

    Description:
        Cancels and awaits completion of maintenance and cleanup tasks,
        then closes the Redis client connection. Used internally by
        cleanup() and can be called directly for graceful shutdown.
    """
```

---

#### `cleanup()`

```python
async def cleanup(self) -> None:
    """Clean up async resources and stop all background tasks.

    Description:
        Stops all consumer tasks, maintenance tasks, and cleanup tasks,
        and closes the Redis client connection. Should be called before
        terminating the application or when using as a context manager.
    """
```

---

### Statistics and Monitoring

#### `get_stats()`

```python
async def get_stats(self) -> Dict[str, Any]:
    """Get current statistics and state information about the streamer.

    Returns:
        Dict[str, Any]: Statistics including listener_name, consumer_instance,
            subscriptions count, channels list, dedup_window_ms,
            last_ledger_cleanup timestamp, and maintenance_running status.
    """
```

**Example Output**:

```python
{
    "listener_name": "order-processor",
    "consumer_instance": "order-processor.pod-abc.12345.a1b2c3d4",
    "subscriptions": 2,
    "channels": ["orders", "payments"],
    "dedup_window_ms": 604800000,
    "last_ledger_cleanup": 1729768245123,
    "maintenance_running": True
}
```

---

### Context Manager Support

#### `__aenter__()` and `__aexit__()`

```python
async def __aenter__(self) -> "AsyncRedisStreamer":
    """Async context manager entry point."""
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb) -> Optional[bool]:
    """Async context manager exit with automatic cleanup."""
    await self.cleanup()
    return False
```

**Usage**:

```python
async with AsyncRedisStreamer(redis_instance, "service") as streamer:
    await streamer.subscribe("channel")
    streamer.register_handler("channel", my_handler)
    await streamer.persist_consume()
# Automatic cleanup on exit
```

---

## Complete Usage Examples

### Example 1: Basic Async Consumer

```python
import asyncio
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer
from dtpyfw.redis_streamer.message import Message
from typing import Dict, Any

async def process_order(name: str, payload: Dict[str, Any]) -> None:
    """Handler for order events."""
    print(f"Processing {name}: Order ID {payload.get('order_id')}")
    # Add your business logic here
    await asyncio.sleep(0.1)  # Simulate processing

async def main():
    # Initialize Redis connection
    redis_instance = RedisInstance(
        host="localhost",
        port=6379,
        db=0
    )
    
    # Create consumer
    streamer = AsyncRedisStreamer(
        redis_instance=redis_instance,
        consumer_name="order-processor",
        dedup_window_ms=24 * 60 * 60 * 1000  # 24 hours
    )
    
    # Subscribe to channel
    await streamer.subscribe("orders", start_from_latest=True)
    
    # Register handler
    streamer.register_handler("orders", process_order)
    
    # Start consuming
    await streamer.persist_consume()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Multiple Channels with Different Handlers

```python
import asyncio
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer
from typing import Dict, Any

async def handle_order(name: str, payload: Dict[str, Any]) -> None:
    """Process order events."""
    if name == "order.created":
        print(f"New order: {payload['order_id']}")
    elif name == "order.updated":
        print(f"Updated order: {payload['order_id']}")

async def handle_payment(name: str, payload: Dict[str, Any]) -> None:
    """Process payment events."""
    if name == "payment.succeeded":
        print(f"Payment successful: {payload['payment_id']}")
    elif name == "payment.failed":
        print(f"Payment failed: {payload['payment_id']}")

async def handle_notification(name: str, payload: Dict[str, Any]) -> None:
    """Process notification events."""
    print(f"Sending notification: {payload['type']}")

async def main():
    streamer = AsyncRedisStreamer(redis_instance, "multi-service")
    
    # Subscribe to multiple channels
    await streamer.subscribe("orders")
    await streamer.subscribe("payments")
    await streamer.subscribe("notifications")
    
    # Register handlers
    streamer.register_handler("orders", handle_order)
    streamer.register_handler("payments", handle_payment)
    streamer.register_handler("notifications", handle_notification)
    
    # Start consuming
    await streamer.persist_consume()

asyncio.run(main())
```

### Example 3: Publisher-Consumer Pattern

```python
import asyncio
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer
from dtpyfw.redis_streamer.message import Message

async def publisher():
    """Publish messages to Redis Streams."""
    streamer = AsyncRedisStreamer(redis_instance, "publisher")
    
    for i in range(10):
        message = Message(
            name="task.created",
            body={
                "task_id": f"TASK-{i:03d}",
                "priority": i % 3,
                "created_at": str(asyncio.get_event_loop().time())
            }
        )
        await streamer.send_message("tasks", message)
        print(f"Published task {i}")
        await asyncio.sleep(1)

async def consumer():
    """Consume messages from Redis Streams."""
    streamer = AsyncRedisStreamer(redis_instance, "worker")
    
    async def process_task(name: str, payload: Dict[str, Any]):
        task_id = payload['task_id']
        priority = payload['priority']
        print(f"Processing {task_id} (priority: {priority})")
        await asyncio.sleep(0.5)  # Simulate work
    
    await streamer.subscribe("tasks")
    streamer.register_handler("tasks", process_task)
    await streamer.persist_consume()

async def main():
    # Run publisher and consumer concurrently
    await asyncio.gather(
        publisher(),
        consumer()
    )

asyncio.run(main())
```

### Example 4: Error Handling and Dead Letter

```python
import asyncio
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer
from typing import Dict, Any

async def safe_handler(name: str, payload: Dict[str, Any]) -> None:
    """Handler with comprehensive error handling."""
    try:
        # Validate payload
        required_fields = ["id", "type", "data"]
        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
        
        # Process message
        print(f"Processing {name}: {payload['id']}")
        
        # Simulate processing
        if payload["type"] == "error-test":
            raise RuntimeError("Simulated processing error")
        
        await asyncio.sleep(0.1)
        print(f"Successfully processed {payload['id']}")
        
    except ValueError as e:
        # Validation errors - log and skip
        print(f"Validation error: {e}")
        # Message will be ACKed (not reprocessed)
        
    except Exception as e:
        # Processing errors - log to dead letter
        print(f"Processing error: {e}")
        # Re-raise to trigger dead letter logging
        raise

async def main():
    streamer = AsyncRedisStreamer(redis_instance, "error-handler")
    
    await streamer.subscribe("events")
    streamer.register_handler("events", safe_handler)
    
    await streamer.persist_consume()

asyncio.run(main())
```

### Example 5: Context Manager Pattern

```python
import asyncio
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

async def process_event(name: str, payload: Dict[str, Any]) -> None:
    print(f"Event: {name}")

async def main():
    # Automatic cleanup on exit
    async with AsyncRedisStreamer(redis_instance, "service") as streamer:
        await streamer.subscribe("events")
        streamer.register_handler("events", process_event)
        
        try:
            await streamer.persist_consume()
        except KeyboardInterrupt:
            print("Shutting down gracefully...")
            # cleanup() called automatically

asyncio.run(main())
```

### Example 6: Channel Retention Management

```python
import asyncio
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

async def main():
    streamer = AsyncRedisStreamer(redis_instance, "retention-service")
    
    # High-volume metrics with short retention
    streamer.register_channel(
        "metrics.cpu",
        retention_ms=1 * 60 * 60 * 1000  # 1 hour
    )
    
    # User events with medium retention
    streamer.register_channel(
        "user.activity",
        retention_ms=7 * 24 * 60 * 60 * 1000  # 7 days
    )
    
    # Audit logs with long retention
    streamer.register_channel(
        "audit.logs",
        retention_ms=90 * 24 * 60 * 60 * 1000  # 90 days
    )
    
    # Subscribe to channels
    await streamer.subscribe("metrics.cpu")
    await streamer.subscribe("user.activity")
    await streamer.subscribe("audit.logs")
    
    # Handlers...
    streamer.register_handler("metrics.cpu", handle_metrics)
    streamer.register_handler("user.activity", handle_activity)
    streamer.register_handler("audit.logs", handle_audit)
    
    # Start with custom cleanup interval
    await streamer.persist_consume(cleanup_interval=60.0)  # Every minute

asyncio.run(main())
```

### Example 7: Multi-Handler Pattern

```python
import asyncio
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer
from typing import Dict, Any

async def logger(name: str, payload: Dict[str, Any]) -> None:
    """Log all events."""
    print(f"[LOG] {name}: {payload}")

async def metrics_collector(name: str, payload: Dict[str, Any]) -> None:
    """Collect metrics for all events."""
    # Send to metrics system
    print(f"[METRICS] Recorded event: {name}")

async def business_logic(name: str, payload: Dict[str, Any]) -> None:
    """Main business processing."""
    print(f"[PROCESS] Handling: {name}")
    # Actual processing logic

async def main():
    streamer = AsyncRedisStreamer(redis_instance, "multi-handler")
    
    await streamer.subscribe("orders")
    
    # Register multiple handlers - all will be called sequentially
    streamer.register_handler("orders", logger)
    streamer.register_handler("orders", metrics_collector)
    streamer.register_handler("orders", business_logic)
    
    await streamer.persist_consume()

asyncio.run(main())
```

### Example 8: Historical Message Processing

```python
import asyncio
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

async def backfill_processor(name: str, payload: Dict[str, Any]) -> None:
    """Process historical messages."""
    print(f"Backfilling: {name} - {payload.get('timestamp')}")

async def main():
    streamer = AsyncRedisStreamer(redis_instance, "backfill-service")
    
    # Subscribe from the beginning to process all historical messages
    await streamer.subscribe("orders", start_from_latest=False)
    
    streamer.register_handler("orders", backfill_processor)
    
    # Process with higher batch size for throughput
    await streamer.persist_consume(
        count=100,          # Larger batches
        block_time=1.0,     # Shorter block time
        rest_time=0.0       # No rest between batches
    )

asyncio.run(main())
```

### Example 9: Statistics Monitoring

```python
import asyncio
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

async def monitor_stats(streamer: AsyncRedisStreamer):
    """Periodically log consumer statistics."""
    while True:
        await asyncio.sleep(60)  # Every minute
        stats = await streamer.get_stats()
        print(f"Consumer Stats:")
        print(f"  Instance: {stats['consumer_instance']}")
        print(f"  Channels: {stats['channels']}")
        print(f"  Subscriptions: {stats['subscriptions']}")
        print(f"  Maintenance: {stats.get('maintenance_running', False)}")
        print(f"  Last Cleanup: {stats['last_ledger_cleanup']}")

async def process_message(name: str, payload: Dict[str, Any]) -> None:
    print(f"Processing: {name}")

async def main():
    streamer = AsyncRedisStreamer(redis_instance, "monitored-service")
    
    await streamer.subscribe("events")
    streamer.register_handler("events", process_message)
    
    # Run monitoring and consumption concurrently
    await asyncio.gather(
        streamer.persist_consume(),
        monitor_stats(streamer)
    )

asyncio.run(main())
```

### Example 10: Graceful Shutdown

```python
import asyncio
import signal
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer

class GracefulConsumer:
    def __init__(self, redis_instance, consumer_name):
        self.streamer = AsyncRedisStreamer(redis_instance, consumer_name)
        self.shutdown_event = asyncio.Event()
    
    async def handle_message(self, name: str, payload: Dict[str, Any]) -> None:
        print(f"Processing: {name}")
        await asyncio.sleep(0.1)
    
    async def run(self):
        """Run consumer with graceful shutdown support."""
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.shutdown())
            )
        
        # Setup consumer
        await self.streamer.subscribe("orders")
        self.streamer.register_handler("orders", self.handle_message)
        
        # Run consumption with shutdown monitoring
        consume_task = asyncio.create_task(
            self.streamer.persist_consume()
        )
        shutdown_task = asyncio.create_task(
            self.shutdown_event.wait()
        )
        
        # Wait for shutdown signal
        await shutdown_task
        
        # Cancel consumption
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass
        
        # Cleanup
        await self.streamer.cleanup()
        print("Shutdown complete")
    
    async def shutdown(self):
        """Trigger graceful shutdown."""
        print("Shutdown signal received...")
        self.shutdown_event.set()

async def main():
    consumer = GracefulConsumer(redis_instance, "graceful-service")
    await consumer.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Architecture Patterns

### Fan-Out Pattern

Multiple independent services consume all messages:

```python
# Order Processor Service
order_processor = AsyncRedisStreamer(redis_instance, "order-processor")
await order_processor.subscribe("orders")
order_processor.register_handler("orders", process_order)

# Inventory Service
inventory_service = AsyncRedisStreamer(redis_instance, "inventory-service")
await inventory_service.subscribe("orders")
inventory_service.register_handler("orders", update_inventory)

# Analytics Service
analytics_service = AsyncRedisStreamer(redis_instance, "analytics-service")
await analytics_service.subscribe("orders")
analytics_service.register_handler("orders", track_metrics)

# All three services receive ALL messages from "orders" channel
```

### Load Balancing Pattern

Multiple instances of the same service share workload:

```python
# Deploy 3 instances with same consumer_name
# Redis will distribute messages across instances within the group

# Instance 1 (pod-1)
streamer1 = AsyncRedisStreamer(redis_instance, "order-processor")

# Instance 2 (pod-2)
streamer2 = AsyncRedisStreamer(redis_instance, "order-processor")

# Instance 3 (pod-3)
streamer3 = AsyncRedisStreamer(redis_instance, "order-processor")

# Each instance processes different messages (load balanced)
```

### Event Sourcing Pattern

```python
async def event_handler(name: str, payload: Dict[str, Any]) -> None:
    """Handle events in event sourcing pattern."""
    if name == "order.created":
        await create_order_aggregate(payload)
    elif name == "order.item.added":
        await add_item_to_order(payload)
    elif name == "order.shipped":
        await mark_order_shipped(payload)

streamer = AsyncRedisStreamer(redis_instance, "event-sourced-service")
await streamer.subscribe("order-events", start_from_latest=False)
streamer.register_handler("order-events", event_handler)
```

## Performance Tuning

### Batch Size Optimization

```python
# High-throughput scenario
await streamer.persist_consume(
    count=100,        # Process 100 messages per batch
    block_time=1.0,   # Quick timeout
    rest_time=0.0     # No sleep between batches
)

# Low-latency scenario
await streamer.persist_consume(
    count=1,          # Process 1 message at a time
    block_time=0.1,   # Very quick timeout
    rest_time=0.0     # Immediate processing
)

# Balanced scenario (default)
await streamer.persist_consume(
    count=32,         # Moderate batch size
    block_time=5.0,   # Standard timeout
    rest_time=0.1     # Small sleep
)
```

### Memory Management

```python
# Memory-constrained environment
streamer = AsyncRedisStreamer(
    redis_instance,
    "memory-optimized",
    dedup_window_ms=1 * 60 * 60 * 1000  # 1 hour dedup window
)

# Register channels with aggressive retention
streamer.register_channel("channel", retention_ms=1*60*60*1000)

# Frequent cleanup
await streamer.persist_consume(cleanup_interval=60.0)  # Every minute
```

### Network Optimization

```python
# Reduce network roundtrips
await streamer.persist_consume(
    count=64,         # Larger batches
    block_time=10.0,  # Longer blocking
    rest_time=0.5     # More rest between cycles
)
```

## Best Practices

### 1. Use Async Handlers

```python
# Good: Async handler
async def good_handler(name: str, payload: Dict[str, Any]) -> None:
    result = await async_operation(payload)
    await another_async_operation(result)

# Also works: Sync handler (but blocks event loop)
def sync_handler(name: str, payload: Dict[str, Any]) -> None:
    result = blocking_operation(payload)
```

### 2. Implement Proper Error Handling

```python
async def robust_handler(name: str, payload: Dict[str, Any]) -> None:
    try:
        # Validate
        validate_payload(payload)
        
        # Process
        await process(payload)
        
    except ValidationError as e:
        # Don't re-raise validation errors
        log_validation_error(e)
        
    except Exception as e:
        # Re-raise for dead letter logging
        log_error(e)
        raise
```

### 3. Monitor Consumer Health

```python
async def health_check(streamer: AsyncRedisStreamer):
    while True:
        stats = await streamer.get_stats()
        if not stats.get('maintenance_running'):
            alert("Maintenance task died!")
        await asyncio.sleep(60)
```

### 4. Use Context Managers

```python
# Good: Automatic cleanup
async with AsyncRedisStreamer(redis_instance, "service") as streamer:
    await streamer.subscribe("channel")
    streamer.register_handler("channel", handler)
    await streamer.persist_consume()
```

### 5. Configure Appropriate Dedup Windows

```python
# Critical financial operations: Long window
payment_processor = AsyncRedisStreamer(
    redis_instance,
    "payments",
    dedup_window_ms=30 * 24 * 60 * 60 * 1000  # 30 days
)

# High-volume metrics: Short window
metrics_processor = AsyncRedisStreamer(
    redis_instance,
    "metrics",
    dedup_window_ms=1 * 60 * 60 * 1000  # 1 hour
)
```

## Troubleshooting

### Issue: Messages Not Being Consumed

**Symptoms**:
- `persist_consume()` starts but no messages are processed
- No errors in logs

**Solutions**:

```python
# 1. Check subscription
await streamer.subscribe("correct-channel-name")

# 2. Verify handler registration
streamer.register_handler("correct-channel-name", handler)

# 3. Check consumer group exists
# Use Redis CLI: XINFO GROUPS channel-name

# 4. Verify messages exist in stream
# Use Redis CLI: XLEN channel-name
```

### Issue: Duplicate Message Processing

**Symptoms**:
- Same message processed multiple times
- Deduplication not working

**Solutions**:

```python
# 1. Ensure same consumer_name for instances
streamer = AsyncRedisStreamer(redis_instance, "same-name")

# 2. Check dedup window is sufficient
streamer = AsyncRedisStreamer(
    redis_instance,
    "service",
    dedup_window_ms=24 * 60 * 60 * 1000  # Increase window
)

# 3. Verify maintenance task is running
stats = await streamer.get_stats()
print(stats['maintenance_running'])  # Should be True
```

### Issue: High Memory Usage

**Symptoms**:
- Redis memory grows unbounded
- ZSET keys consuming too much memory

**Solutions**:

```python
# 1. Reduce dedup window
streamer = AsyncRedisStreamer(
    redis_instance,
    "service",
    dedup_window_ms=1 * 60 * 60 * 1000  # 1 hour instead of 7 days
)

# 2. Enable channel retention
streamer.register_channel("channel", retention_ms=24*60*60*1000)

# 3. Increase cleanup frequency
await streamer.persist_consume(cleanup_interval=60.0)
```

### Issue: Connection Timeouts

**Symptoms**:
- Frequent reconnection attempts
- `ConnectionError` exceptions

**Solutions**:

```python
# 1. Increase Redis connection timeout
redis_instance = RedisInstance(
    host="localhost",
    port=6379,
    socket_timeout=30  # Increase timeout
)

# 2. Check Redis server health
# 3. Verify network connectivity
```

### Issue: Slow Message Processing

**Symptoms**:
- Messages backing up in stream
- High consumer lag

**Solutions**:

```python
# 1. Increase batch size
await streamer.persist_consume(count=100)

# 2. Optimize handler performance
async def optimized_handler(name: str, payload: Dict[str, Any]) -> None:
    # Use connection pooling
    # Batch database operations
    # Cache frequently accessed data
    pass

# 3. Scale horizontally (more consumer instances)
```

## Related Documentation

- [Message](message.md) - Message data structure
- [CommonMethods](common.md) - Base class with shared utilities
- [RedisStreamer](synchronize.md) - Synchronous consumer implementation
- [Redis Connection](../redis/connection.md) - Redis connection management
- [Logging](../log/footprint.md) - Footprint logging system

## External References

- [Redis Streams Documentation](https://redis.io/docs/data-types/streams/)
- [Redis Consumer Groups](https://redis.io/docs/data-types/streams/#consumer-groups)
- [Python Asyncio](https://docs.python.org/3/library/asyncio.html)
- [Redis-py Async](https://redis-py.readthedocs.io/en/stable/examples/asyncio_examples.html)
