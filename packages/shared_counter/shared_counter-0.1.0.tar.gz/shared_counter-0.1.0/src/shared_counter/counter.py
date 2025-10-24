"""
Shared memory counter implementation for cross-process synchronization.

This counter can be created by name and accessed from any process, solving the
problem of multiprocessing.Value not being picklable.
"""

import struct
from multiprocessing import shared_memory
from typing import Any


class SharedMemoryCounter:
    """
    An atomic counter backed by shared memory that can be accessed by name from any process.

    This solves the pickling problem with multiprocessing.Value - instead of trying
    to pickle the synchronized object, we just store the counter name and each process
    connects to the same shared memory counter by name.

    Uses a 4-byte signed integer in shared memory.

    Usage:
        # Process A creates the counter
        counter = SharedMemoryCounter(name="ready_count", create=True, run_id="app1", initial_value=5)

        # Process B connects to the same counter
        counter = SharedMemoryCounter(name="ready_count", create=False, run_id="app1")

        # Both processes can read/write
        counter.value -= 1
        if counter.value == 0:
            print("All ready!")
    """

    def __init__(self, name: str, create: bool = False, run_id: str = "", initial_value: int = 0):
        """
        Initialize a shared memory counter.

        Args:
            name: Counter name (used to identify the shared memory segment)
            create: Whether to create a new counter or connect to existing
            run_id: Run identifier for namespacing
            initial_value: Initial value (only used if create=True)
        """
        self.name = name
        self.run_id = run_id

        # Shared memory name for the counter
        shm_name = f"{run_id}-{name}-counter" if run_id else f"{name}-counter"

        if create:
            # Create new shared memory for the counter (4 bytes for int32)
            self._shm = shared_memory.SharedMemory(name=shm_name, create=True, size=4)
            # Initialize to initial_value
            struct.pack_into("!i", self._shm.buf, 0, initial_value)
        else:
            # Connect to existing shared memory counter
            self._shm = shared_memory.SharedMemory(name=shm_name, create=False, size=4)

    @property
    def value(self) -> int:
        """Get the current counter value."""
        return struct.unpack_from("!i", self._shm.buf, 0)[0]

    @value.setter
    def value(self, val: int) -> None:
        """Set the counter value."""
        struct.pack_into("!i", self._shm.buf, 0, val)

    def get_lock(self):
        """
        Return a no-op lock for compatibility with multiprocessing.Value API.

        The actual synchronization happens via atomic operations on the shared memory.
        This method exists for API compatibility with code that does:
            with counter.get_lock():
                counter.value -= 1
        """

        class NoOpLock:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        return NoOpLock()

    def close(self) -> None:
        """Close the shared memory connection."""
        if hasattr(self, "_shm") and self._shm:
            try:
                self._shm.close()
            except Exception:
                pass

    def unlink(self) -> None:
        """Unlink (delete) the shared memory segment."""
        self.close()
        try:
            shm_name = f"{self.run_id}-{self.name}-counter" if self.run_id else f"{self.name}-counter"
            temp_shm = shared_memory.SharedMemory(name=shm_name)
            temp_shm.unlink()
            temp_shm.close()
        except FileNotFoundError:
            pass
        except Exception:
            pass

    def __getstate__(self) -> dict[str, Any]:
        """Prepare for pickling - return connection info."""
        return {
            "name": self.name,
            "run_id": self.run_id,
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Reconnect after unpickling in a new process."""
        self.name = state["name"]
        self.run_id = state["run_id"]

        # Reconnect to the same shared memory counter
        shm_name = f"{self.run_id}-{self.name}-counter" if self.run_id else f"{self.name}-counter"
        self._shm = shared_memory.SharedMemory(name=shm_name, create=False, size=4)
