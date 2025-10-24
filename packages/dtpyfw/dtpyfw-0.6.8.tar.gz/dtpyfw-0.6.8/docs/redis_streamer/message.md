# dtpyfw.redis_streamer.message

## Overview

The `message` module provides the `Message` dataclass, a simple yet essential container for Redis Streams messages. It encapsulates event names and payload data with built-in JSON encoding capabilities for seamless transmission over Redis Streams. This message structure serves as the standard format for both publishing and consuming messages in the `redis_streamer` module.

## Module Information

- **Module Path**: `dtpyfw.redis_streamer.message`
- **Class**: `Message`
- **Dependencies**:
  - `json` (standard library)
  - `dataclasses` (standard library)
  - `typing` (standard library)
- **Used By**: `AsyncRedisStreamer`, `RedisStreamer`

## Message Dataclass

The `Message` dataclass provides a structured way to represent events and their associated data for transmission through Redis Streams.

### Class Definition

```python
@dataclass
class Message:
    """Redis Streams message container.

    Description:
        A simple dataclass that encapsulates a message name and body payload
        for transmission over Redis Streams. Provides JSON encoding for
        serialization into Redis stream fields. This message structure is
        used by both AsyncRedisStreamer and RedisStreamer for publishing
        and consuming messages.

    Attributes:
        name (str): The message type or event name identifier used to route
            messages to appropriate handlers.
        body (Dict[str, Any]): The message payload as a dictionary containing
            the actual data to be transmitted.
    """

    name: str
    body: Dict[str, Any]
```

### Attributes

| Attribute | Type             | Required | Description                                                                                           |
|-----------|------------------|----------|-------------------------------------------------------------------------------------------------------|
| `name`    | `str`            | Yes      | The message type or event name. Used by consumers to route messages to the appropriate handlers.     |
| `body`    | `Dict[str, Any]` | Yes      | The message payload containing the actual data. Must be a dictionary that can be JSON-serialized.    |

## Methods

### `get_json_encoded()`

Converts the message into a format suitable for Redis Streams transmission.

```python
def get_json_encoded(self) -> Dict[str, str]:
    """Return a JSON-encoded representation of the message.

    Description:
        Converts the message into a dictionary with the name as-is and
        the body JSON-serialized to a string. This format is compatible
        with Redis Streams XADD commands.

    Returns:
        Dict[str, str]: Dictionary with 'name' and JSON-encoded 'body'.
    """
    return {"name": self.name, "body": json.dumps(self.body, default=str)}
```

**Returns**: `Dict[str, str]` - A dictionary containing:
- `'name'` (`str`): The message name as-is (not encoded)
- `'body'` (`str`): The JSON-serialized payload as a string

**Note**: The `default=str` parameter in `json.dumps()` ensures that non-serializable objects (like datetime, UUID, etc.) are converted to strings, preventing serialization errors.

## Usage Examples

### Example 1: Creating a Simple Message

```python
from dtpyfw.redis_streamer.message import Message

# Create a basic message
message = Message(
    name="user.created",
    body={
        "user_id": 12345,
        "username": "johndoe",
        "email": "john@example.com"
    }
)

print(f"Message name: {message.name}")
print(f"Message body: {message.body}")
```

**Output**:
```
Message name: user.created
Message body: {'user_id': 12345, 'username': 'johndoe', 'email': 'john@example.com'}
```

### Example 2: Encoding for Redis Transmission

```python
from dtpyfw.redis_streamer.message import Message

# Create a message
message = Message(
    name="order.placed",
    body={
        "order_id": "ORD-2024-001",
        "customer_id": 789,
        "total": 299.99,
        "items": ["item1", "item2"]
    }
)

# Get encoded format for Redis
encoded = message.get_json_encoded()
print(f"Name: {encoded['name']}")
print(f"Body: {encoded['body']}")
```

**Output**:
```
Name: order.placed
Body: {"order_id": "ORD-2024-001", "customer_id": 789, "total": 299.99, "items": ["item1", "item2"]}
```

### Example 3: Message with Complex Data Types

```python
from datetime import datetime
from uuid import uuid4
from dtpyfw.redis_streamer.message import Message

# Create a message with non-serializable types
message = Message(
    name="event.logged",
    body={
        "event_id": uuid4(),  # UUID object
        "timestamp": datetime.now(),  # datetime object
        "description": "User login",
        "metadata": {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0"
        }
    }
)

# Encode - non-serializable types are converted to strings
encoded = message.get_json_encoded()
print(f"Encoded body: {encoded['body']}")
```

**Output** (example):
```
Encoded body: {"event_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d", "timestamp": "2024-10-24 10:30:45.123456", "description": "User login", "metadata": {"ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0"}}
```

### Example 4: Using with AsyncRedisStreamer

```python
import asyncio
from dtpyfw.redis_streamer.message import Message
from dtpyfw.redis_streamer.asynchronize import AsyncRedisStreamer
from dtpyfw.redis.connection import RedisInstance

async def send_notification():
    # Initialize Redis connection
    redis_instance = RedisInstance(
        host="localhost",
        port=6379,
        db=0
    )
    
    # Create streamer
    streamer = AsyncRedisStreamer(
        redis_instance=redis_instance,
        consumer_name="notification-service"
    )
    
    # Create and send message
    message = Message(
        name="notification.send",
        body={
            "recipient": "user@example.com",
            "subject": "Welcome!",
            "template": "welcome_email"
        }
    )
    
    await streamer.send_message("notifications", message)
    print("Notification message sent!")

# Run the async function
asyncio.run(send_notification())
```

### Example 5: Using with RedisStreamer (Synchronous)

```python
from dtpyfw.redis_streamer.message import Message
from dtpyfw.redis_streamer.synchronize import RedisStreamer
from dtpyfw.redis.connection import RedisInstance

def send_inventory_update():
    # Initialize Redis connection
    redis_instance = RedisInstance(
        host="localhost",
        port=6379,
        db=0
    )
    
    # Create streamer
    streamer = RedisStreamer(
        redis_instance=redis_instance,
        consumer_name="inventory-service"
    )
    
    # Create and send message
    message = Message(
        name="inventory.updated",
        body={
            "product_id": "PROD-123",
            "quantity": 50,
            "warehouse": "MAIN-01"
        }
    )
    
    streamer.send_message("inventory-updates", message)
    print("Inventory update sent!")

# Send the message
send_inventory_update()
```

### Example 6: Message Factory Pattern

```python
from typing import Any, Dict
from dtpyfw.redis_streamer.message import Message

class MessageFactory:
    """Factory for creating standardized messages."""
    
    @staticmethod
    def user_event(event_type: str, user_id: int, **kwargs) -> Message:
        """Create a user-related event message."""
        return Message(
            name=f"user.{event_type}",
            body={
                "user_id": user_id,
                **kwargs
            }
        )
    
    @staticmethod
    def system_event(event_type: str, severity: str, details: Dict[str, Any]) -> Message:
        """Create a system event message."""
        return Message(
            name=f"system.{event_type}",
            body={
                "severity": severity,
                "details": details
            }
        )

# Usage
user_message = MessageFactory.user_event(
    "registered",
    user_id=12345,
    email="user@example.com",
    plan="premium"
)

system_message = MessageFactory.system_event(
    "error",
    severity="high",
    details={"error_code": "DB_CONNECTION_FAILED", "retry_count": 3}
)

print(f"User message: {user_message.name}")
print(f"System message: {system_message.name}")
```

### Example 7: Batch Message Creation

```python
from dtpyfw.redis_streamer.message import Message
from typing import List

def create_batch_messages(event_name: str, items: List[Dict]) -> List[Message]:
    """Create multiple messages for batch processing."""
    messages = []
    
    for item in items:
        message = Message(
            name=event_name,
            body=item
        )
        messages.append(message)
    
    return messages

# Create batch of messages
order_items = [
    {"order_id": "ORD-001", "amount": 99.99},
    {"order_id": "ORD-002", "amount": 149.50},
    {"order_id": "ORD-003", "amount": 75.00}
]

messages = create_batch_messages("order.processed", order_items)
print(f"Created {len(messages)} messages")

# Send all messages
# for message in messages:
#     await streamer.send_message("orders", message)
```

### Example 8: Message Validation

```python
from dtpyfw.redis_streamer.message import Message
from typing import Dict, Any

class ValidatedMessage(Message):
    """Message with payload validation."""
    
    def __post_init__(self):
        """Validate message after initialization."""
        if not self.name:
            raise ValueError("Message name cannot be empty")
        
        if not isinstance(self.body, dict):
            raise TypeError("Message body must be a dictionary")
        
        if not self.body:
            raise ValueError("Message body cannot be empty")
    
    @classmethod
    def create_with_schema(cls, name: str, body: Dict[str, Any], required_fields: List[str]):
        """Create a message with schema validation."""
        # Validate required fields
        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        return cls(name=name, body=body)

# Usage with validation
try:
    valid_message = ValidatedMessage.create_with_schema(
        name="user.update",
        body={"user_id": 123, "email": "new@example.com"},
        required_fields=["user_id", "email"]
    )
    print("Valid message created")
except ValueError as e:
    print(f"Validation error: {e}")

# This will raise an error
try:
    invalid_message = ValidatedMessage.create_with_schema(
        name="user.update",
        body={"user_id": 123},  # Missing 'email'
        required_fields=["user_id", "email"]
    )
except ValueError as e:
    print(f"Validation error: {e}")
```

### Example 9: Message with Metadata

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from dtpyfw.redis_streamer.message import Message

@dataclass
class EnhancedMessage(Message):
    """Extended message with metadata."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Add automatic metadata."""
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.now()
        if "version" not in self.metadata:
            self.metadata["version"] = "1.0"
    
    def get_json_encoded(self) -> Dict[str, str]:
        """Include metadata in encoding."""
        import json
        return {
            "name": self.name,
            "body": json.dumps(self.body, default=str),
            "metadata": json.dumps(self.metadata, default=str)
        }

# Usage
message = EnhancedMessage(
    name="data.processed",
    body={"record_count": 1000, "status": "success"},
    metadata={"source": "batch-processor", "job_id": "JOB-123"}
)

encoded = message.get_json_encoded()
print(f"Name: {encoded['name']}")
print(f"Body: {encoded['body']}")
print(f"Metadata: {encoded['metadata']}")
```

## Integration with Redis Streams

### How Messages Flow Through the System

1. **Message Creation**: Application creates a `Message` instance with a name and body
2. **Encoding**: The `get_json_encoded()` method converts the message to Redis-compatible format
3. **Publishing**: `AsyncRedisStreamer` or `RedisStreamer` sends the encoded message via `XADD`
4. **Storage**: Redis Streams stores the message with a unique ID
5. **Consumption**: Consumer groups read messages via `XREADGROUP`
6. **Decoding**: Consumers decode the JSON body back to a dictionary
7. **Routing**: The message name routes to the appropriate handler function
8. **Processing**: Handler functions process the message payload

### Redis Streams Format

When a message is sent to Redis Streams, it's stored in this format:

```
Stream: channel_name
  Message ID: 1729768245123-0
    name: "user.created"
    body: "{\"user_id\": 12345, \"username\": \"johndoe\", \"email\": \"john@example.com\"}"
```

## Best Practices

### 1. Use Descriptive Message Names

Message names should clearly indicate the event type and domain:

```python
# Good: Clear hierarchy and purpose
Message(name="user.created", body={...})
Message(name="order.payment.succeeded", body={...})
Message(name="inventory.stock.depleted", body={...})

# Avoid: Vague or unclear names
Message(name="event1", body={...})
Message(name="update", body={...})
```

### 2. Include Essential Context in Body

The message body should contain all information needed to process the event:

```python
# Good: Self-contained message
Message(
    name="order.shipped",
    body={
        "order_id": "ORD-123",
        "customer_id": 456,
        "tracking_number": "TRACK-789",
        "carrier": "FedEx",
        "shipped_at": datetime.now()
    }
)

# Avoid: Incomplete information requiring additional lookups
Message(
    name="order.shipped",
    body={"order_id": "ORD-123"}  # Missing critical details
)
```

### 3. Keep Message Bodies Serializable

Ensure all data types in the body can be JSON-serialized:

```python
from datetime import datetime
from decimal import Decimal

# Good: Using serializable types or converting
Message(
    name="payment.received",
    body={
        "amount": float(Decimal("99.99")),  # Convert Decimal to float
        "timestamp": datetime.now(),  # Will be converted to string
        "currency": "USD"
    }
)
```

### 4. Use Consistent Naming Conventions

Establish a naming convention across your application:

```python
# Convention: <domain>.<entity>.<action>
Message(name="auth.user.login", body={...})
Message(name="auth.user.logout", body={...})
Message(name="billing.invoice.created", body={...})
Message(name="billing.payment.processed", body={...})
```

### 5. Version Your Message Schemas

Include version information for schema evolution:

```python
Message(
    name="user.profile.updated",
    body={
        "version": "2.0",  # Schema version
        "user_id": 123,
        "changes": {
            "email": "new@example.com",
            "phone": "+1234567890"
        }
    }
)
```

### 6. Handle Large Payloads Appropriately

For large payloads, consider storing data separately and passing references:

```python
# For small data (< 1MB): Include directly
Message(
    name="report.generated",
    body={"report_data": [...]}  # OK for small datasets
)

# For large data: Store separately and reference
Message(
    name="report.generated",
    body={
        "report_id": "RPT-123",
        "storage_location": "s3://bucket/reports/RPT-123.json",
        "size_bytes": 5242880
    }
)
```

### 7. Include Idempotency Keys

For operations that should be executed once:

```python
import uuid

Message(
    name="payment.process",
    body={
        "idempotency_key": str(uuid.uuid4()),
        "payment_id": "PAY-123",
        "amount": 99.99
    }
)
```

## Common Patterns

### Event Notification Pattern

```python
Message(
    name="resource.state.changed",
    body={
        "resource_type": "user",
        "resource_id": 123,
        "previous_state": "pending",
        "new_state": "active",
        "changed_by": "admin@example.com",
        "changed_at": datetime.now()
    }
)
```

### Command Pattern

```python
Message(
    name="command.send.email",
    body={
        "command_id": str(uuid.uuid4()),
        "to": "user@example.com",
        "subject": "Welcome",
        "template": "welcome_email",
        "context": {"username": "johndoe"}
    }
)
```

### Data Synchronization Pattern

```python
Message(
    name="sync.customer.data",
    body={
        "source_system": "CRM",
        "target_system": "Data Warehouse",
        "entity_type": "customer",
        "entity_ids": [123, 456, 789],
        "sync_type": "full"
    }
)
```

## Troubleshooting

### JSON Serialization Errors

**Problem**: Non-serializable objects in message body

```python
# This will fail
from decimal import Decimal
message = Message(
    name="test",
    body={"amount": Decimal("99.99")}
)
# TypeError: Object of type Decimal is not JSON serializable
```

**Solution**: The `default=str` parameter in `get_json_encoded()` handles this automatically, but you can also convert explicitly:

```python
# Automatic conversion via get_json_encoded()
message = Message(
    name="test",
    body={"amount": Decimal("99.99")}
)
encoded = message.get_json_encoded()  # Works fine

# Or convert explicitly
message = Message(
    name="test",
    body={"amount": float(Decimal("99.99"))}
)
```

### Message Name Best Practices

**Problem**: Inconsistent or unclear message names make routing difficult

**Solution**: Use a hierarchical naming scheme:

```python
# Good naming structure
"domain.entity.action"
"user.account.created"
"order.payment.succeeded"
"inventory.stock.updated"
```

## Performance Considerations

### Message Size

- **Small messages** (< 10KB): Ideal for high-throughput scenarios
- **Medium messages** (10KB - 1MB): Acceptable for most use cases
- **Large messages** (> 1MB): Consider storing externally and passing references

### JSON Encoding Overhead

The `get_json_encoded()` method has minimal overhead, but for extremely high-throughput scenarios:

```python
# Pre-encode messages if sending the same message multiple times
message = Message(name="heartbeat", body={"status": "ok"})
encoded = message.get_json_encoded()

# Reuse encoded version
for _ in range(1000):
    # Send encoded directly to Redis instead of re-encoding
    pass
```

## Related Documentation

- [AsyncRedisStreamer](asynchronize.md) - Async consumer implementation
- [RedisStreamer](synchronize.md) - Synchronous consumer implementation
- [CommonMethods](common.md) - Base class with shared utilities
- [Redis Connection](../redis/connection.md) - Redis connection management

## External References

- [Redis Streams Documentation](https://redis.io/docs/data-types/streams/)
- [Python JSON Documentation](https://docs.python.org/3/library/json.html)
- [Python Dataclasses](https://docs.python.org/3/library/dataclasses.html)
