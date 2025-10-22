"""Async socket-based process lock implementation.

This module provides an async-friendly process lock using TCP sockets
with application-level handshake verification for security.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AsyncSocketLock:
    """Async process lock using dynamic socket binding with handshake verification.

    This implementation uses asyncio server for the lock mechanism, with
    atomic file creation to prevent race conditions. The server is the actual lock -
    the file is used both for atomic acquisition and port discovery.

    When a process crashes, the OS automatically releases the socket,
    preventing stale lock issues common with PID files.

    To prevent imposter processes from blocking legitimate ones, we implement an
    application-level handshake protocol. Only processes that respond
    correctly to our challenge are considered valid lock holders.
    """

    # Default handshake protocol constants
    DEFAULT_CHALLENGE = b"SOCKETLOCK_CHECK"
    DEFAULT_RESPONSE_PREFIX = b"SOCKETLOCK_ACTIVE:"
    HANDSHAKE_TIMEOUT = 1.0  # seconds

    def __init__(
        self,
        name: str,
        lock_dir: Optional[str] = None,
        timeout: int = 21600,  # 6 hours default
        signature_seed: Optional[str] = None,
    ) -> None:
        """Initialize the async socket lock.

        Args:
            name: Name of the lock (used for lock file naming)
            lock_dir: Directory to store lock files (defaults to system temp)
            timeout: Stale lock timeout in seconds (default: 6 hours)
            signature_seed: Custom seed for handshake signature (optional)
        """
        self._name = name
        self._server: Optional[asyncio.Server] = None
        self._port: Optional[int] = None
        self._pid: Optional[int] = None
        self._lock_acquired = False
        self._timeout = timeout

        # Generate a unique response for this lock
        seed = signature_seed or f"socketlock_{name}"
        self._lock_signature = hashlib.sha256(seed.encode()).hexdigest()[:16].encode()

        # Set up lock directory
        if lock_dir:
            self._lock_dir = Path(lock_dir)
            self._lock_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._lock_dir = Path(tempfile.gettempdir())

        # Lock file stores port number for discovery
        self._lock_file = self._lock_dir / f".{name}.lock"

        logger.debug(f"Initializing AsyncSocketLock for '{name}' at {self._lock_file}")

    @property
    def port(self) -> Optional[int]:
        """Get the port number if lock is acquired."""
        return self._port

    @property
    def pid(self) -> Optional[int]:
        """Get the process ID if lock is acquired."""
        return self._pid

    async def _cleanup(self) -> None:
        """Clean up the server and lock file."""
        if self._server:
            try:
                self._server.close()
                await self._server.wait_closed()
                logger.debug(f"Server released (was on port {self._port})")
            except Exception as e:
                logger.error(f"Error closing server: {e}")
            finally:
                self._server = None

        if self._lock_acquired and self._lock_file.exists():
            try:
                self._lock_file.unlink()
                logger.debug("Lock file cleaned up")
            except OSError as e:
                logger.error(f"Error removing lock file: {e}")

        self._port = None
        self._pid = None
        self._lock_acquired = False

    async def _handle_verification(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle lock verification requests.

        This coroutine responds to handshake challenges, proving that
        this is a legitimate process holding the lock.
        """
        addr = writer.get_extra_info("peername")

        try:
            challenge = await asyncio.wait_for(
                reader.read(64), timeout=self.HANDSHAKE_TIMEOUT
            )

            if challenge == self.DEFAULT_CHALLENGE:
                response = self.DEFAULT_RESPONSE_PREFIX + self._lock_signature
                writer.write(response)
                await writer.drain()
                logger.debug(f"Responded to lock verification from {addr}")
            else:
                logger.debug(f"Invalid challenge from {addr}: {challenge}")

        except asyncio.TimeoutError:
            logger.debug(f"Verification timeout from {addr}")
        except Exception as e:
            logger.debug(f"Error handling verification from {addr}: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def acquire(self) -> None:
        """Acquire the process lock using async server with handshake verification.

        Uses atomic file creation to prevent race conditions where multiple
        instances might try to acquire the lock simultaneously.

        Raises:
            RuntimeError: If another instance is already running or lock fails
        """
        # Try to atomically create the lock file
        # NOTE: We do NOT check for existing lock first to avoid TOCTOU bugs
        tmp_file = self._lock_file.with_suffix(f".tmp.{os.getpid()}")

        try:
            # Start async server with dynamic port allocation
            self._server = await asyncio.start_server(
                self._handle_verification,
                "127.0.0.1",
                0,  # OS assigns available port
            )

            # Get the actual port that was assigned
            sockets = self._server.sockets
            if sockets:
                self._port = sockets[0].getsockname()[1]
            else:
                raise RuntimeError("Failed to get server socket")

            self._pid = os.getpid()

            # Prepare lock info
            lock_info = {
                "port": self._port,
                "pid": self._pid,
                "timestamp": time.time(),
                "name": self._name,
            }

            # Write to temp file first
            with open(tmp_file, "w") as f:
                json.dump(lock_info, f, indent=2)

            # Try to atomically move to the real location
            if sys.platform == "win32":
                # Windows: Use O_CREAT | O_EXCL for exclusive creation
                try:
                    fd = os.open(str(self._lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.close(fd)
                    # If we got here, we have the lock
                    self._lock_file.unlink()  # Remove empty file
                    tmp_file.rename(self._lock_file)
                    self._lock_acquired = True
                except FileExistsError:
                    # Another instance got the lock first
                    await self._handle_lock_exists(tmp_file)
            else:
                # Unix: Use os.link for atomic operation
                try:
                    os.link(tmp_file, self._lock_file)
                    tmp_file.unlink()
                    self._lock_acquired = True
                except FileExistsError:
                    # Another instance got the lock first
                    await self._handle_lock_exists(tmp_file)

            if self._lock_acquired:
                logger.info(f"Lock acquired on port {self._port}")

        except Exception as e:
            # Clean up on any failure
            if tmp_file.exists():
                tmp_file.unlink()
            if self._server:
                self._server.close()
                await self._server.wait_closed()
                self._server = None
                self._port = None
                self._pid = None
            raise RuntimeError(f"Failed to acquire lock: {e}")

    async def _handle_lock_exists(self, tmp_file: Path) -> None:
        """Handle the case when lock file already exists."""
        tmp_file.unlink()

        # Close our server since we didn't get the lock
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            self._port = None
            self._pid = None

        # Check if the other instance is valid
        existing_lock = await self._check_existing_lock_with_info()
        if existing_lock:
            pid = existing_lock.get("pid", "unknown")
            port = existing_lock.get("port", "unknown")
            raise RuntimeError(
                f"Another {self._name} instance is already running "
                f"(PID: {pid}, Port: {port})"
            )
        else:
            # The other instance died between creating file and starting server
            # Try again recursively
            await self.acquire()

    async def try_acquire(self) -> bool:
        """Try to acquire the lock without blocking.

        Returns:
            True if lock was acquired, False if already held
        """
        try:
            await self.acquire()
            return True
        except RuntimeError:
            return False

    async def release(self) -> None:
        """Release the process lock."""
        await self._cleanup()

    async def _verify_lock_holder(self, port: int) -> bool:
        """Verify that the process on the port is a legitimate lock holder.

        Args:
            port: Port number to verify

        Returns:
            True if the port has a valid lock holder, False otherwise
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", port),
                timeout=self.HANDSHAKE_TIMEOUT,
            )

            # Send challenge
            writer.write(self.DEFAULT_CHALLENGE)
            await writer.drain()

            # Wait for response
            response = await asyncio.wait_for(
                reader.read(64), timeout=self.HANDSHAKE_TIMEOUT
            )

            # Clean up connection
            writer.close()
            await writer.wait_closed()

            # Verify response
            expected_response = self.DEFAULT_RESPONSE_PREFIX + self._lock_signature
            if response == expected_response:
                logger.debug(f"Port {port} verified as legitimate lock")
                return True
            else:
                logger.warning(f"Port {port} failed verification")
                return False

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            logger.debug(f"Could not verify port {port}: {e}")
            return False

    async def _check_existing_lock_with_info(self) -> Optional[Dict[str, Any]]:
        """Check if another instance is already running and return its info.

        Returns:
            Dictionary with lock info if another valid instance is running, None otherwise
        """
        if not self._lock_file.exists():
            return None

        try:
            with open(self._lock_file, "r") as f:
                info = json.load(f)

            port = info.get("port")
            timestamp = info.get("timestamp", 0)

            # Check if lock is stale
            age_seconds = time.time() - timestamp
            if age_seconds > self._timeout:
                logger.warning(f"Lock file is stale (age: {age_seconds/3600:.1f} hours), removing")
                try:
                    self._lock_file.unlink()
                except OSError:
                    pass
                return None

            # Verify the lock holder with handshake protocol
            if await self._verify_lock_holder(port):
                return info
            else:
                # Port not in use or held by non-legitimate process
                logger.warning(f"Port {port} is not held by valid process, removing stale lock")
                try:
                    self._lock_file.unlink()
                except OSError:
                    pass
                return None

        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.warning(f"Invalid or corrupted lock file: {e}")
            try:
                self._lock_file.unlink()
            except OSError:
                pass
            return None

    async def get_lock_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current lock if one exists.

        Returns:
            Dictionary with lock info (port, pid, timestamp) or None if no valid lock
        """
        return await self._check_existing_lock_with_info()

    async def __aenter__(self) -> "AsyncSocketLock":
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.release()