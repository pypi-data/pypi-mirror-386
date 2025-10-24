"""Stress tests for SharedMemoryEvent to ensure reliability under concurrent usage."""

import multiprocessing as mp
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest_check as check

from shared_event import SharedMemoryEvent


def _stress_waiter(run_id: str, event_name: str, worker_id: int, result_queue: mp.Queue):
    """Worker that waits for event and reports timing."""
    event = SharedMemoryEvent(name=event_name, create=False, run_id=run_id)

    start_time = time.time()
    success = event.wait(timeout=10.0)
    end_time = time.time()

    result_queue.put({
        'worker_id': worker_id,
        'success': success,
        'wait_time': end_time - start_time,
        'timestamp': end_time
    })


def _stress_setter(run_id: str, event_name: str, delay: float):
    """Worker that sets the event after a delay."""
    time.sleep(delay)
    event = SharedMemoryEvent(name=event_name, create=False, run_id=run_id)
    event.set()


def test_multiple_waiters_single_setter():
    """Test that multiple processes can wait for the same event."""
    run_id = f"stress_multi_wait_{time.time()}"
    event_name = "multi_wait_event"
    num_waiters = 20

    ctx = mp.get_context("fork")
    result_queue = ctx.Queue()

    # Create the event
    event = SharedMemoryEvent(name=event_name, create=True, run_id=run_id)

    try:
        # Start waiter processes
        waiters = []
        for i in range(num_waiters):
            p = ctx.Process(target=_stress_waiter, args=(run_id, event_name, i, result_queue))
            p.start()
            waiters.append(p)

        # Wait a bit to ensure all waiters are waiting
        time.sleep(0.5)

        # Set the event
        set_time = time.time()
        event.set()

        # Collect results
        results = []
        for _ in range(num_waiters):
            result = result_queue.get(timeout=15.0)
            results.append(result)

        # Wait for all processes to finish
        for p in waiters:
            p.join(timeout=2.0)

        # Verify all waiters succeeded
        for result in results:
            check.is_true(result['success'], f"Worker {result['worker_id']} failed to wake up")
            check.less(result['wait_time'], 2.0, f"Worker {result['worker_id']} took too long")
            check.greater_equal(result['timestamp'], set_time, f"Worker {result['worker_id']} woke up before set")

        check.equal(len(results), num_waiters, "Not all waiters reported results")

    finally:
        # Cleanup
        for p in waiters:
            if p.is_alive():
                p.kill()
        event.unlink()


def test_rapid_set_clear_cycles():
    """Test rapid set/clear cycles for race conditions."""
    run_id = f"stress_rapid_{time.time()}"
    event = SharedMemoryEvent(name="rapid_test", create=True, run_id=run_id)

    try:
        # Rapid set/clear cycles
        for i in range(1000):
            event.set()
            check.is_true(event.is_set(), f"Event not set on iteration {i}")

            event.clear()
            check.is_false(event.is_set(), f"Event not cleared on iteration {i}")
    finally:
        event.unlink()


def _threaded_set_clear_worker(event: SharedMemoryEvent, operations: int, results: list):
    """Worker for multithreaded set/clear test."""
    success_count = 0
    for _ in range(operations):
        try:
            if random.choice([True, False]):
                event.set()
            else:
                event.clear()
            success_count += 1
        except Exception as e:
            results.append(f"Error: {e}")
            break
    results.append(f"Completed {success_count} operations")


def test_multithreaded_access():
    """Test concurrent access from multiple threads."""
    run_id = f"stress_threads_{time.time()}"
    event = SharedMemoryEvent(name="thread_test", create=True, run_id=run_id)

    try:
        num_threads = 10
        operations_per_thread = 100
        results = []

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(
                target=_threaded_set_clear_worker,
                args=(event, operations_per_thread, results)
            )
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join(timeout=5.0)

        # Verify no errors occurred
        error_count = sum(1 for r in results if r.startswith("Error"))
        check.equal(error_count, 0, f"Found {error_count} errors in multithreaded access")

    finally:
        event.unlink()


def test_memory_cleanup():
    """Test that creating/destroying many events doesn't leak memory."""
    run_id = f"stress_cleanup_{time.time()}"

    # Create and destroy many events
    for i in range(100):
        event_name = f"cleanup_test_{i}"
        event = SharedMemoryEvent(name=event_name, create=True, run_id=run_id)

        # Do some operations
        event.set()
        check.is_true(event.is_set())
        event.clear()
        check.is_false(event.is_set())

        # Clean up
        event.unlink()


def _timeout_waiter(run_id: str, event_name: str, timeout: float, result_queue: mp.Queue):
    """Worker that waits with timeout."""
    event = SharedMemoryEvent(name=event_name, create=False, run_id=run_id)

    start_time = time.time()
    result = event.wait(timeout=timeout)
    elapsed = time.time() - start_time

    result_queue.put({
        'success': result,
        'elapsed': elapsed,
        'expected_timeout': not result
    })


def test_timeout_accuracy():
    """Test that timeouts are reasonably accurate."""
    run_id = f"stress_timeout_{time.time()}"
    event_name = "timeout_test"
    timeout_duration = 0.5

    ctx = mp.get_context("fork")
    result_queue = ctx.Queue()

    # Create event but don't set it
    event = SharedMemoryEvent(name=event_name, create=True, run_id=run_id)

    try:
        # Start waiter process
        p = ctx.Process(target=_timeout_waiter, args=(run_id, event_name, timeout_duration, result_queue))
        p.start()

        # Get result
        result = result_queue.get(timeout=2.0)
        p.join(timeout=1.0)

        # Verify timeout occurred and timing is reasonable
        check.is_true(result['expected_timeout'], "Wait should have timed out")
        check.greater(result['elapsed'], timeout_duration * 0.9, "Timeout too early")
        check.less(result['elapsed'], timeout_duration * 1.5, "Timeout too late")

    finally:
        if p.is_alive():
            p.kill()
        event.unlink()


def test_cross_process_pickle_reliability():
    """Test that pickling works reliably across processes under stress."""
    import pickle

    run_id = f"stress_pickle_{time.time()}"

    for i in range(50):
        event_name = f"pickle_test_{i}"
        event = SharedMemoryEvent(name=event_name, create=True, run_id=run_id)

        try:
            # Set random state
            if i % 2 == 0:
                event.set()

            # Pickle and unpickle
            pickled = pickle.dumps(event)
            event2 = pickle.loads(pickled)

            # Verify state consistency
            check.equal(event.is_set(), event2.is_set(), f"State mismatch on iteration {i}")

            # Verify operations work on unpickled version
            event2.clear()
            check.is_false(event.is_set(), f"Clear failed on iteration {i}")
            check.is_false(event2.is_set(), f"Clear failed on unpickled version {i}")

        finally:
            event.unlink()