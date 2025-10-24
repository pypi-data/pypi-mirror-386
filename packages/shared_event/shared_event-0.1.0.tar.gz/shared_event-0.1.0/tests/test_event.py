"""Tests for SharedMemoryEvent."""

import multiprocessing as mp
import time
from multiprocessing.context import BaseContext

import pytest_check as check

from shared_event import SharedMemoryEvent


def test_event_creation_and_cleanup():
    """Test that an event can be created and unlinked."""
    run_id = f"test_creation_{time.time()}"
    event = SharedMemoryEvent(name="test_event", create=True, run_id=run_id)
    check.is_not_none(event)
    check.is_false(event.is_set())
    event.unlink()


def test_set_and_clear():
    """Test basic set and clear operations."""
    run_id = f"test_set_clear_{time.time()}"
    event = SharedMemoryEvent(name="test_event", create=True, run_id=run_id)
    try:
        # Initially clear
        check.is_false(event.is_set())

        # Set the event
        event.set()
        check.is_true(event.is_set())

        # Clear the event
        event.clear()
        check.is_false(event.is_set())
    finally:
        event.unlink()


def test_wait_timeout():
    """Test that wait returns False on timeout."""
    run_id = f"test_wait_timeout_{time.time()}"
    event = SharedMemoryEvent(name="test_event", create=True, run_id=run_id)
    try:
        # Event is not set, wait should timeout
        result = event.wait(timeout=0.1)
        check.is_false(result)
    finally:
        event.unlink()


def test_wait_success():
    """Test that wait returns True when event is set."""
    run_id = f"test_wait_success_{time.time()}"
    event = SharedMemoryEvent(name="test_event", create=True, run_id=run_id)
    try:
        # Set the event
        event.set()

        # Wait should return immediately
        result = event.wait(timeout=1.0)
        check.is_true(result)
    finally:
        event.unlink()


def _waiter_process(run_id: str, event_name: str, result_queue: mp.Queue, ctx: BaseContext):
    """Target for waiter process in cross-process test."""
    event = SharedMemoryEvent(name=event_name, create=False, run_id=run_id)

    # Wait for event to be set
    start = time.time()
    result = event.wait(timeout=5.0)
    elapsed = time.time() - start

    result_queue.put({"result": result, "elapsed": elapsed})


def test_cross_process_signaling():
    """Test that events work across processes."""
    run_id = f"test_cross_process_{time.time()}"
    event_name = "cross_process_event"
    ctx = mp.get_context("fork")
    result_queue = ctx.Queue()

    # Create event in main process
    event = SharedMemoryEvent(name=event_name, create=True, run_id=run_id)

    # Start waiter process
    waiter = ctx.Process(target=_waiter_process, args=(run_id, event_name, result_queue, ctx))
    waiter.start()

    try:
        # Wait a bit to ensure waiter is waiting
        time.sleep(0.1)

        # Set the event
        event.set()

        # Get result from waiter
        result_data = result_queue.get(timeout=2.0)

        check.is_true(result_data["result"])
        check.less(result_data["elapsed"], 1.0)  # Should wake up quickly

    finally:
        waiter.join(timeout=1)
        if waiter.is_alive():
            waiter.kill()
        event.unlink()


def test_pickle_and_reconnect():
    """Test that events can be pickled and reconnected."""
    import pickle

    run_id = f"test_pickle_{time.time()}"
    event = SharedMemoryEvent(name="test_event", create=True, run_id=run_id)

    try:
        # Set the event
        event.set()

        # Pickle and unpickle
        pickled = pickle.dumps(event)
        event2 = pickle.loads(pickled)

        # Should still be set
        check.is_true(event2.is_set())

        # Clear via new instance
        event2.clear()

        # Original should also see it as clear
        check.is_false(event.is_set())

    finally:
        event.unlink()