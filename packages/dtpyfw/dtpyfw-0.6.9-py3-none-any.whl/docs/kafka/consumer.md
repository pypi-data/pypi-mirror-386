# Consumer

## Overview

`Consumer` is a high-level Kafka consumer class that simplifies message consumption by allowing registration of topic-specific message handler functions. It manages polling, message dispatching, and optional manual offset committing with integrated error handling and logging.

## Module Location

```python
from dtpyfw.kafka.consumer import Consumer
```

## Class Definition

```python
class Consumer:
    """High-level Kafka consumer with topic-specific message handlers."""
```

## Dependencies

```python
from kafka import KafkaConsumer
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.core.exception import exception_to_dict
from dtpyfw.log import footprint
```

**Type Aliases:**

```python
MessageHandler = Callable[..., None]
```

## Constructor

### `__init__(kafka_instance: KafkaInstance, topics: list[str], **consumer_kwargs: Any)`

Initializes the consumer with specified topics and configuration.

**Parameters:**

- `kafka_instance` (KafkaInstance): KafkaInstance used to create the consumer
- `topics` (list[str]): List of topic names to subscribe to
- `**consumer_kwargs` (Any): Additional keyword arguments passed to KafkaConsumer constructor

**Returns:**

- `None`

**Example:**

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.kafka.consumer import Consumer

# Configure Kafka
config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('my-consumer-group')
    .set_auto_offset_reset('earliest')
)

kafka_instance = KafkaInstance(config)

# Create consumer for single topic
consumer = Consumer(kafka_instance, ['orders'])

# Create consumer for multiple topics
consumer = Consumer(kafka_instance, ['orders', 'payments', 'notifications'])

# Create consumer with custom settings
consumer = Consumer(
    kafka_instance,
    ['events'],
    max_poll_records=100,
    session_timeout_ms=30000
)
```

## Methods

### `register_handler(topic: str, handler: MessageHandler)`

Registers a handler function for a specific topic.

**Parameters:**

- `topic` (str): Topic name to handle messages from
- `handler` (MessageHandler): Callback function that accepts keyword arguments

**Handler Signature:**

The handler function receives the following keyword arguments:

- `topic` (str): The topic name the message came from
- `partition` (int): The partition number
- `offset` (int): The message offset within the partition
- `key` (bytes | None): The message key (can be None)
- `value` (Any): The deserialized message value

**Returns:**

- `Consumer`: Self reference for method chaining

**Features:**

- Multiple handlers can be registered for the same topic
- Handlers are invoked in registration order
- Handler exceptions are caught and logged but don't stop message processing

**Example:**

```python
from dtpyfw.kafka.consumer import Consumer

# Define a handler function
def order_handler(topic, partition, offset, key, value):
    print(f"Processing order from {topic}")
    print(f"Order ID: {value.get('order_id')}")
    print(f"Amount: {value.get('amount')}")
    # Process the order...

# Register the handler
consumer.register_handler('orders', order_handler)

# Register multiple handlers for the same topic
def logging_handler(topic, partition, offset, key, value):
    print(f"[LOG] Message received: topic={topic}, offset={offset}")

consumer.register_handler('orders', logging_handler)
consumer.register_handler('orders', order_handler)

# Chain registrations
consumer.register_handler('orders', order_handler).register_handler('payments', payment_handler)
```

**Handler Best Practices:**

1. Keep handlers focused and lightweight
2. Handle exceptions within handlers
3. Avoid long-running operations (use async tasks/queues)
4. Log processing status for debugging

---

### `commit()`

Manually commits the current consumer offsets to Kafka.

**Parameters:**

- None

**Returns:**

- `None`

**Raises:**

- `Exception`: Propagates any exception from the commit operation after logging

**Features:**

- Commits current read positions for all assigned partitions
- Logs errors via footprint before raising
- Should be called after successfully processing messages when `enable_auto_commit=False`

**Example:**

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.kafka.consumer import Consumer

# Configure with manual commit
config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('manual-commit-group')
    .set_enable_auto_commit(False)  # Disable auto-commit
)

kafka_instance = KafkaInstance(config)
consumer = Consumer(kafka_instance, ['orders'])

def order_handler(topic, partition, offset, key, value):
    process_order(value)

consumer.register_handler('orders', order_handler)

# Consume and commit manually
consumer.consume(timeout_ms=5000)
consumer.commit()  # Commit after successful processing
```

**When to Use Manual Commit:**

- When you need exactly-once semantics
- When processing must be confirmed before committing
- When batching operations (commit after processing batch)
- When integrating with transactional systems

**Warning:**

Only call `commit()` when `enable_auto_commit=False`, otherwise offsets are already committed automatically.

---

### `consume(timeout_ms: int = 1000)`

Polls for new messages and dispatches them to registered handlers.

**Parameters:**

- `timeout_ms` (int, optional): Maximum time to block waiting for messages in milliseconds. Defaults to 1000ms (1 second)

**Returns:**

- `None`

**Features:**

- Fetches new messages from all subscribed topics
- Invokes all registered handlers for each message's topic
- Catches and logs handler exceptions without stopping processing
- Automatically commits offsets when `enable_auto_commit=False` after processing all polled messages
- Non-blocking: returns after timeout even if no messages received

**Example:**

```python
from dtpyfw.kafka.consumer import Consumer

consumer = Consumer(kafka_instance, ['orders', 'payments'])

# Register handlers
consumer.register_handler('orders', handle_order)
consumer.register_handler('payments', handle_payment)

# Single consumption cycle
consumer.consume(timeout_ms=5000)

# Continuous consumption loop
while True:
    consumer.consume(timeout_ms=1000)
    
# Batch processing with longer timeout
while True:
    consumer.consume(timeout_ms=30000)  # Wait up to 30 seconds for messages
```

**Processing Flow:**

1. Poll Kafka for messages (up to `timeout_ms`)
2. For each message received:
   - Find all registered handlers for the message's topic
   - Invoke each handler with message details
   - Catch and log any handler exceptions
3. If `enable_auto_commit=False`, commit offsets after all messages processed

**Error Handling:**

- Handler exceptions are caught and logged via footprint
- Processing continues for remaining messages even if a handler fails
- Consumption exceptions are caught and logged but not raised

## Usage Examples

### Basic Consumer with Handler

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.kafka.consumer import Consumer

# Configure
config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('basic-consumer')
    .set_auto_offset_reset('latest')
)

kafka_instance = KafkaInstance(config)
consumer = Consumer(kafka_instance, ['notifications'])

# Define handler
def notification_handler(topic, partition, offset, key, value):
    user_id = value.get('user_id')
    message = value.get('message')
    print(f"Sending notification to user {user_id}: {message}")
    send_notification(user_id, message)

# Register and consume
consumer.register_handler('notifications', notification_handler)

# Run consumer
while True:
    consumer.consume(timeout_ms=1000)
```

### Multiple Topics with Different Handlers

```python
from dtpyfw.kafka.consumer import Consumer

consumer = Consumer(
    kafka_instance,
    ['user-created', 'user-updated', 'user-deleted']
)

# Handler for user creation
def handle_user_created(topic, partition, offset, key, value):
    user = value
    print(f"Creating user profile for: {user['email']}")
    create_user_profile(user)
    send_welcome_email(user['email'])

# Handler for user updates
def handle_user_updated(topic, partition, offset, key, value):
    user_id = value['user_id']
    updates = value['updates']
    print(f"Updating user {user_id}")
    update_user_profile(user_id, updates)

# Handler for user deletion
def handle_user_deleted(topic, partition, offset, key, value):
    user_id = value['user_id']
    print(f"Deleting user {user_id}")
    delete_user_profile(user_id)
    cleanup_user_data(user_id)

# Register handlers
consumer.register_handler('user-created', handle_user_created)
consumer.register_handler('user-updated', handle_user_updated)
consumer.register_handler('user-deleted', handle_user_deleted)

# Start consuming
while True:
    consumer.consume(timeout_ms=2000)
```

### Manual Offset Management

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.kafka.consumer import Consumer

# Disable auto-commit for manual control
config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('manual-commit-group')
    .set_enable_auto_commit(False)
    .set_auto_offset_reset('earliest')
)

kafka_instance = KafkaInstance(config)
consumer = Consumer(kafka_instance, ['transactions'])

# Track processing success
messages_processed = 0
processing_errors = 0

def transaction_handler(topic, partition, offset, key, value):
    global messages_processed, processing_errors
    try:
        process_transaction(value)
        messages_processed += 1
    except Exception as e:
        print(f"Error processing transaction: {e}")
        processing_errors += 1
        raise  # Re-raise to be caught by Consumer

consumer.register_handler('transactions', transaction_handler)

# Consume with manual commit
batch_size = 100
while True:
    consumer.consume(timeout_ms=5000)
    
    # Commit after processing batch
    if messages_processed >= batch_size:
        try:
            consumer.commit()
            print(f"Committed {messages_processed} messages")
            messages_processed = 0
        except Exception as e:
            print(f"Commit failed: {e}")
```

### Multiple Handlers for Single Topic

```python
from dtpyfw.kafka.consumer import Consumer

consumer = Consumer(kafka_instance, ['orders'])

# Logging handler
def log_handler(topic, partition, offset, key, value):
    print(f"[{offset}] Received order: {value.get('order_id')}")

# Metrics handler
def metrics_handler(topic, partition, offset, key, value):
    order_amount = value.get('amount', 0)
    increment_metric('orders_received')
    increment_metric('revenue', order_amount)

# Processing handler
def process_handler(topic, partition, offset, key, value):
    order_id = value.get('order_id')
    print(f"Processing order {order_id}")
    process_order(value)

# Register all handlers (executed in order)
consumer.register_handler('orders', log_handler)
consumer.register_handler('orders', metrics_handler)
consumer.register_handler('orders', process_handler)

# All three handlers will be called for each order message
while True:
    consumer.consume()
```

### Error Handling in Handlers

```python
from dtpyfw.kafka.consumer import Consumer
import logging

logger = logging.getLogger(__name__)

consumer = Consumer(kafka_instance, ['events'])

def robust_handler(topic, partition, offset, key, value):
    """Handler with comprehensive error handling."""
    try:
        event_type = value.get('type')
        
        if event_type == 'payment':
            process_payment(value)
        elif event_type == 'refund':
            process_refund(value)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            
    except KeyError as e:
        logger.error(f"Missing required field: {e}")
    except ValueError as e:
        logger.error(f"Invalid value: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        # Don't re-raise - let processing continue

consumer.register_handler('events', robust_handler)

while True:
    consumer.consume(timeout_ms=1000)
```

### Graceful Shutdown

```python
import signal
import sys
from dtpyfw.kafka.consumer import Consumer

consumer = Consumer(kafka_instance, ['orders'])
consumer.register_handler('orders', handle_order)

# Graceful shutdown handler
shutdown_requested = False

def signal_handler(sig, frame):
    global shutdown_requested
    print("Shutdown requested, finishing current batch...")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Consumption loop with shutdown
print("Starting consumer...")
while not shutdown_requested:
    consumer.consume(timeout_ms=1000)

print("Consumer stopped gracefully")
sys.exit(0)
```

### Batch Processing Pattern

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.kafka.consumer import Consumer

config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('batch-processor')
    .set_enable_auto_commit(False)
)

kafka_instance = KafkaInstance(config)
consumer = Consumer(kafka_instance, ['events'], max_poll_records=500)

# Collect messages in batches
batch = []
BATCH_SIZE = 100

def event_handler(topic, partition, offset, key, value):
    batch.append(value)

consumer.register_handler('events', event_handler)

# Process in batches
while True:
    consumer.consume(timeout_ms=5000)
    
    if len(batch) >= BATCH_SIZE:
        # Process batch
        print(f"Processing batch of {len(batch)} events")
        process_event_batch(batch)
        
        # Commit and clear
        consumer.commit()
        batch.clear()
```

### Dead Letter Queue Pattern

```python
from dtpyfw.kafka.consumer import Consumer
from dtpyfw.kafka.producer import Producer

# Main consumer
consumer = Consumer(kafka_instance, ['orders'])

# Dead letter queue producer
dlq_producer = Producer(kafka_instance)

def order_handler_with_dlq(topic, partition, offset, key, value):
    try:
        process_order(value)
    except ValidationError as e:
        # Send to dead letter queue for manual review
        print(f"Validation error, sending to DLQ: {e}")
        dlq_producer.send(
            'orders-dlq',
            value={
                'original_topic': topic,
                'original_offset': offset,
                'error': str(e),
                'message': value
            },
            key=key
        )
    except Exception as e:
        # Log and re-raise for retry
        print(f"Processing error: {e}")
        raise

consumer.register_handler('orders', order_handler_with_dlq)

while True:
    consumer.consume()
```

## Error Handling

### Handler Exceptions

Handler exceptions are caught and logged but don't stop processing:

```python
def problematic_handler(topic, partition, offset, key, value):
    raise ValueError("Something went wrong")

consumer.register_handler('topic', problematic_handler)
consumer.consume()  # Exception is logged, processing continues
```

**Logged Information:**

- Handler name and topic
- Exception details via `exception_to_dict()`
- Controller (module.class.method)
- Subject: "Handler failed"

### Commit Exceptions

Commit exceptions are logged and raised:

```python
try:
    consumer.commit()
except Exception as e:
    # Exception is logged with full details
    print(f"Commit failed: {e}")
```

### Consume Exceptions

Consume exceptions are caught and logged but not raised:

```python
consumer.consume()  # If polling fails, error is logged but no exception raised
```

## Best Practices

1. **Keep Handlers Fast**: Avoid blocking operations in handlers
   ```python
   def fast_handler(topic, partition, offset, key, value):
       queue.put(value)  # Queue for async processing
   ```

2. **Handle Exceptions**: Catch exceptions in handlers to avoid disrupting processing
   ```python
   def safe_handler(topic, partition, offset, key, value):
       try:
           process(value)
       except Exception as e:
           logger.error(f"Processing failed: {e}")
   ```

3. **Use Manual Commit for Reliability**: Disable auto-commit for critical data
   ```python
   config.set_enable_auto_commit(False)
   # Process messages
   consumer.commit()  # Commit only after successful processing
   ```

4. **Set Appropriate Timeouts**: Balance responsiveness with efficiency
   ```python
   consumer.consume(timeout_ms=5000)  # 5 seconds for batch processing
   ```

5. **Monitor Consumer Lag**: Track offset lag to ensure consumer keeps up
   ```python
   # Check consumer lag via metrics or monitoring tools
   ```

6. **Implement Graceful Shutdown**: Handle signals properly
   ```python
   signal.signal(signal.SIGTERM, lambda s, f: set_shutdown_flag())
   ```

7. **Use Dead Letter Queues**: Handle poison messages
   ```python
   # Send failed messages to DLQ instead of blocking
   ```

8. **Test Handler Logic**: Unit test handlers independently
   ```python
   def test_handler():
       handler('topic', 0, 100, None, {'test': 'data'})
   ```

## Performance Considerations

1. **Batch Size**: Configure `max_poll_records` for optimal throughput
   ```python
   Consumer(kafka_instance, ['topic'], max_poll_records=500)
   ```

2. **Poll Timeout**: Adjust based on message frequency
   - High frequency: Short timeout (1000ms)
   - Low frequency: Longer timeout (10000ms)

3. **Handler Efficiency**: Keep handlers lightweight
   - Use async processing for heavy operations
   - Offload to worker queues or thread pools

4. **Commit Frequency**: Balance durability with performance
   - Auto-commit: Less control, simpler
   - Manual commit: More control, better reliability

5. **Session Timeout**: Configure based on processing time
   ```python
   Consumer(kafka_instance, ['topic'], session_timeout_ms=30000)
   ```

## Related Classes

- [`KafkaConfig`](config.md) - Configuration builder for Kafka settings
- [`KafkaInstance`](connection.md) - Factory for creating Kafka clients
- [`Producer`](producer.md) - High-level producer for sending messages

## Thread Safety

- `Consumer` is **not** thread-safe
- Create separate consumer instances per thread
- Kafka consumers cannot be shared across threads

## Limitations

1. **Single-threaded Processing**: Each consumer processes messages sequentially
2. **Handler Execution Order**: Handlers execute in registration order
3. **No Message Filtering**: All messages from subscribed topics are received
4. **Auto-deserialize**: Assumes message values can be auto-deserialized by kafka-python

## Dependencies

- `kafka-python`: Python client for Apache Kafka
- `dtpyfw.kafka.connection`: KafkaInstance factory
- `dtpyfw.core.exception`: Exception handling utilities
- `dtpyfw.log`: Logging framework (footprint)
