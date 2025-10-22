"""Tests for race conditions and atomic lock acquisition."""

import asyncio
import os

import pytest

from socketlock import AsyncSocketLock


@pytest.mark.asyncio
async def test_no_race_condition():
    """Test that only one instance can acquire lock even with concurrent attempts."""
    lock_name = "test_race"
    num_instances = 10

    async def try_acquire(instance_id):
        """Try to acquire a lock with given instance ID."""
        lock = AsyncSocketLock(lock_name)
        try:
            await lock.acquire()
            # If we got here, we acquired the lock
            await asyncio.sleep(0.1)  # Hold briefly
            await lock.release()
            return True
        except RuntimeError:
            return False

    # Launch all instances concurrently
    tasks = [try_acquire(i) for i in range(num_instances)]
    results = await asyncio.gather(*tasks)

    # Exactly one should succeed
    assert sum(results) == 1, f"Expected 1 success, got {sum(results)}"
    assert results.count(False) == num_instances - 1


@pytest.mark.asyncio
async def test_rapid_succession():
    """Test rapid lock acquisition when one is already held."""
    lock_name = "test_rapid"

    # First, acquire and hold the lock
    main_lock = AsyncSocketLock(lock_name)
    await main_lock.acquire()

    # Now try multiple rapid attempts while lock is held
    async def try_acquire():
        lock = AsyncSocketLock(lock_name)
        return await lock.try_acquire()

    # All should fail since main_lock holds it
    tasks = [try_acquire() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # All attempts should fail
    assert all(r is False for r in results)

    # Release main lock
    await main_lock.release()

    # Now one should succeed
    final_lock = AsyncSocketLock(lock_name)
    assert await final_lock.try_acquire() is True
    await final_lock.release()


@pytest.mark.asyncio
async def test_handshake_prevents_imposters():
    """Test that handshake protocol prevents false lock holders."""
    lock = AsyncSocketLock("test_imposter", signature_seed="real_app")

    # Acquire the lock
    await lock.acquire()
    port = lock.port

    # Create another lock with different signature
    imposter = AsyncSocketLock("test_imposter", signature_seed="fake_app")

    # Imposter should not be able to verify the lock
    assert await imposter._verify_lock_holder(port) is False

    # But same signature should work
    legit = AsyncSocketLock("test_imposter", signature_seed="real_app")
    assert await legit._verify_lock_holder(port) is True

    await lock.release()


@pytest.mark.asyncio
async def test_atomic_file_creation():
    """Test that file creation is truly atomic."""
    lock_name = "test_atomic"
    successes = []

    async def try_atomic_acquire(instance_id):
        """Attempt to acquire lock atomically."""
        lock = AsyncSocketLock(lock_name)
        try:
            # This should be atomic - only one can succeed
            await lock.acquire()
            successes.append(instance_id)
            await asyncio.sleep(0.1)
            await lock.release()
            return True
        except RuntimeError:
            return False

    # Run many concurrent attempts
    tasks = [try_atomic_acquire(i) for i in range(20)]
    results = await asyncio.gather(*tasks)

    # Exactly one should succeed
    assert len(successes) == 1
    assert sum(results) == 1


@pytest.mark.asyncio
async def test_no_toctou_vulnerability():
    """Test that there's no Time-of-Check-Time-of-Use vulnerability."""
    lock_name = "test_toctou"

    # This test ensures we don't check for lock existence
    # before trying to acquire it atomically

    async def acquire_without_check():
        """Acquire lock without pre-checking."""
        lock = AsyncSocketLock(lock_name)
        # The implementation should NOT check first then acquire
        # It should try atomic acquisition immediately
        try:
            await lock.acquire()
            await asyncio.sleep(0.1)
            await lock.release()
            return "acquired"
        except RuntimeError as e:
            # Should get detailed error AFTER atomic attempt fails
            if "PID" in str(e) and "Port" in str(e):
                return "blocked_with_info"
            return "blocked_no_info"

    # Launch multiple attempts
    tasks = [acquire_without_check() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # One should acquire, others should be blocked with info
    assert results.count("acquired") == 1
    assert results.count("blocked_with_info") == 4
    assert results.count("blocked_no_info") == 0