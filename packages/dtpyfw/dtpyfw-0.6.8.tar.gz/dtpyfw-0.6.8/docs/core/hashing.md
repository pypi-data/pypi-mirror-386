# Hashing Utilities

## Overview

The `dtpyfw.core.hashing` module provides utilities for hashing arbitrary data using various cryptographic algorithms. This module is useful for generating checksums, cache keys, data fingerprints, and ensuring data integrity.

## Module Path

```python
from dtpyfw.core.hashing import hash_data
```

## Functions

### `hash_data(data: Any, algorithm: str = "sha512") -> str`

Hash the provided data using the specified algorithm.

**Description:**

Serializes the input data and generates a cryptographic hash using one of the supported algorithms. The default algorithm is SHA-512, which provides strong security for most use cases.

**Parameters:**

- **data** (`Any`): The data to hash. Can be any serializable type (str, dict, list, tuple, etc.).
- **algorithm** (`str`, optional): The hashing algorithm to use. Defaults to `"sha512"`.

**Supported Algorithms:**

| Algorithm | Output Length | Use Case |
|-----------|--------------|----------|
| `md5` | 32 characters | Legacy systems (not recommended for security) |
| `sha1` | 40 characters | Git commits, legacy compatibility |
| `sha256` | 64 characters | General purpose, good security |
| `sha512` | 128 characters | High security (default) |
| `blake2b` | 32 characters | Fast, modern alternative |
| `blake2s` | 32 characters | Fast, optimized for 32-bit systems |

**Returns:**

- **`str`**: The hexadecimal string representation of the hash digest.

**Raises:**

- **ValueError**: If an unsupported algorithm is specified.

**Example:**

```python
from dtpyfw.core.hashing import hash_data

# Hash a string
text = "Hello, World!"
hash_value = hash_data(text)
print(hash_value)  # 128-character SHA-512 hash

# Hash a dictionary
user_data = {"id": 123, "name": "John", "email": "john@example.com"}
hash_value = hash_data(user_data, algorithm="sha256")
print(hash_value)  # 64-character SHA-256 hash

# Hash a list
items = [1, 2, 3, 4, 5]
hash_value = hash_data(items, algorithm="blake2b")
print(hash_value)  # 32-character BLAKE2b hash
```

## Internal Helper

### `serialize_data(data: Any) -> bytes`

Serialize data into a bytes object for hashing.

**Description:**

Converts various data types into a consistent byte representation suitable for hashing. Handles strings, dictionaries, and other JSON-serializable types with fallback to `repr()` for non-serializable objects.

**Parameters:**

- **data** (`Any`): The data to serialize.

**Returns:**

- **`bytes`**: The serialized data as bytes.

**Note:** This is an internal function used by `hash_data()` and is not exported in `__all__`.

## Complete Usage Examples

### 1. Cache Key Generation

```python
from dtpyfw.core.hashing import hash_data
from dtpyfw.redis import caching

class UserService:
    def get_user_profile(self, user_id: int, include_details: bool = False):
        """Fetch user profile with caching."""
        # Generate cache key from parameters
        cache_key = f"user_profile:{hash_data({'id': user_id, 'details': include_details})}"
        
        # Try cache first
        cached = caching.get(cache_key)
        if cached:
            return cached
        
        # Fetch from database
        profile = self._fetch_from_db(user_id, include_details)
        
        # Cache for 1 hour
        caching.set(cache_key, profile, ttl=3600)
        return profile

# Usage
service = UserService()
profile = service.get_user_profile(123, include_details=True)
```

### 2. Data Deduplication

```python
from dtpyfw.core.hashing import hash_data

class DocumentStore:
    def __init__(self):
        self.documents = {}  # hash -> document
        self.hashes = {}  # document_id -> hash
    
    def add_document(self, doc_id: str, content: str) -> bool:
        """Add document, returning False if duplicate detected."""
        content_hash = hash_data(content, algorithm="sha256")
        
        # Check for duplicate
        if content_hash in self.documents:
            print(f"Duplicate content detected! Same as {self.documents[content_hash]}")
            return False
        
        # Store document
        self.documents[content_hash] = doc_id
        self.hashes[doc_id] = content_hash
        return True
    
    def has_changed(self, doc_id: str, new_content: str) -> bool:
        """Check if document content has changed."""
        new_hash = hash_data(new_content, algorithm="sha256")
        old_hash = self.hashes.get(doc_id)
        return new_hash != old_hash

# Usage
store = DocumentStore()
store.add_document("doc1", "This is the content")
is_duplicate = store.add_document("doc2", "This is the content")  # False
has_changed = store.has_changed("doc1", "Updated content")  # True
```

### 3. API Request Signature

```python
from dtpyfw.core.hashing import hash_data
import time

class APIClient:
    def __init__(self, api_key: str, secret: str):
        self.api_key = api_key
        self.secret = secret
    
    def generate_signature(self, endpoint: str, params: dict) -> str:
        """Generate request signature for authentication."""
        timestamp = int(time.time())
        
        # Create signature payload
        signature_data = {
            "endpoint": endpoint,
            "params": params,
            "timestamp": timestamp,
            "secret": self.secret
        }
        
        # Generate signature
        signature = hash_data(signature_data, algorithm="sha256")
        return signature
    
    def make_request(self, endpoint: str, params: dict):
        """Make authenticated API request."""
        signature = self.generate_signature(endpoint, params)
        
        headers = {
            "X-API-Key": self.api_key,
            "X-Signature": signature,
            "X-Timestamp": str(int(time.time()))
        }
        
        # Make request with headers
        return requests.post(endpoint, json=params, headers=headers)

# Usage
client = APIClient("my-api-key", "my-secret")
response = client.make_request("/api/users", {"name": "John"})
```

### 4. Content Versioning

```python
from dtpyfw.core.hashing import hash_data
from datetime import datetime

class ContentVersion:
    def __init__(self, content: str, author: str):
        self.content = content
        self.author = author
        self.timestamp = datetime.now()
        self.hash = hash_data(content, algorithm="sha256")
    
    def __repr__(self):
        return f"Version({self.hash[:8]}... by {self.author})"

class VersionedDocument:
    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        self.versions = []
    
    def add_version(self, content: str, author: str) -> bool:
        """Add new version if content has changed."""
        new_version = ContentVersion(content, author)
        
        # Check if content actually changed
        if self.versions and self.versions[-1].hash == new_version.hash:
            return False  # No change
        
        self.versions.append(new_version)
        return True
    
    def get_version_by_hash(self, content_hash: str):
        """Retrieve specific version by hash."""
        for version in self.versions:
            if version.hash == content_hash:
                return version
        return None
    
    def compare_versions(self, hash1: str, hash2: str) -> bool:
        """Check if two versions are identical."""
        return hash1 == hash2

# Usage
doc = VersionedDocument("article-123")
doc.add_version("First draft", "alice")
doc.add_version("Updated draft", "bob")
doc.add_version("Updated draft", "charlie")  # False - no change
```

### 5. Database Query Result Caching

```python
from dtpyfw.core.hashing import hash_data
from functools import wraps

def cache_query_result(ttl: int = 300):
    """Decorator to cache database query results."""
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = hash_data({
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            })
            
            # Check cache
            if cache_key in cache:
                cached_data, cached_time = cache[cache_key]
                if time.time() - cached_time < ttl:
                    return cached_data
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Store in cache
            cache[cache_key] = (result, time.time())
            return result
        
        return wrapper
    return decorator

# Usage
@cache_query_result(ttl=600)
def get_user_orders(user_id: int, status: str = None):
    # Expensive database query
    return db.query(Order).filter_by(user_id=user_id, status=status).all()

# First call hits database
orders = get_user_orders(123, status="pending")

# Second call returns cached result
orders = get_user_orders(123, status="pending")
```

### 6. File Integrity Verification

```python
from dtpyfw.core.hashing import hash_data
import os

class FileIntegrityChecker:
    def __init__(self):
        self.checksums = {}
    
    def calculate_checksum(self, filepath: str) -> str:
        """Calculate checksum for a file."""
        with open(filepath, 'rb') as f:
            content = f.read()
        return hash_data(content, algorithm="sha256")
    
    def store_checksum(self, filepath: str) -> str:
        """Store checksum for future verification."""
        checksum = self.calculate_checksum(filepath)
        self.checksums[filepath] = checksum
        return checksum
    
    def verify_file(self, filepath: str) -> bool:
        """Verify file hasn't been modified."""
        if filepath not in self.checksums:
            return None  # No stored checksum
        
        current_checksum = self.calculate_checksum(filepath)
        stored_checksum = self.checksums[filepath]
        
        return current_checksum == stored_checksum
    
    def scan_directory(self, directory: str):
        """Calculate checksums for all files in directory."""
        for root, dirs, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                self.store_checksum(filepath)
    
    def find_modified_files(self) -> list:
        """Find all files that have been modified."""
        modified = []
        for filepath in self.checksums:
            if os.path.exists(filepath):
                if not self.verify_file(filepath):
                    modified.append(filepath)
        return modified

# Usage
checker = FileIntegrityChecker()
checker.scan_directory("/app/data")
modified_files = checker.find_modified_files()
```

### 7. Idempotency Key Generation

```python
from dtpyfw.core.hashing import hash_data
from datetime import datetime

class PaymentProcessor:
    def __init__(self):
        self.processed_payments = set()
    
    def generate_idempotency_key(self, user_id: int, amount: float, 
                                   currency: str, description: str) -> str:
        """Generate idempotency key for payment."""
        key_data = {
            'user_id': user_id,
            'amount': amount,
            'currency': currency,
            'description': description,
            'date': datetime.now().date().isoformat()
        }
        return hash_data(key_data, algorithm="sha256")
    
    def process_payment(self, user_id: int, amount: float, 
                        currency: str, description: str) -> dict:
        """Process payment with idempotency protection."""
        idempotency_key = self.generate_idempotency_key(
            user_id, amount, currency, description
        )
        
        # Check if already processed
        if idempotency_key in self.processed_payments:
            return {
                "status": "already_processed",
                "idempotency_key": idempotency_key
            }
        
        # Process payment
        result = self._charge_payment(user_id, amount, currency)
        
        # Mark as processed
        self.processed_payments.add(idempotency_key)
        
        return {
            "status": "success",
            "idempotency_key": idempotency_key,
            "result": result
        }

# Usage
processor = PaymentProcessor()
result1 = processor.process_payment(123, 99.99, "USD", "Premium subscription")
result2 = processor.process_payment(123, 99.99, "USD", "Premium subscription")
# result2["status"] == "already_processed"
```

## Algorithm Selection Guide

### MD5 (Not Recommended for Security)

```python
# Fast but cryptographically broken
hash_value = hash_data(data, algorithm="md5")
# Use only for: Non-security checksums, legacy compatibility
```

### SHA-1 (Legacy)

```python
# Better than MD5 but still vulnerable
hash_value = hash_data(data, algorithm="sha1")
# Use only for: Git compatibility, legacy systems
```

### SHA-256 (Recommended)

```python
# Good balance of security and performance
hash_value = hash_data(data, algorithm="sha256")
# Use for: General purpose, cache keys, signatures
```

### SHA-512 (High Security - Default)

```python
# Maximum security
hash_value = hash_data(data, algorithm="sha512")
# Use for: Critical data, passwords (with salting), sensitive checksums
```

### BLAKE2b/BLAKE2s (Modern & Fast)

```python
# Faster than SHA-256, equally secure
hash_value = hash_data(data, algorithm="blake2b")
# Use for: High-performance applications, modern systems
```

## Performance Comparison

Approximate relative speeds (higher is faster):

| Algorithm | Speed | Security | Output Size |
|-----------|-------|----------|-------------|
| MD5 | 10x | ⚠️ Broken | 32 chars |
| SHA-1 | 8x | ⚠️ Weak | 40 chars |
| BLAKE2b | 5x | ✅ Strong | 32 chars |
| SHA-256 | 3x | ✅ Strong | 64 chars |
| SHA-512 | 1x | ✅ Very Strong | 128 chars |

## Best Practices

1. **Choose the right algorithm:**
   ```python
   # For cache keys
   hash_data(data, algorithm="sha256")
   
   # For security-critical applications
   hash_data(data, algorithm="sha512")
   
   # For high-performance needs
   hash_data(data, algorithm="blake2b")
   ```

2. **Consistent data serialization:**
   ```python
   # Dictionary keys are sorted automatically
   hash1 = hash_data({"a": 1, "b": 2})
   hash2 = hash_data({"b": 2, "a": 1})
   assert hash1 == hash2  # ✓ Same hash
   ```

3. **Handle non-serializable objects:**
   ```python
   class CustomClass:
       def __init__(self, value):
           self.value = value
       
       def __repr__(self):
           return f"CustomClass({self.value})"
   
   obj = CustomClass(42)
   # Falls back to repr()
   hash_value = hash_data(obj)
   ```

4. **Use for comparisons, not storage:**
   ```python
   # Good: Compare hashes
   if hash_data(data1) == hash_data(data2):
       print("Data is identical")
   
   # Bad: Trying to reverse hash
   # original = unhash(hash_value)  # Impossible!
   ```

## Related Modules

- **dtpyfw.encrypt.hashing** - Password hashing with salt and pepper
- **dtpyfw.core.jsonable_encoder** - Data serialization
- **dtpyfw.redis.caching** - Caching with hash-based keys

## Dependencies

- `hashlib` - Python's built-in hashing library
- `json` - For data serialization

## See Also

- [Python hashlib documentation](https://docs.python.org/3/library/hashlib.html)
- [BLAKE2 official site](https://www.blake2.net/)
- [Hash functions comparison](https://en.wikipedia.org/wiki/Comparison_of_cryptographic_hash_functions)
