"""
threading.Lock examples
-----------------------
This file shows two patterns:

1) Basic mutual exclusion:
   A lock serializes access to a shared resource (stdout).
   It does NOT force global ordering between threads.

2) Slightly more useful real-world pattern:
   Multiple threads update shared state + shared file output.
   A lock protects the read-modify-write critical section.
"""

import threading
import time
from pathlib import Path


def basic_stdout_demo() -> None:
    """
    Similar to your screenshot:
    - both main thread and worker thread call the same print function
    - lock prevents interleaving inside the critical section
    """
    print("\n=== Basic Lock demo (stdout as shared resource) ===")
    stdout_lock = threading.Lock()

    def print_something(message: str) -> None:
        # Only one thread can print this block at a time.
        with stdout_lock:
            print(message)

    t = threading.Thread(target=print_something, args=("hello",), daemon=True)
    t.start()
    print_something("thread started")
    t.join()

    print(
        "Note: output order may differ across runs, but each print call is protected."
    )


def practical_counter_and_file_demo() -> None:
    """
    Practical example:
    - N threads increment a shared counter
    - each increment also writes one line to the same log file

    Without the lock, count updates can be lost (race condition), and
    file writes can interleave unpredictably.
    """
    print("\n=== Practical Lock demo (shared counter + file) ===")
    lock = threading.Lock()
    counter = {"value": 0}
    script_dir = Path(__file__).resolve().parent
    log_path = script_dir / "lock_demo_output.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("")  # reset each run for easier learning

    def worker(worker_id: int, iterations: int) -> None:
        for _ in range(iterations):
            # Simulate non-trivial work around shared mutation.
            time.sleep(0.0005)
            with lock:
                # Critical section: read-modify-write must be atomic as a unit.
                current = counter["value"]
                counter["value"] = current + 1
                with log_path.open("a", encoding="utf-8") as f:
                    f.write(f"worker-{worker_id} -> {counter['value']}\n")

    threads = [threading.Thread(target=worker, args=(i, 200)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    expected = 4 * 200
    print(f"Final counter value: {counter['value']} (expected {expected})")
    print(f"Log file written to: {log_path}")


if __name__ == "__main__":
    basic_stdout_demo()
    practical_counter_and_file_demo()
