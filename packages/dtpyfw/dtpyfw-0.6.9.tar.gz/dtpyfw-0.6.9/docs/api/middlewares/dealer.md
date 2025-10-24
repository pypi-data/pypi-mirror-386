# dtpyfw.api.middlewares.dealer

Dealer context middleware for extracting and validating dealer information from request headers.

## Module Overview

The `dealer` module provides functionality for extracting dealer identification information from HTTP request headers. It defines the `DealerData` model for storing dealer context and a FastAPI dependency function `get_dealer_data` for validating dealer headers in incoming requests.

## Key Features

- **Header Extraction**: Automatically extracts dealer ID from request headers
- **Validation**: Ensures required dealer identification is present
- **FastAPI Integration**: Works as a dependency for route handlers
- **Type Safety**: Uses UUID for dealer identification with Pydantic validation

## Classes

### DealerData

```python
class DealerData(BaseModel):
    """Container for dealer-specific context extracted from request headers."""
```

A Pydantic model that stores dealer identification information parsed from incoming HTTP request headers.

**Attributes:**

- **main_dealer_id** (`UUID | None`): The unique identifier of the primary dealer associated with the request. Defaults to `None`

**Example:**

```python
dealer_data = DealerData(main_dealer_id=UUID("123e4567-e89b-12d3-a456-426614174000"))
```

## Functions

### get_dealer_data

```python
def get_dealer_data(
    request: Request,
    main_dealer_id: Annotated[
        UUID | None,
        Header(
            alias="main-dealer-id",
            description="Unique identifier of the primary dealer associated with the request.",
        ),
    ] = None,
) -> DealerData
```

FastAPI dependency function that extracts and validates dealer identification data from request headers.

**Parameters:**

- **request** (`Request`): The incoming FastAPI request object
- **main_dealer_id** (`UUID | None`): UUID of the main dealer extracted from the `main-dealer-id` header. Defaults to `None`

**Returns:**

- `DealerData`: Container with the validated dealer ID

**Raises:**

- `HTTPException` (401): If the `main-dealer-id` header is missing from the request

**Header Requirements:**

The function expects the following HTTP header:

- **main-dealer-id**: UUID string identifying the primary dealer (required)

## Usage Examples

### Basic Usage as Dependency

```python
from fastapi import Depends
from dtpyfw.api.middlewares.dealer import DealerData, get_dealer_data

@app.get("/dealer-info")
def get_dealer_info(dealer_data: DealerData = Depends(get_dealer_data)):
    return {
        "dealer_id": dealer_data.main_dealer_id,
        "message": f"Processing request for dealer {dealer_data.main_dealer_id}"
    }
```

### Using with Permission Checks

```python
from fastapi import Depends
from dtpyfw.api.middlewares.dealer import DealerData, get_dealer_data
from dtpyfw.api.middlewares.user import UserData, get_user_data

@app.get("/dealer-products")
def get_dealer_products(
    dealer_data: DealerData = Depends(get_dealer_data),
    user_data: UserData = Depends(get_user_data),
):
    # Verify user has access to this dealer
    if not user_data.check_accessibility(dealer_data.main_dealer_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"products": [...], "dealer_id": dealer_data.main_dealer_id}
```

### Combining with Permission Restrictions

```python
from fastapi import Depends
from dtpyfw.api.middlewares.dealer import DealerData, get_dealer_data
from dtpyfw.api.middlewares.permission import permission_restriction
from dtpyfw.api.middlewares.user import PermissionType, UserData

@app.put("/dealer-settings")
def update_dealer_settings(
    settings: dict,
    auth_data: tuple[UserData, DealerData] = Depends(
        permission_restriction([PermissionType.dealer])
    ),
):
    user_data, dealer_data = auth_data
    
    # Update settings for the dealer
    return {
        "dealer_id": dealer_data.main_dealer_id,
        "updated_by": user_data.id,
        "success": True
    }
```

### Manual DealerData Creation

```python
from uuid import UUID
from dtpyfw.api.middlewares.dealer import DealerData

# Create dealer data manually
dealer_data = DealerData(
    main_dealer_id=UUID("550e8400-e29b-41d4-a716-446655440000")
)

print(dealer_data.main_dealer_id)  # UUID('550e8400-e29b-41d4-a716-446655440000')
```

### Error Handling

```python
from fastapi import Request
from fastapi.exceptions import HTTPException
from dtpyfw.api.middlewares.dealer import get_dealer_data

# When calling without the required header:
# Request without 'main-dealer-id' header will raise:
# HTTPException(status_code=401, detail="Missing main-dealer-id header")

@app.get("/protected-endpoint")
def protected_endpoint(dealer_data = Depends(get_dealer_data)):
    # This will only execute if the header is present and valid
    return {"dealer_id": dealer_data.main_dealer_id}
```

## Request Header Format

When making API calls that use this middleware, include the dealer ID in the request headers:

```bash
# curl example
curl -X GET "https://api.example.com/dealer-info" \
  -H "main-dealer-id: 550e8400-e29b-41d4-a716-446655440000"
```

```python
# Python requests example
import requests

headers = {
    "main-dealer-id": "550e8400-e29b-41d4-a716-446655440000"
}

response = requests.get(
    "https://api.example.com/dealer-info",
    headers=headers
)
```

```javascript
// JavaScript fetch example
fetch("https://api.example.com/dealer-info", {
  headers: {
    "main-dealer-id": "550e8400-e29b-41d4-a716-446655440000"
  }
})
```

## Integration with Router

```python
from dtpyfw.api import Router, Route, RouteMethod
from dtpyfw.api.middlewares.dealer import DealerData, get_dealer_data
from fastapi import Depends

def get_inventory(dealer_data: DealerData = Depends(get_dealer_data)):
    return {"inventory": [...], "dealer": str(dealer_data.main_dealer_id)}

# Create router with dealer dependency on all routes
dealer_router = Router(
    prefix="/dealer",
    tags=["Dealer Operations"],
    dependencies=[Depends(get_dealer_data)],
    routes=[
        Route(
            path="/inventory",
            method=RouteMethod.GET,
            handler=get_inventory,
        ),
    ],
)
```

## Best Practices

1. **Always Validate Access**: After extracting dealer data, verify the user has permission to access that dealer's resources
2. **Use with User Middleware**: Combine with `get_user_data` for complete authentication and authorization
3. **Handle UUID Parsing**: The middleware automatically handles UUID parsing and validation
4. **Error Messages**: The 401 error is clear about the missing header for easy debugging
5. **Router-Level Dependencies**: Apply dealer validation at the router level for routes that always require dealer context
6. **Logging**: Log dealer ID for audit trails and debugging purposes

## Common Patterns

### Multi-Dealer Operations

```python
from typing import List
from uuid import UUID
from dtpyfw.api.middlewares.dealer import DealerData, get_dealer_data

@app.post("/bulk-operation")
def bulk_operation(
    dealer_ids: List[UUID],
    current_dealer: DealerData = Depends(get_dealer_data),
):
    # Verify current dealer can perform operations on other dealers
    if current_dealer.main_dealer_id not in dealer_ids:
        raise HTTPException(status_code=403, detail="Invalid dealer access")
    
    return {"processed": dealer_ids}
```

### Dealer-Specific Data Filtering

```python
from sqlalchemy import select
from dtpyfw.api.middlewares.dealer import DealerData, get_dealer_data

@app.get("/products")
async def get_products(
    dealer_data: DealerData = Depends(get_dealer_data),
    db: AsyncSession = Depends(get_db),
):
    # Automatically filter by dealer
    query = select(Product).where(
        Product.dealer_id == dealer_data.main_dealer_id
    )
    results = await db.execute(query)
    return {"products": results.scalars().all()}
```

## Security Considerations

1. **Header Spoofing**: Ensure your API gateway or authentication layer validates the dealer ID header before it reaches your application
2. **Authorization**: Dealer ID extraction does not imply authorization; always check user permissions
3. **Audit Logging**: Log dealer ID with all operations for security audits
4. **Rate Limiting**: Consider implementing rate limiting per dealer ID

## Related Modules

- [`dtpyfw.api.middlewares.user`](user.md): User authentication and role management
- [`dtpyfw.api.middlewares.permission`](permission.md): Permission-based access control
- [`dtpyfw.api.routes.route`](../routes/route.md): Route configuration with dependencies
- [`dtpyfw.api.routes.router`](../routes/router.md): Router configuration with shared dependencies
