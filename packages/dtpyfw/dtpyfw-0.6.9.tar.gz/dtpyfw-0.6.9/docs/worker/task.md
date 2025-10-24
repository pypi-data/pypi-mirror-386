# Task

## Overview

The `Task` class provides a centralized registry for managing Celery task routing, queue assignment, and periodic scheduling within the DealerTower framework. It maintains internal collections of task routes, queue mappings, and periodic schedules that can be consumed by the Worker builder to configure a Celery application.

## Module Location

```python
from dtpyfw.worker import Task
```

## Class Definition

### Task

A registry class for collecting and organizing Celery task configurations including import paths, queue routing, and periodic execution schedules.

#### Attributes

- **`_tasks`** (`list[str]`): List of registered task module paths for Celery's autodiscovery mechanism.
- **`_tasks_routes`** (`dict[str, dict[str, str]]`): Dictionary mapping task names to queue configurations.
- **`_periodic_tasks`** (`dict[str, dict[str, Any]]`): Dictionary mapping task names to schedule configurations including timing and arguments.

## Methods

### Task Registration

#### `register(route: str, queue: Optional[str] = None) -> Task`

Register a single Celery task with optional queue routing.

**Parameters:**

- `route` (`str`): The dotted import path to the task module (e.g., "myapp.tasks.process_data").
- `queue` (`Optional[str]`, optional): Optional queue name to route this task to. If `None`, uses default routing. Defaults to `None`.

**Returns:**

- `Task`: The current Task instance for method chaining.

**Description:**

Registers a task module path for autodiscovery and optionally assigns it to a specific queue. If no queue is specified, the task will use Celery's default queue routing.

**Example:**

```python
from dtpyfw.worker import Task

task = Task()

# Register task with default queue
task.register("myapp.tasks.send_email")

# Register task with specific queue
task.register("myapp.tasks.process_payment", queue="payments")
task.register("myapp.tasks.generate_report", queue="reports")
```

---

#### `bulk_register(routes: Sequence[str], queue: Optional[str] = None) -> Task`

Register multiple Celery tasks with an optional shared queue.

**Parameters:**

- `routes` (`Sequence[str]`): A sequence of dotted import paths to task modules (e.g., `["myapp.tasks.task1", "myapp.tasks.task2"]`).
- `queue` (`Optional[str]`, optional): Optional queue name to route all tasks to. If `None`, uses default routing. Defaults to `None`.

**Returns:**

- `Task`: The current Task instance for method chaining.

**Description:**

Convenience method for registering multiple task module paths at once. All tasks in the sequence will be assigned to the same queue if one is specified.

**Example:**

```python
from dtpyfw.worker import Task

task = Task()

# Register multiple tasks with default queue
task.bulk_register([
    "myapp.tasks.task1",
    "myapp.tasks.task2",
    "myapp.tasks.task3"
])

# Register multiple tasks to specific queue
task.bulk_register([
    "myapp.tasks.send_welcome_email",
    "myapp.tasks.send_notification",
    "myapp.tasks.send_digest"
], queue="emails")
```

---

### Periodic Task Registration

#### `register_periodic_task(route: str, schedule: crontab | timedelta, queue: Optional[str] = None, *args: Any) -> Task`

Register a periodic task with schedule and optional arguments.

**Parameters:**

- `route` (`str`): The dotted import path to the task module (e.g., "myapp.tasks.nightly_cleanup").
- `schedule` (`crontab | timedelta`): The schedule for task execution. Use `crontab` for cron-style schedules or `timedelta` for interval-based scheduling.
- `queue` (`Optional[str]`, optional): Optional queue name to route this task to. If `None`, uses default routing. Defaults to `None`.
- `*args` (`Any`): Positional arguments to pass to the task when it executes.

**Returns:**

- `Task`: The current Task instance for method chaining.

**Description:**

Registers a task that should run on a recurring schedule using either crontab-style scheduling or time-based intervals. The task is also registered for autodiscovery and optional queue routing.

**Example:**

```python
from dtpyfw.worker import Task
from celery.schedules import crontab
from datetime import timedelta

task = Task()

# Crontab-style schedule - every day at 2 AM
task.register_periodic_task(
    route="myapp.tasks.daily_cleanup",
    schedule=crontab(hour=2, minute=0),
    queue="maintenance"
)

# Crontab-style schedule - every Monday at 8 AM
task.register_periodic_task(
    route="myapp.tasks.weekly_report",
    schedule=crontab(hour=8, minute=0, day_of_week=1),
    queue="reports"
)

# Interval-based schedule - every 5 minutes
task.register_periodic_task(
    route="myapp.tasks.health_check",
    schedule=timedelta(minutes=5),
    queue="monitoring"
)

# Periodic task with arguments
task.register_periodic_task(
    route="myapp.tasks.send_reminder",
    schedule=crontab(hour=9, minute=0),
    queue="notifications",
    "daily",  # First argument
    True      # Second argument
)
```

---

#### `bulk_register_periodic_task(tasks: Sequence[tuple[str, crontab | timedelta, Sequence[Any]]], queue: Optional[str] = None) -> Task`

Register multiple periodic tasks in bulk with optional shared queue.

**Parameters:**

- `tasks` (`Sequence[tuple[str, crontab | timedelta, Sequence[Any]]]`): A sequence of tuples where each tuple contains:
  - `route` (`str`): The dotted import path to the task module.
  - `schedule` (`crontab | timedelta`): The schedule for task execution.
  - `args` (`Sequence[Any]`): Positional arguments to pass to the task.
- `queue` (`Optional[str]`, optional): Optional queue name to route all tasks to. If `None`, uses default routing. Defaults to `None`.

**Returns:**

- `Task`: The current Task instance for method chaining.

**Description:**

Convenience method for registering multiple periodic tasks at once. Each task is defined as a tuple containing the route, schedule, and arguments. All tasks will be assigned to the same queue if specified.

**Example:**

```python
from dtpyfw.worker import Task
from celery.schedules import crontab
from datetime import timedelta

task = Task()

# Register multiple periodic tasks
periodic_tasks = [
    ("myapp.tasks.hourly_sync", timedelta(hours=1), []),
    ("myapp.tasks.daily_report", crontab(hour=8, minute=0), ["daily"]),
    ("myapp.tasks.weekly_cleanup", crontab(hour=2, minute=0, day_of_week=0), []),
]

task.bulk_register_periodic_task(periodic_tasks, queue="scheduled")
```

---

### Getter Methods

#### `get_tasks() -> list[str]`

Retrieve all registered task module paths for autodiscovery.

**Returns:**

- `list[str]`: A list of dotted import paths to task modules.

**Description:**

Returns the list of task import paths that have been registered via `register()` or `bulk_register()` methods. This list is used by Celery's autodiscover_tasks mechanism.

**Example:**

```python
from dtpyfw.worker import Task

task = Task()
task.register("myapp.tasks.task1")
task.register("myapp.tasks.task2")

task_list = task.get_tasks()
# Returns: ["myapp.tasks.task1", "myapp.tasks.task2"]
```

---

#### `get_tasks_routes() -> dict[str, dict[str, str]]`

Retrieve the task-to-queue routing configuration.

**Returns:**

- `dict[str, dict[str, str]]`: A dictionary where keys are task import paths and values are dictionaries containing routing configuration (e.g., `{"queue": "name"}`).

**Description:**

Returns a dictionary mapping task names to their queue routing configuration. This dictionary is suitable for Celery's `task_routes` configuration setting.

**Example:**

```python
from dtpyfw.worker import Task

task = Task()
task.register("myapp.tasks.email", queue="emails")
task.register("myapp.tasks.payment", queue="payments")
task.register("myapp.tasks.default_task")

routes = task.get_tasks_routes()
# Returns:
# {
#     "myapp.tasks.email": {"queue": "emails"},
#     "myapp.tasks.payment": {"queue": "payments"},
#     "myapp.tasks.default_task": {}
# }
```

---

#### `get_periodic_tasks() -> dict[str, dict[str, Any]]`

Retrieve the periodic task schedule configuration.

**Returns:**

- `dict[str, dict[str, Any]]`: A dictionary where keys are task import paths and values are dictionaries containing "task", "schedule", and "args" keys.

**Description:**

Returns a dictionary containing all registered periodic tasks with their schedules and arguments. This dictionary is suitable for Celery's `beat_schedule` configuration setting (used by RedBeat).

**Example:**

```python
from dtpyfw.worker import Task
from celery.schedules import crontab

task = Task()
task.register_periodic_task(
    "myapp.tasks.daily_job",
    crontab(hour=2, minute=0),
    queue="maintenance"
)

schedules = task.get_periodic_tasks()
# Returns:
# {
#     "myapp.tasks.daily_job": {
#         "task": "myapp.tasks.daily_job",
#         "schedule": <crontab object>,
#         "args": ()
#     }
# }
```

---

## Complete Usage Examples

### Basic Task Registration

```python
from dtpyfw.worker import Task

# Create task registry
task = Task()

# Register individual tasks
task.register("myapp.tasks.send_email")
task.register("myapp.tasks.process_order")
task.register("myapp.tasks.update_inventory")

# Register tasks with specific queues
task.register("myapp.tasks.send_sms", queue="notifications")
task.register("myapp.tasks.generate_invoice", queue="reports")
```

---

### Queue-Based Task Organization

```python
from dtpyfw.worker import Task

task = Task()

# Email processing queue
task.bulk_register([
    "myapp.tasks.send_welcome_email",
    "myapp.tasks.send_password_reset",
    "myapp.tasks.send_notification"
], queue="emails")

# Payment processing queue
task.bulk_register([
    "myapp.tasks.process_payment",
    "myapp.tasks.refund_payment",
    "myapp.tasks.verify_transaction"
], queue="payments")

# High-priority queue
task.bulk_register([
    "myapp.tasks.urgent_notification",
    "myapp.tasks.emergency_alert"
], queue="high_priority")

# Default queue
task.bulk_register([
    "myapp.tasks.log_event",
    "myapp.tasks.update_cache"
])
```

---

### Periodic Task Scheduling

```python
from dtpyfw.worker import Task
from celery.schedules import crontab
from datetime import timedelta

task = Task()

# Daily tasks
task.register_periodic_task(
    route="myapp.tasks.generate_daily_report",
    schedule=crontab(hour=8, minute=0),  # Every day at 8:00 AM
    queue="reports"
)

task.register_periodic_task(
    route="myapp.tasks.cleanup_old_logs",
    schedule=crontab(hour=2, minute=0),  # Every day at 2:00 AM
    queue="maintenance"
)

# Weekly tasks
task.register_periodic_task(
    route="myapp.tasks.weekly_summary",
    schedule=crontab(hour=9, minute=0, day_of_week=1),  # Every Monday at 9:00 AM
    queue="reports"
)

# Monthly tasks
task.register_periodic_task(
    route="myapp.tasks.monthly_billing",
    schedule=crontab(hour=0, minute=0, day_of_month=1),  # 1st day of month at midnight
    queue="billing"
)

# Interval-based tasks
task.register_periodic_task(
    route="myapp.tasks.health_check",
    schedule=timedelta(minutes=5),  # Every 5 minutes
    queue="monitoring"
)

task.register_periodic_task(
    route="myapp.tasks.sync_data",
    schedule=timedelta(hours=1),  # Every hour
    queue="sync"
)

# Periodic task with arguments
task.register_periodic_task(
    route="myapp.tasks.send_reminder",
    schedule=crontab(hour=10, minute=0),
    queue="notifications",
    "morning_reminder",  # arg1
    True,                # arg2
    {"type": "email"}    # arg3
)
```

---

### Bulk Periodic Task Registration

```python
from dtpyfw.worker import Task
from celery.schedules import crontab
from datetime import timedelta

task = Task()

# Define multiple periodic tasks
maintenance_tasks = [
    ("myapp.tasks.cleanup_temp_files", crontab(hour=3, minute=0), []),
    ("myapp.tasks.optimize_database", crontab(hour=4, minute=0), []),
    ("myapp.tasks.backup_data", crontab(hour=1, minute=0), ["full_backup"]),
]

monitoring_tasks = [
    ("myapp.tasks.check_disk_space", timedelta(minutes=10), []),
    ("myapp.tasks.check_memory_usage", timedelta(minutes=5), []),
    ("myapp.tasks.ping_services", timedelta(minutes=1), []),
]

# Register in bulk
task.bulk_register_periodic_task(maintenance_tasks, queue="maintenance")
task.bulk_register_periodic_task(monitoring_tasks, queue="monitoring")
```

---

### Complete Application Setup

```python
from dtpyfw.worker import Worker, Task
from dtpyfw.redis.connection import RedisInstance
from celery.schedules import crontab
from datetime import timedelta

# Step 1: Create and configure task registry
task = Task()

# Register regular tasks with queues
task.register("myapp.tasks.process_order", queue="orders")
task.register("myapp.tasks.send_email", queue="emails")
task.register("myapp.tasks.generate_pdf", queue="documents")

# Register periodic tasks
task.register_periodic_task(
    route="myapp.tasks.daily_report",
    schedule=crontab(hour=8, minute=0),
    queue="reports"
)

task.register_periodic_task(
    route="myapp.tasks.cleanup",
    schedule=crontab(hour=2, minute=0),
    queue="maintenance"
)

task.register_periodic_task(
    route="myapp.tasks.health_check",
    schedule=timedelta(minutes=5),
    queue="monitoring"
)

# Step 2: Configure Redis
redis = RedisInstance(
    redis_host="localhost",
    redis_port=6379,
    redis_db=0
)

# Step 3: Create worker with task registry
worker = Worker()
worker.set_name("myapp_worker")
worker.set_redis(redis)
worker.set_task(task)  # Attach task registry
worker.set_timezone("UTC")

# Step 4: Create Celery application
celery_app = worker.create()

# The celery_app now has:
# - All registered tasks available for autodiscovery
# - Task-to-queue routing configured
# - Periodic tasks scheduled via RedBeat
```

---

### Multi-Module Task Organization

```python
from dtpyfw.worker import Task

task = Task()

# Core business logic tasks
task.bulk_register([
    "myapp.orders.tasks.create_order",
    "myapp.orders.tasks.cancel_order",
    "myapp.orders.tasks.process_refund"
], queue="orders")

# User management tasks
task.bulk_register([
    "myapp.users.tasks.create_user",
    "myapp.users.tasks.send_verification",
    "myapp.users.tasks.update_profile"
], queue="users")

# Notification tasks
task.bulk_register([
    "myapp.notifications.tasks.send_email",
    "myapp.notifications.tasks.send_sms",
    "myapp.notifications.tasks.send_push"
], queue="notifications")

# Analytics tasks
task.bulk_register([
    "myapp.analytics.tasks.track_event",
    "myapp.analytics.tasks.generate_metrics",
    "myapp.analytics.tasks.export_data"
], queue="analytics")

# Background maintenance
task.bulk_register([
    "myapp.maintenance.tasks.cleanup_logs",
    "myapp.maintenance.tasks.archive_data",
    "myapp.maintenance.tasks.optimize_db"
], queue="maintenance")
```

---

### Advanced Crontab Schedules

```python
from dtpyfw.worker import Task
from celery.schedules import crontab

task = Task()

# Every 15 minutes
task.register_periodic_task(
    "myapp.tasks.frequent_sync",
    crontab(minute="*/15")
)

# Every weekday at 9 AM
task.register_periodic_task(
    "myapp.tasks.weekday_report",
    crontab(hour=9, minute=0, day_of_week="1-5")
)

# Every weekend at 10 AM
task.register_periodic_task(
    "myapp.tasks.weekend_cleanup",
    crontab(hour=10, minute=0, day_of_week="6-7")
)

# Every quarter hour between 9 AM and 5 PM on weekdays
task.register_periodic_task(
    "myapp.tasks.business_hours_check",
    crontab(minute="*/15", hour="9-17", day_of_week="1-5")
)

# First day of every month at midnight
task.register_periodic_task(
    "myapp.tasks.monthly_reset",
    crontab(hour=0, minute=0, day_of_month=1)
)

# Every 3 hours
task.register_periodic_task(
    "myapp.tasks.periodic_sync",
    crontab(minute=0, hour="*/3")
)

# Multiple specific times
task.register_periodic_task(
    "myapp.tasks.scheduled_report",
    crontab(hour="8,12,18", minute=0)  # 8 AM, 12 PM, 6 PM
)
```

---

## Integration with Worker

The Task class is designed to be consumed by the Worker builder. The Worker's `set_task()` method extracts the registered tasks, routes, and schedules:

```python
from dtpyfw.worker import Worker, Task

# Configure tasks
task = Task()
task.register("myapp.tasks.example", queue="default")

# Pass to worker
worker = Worker()
worker.set_task(task)  # Internally calls:
                        # - task.get_tasks() for autodiscovery
                        # - task.get_tasks_routes() for routing
                        # - task.get_periodic_tasks() for schedules

celery_app = worker.create()
```

---

## Best Practices

1. **Organize by Domain**: Group related tasks by business domain or functionality:
   ```python
   task.bulk_register([
       "orders.tasks.create",
       "orders.tasks.update",
       "orders.tasks.delete"
   ], queue="orders")
   ```

2. **Dedicated Queues**: Use separate queues for different task types to control concurrency and priority:
   ```python
   task.register("tasks.critical", queue="high_priority")
   task.register("tasks.background", queue="low_priority")
   ```

3. **Time Zone Awareness**: When using crontab schedules, ensure your Worker's timezone is set appropriately:
   ```python
   worker.set_timezone("America/New_York")
   ```

4. **Meaningful Task Names**: Use clear, descriptive task route names:
   ```python
   task.register("myapp.orders.tasks.process_payment")  # Good
   task.register("myapp.tasks.task1")  # Avoid
   ```

5. **Periodic Task Intervals**: Choose appropriate intervals for periodic tasks to balance responsiveness and resource usage:
   ```python
   # Critical monitoring - frequent
   task.register_periodic_task("health_check", timedelta(minutes=1))
   
   # Regular sync - moderate
   task.register_periodic_task("data_sync", timedelta(hours=1))
   
   # Maintenance - infrequent
   task.register_periodic_task("cleanup", crontab(hour=2))
   ```

6. **Queue Isolation**: Isolate long-running or resource-intensive tasks:
   ```python
   task.register("tasks.heavy_processing", queue="heavy")
   task.register("tasks.quick_action", queue="fast")
   ```

7. **Documentation**: Document task arguments when using periodic tasks:
   ```python
   # Task expects: reminder_type (str), send_email (bool)
   task.register_periodic_task(
       "tasks.send_reminder",
       crontab(hour=9),
       None,
       "daily",  # reminder_type
       True      # send_email
   )
   ```

---

## Common Crontab Patterns

Here are commonly used crontab schedule patterns:

| Pattern | Description | Example |
|---------|-------------|---------|
| `crontab(minute=0)` | Every hour | Top of every hour |
| `crontab(minute=0, hour=0)` | Daily at midnight | Once per day |
| `crontab(minute=0, hour=0, day_of_week=1)` | Weekly | Every Monday |
| `crontab(minute=0, hour=0, day_of_month=1)` | Monthly | First of month |
| `crontab(minute="*/15")` | Every 15 minutes | 4 times per hour |
| `crontab(hour="*/2")` | Every 2 hours | 12 times per day |
| `crontab(day_of_week="1-5")` | Weekdays only | Monday-Friday |
| `crontab(day_of_week="6-7")` | Weekends only | Saturday-Sunday |
| `crontab(hour=9, day_of_week=1)` | Weekly on Monday | Monday 9 AM |

---

## Dependencies

- **celery**: For crontab and schedule types
- **datetime**: For timedelta-based scheduling

These are standard library or already included in Celery.

---

## Related Documentation

- [Worker Configuration](worker.md) - Worker builder and Celery setup
- [Redis Connection](../redis/connection.md) - Redis configuration for broker/backend

---

## Notes

- The Task class uses class-level collections for storing task configurations. Each instance starts with empty collections.
- Task routes are stored as dotted import paths (e.g., "myapp.tasks.function_name"), not function objects.
- When using `bulk_register_periodic_task()`, arguments must be provided as a sequence (list or tuple).
- Periodic tasks are automatically registered as regular tasks, so you don't need to call `register()` separately.
- The class supports method chaining for fluent configuration.
- RedBeat (used by Worker) stores all periodic schedules in Redis, making them dynamically editable at runtime.
