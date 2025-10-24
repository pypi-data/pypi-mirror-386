# Async Utilities

## Overview

The `dtpyfw.core.async` module provides helpers for bridging asynchronous and synchronous code. This is particularly useful when you need to execute async functions from synchronous contexts or when integrating async libraries with sync codebases.

## Module Path

```python
from dtpyfw.core.async import async_to_sync
```

## Functions

### `async_to_sync(awaitable: Awaitable) -> Any`

Execute an awaitable in a new event loop and return its result.

**Description:**

Runs an async coroutine or awaitable object in a synchronous context by using the current event loop to execute it to completion. This function is useful when you have asynchronous code that needs to be called from a synchronous function or script.

**Parameters:**

- **awaitable** (`Awaitable`): An awaitable object (coroutine, task, or future) to execute.

**Returns:**

- **`Any`**: The result returned by the awaitable after it completes execution.

**Example:**

```python
import asyncio
from dtpyfw.core.async import async_to_sync

# Define an async function
async def fetch_data():
    await asyncio.sleep(1)
    return {"data": "example"}

# Execute it synchronously
result = async_to_sync(fetch_data())
print(result)  # Output: {'data': 'example'}
```

**Use Cases:**

1. **Calling async APIs from sync code:**
   ```python
   from dtpyfw.core.async import async_to_sync
   import httpx
   
   async def get_user(user_id: int):
       async with httpx.AsyncClient() as client:
           response = await client.get(f"https://api.example.com/users/{user_id}")
           return response.json()
   
   # In a synchronous context
   user_data = async_to_sync(get_user(123))
   ```

2. **Testing async code:**
   ```python
   from dtpyfw.core.async import async_to_sync
   
   async def process_items(items):
       results = []
       for item in items:
           await asyncio.sleep(0.1)
           results.append(item * 2)
       return results
   
   # Test synchronously
   result = async_to_sync(process_items([1, 2, 3]))
   assert result == [2, 4, 6]
   ```

3. **Legacy code integration:**
   ```python
   from dtpyfw.core.async import async_to_sync
   
   # Legacy synchronous function that needs to call new async code
   def legacy_function():
       # New async functionality
       async def new_async_feature():
           await some_async_operation()
           return result
       
       # Bridge the gap
       return async_to_sync(new_async_feature())
   ```

## Important Notes

1. **Event Loop Requirement:** This function uses `asyncio.get_event_loop()` which assumes an event loop is available. In Python 3.10+, you might want to use `asyncio.run()` as an alternative for simpler cases.

2. **Blocking Nature:** While this function allows you to call async code from sync contexts, it will block the calling thread until the awaitable completes. It does not make the synchronous code asynchronous.

3. **Nested Event Loops:** Be cautious when using this function within an already running event loop, as it may cause issues. It's best used from purely synchronous contexts.

4. **Alternative Approach:** For newer Python versions (3.7+), consider using `asyncio.run()` directly for simpler use cases:
   ```python
   import asyncio
   
   result = asyncio.run(fetch_data())
   ```

## Related Modules

- **dtpyfw.core.retry** - For retry logic that works with both sync and async functions
- **dtpyfw.api** - FastAPI application helpers that work natively with async

## Dependencies

- `asyncio` - Python's built-in async library (no external dependencies)

## Best Practices

1. **Use sparingly:** Prefer async contexts when possible rather than bridging to sync.
2. **Document usage:** Clearly document when sync-to-async bridging is happening.
3. **Consider alternatives:** Evaluate if your entire workflow could be async instead.
4. **Test thoroughly:** Ensure the bridging doesn't introduce unexpected blocking behavior.

## See Also

- Python's [asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [Async/await in Python](https://docs.python.org/3/library/asyncio-task.html)
