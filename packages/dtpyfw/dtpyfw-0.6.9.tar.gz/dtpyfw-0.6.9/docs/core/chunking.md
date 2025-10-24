# Chunking Utilities

## Overview

The `dtpyfw.core.chunking` module provides utilities for splitting lists into smaller, manageable chunks. This is useful for batch processing, pagination, memory optimization, and parallel processing of large datasets.

## Module Path

```python
from dtpyfw.core.chunking import chunk_list, chunk_list_generator
```

## Functions

### `chunk_list(lst: List[Any], chunk_size: int) -> List[Any]`

Split a list into chunks of a specified size.

**Description:**

Divides a list into smaller sublists, each with a maximum size specified by `chunk_size`. The last chunk may be smaller if the list length is not evenly divisible by `chunk_size`. All chunks are created in memory at once.

**Parameters:**

- **lst** (`List[Any]`): The list to split into chunks.
- **chunk_size** (`int`): The maximum number of elements in each chunk.

**Returns:**

- **`List[Any]`**: A list of chunks, where each chunk is itself a list.

**Example:**

```python
from dtpyfw.core.chunking import chunk_list

# Split a list into chunks of 3
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
chunks = chunk_list(numbers, 3)
print(chunks)
# Output: [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

# Process each chunk
for chunk in chunks:
    process_batch(chunk)
```

---

### `chunk_list_generator(lst: List[Any], chunk_size: int) -> Generator[List[Any], None, None]`

Generate chunks of a specified size from a list.

**Description:**

Yields successive chunks from the input list without creating all chunks in memory at once. This is a memory-efficient alternative to `chunk_list()`, especially useful for processing large lists with limited memory.

**Parameters:**

- **lst** (`List[Any]`): The list to split into chunks.
- **chunk_size** (`int`): The maximum number of elements in each chunk.

**Yields:**

- **`List[Any]`**: Lists containing up to `chunk_size` elements from the original list.

**Example:**

```python
from dtpyfw.core.chunking import chunk_list_generator

# Create a generator for chunks of 100
large_list = list(range(1000))
chunk_gen = chunk_list_generator(large_list, 100)

# Process chunks one at a time (memory efficient)
for chunk in chunk_gen:
    process_batch(chunk)
```

## Use Cases

### 1. Database Batch Operations

```python
from dtpyfw.core.chunking import chunk_list
from your_db import bulk_insert

# Insert 10,000 records in batches of 500
records = [{"id": i, "data": f"record_{i}"} for i in range(10000)]

for chunk in chunk_list(records, 500):
    bulk_insert(chunk)
```

### 2. API Rate Limiting

```python
from dtpyfw.core.chunking import chunk_list_generator
import time

# Process API requests in batches to respect rate limits
user_ids = range(1, 1001)

for batch in chunk_list_generator(list(user_ids), 10):
    # Process 10 users at a time
    results = [fetch_user_data(uid) for uid in batch]
    time.sleep(1)  # Wait between batches
```

### 3. Parallel Processing

```python
from dtpyfw.core.chunking import chunk_list
from concurrent.futures import ThreadPoolExecutor

def process_chunk(chunk):
    # Process items in this chunk
    return [item * 2 for item in chunk]

data = list(range(1000))
chunks = chunk_list(data, 100)

# Process chunks in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(process_chunk, chunks)
```

### 4. Memory-Efficient File Processing

```python
from dtpyfw.core.chunking import chunk_list_generator

# Read large file and process in chunks
with open("large_file.txt", "r") as f:
    lines = f.readlines()

for chunk in chunk_list_generator(lines, 1000):
    # Process 1000 lines at a time
    process_lines(chunk)
```

### 5. Pagination Implementation

```python
from dtpyfw.core.chunking import chunk_list

def paginate_results(items, page_number, page_size=20):
    """Return a specific page of results."""
    pages = chunk_list(items, page_size)
    if 0 <= page_number < len(pages):
        return pages[page_number]
    return []

# Get page 2 (0-indexed) of results
all_items = fetch_all_items()
page_items = paginate_results(all_items, page_number=2, page_size=20)
```

### 6. Bulk Email Sending

```python
from dtpyfw.core.chunking import chunk_list_generator

recipients = get_all_recipients()  # Could be thousands

# Send emails in batches of 50
for batch in chunk_list_generator(recipients, 50):
    send_bulk_email(
        recipients=batch,
        subject="Newsletter",
        body="..."
    )
```

## Performance Considerations

### `chunk_list()` vs `chunk_list_generator()`

| Feature | `chunk_list()` | `chunk_list_generator()` |
|---------|---------------|-------------------------|
| Memory Usage | High (creates all chunks) | Low (lazy evaluation) |
| Speed | Faster for small lists | Better for large lists |
| Use Case | When you need all chunks | When processing sequentially |
| Iteration | Can iterate multiple times | Single iteration (generator) |

**Recommendation:**

- Use `chunk_list()` when:
  - The list is small (< 10,000 items)
  - You need to access chunks multiple times
  - You need random access to chunks

- Use `chunk_list_generator()` when:
  - The list is very large (> 100,000 items)
  - You only need to process chunks once
  - Memory is a concern
  - Processing each chunk is time-consuming

## Examples with Real-World Data

### Processing Database Records

```python
from dtpyfw.core.chunking import chunk_list
from your_orm import session, User

# Fetch all users
all_users = session.query(User).all()

# Update users in batches
for user_chunk in chunk_list(all_users, 100):
    for user in user_chunk:
        user.last_checked = datetime.now()
    session.commit()  # Commit each batch
```

### S3 File Upload

```python
from dtpyfw.core.chunking import chunk_list_generator
import boto3

s3_client = boto3.client('s3')
files_to_upload = ["file1.txt", "file2.txt", ...]  # 10,000 files

for batch in chunk_list_generator(files_to_upload, 25):
    # Upload 25 files at a time
    for filename in batch:
        s3_client.upload_file(filename, 'my-bucket', filename)
```

## Related Modules

- **dtpyfw.core.async** - For async batch processing
- **dtpyfw.worker** - For distributed task processing
- **dtpyfw.db** - For database batch operations

## Best Practices

1. **Choose appropriate chunk size:**
   - Too small: Overhead from many iterations
   - Too large: Memory issues or timeout problems
   - Typical range: 50-1000 depending on data size

2. **Handle errors per chunk:**
   ```python
   from dtpyfw.core.chunking import chunk_list
   
   for chunk in chunk_list(items, 100):
       try:
           process_chunk(chunk)
       except Exception as e:
           log_error(f"Failed to process chunk: {e}")
           continue  # Continue with next chunk
   ```

3. **Monitor progress:**
   ```python
   from dtpyfw.core.chunking import chunk_list
   
   chunks = chunk_list(items, 100)
   total_chunks = len(chunks)
   
   for i, chunk in enumerate(chunks, 1):
       process_chunk(chunk)
       print(f"Processed {i}/{total_chunks} chunks")
   ```

4. **Use generators for large datasets:**
   Always prefer `chunk_list_generator()` when dealing with datasets that might grow or are already large.

## Dependencies

This module has no external dependencies and uses only Python's built-in features.

## See Also

- [Python's itertools.batched()](https://docs.python.org/3/library/itertools.html#itertools.batched) (Python 3.12+)
- [Generator expressions](https://docs.python.org/3/tutorial/classes.html#generators)
