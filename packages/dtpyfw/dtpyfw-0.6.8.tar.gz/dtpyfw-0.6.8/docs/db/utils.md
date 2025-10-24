# Bulk Operations and Upsert Utilities (`dtpyfw.db.utils`)

## Overview

The `utils` module provides efficient bulk operation utilities for PostgreSQL databases, including upsert (INSERT ... ON CONFLICT DO UPDATE) functionality with both synchronous and asynchronous support. These utilities are optimized for high-performance batch processing of large datasets.

## Module Location

```python
from dtpyfw.db.utils import upsert_data, upsert_data_async
```

## Functions

### `upsert_data`

```python
upsert_data(
    list_of_data: List[Dict[str, Any]],
    model: Type[DeclarativeBase],
    db: Session,
    only_update: bool = False,
    only_insert: bool = False,
) -> bool
```

Insert or update records in bulk using PostgreSQL upsert semantics.

Performs bulk insert/update operations with support for PostgreSQL's ON CONFLICT DO UPDATE functionality. Can be configured for insert-only or update-only operations.

**Parameters:**

- `list_of_data` (List[Dict[str, Any]]): List of dictionaries containing the data to upsert. Each dictionary should have keys matching the model's column names
- `model` (Type[DeclarativeBase]): The SQLAlchemy model class representing the target table
- `db` (Session): SQLAlchemy Session for database operations
- `only_update` (bool, optional): If `True`, only perform updates on existing records. Default: `False`
- `only_insert` (bool, optional): If `True`, only insert new records without updates. Default: `False`

**Returns:**

- `bool`: `True` if the operation succeeded, `False` if there was no data to process

**Raises:**

- `SQLAlchemyError`: If database operation fails
- `IntegrityError`: If constraint violations occur

**Example:**

```python
from dtpyfw.db.utils import upsert_data
from myapp.models import User

# Data to upsert
users_data = [
    {
        "id": "uuid-1",
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    },
    {
        "id": "uuid-2",
        "name": "Jane Smith",
        "email": "jane@example.com",
        "age": 25
    }
]

with db.get_db_cm_write() as session:
    success = upsert_data(users_data, User, session)
    if success:
        print("Users upserted successfully")
```

### `upsert_data_async`

```python
async def upsert_data_async(
    list_of_data: List[Dict[str, Any]],
    model: Type[DeclarativeBase],
    db: AsyncSession,
    only_update: bool = False,
    only_insert: bool = False,
) -> bool
```

Asynchronously insert or update records in bulk using PostgreSQL upsert.

Performs async bulk insert/update operations with support for PostgreSQL's ON CONFLICT DO UPDATE functionality. Can be configured for insert-only or update-only operations.

**Parameters:**

- `list_of_data` (List[Dict[str, Any]]): List of dictionaries containing the data to upsert
- `model` (Type[DeclarativeBase]): The SQLAlchemy model class representing the target table
- `db` (AsyncSession): AsyncSession for asynchronous database operations
- `only_update` (bool, optional): If `True`, only perform updates on existing records. Default: `False`
- `only_insert` (bool, optional): If `True`, only insert new records without updates. Default: `False`

**Returns:**

- `bool`: `True` if the operation succeeded, `False` if there was no data to process

**Raises:**

- `SQLAlchemyError`: If database operation fails
- `IntegrityError`: If constraint violations occur

**Example:**

```python
from dtpyfw.db.utils import upsert_data_async

async def bulk_upsert_users():
    users_data = [
        {"id": "uuid-1", "name": "John", "email": "john@example.com"},
        {"id": "uuid-2", "name": "Jane", "email": "jane@example.com"}
    ]
    
    async with db.async_get_db_cm_write() as session:
        success = await upsert_data_async(users_data, User, session)
        return success
```

## Upsert Behavior

### Standard Upsert (default)

When both `only_update` and `only_insert` are `False`, the function performs a true upsert:

- **If record exists** (based on primary key): Updates the record with new values
- **If record doesn't exist**: Inserts a new record

```python
data = [
    {"id": "existing-id", "name": "Updated Name"},  # Will UPDATE
    {"id": "new-id", "name": "New User"}            # Will INSERT
]

upsert_data(data, User, session)
```

### Insert-Only Mode

When `only_insert=True`, only new records are inserted. Existing records are ignored:

```python
data = [
    {"id": "existing-id", "name": "Ignored"},  # Skipped (already exists)
    {"id": "new-id", "name": "New User"}       # Inserted
]

upsert_data(data, User, session, only_insert=True)
```

**Use Case:** Importing new records without modifying existing ones

### Update-Only Mode

When `only_update=True`, only existing records are updated. New records are ignored:

```python
data = [
    {"id": "existing-id", "name": "Updated"},  # Updated
    {"id": "new-id", "name": "Ignored"}        # Skipped (doesn't exist)
]

upsert_data(data, User, session, only_update=True)
```

**Use Case:** Bulk updating existing records without creating new ones

## Usage Examples

### Basic Upsert

```python
from dtpyfw.db.utils import upsert_data

# Prepare data
products_data = [
    {"id": 1, "name": "Product A", "price": 99.99, "stock": 100},
    {"id": 2, "name": "Product B", "price": 149.99, "stock": 50},
    {"id": 3, "name": "Product C", "price": 199.99, "stock": 25},
]

# Perform upsert
with db.get_db_cm_write() as session:
    success = upsert_data(products_data, Product, session)
    print(f"Upsert {'successful' if success else 'failed'}")
```

### Importing from CSV

```python
import csv
from dtpyfw.db.utils import upsert_data

def import_users_from_csv(filename: str):
    """Import users from CSV file using bulk upsert."""
    users_data = []
    
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            users_data.append({
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "age": int(row["age"])
            })
    
    with db.get_db_cm_write() as session:
        success = upsert_data(users_data, User, session)
        return len(users_data) if success else 0

# Usage
imported_count = import_users_from_csv('users.csv')
print(f"Imported {imported_count} users")
```

### Syncing from External API

```python
import requests
from dtpyfw.db.utils import upsert_data

def sync_products_from_api():
    """Sync products from external API to database."""
    # Fetch from API
    response = requests.get('https://api.example.com/products')
    products_from_api = response.json()
    
    # Transform to match our model
    products_data = [
        {
            "id": p["product_id"],
            "name": p["product_name"],
            "price": p["price"],
            "description": p["desc"],
            "last_synced": datetime.utcnow()
        }
        for p in products_from_api
    ]
    
    # Upsert to database
    with db.get_db_cm_write() as session:
        success = upsert_data(products_data, Product, session)
        return len(products_data) if success else 0
```

### Async Batch Processing

```python
from dtpyfw.db.utils import upsert_data_async
import asyncio

async def process_user_batch(batch: List[Dict]):
    """Process a batch of users asynchronously."""
    async with db.async_get_db_cm_write() as session:
        return await upsert_data_async(batch, User, session)

async def import_users_in_batches(all_users: List[Dict], batch_size: int = 1000):
    """Import users in batches asynchronously."""
    total = len(all_users)
    processed = 0
    
    for i in range(0, total, batch_size):
        batch = all_users[i:i + batch_size]
        success = await process_user_batch(batch)
        if success:
            processed += len(batch)
            print(f"Processed {processed}/{total} users")
    
    return processed

# Usage
users_data = [...] # Large list of user dictionaries
total_processed = await import_users_in_batches(users_data)
```

### Conditional Updates

```python
from dtpyfw.db.utils import upsert_data
from datetime import datetime

def update_product_prices(price_updates: List[Dict]):
    """Update product prices without inserting new products."""
    # Only update existing products
    with db.get_db_cm_write() as session:
        success = upsert_data(
            price_updates,
            Product,
            session,
            only_update=True  # Don't create new products
        )
        return success

# Usage
price_updates = [
    {"id": 1, "price": 109.99, "updated_at": datetime.utcnow()},
    {"id": 2, "price": 159.99, "updated_at": datetime.utcnow()},
]

update_product_prices(price_updates)
```

### Initial Data Load

```python
from dtpyfw.db.utils import upsert_data

def load_initial_categories():
    """Load initial category data without updating existing ones."""
    categories = [
        {"id": 1, "name": "Electronics", "slug": "electronics"},
        {"id": 2, "name": "Books", "slug": "books"},
        {"id": 3, "name": "Clothing", "slug": "clothing"},
    ]
    
    with db.get_db_cm_write() as session:
        success = upsert_data(
            categories,
            Category,
            session,
            only_insert=True  # Only add if they don't exist
        )
        return success
```

### Error Handling

```python
from dtpyfw.db.utils import upsert_data
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

def safe_upsert_users(users_data: List[Dict]):
    """Safely upsert users with comprehensive error handling."""
    try:
        with db.get_db_cm_write() as session:
            success = upsert_data(users_data, User, session)
            
            if not success:
                return {
                    "status": "skipped",
                    "message": "No data to process"
                }
            
            return {
                "status": "success",
                "count": len(users_data)
            }
            
    except IntegrityError as e:
        return {
            "status": "error",
            "type": "integrity",
            "message": "Constraint violation",
            "details": str(e)
        }
    except SQLAlchemyError as e:
        return {
            "status": "error",
            "type": "database",
            "message": "Database operation failed",
            "details": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "type": "unknown",
            "message": str(e)
        }
```

## Performance Characteristics

### Advantages

1. **Bulk Operations**: Processes multiple records in a single database round-trip
2. **Atomic**: All operations succeed or fail together (within transaction)
3. **PostgreSQL-Optimized**: Uses native `ON CONFLICT` for maximum efficiency
4. **Reduced Network Overhead**: Minimizes database communication
5. **Connection Pool Friendly**: Uses existing sessions efficiently

### Performance Comparison

```python
# ❌ SLOW: Individual inserts (N database calls)
for user_data in users:
    User.create(session, user_data)

# ✅ FAST: Bulk upsert (1 database call)
upsert_data(users, User, session)
```

### Benchmarks (Approximate)

- 1,000 records: ~10x faster than individual inserts
- 10,000 records: ~50x faster
- 100,000 records: ~100x faster

## Data Preparation Guidelines

### Required Fields

```python
# ✅ Good: Include primary key
data = [
    {"id": 1, "name": "Product A"},
    {"id": 2, "name": "Product B"}
]

# ❌ Bad: Missing primary key (will insert new records each time)
data = [
    {"name": "Product A"},
    {"name": "Product B"}
]
```

### Column Names

```python
# ✅ Good: Match model column names exactly
data = [
    {"id": 1, "product_name": "Product A"}  # If column is 'product_name'
]

# ❌ Bad: Mismatched names
data = [
    {"id": 1, "name": "Product A"}  # If column is 'product_name'
]
```

### Type Safety

```python
# ✅ Good: Correct types
data = [
    {
        "id": 1,
        "name": "Product",
        "price": 99.99,
        "active": True,
        "created_at": datetime.utcnow()
    }
]

# ⚠️ Careful: Type mismatches may cause errors
data = [
    {
        "id": "1",  # Should be int
        "price": "99.99",  # Should be float
        "active": "true"  # Should be bool
    }
]
```

## Batch Processing Strategies

### Fixed Batch Size

```python
def upsert_in_batches(data: List[Dict], batch_size: int = 1000):
    """Upsert data in fixed-size batches."""
    total = len(data)
    success_count = 0
    
    for i in range(0, total, batch_size):
        batch = data[i:i + batch_size]
        
        with db.get_db_cm_write() as session:
            if upsert_data(batch, User, session):
                success_count += len(batch)
        
        print(f"Processed {min(i + batch_size, total)}/{total}")
    
    return success_count
```

### Adaptive Batch Size

```python
def upsert_adaptive(data: List[Dict], initial_batch_size: int = 1000):
    """Upsert with adaptive batch sizing based on performance."""
    import time
    
    batch_size = initial_batch_size
    total = len(data)
    processed = 0
    
    while processed < total:
        batch = data[processed:processed + batch_size]
        start_time = time.time()
        
        with db.get_db_cm_write() as session:
            success = upsert_data(batch, User, session)
        
        elapsed = time.time() - start_time
        
        if success:
            processed += len(batch)
            
            # Adjust batch size based on performance
            if elapsed < 1.0 and batch_size < 10000:
                batch_size *= 2  # Increase if fast
            elif elapsed > 5.0 and batch_size > 100:
                batch_size //= 2  # Decrease if slow
        
        print(f"Batch size: {batch_size}, Processed: {processed}/{total}")
    
    return processed
```

## Best Practices

1. **Use Batching**: Process large datasets in batches (1000-10000 records)
   ```python
   for i in range(0, len(data), 1000):
       batch = data[i:i+1000]
       upsert_data(batch, Model, session)
   ```

2. **Always Include Primary Keys**: For proper conflict detection
   ```python
   data = [{"id": row_id, "name": name} for row_id, name in rows]
   ```

3. **Handle Errors**: Wrap upsert operations in try-except blocks
   ```python
   try:
       upsert_data(data, Model, session)
   except IntegrityError:
       # Handle constraint violations
   ```

4. **Monitor Performance**: Log batch processing progress
   ```python
   print(f"Processing batch {i}/{total_batches}")
   ```

5. **Use Async for I/O-Bound**: When fetching from APIs or external sources
   ```python
   data = await fetch_from_api()
   await upsert_data_async(data, Model, session)
   ```

6. **Validate Data**: Check data quality before upserting
   ```python
   validated_data = [d for d in data if is_valid(d)]
   upsert_data(validated_data, Model, session)
   ```

## Limitations

1. **PostgreSQL Only**: Uses PostgreSQL-specific `ON CONFLICT` syntax
2. **Primary Key Required**: Records must have primary keys for conflict detection
3. **No Relationship Handling**: Only updates direct columns, not relationships
4. **All or Nothing**: If one record fails, entire batch fails (transactional)

## Comparison with Alternative Approaches

### vs. Individual Inserts/Updates

```python
# ❌ Slow: N database calls
for data in list_of_data:
    existing = session.query(Model).get(data["id"])
    if existing:
        existing.update(session, data)
    else:
        Model.create(session, data)

# ✅ Fast: 1 database call
upsert_data(list_of_data, Model, session)
```

### vs. SQLAlchemy bulk_insert_mappings

```python
# ⚠️ Insert-only, no conflict handling
session.bulk_insert_mappings(Model, list_of_data)

# ✅ Handles conflicts, updates existing
upsert_data(list_of_data, Model, session)
```

## Related Documentation

- [model.md](./model.md) - Model create/update methods
- [database.md](./database.md) - Session management
- [PostgreSQL ON CONFLICT](https://www.postgresql.org/docs/current/sql-insert.html)

## Notes

- The function commits automatically on success
- Rollback happens automatically on failure
- Empty lists return `False` immediately without database access
- Primary keys in the data must match existing records for updates
- Only columns present in the first dictionary are used for updates
