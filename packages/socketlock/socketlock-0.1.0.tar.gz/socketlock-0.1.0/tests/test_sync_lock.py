"""Tests for the SocketLock (synchronous) class."""

import os
import threading
import time

import pytest

from socketlock import SocketLock


def test_basic_lock_acquisition():
    """Test basic lock acquisition and release."""
    lock = SocketLock("test_sync_basic")

    lock.acquire()
    assert lock.port is not None
    assert lock.pid == os.getpid()

    lock.release()
    assert lock.port is None
    assert lock.pid is None


def test_context_manager():
    """Test sync context manager interface."""
    with SocketLock("test_sync_context") as lock:
        assert lock.port is not None
        assert lock.pid == os.getpid()

    # After context exit, lock should be released
    assert lock.port is None
    assert lock.pid is None


def test_concurrent_acquisition_blocked():
    """Test that concurrent acquisition is properly blocked."""
    lock1 = SocketLock("test_sync_concurrent")
    lock2 = SocketLock("test_sync_concurrent")

    # First lock should succeed
    lock1.acquire()

    # Second lock should fail
    with pytest.raises(RuntimeError) as exc_info:
        lock2.acquire()

    # Error message should include PID and port
    error_msg = str(exc_info.value)
    assert str(os.getpid()) in error_msg
    assert str(lock1.port) in error_msg

    lock1.release()


def test_try_acquire():
    """Test non-blocking lock acquisition."""
    lock1 = SocketLock("test_sync_try")
    lock2 = SocketLock("test_sync_try")

    # First lock should succeed
    assert lock1.try_acquire() is True

    # Second lock should fail without blocking
    assert lock2.try_acquire() is False

    lock1.release()

    # Now second lock should succeed
    assert lock2.try_acquire() is True
    lock2.release()


def test_lock_info():
    """Test getting lock information."""
    lock1 = SocketLock("test_sync_info")
    lock2 = SocketLock("test_sync_info")

    # No lock initially
    info = lock2.get_lock_info()
    assert info is None

    # Acquire lock
    lock1.acquire()

    # Now we should get lock info
    info = lock2.get_lock_info()
    assert info is not None
    assert info["pid"] == os.getpid()
    assert info["port"] == lock1.port
    assert info["name"] == "test_sync_info"
    assert "timestamp" in info

    lock1.release()


def test_threaded_lock_attempts():
    """Test lock behavior with multiple threads."""
    lock_name = "test_sync_threaded"
    results = []

    def try_lock():
        lock = SocketLock(lock_name)
        try:
            lock.acquire()
            results.append(True)
            time.sleep(0.5)  # Hold lock briefly
            lock.release()
        except RuntimeError:
            results.append(False)

    # Create multiple threads
    threads = [threading.Thread(target=try_lock) for _ in range(3)]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for all to complete
    for t in threads:
        t.join()

    # Only one should have succeeded
    assert sum(results) == 1
    assert results.count(False) == 2


def test_custom_lock_directory():
    """Test using a custom lock directory."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        lock = SocketLock("test_sync_custom", lock_dir=tmpdir)
        lock.acquire()

        # Lock file should be in custom directory
        lock_file = lock._async_lock._lock_file
        assert str(lock_file.parent) == tmpdir
        assert lock_file.exists()

        lock.release()


def test_lock_reacquisition():
    """Test that a lock can be reacquired after release."""
    lock = SocketLock("test_sync_reacquire")

    # First acquisition
    lock.acquire()
    port1 = lock.port
    lock.release()

    # Second acquisition
    lock.acquire()
    port2 = lock.port
    lock.release()

    # Should work both times (ports may differ)
    assert port1 is not None
    assert port2 is not None


def test_nested_context_managers_fail():
    """Test that nested context managers with same lock fail appropriately."""
    with SocketLock("test_sync_nested") as lock1:
        assert lock1.port is not None

        # Trying to acquire same lock should fail
        lock2 = SocketLock("test_sync_nested")
        with pytest.raises(RuntimeError):
            lock2.acquire()