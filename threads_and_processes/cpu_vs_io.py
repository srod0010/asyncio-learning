"""
ThreadPoolExecutor vs ProcessPoolExecutor (I/O-bound vs CPU-bound)

Goal:
- Show why threads are great for I/O-bound tasks (waiting on disk/network/sleep/user input, API calls, reading files or db queries)
- Show why processes are better for CPU-bound tasks (heavy computation, cryptography, image processing, encryption/decryption)

Rule of thumb:
- I/O-bound  -> ThreadPoolExecutor
- CPU-bound  -> ProcessPoolExecutor
"""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import math


# -------------------- I/O-bound task --------------------
def io_task(seconds: int) -> str:
    """
    Simulates I/O work (e.g., waiting for network/disk).
    time.sleep releases the GIL while waiting.
    """
    time.sleep(seconds)
    return f"Done sleeping {seconds}s"


# -------------------- CPU-bound task --------------------
def cpu_task(n: int) -> float:
    """
    Simulates CPU-heavy work.
    Threads won't speed this up much in CPython due to the GIL.
    Processes can run in parallel across CPU cores.
    """
    total = 0.0
    for i in range(1, n):
        total += math.sqrt(i)
    return total


# -------------------- Runner helper --------------------
def run(executor_class, func, inputs):
    """
    Runs func over inputs using the provided executor class
    and prints how long it took.
    """
    start = time.time()

    # The context manager ensures proper cleanup of workers.
    with executor_class() as executor:
        results = list(executor.map(func, inputs))

    end = time.time()
    print(f"{executor_class.__name__} took {end - start:.2f}s")
    return results


if __name__ == "__main__":
    # ==================== I/O-bound test ====================
    print("== I/O-bound test ==")
    io_inputs = [1, 1, 1, 1]  # each sleeps for 1 second

    run(ThreadPoolExecutor, io_task, io_inputs)
    run(ProcessPoolExecutor, io_task, io_inputs)

    # ==================== CPU-bound test ====================
    print("\n== CPU-bound test ==")
    cpu_inputs = [10_000_000] * 4

    run(ThreadPoolExecutor, cpu_task, cpu_inputs)
    run(ProcessPoolExecutor, cpu_task, cpu_inputs)


"""
==================== Expected Output (on a 4-core CPU) ====================

I/O-bound (time.sleep)
--------------------------------------------------------
Executor              Time (approx.)     Why
--------------------------------------------------------
ThreadPoolExecutor    ~1s                Threads overlap while waiting.
ProcessPoolExecutor   ~1.1-1.2s          Works too, but process startup adds overhead.


CPU-bound (math loop)
--------------------------------------------------------
Executor              Time (approx.)     Why
--------------------------------------------------------
ThreadPoolExecutor    ~0.8-1s                Limited by GIL → no true parallelism.
ProcessPoolExecutor   ~0.26s                Each process uses a separate CPU core.


==================== Summary ====================

Task Type   Best Executor         Why
--------------------------------------------------------
I/O-bound   ThreadPoolExecutor    Threads overlap while waiting (GIL not a problem).
CPU-bound   ProcessPoolExecutor   Separate processes avoid the GIL and run in parallel.

==========================================================================

Important Notes:
- Exact timings vary by machine and CPU core count.
- ProcessPoolExecutor has overhead (process startup + data serialization).
- For small CPU tasks, processes may be slower due to overhead.
- For heavy CPU tasks, processes usually outperform threads.
"""