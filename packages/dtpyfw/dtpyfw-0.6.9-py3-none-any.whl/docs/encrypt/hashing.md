# Password Hashing Module

## Overview

The `dtpyfw.encrypt.hashing` module provides secure password hashing and verification utilities using industry-standard algorithms. This module leverages the `passlib` library to implement Argon2 and bcrypt hashing schemes, with Argon2 as the primary recommended algorithm and bcrypt for backward compatibility.

## Module Location

```python
from dtpyfw.encrypt.hashing import Hash
```

## Purpose

Password hashing is essential for secure authentication systems. This module enables you to:

1. **Hash Passwords**: Convert plaintext passwords into secure, one-way hashes for storage
2. **Verify Passwords**: Validate user-provided passwords against stored hashes during authentication
3. **Migrate Hashes**: Identify and upgrade legacy password hashes to stronger algorithms
4. **Prevent Attacks**: Protect against rainbow tables, brute force, and timing attacks

## Dependencies

This module requires the `passlib` library with Argon2 support:

```bash
pip install dtpyfw[encrypt]
# or
pip install passlib[argon2]
```

## Hashing Algorithms

### Argon2 (Primary - Recommended)

**Argon2** is the winner of the Password Hashing Competition (2015) and is currently the recommended algorithm for password hashing.

**Advantages**:
- Memory-hard algorithm (resistant to GPU/ASIC attacks)
- Configurable time, memory, and parallelism parameters
- Three variants: Argon2i (optimized against side-channel attacks), Argon2d (optimized against GPU attacks), Argon2id (hybrid - default)
- Industry standard for new applications

**Hash Format**: `$argon2id$v=19$m=65536,t=3,p=4$salt$hash`

### bcrypt (Deprecated - Legacy Support)

**bcrypt** is an older but still secure hashing algorithm based on the Blowfish cipher.

**Status**: Marked as deprecated in this module's configuration

**Use Cases**:
- Verifying existing passwords hashed with bcrypt
- Backward compatibility with legacy systems
- Automatic migration to Argon2 on next login

**Hash Format**: `$2b$12$salt_and_hash`

**Note**: The module disables bcrypt truncation errors (`bcrypt__truncate_error=False`) for compatibility with passwords longer than 72 bytes.

## Password Context Configuration

The module uses a pre-configured `CryptContext` from passlib:

```python
from passlib.context import CryptContext

pwd_cxt: CryptContext = CryptContext(
    schemes=["argon2", "bcrypt"],      # Supported algorithms
    deprecated=["bcrypt"],              # bcrypt marked as deprecated
    bcrypt__truncate_error=False,       # Disable bcrypt truncation warnings
)
```

This configuration:
- Uses Argon2 for all new password hashes
- Accepts and verifies bcrypt hashes (for legacy passwords)
- Automatically identifies bcrypt hashes as needing updates
- Handles long passwords gracefully with bcrypt

## API Reference

### Hash Class

The `Hash` class provides static methods for password operations. It is designed to be used without instantiation.

```python
class Hash:
    """Password hashing and verification using Argon2 and bcrypt."""
    
    @staticmethod
    def crypt(password: str) -> str:
        """Hash a password using Argon2."""
        
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        
    @staticmethod
    def needs_update(hashed_password: str) -> bool:
        """Check if a hash should be upgraded."""
```

---

### Hash.crypt()

Hash a plaintext password using the Argon2 algorithm.

#### Method Signature

```python
@staticmethod
def crypt(password: str) -> str
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `password` | `str` | Yes | The plaintext password to hash. Can be any length, though extremely long passwords may be handled differently by the algorithm. Should be the raw password string provided by the user. |

#### Returns

| Type | Description |
|------|-------------|
| `str` | The hashed password string in passlib's modular crypt format. Includes the algorithm identifier (`$argon2id$`), version, parameters, salt, and hash value. This string is safe to store directly in databases. Format: `$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>` |

#### Behavior

- Generates a unique random salt for each hash (even for identical passwords)
- Uses Argon2id variant by default (balanced security)
- Returns different hashes for the same password on each call (expected and secure)
- The hash is self-contained—includes all parameters needed for verification
- Typical execution time: 100-500ms (intentionally slow to prevent brute force)

#### Example Usage

##### Basic Password Hashing

```python
from dtpyfw.encrypt.hashing import Hash

# Hash a user's password during registration
password = "MySecureP@ssw0rd"
hashed = Hash.crypt(password)

print(f"Original: {password}")
print(f"Hashed: {hashed}")
# Output: $argon2id$v=19$m=65536,t=3,p=4$randomsalt$randomhash

# Store hashed password in database
# db.users.update(user_id, {"password": hashed})
```

##### Multiple Hashes Are Different

```python
from dtpyfw.encrypt.hashing import Hash

password = "same_password"

hash1 = Hash.crypt(password)
hash2 = Hash.crypt(password)

print(f"Hash 1: {hash1}")
print(f"Hash 2: {hash2}")
print(f"Hashes are different: {hash1 != hash2}")  # True

# This is expected behavior due to random salts
# Both hashes will verify successfully against the same password
```

##### User Registration Example

```python
from dtpyfw.encrypt.hashing import Hash

def register_user(username: str, password: str) -> dict:
    """Register a new user with hashed password."""
    
    # Validate password strength (add your rules)
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    # Hash the password
    hashed_password = Hash.crypt(password)
    
    # Store in database
    user_data = {
        "username": username,
        "password": hashed_password,  # Only store the hash!
        "created_at": "2025-10-24T10:00:00Z"
    }
    
    # db.users.insert(user_data)
    return user_data

# Usage
user = register_user("john_doe", "SecurePass123!")
print(f"User created: {user['username']}")
print(f"Password hash: {user['password'][:50]}...")
```

##### Batch Password Hashing

```python
from dtpyfw.encrypt.hashing import Hash

def hash_multiple_passwords(passwords: list) -> dict:
    """Hash multiple passwords and return mapping."""
    return {pwd: Hash.crypt(pwd) for pwd in passwords}

# Hash passwords for multiple users
passwords = ["user1_pass", "user2_pass", "user3_pass"]
hashed_map = hash_multiple_passwords(passwords)

for original, hashed in hashed_map.items():
    print(f"{original} -> {hashed[:30]}...")
```

#### Notes

- Never store plaintext passwords—always hash them before storing
- Each hash includes a unique random salt, so identical passwords produce different hashes
- The hashing operation is intentionally slow (CPU/memory intensive) to prevent brute force attacks
- The returned hash string is URL-safe and can be stored in text columns
- Typical hash length: 90-100 characters for Argon2

---

### Hash.verify()

Verify a plaintext password against a stored hash.

#### Method Signature

```python
@staticmethod
def verify(plain_password: str, hashed_password: str) -> bool
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `plain_password` | `str` | Yes | The plaintext password string provided by the user during authentication. This is compared against the stored hash. |
| `hashed_password` | `str` | Yes | The previously hashed password string retrieved from storage (database). Should be a valid hash in passlib's modular crypt format (Argon2 or bcrypt). |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | `True` if the plaintext password matches the hash, `False` otherwise. Returns `False` for malformed hashes, algorithm mismatches, or incorrect passwords. |

#### Behavior

- Uses constant-time comparison to prevent timing attacks
- Automatically detects the hashing algorithm from the hash string prefix
- Works with both Argon2 (`$argon2id$...`) and bcrypt (`$2b$...`) hashes
- Returns `False` gracefully for invalid hash formats (no exceptions)
- Typical execution time: 100-500ms (matches hashing time)

#### Example Usage

##### Basic Password Verification

```python
from dtpyfw.encrypt.hashing import Hash

# During user login
def authenticate_user(username: str, password: str, stored_hash: str) -> bool:
    """Authenticate a user by verifying their password."""
    
    # Verify the provided password against the stored hash
    is_valid = Hash.verify(password, stored_hash)
    
    if is_valid:
        print(f"User {username} authenticated successfully")
        return True
    else:
        print(f"Invalid password for user {username}")
        return False

# Example usage
stored_hash = "$argon2id$v=19$m=65536,t=3,p=4$..."  # From database
result = authenticate_user("john_doe", "SecurePass123!", stored_hash)
```

##### Login Endpoint Example

```python
from dtpyfw.encrypt.hashing import Hash

def login(username: str, password: str) -> dict:
    """Handle user login with password verification."""
    
    # Fetch user from database
    user = get_user_from_database(username)
    
    if not user:
        return {"success": False, "error": "User not found"}
    
    # Verify password
    is_valid = Hash.verify(password, user["password_hash"])
    
    if not is_valid:
        # Log failed attempt
        log_failed_login(username)
        return {"success": False, "error": "Invalid password"}
    
    # Password is correct
    return {
        "success": True,
        "user_id": user["id"],
        "username": user["username"]
    }

# Usage
result = login("john_doe", "user_password")
if result["success"]:
    print(f"Welcome {result['username']}!")
else:
    print(f"Login failed: {result['error']}")
```

##### Verify with Rate Limiting

```python
from dtpyfw.encrypt.hashing import Hash
import time

class LoginAttemptTracker:
    """Track failed login attempts."""
    
    def __init__(self):
        self.attempts = {}  # username -> (count, last_attempt_time)
    
    def check_rate_limit(self, username: str) -> bool:
        """Check if user is rate limited."""
        if username not in self.attempts:
            return True
        
        count, last_time = self.attempts[username]
        
        # Reset after 15 minutes
        if time.time() - last_time > 900:
            del self.attempts[username]
            return True
        
        # Max 5 attempts
        return count < 5
    
    def record_attempt(self, username: str, success: bool):
        """Record a login attempt."""
        if success and username in self.attempts:
            del self.attempts[username]
        elif not success:
            count, _ = self.attempts.get(username, (0, 0))
            self.attempts[username] = (count + 1, time.time())

tracker = LoginAttemptTracker()

def secure_login(username: str, password: str, stored_hash: str) -> dict:
    """Login with rate limiting."""
    
    # Check rate limit
    if not tracker.check_rate_limit(username):
        return {"success": False, "error": "Too many failed attempts. Try again later."}
    
    # Verify password
    is_valid = Hash.verify(password, stored_hash)
    
    # Record attempt
    tracker.record_attempt(username, is_valid)
    
    if is_valid:
        return {"success": True, "message": "Login successful"}
    else:
        return {"success": False, "error": "Invalid credentials"}
```

##### Handling Invalid Hashes

```python
from dtpyfw.encrypt.hashing import Hash

# Verify returns False for invalid hashes (doesn't raise exceptions)
results = [
    Hash.verify("password", ""),                    # False - empty hash
    Hash.verify("password", "invalid_format"),      # False - invalid format
    Hash.verify("password", "$invalid$hash$"),      # False - unknown algorithm
    Hash.verify("", valid_hash),                    # False - empty password
]

print(f"All invalid: {all(not r for r in results)}")  # True
```

##### Verifying bcrypt Hashes (Legacy)

```python
from dtpyfw.encrypt.hashing import Hash

# The module automatically detects and verifies bcrypt hashes
bcrypt_hash = "$2b$12$oldBcryptHashFromLegacySystem..."
password = "old_user_password"

# Works seamlessly with bcrypt hashes
is_valid = Hash.verify(password, bcrypt_hash)

if is_valid:
    print("Password verified (bcrypt hash)")
    
    # Consider upgrading the hash
    if Hash.needs_update(bcrypt_hash):
        new_hash = Hash.crypt(password)
        # Update database with new Argon2 hash
        print("Hash upgraded to Argon2")
```

#### Security Notes

- Uses constant-time comparison to prevent timing attacks
- Failed verifications take the same time as successful ones
- Always returns boolean—never raises exceptions for invalid inputs
- Log failed attempts for security monitoring
- Implement rate limiting to prevent brute force attacks

---

### Hash.needs_update()

Check if a password hash should be re-hashed with current algorithm settings.

#### Method Signature

```python
@staticmethod
def needs_update(hashed_password: str) -> bool
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `hashed_password` | `str` | Yes | The stored password hash string to evaluate. Should be a valid hash in passlib's modular crypt format (Argon2 or bcrypt). |

#### Returns

| Type | Description |
|------|-------------|
| `bool` | `True` if the hash should be re-hashed with current settings (e.g., bcrypt hash that should be upgraded to Argon2), `False` if the hash is already using the current algorithm and parameters. |

#### Behavior

- Returns `True` for bcrypt hashes (marked as deprecated)
- Returns `False` for Argon2 hashes (current algorithm)
- Enables transparent migration from legacy hashing schemes
- Does not modify the hash—only checks if it needs updating
- Can be used to identify weak or outdated hashes

#### Use Cases

1. **Algorithm Migration**: Upgrading from bcrypt to Argon2
2. **Parameter Updates**: When Argon2 parameters are strengthened
3. **Security Audits**: Identifying users with outdated password hashes
4. **Transparent Upgrades**: Re-hashing passwords on successful login

#### Example Usage

##### Basic Hash Update Check

```python
from dtpyfw.encrypt.hashing import Hash

# Check if a hash needs updating
argon2_hash = "$argon2id$v=19$m=65536,t=3,p=4$..."
bcrypt_hash = "$2b$12$..."

print(f"Argon2 needs update: {Hash.needs_update(argon2_hash)}")  # False
print(f"bcrypt needs update: {Hash.needs_update(bcrypt_hash)}")  # True
```

##### Transparent Password Migration

```python
from dtpyfw.encrypt.hashing import Hash

def login_with_migration(username: str, password: str, stored_hash: str) -> dict:
    """Login with automatic password hash migration."""
    
    # Verify password
    if not Hash.verify(password, stored_hash):
        return {"success": False, "error": "Invalid credentials"}
    
    # Check if hash needs updating
    if Hash.needs_update(stored_hash):
        # Re-hash with current algorithm (Argon2)
        new_hash = Hash.crypt(password)
        
        # Update database
        update_user_password(username, new_hash)
        
        print(f"Migrated password hash for {username} from bcrypt to Argon2")
        
        return {
            "success": True,
            "migrated": True,
            "message": "Login successful (password upgraded)"
        }
    
    return {"success": True, "migrated": False, "message": "Login successful"}

# Usage
result = login_with_migration("legacy_user", "password123", bcrypt_hash)
```

##### Batch Migration Script

```python
from dtpyfw.encrypt.hashing import Hash

def identify_users_needing_migration(users: list) -> list:
    """Identify users with outdated password hashes."""
    
    needs_migration = []
    
    for user in users:
        if Hash.needs_update(user["password_hash"]):
            needs_migration.append({
                "user_id": user["id"],
                "username": user["username"],
                "current_hash": user["password_hash"][:20] + "..."
            })
    
    return needs_migration

# Get all users from database
all_users = get_all_users_from_database()

# Find users with outdated hashes
migration_list = identify_users_needing_migration(all_users)

print(f"Users needing migration: {len(migration_list)}")
for user in migration_list:
    print(f"- {user['username']} (ID: {user['user_id']})")

# Users will be migrated on their next successful login
```

##### Proactive Migration (Requires Re-authentication)

```python
from dtpyfw.encrypt.hashing import Hash

def force_password_reset_for_outdated_hashes():
    """Force password reset for users with outdated hashes."""
    
    users = get_all_users_from_database()
    users_to_reset = []
    
    for user in users:
        if Hash.needs_update(user["password_hash"]):
            # Mark account for password reset
            mark_user_for_password_reset(user["id"])
            users_to_reset.append(user["username"])
    
    print(f"Marked {len(users_to_reset)} users for password reset")
    return users_to_reset

# This approach requires users to reset their passwords
# but ensures immediate migration
```

##### Audit Report

```python
from dtpyfw.encrypt.hashing import Hash

def generate_password_hash_audit() -> dict:
    """Generate audit report of password hash status."""
    
    users = get_all_users_from_database()
    
    stats = {
        "total_users": len(users),
        "argon2_users": 0,
        "bcrypt_users": 0,
        "unknown_users": 0
    }
    
    for user in users:
        hash_str = user["password_hash"]
        
        if hash_str.startswith("$argon2"):
            stats["argon2_users"] += 1
        elif hash_str.startswith("$2b$"):
            stats["bcrypt_users"] += 1
        else:
            stats["unknown_users"] += 1
    
    stats["migration_percentage"] = (
        stats["argon2_users"] / stats["total_users"] * 100
    )
    
    return stats

# Generate report
report = generate_password_hash_audit()
print(f"Password Hash Audit Report:")
print(f"  Total Users: {report['total_users']}")
print(f"  Argon2 (current): {report['argon2_users']}")
print(f"  bcrypt (deprecated): {report['bcrypt_users']}")
print(f"  Unknown: {report['unknown_users']}")
print(f"  Migration Progress: {report['migration_percentage']:.1f}%")
```

#### Migration Strategy

**Recommended Approach**: Transparent migration on login

1. User logs in with their password
2. Verify password against stored hash (bcrypt or Argon2)
3. If verification succeeds and `needs_update()` returns `True`:
   - Re-hash password with current algorithm (Argon2)
   - Update database with new hash
   - User doesn't notice any change
4. Over time, all active users migrate automatically

**Benefits**:
- No user disruption
- No mass password resets required
- Gradual, seamless migration
- Inactive accounts can be handled separately

---

## Complete Usage Examples

### User Registration and Login System

```python
from dtpyfw.encrypt.hashing import Hash
from datetime import datetime

class UserAuthentication:
    """Complete user authentication system."""
    
    def __init__(self):
        self.users = {}  # In production, use a database
    
    def register(self, username: str, password: str) -> dict:
        """Register a new user."""
        
        # Validate username
        if username in self.users:
            return {"success": False, "error": "Username already exists"}
        
        # Validate password strength
        if not self._is_strong_password(password):
            return {
                "success": False,
                "error": "Password must be at least 8 characters with uppercase, lowercase, and numbers"
            }
        
        # Hash password
        hashed = Hash.crypt(password)
        
        # Store user
        self.users[username] = {
            "password_hash": hashed,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        return {"success": True, "message": "User registered successfully"}
    
    def login(self, username: str, password: str) -> dict:
        """Authenticate a user."""
        
        # Check if user exists
        if username not in self.users:
            return {"success": False, "error": "Invalid credentials"}
        
        user = self.users[username]
        
        # Verify password
        if not Hash.verify(password, user["password_hash"]):
            return {"success": False, "error": "Invalid credentials"}
        
        # Check if hash needs updating
        if Hash.needs_update(user["password_hash"]):
            # Re-hash with current algorithm
            new_hash = Hash.crypt(password)
            self.users[username]["password_hash"] = new_hash
            print(f"Password hash upgraded for {username}")
        
        # Update last login
        self.users[username]["last_login"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "username": username,
                "last_login": user["last_login"]
            }
        }
    
    def change_password(self, username: str, old_password: str, 
                       new_password: str) -> dict:
        """Change user password."""
        
        # Verify user exists
        if username not in self.users:
            return {"success": False, "error": "User not found"}
        
        user = self.users[username]
        
        # Verify old password
        if not Hash.verify(old_password, user["password_hash"]):
            return {"success": False, "error": "Current password is incorrect"}
        
        # Validate new password
        if not self._is_strong_password(new_password):
            return {"success": False, "error": "New password is too weak"}
        
        # Hash and store new password
        new_hash = Hash.crypt(new_password)
        self.users[username]["password_hash"] = new_hash
        
        return {"success": True, "message": "Password changed successfully"}
    
    @staticmethod
    def _is_strong_password(password: str) -> bool:
        """Validate password strength."""
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True

# Usage example
auth = UserAuthentication()

# Register users
print(auth.register("john_doe", "SecurePass123"))
print(auth.register("jane_smith", "AnotherPass456"))

# Login
print(auth.login("john_doe", "SecurePass123"))
print(auth.login("john_doe", "wrong_password"))

# Change password
print(auth.change_password("john_doe", "SecurePass123", "NewSecurePass789"))
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from dtpyfw.encrypt.hashing import Hash

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simulated database
fake_users_db = {}

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str
    disabled: bool = False

@app.post("/register")
async def register(user: UserCreate):
    """Register a new user."""
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password
    hashed_password = Hash.crypt(user.password)
    
    # Store user
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed_password,
        "disabled": False
    }
    
    return {"message": "User created successfully"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return token."""
    user = fake_users_db.get(form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not Hash.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if hash needs updating
    if Hash.needs_update(user["hashed_password"]):
        new_hash = Hash.crypt(form_data.password)
        fake_users_db[form_data.username]["hashed_password"] = new_hash
    
    # Return token (simplified - use JWT in production)
    return {"access_token": form_data.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    """Get current user info."""
    user = fake_users_db.get(token)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)
```

### Password Reset Flow

```python
from dtpyfw.encrypt.hashing import Hash
import secrets
from datetime import datetime, timedelta

class PasswordResetManager:
    """Manage password reset tokens and processes."""
    
    def __init__(self):
        self.reset_tokens = {}  # token -> (username, expiry)
    
    def request_reset(self, username: str, email: str) -> str:
        """Generate a password reset token."""
        
        # Verify user exists (check database in production)
        if not user_exists(username, email):
            # Don't reveal if user exists
            return "If the email exists, a reset link has been sent"
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Store token with 1-hour expiry
        expiry = datetime.now() + timedelta(hours=1)
        self.reset_tokens[token] = (username, expiry)
        
        # Send email with reset link (implement email sending)
        reset_link = f"https://example.com/reset-password?token={token}"
        # send_email(email, "Password Reset", f"Click here: {reset_link}")
        
        return "If the email exists, a reset link has been sent"
    
    def reset_password(self, token: str, new_password: str) -> dict:
        """Reset password using token."""
        
        # Validate token
        if token not in self.reset_tokens:
            return {"success": False, "error": "Invalid or expired token"}
        
        username, expiry = self.reset_tokens[token]
        
        # Check expiry
        if datetime.now() > expiry:
            del self.reset_tokens[token]
            return {"success": False, "error": "Token has expired"}
        
        # Validate new password
        if len(new_password) < 8:
            return {"success": False, "error": "Password too weak"}
        
        # Hash new password
        new_hash = Hash.crypt(new_password)
        
        # Update database
        update_user_password(username, new_hash)
        
        # Invalidate token
        del self.reset_tokens[token]
        
        return {"success": True, "message": "Password reset successfully"}

# Usage
manager = PasswordResetManager()

# User requests reset
manager.request_reset("john_doe", "john@example.com")

# User clicks link and submits new password
result = manager.reset_password(token="abc123...", new_password="NewPass123")
print(result)
```

## Security Best Practices

### 1. Never Store Plaintext Passwords

```python
from dtpyfw.encrypt.hashing import Hash

# ✅ GOOD: Always hash passwords
hashed = Hash.crypt(user_password)
db.store(username, hashed)

# ❌ BAD: Never store plaintext
db.store(username, user_password)  # NEVER DO THIS!
```

### 2. Validate Password Strength

```python
def validate_password(password: str) -> tuple:
    """Validate password meets security requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letters"
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain numbers"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain special characters"
    return True, "Password is strong"

# Use before hashing
is_valid, message = validate_password(user_password)
if is_valid:
    hashed = Hash.crypt(user_password)
else:
    return {"error": message}
```

### 3. Implement Rate Limiting

```python
from collections import defaultdict
import time

class RateLimiter:
    """Simple rate limiter for login attempts."""
    
    def __init__(self, max_attempts=5, window_seconds=900):
        self.attempts = defaultdict(list)
        self.max_attempts = max_attempts
        self.window = window_seconds
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if attempt is allowed."""
        now = time.time()
        
        # Clean old attempts
        self.attempts[identifier] = [
            t for t in self.attempts[identifier]
            if now - t < self.window
        ]
        
        # Check limit
        if len(self.attempts[identifier]) >= self.max_attempts:
            return False
        
        # Record attempt
        self.attempts[identifier].append(now)
        return True

limiter = RateLimiter()

def safe_login(username: str, password: str, stored_hash: str) -> dict:
    """Login with rate limiting."""
    if not limiter.is_allowed(username):
        return {"success": False, "error": "Too many attempts. Try again later."}
    
    if Hash.verify(password, stored_hash):
        return {"success": True}
    return {"success": False, "error": "Invalid credentials"}
```

### 4. Log Security Events

```python
import logging

logger = logging.getLogger(__name__)

def secure_login(username: str, password: str, stored_hash: str) -> dict:
    """Login with security logging."""
    
    if Hash.verify(password, stored_hash):
        logger.info(f"Successful login: {username}")
        return {"success": True}
    else:
        logger.warning(f"Failed login attempt: {username}")
        return {"success": False}
```

### 5. Use HTTPS Only

Always transmit passwords over HTTPS to prevent interception:

```python
# In FastAPI
from fastapi import Request, HTTPException

@app.middleware("http")
async def enforce_https(request: Request, call_next):
    if not request.url.scheme == "https" and not request.url.hostname == "localhost":
        raise HTTPException(status_code=403, detail="HTTPS required")
    return await call_next(request)
```

## Performance Considerations

### Hashing Performance

- **Argon2**: ~100-500ms per hash (configurable)
- **bcrypt**: ~50-200ms per hash
- Intentionally slow to prevent brute force attacks
- Don't hash passwords in loops—hash once and store

### Optimization Tips

```python
from dtpyfw.encrypt.hashing import Hash

# ❌ BAD: Hashing in a loop
for user in users:
    # This is slow if verifying against multiple hashes
    if Hash.verify(password, user.hash):
        break

# ✅ GOOD: Hash once, store, retrieve by username
hashed = Hash.crypt(password)
store_user(username, hashed)

# Later, retrieve specific user's hash
user_hash = get_user_hash(username)
is_valid = Hash.verify(password, user_hash)
```

### Async Considerations

Password hashing is CPU-intensive. In async applications, run in thread pool:

```python
from concurrent.futures import ThreadPoolExecutor
from dtpyfw.encrypt.hashing import Hash

executor = ThreadPoolExecutor(max_workers=4)

async def hash_password_async(password: str) -> str:
    """Hash password in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, Hash.crypt, password)

async def verify_password_async(password: str, hashed: str) -> bool:
    """Verify password in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, Hash.verify, password, hashed)
```

## Common Pitfalls

### 1. Comparing Hashes Directly

```python
# ❌ WRONG: Don't compare hash strings
if hashed_password == stored_hash:
    # This won't work—different salts produce different hashes
    pass

# ✅ CORRECT: Always use verify()
if Hash.verify(plain_password, stored_hash):
    # This works correctly
    pass
```

### 2. Not Checking needs_update()

```python
# ❌ WRONG: Missing migration opportunity
if Hash.verify(password, stored_hash):
    return "Login successful"

# ✅ CORRECT: Check for updates
if Hash.verify(password, stored_hash):
    if Hash.needs_update(stored_hash):
        new_hash = Hash.crypt(password)
        update_database(username, new_hash)
    return "Login successful"
```

### 3. Weak Password Requirements

```python
# ❌ WRONG: Too permissive
if len(password) >= 6:
    hashed = Hash.crypt(password)

# ✅ CORRECT: Strong requirements
if (len(password) >= 8 and 
    any(c.isupper() for c in password) and
    any(c.islower() for c in password) and
    any(c.isdigit() for c in password)):
    hashed = Hash.crypt(password)
```

## Testing

```python
import pytest
from dtpyfw.encrypt.hashing import Hash

def test_password_hashing():
    """Test basic hashing functionality."""
    password = "TestPassword123!"
    hashed = Hash.crypt(password)
    
    # Hash should be different from original
    assert hashed != password
    
    # Should verify correctly
    assert Hash.verify(password, hashed)
    
    # Should not verify with wrong password
    assert not Hash.verify("WrongPassword", hashed)

def test_hash_uniqueness():
    """Test that same password produces different hashes."""
    password = "SamePassword123"
    hash1 = Hash.crypt(password)
    hash2 = Hash.crypt(password)
    
    # Hashes should be different (different salts)
    assert hash1 != hash2
    
    # Both should verify
    assert Hash.verify(password, hash1)
    assert Hash.verify(password, hash2)

def test_needs_update():
    """Test hash update detection."""
    # Argon2 hash (current)
    argon2_hash = Hash.crypt("password")
    assert not Hash.needs_update(argon2_hash)
    
    # bcrypt hash (deprecated) - if you have one
    bcrypt_hash = "$2b$12$fakebcrypthash..."
    # This would return True in production with real bcrypt hash

def test_invalid_inputs():
    """Test handling of invalid inputs."""
    valid_hash = Hash.crypt("password")
    
    # Empty password
    assert not Hash.verify("", valid_hash)
    
    # Invalid hash format
    assert not Hash.verify("password", "invalid_hash")
    assert not Hash.verify("password", "")
```

## Migration Guide

### From bcrypt to Argon2

If you're migrating from a system using bcrypt:

1. **Phase 1**: Install dtpyfw with encrypt extra
2. **Phase 2**: Implement transparent migration on login
3. **Phase 3**: Monitor migration progress
4. **Phase 4**: Handle inactive users

```python
from dtpyfw.encrypt.hashing import Hash

def migrate_on_login(username, password, stored_bcrypt_hash):
    """Transparently migrate from bcrypt to Argon2."""
    
    # Verify password (works with bcrypt)
    if not Hash.verify(password, stored_bcrypt_hash):
        return False
    
    # Check if migration needed
    if Hash.needs_update(stored_bcrypt_hash):
        # Re-hash with Argon2
        new_hash = Hash.crypt(password)
        
        # Update database
        db.update_user_password(username, new_hash)
        
        logger.info(f"Migrated {username} from bcrypt to Argon2")
    
    return True
```

## Related Documentation

- [Encryption Module](./encryption.md) - JWT token encryption utilities
- [Core Module](../core/__init__.md) - Core framework utilities
- [API Module](../api/application.md) - FastAPI integration

## External References

- [Argon2 Official Site](https://github.com/P-H-C/phc-winner-argon2)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Passlib Documentation](https://passlib.readthedocs.io/)
- [Password Hashing Competition](https://password-hashing.net/)
