# JSON Encoding Utilities

## Overview

The `dtpyfw.core.jsonable_encoder` module provides utilities to ensure data can be safely JSON-encoded by converting it through a JSON round-trip with string fallbacks. This is particularly useful for handling complex Python objects that need to be serialized for APIs, databases, or caching.

## Module Path

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder
```

## Functions

### `jsonable_encoder(data: Any) -> Any`

Return data encoded to JSON and back to ensure primitives only.

**Description:**

Converts the input data to JSON format and then parses it back, ensuring all values are JSON-compatible primitives (str, int, float, bool, None, list, dict). Non-serializable types are automatically converted to strings using their string representation.

**Parameters:**

- **data** (`Any`): The data to encode, can be any type.

**Returns:**

- **`Any`**: The data with all values converted to JSON-compatible primitives.

**Example:**

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder
from datetime import datetime
from decimal import Decimal

# Complex data with non-JSON types
data = {
    "id": 123,
    "name": "John Doe",
    "created_at": datetime(2024, 1, 15, 10, 30),
    "price": Decimal("99.99"),
    "active": True
}

# Convert to JSON-compatible format
encoded = jsonable_encoder(data)
print(encoded)
# Output: {
#     'id': 123,
#     'name': 'John Doe',
#     'created_at': '2024-01-15 10:30:00',
#     'price': '99.99',
#     'active': True
# }
```

## Complete Usage Examples

### 1. API Response Preparation

```python
from fastapi import FastAPI
from dtpyfw.core.jsonable_encoder import jsonable_encoder
from datetime import datetime
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session):
    """Get user with properly encoded response."""
    user = db.query(User).filter_by(id=user_id).first()
    
    # SQLAlchemy models may contain non-JSON types
    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at,  # datetime
        "updated_at": user.updated_at,  # datetime
        "balance": user.balance,  # Decimal
        "settings": user.settings  # JSON field
    }
    
    # Ensure everything is JSON-compatible
    return jsonable_encoder(user_data)
```

### 2. Database Record Serialization

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary with JSON-safe values."""
        data = {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at
        }
        return jsonable_encoder(data)

# Usage
user = User(id=1, name="Alice", created_at=datetime.now())
user_dict = user.to_dict()
# All fields are now JSON-compatible
```

### 3. Cache Value Preparation

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder
from dtpyfw.redis import caching
import json

class CacheHelper:
    @staticmethod
    def set(key: str, value: any, ttl: int = 3600):
        """Store value in cache with JSON encoding."""
        # Ensure value is JSON-compatible
        encoded_value = jsonable_encoder(value)
        
        # Serialize to JSON string
        json_value = json.dumps(encoded_value)
        
        # Store in cache
        caching.set(key, json_value, ttl=ttl)
    
    @staticmethod
    def get(key: str):
        """Retrieve and parse value from cache."""
        json_value = caching.get(key)
        if json_value:
            return json.loads(json_value)
        return None

# Usage
data = {
    "user_id": 123,
    "timestamp": datetime.now(),
    "amount": Decimal("150.00")
}

CacheHelper.set("order:123", data)
retrieved = CacheHelper.get("order:123")
```

### 4. Logging Complex Objects

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder
from dtpyfw.log import footprint
from datetime import datetime
from uuid import UUID

class AuditLogger:
    @staticmethod
    def log_action(action: str, user_id: int, details: dict):
        """Log user action with complex data."""
        # Prepare payload with non-JSON types
        payload = {
            "action": action,
            "user_id": user_id,
            "timestamp": datetime.now(),
            "details": details,
            "session_id": UUID("12345678-1234-5678-1234-567812345678")
        }
        
        # Encode to JSON-compatible format
        encoded_payload = jsonable_encoder(payload)
        
        # Log to footprint
        footprint.leave(
            log_type="info",
            controller="AuditLogger",
            message=f"User {user_id} performed {action}",
            payload=encoded_payload
        )

# Usage
AuditLogger.log_action(
    action="update_profile",
    user_id=123,
    details={"field": "email", "old": "old@example.com", "new": "new@example.com"}
)
```

### 5. Webhook Payload Preparation

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder
import requests
from datetime import datetime
from decimal import Decimal

class WebhookSender:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_event(self, event_type: str, data: dict):
        """Send webhook with properly encoded payload."""
        payload = {
            "event": event_type,
            "timestamp": datetime.now(),
            "data": data
        }
        
        # Ensure all data is JSON-compatible
        json_payload = jsonable_encoder(payload)
        
        # Send webhook
        response = requests.post(
            self.webhook_url,
            json=json_payload,
            headers={"Content-Type": "application/json"}
        )
        
        return response.status_code == 200

# Usage
sender = WebhookSender("https://example.com/webhook")
sender.send_event("order.created", {
    "order_id": 12345,
    "amount": Decimal("299.99"),
    "created_at": datetime.now()
})
```

### 6. Configuration File Export

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder
import json
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config = {}
    
    def set(self, key: str, value: any):
        """Set configuration value."""
        self.config[key] = value
    
    def save(self):
        """Save configuration to JSON file."""
        # Encode complex types
        encoded_config = jsonable_encoder(self.config)
        
        # Write to file
        with open(self.config_file, 'w') as f:
            json.dump(encoded_config, f, indent=2)
    
    def load(self):
        """Load configuration from JSON file."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)

# Usage
config = ConfigManager()
config.set("database_url", "postgresql://localhost/mydb")
config.set("last_backup", datetime.now())
config.set("retry_delay", Decimal("2.5"))
config.save()
```

### 7. Message Queue Serialization

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder
from dtpyfw.kafka import producer
import json

class TaskQueue:
    def __init__(self, topic: str = "tasks"):
        self.topic = topic
    
    def enqueue(self, task_type: str, params: dict, priority: int = 0):
        """Add task to queue with JSON serialization."""
        message = {
            "task_type": task_type,
            "params": params,
            "priority": priority,
            "created_at": datetime.now(),
            "task_id": uuid.uuid4()
        }
        
        # Encode to JSON-compatible format
        encoded_message = jsonable_encoder(message)
        
        # Serialize to JSON string
        json_message = json.dumps(encoded_message)
        
        # Send to Kafka
        producer.send(self.topic, json_message)

# Usage
queue = TaskQueue()
queue.enqueue(
    task_type="process_order",
    params={
        "order_id": 12345,
        "user_id": 678,
        "amount": Decimal("99.99"),
        "timestamp": datetime.now()
    },
    priority=1
)
```

### 8. GraphQL Response Formatting

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder
from graphql import GraphQLObjectType, GraphQLField, GraphQLString

class UserResolver:
    @staticmethod
    def resolve_user(root, info, user_id: int):
        """Resolve user query with encoded data."""
        # Fetch user from database
        user = db.query(User).filter_by(id=user_id).first()
        
        # Prepare response with various data types
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "account_balance": user.account_balance,  # Decimal
            "metadata": user.metadata  # JSON
        }
        
        # Encode for GraphQL response
        return jsonable_encoder(user_data)
```

## Handling Different Data Types

### Datetime Objects

```python
from datetime import datetime, date, time
from dtpyfw.core.jsonable_encoder import jsonable_encoder

data = {
    "datetime": datetime(2024, 1, 15, 10, 30, 45),
    "date": date(2024, 1, 15),
    "time": time(10, 30, 45)
}

encoded = jsonable_encoder(data)
# All converted to strings: '2024-01-15 10:30:45', '2024-01-15', '10:30:45'
```

### Decimal Numbers

```python
from decimal import Decimal
from dtpyfw.core.jsonable_encoder import jsonable_encoder

data = {
    "price": Decimal("99.99"),
    "tax": Decimal("8.50"),
    "total": Decimal("108.49")
}

encoded = jsonable_encoder(data)
# Decimals converted to strings: '99.99', '8.50', '108.49'
```

### UUID Objects

```python
from uuid import UUID, uuid4
from dtpyfw.core.jsonable_encoder import jsonable_encoder

data = {
    "id": uuid4(),
    "user_id": UUID("12345678-1234-5678-1234-567812345678")
}

encoded = jsonable_encoder(data)
# UUIDs converted to strings
```

### Custom Objects

```python
from dtpyfw.core.jsonable_encoder import jsonable_encoder

class CustomClass:
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return f"CustomClass({self.value})"

data = {
    "object": CustomClass(42),
    "nested": {"obj": CustomClass("test")}
}

encoded = jsonable_encoder(data)
# Custom objects converted to their string representation
```

## Best Practices

1. **Use before JSON serialization:**
   ```python
   import json
   from dtpyfw.core.jsonable_encoder import jsonable_encoder
   
   # Good
   data = jsonable_encoder(complex_data)
   json_string = json.dumps(data)
   
   # May fail
   # json_string = json.dumps(complex_data)  # Error if contains datetime
   ```

2. **Handle nested structures:**
   ```python
   data = {
       "user": {
           "profile": {
               "created_at": datetime.now()
           }
       }
   }
   encoded = jsonable_encoder(data)
   # All levels are encoded
   ```

3. **Combine with type hints:**
   ```python
   from typing import Any
   
   def prepare_response(data: dict) -> dict[str, Any]:
       """Prepare API response with encoded data."""
       return jsonable_encoder(data)
   ```

4. **Document encoding behavior:**
   ```python
   def get_order(order_id: int) -> dict:
       """
       Get order details.
       
       Returns:
           dict: Order data with datetime fields converted to strings
                 and Decimal fields converted to strings.
       """
       order = fetch_order(order_id)
       return jsonable_encoder(order.to_dict())
   ```

## Limitations

1. **Information loss for custom types:**
   - Custom objects are converted to strings via `str()`
   - Cannot be reversed back to original type

2. **Precision for floats:**
   - Decimal precision may be lost in conversion
   - Use string conversion for exact decimal representation

3. **Circular references:**
   - Will raise an error if data contains circular references
   - Ensure data structures are acyclic

## Related Modules

- **dtpyfw.core.hashing** - Uses serialized data for hashing
- **dtpyfw.api.schemas.response** - Response schemas using encoded data
- **dtpyfw.redis.caching** - Cache storage with JSON encoding

## Dependencies

- `json` - Python's built-in JSON library

## See Also

- [Python json module](https://docs.python.org/3/library/json.html)
- [FastAPI JSON Compatible Encoder](https://fastapi.tiangolo.com/tutorial/encoder/)
- [Pydantic JSON Encoders](https://docs.pydantic.dev/latest/concepts/json/)
