# Database Health Check (`dtpyfw.db.health`)

## Overview

The `health` module provides utilities for checking database connectivity and operational status. It offers a simple function to verify that both read and write database connections are working properly, which is essential for health check endpoints and monitoring systems.

## Module Location

```python
from dtpyfw.db.health import is_database_connected
```

## Functions

### `is_database_connected(db: DatabaseInstance) -> Tuple[bool, Exception | None]`

Check if both read and write database connections are working.

This function executes a simple `SELECT 1` query on both the read and write database engines to verify connectivity and operational status. It's a lightweight check that confirms the database is reachable and can execute queries.

**Parameters:**

- `db` (DatabaseInstance): The `DatabaseInstance` to check for connectivity

**Returns:**

- `Tuple[bool, Exception | None]`: A tuple containing:
  - `bool`: `True` if both connections are working, `False` otherwise
  - `Exception | None`: The exception if connection failed, `None` if successful

**Example:**

```python
from dtpyfw.db import DatabaseInstance, DatabaseConfig, is_database_connected

# Create database instance
config = DatabaseConfig().set_db_name("mydb").set_db_host("localhost")
db = DatabaseInstance(config)

# Check connectivity
is_connected, error = is_database_connected(db)

if is_connected:
    print("Database is healthy and connected")
else:
    print(f"Database connection failed: {error}")
```

## Detailed Behavior

The function performs the following operations:

1. **Tests Write Connection**: Executes `SELECT 1` on the write engine
2. **Tests Read Connection**: Executes `SELECT 1` on the read engine
3. **Returns Results**: Returns success status and any exception that occurred

### Success Case

```python
is_connected, error = is_database_connected(db)
# is_connected = True
# error = None
```

### Failure Case

```python
# Database is down or unreachable
is_connected, error = is_database_connected(db)
# is_connected = False
# error = <Exception instance with details>
```

## Usage Patterns

### Basic Health Check

```python
from dtpyfw.db import is_database_connected

def check_database():
    is_healthy, error = is_database_connected(db)
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "database": "connected" if is_healthy else "disconnected",
        "error": str(error) if error else None
    }
```

### FastAPI Health Endpoint

```python
from fastapi import FastAPI, HTTPException
from dtpyfw.db import is_database_connected

app = FastAPI()

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring systems."""
    is_connected, error = is_database_connected(db)
    
    if is_connected:
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        # Return 503 Service Unavailable if database is down
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(error),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

### Detailed Health Check

```python
from dtpyfw.db import is_database_connected

@app.get("/health/detailed")
def detailed_health_check():
    """Detailed health check with additional information."""
    is_connected, error = is_database_connected(db)
    
    health_info = {
        "status": "healthy" if is_connected else "unhealthy",
        "database": {
            "connected": is_connected,
            "write_engine": "operational" if is_connected else "failed",
            "read_engine": "operational" if is_connected else "failed",
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if error:
        health_info["database"]["error"] = {
            "type": type(error).__name__,
            "message": str(error)
        }
    
    if not is_connected:
        raise HTTPException(status_code=503, detail=health_info)
    
    return health_info
```

### Startup Check

```python
from fastapi import FastAPI
from dtpyfw.db import is_database_connected
import sys

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Verify database connectivity on startup."""
    is_connected, error = is_database_connected(db)
    
    if not is_connected:
        print(f"FATAL: Database connection failed: {error}")
        print("Shutting down application...")
        sys.exit(1)
    
    print("Database connection verified successfully")
```

### Retry Logic

```python
import time
from dtpyfw.db import is_database_connected

def wait_for_database(db, max_retries=10, delay=2):
    """Wait for database to become available with retry logic."""
    for attempt in range(1, max_retries + 1):
        is_connected, error = is_database_connected(db)
        
        if is_connected:
            print(f"Database connected on attempt {attempt}")
            return True
        
        print(f"Attempt {attempt}/{max_retries}: Database not ready - {error}")
        
        if attempt < max_retries:
            time.sleep(delay)
    
    raise Exception("Failed to connect to database after maximum retries")

# Usage during application initialization
wait_for_database(db)
```

### Background Health Monitoring

```python
import asyncio
from dtpyfw.db import is_database_connected

async def monitor_database_health(db, interval=60):
    """Continuously monitor database health in the background."""
    while True:
        is_connected, error = is_database_connected(db)
        
        if not is_connected:
            # Log error, send alert, etc.
            print(f"WARNING: Database health check failed: {error}")
            # Could send alerts to monitoring systems
        else:
            print("Database health check: OK")
        
        await asyncio.sleep(interval)

# Start monitoring in background
@app.on_event("startup")
async def start_monitoring():
    asyncio.create_task(monitor_database_health(db, interval=60))
```

### Kubernetes Readiness Probe

```python
from fastapi import FastAPI, Response
from dtpyfw.db import is_database_connected

app = FastAPI()

@app.get("/ready")
def readiness_probe():
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if ready, 503 if not ready.
    """
    is_connected, error = is_database_connected(db)
    
    if is_connected:
        return Response(status_code=200, content="Ready")
    else:
        return Response(status_code=503, content="Not Ready")
```

### Liveness Probe

```python
@app.get("/live")
def liveness_probe():
    """
    Kubernetes liveness probe endpoint.
    Application is alive even if database is temporarily down.
    """
    # Could add application-specific health checks
    return {"status": "alive"}

@app.get("/health")
def health_probe():
    """
    Combined health check including database.
    Used by monitoring systems.
    """
    is_connected, error = is_database_connected(db)
    
    status_code = 200 if is_connected else 503
    return Response(
        status_code=status_code,
        content=json.dumps({
            "application": "alive",
            "database": "connected" if is_connected else "disconnected"
        })
    )
```

## Integration with DatabaseInstance

The `is_database_connected` function is a standalone function that complements the `check_database_health()` method on `DatabaseInstance`:

### Using is_database_connected

```python
from dtpyfw.db import is_database_connected

is_healthy, error = is_database_connected(db)
```

### Using DatabaseInstance method

```python
# Alternative: use the instance method
is_healthy = db.check_database_health()
```

The key difference:
- `is_database_connected()`: Returns both status and exception details
- `db.check_database_health()`: Returns only boolean status

## Best Practices

1. **Use in Health Endpoints**: Always include database health checks in monitoring endpoints

2. **Check on Startup**: Verify database connectivity when the application starts

3. **Implement Retries**: Add retry logic with exponential backoff for startup checks

4. **Monitor Regularly**: Set up periodic health checks for continuous monitoring

5. **Return Appropriate Status Codes**: Use HTTP 503 (Service Unavailable) when unhealthy

6. **Log Errors**: Always log health check failures for debugging

7. **Separate Liveness and Readiness**: In Kubernetes, use separate endpoints for different probe types

8. **Don't Block Requests**: Run health checks in background threads/tasks, not on every request

## Common Error Scenarios

### Connection Refused

```python
is_connected, error = is_database_connected(db)
# is_connected = False
# error = ConnectionRefusedError("Connection refused")
```

**Cause**: Database server is not running or not reachable

### Authentication Failed

```python
is_connected, error = is_database_connected(db)
# is_connected = False  
# error = OperationalError("authentication failed")
```

**Cause**: Invalid database credentials

### Timeout

```python
is_connected, error = is_database_connected(db)
# is_connected = False
# error = OperationalError("connection timeout")
```

**Cause**: Database is overloaded or network issues

### Database Does Not Exist

```python
is_connected, error = is_database_connected(db)
# is_connected = False
# error = OperationalError("database 'mydb' does not exist")
```

**Cause**: Database name is incorrect or database hasn't been created

## Performance Considerations

- **Lightweight**: The `SELECT 1` query is extremely fast and lightweight
- **Connection Pooling**: Uses existing connection pool, doesn't create new connections
- **Both Engines**: Tests both read and write connections, ensuring complete health
- **No Side Effects**: Does not modify any data or state

## Error Handling Example

```python
from dtpyfw.db import is_database_connected
from sqlalchemy.exc import OperationalError, ProgrammingError

def comprehensive_health_check(db):
    """Comprehensive health check with error categorization."""
    is_connected, error = is_database_connected(db)
    
    if is_connected:
        return {"status": "healthy", "message": "All database connections operational"}
    
    # Categorize errors
    if isinstance(error, OperationalError):
        if "authentication" in str(error).lower():
            return {
                "status": "unhealthy",
                "category": "authentication",
                "message": "Database authentication failed",
                "action": "Check credentials"
            }
        elif "refused" in str(error).lower():
            return {
                "status": "unhealthy",
                "category": "connection",
                "message": "Database connection refused",
                "action": "Check if database server is running"
            }
        else:
            return {
                "status": "unhealthy",
                "category": "operational",
                "message": str(error),
                "action": "Check database logs"
            }
    elif isinstance(error, ProgrammingError):
        return {
            "status": "unhealthy",
            "category": "configuration",
            "message": "Database configuration error",
            "action": "Check database name and permissions"
        }
    else:
        return {
            "status": "unhealthy",
            "category": "unknown",
            "message": str(error),
            "action": "Check logs for details"
        }
```

## Related Documentation

- [database.md](./database.md) - DatabaseInstance and session management
- [config.md](./config.md) - Database configuration

## Notes

- The health check uses the connection pool and doesn't create new connections
- Both read and write engines are tested to ensure complete health verification
- The function is synchronous and suitable for health check endpoints
- Consider implementing exponential backoff when used in retry logic
