"""
Interprocess lock examples with `fasteners`.

Why this exists:
- `multiprocessing.Lock` coordinates only related child processes.
- Independent processes (separate Python programs) need a lock visible to all.
- `fasteners.InterProcessLock(path)` uses a file lock identified by `path`.

How to try:
1) Install dependency:
   python3 -m pip install fasteners
2) In terminal A:
   python3 thread_locks/process_locks/fasteners_interprocess_lock.py direct
3) Quickly in terminal B:
   python3 thread_locks/process_locks/fasteners_interprocess_lock.py direct
You will see the second process wait until the first one releases the lock.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time

try:
    import fasteners
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: fasteners. Install with "
        "`python3 -m pip install fasteners`."
    ) from exc


# Shared lock identity. Any independent process using the same file path
# competes for the same lock.
LOCK_PATH = os.path.join(tempfile.gettempdir(), "asyncio_code_examples_fasteners.lock")


def log(message: str) -> None:
    """Print with process id so you can see which process owns the lock."""
    print(f"[pid={os.getpid()}] {message}", flush=True)


def demo_direct_lock() -> None:
    """
    Example 1: direct `InterProcessLock`.
    This is the explicit style: create lock, acquire with `with lock:`.
    """
    lock = fasteners.InterProcessLock(LOCK_PATH)
    log(f"waiting for lock: {LOCK_PATH}")

    with lock:
        log("acquired lock (direct)")
        for i in range(5):
            log(f"critical section step {i + 1}/5")
            time.sleep(0.2)
        log("releasing lock (direct)")


@fasteners.interprocess_locked(LOCK_PATH)
def decorated_critical_section() -> None:
    """
    Example 2: decorator form.
    Entire function is executed under the same interprocess lock.
    """
    log("acquired lock (decorator)")
    for i in range(3):
        log(f"decorated work {i + 1}/3")
        time.sleep(0.2)
    log("releasing lock (decorator)")


def main() -> None:
    """
    CLI:
    - `direct`    -> run direct lock example
    - `decorator` -> run decorator example
    """
    mode = sys.argv[1] if len(sys.argv) > 1 else "direct"
    if mode == "direct":
        demo_direct_lock()
    elif mode == "decorator":
        decorated_critical_section()
    else:
        raise SystemExit("Usage: ...fasteners_interprocess_lock.py [direct|decorator]")


if __name__ == "__main__":
    main()
