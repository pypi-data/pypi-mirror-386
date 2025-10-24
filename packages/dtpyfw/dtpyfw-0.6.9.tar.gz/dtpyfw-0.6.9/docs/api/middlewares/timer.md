# dtpyfw.api.middlewares.timer

Request timing middleware for measuring and reporting API response times.

## Module Overview

The `timer` module provides the `Timer` middleware class that measures the processing time for each request and adds it to the response headers. This is useful for performance monitoring, debugging, and identifying slow endpoints.

## Key Features

- **Automatic Timing**: Measures request processing time automatically
- **Response Header**: Adds processing time to `X-Process-Time` header
- **Millisecond Precision**: Reports time in milliseconds, rounded to nearest integer
- **Zero Configuration**: Works out of the box with no setup required
- **Low Overhead**: Minimal performance impact

## Classes

### Timer

```python
class Timer:
    """Middleware for tracking request processing time."""
```

#### Constructor

```python
def __init__(self) -> None
```

Creates a new Timer middleware instance with no configuration required.

**Parameters:**

None

**Returns:**

None

#### Methods

##### \_\_call\_\_

```python
async def __call__(self, request: Request, call_next: Callable) -> Response
```

Starlette middleware dispatch method that measures processing time and adds it to response headers.

**Parameters:**

- **request** (`Request`): The incoming FastAPI request
- **call_next** (`Callable`): The next middleware or route handler in the chain

**Returns:**

- `Response`: The response with added `X-Process-Time` header

**Behavior:**

1. Records start time before processing request
2. Calls next middleware/handler in the chain
3. Calculates elapsed time after response is ready
4. Adds `X-Process-Time` header with duration in milliseconds
5. Returns the enhanced response

## Usage Examples

### Automatic Registration with Application

The Timer middleware is automatically registered when using the `Application` class:

```python
from dtpyfw.api import Application

app = Application(
    title="My API",
    version="1.0.0"
).get_app()

# Timer middleware is automatically included
# No additional configuration needed
```

### Manual Registration

If using FastAPI directly without the `Application` wrapper:

```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from dtpyfw.api.middlewares.timer import Timer

app = FastAPI()

# Register timer middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=Timer())

@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}

# All responses will include X-Process-Time header
```

### Reading Processing Time in Responses

```python
import requests

response = requests.get("https://api.example.com/users")

# Access the processing time from response headers
process_time = response.headers.get("X-Process-Time")
print(f"Request took {process_time}ms")
```

### Client-Side Example (JavaScript)

```javascript
fetch("https://api.example.com/users")
  .then(response => {
    const processTime = response.headers.get("X-Process-Time");
    console.log(`Request took ${processTime}ms`);
    return response.json();
  })
  .then(data => console.log(data));
```

### Using in Frontend Monitoring

```typescript
// React hook for API monitoring
function useApiCall(url: string) {
  const [data, setData] = useState(null);
  const [processTime, setProcessTime] = useState<number | null>(null);

  useEffect(() => {
    fetch(url)
      .then(response => {
        const time = response.headers.get("X-Process-Time");
        setProcessTime(time ? parseInt(time) : null);
        return response.json();
      })
      .then(setData);
  }, [url]);

  return { data, processTime };
}
```

### Performance Testing

```python
from fastapi.testclient import TestClient

def test_endpoint_performance():
    client = TestClient(app)
    
    response = client.get("/users")
    process_time = int(response.headers["X-Process-Time"])
    
    # Assert response time is acceptable
    assert process_time < 1000, f"Endpoint too slow: {process_time}ms"
    assert response.status_code == 200
```

### Logging Slow Requests

```python
from fastapi import Request, Response
from dtpyfw.log import footprint

async def log_slow_requests(request: Request, call_next):
    response = await call_next(request)
    
    # Timer middleware has already added the header
    process_time = int(response.headers.get("X-Process-Time", 0))
    
    if process_time > 1000:  # Log if > 1 second
        footprint.leave(
            log_type="warning",
            controller="slow_request_logger",
            subject="Slow API Request",
            message=f"Request took {process_time}ms",
            payload={
                "path": request.url.path,
                "method": request.method,
                "process_time_ms": process_time
            }
        )
    
    return response

# Add after Timer middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=log_slow_requests)
```

## Response Header Format

The middleware adds a single header to all responses:

```
X-Process-Time: <milliseconds>
```

### Example Response Headers

```http
HTTP/1.1 200 OK
content-type: application/json
x-process-time: 42
content-length: 156

{"success": true, "data": [...]}
```

**Values:**

- `X-Process-Time`: Integer representing milliseconds (rounded)
- Fast requests: Typically 1-100ms
- Slow requests: > 1000ms may indicate performance issues

## Performance Monitoring Examples

### Simple Performance Dashboard

```python
from collections import defaultdict
from fastapi import Request, Response

# Store processing times by endpoint
endpoint_times = defaultdict(list)

async def collect_metrics(request: Request, call_next):
    response = await call_next(request)
    
    process_time = int(response.headers.get("X-Process-Time", 0))
    endpoint_times[request.url.path].append(process_time)
    
    return response

@app.get("/metrics/performance")
def get_performance_metrics():
    metrics = {}
    for endpoint, times in endpoint_times.items():
        metrics[endpoint] = {
            "count": len(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
        }
    return metrics
```

### Prometheus Integration

```python
from prometheus_client import Histogram

# Create histogram metric
request_duration = Histogram(
    'http_request_duration_milliseconds',
    'HTTP request duration in milliseconds',
    ['method', 'endpoint']
)

async def prometheus_metrics(request: Request, call_next):
    response = await call_next(request)
    
    process_time = int(response.headers.get("X-Process-Time", 0))
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    return response
```

### Alerting on Slow Endpoints

```python
from dtpyfw.log import footprint

SLOW_THRESHOLD_MS = 2000

async def alert_slow_requests(request: Request, call_next):
    response = await call_next(request)
    
    process_time = int(response.headers.get("X-Process-Time", 0))
    
    if process_time > SLOW_THRESHOLD_MS:
        # Send alert to monitoring system
        footprint.leave(
            log_type="error",
            controller="performance_monitor",
            subject="Critical: Slow API Response",
            message=f"Endpoint {request.url.path} took {process_time}ms",
            payload={
                "path": request.url.path,
                "method": request.method,
                "process_time_ms": process_time,
                "threshold_ms": SLOW_THRESHOLD_MS
            }
        )
    
    return response
```

## Integration with Other Middlewares

The Timer middleware is typically registered first to measure total processing time:

```python
from dtpyfw.api.middlewares import Timer, Runtime

app = FastAPI()

# Timer should be first to measure total time
app.add_middleware(BaseHTTPMiddleware, dispatch=Timer())
app.add_middleware(BaseHTTPMiddleware, dispatch=Runtime(hide_error_messages=True))
app.add_middleware(BaseHTTPMiddleware, dispatch=CustomMiddleware())
```

## Middleware Execution Order

```
Client Request
    ↓
[Timer Start] ← Records start time
    ↓
[Other Middlewares]
    ↓
[Route Handler]
    ↓
[Other Middlewares]
    ↓
[Timer End] ← Calculates duration, adds header
    ↓
Client Response (with X-Process-Time header)
```

## Testing Timer Middleware

```python
from fastapi.testclient import TestClient
import time

def test_timer_adds_header():
    client = TestClient(app)
    
    response = client.get("/users")
    
    # Timer header should be present
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Process-Time"].isdigit()

def test_timer_measures_accurately():
    @app.get("/slow-endpoint")
    async def slow_endpoint():
        await asyncio.sleep(0.1)  # Sleep for 100ms
        return {"status": "ok"}
    
    client = TestClient(app)
    response = client.get("/slow-endpoint")
    
    process_time = int(response.headers["X-Process-Time"])
    
    # Should be at least 100ms
    assert process_time >= 100
    # Should not be unreasonably high
    assert process_time < 200
```

## Use Cases

### 1. Performance Monitoring

Track endpoint performance over time to identify degradation:

```python
# Monitor average response times
# Alert when averages exceed thresholds
# Identify endpoints that need optimization
```

### 2. Load Testing

Measure performance under load:

```python
# Run load tests and collect X-Process-Time values
# Analyze percentiles (p50, p95, p99)
# Identify breaking points
```

### 3. SLA Compliance

Ensure API meets service level agreements:

```python
# Track percentage of requests under SLA threshold
# Generate SLA compliance reports
# Alert on SLA violations
```

### 4. Debugging

Identify slow operations during development:

```python
# Check X-Process-Time in browser DevTools
# Compare times across different endpoints
# Optimize slow operations
```

### 5. User Experience

Provide timing information to frontend:

```python
# Show loading indicators based on expected time
# Retry logic for slow requests
# Timeout handling
```

## Best Practices

1. **Always Include Timer**: Register Timer middleware in all applications for monitoring
2. **Register First**: Place Timer as the first middleware to measure total processing time
3. **Log Slow Requests**: Set up monitoring for requests exceeding thresholds
4. **Track Trends**: Monitor processing times over time, not just individual requests
5. **Set Baselines**: Establish baseline performance metrics for each endpoint
6. **Alert on Anomalies**: Set up alerts for unusual performance degradation
7. **Regular Reviews**: Periodically review slow endpoints and optimize

## Performance Characteristics

- **Overhead**: < 1ms per request (negligible)
- **Memory**: No additional memory used (no state stored)
- **CPU**: Minimal CPU usage (two time.time() calls)
- **Thread-Safe**: Safe for concurrent requests
- **Async-Compatible**: Works with both sync and async handlers

## Common Performance Thresholds

| Response Time | Category | Action |
|--------------|----------|---------|
| < 100ms | Excellent | No action needed |
| 100-300ms | Good | Monitor |
| 300-1000ms | Acceptable | Consider optimization |
| 1000-3000ms | Slow | Investigate and optimize |
| > 3000ms | Critical | Immediate attention required |

## Debugging Slow Requests

When you see high processing times:

1. **Check Database Queries**: Use query profiling tools
2. **Review External API Calls**: Check third-party service response times
3. **Examine Loops**: Look for inefficient loops or algorithms
4. **Check I/O Operations**: Identify blocking I/O operations
5. **Profile Code**: Use profiling tools to find bottlenecks
6. **Review Middleware**: Check if other middlewares are slow
7. **Database Connections**: Ensure connection pooling is configured properly

## Related Modules

- [`dtpyfw.api.middlewares.runtime`](runtime.md): Runtime exception handler
- [`dtpyfw.api.application`](../application.md): Application configuration
- [`dtpyfw.log.footprint`](../../log/footprint.md): Logging system
- FastAPI Middleware: [FastAPI Middleware Documentation](https://fastapi.tiangolo.com/tutorial/middleware/)
