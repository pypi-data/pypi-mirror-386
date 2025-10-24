# JWT Encryption Module

## Overview

The `dtpyfw.encrypt.encryption` module provides robust JWT (JSON Web Token) encryption and decryption utilities for secure authentication and authorization workflows. This module leverages the `python-jose` library to create, sign, and validate JWT tokens with configurable algorithms and custom claims.

## Module Location

```python
from dtpyfw.encrypt.encryption import jwt_encrypt, jwt_decrypt
```

## Purpose

JWT tokens are a compact, URL-safe means of representing claims between two parties. This module enables you to:

1. **Create Tokens**: Generate signed JWT tokens with custom payload data and expiration times
2. **Validate Tokens**: Decrypt and verify token signatures, expiration, and subject claims
3. **Secure Communication**: Implement stateless authentication without server-side session storage
4. **Microservices Auth**: Share authentication state across distributed services

## Dependencies

This module requires the `python-jose` library:

```bash
pip install dtpyfw[encrypt]
# or
pip install python-jose[cryptography]
```

## Supported Algorithms

The module supports various cryptographic algorithms for token signing:

### HMAC Algorithms (Symmetric)

- **HS256**: HMAC using SHA-256 (recommended for most use cases)
- **HS384**: HMAC using SHA-384
- **HS512**: HMAC using SHA-512

**Use when**: You control both token creation and validation, and can securely share the secret key.

### RSA Algorithms (Asymmetric)

- **RS256**: RSA signature with SHA-256
- **RS384**: RSA signature with SHA-384
- **RS512**: RSA signature with SHA-512

**Use when**: Tokens are created by one service and validated by multiple services (public key distribution).

### Other Algorithms

- **ES256**, **ES384**, **ES512**: ECDSA signatures
- **PS256**, **PS384**, **PS512**: RSA-PSS signatures

## API Reference

### jwt_encrypt()

Create and sign a JWT token with the specified subject, claims, and optional expiration.

#### Signature

```python
def jwt_encrypt(
    tokens_secret_key: str,
    encryption_algorithm: str,
    subject: str,
    claims: Dict[str, Any],
    expiration_timedelta: Optional[timedelta] = None,
) -> str
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tokens_secret_key` | `str` | Yes | The secret key used for signing the JWT token. Must be kept secure and confidential. For HS256, use a strong random string (32+ characters). For RSA, use a private key in PEM format. |
| `encryption_algorithm` | `str` | Yes | The cryptographic algorithm for signing. Common values: `"HS256"`, `"HS384"`, `"HS512"`, `"RS256"`, `"RS384"`, `"RS512"`. Must match the algorithm used during decryption. |
| `subject` | `str` | Yes | The subject identifier for the token. Typically represents the user ID, username, or entity the token is issued for. Stored in the `subject` claim of the token payload. |
| `claims` | `Dict[str, Any]` | Yes | Dictionary of additional claims to embed in the token. Can include standard JWT claims (`iss`, `aud`, `iat`, etc.) or custom application-specific claims (roles, permissions, metadata). All values must be JSON-serializable. |
| `expiration_timedelta` | `Optional[timedelta]` | No | Time duration after which the token expires. If provided, sets the `exp` claim to `current_time + expiration_timedelta`. If `None`, no expiration is set (not recommended for security). |

#### Returns

| Type | Description |
|------|-------------|
| `str` | The encoded JWT token as a compact URL-safe string in the format `header.payload.signature`. This token can be transmitted via HTTP headers, URL parameters, or request bodies. |

#### Example Usage

##### Basic Token Creation

```python
from dtpyfw.encrypt.encryption import jwt_encrypt
from datetime import timedelta

# Create a simple access token
token = jwt_encrypt(
    tokens_secret_key="my-super-secret-key-keep-it-safe",
    encryption_algorithm="HS256",
    subject="user_12345",
    claims={"role": "user", "email": "user@example.com"},
    expiration_timedelta=timedelta(hours=1)
)

print(f"Generated token: {token}")
# Output: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWJqZWN0IjoidXNlcl8xMjM0NSIsImV4cCI6MTcyOTgwMzYwMC4wLCJyb2xlIjoidXNlciIsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSJ9.signature
```

##### Token with Multiple Claims

```python
from datetime import timedelta

# Create token with rich metadata
token = jwt_encrypt(
    tokens_secret_key="your-secret-key",
    encryption_algorithm="HS256",
    subject="admin_user_001",
    claims={
        "role": "admin",
        "permissions": ["read", "write", "delete"],
        "department": "engineering",
        "email": "admin@company.com",
        "session_id": "sess_abc123xyz",
        "issued_at": "2025-10-24T10:00:00Z"
    },
    expiration_timedelta=timedelta(hours=8)  # 8-hour work session
)
```

##### Long-Lived API Key

```python
from datetime import timedelta

# Create a long-lived API token for machine-to-machine communication
api_token = jwt_encrypt(
    tokens_secret_key="api-secret-key",
    encryption_algorithm="HS512",  # Stronger algorithm for long-lived tokens
    subject="service_payment_gateway",
    claims={
        "type": "api_key",
        "scopes": ["payment.create", "payment.read", "refund.create"],
        "rate_limit": 1000,  # requests per hour
        "environment": "production"
    },
    expiration_timedelta=timedelta(days=365)  # 1 year validity
)
```

##### Token Without Expiration

```python
# Create a token that never expires (not recommended for production)
permanent_token = jwt_encrypt(
    tokens_secret_key="secret",
    encryption_algorithm="HS256",
    subject="legacy_system",
    claims={"integration": "legacy_crm"},
    expiration_timedelta=None  # No expiration
)
```

##### Using RSA Algorithm

```python
# Load RSA private key
with open("private_key.pem", "r") as f:
    private_key = f.read()

token = jwt_encrypt(
    tokens_secret_key=private_key,
    encryption_algorithm="RS256",
    subject="user_001",
    claims={"role": "user"},
    expiration_timedelta=timedelta(hours=2)
)
```

#### Notes

- The `subject` claim is stored as `"subject"` in the token payload, not the standard `"sub"` claim
- All values in the `claims` dictionary are automatically JSON-encoded using the framework's `jsonable_encoder`
- The `exp` claim is set as a Unix timestamp (seconds since epoch)
- Generated tokens are stateless—all information is contained within the token itself

---

### jwt_decrypt()

Decrypt, validate, and extract claims from a JWT token.

#### Signature

```python
def jwt_decrypt(
    tokens_secret_key: str,
    encryption_algorithm: str,
    token: str,
    subject: str,
    check_exp: bool = True,
) -> Dict[str, Any]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tokens_secret_key` | `str` | Yes | The secret key used for verifying the token signature. Must be the same key used during token creation. For RSA, use the public key in PEM format. |
| `encryption_algorithm` | `str` | Yes | The cryptographic algorithm used to sign the token. Must match the algorithm used during token creation (e.g., `"HS256"`, `"RS256"`). |
| `token` | `str` | Yes | The JWT token string to decrypt and validate. Should be in the format `header.payload.signature`. |
| `subject` | `str` | Yes | The expected subject identifier to validate against the token's `subject` claim. This ensures the token was issued for the intended recipient. |
| `check_exp` | `bool` | No | Whether to validate the token's expiration time. Defaults to `True`. When `True`, requires the `exp` claim and raises `ExpiredSignatureError` if expired. Set to `False` for tokens without expiration (not recommended). |

#### Returns

| Type | Description |
|------|-------------|
| `Dict[str, Any]` | The decoded token payload containing all claims. Always includes the `subject` claim and any custom claims added during token creation. If expiration was set, includes the `exp` claim as a Unix timestamp. |

#### Raises

| Exception | When Raised |
|-----------|-------------|
| `Exception` | Raised with message `"wrong_token_subject"` if the token's subject claim does not match the expected `subject` parameter. |
| `jose.exceptions.ExpiredSignatureError` | Raised when `check_exp=True` and the token has expired (current time > `exp` claim). |
| `jose.exceptions.JWTError` | Raised for various token validation failures: invalid signature, malformed token, algorithm mismatch, or decoding errors. |
| `jose.exceptions.JWTClaimsError` | Raised when required claims are missing or invalid (e.g., missing `exp` when `check_exp=True`). |

#### Example Usage

##### Basic Token Validation

```python
from dtpyfw.encrypt.encryption import jwt_decrypt

# Decrypt and validate a token
try:
    payload = jwt_decrypt(
        tokens_secret_key="my-super-secret-key-keep-it-safe",
        encryption_algorithm="HS256",
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        subject="user_12345",
        check_exp=True
    )
    
    print(f"User ID: {payload['subject']}")
    print(f"Role: {payload['role']}")
    print(f"Email: {payload['email']}")
    
except Exception as e:
    print(f"Token validation failed: {e}")
```

##### Comprehensive Error Handling

```python
from jose import JWTError, ExpiredSignatureError
from dtpyfw.encrypt.encryption import jwt_decrypt

def validate_user_token(token: str, expected_user_id: str, secret_key: str) -> dict:
    """Validate a user token with comprehensive error handling."""
    try:
        payload = jwt_decrypt(
            tokens_secret_key=secret_key,
            encryption_algorithm="HS256",
            token=token,
            subject=expected_user_id,
            check_exp=True
        )
        return {"valid": True, "payload": payload}
    
    except ExpiredSignatureError:
        return {"valid": False, "error": "token_expired"}
    
    except JWTError as e:
        return {"valid": False, "error": f"invalid_token: {str(e)}"}
    
    except Exception as e:
        if str(e) == "wrong_token_subject":
            return {"valid": False, "error": "token_subject_mismatch"}
        return {"valid": False, "error": f"validation_error: {str(e)}"}

# Usage
result = validate_user_token(
    token=user_provided_token,
    expected_user_id="user_12345",
    secret_key="secret-key"
)

if result["valid"]:
    print(f"Welcome {result['payload']['subject']}!")
else:
    print(f"Access denied: {result['error']}")
```

##### Skip Expiration Check

```python
# Validate a token without checking expiration (use cautiously)
payload = jwt_decrypt(
    tokens_secret_key="secret-key",
    encryption_algorithm="HS256",
    token=old_token,
    subject="user_001",
    check_exp=False  # Skip expiration validation
)

# Manually check expiration if needed
if "exp" in payload:
    from datetime import datetime
    exp_time = datetime.fromtimestamp(payload["exp"])
    print(f"Token expired at: {exp_time}")
```

##### Using RSA Algorithm

```python
# Load RSA public key
with open("public_key.pem", "r") as f:
    public_key = f.read()

try:
    payload = jwt_decrypt(
        tokens_secret_key=public_key,
        encryption_algorithm="RS256",
        token=token,
        subject="user_001",
        check_exp=True
    )
except JWTError:
    print("Invalid signature or malformed token")
```

##### Extract Specific Claims

```python
from dtpyfw.encrypt.encryption import jwt_decrypt

def get_user_permissions(token: str, user_id: str, secret: str) -> list:
    """Extract permissions from a JWT token."""
    try:
        payload = jwt_decrypt(
            tokens_secret_key=secret,
            encryption_algorithm="HS256",
            token=token,
            subject=user_id,
            check_exp=True
        )
        return payload.get("permissions", [])
    
    except Exception:
        return []  # No permissions if token is invalid

# Usage
permissions = get_user_permissions(token, "user_123", "secret")
if "admin" in permissions:
    print("User has admin access")
```

#### Notes

- Subject validation is always performed—if the token's `subject` claim doesn't match the `subject` parameter, an exception is raised
- When `check_exp=True`, both `require_exp` and `verify_exp` options are set for jose's JWT decoder
- The function returns the full payload dictionary, allowing access to all embedded claims
- Token validation is cryptographically secure—tampered tokens will fail signature verification

---

## Complete Usage Examples

### Authentication Flow

```python
from dtpyfw.encrypt.encryption import jwt_encrypt, jwt_decrypt
from datetime import timedelta
from jose import ExpiredSignatureError, JWTError

SECRET_KEY = "your-application-secret-key"
ALGORITHM = "HS256"

# Step 1: User Login - Create Access and Refresh Tokens
def create_tokens(user_id: str, user_role: str):
    """Create access and refresh tokens after successful login."""
    
    # Short-lived access token (15 minutes)
    access_token = jwt_encrypt(
        tokens_secret_key=SECRET_KEY,
        encryption_algorithm=ALGORITHM,
        subject=user_id,
        claims={
            "type": "access",
            "role": user_role,
            "permissions": ["read", "write"]
        },
        expiration_timedelta=timedelta(minutes=15)
    )
    
    # Long-lived refresh token (30 days)
    refresh_token = jwt_encrypt(
        tokens_secret_key=SECRET_KEY,
        encryption_algorithm=ALGORITHM,
        subject=user_id,
        claims={
            "type": "refresh"
        },
        expiration_timedelta=timedelta(days=30)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# Step 2: Validate Access Token on Protected Endpoints
def validate_access_token(token: str) -> dict:
    """Validate an access token and return user info."""
    try:
        # Extract user_id from token first (without full validation)
        # In production, you might decode without verification first
        import json
        import base64
        
        # Decode payload to get subject (without verification)
        payload_part = token.split('.')[1]
        # Add padding if needed
        payload_part += '=' * (4 - len(payload_part) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload_part))
        user_id = decoded.get('subject')
        
        # Now validate with full checks
        payload = jwt_decrypt(
            tokens_secret_key=SECRET_KEY,
            encryption_algorithm=ALGORITHM,
            token=token,
            subject=user_id,
            check_exp=True
        )
        
        # Verify it's an access token
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        
        return {
            "authenticated": True,
            "user_id": user_id,
            "role": payload.get("role"),
            "permissions": payload.get("permissions", [])
        }
    
    except ExpiredSignatureError:
        return {"authenticated": False, "error": "token_expired"}
    except (JWTError, ValueError, Exception) as e:
        return {"authenticated": False, "error": str(e)}

# Step 3: Refresh Access Token using Refresh Token
def refresh_access_token(refresh_token: str) -> dict:
    """Generate a new access token using a refresh token."""
    try:
        # Extract user_id from refresh token
        import json, base64
        payload_part = refresh_token.split('.')[1]
        payload_part += '=' * (4 - len(payload_part) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload_part))
        user_id = decoded.get('subject')
        
        # Validate refresh token
        payload = jwt_decrypt(
            tokens_secret_key=SECRET_KEY,
            encryption_algorithm=ALGORITHM,
            token=refresh_token,
            subject=user_id,
            check_exp=True
        )
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        
        # Fetch user role from database (in production)
        user_role = "user"  # Placeholder
        
        # Create new access token
        new_access_token = jwt_encrypt(
            tokens_secret_key=SECRET_KEY,
            encryption_algorithm=ALGORITHM,
            subject=user_id,
            claims={
                "type": "access",
                "role": user_role,
                "permissions": ["read", "write"]
            },
            expiration_timedelta=timedelta(minutes=15)
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    
    except Exception as e:
        return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    # Login
    tokens = create_tokens(user_id="user_123", user_role="admin")
    print(f"Access Token: {tokens['access_token'][:50]}...")
    print(f"Refresh Token: {tokens['refresh_token'][:50]}...")
    
    # Validate access token
    auth_result = validate_access_token(tokens['access_token'])
    print(f"Authentication: {auth_result}")
    
    # Refresh access token
    new_tokens = refresh_access_token(tokens['refresh_token'])
    print(f"New Access Token: {new_tokens.get('access_token', 'N/A')[:50]}...")
```

### API Key Management

```python
from dtpyfw.encrypt.encryption import jwt_encrypt, jwt_decrypt
from datetime import timedelta
import secrets

class APIKeyManager:
    """Manage API keys for external integrations."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS512"  # Stronger algorithm for API keys
    
    def create_api_key(self, client_id: str, scopes: list, 
                       valid_days: int = 365) -> str:
        """Create a new API key with specified permissions."""
        return jwt_encrypt(
            tokens_secret_key=self.secret_key,
            encryption_algorithm=self.algorithm,
            subject=client_id,
            claims={
                "type": "api_key",
                "scopes": scopes,
                "key_id": secrets.token_hex(16),
                "created_at": "2025-10-24T10:00:00Z"
            },
            expiration_timedelta=timedelta(days=valid_days)
        )
    
    def validate_api_key(self, api_key: str, required_scope: str) -> dict:
        """Validate an API key and check for required scope."""
        try:
            # Extract client_id
            import json, base64
            payload_part = api_key.split('.')[1]
            payload_part += '=' * (4 - len(payload_part) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload_part))
            client_id = decoded.get('subject')
            
            # Validate API key
            payload = jwt_decrypt(
                tokens_secret_key=self.secret_key,
                encryption_algorithm=self.algorithm,
                token=api_key,
                subject=client_id,
                check_exp=True
            )
            
            # Check scope
            scopes = payload.get("scopes", [])
            has_scope = required_scope in scopes
            
            return {
                "valid": True,
                "client_id": client_id,
                "has_scope": has_scope,
                "scopes": scopes
            }
        
        except Exception as e:
            return {"valid": False, "error": str(e)}

# Usage
manager = APIKeyManager(secret_key="api-master-secret")

# Create API key for a client
api_key = manager.create_api_key(
    client_id="client_acme_corp",
    scopes=["payment.read", "payment.create", "customer.read"],
    valid_days=365
)
print(f"API Key: {api_key}")

# Validate and check permissions
result = manager.validate_api_key(api_key, required_scope="payment.create")
if result["valid"] and result["has_scope"]:
    print("Access granted")
else:
    print("Access denied")
```

### Microservices Authentication

```python
from dtpyfw.encrypt.encryption import jwt_encrypt, jwt_decrypt
from datetime import timedelta

class ServiceAuthenticator:
    """Handle authentication between microservices."""
    
    def __init__(self, service_secret: str):
        self.secret = service_secret
        self.algorithm = "HS256"
    
    def create_service_token(self, from_service: str, to_service: str, 
                            request_id: str) -> str:
        """Create a token for service-to-service communication."""
        return jwt_encrypt(
            tokens_secret_key=self.secret,
            encryption_algorithm=self.algorithm,
            subject=from_service,
            claims={
                "target_service": to_service,
                "request_id": request_id,
                "type": "service_token"
            },
            expiration_timedelta=timedelta(minutes=5)  # Short-lived
        )
    
    def validate_service_token(self, token: str, 
                              expected_service: str) -> dict:
        """Validate a service token."""
        try:
            # Extract subject
            import json, base64
            payload_part = token.split('.')[1]
            payload_part += '=' * (4 - len(payload_part) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload_part))
            from_service = decoded.get('subject')
            
            payload = jwt_decrypt(
                tokens_secret_key=self.secret,
                encryption_algorithm=self.algorithm,
                token=token,
                subject=from_service,
                check_exp=True
            )
            
            # Verify target service
            if payload.get("target_service") != expected_service:
                raise ValueError("Token not intended for this service")
            
            return {
                "valid": True,
                "from_service": from_service,
                "request_id": payload.get("request_id")
            }
        
        except Exception as e:
            return {"valid": False, "error": str(e)}

# Usage
auth = ServiceAuthenticator(service_secret="shared-secret-key")

# Service A calls Service B
token = auth.create_service_token(
    from_service="order-service",
    to_service="payment-service",
    request_id="req_12345"
)

# Service B validates the token
result = auth.validate_service_token(token, expected_service="payment-service")
if result["valid"]:
    print(f"Request from {result['from_service']}: {result['request_id']}")
```

## Security Best Practices

### 1. Secret Key Management

```python
import os

# ✅ GOOD: Use environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable not set")

# ❌ BAD: Hardcoded secrets
SECRET_KEY = "my-secret-key"  # Never do this!
```

### 2. Strong Secret Keys

```python
import secrets

# Generate a strong secret key (run once, store securely)
def generate_secret_key(length: int = 64) -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(length)

# For HS256, HS384, HS512
secret = generate_secret_key(64)  # At least 32 bytes recommended
```

### 3. Token Expiration

```python
from datetime import timedelta

# ✅ GOOD: Short-lived tokens
access_token = jwt_encrypt(
    tokens_secret_key=secret,
    encryption_algorithm="HS256",
    subject="user",
    claims={},
    expiration_timedelta=timedelta(minutes=15)  # 15 minutes
)

# ❌ BAD: No expiration or very long expiration
bad_token = jwt_encrypt(
    tokens_secret_key=secret,
    encryption_algorithm="HS256",
    subject="user",
    claims={},
    expiration_timedelta=None  # Never expires!
)
```

### 4. HTTPS Only

Always transmit JWT tokens over HTTPS to prevent interception:

```python
# In FastAPI
from fastapi import Header, HTTPException

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    
    token = authorization.split(" ")[1]
    # Validate token...
```

### 5. Token Validation

```python
def validate_token_strict(token: str, expected_user: str, secret: str) -> dict:
    """Strictly validate all aspects of a token."""
    try:
        # Always check expiration
        payload = jwt_decrypt(
            tokens_secret_key=secret,
            encryption_algorithm="HS256",
            token=token,
            subject=expected_user,
            check_exp=True  # Always True for production
        )
        
        # Additional validation
        token_type = payload.get("type")
        if token_type not in ["access", "refresh"]:
            raise ValueError("Invalid token type")
        
        # Check for token revocation (if using a blacklist)
        # if is_token_blacklisted(payload.get("jti")):
        #     raise ValueError("Token has been revoked")
        
        return payload
    
    except Exception:
        return None
```

## Common Patterns

### Token Refresh Pattern

```python
from datetime import timedelta

# Create tokens with different lifetimes
def create_token_pair(user_id: str, secret: str):
    access_token = jwt_encrypt(
        tokens_secret_key=secret,
        encryption_algorithm="HS256",
        subject=user_id,
        claims={"type": "access"},
        expiration_timedelta=timedelta(minutes=15)
    )
    
    refresh_token = jwt_encrypt(
        tokens_secret_key=secret,
        encryption_algorithm="HS256",
        subject=user_id,
        claims={"type": "refresh"},
        expiration_timedelta=timedelta(days=30)
    )
    
    return access_token, refresh_token
```

### Token Blacklist Pattern

```python
# Store revoked tokens (simplified example)
revoked_tokens = set()

def revoke_token(token: str):
    """Add token to blacklist."""
    revoked_tokens.add(token)

def is_token_revoked(token: str) -> bool:
    """Check if token is blacklisted."""
    return token in revoked_tokens

def validate_with_blacklist(token: str, user_id: str, secret: str):
    """Validate token and check blacklist."""
    if is_token_revoked(token):
        raise ValueError("Token has been revoked")
    
    return jwt_decrypt(
        tokens_secret_key=secret,
        encryption_algorithm="HS256",
        token=token,
        subject=user_id,
        check_exp=True
    )
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dtpyfw.encrypt.encryption import jwt_encrypt, jwt_decrypt
from datetime import timedelta

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "your-secret-key"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to extract and validate user from token."""
    try:
        # Extract user_id
        import json, base64
        payload_part = token.split('.')[1]
        payload_part += '=' * (4 - len(payload_part) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload_part))
        user_id = decoded.get('subject')
        
        payload = jwt_decrypt(
            tokens_secret_key=SECRET_KEY,
            encryption_algorithm="HS256",
            token=token,
            subject=user_id,
            check_exp=True
        )
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['subject']}"}
```

### Flask Integration

```python
from flask import Flask, request, jsonify
from functools import wraps
from dtpyfw.encrypt.encryption import jwt_decrypt

app = Flask(__name__)
SECRET_KEY = "your-secret-key"

def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove "Bearer " prefix
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Extract user_id and validate
            import json, base64
            payload_part = token.split('.')[1]
            payload_part += '=' * (4 - len(payload_part) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload_part))
            user_id = decoded.get('subject')
            
            payload = jwt_decrypt(
                tokens_secret_key=SECRET_KEY,
                encryption_algorithm="HS256",
                token=token,
                subject=user_id,
                check_exp=True
            )
            
            request.current_user = payload
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@app.route('/protected')
@token_required
def protected():
    return jsonify({'user': request.current_user['subject']})
```

## Troubleshooting

### Common Errors

#### 1. "wrong_token_subject"

**Cause**: The token's subject claim doesn't match the expected subject.

**Solution**:
```python
# Ensure you're using the correct user_id
token = jwt_encrypt(..., subject="user_123", ...)
# Must match during decryption
payload = jwt_decrypt(..., subject="user_123", ...)  # Not "user_456"!
```

#### 2. ExpiredSignatureError

**Cause**: Token has expired.

**Solution**:
```python
from jose import ExpiredSignatureError

try:
    payload = jwt_decrypt(..., check_exp=True)
except ExpiredSignatureError:
    # Prompt user to refresh token or login again
    return {"error": "token_expired", "action": "refresh_or_login"}
```

#### 3. JWTError: Signature verification failed

**Cause**: Token signature is invalid (wrong secret key or tampered token).

**Solution**:
```python
# Ensure secret keys match
# Encryption:
token = jwt_encrypt(tokens_secret_key="secret-A", ...)

# Decryption:
payload = jwt_decrypt(tokens_secret_key="secret-A", ...)  # Must be same!
```

#### 4. Algorithm Mismatch

**Cause**: Different algorithms used for encryption and decryption.

**Solution**:
```python
# Both must use the same algorithm
token = jwt_encrypt(..., encryption_algorithm="HS256", ...)
payload = jwt_decrypt(..., encryption_algorithm="HS256", ...)  # Match!
```

## Performance Considerations

- **Token Size**: JWT tokens can be large if you include many claims. Keep claims minimal.
- **Validation Speed**: Token validation is fast (~0.1-1ms per token) and suitable for high-throughput applications.
- **No Database Lookups**: JWT tokens are stateless—no database queries needed for validation.

```python
# ✅ GOOD: Minimal claims
claims = {"role": "user"}

# ⚠️ CAUTION: Large claims increase token size
claims = {
    "role": "user",
    "permissions": [...100 permissions...],
    "metadata": {...large object...}
}
```

## Related Documentation

- [Hashing Module](./hashing.md) - Password hashing utilities
- [Core Module](../core/__init__.md) - Core framework utilities
- [API Module](../api/application.md) - FastAPI integration

## External References

- [JWT.io](https://jwt.io/) - JWT specification and debugger
- [python-jose Documentation](https://python-jose.readthedocs.io/)
- [RFC 7519: JWT Specification](https://tools.ietf.org/html/rfc7519)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
