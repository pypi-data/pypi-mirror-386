# Validation Utilities

## Overview

The `dtpyfw.core.validation` module provides validation utilities for common data types and formats. This module offers simple, reusable validators for emails, VINs, years, UUIDs, and URLs that can be used throughout your application.

## Module Path

```python
from dtpyfw.core.validation import (
    is_email,
    is_vin,
    is_year,
    is_uuid,
    is_valid_http_url
)
```

## Functions

### `is_email(email: str) -> bool`

Check if a string is a valid email address.

**Description:**

Validates email format using a regular expression pattern that checks for basic email structure with username, @ symbol, domain, and TLD.

**Parameters:**

- **email** (`str`): The string to validate

**Returns:**

- **`bool`**: True if the string is a valid email address, False otherwise

**Example:**

```python
from dtpyfw.core.validation import is_email

print(is_email("user@example.com"))  # True
print(is_email("invalid.email"))  # False
print(is_email("user@domain"))  # False
print(is_email("user+tag@example.co.uk"))  # True
```

---

### `is_vin(vin: str) -> bool`

Validate a Vehicle Identification Number (VIN).

**Description:**

Checks if a string matches the standard 17-character VIN format using alphanumeric characters excluding I, O, and Q to avoid confusion with numbers.

**Parameters:**

- **vin** (`str`): The VIN string to validate

**Returns:**

- **`bool`**: True if the VIN is valid (17 characters, alphanumeric excluding I/O/Q), False otherwise

**Example:**

```python
from dtpyfw.core.validation import is_vin

print(is_vin("1HGBH41JXMN109186"))  # True
print(is_vin("1HGBH41JXMN10918"))  # False (16 chars)
print(is_vin("1HGBH41JXMN1091866"))  # False (18 chars)
print(is_vin("1HGBH41JXMN10918I"))  # False (contains I)
```

---

### `is_year(s: str) -> bool`

Check if a string represents a valid four-digit year.

**Description:**

Validates that the string is exactly 4 digits and represents a positive year value (greater than 0).

**Parameters:**

- **s** (`str`): The string to check

**Returns:**

- **`bool`**: True if the string is a valid year (4 digits, positive integer), False otherwise

**Example:**

```python
from dtpyfw.core.validation import is_year

print(is_year("2024"))  # True
print(is_year("1999"))  # True
print(is_year("0001"))  # True
print(is_year("0000"))  # False (year must be > 0)
print(is_year("24"))  # False (not 4 digits)
print(is_year("20240"))  # False (5 digits)
print(is_year("abcd"))  # False (not a number)
```

---

### `is_uuid(uuid_to_test: Union[str, UUID], version: int = 4) -> bool`

Validate if a string is a valid UUID of a specified version.

**Description:**

Checks if the input is a UUID object or a valid UUID string matching the specified version (default: version 4).

**Parameters:**

- **uuid_to_test** (`Union[str, UUID]`): The string or UUID object to test
- **version** (`int`, optional): The UUID version to validate against (1-5). Defaults to 4

**Returns:**

- **`bool`**: True if the input is a valid UUID of the specified version, False otherwise

**Example:**

```python
from dtpyfw.core.validation import is_uuid
from uuid import uuid4, UUID

# Valid UUID v4
print(is_uuid("550e8400-e29b-41d4-a716-446655440000"))  # True
print(is_uuid(str(uuid4())))  # True

# UUID object
print(is_uuid(UUID("550e8400-e29b-41d4-a716-446655440000")))  # True

# Invalid UUIDs
print(is_uuid("invalid-uuid"))  # False
print(is_uuid("550e8400-e29b-41d4-a716"))  # False (incomplete)

# Different versions
uuid_v1 = "a8098c1a-f86e-11da-bd1a-00112444be1e"
print(is_uuid(uuid_v1, version=1))  # True
print(is_uuid(uuid_v1, version=4))  # False (wrong version)
```

---

### `is_valid_http_url(url: str) -> bool`

Check if a string is a valid HTTP or HTTPS URL.

**Description:**

Validates that a URL has a valid structure with http/https scheme and a non-empty network location (domain).

**Parameters:**

- **url** (`str`): The URL string to validate

**Returns:**

- **`bool`**: True if the URL is valid (http/https with domain), False otherwise

**Example:**

```python
from dtpyfw.core.validation import is_valid_http_url

print(is_valid_http_url("https://example.com"))  # True
print(is_valid_http_url("http://localhost:8000"))  # True
print(is_valid_http_url("https://api.example.com/v1/users"))  # True

print(is_valid_http_url("ftp://example.com"))  # False (not http/https)
print(is_valid_http_url("example.com"))  # False (no scheme)
print(is_valid_http_url("https://"))  # False (no domain)
print(is_valid_http_url("not a url"))  # False
```

## Complete Usage Examples

### 1. Form Validation

```python
from dtpyfw.core.validation import is_email, is_year

class UserRegistrationForm:
    @staticmethod
    def validate(data: dict) -> tuple[bool, list]:
        """Validate user registration form."""
        errors = []
        
        # Validate email
        if not data.get("email"):
            errors.append("Email is required")
        elif not is_email(data["email"]):
            errors.append("Invalid email format")
        
        # Validate birth year
        if data.get("birth_year"):
            if not is_year(str(data["birth_year"])):
                errors.append("Invalid birth year")
            elif int(data["birth_year"]) > 2024:
                errors.append("Birth year cannot be in the future")
        
        return len(errors) == 0, errors

# Usage
form_data = {
    "email": "user@example.com",
    "birth_year": "1990"
}

is_valid, errors = UserRegistrationForm.validate(form_data)
if not is_valid:
    print("Validation errors:", errors)
```

### 2. API Request Validation

```python
from fastapi import FastAPI, HTTPException
from dtpyfw.core.validation import is_email, is_uuid
from pydantic import BaseModel, validator

app = FastAPI()

class UserUpdateRequest(BaseModel):
    user_id: str
    email: str
    
    @validator("user_id")
    def validate_user_id(cls, v):
        if not is_uuid(v):
            raise ValueError("Invalid user ID format")
        return v
    
    @validator("email")
    def validate_email(cls, v):
        if not is_email(v):
            raise ValueError("Invalid email format")
        return v

@app.patch("/users")
def update_user(request: UserUpdateRequest):
    # Request is automatically validated
    return {"message": "User updated"}
```

### 3. Vehicle Management System

```python
from dtpyfw.core.validation import is_vin, is_year

class Vehicle:
    def __init__(self, vin: str, year: str, make: str, model: str):
        if not is_vin(vin):
            raise ValueError(f"Invalid VIN: {vin}")
        
        if not is_year(year):
            raise ValueError(f"Invalid year: {year}")
        
        self.vin = vin
        self.year = int(year)
        self.make = make
        self.model = model
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create vehicle from dictionary with validation."""
        try:
            return cls(
                vin=data["vin"],
                year=str(data["year"]),
                make=data["make"],
                model=data["model"]
            )
        except ValueError as e:
            raise ValueError(f"Invalid vehicle data: {e}")

# Usage
try:
    vehicle = Vehicle("1HGBH41JXMN109186", "2024", "Honda", "Accord")
    print(f"Valid vehicle: {vehicle.make} {vehicle.model}")
except ValueError as e:
    print(f"Error: {e}")
```

### 4. URL Validator Middleware

```python
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from dtpyfw.core.validation import is_valid_http_url

class WebhookURLValidator(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Validate webhook URLs in requests
        if request.url.path.startswith("/api/webhooks"):
            body = await request.json()
            webhook_url = body.get("webhook_url")
            
            if webhook_url and not is_valid_http_url(webhook_url):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid webhook URL format"
                )
        
        response = await call_next(request)
        return response

app = FastAPI()
app.add_middleware(WebhookURLValidator)
```

### 5. Data Import Validator

```python
from dtpyfw.core.validation import is_email, is_year, is_vin
from typing import List, Dict

class DataImportValidator:
    @staticmethod
    def validate_user_row(row: dict) -> tuple[bool, str]:
        """Validate a single user data row."""
        if not is_email(row.get("email", "")):
            return False, f"Invalid email: {row.get('email')}"
        
        if "birth_year" in row and not is_year(str(row["birth_year"])):
            return False, f"Invalid birth year: {row.get('birth_year')}"
        
        return True, ""
    
    @staticmethod
    def validate_vehicle_row(row: dict) -> tuple[bool, str]:
        """Validate a single vehicle data row."""
        if not is_vin(row.get("vin", "")):
            return False, f"Invalid VIN: {row.get('vin')}"
        
        if not is_year(str(row.get("year", ""))):
            return False, f"Invalid year: {row.get('year')}"
        
        return True, ""
    
    @staticmethod
    def validate_import(data: List[dict], row_type: str) -> Dict:
        """Validate entire import dataset."""
        results = {
            "valid_count": 0,
            "invalid_count": 0,
            "errors": []
        }
        
        validator = (
            DataImportValidator.validate_user_row
            if row_type == "user"
            else DataImportValidator.validate_vehicle_row
        )
        
        for idx, row in enumerate(data, 1):
            is_valid, error = validator(row)
            if is_valid:
                results["valid_count"] += 1
            else:
                results["invalid_count"] += 1
                results["errors"].append(f"Row {idx}: {error}")
        
        return results

# Usage
import_data = [
    {"email": "user1@example.com", "birth_year": "1990"},
    {"email": "invalid.email", "birth_year": "2050"},
    {"email": "user2@example.com", "birth_year": "1985"}
]

results = DataImportValidator.validate_import(import_data, "user")
print(f"Valid: {results['valid_count']}, Invalid: {results['invalid_count']}")
for error in results["errors"]:
    print(error)
```

### 6. Configuration Validator

```python
from dtpyfw.core.validation import is_valid_http_url
from dtpyfw.core.env import Env

class ConfigValidator:
    @staticmethod
    def validate_required_urls():
        """Validate that required URL configurations are valid."""
        url_configs = {
            "API_URL": Env.get("API_URL"),
            "WEBHOOK_URL": Env.get("WEBHOOK_URL"),
            "REDIRECT_URL": Env.get("REDIRECT_URL")
        }
        
        errors = []
        for key, url in url_configs.items():
            if not url:
                errors.append(f"{key} is not configured")
            elif not is_valid_http_url(url):
                errors.append(f"{key} has invalid URL format: {url}")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    @staticmethod
    def validate_admin_email():
        """Validate admin email configuration."""
        admin_email = Env.get("ADMIN_EMAIL")
        if not admin_email:
            raise ValueError("ADMIN_EMAIL is not configured")
        
        if not is_email(admin_email):
            raise ValueError(f"Invalid ADMIN_EMAIL format: {admin_email}")

# Usage at application startup
try:
    ConfigValidator.validate_required_urls()
    ConfigValidator.validate_admin_email()
    print("Configuration valid")
except ValueError as e:
    print(f"Configuration error: {e}")
    exit(1)
```

### 7. Batch Validation Helper

```python
from dtpyfw.core.validation import is_email, is_uuid, is_valid_http_url
from typing import List, Callable

class BatchValidator:
    VALIDATORS = {
        "email": is_email,
        "uuid": is_uuid,
        "url": is_valid_http_url
    }
    
    @classmethod
    def validate_list(
        cls,
        items: List[str],
        validator_name: str
    ) -> Dict[str, List[str]]:
        """Validate a list of items."""
        validator = cls.VALIDATORS.get(validator_name)
        if not validator:
            raise ValueError(f"Unknown validator: {validator_name}")
        
        valid = []
        invalid = []
        
        for item in items:
            if validator(item):
                valid.append(item)
            else:
                invalid.append(item)
        
        return {"valid": valid, "invalid": invalid}

# Usage
emails = [
    "user1@example.com",
    "invalid.email",
    "user2@example.com",
    "another-invalid"
]

results = BatchValidator.validate_list(emails, "email")
print(f"Valid emails: {results['valid']}")
print(f"Invalid emails: {results['invalid']}")
```

### 8. Custom Validator Composer

```python
from dtpyfw.core.validation import is_email
from typing import Callable, List

class ValidatorChain:
    def __init__(self):
        self.validators: List[Callable] = []
    
    def add_validator(self, validator: Callable, error_message: str):
        """Add a validator function to the chain."""
        self.validators.append((validator, error_message))
        return self
    
    def validate(self, value: any) -> tuple[bool, List[str]]:
        """Run all validators and collect errors."""
        errors = []
        for validator, error_message in self.validators:
            if not validator(value):
                errors.append(error_message)
        
        return len(errors) == 0, errors

# Usage
email_chain = ValidatorChain()
email_chain.add_validator(
    lambda x: isinstance(x, str),
    "Email must be a string"
).add_validator(
    lambda x: len(x) > 0,
    "Email cannot be empty"
).add_validator(
    is_email,
    "Invalid email format"
).add_validator(
    lambda x: not x.endswith("@tempmail.com"),
    "Temporary emails not allowed"
)

is_valid, errors = email_chain.validate("user@example.com")
if not is_valid:
    print("Validation errors:", errors)
```

## Best Practices

1. **Always validate user input:**
   ```python
   # Good
   if is_email(user_input):
       save_email(user_input)
   else:
       raise ValueError("Invalid email")
   
   # Risky
   # save_email(user_input)  # No validation
   ```

2. **Provide clear error messages:**
   ```python
   if not is_vin(vin):
       raise ValueError(f"Invalid VIN format: {vin}. VIN must be 17 characters.")
   ```

3. **Use in Pydantic validators:**
   ```python
   from pydantic import BaseModel, validator
   
   class User(BaseModel):
       email: str
       
       @validator("email")
       def validate_email(cls, v):
           if not is_email(v):
               raise ValueError("Invalid email format")
           return v
   ```

4. **Combine multiple validations:**
   ```python
   def validate_user_data(data: dict) -> bool:
       return (
           is_email(data.get("email", "")) and
           is_year(str(data.get("birth_year", ""))) and
           is_valid_http_url(data.get("website", "https://example.com"))
       )
   ```

## Validation Patterns

### Required vs Optional Fields

```python
from dtpyfw.core.validation import is_email

def validate_optional_email(email: str = None) -> bool:
    """Validate email only if provided."""
    if email is None or email == "":
        return True  # Optional field
    return is_email(email)
```

### Custom Error Handling

```python
from dtpyfw.core.validation import is_uuid

def get_user_by_id(user_id: str):
    if not is_uuid(user_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid user ID",
                "field": "user_id",
                "value": user_id
            }
        )
    return fetch_user(user_id)
```

## Related Modules

- **dtpyfw.api.schemas** - Pydantic schemas with validation
- **dtpyfw.core.safe_access** - Safe data access
- **dtpyfw.db.schema** - Database schema validation

## Dependencies

- `re` - Regular expressions
- `urllib.parse` - URL parsing
- `uuid` - UUID handling

## See Also

- [Python re module](https://docs.python.org/3/library/re.html)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Email Validation RFC](https://tools.ietf.org/html/rfc5322)
- [UUID Standards](https://tools.ietf.org/html/rfc4122)
