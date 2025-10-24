# dtpyfw.api.middlewares.permission

Permission and role-based access control middleware helpers for FastAPI applications.

## Module Overview

The `permission` module provides utilities for implementing fine-grained access control in FastAPI applications. It includes functions for checking user permissions on a per-dealer basis and creating FastAPI dependencies that enforce permission and role requirements.

## Key Features

- **Permission Checking**: Validate user permissions for specific dealers
- **Role-Based Access Control**: Restrict endpoints based on user roles
- **Dealer-Specific Permissions**: Support for multi-tenant permission models
- **FastAPI Dependencies**: Easy integration with route handlers
- **Flexible Authorization**: Supports hierarchical permission models

## Functions

### check_permissions

```python
def check_permissions(
    user_data: UserData,
    dealer_data: DealerData,
    required_permissions: list[PermissionType],
) -> bool
```

Verifies if a user has the required permissions for a specific dealer.

**Parameters:**

- **user_data** (`UserData`): User authentication and permission data
- **dealer_data** (`DealerData`): Dealer context information from the request
- **required_permissions** (`list[PermissionType]`): List of permissions required for the action

**Returns:**

- `bool`: `True` if user has required permissions, `False` otherwise

**Permission Logic:**

1. **Super Administrators & Administrators**: Always have access (bypass permission checks)
2. **Managers**: Must have explicit permissions for the specific dealer
3. Permission check fails if:
   - Dealer ID is missing
   - User has no permissions mapping
   - User lacks any required permission for the dealer

### permission_restriction

```python
def permission_restriction(
    required_permissions: list[PermissionType],
) -> Callable[[UserData, DealerData], tuple[UserData, DealerData]]
```

Creates a FastAPI dependency that enforces permission requirements for dealer-specific operations.

**Parameters:**

- **required_permissions** (`list[PermissionType]`): List of permissions needed to access the endpoint

**Returns:**

- `Callable`: FastAPI dependency function that validates permissions

**Raises:**

- `RequestException` (403): If user lacks required permissions with message: "You don't have permission to access this dealer or this section."

### role_restriction

```python
def role_restriction(
    required_roles: list[UserRole],
) -> Callable[[UserData], UserData]
```

Creates a FastAPI dependency that enforces role requirements.

**Parameters:**

- **required_roles** (`list[UserRole]`): List of roles allowed to access the endpoint

**Returns:**

- `Callable`: FastAPI dependency function that validates user role

**Raises:**

- `RequestException` (403): If user's role is not in `required_roles` with message: "You don't have permission to access this section."

## Usage Examples

### Basic Permission Restriction

```python
from fastapi import Depends
from dtpyfw.api.middlewares.permission import permission_restriction
from dtpyfw.api.middlewares.user import PermissionType, UserData
from dtpyfw.api.middlewares.dealer import DealerData

@app.put("/dealers/{dealer_id}/settings")
def update_dealer_settings(
    dealer_id: str,
    settings: dict,
    auth_data: tuple[UserData, DealerData] = Depends(
        permission_restriction([PermissionType.dealer])
    )
):
    user_data, dealer_data = auth_data
    
    # User has 'dealer' permission for this dealer
    return {
        "dealer_id": dealer_data.main_dealer_id,
        "updated_by": user_data.id,
        "settings": settings
    }
```

### Multiple Permission Requirements

```python
from dtpyfw.api.middlewares.permission import permission_restriction
from dtpyfw.api.middlewares.user import PermissionType

@app.post("/dealers/{dealer_id}/inventory")
def create_inventory_item(
    dealer_id: str,
    item: InventoryItem,
    auth_data: tuple[UserData, DealerData] = Depends(
        permission_restriction([
            PermissionType.dealer,
            PermissionType.inventory
        ])
    )
):
    user_data, dealer_data = auth_data
    
    # User must have BOTH 'dealer' AND 'inventory' permissions
    return {"created": True, "item": item}
```

### Role Restriction

```python
from dtpyfw.api.middlewares.permission import role_restriction
from dtpyfw.api.middlewares.user import UserRole, UserData

@app.get("/admin/users")
def list_all_users(
    user_data: UserData = Depends(
        role_restriction([UserRole.administrator, UserRole.super_administrator])
    )
):
    # Only administrators and super_administrators can access
    return {"users": get_all_users()}
```

### Combining Permission and Role Restrictions

```python
from fastapi import Depends
from dtpyfw.api.middlewares.permission import permission_restriction, role_restriction
from dtpyfw.api.middlewares.user import PermissionType, UserRole, UserData

# First check role, then check permissions
@app.delete("/dealers/{dealer_id}")
def delete_dealer(
    dealer_id: str,
    user_data: UserData = Depends(
        role_restriction([UserRole.super_administrator])
    ),
    auth_data: tuple[UserData, DealerData] = Depends(
        permission_restriction([PermissionType.dealer])
    )
):
    # Only super_administrators with dealer permission can delete
    return {"deleted": True}
```

### Manual Permission Checking

```python
from dtpyfw.api.middlewares.permission import check_permissions
from dtpyfw.api.middlewares.user import PermissionType, UserData, get_user_data
from dtpyfw.api.middlewares.dealer import DealerData, get_dealer_data

@app.post("/custom-operation")
def custom_operation(
    user_data: UserData = Depends(get_user_data),
    dealer_data: DealerData = Depends(get_dealer_data),
):
    # Manual permission check
    has_access = check_permissions(
        user_data=user_data,
        dealer_data=dealer_data,
        required_permissions=[PermissionType.dealer, PermissionType.inventory]
    )
    
    if not has_access:
        return {"status": "limited", "message": "Read-only access"}
    
    # Full access granted
    return {"status": "full_access", "can_modify": True}
```

### Router-Level Permission Enforcement

```python
from dtpyfw.api import Router, Route, RouteMethod
from dtpyfw.api.middlewares.permission import permission_restriction
from dtpyfw.api.middlewares.user import PermissionType

# Apply permission restriction to all routes in the router
inventory_router = Router(
    prefix="/inventory",
    tags=["Inventory"],
    dependencies=[
        Depends(permission_restriction([PermissionType.inventory]))
    ],
    routes=[
        Route(
            path="/",
            method=RouteMethod.GET,
            handler=list_inventory,
        ),
        Route(
            path="/",
            method=RouteMethod.POST,
            handler=create_inventory,
        ),
    ],
)
```

### Conditional Access Based on Role

```python
from dtpyfw.api.middlewares.user import UserRole, UserData, get_user_data

@app.get("/reports")
def get_reports(user_data: UserData = Depends(get_user_data)):
    # Different behavior based on role
    if user_data.role == UserRole.super_administrator:
        return {"reports": get_all_reports()}
    elif user_data.role == UserRole.administrator:
        return {"reports": get_admin_reports(user_data.id)}
    else:
        return {"reports": get_user_reports(user_data.id)}
```

## Permission Types

The framework defines the following permission types in `dtpyfw.api.middlewares.user`:

```python
class PermissionType(str, Enum):
    dealer = "dealer"           # Access to dealer management
    bulk_rule = "bulk_rule"     # Access to bulk rules
    inventory = "inventory"     # Access to inventory management
    lead = "lead"               # Access to lead management
    page = "page"               # Access to page management
```

## User Roles

The framework defines the following user roles:

```python
class UserRole(str, Enum):
    manager = "manager"                           # Limited access, requires explicit permissions
    administrator = "administrator"                # Full access within organization
    super_administrator = "super_administrator"    # Universal access across all dealers
```

### Role Hierarchy

- **manager**: Restricted role with explicit per-dealer permissions required
- **administrator**: Full access without dealer-specific permission checks
- **super_administrator**: Highest level, bypasses all permission checks

## Access Control Matrix

| Role | Permission Check | Dealer Access |
|------|------------------|---------------|
| **super_administrator** | Bypassed (always granted) | All dealers |
| **administrator** | Bypassed (always granted) | All dealers |
| **manager** | Required | Only dealers with explicit permissions |

## Error Responses

### Permission Denied

```json
{
  "success": false,
  "message": "You don't have permission to access this dealer or this section."
}
```

**HTTP Status:** 403 Forbidden

### Role Restriction Failed

```json
{
  "success": false,
  "message": "You don't have permission to access this section."
}
```

**HTTP Status:** 403 Forbidden

## Request Headers Required

These middleware functions depend on user and dealer headers:

### User Headers

```
user-id: <UUID>
user-role: <manager|administrator|super_administrator>
user-permissions: <JSON_encoded_permissions>
```

### Dealer Header

```
main-dealer-id: <UUID>
```

### Example Request

```bash
curl -X PUT "https://api.example.com/dealers/123/settings" \
  -H "user-id: 550e8400-e29b-41d4-a716-446655440000" \
  -H "user-role: manager" \
  -H "user-permissions: {\"123e4567-e89b-12d3-a456-426614174000\": [\"dealer\", \"inventory\"]}" \
  -H "main-dealer-id: 123e4567-e89b-12d3-a456-426614174000" \
  -d '{"setting": "value"}'
```

## Advanced Usage Patterns

### Dynamic Permission Requirements

```python
from typing import List
from dtpyfw.api.middlewares.user import PermissionType

def get_required_permissions(operation: str) -> List[PermissionType]:
    """Determine required permissions based on operation."""
    permission_map = {
        "view": [],
        "edit": [PermissionType.dealer],
        "delete": [PermissionType.dealer, PermissionType.inventory],
    }
    return permission_map.get(operation, [])

@app.post("/perform-operation")
def perform_operation(
    operation: str,
    user_data: UserData = Depends(get_user_data),
    dealer_data: DealerData = Depends(get_dealer_data),
):
    required_perms = get_required_permissions(operation)
    
    if required_perms and not check_permissions(user_data, dealer_data, required_perms):
        raise RequestException(
            status_code=403,
            controller="perform_operation",
            message="Insufficient permissions for this operation"
        )
    
    return {"operation": operation, "status": "success"}
```

### Permission Caching

```python
from functools import lru_cache
from dtpyfw.api.middlewares.permission import check_permissions

@lru_cache(maxsize=1000)
def cached_permission_check(
    user_id: str,
    dealer_id: str,
    permission_tuple: tuple
) -> bool:
    """Cache permission check results for performance."""
    # Note: In production, implement proper cache invalidation
    pass
```

## Testing Permission Logic

```python
from uuid import UUID
from dtpyfw.api.middlewares.permission import check_permissions
from dtpyfw.api.middlewares.user import UserData, UserRole, PermissionType
from dtpyfw.api.middlewares.dealer import DealerData

def test_super_admin_access():
    """Super admins bypass permission checks."""
    user_data = UserData(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        role=UserRole.super_administrator,
        permissions=None
    )
    dealer_data = DealerData(
        main_dealer_id=UUID("123e4567-e89b-12d3-a456-426614174000")
    )
    
    assert check_permissions(
        user_data, dealer_data, [PermissionType.dealer]
    ) is True

def test_manager_with_permission():
    """Managers need explicit permissions."""
    dealer_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    user_data = UserData(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        role=UserRole.manager,
        permissions={dealer_id: [PermissionType.dealer, PermissionType.inventory]}
    )
    dealer_data = DealerData(main_dealer_id=dealer_id)
    
    # Has permission
    assert check_permissions(
        user_data, dealer_data, [PermissionType.dealer]
    ) is True
    
    # Lacks permission
    assert check_permissions(
        user_data, dealer_data, [PermissionType.lead]
    ) is False
```

## Best Practices

1. **Principle of Least Privilege**: Grant only the minimum permissions necessary
2. **Layer Security**: Combine role and permission checks for sensitive operations
3. **Clear Error Messages**: Help users understand why access was denied
4. **Audit Logging**: Log all permission checks and denials
5. **Consistent Patterns**: Use the same permission checking approach across your API
6. **Test Thoroughly**: Write tests for all permission combinations
7. **Document Requirements**: Clearly document which permissions are needed for each endpoint

## Security Considerations

1. **Validate Headers**: Ensure authentication middleware validates user headers before permission checks
2. **Don't Trust Client**: Permission headers should be set by your authentication layer, not the client
3. **Cache Carefully**: If caching permission checks, implement proper cache invalidation
4. **Monitor Access**: Track and alert on repeated permission denials
5. **Regular Audits**: Periodically review and audit user permissions

## Related Modules

- [`dtpyfw.api.middlewares.user`](user.md): User authentication and role management
- [`dtpyfw.api.middlewares.dealer`](dealer.md): Dealer context extraction
- [`dtpyfw.core.exception`](../../core/exception.md): Exception handling utilities
- [`dtpyfw.api.routes.route`](../routes/route.md): Route configuration
- [`dtpyfw.api.routes.router`](../routes/router.md): Router configuration with shared dependencies
