"""socketlock - A robust, secure, and async-friendly process lock using TCP sockets.

This package provides process locking using TCP sockets with application-level
handshake verification for security. It offers both async and sync interfaces.
"""

from .async_lock import AsyncSocketLock
from .sync_lock import SocketLock

__version__ = "0.1.0"
__all__ = ["AsyncSocketLock", "SocketLock"]