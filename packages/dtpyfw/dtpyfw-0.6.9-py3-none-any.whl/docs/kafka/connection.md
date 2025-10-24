# KafkaInstance

## Overview

`KafkaInstance` is a manager class that simplifies the creation of Kafka producers and consumers. It uses a `KafkaConfig` object to initialize clients with proper configuration, provides factory methods for creating producers and consumers, and offers context managers for automatic resource cleanup.

## Module Location

```python
from dtpyfw.kafka.connection import KafkaInstance
```

## Class Definition

```python
class KafkaInstance:
    """Manages Kafka producer and consumer instances."""
```

## Dependencies

```python
from kafka import KafkaConsumer, KafkaProducer
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.core.exception import exception_to_dict
from dtpyfw.log import footprint
```

**Required Package:**

- `kafka-python` or compatible Kafka client library

## Constructor

### `__init__(config: KafkaConfig)`

Initializes the Kafka instance manager with the provided configuration.

**Parameters:**

- `config` (KafkaConfig): KafkaConfig instance containing connection settings

**Returns:**

- `None`

**Raises:**

- `ValueError`: If neither `kafka_url` nor `bootstrap_servers` is configured

**Example:**

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = KafkaConfig().set_bootstrap_servers(['localhost:9092'])
kafka_instance = KafkaInstance(config)
```

## Methods

### `get_producer(**kwargs: Any)`

Creates and returns a configured KafkaProducer instance.

**Parameters:**

- `**kwargs` (Any): Additional keyword arguments to pass to KafkaProducer constructor, allowing override of default settings

**Returns:**

- `KafkaProducer`: Configured producer instance ready to send messages

**Raises:**

- `Exception`: Propagates any exception from KafkaProducer initialization after logging

**Features:**

- Automatically configures JSON serialization for message values
- Logs errors with detailed information via footprint
- Merges base configuration with custom kwargs

**Example:**

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = KafkaConfig().set_bootstrap_servers(['localhost:9092'])
kafka_instance = KafkaInstance(config)

# Create a producer
producer = kafka_instance.get_producer()

# Create a producer with custom settings
producer = kafka_instance.get_producer(
    acks='all',
    retries=3,
    compression_type='gzip'
)
```

**JSON Serialization:**

The producer automatically serializes values to JSON:

```python
producer.send('my-topic', value={'key': 'value', 'number': 42})
# Automatically encoded as: b'{"key": "value", "number": 42}'
```

---

### `get_consumer(topics: list[str], **kwargs: Any)`

Creates and returns a configured KafkaConsumer subscribed to specified topics.

**Parameters:**

- `topics` (list[str]): List of topic names to subscribe to
- `**kwargs` (Any): Additional keyword arguments to pass to KafkaConsumer constructor

**Returns:**

- `KafkaConsumer`: Configured and subscribed consumer instance ready to receive messages

**Raises:**

- `Exception`: Propagates any exception from KafkaConsumer initialization or subscription after logging

**Features:**

- Automatically subscribes to specified topics
- Configures consumer-specific settings (group_id, auto_offset_reset, etc.)
- Logs errors with detailed information via footprint
- Merges base configuration with consumer-specific and custom kwargs

**Example:**

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('my-consumer-group')
    .set_auto_offset_reset('earliest')
)
kafka_instance = KafkaInstance(config)

# Create a consumer for single topic
consumer = kafka_instance.get_consumer(['orders'])

# Create a consumer for multiple topics
consumer = kafka_instance.get_consumer(['orders', 'payments', 'notifications'])

# Create a consumer with custom settings
consumer = kafka_instance.get_consumer(
    ['orders'],
    max_poll_records=100,
    session_timeout_ms=30000
)
```

**Default Consumer Configuration:**

- `group_id`: From KafkaConfig (required for consumers)
- `auto_offset_reset`: From KafkaConfig or defaults to `'latest'`
- `enable_auto_commit`: From KafkaConfig or defaults to `True`

---

### `producer_context(**kwargs: Any)`

Context manager that provides a KafkaProducer with automatic resource cleanup.

**Parameters:**

- `**kwargs` (Any): Additional arguments to pass to `get_producer()`

**Yields:**

- `KafkaProducer`: Configured producer instance

**Features:**

- Automatically flushes pending messages on exit
- Automatically closes the producer connection
- Ensures reliable message delivery before cleanup
- Exception-safe resource management

**Example:**

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = KafkaConfig().set_bootstrap_servers(['localhost:9092'])
kafka_instance = KafkaInstance(config)

# Using producer context manager
with kafka_instance.producer_context() as producer:
    producer.send('orders', value={'order_id': 123, 'amount': 99.99})
    producer.send('orders', value={'order_id': 124, 'amount': 149.99})
# Producer is automatically flushed and closed here

# With custom configuration
with kafka_instance.producer_context(acks='all', retries=5) as producer:
    producer.send('critical-topic', value={'important': 'data'})
```

**Best Practice:**

Always use the context manager when possible to ensure proper cleanup and message delivery.

---

### `consumer_context(topics: list[str], **kwargs: Any)`

Context manager that provides a KafkaConsumer with automatic resource cleanup.

**Parameters:**

- `topics` (list[str]): List of topic names to subscribe to
- `**kwargs` (Any): Additional arguments to pass to `get_consumer()`

**Yields:**

- `KafkaConsumer`: Configured and subscribed consumer instance

**Features:**

- Automatically closes the consumer connection on exit
- Exception-safe resource management
- Proper cleanup even if errors occur during consumption

**Example:**

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('my-group')
)
kafka_instance = KafkaInstance(config)

# Using consumer context manager
with kafka_instance.consumer_context(['orders']) as consumer:
    for message in consumer:
        print(f"Received: {message.value}")
        if some_condition:
            break
# Consumer is automatically closed here

# Processing batch of messages
with kafka_instance.consumer_context(['notifications'], max_poll_records=50) as consumer:
    messages = consumer.poll(timeout_ms=5000)
    for topic_partition, records in messages.items():
        for record in records:
            process_notification(record.value)
```

**Best Practice:**

Use context managers for short-lived consumer operations. For long-running consumers, use `get_consumer()` directly with proper shutdown handling.

## Private Methods

### `_build_base_config()`

Builds the base configuration dictionary for Kafka clients.

**Returns:**

- `dict[str, Any]`: Dictionary with common Kafka connection settings

**Raises:**

- `ValueError`: If neither `kafka_url` nor `bootstrap_servers` is configured

**Logic:**

1. Checks if `kafka_url` is provided → uses it directly as bootstrap_servers
2. Otherwise, checks for `bootstrap_servers` → builds config from individual parameters
3. Includes optional parameters: `security_protocol`, `sasl_mechanism`, `sasl_plain_username`, `sasl_plain_password`, `client_id`

**Note:**

This is an internal method and should not be called directly by users.

## Usage Examples

### Basic Producer Setup

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

# Configure and create instance
config = KafkaConfig().set_bootstrap_servers(['localhost:9092'])
kafka_instance = KafkaInstance(config)

# Create producer and send messages
producer = kafka_instance.get_producer()
try:
    future = producer.send('test-topic', value={'message': 'Hello Kafka'})
    result = future.get(timeout=10)
    print(f"Message sent successfully: {result}")
finally:
    producer.flush()
    producer.close()
```

### Basic Consumer Setup

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

# Configure and create instance
config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('test-consumer-group')
    .set_auto_offset_reset('earliest')
)
kafka_instance = KafkaInstance(config)

# Create consumer and receive messages
consumer = kafka_instance.get_consumer(['test-topic'])
try:
    for message in consumer:
        print(f"Received: {message.value}")
        if message.offset > 100:  # Stop after 100 messages
            break
finally:
    consumer.close()
```

### Using Context Managers

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('batch-processor')
)
kafka_instance = KafkaInstance(config)

# Producer context
with kafka_instance.producer_context() as producer:
    for i in range(100):
        producer.send('events', value={'event_id': i, 'type': 'click'})
# Automatically flushed and closed

# Consumer context
with kafka_instance.consumer_context(['events']) as consumer:
    messages = consumer.poll(timeout_ms=10000)
    for tp, records in messages.items():
        print(f"Received {len(records)} messages from {tp}")
# Automatically closed
```

### Secure Connection with SASL/SSL

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

# Production configuration with security
config = (
    KafkaConfig()
    .set_bootstrap_servers(['prod-broker1:9093', 'prod-broker2:9093'])
    .set_security_protocol('SASL_SSL')
    .set_sasl_mechanism('SCRAM-SHA-256')
    .set_sasl_plain_username('app_user')
    .set_sasl_plain_password('secure_password')
    .set_client_id('payment-service')
)

kafka_instance = KafkaInstance(config)

# Use as normal - security is handled automatically
with kafka_instance.producer_context(acks='all') as producer:
    producer.send('payments', value={'payment_id': 'PAY-123', 'amount': 500.00})
```

### Multiple Topics Consumer

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('multi-topic-consumer')
    .set_auto_offset_reset('latest')
)

kafka_instance = KafkaInstance(config)

# Subscribe to multiple related topics
topics = ['user-created', 'user-updated', 'user-deleted']
consumer = kafka_instance.get_consumer(topics)

try:
    for message in consumer:
        print(f"Topic: {message.topic}")
        print(f"Partition: {message.partition}")
        print(f"Offset: {message.offset}")
        print(f"Value: {message.value}")
        
        # Handle different topics
        if message.topic == 'user-created':
            handle_user_created(message.value)
        elif message.topic == 'user-updated':
            handle_user_updated(message.value)
        elif message.topic == 'user-deleted':
            handle_user_deleted(message.value)
finally:
    consumer.close()
```

### Custom Producer Configuration

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = KafkaConfig().set_bootstrap_servers(['localhost:9092'])
kafka_instance = KafkaInstance(config)

# High-reliability producer
producer = kafka_instance.get_producer(
    acks='all',  # Wait for all replicas
    retries=5,  # Retry up to 5 times
    max_in_flight_requests_per_connection=1,  # Ensure ordering
    compression_type='snappy',  # Compress messages
    linger_ms=10,  # Batch messages for 10ms
    batch_size=32768  # Batch size in bytes
)

# Use producer
try:
    producer.send('critical-events', value={'event': 'system-shutdown'})
finally:
    producer.flush()
    producer.close()
```

### Manual Offset Commit Consumer

```python
from dtpyfw.kafka.config import KafkaConfig
from dtpyfw.kafka.connection import KafkaInstance

config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('manual-commit-group')
    .set_enable_auto_commit(False)  # Disable auto-commit
    .set_auto_offset_reset('earliest')
)

kafka_instance = KafkaInstance(config)
consumer = kafka_instance.get_consumer(['transactions'])

try:
    while True:
        messages = consumer.poll(timeout_ms=1000)
        
        for topic_partition, records in messages.items():
            for message in records:
                try:
                    # Process message
                    process_transaction(message.value)
                    
                    # Commit after successful processing
                    consumer.commit()
                except Exception as e:
                    print(f"Error processing message: {e}")
                    # Don't commit - message will be reprocessed
                    break
finally:
    consumer.close()
```

## Error Handling

All methods log errors using the `footprint` logging system before raising exceptions:

```python
try:
    producer = kafka_instance.get_producer()
except Exception as e:
    # Error is logged with:
    # - log_type: "error"
    # - message: Descriptive error message
    # - controller: Module and method name
    # - subject: Component identifier
    # - payload: Exception details via exception_to_dict()
    print(f"Failed to create producer: {e}")
```

**Logged Information:**

- Error type and message
- Stack trace (via `exception_to_dict`)
- Controller (module.class.method)
- Subject (e.g., "Kafka Producer", "Kafka Consumer")

## Best Practices

1. **Use Context Managers**: For automatic resource cleanup and message flushing
   ```python
   with kafka_instance.producer_context() as producer:
       producer.send('topic', value=data)
   ```

2. **Reuse KafkaInstance**: Create one instance per configuration and reuse it
   ```python
   # Good: One instance, multiple producers/consumers
   kafka_instance = KafkaInstance(config)
   producer1 = kafka_instance.get_producer()
   producer2 = kafka_instance.get_producer()
   ```

3. **Configure Security**: Always use SASL/SSL in production
   ```python
   config.set_security_protocol('SASL_SSL')
   ```

4. **Set Client IDs**: For easier debugging and monitoring
   ```python
   config.set_client_id('service-name-v1')
   ```

5. **Handle Errors**: Always wrap producer/consumer operations in try-except
   ```python
   try:
       producer.send('topic', value=data)
   except Exception as e:
       logger.error(f"Send failed: {e}")
   ```

6. **Flush Before Close**: Ensure messages are sent before closing producer
   ```python
   producer.flush()  # Wait for pending messages
   producer.close()
   ```

7. **Close Consumers**: Always close consumers to leave consumer group cleanly
   ```python
   try:
       consumer = kafka_instance.get_consumer(['topic'])
       # Use consumer
   finally:
       consumer.close()
   ```

## Related Classes

- [`KafkaConfig`](config.md) - Configuration builder for Kafka settings
- [`Producer`](producer.md) - High-level producer wrapper
- [`Consumer`](consumer.md) - High-level consumer with handler registration

## Thread Safety

- `KafkaInstance` itself is thread-safe for creating producers/consumers
- Individual `KafkaProducer` and `KafkaConsumer` instances are **not** thread-safe
- Create separate producer/consumer instances per thread

## Performance Considerations

1. **Producer Batching**: Configure `linger_ms` and `batch_size` for throughput
2. **Compression**: Use `compression_type='snappy'` or `'gzip'` for bandwidth
3. **Consumer Prefetch**: Adjust `max_poll_records` and `fetch_min_bytes`
4. **Reuse Connections**: Don't recreate producers/consumers frequently

## Dependencies

- `kafka-python`: Python client for Apache Kafka
- `dtpyfw.kafka.config`: Configuration management
- `dtpyfw.core.exception`: Exception handling utilities
- `dtpyfw.log`: Logging framework
