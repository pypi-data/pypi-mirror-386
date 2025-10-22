#!/usr/bin/env python3
"""Example demonstrating concurrent process protection using socketlock.

Run multiple instances of this script simultaneously to see the lock in action.
"""

import sys
import time
from random import randint

from socketlock import SocketLock


def protected_task(process_id: str):
    """A task that should only run in one process at a time."""
    lock = SocketLock("critical-section")

    print(f"[{process_id}] Attempting to acquire lock...")

    try:
        lock.acquire()
        print(f"[{process_id}] ✓ Lock acquired on port {lock.port}")
        print(f"[{process_id}] Starting critical work...")

        # Simulate some important work
        for i in range(5):
            print(f"[{process_id}] Working... {i+1}/5")
            time.sleep(1)

        print(f"[{process_id}] Work completed!")

    except RuntimeError as e:
        print(f"[{process_id}] ✗ Could not acquire lock: {e}")
        print(f"[{process_id}] Another instance is running. Exiting.")
        return False

    finally:
        lock.release()
        print(f"[{process_id}] Lock released")

    return True


def main():
    """Main entry point."""
    # Generate a unique ID for this process instance
    process_id = f"Process-{randint(1000, 9999)}"

    print(f"Starting {process_id}")
    print("=" * 50)

    success = protected_task(process_id)

    if success:
        print(f"\n[{process_id}] ✓ Task completed successfully")
    else:
        print(f"\n[{process_id}] ℹ Task skipped (another instance is running)")

    print("=" * 50)


if __name__ == "__main__":
    main()