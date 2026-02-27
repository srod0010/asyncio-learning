"""
threading.Event examples
------------------------
Event is a signaling primitive:
- set() marks the flag true
- clear() marks the flag false
- wait() blocks until the flag is true (or timeout)

Use Event for coordination (start/stop/ready), not data protection.
"""

import queue
import threading
import time


def basic_stop_signal_demo() -> None:
    """
    Basic example matching your screenshot:
    - background thread loops
    - main thread sets Event to request stop
    """
    print("\n=== Basic Event demo (stop signal) ===")
    stop = threading.Event()

    def background_job() -> None:
        while not stop.is_set():
            print("I'm still running!")
            # wait(timeout) sleeps, but also wakes early if stop.set() is called
            stop.wait(0.1)

    t = threading.Thread(target=background_job)
    t.start()
    print("thread started")
    time.sleep(1.0)
    stop.set()
    t.join()
    print("thread stopped cleanly")


def practical_worker_pool_demo() -> None:
    """
    Slightly more useful pattern:
    - start_event releases all workers at the same time
    - stop_event lets main thread request graceful shutdown
    """
    print("\n=== Practical Event demo (coordinated workers) ===")
    start_event = threading.Event()
    stop_event = threading.Event()
    task_queue: queue.Queue[int] = queue.Queue()
    processed: list[tuple[int, int]] = []
    processed_lock = threading.Lock()

    for i in range(20):
        task_queue.put(i)

    def worker(worker_id: int) -> None:
        print(f"worker-{worker_id}: waiting for start signal")
        start_event.wait()  # all workers begin together when set
        print(f"worker-{worker_id}: started")
        while not stop_event.is_set():
            try:
                item = task_queue.get(timeout=0.2)
            except queue.Empty:
                break
            # Simulate work
            time.sleep(0.03)
            with processed_lock:
                processed.append((worker_id, item))
            task_queue.task_done()
        print(f"worker-{worker_id}: exiting")

    workers = [threading.Thread(target=worker, args=(wid,)) for wid in range(3)]
    for w in workers:
        w.start()

    time.sleep(0.3)
    print("main: releasing workers")
    start_event.set()

    task_queue.join()
    stop_event.set()
    for w in workers:
        w.join()

    print(f"processed tasks: {len(processed)} (expected 20)")
    print(f"sample processed records: {processed[:5]}")


if __name__ == "__main__":
    basic_stop_signal_demo()
    practical_worker_pool_demo()
