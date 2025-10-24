# Bucket Module

## Overview

The `bucket` module provides a high-level interface for interacting with S3-compatible object storage services. It wraps the boto3 S3 client and offers simplified methods for common operations such as uploading, downloading, duplicating, and deleting objects.

**Module Path:** `dtpyfw.bucket.bucket`

**Dependencies:** 
- `boto3` (required, install with `pip install dtpyfw[bucket]`)
- `botocore` (required, install with `pip install dtpyfw[bucket]`)

## Installation

To use the bucket module, install dtpyfw with the bucket extra:

```bash
pip install dtpyfw[bucket]
```

Or if installing all extras:

```bash
pip install dtpyfw[all]
```

## Class: Bucket

The `Bucket` class provides a simplified interface for S3-compatible storage operations.

### Constructor

```python
Bucket(
    name: str | None = None,
    s3_mode: str | None = None,
    endpoint_url: str | None = None,
    access_key: str | None = None,
    secret_key: str | None = None,
    region_name: str | None = None,
) -> None
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str \| None` | `None` | Name of the S3 bucket to interact with |
| `s3_mode` | `str \| None` | `None` | Flag to enable AWS S3 mode. If truthy, uses native AWS S3 instead of S3-compatible storage |
| `endpoint_url` | `str \| None` | `None` | Custom endpoint URL for S3-compatible storage (e.g., MinIO, DigitalOcean Spaces). Ignored when `s3_mode` is enabled |
| `access_key` | `str \| None` | `None` | AWS access key ID or equivalent credential for authentication |
| `secret_key` | `str \| None` | `None` | AWS secret access key or equivalent credential for authentication |
| `region_name` | `str \| None` | `None` | AWS region name (e.g., "us-east-1"). Only used when `s3_mode` is enabled |

#### Example

```python
from dtpyfw.bucket import Bucket

# For AWS S3
s3_bucket = Bucket(
    name="my-aws-bucket",
    s3_mode="true",
    access_key="AKIAIOSFODNN7EXAMPLE",
    secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    region_name="us-east-1"
)

# For S3-compatible storage (e.g., MinIO)
minio_bucket = Bucket(
    name="my-minio-bucket",
    endpoint_url="https://minio.example.com",
    access_key="minioadmin",
    secret_key="minioadmin"
)
```

---

## Methods

### url_generator

Generate the public URL for an object in the bucket.

```python
def url_generator(self, key: str) -> str
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | `str` | Object key/path within the bucket |

#### Returns

`str` - The public URL string for accessing the object

#### Behavior

- In **S3 mode**: Returns `{endpoint_url}/{key}`
- In **S3-compatible mode**: Returns `{endpoint_url}/{bucket_name}/{key}`

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")
url = bucket.url_generator("documents/file.pdf")
# Returns: "https://storage.example.com/my-bucket/documents/file.pdf"
```

---

### get_s3

Get the underlying boto3 S3 client instance.

```python
def get_s3(self) -> BaseClient
```

#### Returns

`BaseClient` - The boto3 BaseClient instance for direct S3 operations

#### Use Case

Use this method when you need direct access to boto3 client for advanced operations not covered by the Bucket wrapper.

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")
s3_client = bucket.get_s3()
# Now you can use any boto3 S3 client method
response = s3_client.list_objects_v2(Bucket="my-bucket", Prefix="documents/")
```

---

### get_bucket_name

Get the configured bucket name.

```python
def get_bucket_name(self) -> str | None
```

#### Returns

`str | None` - The bucket name if configured during initialization, otherwise `None`

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")
name = bucket.get_bucket_name()
# Returns: "my-bucket"
```

---

### check_file_exists

Check if an object exists in the bucket.

```python
def check_file_exists(self, key: str) -> bool
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | `str` | Object key/path to check for existence |

#### Returns

`bool` - `True` if the object exists, `False` otherwise

#### Exceptions

- `RequestException` (500): Raised when S3 credentials are invalid or missing

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")

if bucket.check_file_exists("documents/report.pdf"):
    print("File exists")
else:
    print("File not found")
```

---

### upload

Upload bytes content to the bucket.

```python
def upload(
    self, 
    file: bytes, 
    key: str, 
    content_type: str, 
    cache_control: str = "no-cache"
) -> str
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | `bytes` | - | Binary content to upload |
| `key` | `str` | - | Object key/path for the uploaded content |
| `content_type` | `str` | - | MIME type of the content (e.g., "image/png", "application/pdf") |
| `cache_control` | `str` | `"no-cache"` | Cache control header value for HTTP caching |

#### Returns

`str` - Public URL of the uploaded object

#### Exceptions

- `RequestException` (500): Raised when S3 credentials are invalid or missing

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")

# Upload binary data
file_content = b"Hello, World!"
url = bucket.upload(
    file=file_content,
    key="documents/hello.txt",
    content_type="text/plain",
    cache_control="max-age=3600"
)
print(f"Uploaded to: {url}")
```

---

### download

Download an object from the bucket to a local file.

```python
def download(self, key: str, filepath: str) -> bool
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | `str` | Object key/path to download |
| `filepath` | `str` | Local filesystem path where the file will be saved |

#### Returns

`bool` - `True` if download succeeded

#### Exceptions

- `RequestException` (500): Raised when S3 credentials are invalid or missing

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")

# Download file
success = bucket.download(
    key="documents/report.pdf",
    filepath="/tmp/local_report.pdf"
)
if success:
    print("Download completed")
```

---

### download_fileobj

Download an object from the bucket into an open file object.

```python
def download_fileobj(self, key: str, file: BinaryIO) -> bool
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | `str` | Object key/path to download |
| `file` | `BinaryIO` | Open file object in binary write mode to receive the content |

#### Returns

`bool` - `True` if download succeeded

#### Exceptions

- `RequestException` (500): Raised when S3 credentials are invalid or missing

#### Use Case

This method is useful when you want more control over the file handling or need to stream content directly into memory.

#### Example

```python
from io import BytesIO

bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")

# Download to file object
with open("/tmp/output.pdf", "wb") as f:
    bucket.download_fileobj(key="documents/report.pdf", file=f)

# Or download to in-memory buffer
buffer = BytesIO()
bucket.download_fileobj(key="documents/report.pdf", file=buffer)
buffer.seek(0)  # Reset pointer to beginning
content = buffer.read()
```

---

### upload_by_path

Upload a file from the local filesystem to the bucket.

```python
def upload_by_path(
    self,
    file_path: str,
    key: str,
    content_type: str | None = None,
    cache_control: str = "no-cache",
) -> str
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | `str` | - | Local filesystem path to the file to upload |
| `key` | `str` | - | Object key/path for the uploaded content |
| `content_type` | `str \| None` | `None` | MIME type of the content. Defaults to "application/octet-stream" if not specified |
| `cache_control` | `str` | `"no-cache"` | Cache control header value |

#### Returns

`str` - Public URL of the uploaded object

#### Exceptions

- `RequestException` (500): Raised when S3 credentials are invalid or missing
- `FileNotFoundError`: Raised when the specified file_path doesn't exist

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")

# Upload a file
url = bucket.upload_by_path(
    file_path="/home/user/document.pdf",
    key="documents/uploaded_doc.pdf",
    content_type="application/pdf",
    cache_control="public, max-age=86400"
)
print(f"Uploaded to: {url}")
```

---

### duplicate

Duplicate an object within the bucket.

```python
def duplicate(
    self, 
    source_key: str, 
    destination_key: str, 
    cache_control: str = "no-cache"
) -> str
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_key` | `str` | - | Object key/path to copy from |
| `destination_key` | `str` | - | Object key/path to copy to |
| `cache_control` | `str` | `"no-cache"` | Cache control header value for the duplicated object |

#### Returns

`str` - Public URL of the duplicated object

#### Exceptions

- `RequestException` (500): Raised when S3 credentials are invalid or missing

#### Note

This method will overwrite the destination if it already exists.

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")

# Duplicate a file
url = bucket.duplicate(
    source_key="documents/original.pdf",
    destination_key="documents/copy.pdf",
    cache_control="max-age=3600"
)
print(f"Duplicated to: {url}")
```

---

### safe_duplicate

Duplicate an object while avoiding name collisions by automatically appending a counter.

```python
def safe_duplicate(
    self, 
    source_key: str, 
    cache_control: str = "no-cache"
) -> str
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_key` | `str` | - | Object key/path to copy from |
| `cache_control` | `str` | `"no-cache"` | Cache control header value |

#### Returns

`str` - Public URL of the duplicated object with a unique key

#### Exceptions

- `RequestException` (500): Raised when S3 credentials are invalid or missing

#### Behavior

The method generates a unique destination key by appending a counter before the file extension:
- If `documents/file.pdf` exists, creates `documents/file-2.pdf`
- If that exists too, creates `documents/file-3.pdf`, and so on

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")

# Safe duplicate - automatically finds unique name
url1 = bucket.safe_duplicate(source_key="documents/report.pdf")
# Creates: documents/report.pdf (if it doesn't exist) or documents/report-2.pdf

url2 = bucket.safe_duplicate(source_key="documents/report.pdf")
# Creates: documents/report-2.pdf or documents/report-3.pdf (depending on what exists)
```

---

### delete

Delete an object from the bucket.

```python
def delete(self, key: str) -> bool
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | `str` | Object key/path to delete |

#### Returns

`bool` - `True` if the object was deleted or did not exist

#### Exceptions

- `RequestException` (500): Raised when S3 credentials are invalid or missing

#### Note

This method returns `True` even if the object doesn't exist (idempotent operation).

#### Example

```python
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")

# Delete a file
success = bucket.delete(key="documents/old_report.pdf")
if success:
    print("File deleted successfully")
```

---

## Complete Usage Example

Here's a comprehensive example demonstrating various bucket operations:

```python
from dtpyfw.bucket import Bucket
import os

# Initialize bucket
bucket = Bucket(
    name="company-documents",
    endpoint_url="https://minio.example.com",
    access_key="minioadmin",
    secret_key="minioadmin"
)

# 1. Upload a file from disk
upload_url = bucket.upload_by_path(
    file_path="/home/user/report.pdf",
    key="reports/2024/annual_report.pdf",
    content_type="application/pdf",
    cache_control="public, max-age=86400"
)
print(f"Uploaded: {upload_url}")

# 2. Check if file exists
if bucket.check_file_exists("reports/2024/annual_report.pdf"):
    print("File exists in bucket")

# 3. Upload binary data
data = b"Important meeting notes"
notes_url = bucket.upload(
    file=data,
    key="notes/meeting_2024_10_24.txt",
    content_type="text/plain"
)
print(f"Notes uploaded: {notes_url}")

# 4. Duplicate the file
backup_url = bucket.duplicate(
    source_key="reports/2024/annual_report.pdf",
    destination_key="reports/backups/annual_report_backup.pdf"
)
print(f"Backup created: {backup_url}")

# 5. Safe duplicate (auto-increment naming)
safe_backup = bucket.safe_duplicate(
    source_key="reports/2024/annual_report.pdf"
)
print(f"Safe backup: {safe_backup}")

# 6. Download file
bucket.download(
    key="reports/2024/annual_report.pdf",
    filepath="/tmp/downloaded_report.pdf"
)
print("File downloaded to /tmp/")

# 7. Download to file object
with open("/tmp/notes.txt", "wb") as f:
    bucket.download_fileobj(
        key="notes/meeting_2024_10_24.txt",
        file=f
    )

# 8. Generate public URL
url = bucket.url_generator("reports/2024/annual_report.pdf")
print(f"Public URL: {url}")

# 9. Delete old files
bucket.delete(key="reports/2023/old_report.pdf")
print("Old file deleted")

# 10. Access underlying boto3 client for advanced operations
s3_client = bucket.get_s3()
response = s3_client.list_objects_v2(
    Bucket=bucket.get_bucket_name(),
    Prefix="reports/"
)
print(f"Found {response.get('KeyCount', 0)} objects in reports/")
```

---

## Environment Variables Pattern

While the `Bucket` class accepts credentials directly, in production environments, it's common to load these from environment variables:

```python
import os
from dtpyfw.bucket import Bucket

bucket = Bucket(
    name=os.getenv("S3_BUCKET_NAME"),
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    access_key=os.getenv("S3_ACCESS_KEY"),
    secret_key=os.getenv("S3_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION")  # for AWS S3
)
```

Example `.env` file:
```env
S3_BUCKET_NAME=my-bucket
S3_ENDPOINT_URL=https://minio.example.com
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

For AWS S3:
```env
S3_BUCKET_NAME=my-aws-bucket
S3_MODE=true
S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
```

---

## Best Practices

### 1. Connection Reuse
Create a single `Bucket` instance and reuse it for multiple operations instead of creating new instances for each operation:

```python
# Good
bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")
for i in range(100):
    bucket.upload(data, f"file_{i}.txt", "text/plain")

# Avoid
for i in range(100):
    bucket = Bucket(name="my-bucket", endpoint_url="https://storage.example.com")
    bucket.upload(data, f"file_{i}.txt", "text/plain")
```

### 2. Content Type Specification
Always specify the correct content type for better browser handling:

```python
# Images
bucket.upload(image_data, "images/photo.jpg", content_type="image/jpeg")

# JSON
bucket.upload(json_data, "data/config.json", content_type="application/json")

# HTML
bucket.upload(html_data, "pages/index.html", content_type="text/html")
```

### 3. Cache Control for Performance
Use appropriate cache control headers:

```python
# Static assets (cache for 1 year)
bucket.upload(
    css_data, 
    "static/style.css", 
    "text/css",
    cache_control="public, max-age=31536000, immutable"
)

# Dynamic content (no cache)
bucket.upload(
    api_response, 
    "api/data.json", 
    "application/json",
    cache_control="no-cache, no-store, must-revalidate"
)
```

### 4. Error Handling
Always handle potential exceptions:

```python
from dtpyfw.core.exception import RequestException

try:
    url = bucket.upload(file_data, "documents/file.pdf", "application/pdf")
    print(f"Success: {url}")
except RequestException as e:
    print(f"Upload failed: {e.message}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

### 5. Resource Cleanup
When downloading to file objects, ensure proper resource cleanup:

```python
# Using context manager (recommended)
with open("/tmp/output.pdf", "wb") as f:
    bucket.download_fileobj("documents/file.pdf", f)

# File is automatically closed
```

### 6. Key Naming Conventions
Use consistent key naming patterns:

```python
# Good: organized hierarchy
bucket.upload(data, "users/123/profile/avatar.jpg", "image/jpeg")
bucket.upload(data, "documents/2024/Q4/report.pdf", "application/pdf")

# Avoid: flat structure
bucket.upload(data, "avatar.jpg", "image/jpeg")
bucket.upload(data, "report.pdf", "application/pdf")
```

---

## Common Patterns

### Pattern 1: Upload with Existence Check

```python
def upload_if_not_exists(bucket, file_data, key, content_type):
    if not bucket.check_file_exists(key):
        return bucket.upload(file_data, key, content_type)
    else:
        return bucket.url_generator(key)
```

### Pattern 2: Batch Upload

```python
def batch_upload(bucket, files):
    results = []
    for file_path, key in files:
        try:
            url = bucket.upload_by_path(file_path, key)
            results.append({"key": key, "url": url, "success": True})
        except Exception as e:
            results.append({"key": key, "error": str(e), "success": False})
    return results

# Usage
files = [
    ("/tmp/file1.pdf", "documents/file1.pdf"),
    ("/tmp/file2.pdf", "documents/file2.pdf"),
]
results = batch_upload(bucket, files)
```

### Pattern 3: Upload with Fallback

```python
def upload_with_fallback(bucket, file_data, preferred_key, content_type):
    try:
        return bucket.upload(file_data, preferred_key, content_type)
    except Exception:
        # Use safe duplicate logic for fallback
        return bucket.safe_duplicate(preferred_key)
```

---

## Logging

The `Bucket` class integrates with dtpyfw's logging system (`dtpyfw.log.footprint`) and logs all operations at the DEBUG level. Each method call is logged with:
- Controller name (module and method)
- Operation description
- Relevant payload data (keys, paths, etc.)

To enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Troubleshooting

### Issue: NoCredentialsError

**Cause:** Missing or invalid S3 credentials

**Solution:**
```python
# Verify credentials are properly set
bucket = Bucket(
    name="my-bucket",
    endpoint_url="https://storage.example.com",
    access_key="your-access-key",  # Make sure this is set
    secret_key="your-secret-key"   # Make sure this is set
)
```

### Issue: Connection Timeout

**Cause:** Network issues or incorrect endpoint URL

**Solution:**
```python
# Verify endpoint URL is accessible
import requests
response = requests.get("https://storage.example.com")
print(response.status_code)

# Check endpoint format (should include protocol)
bucket = Bucket(
    name="my-bucket",
    endpoint_url="https://storage.example.com"  # Include https://
)
```

### Issue: Access Denied

**Cause:** Insufficient permissions on the bucket

**Solution:** Ensure the access credentials have the necessary permissions:
- `s3:PutObject` for uploads
- `s3:GetObject` for downloads
- `s3:DeleteObject` for deletions
- `s3:ListBucket` for existence checks

---

## Related Modules

- **`dtpyfw.core.exception`**: Contains the `RequestException` class used for error handling
- **`dtpyfw.log.footprint`**: Provides logging functionality used internally by the Bucket class
- **`dtpyfw.core.require_extra`**: Ensures required dependencies are installed

---

## API Reference Summary

| Method | Purpose | Returns |
|--------|---------|---------|
| `__init__()` | Initialize bucket client | `None` |
| `url_generator()` | Generate public URL for object | `str` |
| `get_s3()` | Get boto3 client | `BaseClient` |
| `get_bucket_name()` | Get bucket name | `str \| None` |
| `check_file_exists()` | Check object existence | `bool` |
| `upload()` | Upload bytes to bucket | `str` (URL) |
| `download()` | Download to file path | `bool` |
| `download_fileobj()` | Download to file object | `bool` |
| `upload_by_path()` | Upload from file path | `str` (URL) |
| `duplicate()` | Copy object in bucket | `str` (URL) |
| `safe_duplicate()` | Copy with unique naming | `str` (URL) |
| `delete()` | Delete object | `bool` |

---

## Version Compatibility

This documentation is compatible with dtpyfw bucket module as of October 2024. For the latest updates, refer to the source code at `dtpyfw/bucket/bucket.py`.
