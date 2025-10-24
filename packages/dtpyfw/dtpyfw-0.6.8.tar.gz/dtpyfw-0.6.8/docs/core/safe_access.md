# Safe Access Utilities

## Overview

The `dtpyfw.core.safe_access` module provides utility helpers for safe attribute and function access. These utilities catch exceptions and return default values instead of propagating errors, making code more resilient to unexpected failures.

## Module Path

```python
from dtpyfw.core.safe_access import safe_access, convert_to_int_or_float
```

## Functions

### `safe_access(func: Callable, default_value: Any = None) -> Any`

Execute a function and return a default value if it raises an error.

**Description:**

Provides safe execution of a callable, catching all exceptions and returning a default value instead of propagating errors. Useful for optional operations or fallback scenarios.

**Parameters:**

- **func** (`Callable`): A callable to execute with no arguments
- **default_value** (`Any`, optional): Value to return if func raises any exception. Defaults to None

**Returns:**

- The result of `func()` if successful, otherwise `default_value`

**Example:**

```python
from dtpyfw.core.safe_access import safe_access

# Safe dictionary access
data = {"name": "John"}
email = safe_access(lambda: data["email"], default_value="unknown@example.com")
print(email)  # Output: unknown@example.com

# Safe attribute access
user = get_user()
username = safe_access(lambda: user.profile.username, default_value="Anonymous")

# Safe list access
items = [1, 2, 3]
fifth_item = safe_access(lambda: items[4], default_value=0)
print(fifth_item)  # Output: 0
```

---

### `convert_to_int_or_float(string_num: str) -> int | float | None`

Convert a string to int or float if possible, otherwise None.

**Description:**

Attempts to parse a string as a number. Returns an int if the value is a whole number, float if it has a decimal component, or None if parsing fails.

**Parameters:**

- **string_num** (`str`): The string representation of a number to convert

**Returns:**

- **`int`**: If the number is whole
- **`float`**: If it has decimals
- **`None`**: If invalid

**Example:**

```python
from dtpyfw.core.safe_access import convert_to_int_or_float

# Integer conversion
result = convert_to_int_or_float("42")
print(result, type(result))  # Output: 42 <class 'int'>

# Float conversion
result = convert_to_int_or_float("42.5")
print(result, type(result))  # Output: 42.5 <class 'float'>

# Whole number as float
result = convert_to_int_or_float("42.0")
print(result, type(result))  # Output: 42 <class 'int'>

# Invalid input
result = convert_to_int_or_float("invalid")
print(result)  # Output: None
```

## Complete Usage Examples

### 1. Safe Configuration Access

```python
from dtpyfw.core.safe_access import safe_access
import os

class Config:
    @staticmethod
    def get_database_url():
        """Get database URL with fallback."""
        return safe_access(
            lambda: os.environ["DATABASE_URL"],
            default_value="sqlite:///default.db"
        )
    
    @staticmethod
    def get_max_connections():
        """Get max connections with fallback."""
        value = safe_access(
            lambda: int(os.environ["MAX_CONNECTIONS"]),
            default_value=100
        )
        return value

# Usage
db_url = Config.get_database_url()
max_conn = Config.get_max_connections()
```

### 2. Safe JSON Parsing

```python
from dtpyfw.core.safe_access import safe_access
import json

def parse_json_safely(json_string: str, default=None):
    """Parse JSON with fallback."""
    return safe_access(
        lambda: json.loads(json_string),
        default_value=default or {}
    )

# Usage
data = parse_json_safely('{"name": "John"}')
print(data)  # {'name': 'John'}

invalid_data = parse_json_safely('invalid json')
print(invalid_data)  # {}
```

### 3. Safe Nested Attribute Access

```python
from dtpyfw.core.safe_access import safe_access

class UserService:
    def get_user_email(self, user):
        """Get user email with fallback."""
        return safe_access(
            lambda: user.profile.contact.email,
            default_value="no-email@example.com"
        )
    
    def get_user_age(self, user):
        """Get user age with fallback."""
        return safe_access(
            lambda: user.profile.demographics.age,
            default_value=0
        )

# Usage
service = UserService()
email = service.get_user_email(user)  # Won't crash if any attribute is None
age = service.get_user_age(user)
```

### 4. Query Parameter Parsing

```python
from dtpyfw.core.safe_access import convert_to_int_or_float
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/products")
def list_products(
    page: str = Query("1"),
    limit: str = Query("20"),
    min_price: str = Query(None)
):
    """List products with safe parameter conversion."""
    # Convert query params to appropriate types
    page_num = convert_to_int_or_float(page) or 1
    limit_num = convert_to_int_or_float(limit) or 20
    min_price_num = convert_to_int_or_float(min_price) if min_price else None
    
    # Ensure they're integers
    page_num = int(page_num) if isinstance(page_num, (int, float)) else 1
    limit_num = int(limit_num) if isinstance(limit_num, (int, float)) else 20
    
    return {
        "page": page_num,
        "limit": limit_num,
        "min_price": min_price_num
    }
```

### 5. Safe File Operations

```python
from dtpyfw.core.safe_access import safe_access
import os

def read_file_safely(filepath: str, default_content: str = "") -> str:
    """Read file with fallback."""
    return safe_access(
        lambda: open(filepath, 'r').read(),
        default_value=default_content
    )

def get_file_size(filepath: str) -> int:
    """Get file size with fallback."""
    return safe_access(
        lambda: os.path.getsize(filepath),
        default_value=0
    )

# Usage
content = read_file_safely("/path/to/file.txt", "default content")
size = get_file_size("/path/to/file.txt")
```

### 6. Safe Data Extraction

```python
from dtpyfw.core.safe_access import safe_access, convert_to_int_or_float

class DataExtractor:
    @staticmethod
    def extract_price(product: dict) -> float:
        """Extract price from product dict."""
        price_str = safe_access(
            lambda: product["pricing"]["current"]["amount"],
            default_value="0"
        )
        return convert_to_int_or_float(str(price_str)) or 0.0
    
    @staticmethod
    def extract_quantity(product: dict) -> int:
        """Extract quantity from product dict."""
        qty_str = safe_access(
            lambda: product["inventory"]["quantity"],
            default_value="0"
        )
        qty = convert_to_int_or_float(str(qty_str)) or 0
        return int(qty)

# Usage
extractor = DataExtractor()
price = extractor.extract_price(product_data)
quantity = extractor.extract_quantity(product_data)
```

### 7. Safe API Response Handling

```python
from dtpyfw.core.safe_access import safe_access
import requests

def fetch_user_name(user_id: int) -> str:
    """Fetch user name from API with safe access."""
    try:
        response = requests.get(f"https://api.example.com/users/{user_id}")
        data = response.json()
        
        # Try multiple possible locations for the name
        name = safe_access(lambda: data["user"]["profile"]["full_name"])
        if not name:
            name = safe_access(lambda: data["user"]["name"])
        if not name:
            name = safe_access(lambda: f"{data['first_name']} {data['last_name']}")
        
        return name or f"User {user_id}"
    except Exception:
        return f"User {user_id}"

# Usage
username = fetch_user_name(123)
```

### 8. Form Data Validation

```python
from dtpyfw.core.safe_access import convert_to_int_or_float

def validate_form_data(form_data: dict) -> dict:
    """Validate and convert form data."""
    validated = {}
    
    # Convert age to int
    age = convert_to_int_or_float(form_data.get("age", "0"))
    validated["age"] = int(age) if age else 0
    
    # Convert price to float
    price = convert_to_int_or_float(form_data.get("price", "0"))
    validated["price"] = float(price) if price else 0.0
    
    # Convert quantity to int
    qty = convert_to_int_or_float(form_data.get("quantity", "1"))
    validated["quantity"] = int(qty) if qty else 1
    
    return validated

# Usage
form_data = {"age": "25", "price": "99.99", "quantity": "5"}
validated = validate_form_data(form_data)
```

## Best Practices

1. **Use for optional operations:**
   ```python
   # Good - optional feature that may not be available
   feature_value = safe_access(
       lambda: optional_feature.get_value(),
       default_value=None
   )
   
   # Avoid - hiding critical errors
   # user_id = safe_access(lambda: get_required_user_id())
   ```

2. **Provide meaningful defaults:**
   ```python
   # Good
   email = safe_access(
       lambda: user.email,
       default_value="no-email@example.com"
   )
   
   # Less helpful
   email = safe_access(lambda: user.email, default_value=None)
   ```

3. **Combine with type conversion:**
   ```python
   # Safe access + type conversion
   age_str = safe_access(lambda: user.profile.age, default_value="0")
   age = convert_to_int_or_float(age_str) or 0
   ```

4. **Don't overuse - handle real errors:**
   ```python
   # Good - handle specific errors
   try:
       user = get_user(user_id)
   except UserNotFoundError:
       return None
   
   # Avoid - hiding all errors
   # user = safe_access(lambda: get_user(user_id))
   ```

5. **Use lambda for deferred execution:**
   ```python
   # Correct - lambda defers execution
   value = safe_access(lambda: expensive_operation())
   
   # Wrong - executes immediately, may raise before safe_access
   # value = safe_access(expensive_operation())
   ```

## Common Patterns

### Safe Dictionary Chain

```python
from dtpyfw.core.safe_access import safe_access

data = {"user": {"profile": {"name": "John"}}}

# Chain safe accesses
name = safe_access(lambda: data["user"]["profile"]["name"], "Unknown")
```

### Safe Conversion Pipeline

```python
from dtpyfw.core.safe_access import safe_access, convert_to_int_or_float

# Get string value safely
value_str = safe_access(lambda: config["max_retries"], "3")

# Convert to number
value_num = convert_to_int_or_float(value_str) or 3

# Ensure it's an integer
max_retries = int(value_num)
```

### Optional Chaining Alternative

```python
from dtpyfw.core.safe_access import safe_access

# Python doesn't have optional chaining (?.), use safe_access
email = safe_access(lambda: user.profile.contact.email)

# Instead of (not valid Python):
# email = user?.profile?.contact?.email
```

## Related Modules

- **dtpyfw.core.env** - Environment variable access with defaults
- **dtpyfw.core.validation** - Data validation utilities
- **dtpyfw.api.schemas** - Schema validation with Pydantic

## Dependencies

No external dependencies - uses only Python built-ins.

## See Also

- [Python Exception Handling](https://docs.python.org/3/tutorial/errors.html)
- [Optional Chaining in Other Languages](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining)
