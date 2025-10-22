"""Tests for the AsyncSocketLock class."""

import asyncio
import os
import time
from pathlib import Path

import pytest

from socketlock import AsyncSocketLock


@pytest.mark.asyncio
async def test_basic_lock_acquisition():
    """Test basic lock acquisition and release."""
    lock = AsyncSocketLock("test_basic")

    await lock.acquire()
    assert lock.port is not None
    assert lock.pid == os.getpid()

    await lock.release()
    assert lock.port is None
    assert lock.pid is None


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager interface."""
    async with AsyncSocketLock("test_context") as lock:
        assert lock.port is not None
        assert lock.pid == os.getpid()

    # After context exit, lock should be released
    assert lock.port is None
    assert lock.pid is None


@pytest.mark.asyncio
async def test_concurrent_acquisition_blocked():
    """Test that concurrent acquisition is properly blocked."""
    lock1 = AsyncSocketLock("test_concurrent")
    lock2 = AsyncSocketLock("test_concurrent")

    # First lock should succeed
    await lock1.acquire()

    # Second lock should fail
    with pytest.raises(RuntimeError) as exc_info:
        await lock2.acquire()

    # Error message should include PID and port
    error_msg = str(exc_info.value)
    assert str(os.getpid()) in error_msg
    assert str(lock1.port) in error_msg

    await lock1.release()


@pytest.mark.asyncio
async def test_try_acquire():
    """Test non-blocking lock acquisition."""
    lock1 = AsyncSocketLock("test_try")
    lock2 = AsyncSocketLock("test_try")

    # First lock should succeed
    assert await lock1.try_acquire() is True

    # Second lock should fail without blocking
    assert await lock2.try_acquire() is False

    await lock1.release()

    # Now second lock should succeed
    assert await lock2.try_acquire() is True
    await lock2.release()


@pytest.mark.asyncio
async def test_lock_info():
    """Test getting lock information."""
    lock1 = AsyncSocketLock("test_info")
    lock2 = AsyncSocketLock("test_info")

    # No lock initially
    info = await lock2.get_lock_info()
    assert info is None

    # Acquire lock
    await lock1.acquire()

    # Now we should get lock info
    info = await lock2.get_lock_info()
    assert info is not None
    assert info["pid"] == os.getpid()
    assert info["port"] == lock1.port
    assert info["name"] == "test_info"
    assert "timestamp" in info

    await lock1.release()


@pytest.mark.asyncio
async def test_stale_lock_cleanup():
    """Test that stale locks are automatically cleaned up."""
    # Create a lock with very short timeout
    lock1 = AsyncSocketLock("test_stale", timeout=1)
    await lock1.acquire()

    # Manually modify timestamp to make it stale
    lock_file = lock1._lock_file
    import json
    with open(lock_file, "r") as f:
        info = json.load(f)
    info["timestamp"] = time.time() - 10  # 10 seconds old
    with open(lock_file, "w") as f:
        json.dump(info, f)

    await lock1.release()

    # New lock should succeed as stale lock is cleaned
    lock2 = AsyncSocketLock("test_stale", timeout=1)
    await lock2.acquire()
    assert lock2.port is not None
    await lock2.release()


@pytest.mark.asyncio
async def test_custom_lock_directory():
    """Test using a custom lock directory."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        lock = AsyncSocketLock("test_custom", lock_dir=tmpdir)
        await lock.acquire()

        # Lock file should be in custom directory
        assert lock._lock_file.parent == Path(tmpdir)
        assert lock._lock_file.exists()

        await lock.release()


@pytest.mark.asyncio
async def test_multiple_concurrent_attempts():
    """Test multiple concurrent lock acquisition attempts."""
    locks = [AsyncSocketLock("test_multiple") for _ in range(5)]

    # Try to acquire all locks concurrently
    results = await asyncio.gather(
        *[lock.try_acquire() for lock in locks],
        return_exceptions=False
    )

    # Only one should succeed
    assert sum(results) == 1

    # Release the acquired lock
    for i, result in enumerate(results):
        if result:
            await locks[i].release()
            break


@pytest.mark.asyncio
async def test_handshake_verification():
    """Test that handshake verification works correctly."""
    lock = AsyncSocketLock("test_handshake")
    await lock.acquire()

    # Verify our own lock succeeds
    assert await lock._verify_lock_holder(lock.port) is True

    # Non-existent port fails
    assert await lock._verify_lock_holder(65535) is False

    await lock.release()


@pytest.mark.asyncio
async def test_lock_reacquisition():
    """Test that a lock can be reacquired after release."""
    lock = AsyncSocketLock("test_reacquire")

    # First acquisition
    await lock.acquire()
    port1 = lock.port
    await lock.release()

    # Second acquisition
    await lock.acquire()
    port2 = lock.port
    await lock.release()

    # Should work both times (ports may differ)
    assert port1 is not None
    assert port2 is not None