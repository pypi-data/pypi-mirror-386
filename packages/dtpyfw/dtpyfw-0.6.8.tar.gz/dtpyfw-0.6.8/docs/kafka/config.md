# KafkaConfig

## Overview

`KafkaConfig` is a builder class for constructing Kafka connection settings in a fluent, chainable manner. It provides a flexible interface that supports both full URL-based configuration and individual parameter-based configuration for Kafka clients.

## Module Location

```python
from dtpyfw.kafka.config import KafkaConfig
```

## Class Definition

```python
class KafkaConfig:
    """Builder for Kafka connection settings."""
```

## Constructor

### `__init__()`

Initializes an empty Kafka configuration object.

**Signature:**
```python
def __init__(self) -> None
```

**Returns:**
- `None`

**Example:**
```python
from dtpyfw.kafka.config import KafkaConfig

config = KafkaConfig()
```

## Configuration Methods

All configuration methods return `self` to enable method chaining.

### `set_kafka_url(url: str)`

Sets the full Kafka connection URL with authentication and multiple brokers.

**Parameters:**
- `url` (str): Complete Kafka URL in format `'kafka://user:pass@host1:9092,host2:9092'`

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
config = KafkaConfig().set_kafka_url('kafka://admin:secret@broker1:9092,broker2:9092')
```

**Notes:**
- This method simplifies configuration when all connection details can be expressed in a single URL
- When using `set_kafka_url()`, you don't need to set individual parameters like `bootstrap_servers`

---

### `set_bootstrap_servers(servers: list[str])`

Sets the list of Kafka bootstrap servers for initial cluster discovery.

**Parameters:**
- `servers` (list[str]): List of broker addresses in `'host:port'` format

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
config = KafkaConfig().set_bootstrap_servers(['localhost:9092', 'localhost:9093'])
```

**Notes:**
- Either `kafka_url` or `bootstrap_servers` must be provided
- These servers are used to discover the full cluster membership

---

### `set_security_protocol(protocol: str)`

Sets the security protocol for broker communication.

**Parameters:**
- `protocol` (str): Protocol name. Valid values:
  - `'PLAINTEXT'` - No encryption or authentication
  - `'SSL'` - SSL/TLS encryption
  - `'SASL_PLAINTEXT'` - SASL authentication without encryption
  - `'SASL_SSL'` - SASL authentication with SSL/TLS encryption

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
config = KafkaConfig().set_security_protocol('SASL_SSL')
```

---

### `set_sasl_mechanism(mechanism: str)`

Sets the SASL authentication mechanism.

**Parameters:**
- `mechanism` (str): SASL mechanism name. Valid values:
  - `'PLAIN'` - Simple username/password authentication
  - `'SCRAM-SHA-256'` - SCRAM with SHA-256
  - `'SCRAM-SHA-512'` - SCRAM with SHA-512
  - `'GSSAPI'` - Kerberos authentication

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
config = KafkaConfig().set_sasl_mechanism('SCRAM-SHA-256')
```

**Notes:**
- Only relevant when using `SASL_PLAINTEXT` or `SASL_SSL` security protocols

---

### `set_sasl_plain_username(username: str)`

Sets the username for PLAIN SASL authentication.

**Parameters:**
- `username` (str): Authentication username for SASL/PLAIN

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
config = KafkaConfig().set_sasl_plain_username('kafka_user')
```

**Notes:**
- Used in conjunction with `set_sasl_plain_password()` for PLAIN mechanism

---

### `set_sasl_plain_password(password: str)`

Sets the password for PLAIN SASL authentication.

**Parameters:**
- `password` (str): Authentication password for SASL/PLAIN

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
config = KafkaConfig().set_sasl_plain_password('secure_password')
```

**Security Warning:**
- Store passwords securely, preferably using environment variables or secrets management systems

---

### `set_client_id(client_id: str)`

Sets the client identifier for Kafka connections.

**Parameters:**
- `client_id` (str): Unique identifier for this Kafka client application

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
config = KafkaConfig().set_client_id('my-service-v1')
```

**Notes:**
- This identifier appears in broker logs and metrics
- Useful for tracking and debugging client connections

---

### `set_group_id(group_id: str)`

Sets the consumer group identifier.

**Parameters:**
- `group_id` (str): Unique identifier for the consumer group

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
config = KafkaConfig().set_group_id('order-processing-group')
```

**Notes:**
- Required for consumer applications
- Multiple consumer instances with the same group_id coordinate to share partition consumption
- Each consumer group maintains independent offsets

---

### `set_auto_offset_reset(offset: str)`

Sets the auto offset reset policy for consumers.

**Parameters:**
- `offset` (str): Reset policy. Valid values:
  - `'earliest'` - Reset to the beginning of the partition
  - `'latest'` - Reset to the end of the partition (default)
  - `'none'` - Throw exception if no offset is found

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
config = KafkaConfig().set_auto_offset_reset('earliest')
```

**Notes:**
- Only applies when there is no initial offset in Kafka or the current offset no longer exists
- `'earliest'` is useful for reprocessing all messages
- `'latest'` is useful for only processing new messages

---

### `set_enable_auto_commit(flag: bool)`

Enables or disables automatic offset committing.

**Parameters:**
- `flag` (bool): 
  - `True` - Enable auto-commit (offsets committed automatically)
  - `False` - Require manual commits for offset management

**Returns:**
- `KafkaConfig`: Self reference for method chaining

**Example:**
```python
# Disable auto-commit for manual offset control
config = KafkaConfig().set_enable_auto_commit(False)
```

**Notes:**
- When `False`, you must manually commit offsets after processing messages
- Manual commits provide better control over exactly-once or at-least-once semantics
- Default behavior is typically `True`

---

### `get(key: str, default: Any = None)`

Retrieves a configuration value by key.

**Parameters:**
- `key` (str): The configuration parameter name to retrieve
- `default` (Any, optional): Value to return if key is not found. Defaults to `None`

**Returns:**
- `Any`: The configuration value associated with the key, or the default value if not found

**Example:**
```python
config = KafkaConfig().set_client_id('my-client')
client_id = config.get('client_id')  # Returns 'my-client'
timeout = config.get('timeout', 30)  # Returns 30 (default)
```

## Usage Examples

### Basic Configuration with URL

```python
from dtpyfw.kafka.config import KafkaConfig

# Simple configuration using connection URL
config = KafkaConfig().set_kafka_url('kafka://localhost:9092')
```

### Configuration with Individual Parameters

```python
from dtpyfw.kafka.config import KafkaConfig

# Detailed configuration with multiple brokers
config = (
    KafkaConfig()
    .set_bootstrap_servers(['broker1:9092', 'broker2:9092', 'broker3:9092'])
    .set_client_id('payment-service')
)
```

### Secure Configuration with SASL/SSL

```python
from dtpyfw.kafka.config import KafkaConfig

# Production configuration with authentication
config = (
    KafkaConfig()
    .set_bootstrap_servers(['prod-broker1:9093', 'prod-broker2:9093'])
    .set_security_protocol('SASL_SSL')
    .set_sasl_mechanism('SCRAM-SHA-256')
    .set_sasl_plain_username('app_user')
    .set_sasl_plain_password('strong_password')
    .set_client_id('order-processor')
)
```

### Consumer Configuration

```python
from dtpyfw.kafka.config import KafkaConfig

# Consumer with specific offset behavior
config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_group_id('analytics-consumer-group')
    .set_auto_offset_reset('earliest')  # Process from beginning
    .set_enable_auto_commit(False)  # Manual commit control
    .set_client_id('analytics-service')
)
```

### Producer Configuration

```python
from dtpyfw.kafka.config import KafkaConfig

# Simple producer configuration
config = (
    KafkaConfig()
    .set_bootstrap_servers(['localhost:9092'])
    .set_client_id('notification-producer')
)
```

### Environment-Based Configuration

```python
import os
from dtpyfw.kafka.config import KafkaConfig

# Configuration from environment variables
config = (
    KafkaConfig()
    .set_bootstrap_servers(os.getenv('KAFKA_BROKERS', 'localhost:9092').split(','))
    .set_security_protocol(os.getenv('KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT'))
    .set_sasl_mechanism(os.getenv('KAFKA_SASL_MECHANISM', 'PLAIN'))
    .set_sasl_plain_username(os.getenv('KAFKA_USERNAME', ''))
    .set_sasl_plain_password(os.getenv('KAFKA_PASSWORD', ''))
    .set_client_id(os.getenv('SERVICE_NAME', 'default-client'))
)
```

## Best Practices

1. **Use Method Chaining**: Take advantage of the fluent interface for cleaner configuration:
   ```python
   config = KafkaConfig().set_bootstrap_servers(...).set_client_id(...).set_group_id(...)
   ```

2. **Store Credentials Securely**: Never hardcode passwords; use environment variables or secret management:
   ```python
   config.set_sasl_plain_password(os.getenv('KAFKA_PASSWORD'))
   ```

3. **Choose Appropriate Security**: Use `SASL_SSL` for production environments with sensitive data

4. **Set Meaningful Client IDs**: Use descriptive client IDs for easier debugging and monitoring:
   ```python
   config.set_client_id('user-service-v2-prod')
   ```

5. **Consumer Group Management**: Use consistent group IDs for consumer instances that should coordinate:
   ```python
   config.set_group_id('order-processing-workers')
   ```

6. **Offset Reset Policy**: Choose the right policy based on your use case:
   - `earliest` - For reprocessing or new consumer groups needing historical data
   - `latest` - For real-time processing of new events only
   - `none` - For strict offset management with error handling

## Related Classes

- [`KafkaInstance`](connection.md) - Uses `KafkaConfig` to create producers and consumers
- [`Producer`](producer.md) - High-level producer using configuration
- [`Consumer`](consumer.md) - High-level consumer using configuration

## Thread Safety

`KafkaConfig` is not thread-safe. Create separate instances for concurrent configuration or ensure proper synchronization.

## Dependencies

This module has no external dependencies beyond Python's standard library typing module.
