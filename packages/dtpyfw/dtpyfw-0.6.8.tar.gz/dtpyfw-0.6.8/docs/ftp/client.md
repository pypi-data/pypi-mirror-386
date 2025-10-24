# dtpyfw.ftp.client

## Overview

The `client` module provides the `FTPClient` class, a unified interface for both FTP and SFTP file transfer operations. This class abstracts away protocol-specific differences, allowing you to work with remote file systems using a consistent API regardless of whether you're using FTP or SFTP.

## Module Information

- **Module Path**: `dtpyfw.ftp.client`
- **Class**: `FTPClient`
- **Dependencies**:
  - `ftplib` (standard library - FTP support)
  - `paramiko` (SFTP/SSH support)
  - `python-dateutil` (timestamp parsing)
- **Internal Dependencies**: `dtpyfw.core.file_folder`

## FTPClient Class

The `FTPClient` class provides a context manager-based approach to FTP/SFTP operations with automatic connection management and cleanup.

### Class Signature

```python
class FTPClient:
    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: str,
        timeout: int = 20,
        is_sftp: Optional[bool] = None,
    ) -> None:
        ...
```

### Constructor Parameters

| Parameter  | Type             | Required | Default | Description                                                                                      |
|------------|------------------|----------|---------|--------------------------------------------------------------------------------------------------|
| `server`   | `str`            | Yes      | -       | The hostname or IP address of the FTP/SFTP server                                                |
| `port`     | `int`            | Yes      | -       | The port number to connect to (typically 21 for FTP, 22 for SFTP)                               |
| `username` | `str`            | Yes      | -       | The username for authentication                                                                  |
| `password` | `str`            | Yes      | -       | The password for authentication                                                                  |
| `timeout`  | `int`            | No       | `20`    | Connection timeout in seconds                                                                    |
| `is_sftp`  | `Optional[bool]` | No       | `None`  | Protocol selection: `True` for SFTP, `False` for FTP, `None` for auto-detect (port 22 = SFTP)   |

### Instance Attributes

| Attribute  | Type   | Description                                      |
|------------|--------|--------------------------------------------------|
| `server`   | `str`  | The FTP/SFTP server address                      |
| `port`     | `int`  | The server port number                           |
| `username` | `str`  | Authentication username                          |
| `password` | `str`  | Authentication password                          |
| `timeout`  | `int`  | Connection timeout in seconds                    |
| `is_sftp`  | `bool` | `True` for SFTP protocol, `False` for FTP        |

## Methods

### Connection Management

#### `_connect()`

A private context manager method that establishes and manages connections.

```python
@contextmanager
def _connect(self) -> Generator[Union[SFTPClient, FTP], None, None]:
    ...
```

**Description**: Creates either an SFTP or FTP connection based on configuration. The connection is automatically closed when exiting the context.

**Returns**: `Union[SFTPClient, FTP]` - An active connection object

**Raises**:

- `paramiko.SSHException`: If SFTP connection or authentication fails
- `socket.error`: If network connection cannot be established
- `ftplib.error_perm`: If FTP authentication fails

**Note**: This is an internal method and should not be called directly.

---

### File Content Operations

#### `content()`

Retrieve the content and metadata of a remote file.

```python
def content(self, file_path: str) -> Dict[str, Union[str, datetime]]:
    ...
```

**Parameters**:

- `file_path` (`str`): The full path to the file on the remote server

**Returns**: `Dict[str, Union[str, datetime]]` with keys:

- `'name'` (`str`): The base filename without path
- `'last_modified'` (`datetime`): The file's last modification timestamp
- `'content'` (`str`): The file content decoded as UTF-8

**Raises**:

- `IOError`: If the file cannot be read (SFTP)
- `ftplib.error_perm`: If the file cannot be accessed (FTP)
- `UnicodeDecodeError`: If the file content is not valid UTF-8

**Example**:

```python
from dtpyfw.ftp.client import FTPClient

client = FTPClient(
    server="ftp.example.com",
    port=21,
    username="user",
    password="pass"
)

file_data = client.content("/remote/path/config.txt")
print(f"File: {file_data['name']}")
print(f"Modified: {file_data['last_modified']}")
print(f"Content: {file_data['content']}")
```

---

#### `get_last_modified()`

Get the last modification timestamp of a remote file without downloading its content.

```python
def get_last_modified(self, file_path: str) -> Dict[str, Union[str, datetime, None]]:
    ...
```

**Parameters**:

- `file_path` (`str`): The full path to the file on the remote server

**Returns**: `Dict[str, Union[str, datetime, None]]` with keys:

- `'name'` (`str`): The base filename without path
- `'last_modified'` (`datetime` or `None`): The file's last modification timestamp

**Raises**:

- `IOError`: If the file metadata cannot be retrieved (SFTP)
- `ftplib.error_perm`: If the file cannot be accessed (FTP)

**Example**:

```python
metadata = client.get_last_modified("/remote/data.csv")
if metadata['last_modified']:
    print(f"Last modified: {metadata['last_modified']}")
```

---

### Directory Operations

#### `get_folder_list()`

List the contents of a remote directory.

```python
def get_folder_list(self, folder_path: str = "") -> List[str]:
    ...
```

**Parameters**:

- `folder_path` (`str`): The path to the directory. If empty string, lists the current working directory. Defaults to `""`

**Returns**: `List[str]` - A list of filenames and directory names in the specified path

**Raises**:

- `IOError`: If the directory cannot be accessed (SFTP)

**Example**:

```python
# List root directory
files = client.get_folder_list()
print(f"Files in root: {files}")

# List specific directory
files = client.get_folder_list("/remote/uploads")
for file in files:
    print(f"- {file}")
```

---

#### `create_directory()`

Create a directory on the remote server.

```python
def create_directory(self, directory: str) -> bool:
    ...
```

**Parameters**:

- `directory` (`str`): The full path of the directory to create

**Returns**: `bool` - Always returns `True`, whether the directory was created or already existed

**Description**: Creates a new directory at the specified path. If the directory already exists, the operation succeeds silently without raising an error.

**Example**:

```python
# Create a single directory
client.create_directory("/remote/new_folder")

# Create nested directories (may require multiple calls)
client.create_directory("/remote/path")
client.create_directory("/remote/path/to")
client.create_directory("/remote/path/to/folder")
```

---

### File Upload Operations

#### `upload_file()`

Upload a local file to the remote server.

```python
def upload_file(
    self,
    local_path: str,
    file_path: str,
    confirm: bool = True
) -> bool:
    ...
```

**Parameters**:

- `local_path` (`str`): The path to the local file to upload
- `file_path` (`str`): The destination path on the remote server
- `confirm` (`bool`): For SFTP only, whether to perform a stat call after upload to confirm success. Defaults to `True`

**Returns**: `bool` - Always returns `True` upon successful upload

**Raises**:

- `IOError`: If the file cannot be uploaded or confirmed (SFTP)
- `ftplib.error_perm`: If the upload fails due to permissions (FTP)
- `FileNotFoundError`: If the local file does not exist

**Example**:

```python
# Basic upload
client.upload_file(
    local_path="C:/data/report.pdf",
    file_path="/remote/reports/report.pdf"
)

# Upload without confirmation (SFTP only, faster but less safe)
client.upload_file(
    local_path="C:/data/large_file.zip",
    file_path="/remote/uploads/large_file.zip",
    confirm=False
)
```

---

### File Download Operations

#### `download_file()`

Download a remote file to the local filesystem.

```python
def download_file(
    self,
    local_path: str,
    file_path: str,
    make_directory: bool = True,
    remove_file: bool = True,
) -> bool:
    ...
```

**Parameters**:

- `local_path` (`str`): The local path where the downloaded file will be saved
- `file_path` (`str`): The path to the file on the remote server
- `make_directory` (`bool`): If `True`, creates the local directory structure if it doesn't exist. Defaults to `True`
- `remove_file` (`bool`): If `True`, removes the local file before download if it already exists. Defaults to `True`

**Returns**: `bool` - Always returns `True` upon successful download

**Raises**:

- `IOError`: If the file cannot be downloaded (SFTP)
- `ftplib.error_perm`: If the file cannot be accessed (FTP)
- `OSError`: If local directory creation or file removal fails

**Example**:

```python
# Basic download
client.download_file(
    local_path="C:/downloads/data.csv",
    file_path="/remote/exports/data.csv"
)

# Download without creating directories (assumes path exists)
client.download_file(
    local_path="C:/existing/path/file.txt",
    file_path="/remote/file.txt",
    make_directory=False
)

# Download without removing existing file (will fail if file exists)
client.download_file(
    local_path="C:/downloads/archive.zip",
    file_path="/remote/archive.zip",
    remove_file=False
)
```

---

### File Management Operations

#### `delete_file()`

Delete a file from the remote server.

```python
def delete_file(self, file_path: str) -> bool:
    ...
```

**Parameters**:

- `file_path` (`str`): The full path to the file to delete

**Returns**: `bool` - Always returns `True` upon successful deletion

**Raises**:

- `IOError`: If the file cannot be deleted (SFTP)
- `ftplib.error_perm`: If the file cannot be deleted due to permissions or does not exist (FTP)

**Example**:

```python
# Delete a single file
client.delete_file("/remote/temp/old_file.txt")

# Delete multiple files in a loop
files_to_delete = ["/remote/temp/file1.txt", "/remote/temp/file2.txt"]
for file in files_to_delete:
    try:
        client.delete_file(file)
        print(f"Deleted: {file}")
    except (IOError, ftplib.error_perm) as e:
        print(f"Failed to delete {file}: {e}")
```

---

#### `rename_file()`

Rename or move a file on the remote server.

```python
def rename_file(self, old_path: str, new_path: str) -> bool:
    ...
```

**Parameters**:

- `old_path` (`str`): The current path of the file on the remote server
- `new_path` (`str`): The new path for the file on the remote server

**Returns**: `bool` - Always returns `True` upon successful rename/move

**Raises**:

- `IOError`: If the file cannot be renamed (SFTP)
- `ftplib.error_perm`: If the operation fails due to permissions or if the source file does not exist (FTP)

**Example**:

```python
# Rename a file in the same directory
client.rename_file(
    old_path="/remote/data/old_name.txt",
    new_path="/remote/data/new_name.txt"
)

# Move a file to a different directory
client.rename_file(
    old_path="/remote/temp/file.csv",
    new_path="/remote/archive/file.csv"
)
```

---

#### `file_exists()`

Check if a file exists on the remote server.

```python
def file_exists(self, file_path: str) -> bool:
    ...
```

**Parameters**:

- `file_path` (`str`): The full path to the file to check

**Returns**: `bool` - `True` if the file exists, `False` otherwise

**Description**: Verifies the existence of a file without downloading it. For SFTP, uses `stat()`; for FTP, uses `size()`.

**Example**:

```python
# Check before downloading
if client.file_exists("/remote/data/report.pdf"):
    client.download_file("C:/downloads/report.pdf", "/remote/data/report.pdf")
else:
    print("File not found on server")

# Check before uploading to avoid overwriting
if not client.file_exists("/remote/uploads/data.csv"):
    client.upload_file("C:/data/data.csv", "/remote/uploads/data.csv")
else:
    print("File already exists on server")
```

---

## Complete Usage Examples

### Example 1: Basic FTP Upload and Download

```python
from dtpyfw.ftp.client import FTPClient

# Initialize FTP client
client = FTPClient(
    server="ftp.example.com",
    port=21,
    username="myuser",
    password="mypassword",
    timeout=30
)

# Upload a file
try:
    client.upload_file(
        local_path="C:/local/data.csv",
        file_path="/remote/uploads/data.csv"
    )
    print("Upload successful!")
except Exception as e:
    print(f"Upload failed: {e}")

# Download the file back
try:
    client.download_file(
        local_path="C:/downloads/data.csv",
        file_path="/remote/uploads/data.csv"
    )
    print("Download successful!")
except Exception as e:
    print(f"Download failed: {e}")
```

### Example 2: SFTP with Directory Management

```python
from dtpyfw.ftp.client import FTPClient

# Initialize SFTP client (port 22 auto-detects SFTP)
client = FTPClient(
    server="sftp.example.com",
    port=22,
    username="myuser",
    password="mypassword"
)

# Create directory structure
client.create_directory("/remote/archives")
client.create_directory("/remote/archives/2024")

# List files in a directory
files = client.get_folder_list("/remote/uploads")
print(f"Found {len(files)} files")

for file in files:
    print(f"Processing: {file}")

    # Check file metadata
    metadata = client.get_last_modified(f"/remote/uploads/{file}")
    print(f"  Last modified: {metadata['last_modified']}")

    # Move to archives
    client.rename_file(
        old_path=f"/remote/uploads/{file}",
        new_path=f"/remote/archives/2024/{file}"
    )
```

### Example 3: Conditional File Operations

```python
from dtpyfw.ftp.client import FTPClient
from datetime import datetime, timedelta

client = FTPClient(
    server="ftp.example.com",
    port=21,
    username="user",
    password="pass"
)

remote_file = "/remote/data/daily_report.csv"

# Check if file exists before processing
if client.file_exists(remote_file):
    # Get file metadata
    metadata = client.get_last_modified(remote_file)
    last_modified = metadata['last_modified']

    # Only download if file is recent (within last 24 hours)
    if datetime.now() - last_modified < timedelta(days=1):
        print("File is recent, downloading...")
        client.download_file("C:/reports/latest.csv", remote_file)
    else:
        print("File is outdated")
else:
    print("File does not exist on server")
```

### Example 4: Batch File Transfer

```python
import os
from dtpyfw.ftp.client import FTPClient

client = FTPClient(
    server="sftp.example.com",
    port=22,
    username="user",
    password="pass"
)

# Upload multiple files
local_dir = "C:/data/exports"
remote_dir = "/remote/imports"

# Ensure remote directory exists
client.create_directory(remote_dir)

for filename in os.listdir(local_dir):
    if filename.endswith('.csv'):
        local_path = os.path.join(local_dir, filename)
        remote_path = f"{remote_dir}/{filename}"

        try:
            print(f"Uploading {filename}...")
            client.upload_file(local_path, remote_path)
            print(f"  ✓ Success")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
```

### Example 5: File Content Processing

```python
from dtpyfw.ftp.client import FTPClient
import csv
from io import StringIO

client = FTPClient(
    server="ftp.example.com",
    port=21,
    username="user",
    password="pass"
)

# Read and process file content directly
remote_csv = "/remote/data/users.csv"
file_data = client.content(remote_csv)

# Parse CSV content
csv_content = StringIO(file_data['content'])
reader = csv.DictReader(csv_content)

for row in reader:
    print(f"User: {row['name']}, Email: {row['email']}")

print(f"\nFile last modified: {file_data['last_modified']}")
```

### Example 6: Explicit Protocol Selection

```python
from dtpyfw.ftp.client import FTPClient

# Force FTP even on port 22
ftp_client = FTPClient(
    server="example.com",
    port=22,
    username="user",
    password="pass",
    is_sftp=False  # Explicitly use FTP
)

# Force SFTP on non-standard port
sftp_client = FTPClient(
    server="example.com",
    port=2222,
    username="user",
    password="pass",
    is_sftp=True  # Explicitly use SFTP
)
```

### Example 7: Error Handling

```python
from dtpyfw.ftp.client import FTPClient
from ftplib import error_perm
from paramiko import SSHException
import socket

client = FTPClient(
    server="ftp.example.com",
    port=21,
    username="user",
    password="pass"
)

try:
    client.upload_file("local.txt", "/remote/file.txt")
except FileNotFoundError:
    print("Local file does not exist")
except (error_perm, IOError) as e:
    print(f"Permission denied or file error: {e}")
except (SSHException, socket.error) as e:
    print(f"Connection error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Protocol Differences

While `FTPClient` provides a unified interface, there are subtle differences between FTP and SFTP:

| Feature                  | FTP                          | SFTP                         |
|--------------------------|------------------------------|------------------------------|
| Encryption               | None (plaintext)             | SSH encryption               |
| Default Port             | 21                           | 22                           |
| Authentication           | Username/password            | Username/password or SSH key |
| Upload Confirmation      | Not applicable               | Optional via `confirm` param |
| File Existence Check     | Uses `SIZE` command          | Uses `stat()` call           |
| Directory Listing        | `NLST` command               | `listdir()` method           |

## Best Practices

### 1. Always Use Context Managers Internally

The `_connect()` method uses context managers to ensure connections are properly closed. The public methods handle this automatically.

### 2. Handle Exceptions Appropriately

```python
from ftplib import error_perm
from paramiko import SSHException

try:
    client.upload_file("local.txt", "/remote/file.txt")
except FileNotFoundError:
    # Handle missing local file
    pass
except (error_perm, IOError):
    # Handle FTP/SFTP errors
    pass
except SSHException:
    # Handle SFTP connection errors
    pass
```

### 3. Use SFTP for Sensitive Data

```python
# Good: Using encrypted SFTP for sensitive data
client = FTPClient(
    server="secure.example.com",
    port=22,
    username="user",
    password="pass"
)
```

### 4. Check File Existence Before Operations

```python
if client.file_exists("/remote/file.txt"):
    client.download_file("local.txt", "/remote/file.txt")
```

### 5. Create Directories Before Uploads

```python
client.create_directory("/remote/uploads/2024")
client.upload_file("data.csv", "/remote/uploads/2024/data.csv")
```

### 6. Use Appropriate Timeouts

```python
# For slow connections or large files
client = FTPClient(
    server="ftp.example.com",
    port=21,
    username="user",
    password="pass",
    timeout=120  # 2 minutes
)
```

### 7. Clean Up Remote Files

```python
# After processing, clean up
client.download_file("local.csv", "/remote/processed/data.csv")
client.delete_file("/remote/processed/data.csv")
```

## Performance Considerations

### Upload Confirmation

For SFTP uploads, the `confirm` parameter controls whether to verify the upload:

```python
# Slower but safer (default)
client.upload_file("large_file.zip", "/remote/large_file.zip", confirm=True)

# Faster but no verification
client.upload_file("large_file.zip", "/remote/large_file.zip", confirm=False)
```

### Connection Reuse

Each method call creates a new connection. For bulk operations, consider batching operations where possible, though the current design doesn't expose persistent connections directly.

### Timeout Configuration

Adjust timeouts based on network conditions and file sizes:

```python
# Fast local network
client = FTPClient(..., timeout=10)

# Slow internet connection
client = FTPClient(..., timeout=60)
```

## Security Considerations

### 1. Credential Management

Never hardcode credentials:

```python
import os

# Good: Use environment variables
client = FTPClient(
    server=os.getenv("FTP_SERVER"),
    port=int(os.getenv("FTP_PORT", "21")),
    username=os.getenv("FTP_USERNAME"),
    password=os.getenv("FTP_PASSWORD")
)
```

### 2. Use SFTP When Possible

FTP transmits credentials and data in plaintext. Use SFTP for secure transfers:

```python
# Insecure: FTP
ftp_client = FTPClient(server="example.com", port=21, ...)

# Secure: SFTP
sftp_client = FTPClient(server="example.com", port=22, ...)
```

### 3. Host Key Verification

The module uses `paramiko.AutoAddPolicy()` which accepts any host key. For production, consider implementing stricter host key verification.

## Troubleshooting

### Connection Timeout

```python
# Increase timeout for slow connections
client = FTPClient(..., timeout=60)
```

### Authentication Failed

- Verify username and password
- Check if the account has necessary permissions
- For SFTP, verify SSH is enabled on the server

### File Not Found

```python
# Always check existence first
if client.file_exists("/remote/file.txt"):
    client.download_file("local.txt", "/remote/file.txt")
else:
    print("File not found")
```

### Permission Denied

- Verify user has read/write permissions on the remote directory
- Check that the remote path exists
- For uploads, ensure the remote directory exists

### Unicode Decode Errors

The `content()` method assumes UTF-8 encoding. For binary files or different encodings, use `download_file()` instead.

## Related Documentation

- [FTP Module Overview](__init__.md) - Overview of the FTP module
- [dtpyfw.core.file_folder](../core/file_folder.md) - Local file system utilities

## External References

- [Python ftplib Documentation](https://docs.python.org/3/library/ftplib.html)
- [Paramiko Documentation](https://docs.paramiko.org/)
- [RFC 959 - FTP Protocol](https://tools.ietf.org/html/rfc959)
- [SSH File Transfer Protocol (SFTP)](https://tools.ietf.org/html/draft-ietf-secsh-filexfer-02)
