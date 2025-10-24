"""
Shared memory event implementation for cross-process synchronization.

This event can be created by name and accessed from any process, solving the
problem of multiprocessing.Event not being picklable.
"""

import time
from multiprocessing import shared_memory
from typing import Any


class SharedMemoryEvent:
    """
    An event backed by shared memory that can be accessed by name from any process.

    This solves the pickling problem with multiprocessing.Event - instead of trying
    to pickle the event object, we just store the event name and each process connects
    to the same shared memory event by name.

    Uses a simple flag (0 = clear, 1 = set) in shared memory.

    Usage:
        # Process A creates the event
        event = SharedMemoryEvent(name="ready", create=True, run_id="app1")

        # Process B connects to the same event
        event = SharedMemoryEvent(name="ready", create=False, run_id="app1")

        # Process A signals
        event.set()

        # Process B waits
        event.wait()
    """

    def __init__(self, name: str, create: bool = False, run_id: str = ""):
        """
        Initialize a shared memory event.

        Args:
            name: Event name (used to identify the shared memory segment)
            create: Whether to create a new event or connect to existing
            run_id: Run identifier for namespacing
        """
        self.name = name
        self.run_id = run_id

        # Shared memory name for the event
        shm_name = f"{run_id}-{name}-event" if run_id else f"{name}-event"

        if create:
            # Create new shared memory for the event (1 byte for the flag)
            self._shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1)
            # Initialize to 0 (clear)
            self._shm.buf[0] = 0
        else:
            # Connect to existing shared memory event
            self._shm = shared_memory.SharedMemory(name=shm_name, create=False, size=1)

    def set(self) -> None:
        """Set the event (wake up waiters)."""
        self._shm.buf[0] = 1

    def clear(self) -> None:
        """Clear the event."""
        self._shm.buf[0] = 0

    def is_set(self) -> bool:
        """Check if the event is set."""
        return self._shm.buf[0] == 1

    def wait(self, timeout: float | None = None) -> bool:
        """
        Wait for the event to be set.

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if event was set, False if timeout
        """
        start_time = time.time() if timeout else None

        while self._shm.buf[0] == 0:
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False

            # Brief sleep to avoid busy-waiting
            # TODO: Use futex for efficient waiting instead of polling
            time.sleep(0.001)  # 1ms

        return True

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
            shm_name = f"{self.run_id}-{self.name}-event" if self.run_id else f"{self.name}-event"
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

        # Reconnect to the same shared memory event
        shm_name = f"{self.run_id}-{self.name}-event" if self.run_id else f"{self.name}-event"
        self._shm = shared_memory.SharedMemory(name=shm_name, create=False, size=1)
