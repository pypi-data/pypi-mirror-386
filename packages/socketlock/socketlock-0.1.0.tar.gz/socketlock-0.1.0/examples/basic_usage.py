#!/usr/bin/env python3
"""Basic usage examples for socketlock."""

import asyncio
import time

from socketlock import AsyncSocketLock, SocketLock


def sync_example():
    """Example using the synchronous interface."""
    print("Synchronous Example")
    print("-" * 40)

    # Using context manager (recommended)
    with SocketLock("my-app") as lock:
        print(f"Lock acquired! PID: {lock.pid}, Port: {lock.port}")
        print("Doing important work...")
        time.sleep(2)
        print("Work completed!")

    print("Lock released automatically\n")


def manual_sync_example():
    """Example using manual lock management."""
    print("Manual Synchronous Example")
    print("-" * 40)

    lock = SocketLock("my-app")

    try:
        lock.acquire()
        print(f"Lock acquired! PID: {lock.pid}, Port: {lock.port}")
        print("Doing important work...")
        time.sleep(2)
        print("Work completed!")
    except RuntimeError as e:
        print(f"Could not acquire lock: {e}")
    finally:
        lock.release()
        print("Lock released\n")


def try_acquire_example():
    """Example using non-blocking acquisition."""
    print("Non-blocking Acquisition Example")
    print("-" * 40)

    lock = SocketLock("my-app")

    if lock.try_acquire():
        print("Got the lock!")
        print("Doing work...")
        time.sleep(1)
        lock.release()
    else:
        print("Lock is busy, will try again later")

    print()


async def async_example():
    """Example using the async interface."""
    print("Asynchronous Example")
    print("-" * 40)

    async with AsyncSocketLock("my-app") as lock:
        print(f"Lock acquired! PID: {lock.pid}, Port: {lock.port}")
        print("Doing async work...")
        await asyncio.sleep(2)
        print("Work completed!")

    print("Lock released automatically\n")


async def check_lock_status():
    """Example checking if a lock is held."""
    print("Lock Status Check")
    print("-" * 40)

    lock = AsyncSocketLock("my-app")
    info = await lock.get_lock_info()

    if info:
        print(f"Lock is currently held:")
        print(f"  PID: {info['pid']}")
        print(f"  Port: {info['port']}")
        print(f"  Acquired: {time.ctime(info['timestamp'])}")
    else:
        print("Lock is available")

    print()


def main():
    """Run all examples."""
    print("=" * 50)
    print("SocketLock Usage Examples")
    print("=" * 50)
    print()

    # Synchronous examples
    sync_example()
    manual_sync_example()
    try_acquire_example()

    # Async examples
    asyncio.run(async_example())
    asyncio.run(check_lock_status())


if __name__ == "__main__":
    main()