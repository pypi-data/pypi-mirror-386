# Producer

## Overview

`Producer` is a high-level wrapper for Kafka message production that simplifies sending messages to Kafka topics. It provides a clean interface with built-in error handling, logging, and automatic JSON encoding for message values.

## Module Location

```python
from dtpyfw.kafka.producer import Producer
```

## Class Definition

```python
class Producer:
    """High-level wrapper for Kafka message production."""
```

## Dependencies

```python
from kafka import KafkaProducer
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.core.exception import exception_to_dict
from dtpyfw.log import footprint
```

**Required Package:**

- `kafka-python` or compatible Kafka client library

## Constructor

### `__init__(kafka_instance: KafkaInstance)`

Initializes the producer from a Kafka instance.

**Parameters:**

- `kafka_instance` (KafkaInstance): KafkaInstance to create the producer from

**Returns:**

- `None`

**Features:**

- Creates the underlying KafkaProducer with JSON serialization configured
- Message values are automatically JSON-encoded before transmission
- Inherits all configuration from the KafkaInstance

**Example:**

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.kafka.producer import Producer

# Configure Kafka
config = KafkaConfig().set_bootstrap_servers(['localhost:9092'])
kafka_instance = KafkaInstance(config)

# Create producer
producer = Producer(kafka_instance)
```

## Methods

### `send(topic: str, value: Any, key: str | bytes | None = None, timeout: int = 10)`

Sends a message to a Kafka topic.

**Parameters:**

- `topic` (str): Target topic name for the message. Must be a non-empty string
- `value` (Any): Message payload to send. Will be JSON-serialized automatically
- `key` (str | bytes | None, optional): Optional message key for partitioning and compaction. Can be a string (UTF-8 encoded) or bytes. Defaults to `None`
- `timeout` (int, optional): Maximum time in seconds to wait for broker acknowledgment. Defaults to 10 seconds

**Returns:**

- `None`

**Raises:**

- `ValueError`: If topic is not a non-empty string
- `Exception`: If message sending fails or times out after logging error details

**Features:**

- Automatically JSON-encodes the message value
- Waits for broker acknowledgment before returning
- Logs success and failure via footprint logging system
- Converts string keys to UTF-8 bytes automatically

**Example:**

```python
from dtpyfw.kafka.producer import Producer

producer = Producer(kafka_instance)

# Send simple message
producer.send('notifications', value={'user_id': 123, 'message': 'Hello'})

# Send with key for partitioning
producer.send('orders', value={'order_id': 'ORD-001', 'amount': 99.99}, key='user-123')

# Send with custom timeout
producer.send('events', value={'event': 'click'}, timeout=30)

# Send with bytes key
producer.send('logs', value={'level': 'INFO', 'msg': 'Started'}, key=b'app-1')
```

**Message Key Usage:**

Keys serve multiple purposes:

1. **Partitioning**: Messages with the same key go to the same partition
2. **Ordering**: Messages in the same partition are ordered
3. **Compaction**: In compacted topics, only the latest message per key is retained

```python
# All orders for same user go to same partition (ordering guaranteed)
producer.send('orders', value=order1, key='user-123')
producer.send('orders', value=order2, key='user-123')
producer.send('orders', value=order3, key='user-123')
```

**JSON Serialization:**

The value is automatically converted to JSON:

```python
# This dictionary
value = {'user': 'john', 'age': 30, 'active': True}

# Becomes this JSON string (then encoded to bytes)
'{"user": "john", "age": 30, "active": true}'
```

**Timeout Behavior:**

- If acknowledgment not received within `timeout` seconds, raises exception
- Default 10 seconds is suitable for most cases
- Increase for slow networks or high-latency clusters

## Usage Examples

### Basic Message Sending

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.kafka.producer import Producer

# Setup
config = KafkaConfig().set_bootstrap_servers(['localhost:9092'])
kafka_instance = KafkaInstance(config)
producer = Producer(kafka_instance)

# Send messages
producer.send('events', value={'type': 'user_login', 'user_id': 456})
producer.send('events', value={'type': 'page_view', 'page': '/home'})
producer.send('events', value={'type': 'user_logout', 'user_id': 456})
```

### Sending with Keys for Partitioning

```python
from dtpyfw.kafka.producer import Producer

producer = Producer(kafka_instance)

# Process orders - all orders for same user go to same partition
orders = [
    {'order_id': 'ORD-001', 'user_id': 'user-123', 'amount': 99.99},
    {'order_id': 'ORD-002', 'user_id': 'user-456', 'amount': 149.99},
    {'order_id': 'ORD-003', 'user_id': 'user-123', 'amount': 79.99},
]

for order in orders:
    # Use user_id as key to ensure ordering per user
    producer.send(
        'orders',
        value=order,
        key=order['user_id']
    )
```

### Error Handling

```python
from dtpyfw.kafka.producer import Producer

producer = Producer(kafka_instance)

def safe_send(topic, value, key=None):
    """Send with error handling."""
    try:
        producer.send(topic, value=value, key=key, timeout=15)
        print(f"Message sent successfully to {topic}")
        return True
    except ValueError as e:
        print(f"Invalid parameters: {e}")
        return False
    except TimeoutError as e:
        print(f"Timeout waiting for acknowledgment: {e}")
        return False
    except Exception as e:
        print(f"Send failed: {e}")
        return False

# Use safe send
success = safe_send('notifications', {'user_id': 789, 'msg': 'Welcome'})
if success:
    print("Notification queued")
else:
    print("Failed to queue notification")
```

### Batch Sending

```python
from dtpyfw.kafka.producer import Producer

producer = Producer(kafka_instance)

# Send multiple events
events = [
    {'event': 'click', 'element_id': 'btn-1'},
    {'event': 'scroll', 'position': 500},
    {'event': 'click', 'element_id': 'btn-2'},
]

for event in events:
    try:
        producer.send('analytics', value=event, timeout=5)
    except Exception as e:
        print(f"Failed to send event: {e}")
        # Continue with next event
```

### Different Message Types

```python
from dtpyfw.kafka.producer import Producer
import datetime

producer = Producer(kafka_instance)

# User event
producer.send('users', value={
    'event_type': 'user_registered',
    'user_id': 'USR-123',
    'email': 'user@example.com',
    'timestamp': datetime.datetime.utcnow().isoformat()
})

# Payment event
producer.send('payments', value={
    'payment_id': 'PAY-456',
    'order_id': 'ORD-789',
    'amount': 299.99,
    'currency': 'USD',
    'status': 'completed'
}, key='ORD-789')

# Log event
producer.send('logs', value={
    'level': 'INFO',
    'service': 'api',
    'message': 'Request processed successfully',
    'duration_ms': 45
})
```

### Production Configuration

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance
from dtpyfw.kafka.producer import Producer

# Production configuration with security
config = (
    KafkaConfig()
    .set_bootstrap_servers(['prod-kafka1:9093', 'prod-kafka2:9093'])
    .set_security_protocol('SASL_SSL')
    .set_sasl_mechanism('SCRAM-SHA-256')
    .set_sasl_plain_username('producer_app')
    .set_sasl_plain_password('secure_password')
    .set_client_id('payment-service-v1')
)

kafka_instance = KafkaInstance(config)
producer = Producer(kafka_instance)

# Send critical payment event
try:
    producer.send(
        'payments',
        value={
            'transaction_id': 'TXN-12345',
            'amount': 1500.00,
            'status': 'authorized'
        },
        key='TXN-12345',
        timeout=30  # Longer timeout for critical data
    )
except Exception as e:
    # Log to monitoring system
    alert_ops_team(f"Critical payment event failed: {e}")
    raise
```

### Using with Context Manager

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = KafkaConfig().set_bootstrap_servers(['localhost:9092'])
kafka_instance = KafkaInstance(config)

# Use context manager for automatic cleanup
with kafka_instance.producer_context() as kafka_producer:
    # Create Producer wrapper
    from dtpyfw.kafka.producer import Producer
    # Note: Producer class doesn't have context manager, 
    # but you can use KafkaInstance.producer_context()
    
    kafka_producer.send('events', value={'event': 'start'})
    kafka_producer.send('events', value={'event': 'end'})
# Automatically flushed and closed
```

**Note:** For context manager support, use `KafkaInstance.producer_context()` directly or manually manage the Producer lifecycle.

### Retry Logic

```python
from dtpyfw.kafka.producer import Producer
import time

producer = Producer(kafka_instance)

def send_with_retry(topic, value, key=None, max_retries=3):
    """Send message with retry logic."""
    for attempt in range(max_retries):
        try:
            producer.send(topic, value=value, key=key, timeout=10)
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"All {max_retries} attempts failed")
                return False

# Use with retry
success = send_with_retry('orders', {'order_id': 'ORD-001'}, key='user-123')
```

### Sending Different Data Types

```python
from dtpyfw.kafka.producer import Producer
import json

producer = Producer(kafka_instance)

# Simple types
producer.send('numbers', value=42)  # JSON: 42
producer.send('strings', value="hello")  # JSON: "hello"
producer.send('booleans', value=True)  # JSON: true

# Complex types
producer.send('objects', value={
    'name': 'John',
    'age': 30,
    'hobbies': ['reading', 'gaming']
})

# Lists
producer.send('arrays', value=[1, 2, 3, 4, 5])

# Nested structures
producer.send('nested', value={
    'user': {
        'id': 123,
        'profile': {
            'name': 'Alice',
            'settings': {'theme': 'dark', 'notifications': True}
        }
    }
})
```

### Event Sourcing Pattern

```python
from dtpyfw.kafka.producer import Producer
import uuid
import datetime

producer = Producer(kafka_instance)

class EventStore:
    """Simple event sourcing with Kafka."""
    
    def __init__(self, producer: Producer):
        self.producer = producer
    
    def publish_event(self, aggregate_id: str, event_type: str, data: dict):
        """Publish domain event."""
        event = {
            'event_id': str(uuid.uuid4()),
            'aggregate_id': aggregate_id,
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'version': 1
        }
        
        self.producer.send(
            'domain-events',
            value=event,
            key=aggregate_id  # Ensures ordering per aggregate
        )

# Use event store
event_store = EventStore(producer)
event_store.publish_event('ORDER-123', 'OrderCreated', {'amount': 99.99})
event_store.publish_event('ORDER-123', 'OrderPaid', {'payment_id': 'PAY-456'})
event_store.publish_event('ORDER-123', 'OrderShipped', {'tracking': 'TRK-789'})
```

### Metrics and Monitoring

```python
from dtpyfw.kafka.producer import Producer
import time

producer = Producer(kafka_instance)

class MetricsProducer:
    """Producer with metrics tracking."""
    
    def __init__(self, producer: Producer):
        self.producer = producer
        self.sent_count = 0
        self.error_count = 0
        self.total_latency = 0.0
    
    def send(self, topic: str, value: Any, key: str = None):
        """Send with metrics."""
        start = time.time()
        try:
            self.producer.send(topic, value=value, key=key)
            self.sent_count += 1
        except Exception as e:
            self.error_count += 1
            raise
        finally:
            self.total_latency += time.time() - start
    
    def get_stats(self):
        """Get producer statistics."""
        avg_latency = self.total_latency / self.sent_count if self.sent_count > 0 else 0
        return {
            'sent': self.sent_count,
            'errors': self.error_count,
            'avg_latency_ms': avg_latency * 1000
        }

# Use with metrics
metrics_producer = MetricsProducer(producer)
for i in range(100):
    metrics_producer.send('events', value={'id': i})

print(metrics_producer.get_stats())
# Output: {'sent': 100, 'errors': 0, 'avg_latency_ms': 5.2}
```

### Transactional Outbox Pattern

```python
from dtpyfw.kafka.producer import Producer

producer = Producer(kafka_instance)

def process_order_with_outbox(order_data):
    """Process order and publish event atomically."""
    # Start database transaction
    with db.transaction():
        # Save order to database
        order = db.orders.create(order_data)
        
        # Save event to outbox table
        db.outbox.create({
            'topic': 'orders',
            'key': order.id,
            'value': {
                'order_id': order.id,
                'user_id': order.user_id,
                'amount': order.amount,
                'status': 'created'
            }
        })
    
    # Separate process reads outbox and publishes to Kafka
    # This ensures at-least-once delivery

def outbox_publisher():
    """Background process to publish outbox events."""
    while True:
        events = db.outbox.get_unpublished(limit=100)
        for event in events:
            try:
                producer.send(
                    event.topic,
                    value=event.value,
                    key=event.key
                )
                db.outbox.mark_published(event.id)
            except Exception as e:
                print(f"Failed to publish event {event.id}: {e}")
        time.sleep(1)
```

## Error Handling

### Validation Errors

```python
producer = Producer(kafka_instance)

# ValueError raised for invalid topic
try:
    producer.send('', value={'data': 'value'})  # Empty topic
except ValueError as e:
    print(f"Invalid topic: {e}")

try:
    producer.send(None, value={'data': 'value'})  # None topic
except ValueError as e:
    print(f"Invalid topic: {e}")
```

### Timeout Errors

```python
producer = Producer(kafka_instance)

try:
    producer.send('slow-topic', value={'data': 'value'}, timeout=1)
except TimeoutError:
    print("Broker did not acknowledge in time")
    # Implement retry or alert logic
```

### Network Errors

```python
producer = Producer(kafka_instance)

try:
    producer.send('topic', value={'data': 'value'})
except Exception as e:
    print(f"Network or broker error: {e}")
    # Log to monitoring system
    # Implement fallback logic
```

### Logging

All send operations are logged via footprint:

**Success:**

```python
# Logs:
# log_type: "info"
# message: "Message 'key' has been sent to topic"
# controller: "dtpyfw.kafka.producer.Producer.send"
# subject: "Message sent"
```

**Failure:**

```python
# Logs:
# log_type: "error"
# message: "Failed to send message to topic {topic}"
# controller: "dtpyfw.kafka.producer.Producer.send"
# subject: "Producer Error"
# payload: {"error": <exception_details>}
```

## Best Practices

1. **Reuse Producer Instances**: Create once and reuse for better performance
   ```python
   # Good: Single producer instance
   producer = Producer(kafka_instance)
   for i in range(1000):
       producer.send('events', value={'id': i})
   ```

2. **Use Keys for Ordering**: When order matters, use keys
   ```python
   # Orders for same user stay ordered
   producer.send('orders', value=order, key=user_id)
   ```

3. **Handle Errors Gracefully**: Don't let one failure stop all processing
   ```python
   for event in events:
       try:
           producer.send('topic', value=event)
       except Exception as e:
           logger.error(f"Failed to send: {e}")
           # Continue processing
   ```

4. **Set Appropriate Timeouts**: Balance responsiveness with reliability
   ```python
   # Critical data: longer timeout
   producer.send('payments', value=payment, timeout=30)
   
   # Best-effort data: shorter timeout
   producer.send('analytics', value=event, timeout=5)
   ```

5. **Validate Data Before Sending**: Catch errors early
   ```python
   if not validate_order(order):
       raise ValueError("Invalid order")
   producer.send('orders', value=order)
   ```

6. **Use Meaningful Keys**: Keys should represent logical grouping
   ```python
   # Good: Use entity ID as key
   producer.send('users', value=user, key=user['id'])
   
   # Bad: Random or meaningless keys
   producer.send('users', value=user, key=str(random.random()))
   ```

7. **Monitor Production**: Track send success/failure rates
   ```python
   try:
       producer.send('topic', value=data)
       metrics.increment('messages_sent')
   except Exception:
       metrics.increment('messages_failed')
   ```

8. **Consider Idempotency**: Design messages to be safely reprocessed
   ```python
   # Include unique ID for deduplication
   producer.send('events', value={
       'event_id': uuid.uuid4(),
       'type': 'user_action',
       'data': {...}
   })
   ```

## Performance Considerations

1. **Batching**: Producer automatically batches messages for efficiency
2. **Compression**: Configure at KafkaInstance level for bandwidth savings
3. **Acks Configuration**: Balance reliability vs throughput
4. **Async Sends**: Producer sends are asynchronous by default, but `send()` waits for ack
5. **Connection Pooling**: Reuse producer instances across requests

## Related Classes

- [`KafkaConfig`](config.md) - Configuration builder for Kafka settings
- [`KafkaInstance`](connection.md) - Factory for creating Kafka clients
- [`Consumer`](consumer.md) - High-level consumer for receiving messages

## Thread Safety

- `Producer` wraps `KafkaProducer` which is thread-safe
- Safe to use single Producer instance across multiple threads
- Each thread can call `send()` concurrently

## Limitations

1. **JSON Serialization Only**: Values are always JSON-serialized
   - For binary data, use base64 encoding within JSON
2. **Synchronous Acknowledgment**: `send()` blocks waiting for broker ack
   - For fire-and-forget, use `KafkaProducer` directly
3. **No Transaction Support**: For transactions, use `KafkaProducer` API directly
4. **No Custom Partitioner**: Uses default partitioning logic

## Dependencies

- `kafka-python`: Python client for Apache Kafka
- `dtpyfw.kafka.connection`: KafkaInstance factory
- `dtpyfw.core.exception`: Exception handling utilities
- `dtpyfw.log`: Logging framework (footprint)

## Advanced Usage

### Custom Serialization

If you need custom serialization beyond JSON:

```python
# Use KafkaInstance.get_producer() directly
from kafka import KafkaProducer
import pickle

kafka_instance = KafkaInstance(config)
custom_producer = kafka_instance.get_producer(
    value_serializer=lambda v: pickle.dumps(v)
)
```

### Async Fire-and-Forget

For fire-and-forget without waiting for ack:

```python
kafka_producer = kafka_instance.get_producer()
future = kafka_producer.send('topic', value={'data': 'value'})
# Don't call future.get() - continues immediately
```

### Callbacks

For handling send results asynchronously:

```python
kafka_producer = kafka_instance.get_producer()

def on_success(metadata):
    print(f"Sent to {metadata.topic} partition {metadata.partition}")

def on_error(exc):
    print(f"Failed: {exc}")

kafka_producer.send('topic', value={'data': 'value'}).add_callback(on_success).add_errback(on_error)
```
