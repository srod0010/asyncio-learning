"""
threading.RLock examples
------------------------
RLock is a reentrant lock:
- Same thread can acquire it multiple times.
- Useful when locked code calls other locked methods on the same object.
"""

import threading
import time


def basic_double_acquire_demo() -> None:
    """
    Same idea as your screenshot:
    the same thread acquires the same lock twice safely.
    """
    print("\n=== Basic RLock demo (double acquire) ===")
    rlock = threading.RLock()

    with rlock:  # 1st acquire by this thread
        with rlock:  # 2nd acquire by the same thread (allowed for RLock)
            print("Double acquired")


class SafeCounter:
    """
    Slightly more useful example:
    increment() calls another method that also locks the same object.
    RLock prevents self-deadlock in this nested call pattern.
    """

    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.RLock()

    def _add_internal(self, amount: int) -> None:
        # Nested acquire in the same thread is safe with RLock.
        with self._lock:
            old = self._value
            time.sleep(0.001)  # simulate tiny real work
            self._value = old + amount

    def increment(self, amount: int = 1) -> None:
        with self._lock:
            self._add_internal(amount)

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


def practical_nested_lock_demo() -> None:
    print("\n=== Practical demo (nested method locking) ===")
    counter = SafeCounter()

    def worker(n: int) -> None:
        for _ in range(n):
            counter.increment()

    threads = [threading.Thread(target=worker, args=(500,)) for _ in range(4)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"Final counter value: {counter.value} (expected 2000)")


if __name__ == "__main__":
    basic_double_acquire_demo()
    practical_nested_lock_demo()
