"""Tests for SharedMemoryCounter."""

import multiprocessing as mp
import time
from multiprocessing.context import BaseContext

import pytest_check as check

from shared_counter import SharedMemoryCounter


def test_counter_creation_and_cleanup():
    """Test that a counter can be created and unlinked."""
    run_id = f"test_creation_{time.time()}"
    counter = SharedMemoryCounter(name="test_counter", create=True, run_id=run_id, initial_value=5)
    check.is_not_none(counter)
    check.equal(counter.value, 5)
    counter.unlink()


def test_read_and_write():
    """Test basic read and write operations."""
    run_id = f"test_read_write_{time.time()}"
    counter = SharedMemoryCounter(name="test_counter", create=True, run_id=run_id, initial_value=10)
    try:
        # Read initial value
        check.equal(counter.value, 10)

        # Write new value
        counter.value = 20
        check.equal(counter.value, 20)

        # Increment
        counter.value += 5
        check.equal(counter.value, 25)

        # Decrement
        counter.value -= 3
        check.equal(counter.value, 22)
    finally:
        counter.unlink()


def test_get_lock_compatibility():
    """Test that get_lock() returns a usable context manager."""
    run_id = f"test_lock_{time.time()}"
    counter = SharedMemoryCounter(name="test_counter", create=True, run_id=run_id, initial_value=0)
    try:
        # Should work with context manager (even though it's a no-op)
        with counter.get_lock():
            counter.value += 1

        check.equal(counter.value, 1)
    finally:
        counter.unlink()


def _worker_process(run_id: str, counter_name: str, num_increments: int, ctx: BaseContext):
    """Target for worker process in cross-process test."""
    counter = SharedMemoryCounter(name=counter_name, create=False, run_id=run_id)

    for _ in range(num_increments):
        with counter.get_lock():
            counter.value += 1


def test_cross_process_counter():
    """Test that counter works across processes."""
    run_id = f"test_cross_process_{time.time()}"
    counter_name = "cross_process_counter"
    num_workers = 3
    increments_per_worker = 10
    ctx = mp.get_context("fork")

    # Create counter in main process
    counter = SharedMemoryCounter(name=counter_name, create=True, run_id=run_id, initial_value=0)

    # Start worker processes
    workers = []
    for i in range(num_workers):
        worker = ctx.Process(target=_worker_process, args=(run_id, counter_name, increments_per_worker, ctx))
        worker.start()
        workers.append(worker)

    try:
        # Wait for all workers to finish
        for worker in workers:
            worker.join(timeout=2)

        # Check final value
        expected = num_workers * increments_per_worker
        check.equal(counter.value, expected)

    finally:
        for worker in workers:
            if worker.is_alive():
                worker.kill()
        counter.unlink()


def test_pickle_and_reconnect():
    """Test that counters can be pickled and reconnected."""
    import pickle

    run_id = f"test_pickle_{time.time()}"
    counter = SharedMemoryCounter(name="test_counter", create=True, run_id=run_id, initial_value=42)

    try:
        # Pickle and unpickle
        pickled = pickle.dumps(counter)
        counter2 = pickle.loads(pickled)

        # Should have same value
        check.equal(counter2.value, 42)

        # Modify via new instance
        counter2.value = 100

        # Original should also see the change
        check.equal(counter.value, 100)

    finally:
        counter.unlink()


def test_negative_values():
    """Test that counter handles negative values correctly."""
    run_id = f"test_negative_{time.time()}"
    counter = SharedMemoryCounter(name="test_counter", create=True, run_id=run_id, initial_value=5)
    try:
        counter.value -= 10
        check.equal(counter.value, -5)

        counter.value += 3
        check.equal(counter.value, -2)
    finally:
        counter.unlink()