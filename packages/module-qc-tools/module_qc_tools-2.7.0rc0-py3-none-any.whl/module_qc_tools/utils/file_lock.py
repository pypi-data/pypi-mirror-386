"""File locking utilities for YARR executable coordination."""

from __future__ import annotations

import fcntl
import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from rich.console import Console

logger = logging.getLogger("measurement")


@contextmanager
def yarr_file_lock(
    lock_path: str | Path = "/tmp/yarr.lock",
    timeout: float = 300,
    poll_interval: float = 1.0,
    show_status: bool = True,
) -> Generator[None]:
    """
    Context manager that acquires an exclusive file lock for YARR process coordination.

    This prevents multiple YARR processes from running simultaneously,
    which would cause conflicts and process failures.

    Args:
        lock_path: Path to the lock file (default: /tmp/yarr.lock)
        timeout: Maximum time to wait for lock in seconds (default: 300)
        poll_interval: Time between lock acquisition attempts (default: 1.0)
        show_status: Whether to show rich status indicators (default: True)

    Raises:
        TimeoutError: If lock cannot be acquired within timeout period
        FileNotFoundError: If lock file does not exist
        PermissionError: If insufficient permissions to access lock file
    """
    lock_path = Path(lock_path)

    if not lock_path.exists():
        msg = f"Lock file {lock_path} does not exist"
        raise FileNotFoundError(msg)

    console = Console() if show_status else None
    status = None

    try:
        # Open the lock file for locking
        with lock_path.open("r", encoding="utf-8") as lock_file:
            start_time = time.time()

            if console and show_status:
                status = console.status(
                    f"[yellow]Waiting for YARR lock on {lock_path}..."
                )
                status.start()

            while True:
                try:
                    # Try to acquire exclusive lock (non-blocking)
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                    if status:
                        status.update(f"[green]YARR lock acquired on {lock_path}")
                        time.sleep(0.1)  # Brief pause to show success message
                        status.stop()

                    logger.debug(f"Acquired exclusive YARR lock on {lock_path}")

                    try:
                        yield
                    finally:
                        # Lock is automatically released when file is closed
                        logger.debug(f"Released YARR lock on {lock_path}")
                        if console and show_status:
                            console.print(f"[green]Released YARR lock on {lock_path}")

                    break

                except BlockingIOError:
                    # Lock is held by another process
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        if status:
                            status.stop()
                        msg = f"Timeout waiting for YARR lock on {lock_path} after {timeout} seconds"
                        raise TimeoutError(msg) from None

                    # Wait before trying again
                    time.sleep(poll_interval)

    except PermissionError as e:
        if status:
            status.stop()
        msg = f"Permission denied accessing {lock_path}: {e}"
        raise PermissionError(msg) from e
