# DealerTower Python Framework (dtpyfw)

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checked](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

**DealerTower Python Framework (dtpyfw)** is a comprehensive, production-ready framework providing reusable building blocks for microservices. It offers modular sub-packages for API development, database orchestration, caching, messaging, storage, task scheduling, and more—all with full type safety and consistent interfaces.

This library follows Python packaging standards including PEP 561 for type checking support, ensuring excellent IDE integration and compile-time type validation.

---

## 🚀 Installation

Requires **Python 3.11** or newer.

### Base Installation

```bash
pip install dtpyfw
```

The base installation includes:

- **Core utilities**: Environment management, async bridging, validation, hashing, chunking, retry logic, and more
- **Logging system**: Structured logging with multiple handlers and formatters

### Development Installation

Using Poetry (recommended for contributors):

```bash
poetry install -E all
```

### Querying Package Version

```python
import dtpyfw
print(dtpyfw.__version__)  # e.g., "0.6.8"
```

### Optional Extras

Install specific features as needed. Extras can be combined (e.g., `pip install dtpyfw[api,db,redis]`).

| Extra | Description | Key Features | Install Command |
|-------|-------------|--------------|-----------------|
| **api** | FastAPI application framework | Application wrapper, middleware, CORS, exception handling, routing | `pip install dtpyfw[api]` |
| **db** | SQLAlchemy database orchestration | Sync/async engines, connection pooling, health checks, search utilities, PostgreSQL support | `pip install dtpyfw[db]` |
| **db-mysql** | MySQL database support | MySQL-specific drivers (PyMySQL, aiomysql) | `pip install dtpyfw[db-mysql]` |
| **bucket** | S3-compatible object storage | Upload, download, duplicate, delete objects; MinIO & AWS S3 support | `pip install dtpyfw[bucket]` |
| **redis** | Redis client & caching | Connection management, health checks, function memoization, data compression | `pip install dtpyfw[redis]` |
| **redis_streamer** | Redis Streams messaging | Producer/consumer for Redis Streams with sync & async support | `pip install dtpyfw[redis_streamer]` |
| **kafka** | Kafka messaging | Producer/consumer wrappers with error handling and logging | `pip install dtpyfw[kafka]` |
| **worker** | Celery task management | Task registry, periodic scheduling, worker configuration, Redis backend | `pip install dtpyfw[worker]` |
| **ftp** | FTP/SFTP client | Unified interface for FTP & SFTP operations with context manager support | `pip install dtpyfw[ftp]` |
| **encrypt** | Cryptography utilities | JWT encryption/decryption, password hashing (bcrypt, argon2) | `pip install dtpyfw[encrypt]` |
| **all** | All features above | Complete framework installation | `pip install dtpyfw[all]` |

#### Common Installation Profiles

```bash
# Typical API microservice (FastAPI + Database + Redis)
pip install dtpyfw[api,db,redis]

# Background worker service (Celery + Database + Redis)
pip install dtpyfw[worker,db,redis]

# Data processing service (S3 + Database + FTP)
pip install dtpyfw[bucket,db,ftp]

# Full-featured microservice
pip install dtpyfw[all]
```

---

## � Documentation

### Included with Installation

When you install dtpyfw, comprehensive documentation is automatically included in your Python environment:

- **`how-to-use.md`**: AI-friendly developer guide with all import paths, configuration patterns, and usage examples
- **`docs/`**: Detailed module documentation for every component

**Accessing Documentation After Installation:**

```python
# Find dtpyfw installation path
import dtpyfw
import os
dtpyfw_path = os.path.dirname(dtpyfw.__file__)
print(f"dtpyfw installed at: {dtpyfw_path}")

# Documentation is in the parent directory:
# - how-to-use.md: {dtpyfw_path}/../how-to-use.md
# - docs/: {dtpyfw_path}/../docs/
```

**Quick Access Command:**

```bash
# Find and display how-to-use.md path
python -c "import dtpyfw, os; print(os.path.join(os.path.dirname(os.path.dirname(dtpyfw.__file__)), 'how-to-use.md'))"
```

**💡 Pro Tip for AI Assistants**: Copy `how-to-use.md` to your project root so AI coding assistants can reference it directly. This guide contains all import paths, configuration patterns, and usage examples for optimal AI assistance.

---

## �📦 Feature Overview

### Core Utilities (Included in Base)

The `dtpyfw.core` module provides foundational utilities used across all other modules:

- **Async Bridge** (`async.py`): Execute async functions from sync contexts
- **Chunking** (`chunking.py`): Split iterables and files into manageable chunks
- **Environment** (`env.py`): Type-safe environment variable access with validation
- **Exceptions** (`exception.py`): Structured exception handling and serialization
- **File/Folder** (`file_folder.py`): File system operations and path utilities
- **Hashing** (`hashing.py`): Consistent hash generation for data structures
- **JSON Encoding** (`jsonable_encoder.py`): Serialize complex Python objects to JSON
- **Request Utilities** (`request.py`): HTTP request helpers and decorators
- **Retry Logic** (`retry.py`): Configurable retry mechanisms with exponential backoff
- **Safe Access** (`safe_access.py`): Safely access nested data structures
- **Singleton** (`singleton.py`): Thread-safe singleton pattern implementation
- **Slug Generation** (`slug.py`): Create URL-safe slugs from strings
- **URL Utilities** (`url.py`): URL parsing and manipulation helpers
- **Validation** (`validation.py`): Common validation functions for data integrity

📖 **[View Core Documentation](docs/core/)**

### Logging System (Included in Base)

The `dtpyfw.log` module provides production-ready structured logging:

- **Centralized Configuration**: Configure all logging through `LogConfig` class
- **Multiple Handlers**: Console output, file rotation, API logging, Kafka streaming
- **Custom Formatters**: JSON formatting, colored console output, structured data
- **Celery Integration**: Specialized logging for Celery worker contexts
- **Request Footprinting**: Track requests across distributed services
- **Performance Monitoring**: Built-in timing and resource usage tracking

📖 **[View Logging Documentation](docs/log/)**

### API Development (`dtpyfw.api`)

Build production-ready FastAPI applications with pre-configured best practices:

- **Application Wrapper**: Clean OOP interface for FastAPI configuration
- **Middleware Stack**: Timer middleware, error handling, custom middleware support
- **CORS Management**: Flexible CORS configuration with sensible defaults
- **Exception Handling**: Standardized HTTP and validation error responses
- **Router Organization**: Modular router registration with prefix support
- **Sub-Applications**: Mount multiple FastAPI apps as microservice modules
- **Session Management**: Optional session middleware integration
- **Compression**: Automatic gzip compression for responses
- **OpenAPI Integration**: Automatic Swagger UI and ReDoc documentation

📖 **[View API Documentation](docs/api/)**

### Database Management (`dtpyfw.db`)

Comprehensive SQLAlchemy integration with sync/async support:

- **Connection Orchestration**: Automatic engine and session management
- **Sync & Async Support**: Seamless switching between synchronous and asynchronous operations
- **Read/Write Splitting**: Separate connections for read and write operations
- **Connection Pooling**: Configurable connection pools with health monitoring
- **Health Checks**: Built-in database health check endpoints
- **Search Utilities**: Advanced query builders for filtering, sorting, and pagination
- **SSL/TLS Support**: Secure database connections with certificate validation
- **Context Managers**: Safe session handling with automatic cleanup
- **FastAPI Integration**: Dependency injection patterns for FastAPI routes

📖 **[View Database Documentation](docs/db/)**

### S3-Compatible Storage (`dtpyfw.bucket`)

Simple interface for S3-compatible object storage:

- **Unified API**: Works with AWS S3, MinIO, DigitalOcean Spaces, and other S3-compatible services
- **File Operations**: Upload, download, duplicate, delete objects
- **Metadata Management**: Get object info, check existence, list buckets
- **Stream Support**: Handle large files with streaming uploads/downloads
- **Error Handling**: Comprehensive error handling with detailed logging
- **Flexible Configuration**: Support for custom endpoints and credentials

📖 **[View Bucket Documentation](docs/bucket/)**

### Redis Integration (`dtpyfw.redis`)

High-performance Redis client with caching utilities:

- **Connection Management**: Thread-safe Redis connection pools
- **Health Monitoring**: Redis health checks for readiness probes
- **Function Caching**: Automatic memoization with decorator pattern
- **Data Compression**: zlib compression to minimize memory usage
- **Conditional Caching**: Cache based on specific argument conditions
- **TTL Support**: Configurable expiration for cached values
- **Sync & Async**: Support for both synchronous and asynchronous operations
- **Type Safety**: Full type annotations for IDE integration

📖 **[View Redis Documentation](docs/redis/)**

### Kafka Messaging (`dtpyfw.kafka`)

Simplified Kafka producer and consumer wrappers:

- **Producer**: High-level message production with automatic JSON encoding
- **Consumer**: Simplified message consumption with error handling
- **Configuration**: Clean configuration interface with connection management
- **Logging Integration**: Built-in logging for all Kafka operations
- **Error Handling**: Graceful error handling with retry support

📖 **[View Kafka Documentation](docs/kafka/)**

### Celery Workers (`dtpyfw.worker`)

Streamlined Celery task management and scheduling:

- **Task Registry**: Centralized task registration and routing
- **Queue Management**: Flexible queue assignment for task distribution
- **Periodic Scheduling**: Cron-style and interval-based task scheduling
- **Worker Builder**: Simple worker configuration and initialization
- **Redis Backend**: Integrated Redis support for result backend and broker
- **Beat Integration**: RedBeat scheduler for dynamic schedule management

📖 **[View Worker Documentation](docs/worker/)**

### FTP/SFTP Client (`dtpyfw.ftp`)

Unified interface for FTP and SFTP operations:

- **Protocol Abstraction**: Single API for both FTP and SFTP
- **Context Manager**: Automatic connection management and cleanup
- **File Operations**: Upload, download, list, delete, rename files
- **Directory Management**: Create, remove, and navigate directories
- **Auto-Detection**: Automatic protocol detection based on port
- **Timeout Control**: Configurable connection timeouts

📖 **[View FTP Documentation](docs/ftp/)**

### Encryption & Security (`dtpyfw.encrypt`)

Authentication and cryptography utilities:

- **JWT Support**: Create and validate JSON Web Tokens
- **Multiple Algorithms**: HS256, HS384, HS512, RS256, RS384, RS512
- **Password Hashing**: bcrypt and argon2 password hashing
- **Token Expiration**: Configurable TTL for JWT tokens
- **Custom Claims**: Support for custom JWT payload data

📖 **[View Encryption Documentation](docs/encrypt/)**

---

## 🎯 Quick Start Examples

### Building a FastAPI Application

```python
from dtpyfw.api import Application
from dtpyfw.api.routes import Router

# Create routers
router = Router()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Initialize application
app = Application(
    title="My Microservice",
    version="1.0.0",
    routers=[router],
    cors_settings={"allow_origins": ["*"]}
)

# Access the FastAPI app
fastapi_app = app.app
```

### Database Operations

```python
from dtpyfw.db import DatabaseConfig, DatabaseInstance

# Configure database
config = (
    DatabaseConfig()
    .set_db_backend("postgresql")
    .set_db_host("localhost")
    .set_db_port(5432)
    .set_db_name("mydb")
    .set_db_user("user")
    .set_db_password("password")
)

# Create instance
db = DatabaseInstance(config)

# Use context manager for sessions
with db.get_session() as session:
    results = session.execute("SELECT * FROM users").fetchall()

# Async support
async with db.get_async_session() as session:
    result = await session.execute("SELECT * FROM users")
```

### Redis Caching

```python
from dtpyfw.redis.caching import cache_function
from dtpyfw.redis.connection import RedisInstance

# Initialize Redis
redis = RedisInstance(host="localhost", port=6379)

# Cache function results
@cache_function(redis_client=redis.client, expire_time=3600)
def expensive_computation(x: int, y: int) -> int:
    return x ** y

result = expensive_computation(2, 10)  # Computed and cached
result = expensive_computation(2, 10)  # Retrieved from cache
```

### Celery Task Management

```python
from dtpyfw.worker import Task, Worker
from dtpyfw.redis import RedisInstance

# Register tasks
Task.register("myapp.tasks.process_data", queue="high_priority")
Task.register("myapp.tasks.send_email", queue="low_priority")

# Schedule periodic tasks
Task.schedule_periodic(
    "myapp.tasks.cleanup",
    schedule="cron",
    hour="0",
    minute="0"
)

# Build worker
redis = RedisInstance(host="localhost", port=6379)
worker = Worker.build(task=Task, redis=redis, app_name="my_worker")
```

### S3 File Operations

```python
from dtpyfw.bucket import Bucket

# Initialize bucket
bucket = Bucket(
    name="my-bucket",
    endpoint_url="https://s3.amazonaws.com",
    access_key="ACCESS_KEY",
    secret_key="SECRET_KEY"
)

# Upload file
bucket.upload_file("local_file.txt", "remote/path/file.txt")

# Download file
bucket.download_file("remote/path/file.txt", "downloaded_file.txt")

# Check existence
exists = bucket.file_exists("remote/path/file.txt")
```

---

## 📚 Documentation

Comprehensive documentation for each module is available in the `docs/` directory:

- **[Core Utilities](docs/core/)** - Foundational utilities and helpers
- **[Logging](docs/log/)** - Structured logging configuration
- **[API](docs/api/)** - FastAPI application development
- **[Database](docs/db/)** - SQLAlchemy integration and search utilities
- **[Bucket](docs/bucket/)** - S3-compatible object storage
- **[Redis](docs/redis/)** - Redis caching and connection management
- **[Redis Streamer](docs/redis_streamer/)** - Redis Streams messaging
- **[Kafka](docs/kafka/)** - Kafka producer and consumer
- **[Worker](docs/worker/)** - Celery task management
- **[FTP](docs/ftp/)** - FTP/SFTP client operations
- **[Encryption](docs/encrypt/)** - JWT and password hashing

---

## 🤝 Contributing

We welcome contributions from authorized DealerTower employees and contractors! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Development setup and environment configuration
- Coding standards and style guide (PEP 8, Black formatting)
- Type annotations and docstring conventions
- Testing requirements and running tests
- Pull request process and code review
- Documentation standards

### Development Workflow

```bash
# Install dependencies
poetry install -E all

# Run tests
pytest

# Format code
black .

# Type check
mypy dtpyfw

# Run linters
ruff check . --fix
```

---

## 📝 Version History

Current version: **0.6.8**

A detailed changelog is maintained in the git commit history. View releases on the [GitHub repository](https://github.com/datgate/dtpyfw).

---

## 📄 License

DealerTower Python Framework is proprietary software. See [LICENSE](LICENSE) for complete terms and conditions.

---

## 🔗 Resources

- **Repository**: [github.com/datgate/dtpyfw](https://github.com/datgate/dtpyfw)
- **Issue Tracker**: Report bugs and request features via GitHub Issues
- **Internal Documentation**: Additional documentation available on DealerTower's internal wiki

---

## 💡 Philosophy

**dtpyfw** is designed with the following principles:

- **Modularity**: Install only what you need
- **Type Safety**: Full type annotations for better IDE support and fewer runtime errors
- **Production Ready**: Battle-tested patterns and best practices
- **Developer Experience**: Clean APIs with consistent interfaces
- **Documentation**: Comprehensive docs for every module
- **Standards Compliance**: Follows PEP 8, PEP 561, and Python packaging standards
