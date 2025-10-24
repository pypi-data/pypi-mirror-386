# Shared Counter

A shared-memory based multiprocessing counter for cross-process synchronization. Unlike `multiprocessing.Value`, this counter is fully picklable and can be shared between processes by name.

## Features

- **Picklable**: Can be safely passed between processes via pickle
- **Named counters**: Multiple processes can connect to the same counter by name
- **Shared memory backed**: Uses `multiprocessing.shared_memory` for efficient IPC
- **Simple API**: Drop-in replacement for `multiprocessing.Value('i', 0)`
- **Run namespacing**: Isolate counters by run_id to prevent collisions
- **Atomic operations**: Thread-safe and process-safe operations on shared memory

## Installation

```bash
pip install shared_counter
```

Or for development:

```bash
git clone <repo-url>
cd shared_counter
uv sync
uv pip install -e .
```

## Quick Start

```python
from shared_counter import SharedMemoryCounter
from multiprocessing import Process
import time

def worker(counter_name: str, run_id: str, increments: int):
    # Connect to existing counter by name
    counter = SharedMemoryCounter(name=counter_name, create=False, run_id=run_id)

    for i in range(increments):
        counter.value += 1
        print(f"Worker incremented counter to {counter.value}")
        time.sleep(0.1)

    counter.close()

def main():
    run_id = "my_app"

    # Create the counter in main process
    task_counter = SharedMemoryCounter(name="tasks", create=True, run_id=run_id, initial_value=0)

    # Start worker processes
    processes = []
    for i in range(3):
        p = Process(target=worker, args=("tasks", run_id, 5))
        p.start()
        processes.append(p)

    # Wait for all processes to finish
    for p in processes:
        p.join()

    print(f"Final counter value: {task_counter.value}")

    # Cleanup
    task_counter.unlink()  # Delete shared memory

if __name__ == "__main__":
    main()
```

## API Reference

### `SharedMemoryCounter(name, create=False, run_id="", initial_value=0)`

Creates or connects to a shared memory counter.

**Parameters:**
- `name` (str): Counter identifier
- `create` (bool): Whether to create new counter (`True`) or connect to existing (`False`)
- `run_id` (str): Optional run identifier for namespacing counters
- `initial_value` (int): Initial value when creating (ignored when connecting)

**Properties:**
- `value`: Get or set the current counter value (thread-safe)

**Methods:**
- `get_lock()`: Returns a no-op lock for API compatibility with `multiprocessing.Value`
- `close()`: Close connection to shared memory
- `unlink()`: Delete the shared memory segment (call from creator process)

## Use Cases

### 1. Process Coordination

```python
# Coordinator tracks how many workers are ready
ready_counter = SharedMemoryCounter("workers_ready", create=True, run_id="batch_job", initial_value=0)

# Workers increment when ready
worker_counter = SharedMemoryCounter("workers_ready", create=False, run_id="batch_job")
worker_counter.value += 1

# Coordinator waits for all workers
while ready_counter.value < num_workers:
    time.sleep(0.1)
```

### 2. Replacing Non-Picklable Values

```python
# Instead of this (won't work across process boundaries):
# counter = multiprocessing.Value('i', 0)  # Can't pickle reliably

# Use this:
counter = SharedMemoryCounter("shared_count", create=True, run_id="app", initial_value=0)
# This counter can be safely pickled and passed to subprocesses
```

### 3. Resource Counting

```python
# Track available resources across processes
available_slots = SharedMemoryCounter("slots", create=True, run_id="server", initial_value=10)

# Worker processes decrement when taking a slot
slots_counter = SharedMemoryCounter("slots", create=False, run_id="server")
if slots_counter.value > 0:
    slots_counter.value -= 1
    # Do work...
    slots_counter.value += 1  # Release slot when done
```

### 4. Progress Tracking

```python
# Track completed tasks across multiple workers
completed = SharedMemoryCounter("completed", create=True, run_id="pipeline", initial_value=0)
total_tasks = 1000

# Workers update progress
task_counter = SharedMemoryCounter("completed", create=False, run_id="pipeline")
# ... process task ...
task_counter.value += 1

# Monitor progress
print(f"Progress: {completed.value}/{total_tasks}")
```

## API Compatibility

`SharedMemoryCounter` is designed to be a drop-in replacement for `multiprocessing.Value`:

```python
# Old way (not picklable)
counter = multiprocessing.Value('i', 0)
with counter.get_lock():
    counter.value += 1

# New way (picklable and named)
counter = SharedMemoryCounter("my_counter", create=True, initial_value=0)
with counter.get_lock():  # No-op for compatibility
    counter.value += 1
```

## Implementation Notes

- Uses `multiprocessing.shared_memory` for efficient cross-process communication
- Stores values as 4-byte signed integers (supports -2,147,483,648 to 2,147,483,647)
- Each counter uses exactly 4 bytes of shared memory
- Counter names are automatically prefixed with run_id for isolation
- Proper cleanup with `close()` and `unlink()` methods
- Thread-safe and process-safe operations on the `value` property

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=shared_counter

# Type checking
uv run mypy .

# Linting
uv run ruff check .
```

## License

MIT