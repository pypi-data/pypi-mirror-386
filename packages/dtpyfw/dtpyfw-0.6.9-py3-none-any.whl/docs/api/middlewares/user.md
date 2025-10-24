# dtpyfw.api.middlewares.user

User authentication and role management middleware for FastAPI applications.

## Module Overview

The `user` module provides comprehensive user authentication and authorization infrastructure for FastAPI applications. It defines user roles, permission types, and functions for extracting and validating user identity and access rights from request headers.

## Key Features

- **User Role Management**: Hierarchical role system (manager, administrator, super_administrator)
- **Permission System**: Granular dealer-specific permissions
- **Header-Based Authentication**: Extracts user data from HTTP headers
- **Type Safety**: Uses UUID and Enums for type-safe authentication
- **Dealer-Specific Access**: Per-dealer permission mapping
- **FastAPI Integration**: Works as a dependency for route handlers

## Enumerations

### UserRole

```python
class UserRole(str, Enum):
    """Enumeration of user roles with different access levels."""
```

**Values:**

- **manager**: `"manager"` - Limited access, requires explicit per-dealer permissions
- **administrator**: `"administrator"` - Full access within organization, bypasses permission checks
- **super_administrator**: `"super_administrator"` - Highest level, universal access across all dealers

**Hierarchy:**

```
super_administrator (highest privileges)
         ↓
    administrator (organization-wide access)
         ↓
      manager (limited, dealer-specific access)
```

### PermissionType

```python
class PermissionType(str, Enum):
    """Enumeration of permissions that can be granted to users."""
```

**Values:**

- **dealer**: `"dealer"` - Access to dealer management operations
- **bulk_rule**: `"bulk_rule"` - Access to bulk rule management
- **inventory**: `"inventory"` - Access to inventory management operations
- **lead**: `"lead"` - Access to lead management features
- **page**: `"page"` - Access to page/content management

## Classes

### UserData

```python
class UserData(BaseModel):
    """Represents the authenticated user's identity, role, and access permissions."""
```

**Attributes:**

- **id** (`UUID | None`): Unique identifier of the user. Defaults to `None`
- **role** (`UserRole | None`): Role assigned to the user, determining their level of access. Defaults to `None`
- **permissions** (`dict[UUID, list[PermissionType]] | None`): Mapping of dealer IDs to the list of permissions the user has for each dealer. Defaults to `None`

#### Methods

##### check_accessibility

```python
def check_accessibility(self, dealer_id: UUID | str) -> bool
```

Checks whether the user has access rights for a given dealer.

**Parameters:**

- **dealer_id** (`UUID | str`): Dealer identifier as UUID or string

**Returns:**

- `bool`: `True` if the user has access, `False` otherwise

**Logic:**

1. Administrators and super_administrators always return `True`
2. For other roles, checks if dealer_id exists in the user's permissions mapping
3. Normalizes string dealer_id to UUID before checking

**Example:**

```python
user_data = UserData(
    id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    role=UserRole.manager,
    permissions={
        UUID("123e4567-e89b-12d3-a456-426614174000"): [PermissionType.dealer]
    }
)

# Check access
has_access = user_data.check_accessibility("123e4567-e89b-12d3-a456-426614174000")
print(has_access)  # True

has_access = user_data.check_accessibility("999e4567-e89b-12d3-a456-426614174000")
print(has_access)  # False
```

## Functions

### get_user_data

```python
def get_user_data(
    user_id: Annotated[UUID | None, Header(alias="user-id", ...)] = None,
    user_role: Annotated[UserRole | None, Header(alias="user-role", ...)] = None,
    user_permissions: Annotated[str | None, Header(alias="user-permissions", ...)] = None,
) -> UserData
```

FastAPI dependency function that extracts and validates user authentication data from request headers.

**Parameters:**

- **user_id** (`UUID | None`): UUID extracted from the `user-id` header
- **user_role** (`UserRole | None`): User role extracted from the `user-role` header
- **user_permissions** (`str | None`): JSON string of dealer permissions from `user-permissions` header

**Returns:**

- `UserData`: Validated user authentication data

**Raises:**

- `HTTPException` (401): If `user-id` header is missing
- `HTTPException` (400): If `user-permissions` JSON is malformed or invalid

**Header Requirements:**

- **user-id** (required): UUID string identifying the user
- **user-role** (optional): One of: `manager`, `administrator`, `super_administrator`
- **user-permissions** (optional): JSON object mapping dealer UUIDs to permission arrays

## Usage Examples

### Basic Usage as Dependency

```python
from fastapi import Depends
from dtpyfw.api.middlewares.user import UserData, get_user_data

@app.get("/profile")
def get_profile(user_data: UserData = Depends(get_user_data)):
    return {
        "user_id": user_data.id,
        "role": user_data.role,
        "permissions_count": len(user_data.permissions or {})
    }
```

### Role-Based Access

```python
from dtpyfw.api.middlewares.user import UserData, UserRole, get_user_data
from fastapi import HTTPException

@app.get("/admin/settings")
def get_admin_settings(user_data: UserData = Depends(get_user_data)):
    if user_data.role not in [UserRole.administrator, UserRole.super_administrator]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {"settings": [...]}
```

### Checking Dealer Access

```python
from uuid import UUID
from dtpyfw.api.middlewares.user import UserData, get_user_data

@app.get("/dealers/{dealer_id}/info")
def get_dealer_info(
    dealer_id: UUID,
    user_data: UserData = Depends(get_user_data)
):
    if not user_data.check_accessibility(dealer_id):
        raise HTTPException(status_code=403, detail="No access to this dealer")
    
    return {"dealer_id": dealer_id, "info": [...]}
```

### Using with Permission Middleware

```python
from dtpyfw.api.middlewares.permission import permission_restriction
from dtpyfw.api.middlewares.user import PermissionType, UserData
from dtpyfw.api.middlewares.dealer import DealerData

@app.put("/dealers/{dealer_id}/inventory")
def update_inventory(
    dealer_id: UUID,
    inventory: dict,
    auth_data: tuple[UserData, DealerData] = Depends(
        permission_restriction([PermissionType.inventory])
    )
):
    user_data, dealer_data = auth_data
    
    return {
        "updated_by": user_data.id,
        "dealer_id": dealer_data.main_dealer_id,
        "inventory": inventory
    }
```

### Manual UserData Creation

```python
from uuid import UUID
from dtpyfw.api.middlewares.user import UserData, UserRole, PermissionType

# Create user data manually
user_data = UserData(
    id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    role=UserRole.manager,
    permissions={
        UUID("123e4567-e89b-12d3-a456-426614174000"): [
            PermissionType.dealer,
            PermissionType.inventory
        ],
        UUID("234e5678-e89b-12d3-a456-426614174000"): [
            PermissionType.lead
        ]
    }
)
```

## Request Header Format

### Required Headers

```http
user-id: 550e8400-e29b-41d4-a716-446655440000
```

### Optional Headers

```http
user-role: manager
user-permissions: {"123e4567-e89b-12d3-a456-426614174000": ["dealer", "inventory"]}
```

### Complete Example

```bash
curl -X GET "https://api.example.com/profile" \
  -H "user-id: 550e8400-e29b-41d4-a716-446655440000" \
  -H "user-role: manager" \
  -H "user-permissions: {\"123e4567-e89b-12d3-a456-426614174000\": [\"dealer\", \"inventory\"]}"
```

## Permission Mapping Format

The `user-permissions` header contains a JSON object:

```json
{
  "dealer_uuid_1": ["permission1", "permission2"],
  "dealer_uuid_2": ["permission1"],
  "dealer_uuid_3": ["permission1", "permission2", "permission3"]
}
```

**Example:**

```json
{
  "123e4567-e89b-12d3-a456-426614174000": ["dealer", "inventory", "lead"],
  "234e5678-e89b-12d3-a456-426614174000": ["inventory"],
  "345e6789-e89b-12d3-a456-426614174000": ["lead", "page"]
}
```

## Error Handling

### Missing user-id Header

```python
# Request without user-id header
# Raises: HTTPException(status_code=401, detail="Missing user-id header")
```

**Response:**

```json
{
  "detail": "Missing user-id header"
}
```

**HTTP Status:** 401 Unauthorized

### Invalid Permissions JSON

```python
# Malformed JSON in user-permissions header
# Raises: HTTPException(status_code=400, detail="Invalid user-permissions header JSON")
```

**Response:**

```json
{
  "detail": "Invalid user-permissions header JSON"
}
```

**HTTP Status:** 400 Bad Request

## Integration with Router

```python
from dtpyfw.api import Router, Route, RouteMethod
from dtpyfw.api.middlewares.user import UserData, get_user_data
from fastapi import Depends

def get_user_profile(user_data: UserData = Depends(get_user_data)):
    return {"user_id": user_data.id, "role": user_data.role}

# Apply user authentication to all routes
user_router = Router(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(get_user_data)],
    routes=[
        Route(
            path="/profile",
            method=RouteMethod.GET,
            handler=get_user_profile,
        ),
    ],
)
```

## Advanced Usage Patterns

### Role-Based Content Filtering

```python
from dtpyfw.api.middlewares.user import UserData, UserRole, get_user_data

@app.get("/content")
def get_content(user_data: UserData = Depends(get_user_data)):
    if user_data.role == UserRole.super_administrator:
        return {"content": get_all_content()}
    elif user_data.role == UserRole.administrator:
        return {"content": get_organization_content()}
    else:
        # Managers see only their dealer content
        dealer_ids = list(user_data.permissions.keys() if user_data.permissions else [])
        return {"content": get_dealer_content(dealer_ids)}
```

### Multi-Dealer Operations

```python
from dtpyfw.api.middlewares.user import UserData, get_user_data

@app.get("/multi-dealer-report")
def multi_dealer_report(user_data: UserData = Depends(get_user_data)):
    if user_data.role in [UserRole.administrator, UserRole.super_administrator]:
        # Access all dealers
        return {"report": generate_full_report()}
    else:
        # Only dealers with permissions
        accessible_dealers = list(user_data.permissions.keys() if user_data.permissions else [])
        return {"report": generate_report(accessible_dealers)}
```

### Permission-Based Feature Flags

```python
from dtpyfw.api.middlewares.user import UserData, PermissionType, get_user_data

@app.get("/features")
def get_available_features(
    dealer_id: UUID,
    user_data: UserData = Depends(get_user_data)
):
    features = []
    
    if not user_data.check_accessibility(dealer_id):
        return {"features": []}
    
    # Check specific permissions
    dealer_perms = user_data.permissions.get(dealer_id, []) if user_data.permissions else []
    
    if PermissionType.inventory in dealer_perms:
        features.append("inventory_management")
    
    if PermissionType.lead in dealer_perms:
        features.append("lead_tracking")
    
    if PermissionType.page in dealer_perms:
        features.append("content_editing")
    
    return {"features": features}
```

## Testing

```python
from uuid import UUID
from dtpyfw.api.middlewares.user import UserData, UserRole, PermissionType

def test_administrator_accessibility():
    """Administrators can access any dealer."""
    user_data = UserData(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        role=UserRole.administrator,
        permissions=None
    )
    
    # Can access any dealer
    assert user_data.check_accessibility(UUID("123e4567-e89b-12d3-a456-426614174000"))
    assert user_data.check_accessibility("999e4567-e89b-12d3-a456-426614174000")

def test_manager_accessibility():
    """Managers need explicit permissions."""
    dealer_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    user_data = UserData(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        role=UserRole.manager,
        permissions={dealer_id: [PermissionType.dealer]}
    )
    
    # Has access to permitted dealer
    assert user_data.check_accessibility(dealer_id)
    
    # No access to other dealers
    assert not user_data.check_accessibility("999e4567-e89b-12d3-a456-426614174000")
```

## Best Practices

1. **Always Validate user-id**: Ensure the user-id header is present and valid
2. **Use Role Hierarchy**: Leverage role-based access for broader permissions
3. **Granular Permissions**: Use permission types for fine-grained access control
4. **Secure Headers**: Ensure headers are set by your authentication layer, not clients
5. **Log Access Attempts**: Log all access checks for audit trails
6. **Cache Carefully**: If caching user data, implement proper cache invalidation
7. **Test All Roles**: Write tests for each role and permission combination

## Security Considerations

1. **Header Validation**: User headers must be set by a trusted authentication service
2. **Don't Trust Client**: Never allow clients to set authentication headers directly
3. **JWT Integration**: Consider using JWT tokens that are validated and converted to headers
4. **Session Management**: Implement proper session management and expiration
5. **Audit Logging**: Log all authentication and authorization events
6. **Rate Limiting**: Implement rate limiting to prevent brute force attacks
7. **Permission Reviews**: Regularly review and audit user permissions

## Related Modules

- [`dtpyfw.api.middlewares.dealer`](dealer.md): Dealer context extraction
- [`dtpyfw.api.middlewares.permission`](permission.md): Permission checking utilities
- [`dtpyfw.api.routes.route`](../routes/route.md): Route configuration with dependencies
- [`dtpyfw.api.routes.router`](../routes/router.md): Router configuration
- [`dtpyfw.core.exception`](../../core/exception.md): Exception handling utilities
