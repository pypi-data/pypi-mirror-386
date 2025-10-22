# socketlock

A robust, secure, and async-friendly process lock using TCP sockets with handshake protocol verification.

[![CI](https://github.com/comput3/socketlock/actions/workflows/ci.yml/badge.svg)](https://github.com/comput3/socketlock/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/socketlock.svg)](https://badge.fury.io/py/socketlock)
[![Python Support](https://img.shields.io/pypi/pyversions/socketlock.svg)](https://pypi.org/project/socketlock/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **🔒 Atomic Lock Acquisition**: Prevents race conditions with atomic file operations
- **🛡️ Security Handshake**: Application-level protocol prevents imposter processes
- **⚡ Async-First**: Built on asyncio with synchronous wrapper available
- **🔄 Self-Healing**: Automatic detection and cleanup of stale locks
- **📊 Rich Diagnostics**: Lock info includes PID and port for easy troubleshooting
- **🚀 High Performance**: Sub-millisecond lock operations
- **💥 Crash-Safe**: OS automatically releases sockets on process termination
- **🌍 Cross-Platform**: Works on Linux, macOS, and Windows

## Why socketlock?

Traditional process locks suffer from various problems:
- **PID files**: Process IDs can be recycled, causing false positives
- **File locks**: Often platform-specific, may not release on crash
- **Semaphores**: Require cleanup, complex API, platform differences

`socketlock` solves these issues by using TCP sockets with a verification handshake, ensuring that only legitimate processes can hold locks and that locks are always released on process termination.

## Installation

```bash
pip install socketlock
```

## Quick Start

### Async Interface

```python
import asyncio
from socketlock import AsyncSocketLock

async def critical_section():
    async with AsyncSocketLock(name="myapp") as lock:
        print(f"Lock acquired (PID: {lock.pid}, Port: {lock.port})")
        # Your protected code here
        await asyncio.sleep(1)
    # Lock automatically released

asyncio.run(critical_section())
```

### Sync Interface

```python
from socketlock import SocketLock

with SocketLock(name="myapp") as lock:
    print(f"Lock acquired (PID: {lock.pid}, Port: {lock.port})")
    # Your protected code here
# Lock automatically released
```

### Manual Lock Management

```python
import asyncio
from socketlock import AsyncSocketLock

async def manual_lock():
    lock = AsyncSocketLock(name="myapp")
    try:
        await lock.acquire()
        print("Lock acquired!")
        # Your protected code here
    except RuntimeError as e:
        print(f"Could not acquire lock: {e}")
        # Error includes PID and port of lock holder
    finally:
        await lock.release()

asyncio.run(manual_lock())
```

## Advanced Usage

### Custom Configuration

```python
from socketlock import AsyncSocketLock

lock = AsyncSocketLock(
    name="myapp",
    timeout=7200,  # Stale lock timeout (seconds)
    lock_dir="/var/run/myapp",  # Custom lock directory
    signature_seed="custom_seed",  # Custom handshake seed
)
```

### Checking Lock Status

```python
import asyncio
from socketlock import AsyncSocketLock

async def check_status():
    lock = AsyncSocketLock(name="myapp")
    info = await lock.get_lock_info()

    if info:
        print(f"Lock is held by PID {info['pid']} on port {info['port']}")
        print(f"Lock acquired at: {info['timestamp']}")
    else:
        print("Lock is available")

asyncio.run(check_status())
```

### Non-Blocking Acquisition

```python
import asyncio
from socketlock import AsyncSocketLock

async def try_lock():
    lock = AsyncSocketLock(name="myapp")

    if await lock.try_acquire():
        print("Got the lock!")
        # Do work...
        await lock.release()
    else:
        print("Lock is busy, will try again later")

asyncio.run(try_lock())
```

## How It Works

1. **Lock Acquisition**: Process attempts to bind to a TCP socket on localhost
2. **Port Discovery**: Dynamic port allocation (OS-assigned) is written to a lock file
3. **Verification**: Other processes can verify lock validity through handshake protocol
4. **Automatic Release**: OS releases socket when process terminates (any reason)

The handshake protocol prevents denial-of-service attacks where a rogue process could bind to a port and pretend to hold the lock.

## Performance

Typical operation times (Intel i7, Python 3.11):

- **Uncontested acquisition**: ~0.5ms
- **Contested detection**: ~0.7ms (including handshake verification)
- **Lock release**: ~0.06ms
- **Full context manager cycle**: ~0.6ms

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.