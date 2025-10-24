# File and Folder Utilities

## Overview

The `dtpyfw.core.file_folder` module provides simple helper functions for common file system operations. These utilities simplify directory creation, file removal, and path manipulation tasks.

## Module Path

```python
from dtpyfw.core.file_folder import make_directory, folder_path_of_file, remove_file
```

## Functions

### `make_directory(path: str) -> None`

Create a directory if it does not already exist.

**Description:**

Creates the directory specified by path, including any necessary parent directories (similar to `mkdir -p`). If the directory already exists, no action is taken and no error is raised.

**Parameters:**

- **path** (`str`): The directory path to create.

**Returns:**

- `None`

**Example:**

```python
from dtpyfw.core.file_folder import make_directory

# Create a single directory
make_directory("/app/data")

# Create nested directories
make_directory("/app/data/uploads/images")

# Safe to call multiple times
make_directory("/app/data")  # No error if it exists
```

---

### `folder_path_of_file(path: str) -> str`

Return the directory portion of a file path.

**Description:**

Extracts and returns the directory component from a file path, resolving it to an absolute path. This is useful for getting the containing folder of a file.

**Parameters:**

- **path** (`str`): The file path to extract the directory from.

**Returns:**

- **`str`**: The absolute directory path containing the file.

**Example:**

```python
from dtpyfw.core.file_folder import folder_path_of_file

# Get directory of a file
file_path = "/app/data/uploads/image.jpg"
directory = folder_path_of_file(file_path)
print(directory)  # Output: /app/data/uploads

# Works with relative paths
relative_file = "data/file.txt"
directory = folder_path_of_file(relative_file)
print(directory)  # Output: /full/path/to/data
```

---

### `remove_file(path: str) -> None`

Delete a file if it exists.

**Description:**

Removes the file at the specified path. If the file does not exist, no action is taken and no error is raised. This is a safe deletion function that won't fail on missing files.

**Parameters:**

- **path** (`str`): The file path to remove.

**Returns:**

- `None`

**Example:**

```python
from dtpyfw.core.file_folder import remove_file

# Remove a file
remove_file("/app/data/temp.txt")

# Safe to call on non-existent files
remove_file("/app/data/nonexistent.txt")  # No error
```

## Complete Usage Examples

### 1. File Upload Handler

```python
from dtpyfw.core.file_folder import make_directory, remove_file
import os

class FileUploadHandler:
    def __init__(self, upload_dir: str = "/app/uploads"):
        self.upload_dir = upload_dir
        # Ensure upload directory exists
        make_directory(self.upload_dir)
    
    def save_file(self, filename: str, content: bytes) -> str:
        """Save uploaded file to disk."""
        filepath = os.path.join(self.upload_dir, filename)
        
        # Create subdirectory if needed
        folder = folder_path_of_file(filepath)
        make_directory(folder)
        
        # Write file
        with open(filepath, 'wb') as f:
            f.write(content)
        
        return filepath
    
    def delete_file(self, filename: str) -> None:
        """Delete an uploaded file."""
        filepath = os.path.join(self.upload_dir, filename)
        remove_file(filepath)

# Usage
handler = FileUploadHandler()
filepath = handler.save_file("document.pdf", pdf_bytes)
handler.delete_file("old_document.pdf")
```

### 2. Log File Management

```python
from dtpyfw.core.file_folder import make_directory, remove_file
from datetime import datetime, timedelta
import os

class LogManager:
    def __init__(self, log_dir: str = "/var/log/myapp"):
        self.log_dir = log_dir
        make_directory(self.log_dir)
    
    def get_log_file_path(self, date: datetime = None) -> str:
        """Get path for log file of a specific date."""
        if date is None:
            date = datetime.now()
        
        # Organize logs by year/month
        year_month_dir = os.path.join(
            self.log_dir,
            date.strftime("%Y"),
            date.strftime("%m")
        )
        make_directory(year_month_dir)
        
        filename = f"app-{date.strftime('%Y-%m-%d')}.log"
        return os.path.join(year_month_dir, filename)
    
    def cleanup_old_logs(self, days: int = 30):
        """Remove log files older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for root, dirs, files in os.walk(self.log_dir):
            for file in files:
                if file.endswith('.log'):
                    filepath = os.path.join(root, file)
                    file_date = datetime.fromtimestamp(
                        os.path.getctime(filepath)
                    )
                    if file_date < cutoff_date:
                        remove_file(filepath)

# Usage
log_manager = LogManager()
log_file = log_manager.get_log_file_path()
log_manager.cleanup_old_logs(days=30)
```

### 3. Temporary File Handler

```python
from dtpyfw.core.file_folder import make_directory, remove_file, folder_path_of_file
import os
import tempfile

class TempFileManager:
    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), "myapp")
        make_directory(self.temp_dir)
        self.temp_files = []
    
    def create_temp_file(self, prefix: str = "temp") -> str:
        """Create a temporary file and track it."""
        filepath = os.path.join(self.temp_dir, f"{prefix}_{os.getpid()}.tmp")
        self.temp_files.append(filepath)
        return filepath
    
    def cleanup(self):
        """Remove all tracked temporary files."""
        for filepath in self.temp_files:
            remove_file(filepath)
        self.temp_files = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

# Usage with context manager
with TempFileManager() as temp_mgr:
    temp_file = temp_mgr.create_temp_file("processing")
    # Do work with temp_file
    pass
# Files automatically cleaned up
```

### 4. Asset Organization

```python
from dtpyfw.core.file_folder import make_directory, folder_path_of_file
import shutil
import os

class AssetOrganizer:
    def __init__(self, base_dir: str = "/app/assets"):
        self.base_dir = base_dir
        make_directory(self.base_dir)
    
    def organize_by_type(self, filepath: str) -> str:
        """Move file to appropriate subdirectory based on extension."""
        filename = os.path.basename(filepath)
        extension = os.path.splitext(filename)[1].lower()
        
        # Determine subdirectory based on extension
        type_mapping = {
            '.jpg': 'images', '.jpeg': 'images', '.png': 'images', '.gif': 'images',
            '.pdf': 'documents', '.doc': 'documents', '.docx': 'documents',
            '.mp4': 'videos', '.avi': 'videos', '.mov': 'videos',
            '.mp3': 'audio', '.wav': 'audio', '.flac': 'audio'
        }
        
        subdir = type_mapping.get(extension, 'other')
        dest_dir = os.path.join(self.base_dir, subdir)
        
        # Create subdirectory if needed
        make_directory(dest_dir)
        
        # Move file
        dest_path = os.path.join(dest_dir, filename)
        shutil.move(filepath, dest_path)
        
        return dest_path

# Usage
organizer = AssetOrganizer()
new_path = organizer.organize_by_type("/tmp/download.pdf")
print(new_path)  # /app/assets/documents/download.pdf
```

### 5. Data Export System

```python
from dtpyfw.core.file_folder import make_directory, remove_file
from datetime import datetime
import json
import csv

class DataExporter:
    def __init__(self, export_dir: str = "/app/exports"):
        self.export_dir = export_dir
        make_directory(self.export_dir)
    
    def export_to_json(self, data: list, filename: str = None) -> str:
        """Export data to JSON file."""
        if filename is None:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.export_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def export_to_csv(self, data: list, filename: str = None) -> str:
        """Export data to CSV file."""
        if filename is None:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = os.path.join(self.export_dir, filename)
        
        if data:
            keys = data[0].keys()
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
        
        return filepath
    
    def cleanup_exports(self, keep_latest: int = 10):
        """Keep only the most recent export files."""
        files = []
        for filename in os.listdir(self.export_dir):
            filepath = os.path.join(self.export_dir, filename)
            if os.path.isfile(filepath):
                files.append((filepath, os.path.getctime(filepath)))
        
        # Sort by creation time, newest first
        files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old files
        for filepath, _ in files[keep_latest:]:
            remove_file(filepath)

# Usage
exporter = DataExporter()
json_file = exporter.export_to_json(data)
csv_file = exporter.export_to_csv(data)
exporter.cleanup_exports(keep_latest=5)
```

### 6. Backup System

```python
from dtpyfw.core.file_folder import make_directory, remove_file
import shutil
from datetime import datetime

class BackupManager:
    def __init__(self, source_dir: str, backup_dir: str):
        self.source_dir = source_dir
        self.backup_dir = backup_dir
        make_directory(self.backup_dir)
    
    def create_backup(self) -> str:
        """Create a timestamped backup of source directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # Create backup
        shutil.copytree(self.source_dir, backup_path)
        
        return backup_path
    
    def restore_backup(self, backup_name: str):
        """Restore from a specific backup."""
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if os.path.exists(backup_path):
            # Clear source directory
            if os.path.exists(self.source_dir):
                shutil.rmtree(self.source_dir)
            
            # Restore backup
            shutil.copytree(backup_path, self.source_dir)
        else:
            raise FileNotFoundError(f"Backup not found: {backup_name}")
    
    def list_backups(self) -> list:
        """List all available backups."""
        backups = []
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            if os.path.isdir(item_path):
                backups.append({
                    'name': item,
                    'created': datetime.fromtimestamp(os.path.getctime(item_path)),
                    'size': self._get_dir_size(item_path)
                })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def _get_dir_size(self, directory: str) -> int:
        """Calculate total size of directory."""
        total = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total += os.path.getsize(filepath)
        return total

# Usage
backup_mgr = BackupManager(
    source_dir="/app/data",
    backup_dir="/app/backups"
)
backup_path = backup_mgr.create_backup()
backups = backup_mgr.list_backups()
```

## Best Practices

1. **Always use absolute paths when possible:**
   ```python
   import os
   from dtpyfw.core.file_folder import make_directory
   
   # Good
   absolute_path = os.path.abspath("/app/data")
   make_directory(absolute_path)
   
   # Less reliable
   make_directory("data")  # Depends on current working directory
   ```

2. **Handle permissions gracefully:**
   ```python
   from dtpyfw.core.file_folder import make_directory
   
   try:
       make_directory("/restricted/path")
   except PermissionError:
       print("Insufficient permissions to create directory")
   ```

3. **Clean up temporary files:**
   ```python
   from dtpyfw.core.file_folder import remove_file
   
   temp_file = "/tmp/processing.dat"
   try:
       # Do work with temp_file
       pass
   finally:
       remove_file(temp_file)  # Always cleanup
   ```

4. **Validate paths before operations:**
   ```python
   import os
   from dtpyfw.core.file_folder import remove_file
   
   def safe_remove(filepath: str):
       # Prevent directory traversal
       normalized = os.path.normpath(filepath)
       if normalized.startswith("/app/data"):
           remove_file(normalized)
       else:
           raise ValueError("Invalid file path")
   ```

## Platform Compatibility

These functions work across Windows, Linux, and macOS:

```python
from dtpyfw.core.file_folder import make_directory
import os

# Cross-platform path construction
data_dir = os.path.join("app", "data", "uploads")
make_directory(data_dir)

# Works on Windows: app\data\uploads
# Works on Linux/Mac: app/data/uploads
```

## Related Modules

- **dtpyfw.core.env** - For configuring directory paths from environment variables
- **dtpyfw.bucket** - For S3-compatible storage operations
- **dtpyfw.log** - For logging file operations

## Dependencies

- `os` - Python's built-in os module

## See Also

- [Python os module](https://docs.python.org/3/library/os.html)
- [pathlib for modern path handling](https://docs.python.org/3/library/pathlib.html)
- [shutil for higher-level file operations](https://docs.python.org/3/library/shutil.html)
