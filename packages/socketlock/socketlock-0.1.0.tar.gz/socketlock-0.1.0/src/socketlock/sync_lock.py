"""Synchronous wrapper for the async socket lock.

This module provides a synchronous interface to the async socket lock
for applications that don't use asyncio.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict, Optional

from .async_lock import AsyncSocketLock


# Global event loop for sync locks to ensure thread safety
_global_loop: Optional[asyncio.AbstractEventLoop] = None
_global_loop_thread: Optional[threading.Thread] = None
_global_loop_lock = threading.Lock()


def _get_global_loop() -> asyncio.AbstractEventLoop:
    """Get or create the global event loop for sync locks."""
    global _global_loop, _global_loop_thread

    with _global_loop_lock:
        if _global_loop is None or not _global_loop.is_running():
            _global_loop = asyncio.new_event_loop()

            def run_loop():
                asyncio.set_event_loop(_global_loop)
                _global_loop.run_forever()

            _global_loop_thread = threading.Thread(target=run_loop, daemon=True)
            _global_loop_thread.start()

            # Wait for loop to start
            while not _global_loop.is_running():
                pass

    return _global_loop


class SocketLock:
    """Synchronous wrapper for AsyncSocketLock.

    This class provides a synchronous interface to the async socket lock,
    making it easy to use in non-async applications. Thread-safe by using
    a global event loop shared across all instances.
    """

    def __init__(
        self,
        name: str,
        lock_dir: Optional[str] = None,
        timeout: int = 21600,  # 6 hours default
        signature_seed: Optional[str] = None,
    ) -> None:
        """Initialize the synchronous socket lock.

        Args:
            name: Name of the lock (used for lock file naming)
            lock_dir: Directory to store lock files (defaults to system temp)
            timeout: Stale lock timeout in seconds (default: 6 hours)
            signature_seed: Custom seed for handshake signature (optional)
        """
        self._async_lock = AsyncSocketLock(name, lock_dir, timeout, signature_seed)

    @property
    def port(self) -> Optional[int]:
        """Get the port number if lock is acquired."""
        return self._async_lock.port

    @property
    def pid(self) -> Optional[int]:
        """Get the process ID if lock is acquired."""
        return self._async_lock.pid

    def _run_async(self, coro):
        """Run an async coroutine in the global loop."""
        loop = _get_global_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()

    def acquire(self) -> None:
        """Acquire the process lock.

        Raises:
            RuntimeError: If another instance is already running or lock fails
        """
        self._run_async(self._async_lock.acquire())

    def try_acquire(self) -> bool:
        """Try to acquire the lock without blocking.

        Returns:
            True if lock was acquired, False if already held
        """
        return self._run_async(self._async_lock.try_acquire())

    def release(self) -> None:
        """Release the process lock."""
        self._run_async(self._async_lock.release())

    def get_lock_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current lock if one exists.

        Returns:
            Dictionary with lock info (port, pid, timestamp) or None if no valid lock
        """
        return self._run_async(self._async_lock.get_lock_info())

    def __enter__(self) -> "SocketLock":
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.release()