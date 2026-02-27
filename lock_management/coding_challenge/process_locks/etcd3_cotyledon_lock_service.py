"""
Distributed lock service with etcd + Cotyledon (annotated)
===========================================================

Why this is useful:
- Cotyledon runs multiple worker *processes* for the same service.
- etcd provides a distributed lock primitive shared by all those processes.
- If all workers lock the same lock name, only one worker holds the lock at a time.

How this relates to Raft:
- etcd stores lock state in its key-value store.
- In multi-node etcd, that state is replicated and coordinated by Raft.
- Your app does not implement Raft directly; it relies on etcd's correctness.

Learning mode in this file:
1) SHORT_CRITICAL_SECTION mode:
   - hold lock briefly (print + sleep)
   - `with lock:` style is simplest and safest
2) SUSTAINED_CRITICAL_SECTION mode:
   - hold lock for longer than a short action
   - shows explicit acquire/release and periodic `lock.refresh()`

Run locally:
1) Start etcd in terminal A:
   etcd
2) Start this service in terminal B:
   python3 thread_locks/process_locks/etcd3_cotyledon_lock_service.py

Optional env vars:
- WORKERS=4              (how many Cotyledon worker processes)
- ETCD_HOST=127.0.0.1
- ETCD_PORT=2379
- LOCK_NAME=print-lock
- LOCK_TTL=60            (seconds, default etcd lock lease behavior)
- MODE=short             ("short" or "sustained")
- HOLD_SECONDS=1.0       (for short mode)
- LONG_WORK_SECONDS=20   (for sustained mode)

Compatibility note:
- `python-etcd3` is old and may fail with modern `protobuf` (e.g., 6.x) with:
  "Descriptors cannot be created directly."
- This file sets `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` before importing
  etcd3 as a compatibility fallback.
- Preferred dependency fix in your venv:
  python -m pip install "protobuf<4,>=3.20.3"
"""

from __future__ import annotations

import os
import threading
import time

# Compatibility fallback for old etcd3 protobuf stubs.
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

try:
    import cotyledon
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: cotyledon. Install with `python3 -m pip install cotyledon`."
    ) from exc

try:
    import etcd3
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: etcd3. Install with `python3 -m pip install etcd3`."
    ) from exc


class PrinterService(cotyledon.Service):
    """
    One worker process managed by Cotyledon.

    Multiple instances of this class run concurrently in separate processes.
    All instances compete on the same etcd lock key.
    """

    name = "printer"

    def __init__(self, worker_id: int):
        super().__init__(worker_id)
        self._shutdown = threading.Event()

        host = os.getenv("ETCD_HOST", "127.0.0.1")
        port = int(os.getenv("ETCD_PORT", "2379"))
        self.client = etcd3.client(host=host, port=port)

        self.lock_name = os.getenv("LOCK_NAME", "print-lock")
        self.lock_ttl = int(os.getenv("LOCK_TTL", "60"))

        # mode:
        # - short: quick critical section with context manager
        # - sustained: longer critical section with refresh loop
        self.mode = os.getenv("MODE", "short").strip().lower()

        self.hold_seconds = float(os.getenv("HOLD_SECONDS", "1.0"))
        self.long_work_seconds = float(os.getenv("LONG_WORK_SECONDS", "20.0"))

    def run(self) -> None:
        while not self._shutdown.is_set():
            if self.mode == "sustained":
                self._run_sustained_cycle()
            else:
                self._run_short_cycle()

    def _run_short_cycle(self) -> None:
        """
        Recommended for short work:
        lock is held briefly and auto-released on exit.
        """
        lock = self.client.lock(self.lock_name, ttl=self.lock_ttl)
        with lock:
            print(
                f"[worker={self.worker_id}] has lock '{self.lock_name}' "
                f"(mode=short, ttl={self.lock_ttl}s)",
                flush=True,
            )
            time.sleep(self.hold_seconds)

    def _run_sustained_cycle(self) -> None:
        """
        For longer work, keep the lease alive with refresh.
        This avoids lock expiry during a valid long critical section.
        """
        lock = self.client.lock(self.lock_name, ttl=self.lock_ttl)
        acquired = lock.acquire(timeout=10)
        if not acquired:
            print(f"[worker={self.worker_id}] lock acquire timeout; retrying", flush=True)
            return

        try:
            print(
                f"[worker={self.worker_id}] acquired '{self.lock_name}' "
                f"(mode=sustained, ttl={self.lock_ttl}s)",
                flush=True,
            )
            start = time.monotonic()
            refresh_every = max(1.0, self.lock_ttl / 3.0)
            next_refresh = start + refresh_every

            while not self._shutdown.is_set():
                elapsed = time.monotonic() - start
                if elapsed >= self.long_work_seconds:
                    break

                # Simulate ongoing critical work.
                time.sleep(0.25)

                # Keep lock alive for long operations.
                if time.monotonic() >= next_refresh:
                    lock.refresh()
                    print(
                        f"[worker={self.worker_id}] refreshed lock lease "
                        f"at +{elapsed:.1f}s",
                        flush=True,
                    )
                    next_refresh = time.monotonic() + refresh_every
        finally:
            lock.release()
            print(f"[worker={self.worker_id}] released '{self.lock_name}'", flush=True)

    def terminate(self) -> None:
        self._shutdown.set()


def main() -> None:
    workers = int(os.getenv("WORKERS", "4"))
    manager = cotyledon.ServiceManager()
    manager.add(PrinterService, workers)
    manager.run()


if __name__ == "__main__":
    main()
