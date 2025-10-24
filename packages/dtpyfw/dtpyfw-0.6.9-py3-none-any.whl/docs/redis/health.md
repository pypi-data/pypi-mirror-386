# dtpyfw.redis.health

## Overview

The `health` module provides utilities for verifying Redis connectivity and server availability. The primary function, `is_redis_connected()`, performs a health check by sending a ping command to the Redis server, making it ideal for implementing health check endpoints, monitoring systems, and ensuring Redis availability before performing operations.

## Module Information

- **Module Path**: `dtpyfw.redis.health`
- **Functions**: `is_redis_connected`
- **Dependencies**:
  - `typing` - Type hints (standard library)
- **Internal Dependencies**:
  - `dtpyfw.redis.connection.RedisInstance` - Redis connection management

## Key Features

- **Simple Health Checks**: Single-function interface for Redis connectivity verification
- **Exception Capture**: Returns both status and error information for detailed diagnostics
- **Non-Blocking**: Fast operation suitable for frequent health checks
- **Type Safety**: Full type annotations for IDE support
- **Error Details**: Provides exception object for debugging and logging

## Exported Functions

```python
__all__ = ("is_redis_connected",)
```

---

## Public API Functions

### `is_redis_connected()`

Check if Redis connection is functional by sending a ping command.

```python
def is_redis_connected(redis: RedisInstance) -> Tuple[bool, Optional[Exception]]:
    ...
```

#### Parameters

| Parameter | Type            | Required | Description                                                          |
|-----------|-----------------|----------|----------------------------------------------------------------------|
| `redis`   | `RedisInstance` | Yes      | RedisInstance to test connectivity for                               |

#### Returns

`Tuple[bool, Optional[Exception]]` - A tuple containing:

- `bool`: `True` if ping successful and Redis is reachable, `False` otherwise
- `Optional[Exception]`: The exception object if connection failed (for debugging/logging), `None` if successful

#### Description

Attempts to ping the Redis server to verify connectivity and server availability. This function creates a synchronous Redis client from the provided `RedisInstance`, sends a PING command, and returns both a boolean status and any exception encountered.

The function is designed for use in:
- Health check endpoints (e.g., `/health` or `/readiness`)
- Startup validation
- Monitoring systems
- Periodic connectivity verification
- Pre-operation checks

#### Implementation Details

The function uses:
1. `redis.get_redis_client()` to obtain a Redis client
2. `client.ping()` to verify server responsiveness
3. Exception catching to handle all connection failures
4. Returns both success status and exception for flexible error handling

#### Examples

##### Basic Health Check

```python
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.health import is_redis_connected

# Setup Redis
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

redis_instance = RedisInstance(config)

# Check connection
is_connected, error = is_redis_connected(redis_instance)

if is_connected:
    print("✓ Redis is healthy and responsive")
else:
    print(f"✗ Redis connection failed: {error}")
```

##### FastAPI Health Endpoint

```python
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.health import is_redis_connected
import os

app = FastAPI()

# Initialize Redis
config = RedisConfig() \
    .set_redis_host(os.getenv("REDIS_HOST", "localhost")) \
    .set_redis_port(int(os.getenv("REDIS_PORT", "6379"))) \
    .set_redis_db("0")

redis_instance = RedisInstance(config)

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    is_healthy, error = is_redis_connected(redis_instance)
    
    if is_healthy:
        return {
            "status": "healthy",
            "redis": "connected",
            "timestamp": datetime.now().isoformat()
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "redis": "disconnected",
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    is_ready, _ = is_redis_connected(redis_instance)
    
    if is_ready:
        return {"status": "ready"}
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready"}
        )
```

##### Flask Health Endpoint

```python
from flask import Flask, jsonify
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.health import is_redis_connected
from datetime import datetime

app = Flask(__name__)

# Initialize Redis
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

redis_instance = RedisInstance(config)

@app.route("/health")
def health():
    """Health check endpoint."""
    is_healthy, error = is_redis_connected(redis_instance)
    
    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "redis": "connected" if is_healthy else "disconnected",
        "timestamp": datetime.now().isoformat()
    }
    
    if error:
        response["error"] = str(error)
    
    status_code = 200 if is_healthy else 503
    return jsonify(response), status_code

if __name__ == "__main__":
    app.run()
```

##### Startup Validation

```python
import sys
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.health import is_redis_connected

def validate_dependencies():
    """Validate all dependencies before starting the application."""
    
    # Check Redis
    config = RedisConfig() \
        .set_redis_host("localhost") \
        .set_redis_port(6379) \
        .set_redis_db("0")
    
    redis_instance = RedisInstance(config)
    is_connected, error = is_redis_connected(redis_instance)
    
    if not is_connected:
        print(f"ERROR: Redis is not available: {error}")
        print("Please ensure Redis is running and accessible.")
        sys.exit(1)
    
    print("✓ Redis connection validated")
    
    # Check other dependencies...
    return True

if __name__ == "__main__":
    validate_dependencies()
    # Start application...
```

##### Retry Logic with Health Checks

```python
import time
from typing import Optional
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.health import is_redis_connected

def wait_for_redis(
    redis_instance: RedisInstance,
    max_attempts: int = 10,
    delay: int = 2
) -> bool:
    """Wait for Redis to become available with retry logic."""
    
    for attempt in range(1, max_attempts + 1):
        print(f"Checking Redis connectivity (attempt {attempt}/{max_attempts})...")
        
        is_connected, error = is_redis_connected(redis_instance)
        
        if is_connected:
            print("✓ Redis is available")
            return True
        
        print(f"✗ Redis not available: {error}")
        
        if attempt < max_attempts:
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    print("✗ Redis failed to become available")
    return False

# Usage
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

redis_instance = RedisInstance(config)

if wait_for_redis(redis_instance, max_attempts=5, delay=3):
    print("Starting application...")
    # Start application
else:
    print("Cannot start application without Redis")
    sys.exit(1)
```

##### Monitoring and Alerting

```python
import time
from datetime import datetime
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.health import is_redis_connected

class RedisMonitor:
    """Monitor Redis health and send alerts on failures."""
    
    def __init__(self, redis_instance: RedisInstance):
        self.redis = redis_instance
        self.failure_count = 0
        self.last_success = datetime.now()
        self.alert_threshold = 3  # Alert after 3 consecutive failures
    
    def check_health(self) -> dict:
        """Perform health check and track status."""
        is_healthy, error = is_redis_connected(self.redis)
        
        if is_healthy:
            self.failure_count = 0
            self.last_success = datetime.now()
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "last_success": self.last_success.isoformat()
            }
        else:
            self.failure_count += 1
            
            # Send alert if threshold exceeded
            if self.failure_count >= self.alert_threshold:
                self.send_alert(error)
            
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(error),
                "failure_count": self.failure_count,
                "last_success": self.last_success.isoformat()
            }
    
    def send_alert(self, error: Exception):
        """Send alert about Redis failure."""
        print(f"ALERT: Redis has been unavailable for {self.failure_count} checks")
        print(f"Last error: {error}")
        print(f"Last successful connection: {self.last_success}")
        # Send email, Slack notification, PagerDuty alert, etc.
    
    def monitor(self, interval: int = 60):
        """Continuously monitor Redis health."""
        print("Starting Redis monitoring...")
        
        while True:
            status = self.check_health()
            print(f"[{status['timestamp']}] Redis status: {status['status']}")
            
            if status['status'] == 'unhealthy':
                print(f"  Error: {status['error']}")
                print(f"  Consecutive failures: {status['failure_count']}")
            
            time.sleep(interval)

# Usage
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

redis_instance = RedisInstance(config)
monitor = RedisMonitor(redis_instance)

# Run continuous monitoring
monitor.monitor(interval=30)  # Check every 30 seconds
```

##### Circuit Breaker Pattern

```python
from enum import Enum
from datetime import datetime, timedelta
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.health import is_redis_connected

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, don't attempt
    HALF_OPEN = "half_open"  # Testing if recovered

class RedisCircuitBreaker:
    """Circuit breaker for Redis operations."""
    
    def __init__(
        self,
        redis_instance: RedisInstance,
        failure_threshold: int = 5,
        timeout: int = 60
    ):
        self.redis = redis_instance
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # Seconds to wait before trying again
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def is_available(self) -> bool:
        """Check if Redis operations should be attempted."""
        
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                print("Circuit breaker: Moving to HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            print("Circuit breaker: Moving to CLOSED state (recovered)")
        
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                print(f"Circuit breaker: Moving to OPEN state (failed {self.failure_count} times)")
            self.state = CircuitState.OPEN
    
    def check_redis(self) -> bool:
        """Check Redis health and update circuit state."""
        is_healthy, error = is_redis_connected(self.redis)
        
        if is_healthy:
            self.record_success()
            return True
        else:
            print(f"Redis health check failed: {error}")
            self.record_failure()
            return False

# Usage
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_db("0")

redis_instance = RedisInstance(config)
circuit_breaker = RedisCircuitBreaker(
    redis_instance,
    failure_threshold=3,
    timeout=30
)

def perform_redis_operation():
    """Perform Redis operation with circuit breaker protection."""
    
    if not circuit_breaker.is_available():
        print("Circuit breaker is OPEN - Redis unavailable, skipping operation")
        return None
    
    # Check health before operation
    if not circuit_breaker.check_redis():
        print("Redis health check failed")
        return None
    
    # Perform operation
    try:
        with redis_instance.get_redis() as client:
            result = client.get("some_key")
            circuit_breaker.record_success()
            return result
    except Exception as e:
        print(f"Redis operation failed: {e}")
        circuit_breaker.record_failure()
        return None

# Use in application
result = perform_redis_operation()
```

##### Comprehensive Service Health Check

```python
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.health import is_redis_connected

@dataclass
class HealthCheckResult:
    service: str
    status: str
    message: str
    timestamp: str
    error: str = None

class ServiceHealthChecker:
    """Check health of all service dependencies."""
    
    def __init__(self, redis_instance: RedisInstance):
        self.redis = redis_instance
    
    def check_redis(self) -> HealthCheckResult:
        """Check Redis health."""
        is_healthy, error = is_redis_connected(self.redis)
        
        return HealthCheckResult(
            service="redis",
            status="healthy" if is_healthy else "unhealthy",
            message="Redis is responsive" if is_healthy else "Redis connection failed",
            timestamp=datetime.now().isoformat(),
            error=str(error) if error else None
        )
    
    def check_database(self) -> HealthCheckResult:
        """Check database health (example)."""
        # Your database check logic
        return HealthCheckResult(
            service="database",
            status="healthy",
            message="Database is responsive",
            timestamp=datetime.now().isoformat()
        )
    
    def check_all(self) -> Dict[str, any]:
        """Check all service dependencies."""
        checks = [
            self.check_redis(),
            self.check_database(),
            # Add more checks...
        ]
        
        all_healthy = all(check.status == "healthy" for check in checks)
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "checks": [
                {
                    "service": check.service,
                    "status": check.status,
                    "message": check.message,
                    "error": check.error
                }
                for check in checks
            ]
        }

# FastAPI integration
from fastapi import FastAPI

app = FastAPI()
config = RedisConfig().set_redis_host("localhost").set_redis_port(6379).set_redis_db("0")
redis_instance = RedisInstance(config)
health_checker = ServiceHealthChecker(redis_instance)

@app.get("/health")
async def health():
    return health_checker.check_all()
```

---

## Common Error Types

When `is_redis_connected()` returns `False`, the exception object can be one of these types:

### Connection Errors

```python
from redis.exceptions import ConnectionError, TimeoutError

is_connected, error = is_redis_connected(redis_instance)

if not is_connected:
    if isinstance(error, ConnectionError):
        print("Cannot connect to Redis server")
        # Check if Redis is running
        # Check host/port configuration
    
    elif isinstance(error, TimeoutError):
        print("Connection to Redis timed out")
        # Check network latency
        # Check socket_timeout configuration
    
    else:
        print(f"Unknown error: {type(error).__name__}: {error}")
```

### Authentication Errors

```python
from redis.exceptions import AuthenticationError

is_connected, error = is_redis_connected(redis_instance)

if not is_connected:
    if isinstance(error, AuthenticationError):
        print("Redis authentication failed")
        # Check password configuration
        # Verify Redis requirepass setting
```

### Response Errors

```python
from redis.exceptions import ResponseError

is_connected, error = is_redis_connected(redis_instance)

if not is_connected:
    if isinstance(error, ResponseError):
        print("Redis returned an error response")
        # Check Redis server status
        # Review Redis logs
```

---

## Best Practices

### 1. Use in Health Check Endpoints

Always implement health check endpoints for production applications:

```python
@app.get("/health")
async def health():
    redis_healthy, _ = is_redis_connected(redis_instance)
    
    if redis_healthy:
        return {"status": "healthy"}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy"}
        )
```

### 2. Validate Dependencies on Startup

Check Redis availability before starting the application:

```python
def main():
    is_connected, error = is_redis_connected(redis_instance)
    
    if not is_connected:
        print(f"Redis not available: {error}")
        sys.exit(1)
    
    # Start application
    app.run()
```

### 3. Implement Retry Logic

Use retry logic for transient failures:

```python
def check_redis_with_retry(max_attempts=3, delay=1):
    for attempt in range(max_attempts):
        is_connected, error = is_redis_connected(redis_instance)
        if is_connected:
            return True
        time.sleep(delay)
    return False
```

### 4. Log Health Check Results

Log health check outcomes for monitoring:

```python
import logging

logger = logging.getLogger(__name__)

is_healthy, error = is_redis_connected(redis_instance)

if is_healthy:
    logger.info("Redis health check passed")
else:
    logger.error(f"Redis health check failed: {error}")
```

### 5. Include Health Checks in CI/CD

Verify Redis connectivity in deployment pipelines:

```python
# In deployment script
def verify_deployment():
    is_connected, error = is_redis_connected(redis_instance)
    
    if not is_connected:
        print(f"Deployment verification failed: {error}")
        rollback()
        sys.exit(1)
    
    print("Deployment verified successfully")
```

### 6. Use Circuit Breakers for Reliability

Implement circuit breakers to prevent cascading failures:

```python
circuit_breaker = RedisCircuitBreaker(redis_instance)

if circuit_breaker.is_available():
    # Perform Redis operations
    pass
else:
    # Use fallback mechanism
    pass
```

---

## Integration Examples

### Docker Compose Health Check

```yaml
version: '3.8'

services:
  app:
    build: .
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "from app.health import check; exit(0 if check() else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Kubernetes Probes

```python
# health.py - Used by Kubernetes probes
from dtpyfw.redis.connection import RedisInstance
from dtpyfw.redis.config import RedisConfig
from dtpyfw.redis.health import is_redis_connected
import sys

def check() -> bool:
    """Health check for Kubernetes probes."""
    config = RedisConfig() \
        .set_redis_host("redis-service") \
        .set_redis_port(6379) \
        .set_redis_db("0")
    
    redis_instance = RedisInstance(config)
    is_healthy, _ = is_redis_connected(redis_instance)
    return is_healthy

if __name__ == "__main__":
    sys.exit(0 if check() else 1)
```

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:latest
        livenessProbe:
          exec:
            command: ["python", "health.py"]
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command: ["python", "health.py"]
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## Performance Considerations

### Health Check Frequency

The `is_redis_connected()` function is lightweight but should still be used judiciously:

```python
# Good: Reasonable intervals
# Health endpoint: Check on each request (fast operation)
# Monitoring: Every 30-60 seconds
# Startup: Once before starting

# Avoid: Excessive checking
# Don't check before every Redis operation (use circuit breaker instead)
```

### Timeout Configuration

Ensure reasonable timeout settings to avoid hanging health checks:

```python
config = RedisConfig() \
    .set_redis_host("localhost") \
    .set_redis_port(6379) \
    .set_redis_socket_timeout(3)  # 3-second timeout for health checks
```

---

## Related Documentation

- [dtpyfw.redis.connection](connection.md) - Redis connection management and RedisInstance
- [dtpyfw.redis.config](config.md) - Redis configuration builder
- [dtpyfw.redis.caching](caching.md) - Redis caching utilities

---

## External References

- [Redis PING Command](https://redis.io/commands/ping/)
- [Kubernetes Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [FastAPI Health Checks](https://fastapi.tiangolo.com/advanced/custom-response/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
