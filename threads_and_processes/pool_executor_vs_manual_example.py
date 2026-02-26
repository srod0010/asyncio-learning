import os
import queue
import random
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import get_context
"""
Shows when to use pool based executor (ThreadPool, ProcessPool) vs manual thread / processes
"""

def io_task(task_id: int, min_delay: float = 0.03, max_delay: float = 0.08) -> int:
    # Simulate blocking I/O (network/file wait).
    random.seed(task_id)
    time.sleep(random.uniform(min_delay, max_delay))
    return task_id


def io_task_tiny(task_id: int) -> int:
    # Very small waits make per-task thread creation overhead visible.
    return io_task(task_id, min_delay=0.001, max_delay=0.003)


def cpu_task(work_units: int) -> int:
    # Pure Python CPU work (holds the GIL).
    total = 0
    for i in range(work_units):
        total += (i * i) % 97
    return total


def cpu_worker_to_queue(units: int, result_q) -> None:
    result_q.put(cpu_task(units))


def run_manual_threads(num_tasks: int, task_fn=io_task) -> float:
    out: list[int] = []
    out_lock = threading.Lock()
    threads = []
    start = time.perf_counter()

    def worker(task_id: int) -> None:
        result = task_fn(task_id)
        with out_lock:
            out.append(result)

    for i in range(num_tasks):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start
    assert len(out) == num_tasks
    return elapsed


def run_thread_pool(num_tasks: int, max_workers: int, task_fn=io_task) -> float:
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(task_fn, range(num_tasks)))
    elapsed = time.perf_counter() - start
    assert len(results) == num_tasks
    return elapsed


def run_manual_processes(work_items: list[int]) -> float:
    ctx = get_context("spawn")
    q = ctx.Queue()
    processes = []
    start = time.perf_counter()

    def worker(units: int, result_q) -> None:
        result_q.put(cpu_task(units))

    for units in work_items:
        p = ctx.Process(target=cpu_worker_to_queue, args=(units, q))
        p.start()
        processes.append(p)

    results = []
    for _ in work_items:
        try:
            results.append(q.get(timeout=30))
        except queue.Empty:
            raise RuntimeError("Timed out waiting for manual process result.")

    for p in processes:
        p.join()

    elapsed = time.perf_counter() - start
    assert len(results) == len(work_items)
    return elapsed


def run_process_pool(work_items: list[int], max_workers: int) -> float:
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(cpu_task, work_items))
    elapsed = time.perf_counter() - start
    assert len(results) == len(work_items)
    return elapsed


def main() -> None:
    print("\n=== 1) Many small I/O-bound tasks ===")
    many_io_tasks = 2000
    manual_thread_time = run_manual_threads(many_io_tasks, task_fn=io_task_tiny)
    pool_thread_time = run_thread_pool(
        many_io_tasks, max_workers=20, task_fn=io_task_tiny
    )
    print(f"Manual threads (1 per task): {manual_thread_time:.3f}s")
    print(f"ThreadPoolExecutor (20 workers): {pool_thread_time:.3f}s")

    print("\n=== 2) Few one-off tasks ===")
    few_tasks = 3
    manual_few_time = run_manual_threads(few_tasks)
    pool_few_time = run_thread_pool(few_tasks, max_workers=20)
    print(f"Manual threads (few tasks): {manual_few_time:.3f}s")
    print(f"ThreadPoolExecutor (few tasks): {pool_few_time:.3f}s")

    print("\n=== 3) Many CPU-bound tasks ===")
    cpu_cores = os.cpu_count() or 4
    work_items = [900_000] * 24
    manual_proc_time = run_manual_processes(work_items)
    pool_proc_time = run_process_pool(work_items, max_workers=cpu_cores)
    print(f"Manual processes (1 per task): {manual_proc_time:.3f}s")
    print(f"ProcessPoolExecutor ({cpu_cores} workers): {pool_proc_time:.3f}s")

    print("\n=== Interpretation ===")
    print("- Many small I/O tasks: thread pool usually wins (thread reuse).")
    print("- Few one-off tasks: manual thread/process can be competitive.")
    print("- Many CPU tasks: process pool usually wins (reuse + bounded workers).")


if __name__ == "__main__":
    main()
