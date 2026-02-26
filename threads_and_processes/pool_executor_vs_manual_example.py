import os
import queue
import random
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import get_context

"""
Learning benchmark:
- Manual threads/processes: create new workers per task.
- Pool executors: reuse bounded workers across many tasks.

This script intentionally compares:
1) Many tiny I/O tasks over multiple rounds (where thread reuse helps).
2) Few one-off tasks (where manual creation can be competitive).
3) Many CPU tasks (where ProcessPool often wins for stable workloads).
"""

def io_task(task_id: int, min_delay: float = 0.03, max_delay: float = 0.08) -> int:
    # Simulate blocking I/O (network/file wait).
    # Use a per-task RNG to avoid mutating global random state in threads.
    rng = random.Random(task_id)
    time.sleep(rng.uniform(min_delay, max_delay))
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


def run_manual_threads_capped(
    num_tasks: int, max_workers: int, task_fn=io_task
) -> float:
    # Manual producer-consumer style implementation with fixed worker count.
    work_q: queue.Queue[int | None] = queue.Queue()
    out: list[int] = []
    out_lock = threading.Lock()
    workers: list[threading.Thread] = []
    start = time.perf_counter()

    def worker() -> None:
        while True:
            task_id = work_q.get()
            if task_id is None:
                work_q.task_done()
                return
            result = task_fn(task_id)
            with out_lock:
                out.append(result)
            work_q.task_done()

    for _ in range(max_workers):
        t = threading.Thread(target=worker)
        t.start()
        workers.append(t)

    for i in range(num_tasks):
        work_q.put(i)

    work_q.join()

    for _ in range(max_workers):
        work_q.put(None)

    for t in workers:
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


def run_manual_threads_many_rounds(
    tasks_per_round: int, rounds: int, max_workers: int, task_fn=io_task_tiny
) -> float:
    # Recreates a bounded worker set each round.
    start = time.perf_counter()
    for _ in range(rounds):
        run_manual_threads_capped(
            tasks_per_round, max_workers=max_workers, task_fn=task_fn
        )
    return time.perf_counter() - start


def run_thread_pool_many_rounds(
    tasks_per_round: int, rounds: int, max_workers: int, task_fn=io_task_tiny
) -> float:
    # Reuse: one pool survives across all rounds.
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for _ in range(rounds):
            results = list(executor.map(task_fn, range(tasks_per_round)))
            assert len(results) == tasks_per_round
    return time.perf_counter() - start


def run_manual_processes(work_items: list[int]) -> float:
    ctx = get_context("spawn")
    q = ctx.Queue()
    processes = []
    start = time.perf_counter()

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


def winner_line(label_a: str, a: float, label_b: str, b: float) -> str:
    # Simple measured-result commentary line.
    if a < b:
        faster = (b / a) if a > 0 else float("inf")
        return f"{label_a} was faster by ~{faster:.2f}x."
    faster = (a / b) if b > 0 else float("inf")
    return f"{label_b} was faster by ~{faster:.2f}x."


def main() -> None:
    print("\n=== 1) Many tiny I/O tasks (stable workload) ===")
    tasks_per_round = 200
    rounds = 12
    io_workers = 20
    print(
        "Commentary: this models producer/consumer traffic where work keeps arriving.\n"
        "Both approaches use the same concurrency cap; only worker reuse differs."
    )
    manual_thread_time = run_manual_threads_many_rounds(
        tasks_per_round, rounds, max_workers=io_workers, task_fn=io_task_tiny
    )
    pool_thread_time = run_thread_pool_many_rounds(
        tasks_per_round, rounds, max_workers=io_workers, task_fn=io_task_tiny
    )
    print(
        f"Manual threads ({tasks_per_round} tasks x {rounds} rounds): "
        f"{manual_thread_time:.3f}s"
    )
    print(
        f"ThreadPoolExecutor ({io_workers} workers, reused): "
        f"{pool_thread_time:.3f}s"
    )
    print(
        "  -> " + winner_line("Manual threads", manual_thread_time, "ThreadPoolExecutor", pool_thread_time)
    )

    print("\n=== 2) Few one-off tasks ===")
    few_tasks = 3
    print(
        "Commentary: one short burst only. Pool setup overhead can offset reuse benefits."
    )
    manual_few_time = run_manual_threads(few_tasks)
    pool_few_time = run_thread_pool(few_tasks, max_workers=20)
    print(f"Manual threads (few tasks): {manual_few_time:.3f}s")
    print(f"ThreadPoolExecutor (few tasks): {pool_few_time:.3f}s")
    print("  -> " + winner_line("Manual threads", manual_few_time, "ThreadPoolExecutor", pool_few_time))

    print("\n=== 3) Many CPU-bound tasks ===")
    cpu_cores = os.cpu_count() or 4
    work_items = [900_000] * 24
    print(
        "Commentary: CPU-heavy pure Python work. Process pool usually helps by reusing\n"
        "a bounded number of workers (often around CPU core count)."
    )
    manual_proc_time = run_manual_processes(work_items)
    print(f"Manual processes (1 per task): {manual_proc_time:.3f}s")
    try:
        pool_proc_time = run_process_pool(work_items, max_workers=cpu_cores)
        print(f"ProcessPoolExecutor ({cpu_cores} workers): {pool_proc_time:.3f}s")
        print(
            "  -> "
            + winner_line(
                "Manual processes",
                manual_proc_time,
                "ProcessPoolExecutor",
                pool_proc_time,
            )
        )
    except PermissionError:
        print(
            "ProcessPoolExecutor could not run in this environment (permission-limited).\n"
            "Run the same script in your local terminal to see this comparison."
        )

    print("\n=== Interpretation ===")
    print("- For recurring small I/O workloads, thread pools often win via worker reuse.")
    print("- For a tiny one-off burst, manual creation may be similar or slightly faster.")
    print("- For many CPU tasks, process pools are usually the stable default.")
    print("- Always measure on your machine; scheduler/OS/hardware change results.")


if __name__ == "__main__":
    main()
