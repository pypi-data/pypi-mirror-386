# dtpyfw - Quick Reference for AI Developers

> **Purpose**: This is a quick reference guide for AI coding assistants. For detailed documentation, always refer to:
>
> - **Module Docstrings**: Use Python's `help()` function or IDE inspection
> - **Documentation Files**: `docs/` folder with detailed guides for each module
> - **README.md**: Installation instructions, feature overview, and examples
> - **Source Code**: All code has complete type hints and docstrings

> **📍 After Installation**: This file and all docs are in your site-packages:
>
> ```python
> import dtpyfw, os
> docs_path = os.path.dirname(os.path.dirname(dtpyfw.__file__))
> print(f"Docs: {docs_path}/docs/")
> print(f"Guide: {docs_path}/how-to-use.md")
> ```

---

## 📦 Installation

**Requirements**: Python 3.11 or newer (3.11.9+ recommended)

```bash
# Base (core + logging)
pip install dtpyfw

# With specific features
pip install dtpyfw[api,db,redis]

# Everything
pip install dtpyfw[all]
```

**Available extras**: `api`, `db`, `db-mysql`, `bucket`, `redis`, `redis_streamer`, `kafka`, `worker`, `ftp`, `encrypt`

---

## 🧭 Decision Guide: Which Module Should I Use?

Quick reference to find the right dtpyfw module for your task, organized by category:

### Web & API Development

| I need to... | Use this dtpyfw module | Install | Underlying |
|--------------|------------------------|---------|------------|
| Build REST APIs with routing | `from dtpyfw.api import Application` | `[api]` | FastAPI |
| Add middleware (CORS, timing, errors) | `from dtpyfw.api.middlewares import ...` | `[api]` | FastAPI |
| Define API schemas & validation | `from dtpyfw.api.schemas import ...` | `[api]` | Pydantic |
| Create API routes & endpoints | `from fastapi import APIRouter` (with Application) | `[api]` | FastAPI |

### Data Storage & Databases

| I need to... | Use this dtpyfw module | Install | Underlying |
|--------------|------------------------|---------|------------|
| Connect to PostgreSQL/MySQL | `from dtpyfw.db import DatabaseConfig, DatabaseInstance` | `[db]` or `[db-mysql]` | SQLAlchemy |
| Define database models | Use `db.Base` from DatabaseInstance | `[db]` | SQLAlchemy |
| Build queries with filters | `from dtpyfw.db.search import apply_filters, apply_search` | `[db]` | SQLAlchemy |
| Check database health | `db.health_check()` or `from dtpyfw.db.health import ...` | `[db]` | SQLAlchemy |
| Store files in S3/MinIO | `from dtpyfw.bucket import Bucket` | `[bucket]` | boto3 |
| Transfer files via FTP/SFTP | `from dtpyfw.ftp import FTPClient` | `[ftp]` | paramiko |

### Caching & Messaging

| I need to... | Use this dtpyfw module | Install | Underlying |
|--------------|------------------------|---------|------------|
| Cache data in Redis | `from dtpyfw.redis import RedisInstance, cache_result` | `[redis]` | redis-py |
| Use Redis Streams (producer) | `from dtpyfw.redis_streamer.synchronize import SyncProducer` | `[redis_streamer]` | redis-py |
| Use Redis Streams (consumer) | `from dtpyfw.redis_streamer.synchronize import SyncConsumer` | `[redis_streamer]` | redis-py |
| Async Redis Streams | `from dtpyfw.redis_streamer.asynchronize import AsyncProducer, AsyncConsumer` | `[redis_streamer]` | redis-py |
| Send Kafka messages | `from dtpyfw.kafka import KafkaProducerInstance` | `[kafka]` | kafka-python |
| Consume Kafka messages | `from dtpyfw.kafka import KafkaConsumerInstance` | `[kafka]` | kafka-python |

### Background Tasks & Workers

| I need to... | Use this dtpyfw module | Install | Underlying |
|--------------|------------------------|---------|------------|
| Run background tasks | `from dtpyfw.worker import CeleryWorker` | `[worker]` | Celery |
| Register Celery tasks | `from dtpyfw.worker import register_task` | `[worker]` | Celery |
| Schedule periodic tasks | Configure with CeleryWorker (celery-redbeat) | `[worker]` | Celery Beat |

### Security & Encryption

| I need to... | Use this dtpyfw module | Install | Underlying |
|--------------|------------------------|---------|------------|
| Hash passwords (bcrypt/argon2) | `from dtpyfw.encrypt.hashing import hash_password, verify_password` | `[encrypt]` | passlib |
| Create/verify JWT tokens | `from dtpyfw.encrypt.encryption import jwt_encode, jwt_decode` | `[encrypt]` | python-jose |

### Logging & Monitoring

| I need to... | Use this dtpyfw module | Install | Underlying |
|--------------|------------------------|---------|------------|
| Structured logging | `from dtpyfw.log import footprint` then `footprint.leave()` | *(base)* | logging |
| Configure log handlers | `from dtpyfw.log.config import LogConfig` | *(base)* | logging |
| Initialize logging system | `from dtpyfw.log.initializer import initialize_logging` | *(base)* | logging |
| API request/response logging | `from dtpyfw.log.api_handler import ...` | `[api]` | logging |

### Core Utilities (Always Available)

| I need to... | Use this dtpyfw module | Install | Notes |
|--------------|------------------------|---------|-------|
| Access environment variables | `from dtpyfw.core.env import Env` | *(base)* | Type-safe env access |
| Run async code from sync | `from dtpyfw.core.async import run_async` | *(base)* | Async bridge |
| Validate emails/phones/URLs | `from dtpyfw.core.validation import validate_email, validate_phone, validate_url` | *(base)* | Common validators |
| Retry with exponential backoff | `from dtpyfw.core.retry import retry` | *(base)* | Decorator |
| Hash data structures | `from dtpyfw.core.hashing import generate_hash` | *(base)* | Consistent hashing |
| Split data into chunks | `from dtpyfw.core.chunking import chunk_list, chunk_file` | *(base)* | Batch processing |
| Handle exceptions | `from dtpyfw.core.exception import exception_to_dict` | *(base)* | Structured errors |
| Singleton pattern | `from dtpyfw.core.singleton import singleton` | *(base)* | Decorator |
| Safe nested data access | `from dtpyfw.core.safe_access import safe_get` | *(base)* | No KeyError |
| Generate URL-safe slugs | `from dtpyfw.core.slug import slugify` | *(base)* | String utils |
| Parse/validate URLs | `from dtpyfw.core.url import parse_url` | *(base)* | URL utils |
| File/folder operations | `from dtpyfw.core.file_folder import ...` | *(base)* | File system |
| JSON serialization | `from dtpyfw.core.jsonable_encoder import jsonable_encoder` | *(base)* | Complex objects |
| HTTP request helpers | `from dtpyfw.core.request import ...` | *(base)* | Request utils |

> **⚠️ Important**: Always prefer dtpyfw wrappers over direct package imports. The framework provides:
>
> - Consistent configuration patterns (builder pattern with `.set_*()` methods)
> - Built-in logging integration (all operations logged via `footprint`)
> - Error handling and monitoring (structured exception handling)
> - Type safety and validation (complete type hints and runtime validation)
> - Connection pooling and resource management (automatic cleanup)

---

## 📚 Module Overview

### 🔧 Core (`dtpyfw.core`) - Always Available

Foundational utilities used across all modules.

| Module | Import | Purpose |
|--------|--------|---------|
| `env` | `from dtpyfw.core.env import Env` | Environment variable access with type safety |
| `async` | `from dtpyfw.core.async import run_async` | Execute async functions from sync context |
| `validation` | `from dtpyfw.core.validation import validate_email, validate_phone` | Common data validation utilities |
| `retry` | `from dtpyfw.core.retry import retry` | Decorator for automatic retry with backoff |
| `hashing` | `from dtpyfw.core.hashing import generate_hash` | Consistent hash generation |
| `chunking` | `from dtpyfw.core.chunking import chunk_list` | Split large datasets into chunks |
| `exception` | `from dtpyfw.core.exception import exception_to_dict` | Structured exception handling |
| `singleton` | `from dtpyfw.core.singleton import singleton` | Singleton pattern decorator |
| `safe_access` | `from dtpyfw.core.safe_access import safe_get` | Safe nested data access |
| `slug` | `from dtpyfw.core.slug import slugify` | URL-safe slug generation |
| `url` | `from dtpyfw.core.url import parse_url` | URL parsing utilities |
| `file_folder` | `from dtpyfw.core.file_folder import ...` | File system operations |
| `jsonable_encoder` | `from dtpyfw.core.jsonable_encoder import jsonable_encoder` | Serialize complex objects to JSON |
| `request` | `from dtpyfw.core.request import ...` | HTTP request helpers |

**📖 Docs**: `docs/core/` - See individual files for each utility

---

### 📝 Logging (`dtpyfw.log`) - Always Available

Structured logging system with context-aware output.

| Component | Import | Purpose |
|-----------|--------|---------|
| `footprint` | `from dtpyfw.log import footprint` | Main logger - use `footprint.leave()` |
| `config` | `from dtpyfw.log.config import LogConfig` | Configure logging handlers |
| `initializer` | `from dtpyfw.log.initializer import initialize_logging` | Initialize logging system |

**Usage**: `footprint.leave(level="INFO", message="...", **context)`

**📖 Docs**: `docs/log/footprint.md`

---

### 🚀 API (`dtpyfw.api`) - `pip install dtpyfw[api]`

FastAPI application wrapper with middleware and routing.

| Component | Import | Purpose |
|-----------|--------|---------|
| `Application` | `from dtpyfw.api import Application` | FastAPI app wrapper with auto-config |
| Middlewares | `from dtpyfw.api.middlewares import ...` | Request timing, CORS, error handling |
| Schemas | `from dtpyfw.api.schemas import ...` | Pydantic models for common patterns |

**📖 Docs**: `docs/api/application.md`, `docs/api/middlewares/`, `docs/api/schemas/`

---

### 🗄️ Database (`dtpyfw.db`) - `pip install dtpyfw[db]`

SQLAlchemy orchestration with sync/async support.

| Component | Import | Purpose |
|-----------|--------|---------|
| `DatabaseConfig` | `from dtpyfw.db import DatabaseConfig` | Builder pattern for DB configuration |
| `DatabaseInstance` | `from dtpyfw.db import DatabaseInstance` | Engine and session management |
| `BaseModel` | `from dtpyfw.db.model import BaseModel` | Base model with timestamps |
| `BaseSchema` | `from dtpyfw.db.schema import BaseSchema` | Pydantic base schema |
| Search Utils | `from dtpyfw.db.search import apply_filters, apply_search` | Query building utilities |

**📖 Docs**: `docs/db/database.md`, `docs/db/config.md`, `docs/db/model.md`

---

### 🔴 Redis (`dtpyfw.redis`) - `pip install dtpyfw[redis]`

Redis client with connection pooling and caching.

| Component | Import | Purpose |
|-----------|--------|---------|
| `RedisConfig` | `from dtpyfw.redis import RedisConfig` | Redis connection configuration |
| `RedisInstance` | `from dtpyfw.redis import RedisInstance` | Connection pool management |
| `cache_result` | `from dtpyfw.redis.caching import cache_result` | Function memoization decorator |
| Health Check | `from dtpyfw.redis.health import redis_health_check` | Verify Redis connectivity |

**📖 Docs**: `docs/redis/connection.md`, `docs/redis/caching.md`

---

### 🌊 Redis Streams (`dtpyfw.redis_streamer`) - `pip install dtpyfw[redis_streamer]`

Producer/consumer for Redis Streams event messaging.

| Component | Import | Purpose |
|-----------|--------|---------|
| Sync Producer | `from dtpyfw.redis_streamer.synchronize import SyncProducer` | Publish messages (sync) |
| Sync Consumer | `from dtpyfw.redis_streamer.synchronize import SyncConsumer` | Consume messages (sync) |
| Async Producer | `from dtpyfw.redis_streamer.asynchronize import AsyncProducer` | Publish messages (async) |
| Async Consumer | `from dtpyfw.redis_streamer.asynchronize import AsyncConsumer` | Consume messages (async) |

**📖 Docs**: `docs/redis_streamer/synchronize.md`, `docs/redis_streamer/asynchronize.md`

---

### 📦 S3 Bucket (`dtpyfw.bucket`) - `pip install dtpyfw[bucket]`

S3-compatible object storage (AWS S3, MinIO).

| Component | Import | Purpose |
|-----------|--------|---------|
| `Bucket` | `from dtpyfw.bucket import Bucket` | S3 client for upload/download/delete |

**Methods**: `upload_file()`, `download_file()`, `delete_object()`, `list_objects()`, `get_url()`

**📖 Docs**: `docs/bucket/bucket.md`

---

### 📨 Kafka (`dtpyfw.kafka`) - `pip install dtpyfw[kafka]`

Kafka messaging with producer/consumer wrappers.

| Component | Import | Purpose |
|-----------|--------|---------|
| `KafkaConfig` | `from dtpyfw.kafka import KafkaConfig` | Kafka connection configuration |
| `KafkaProducerInstance` | `from dtpyfw.kafka import KafkaProducerInstance` | Send messages to topics |
| `KafkaConsumerInstance` | `from dtpyfw.kafka import KafkaConsumerInstance` | Consume messages from topics |

**📖 Docs**: `docs/kafka/producer.md`, `docs/kafka/consumer.md`

---

### ⚙️ Worker (`dtpyfw.worker`) - `pip install dtpyfw[worker]`

Celery task management and worker configuration.

| Component | Import | Purpose |
|-----------|--------|---------|
| `CeleryWorker` | `from dtpyfw.worker import CeleryWorker` | Celery app wrapper |
| `register_task` | `from dtpyfw.worker import register_task` | Decorator to register tasks |

**📖 Docs**: `docs/worker/worker.md`, `docs/worker/task.md`

---

### 📂 FTP (`dtpyfw.ftp`) - `pip install dtpyfw[ftp]`

Unified FTP/SFTP client interface.

| Component | Import | Purpose |
|-----------|--------|---------|
| `FTPClient` | `from dtpyfw.ftp import FTPClient` | FTP/SFTP operations |

**Methods**: `upload()`, `download()`, `list_directory()`, `delete_file()`, `create_directory()`

**📖 Docs**: `docs/ftp/client.md`

---

### 🔐 Encryption (`dtpyfw.encrypt`) - `pip install dtpyfw[encrypt]`

JWT tokens and password hashing utilities.

| Component | Import | Purpose |
|-----------|--------|---------|
| JWT | `from dtpyfw.encrypt.encryption import jwt_encode, jwt_decode` | JWT token operations |
| Password | `from dtpyfw.encrypt.hashing import hash_password, verify_password` | Secure password hashing |

**📖 Docs**: `docs/encrypt/encryption.md`, `docs/encrypt/hashing.md`

---

## 🎯 How to Use This Guide

### 1. Find the Module You Need

Look at the table above to identify which module provides the functionality you need.

### 2. Check Installation Requirements

Note the install command (e.g., `pip install dtpyfw[redis]`) if the module requires an extra.

### 3. Read the Detailed Documentation

```python
# Access docstrings directly
from dtpyfw.db import DatabaseConfig
help(DatabaseConfig)  # Complete documentation

# Or read the markdown docs
# Located at: {site-packages}/docs/db/config.md
```

### 4. Inspect Type Hints

All modules have complete type annotations:

```python
from dtpyfw.redis import RedisInstance
# Your IDE will show all methods, parameters, and return types
```

### 5. Follow Examples in README.md

The main README has practical examples for common use cases.

---

## 🔍 Finding More Information

```python
# List all available modules
import dtpyfw
print(dir(dtpyfw))

# Get module documentation
from dtpyfw.db import DatabaseInstance
help(DatabaseInstance)

# Find documentation files
import dtpyfw, os, glob
docs_path = os.path.join(os.path.dirname(os.path.dirname(dtpyfw.__file__)), 'docs')
for doc in glob.glob(f"{docs_path}/**/*.md", recursive=True):
    print(doc)
```

---

## 📋 Best Practices for AI Assistants

### ✅ DO

- **Read docstrings** using `help()` or IDE inspection for detailed usage
- **Check type hints** for parameter and return types
- **Reference docs/** folder for comprehensive guides
- **Use builder patterns** for configuration (chain `.set_*()` methods)
- **Use `footprint.leave()`** for all logging (not `print()`)
- **Use context managers** for database sessions and connections
- **Handle exceptions** with structured error logging
- **Prefer dtpyfw wrappers** over direct package imports (FastAPI, SQLAlchemy, Celery, etc.)

### ❌ DON'T

- Hardcode credentials (use `Env.get()` for environment variables)
- Use `print()` for logging (use `footprint.leave()`)
- Create connections without pooling (use provided instances)
- Ignore type hints (all functions are fully typed)
- **Import raw packages directly** when dtpyfw provides a wrapper

#### Common Import Mistakes to Avoid

| ❌ Don't Do This | ✅ Do This Instead | Module |
|------------------|-------------------|--------|
| `from fastapi import FastAPI` | `from dtpyfw.api import Application` | API |
| `from sqlalchemy import create_engine` | `from dtpyfw.db import DatabaseInstance` | Database |
| `from celery import Celery` | `from dtpyfw.worker import CeleryWorker` | Worker |
| `import redis; redis.Redis()` | `from dtpyfw.redis import RedisInstance` | Redis |
| `import boto3.client('s3')` | `from dtpyfw.bucket import Bucket` | S3/Storage |
| `from kafka import KafkaProducer` | `from dtpyfw.kafka import KafkaProducerInstance` | Kafka |
| `import paramiko` | `from dtpyfw.ftp import FTPClient` | FTP/SFTP |
| `from passlib.hash import bcrypt` | `from dtpyfw.encrypt.hashing import hash_password` | Encryption |
| `from jose import jwt` | `from dtpyfw.encrypt.encryption import jwt_encode` | JWT |
| `import logging` | `from dtpyfw.log import footprint` | Logging |

### 🔍 When Raw Packages Are Acceptable

Direct imports of underlying packages (fastapi, sqlalchemy, celery, boto3, redis, kafka-python, etc.) should **only** be used when:

1. dtpyfw doesn't provide an equivalent feature
2. You have specific advanced requirements beyond dtpyfw's scope
3. You maintain compatibility with dtpyfw patterns (logging, configuration, etc.)

**Note**: In these cases, consider requesting a new dtpyfw feature rather than working around the framework.

---

## 📖 Documentation Structure

After installation, documentation is at: `{site-packages}/docs/`

```text
docs/
├── api/            # FastAPI application wrapper
├── bucket/         # S3-compatible storage
├── core/           # Core utilities (15+ files)
├── db/             # Database orchestration
├── encrypt/        # JWT and password hashing
├── ftp/            # FTP/SFTP client
├── kafka/          # Kafka messaging
├── log/            # Structured logging
├── redis/          # Redis client and caching
├── redis_streamer/ # Redis Streams
└── worker/         # Celery task management
```

**Each module has**:

- Detailed usage examples
- Constructor parameters
- Method signatures
- Best practices
- Common patterns

---

## 🚀 Quick Start

```python
# 1. Import what you need
from dtpyfw.log import footprint
from dtpyfw.core.env import Env
from dtpyfw.db import DatabaseConfig, DatabaseInstance

# 2. Configure
db_config = (
    DatabaseConfig()
    .set_db_backend("postgresql")
    .set_db_host(Env.get("DB_HOST", "localhost"))
    .set_db_user(Env.get("DB_USER"))
    .set_db_password(Env.get("DB_PASSWORD"))
)

# 3. Initialize
db = DatabaseInstance(db_config)

# 4. Use with logging
footprint.leave(level="INFO", message="Database initialized")

# 5. For more details, check the docstrings
help(DatabaseInstance)  # Complete API documentation
```

---

**Version**: dtpyfw 0.6.8+  
**Repository**: <https://github.com/datgate/dtpyfw>  
**For detailed documentation**: Check `docs/` folder and module docstrings
