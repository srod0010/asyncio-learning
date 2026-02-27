import multiprocessing
from pathlib import Path

PROCESS_LOCK = None
COUNTER_FILE = None


def init_worker(lock, counter_file):
    """Share lock + file path with each worker process."""
    global PROCESS_LOCK, COUNTER_FILE
    PROCESS_LOCK = lock
    COUNTER_FILE = counter_file


def add_count():
    p_name = multiprocessing.current_process().name
    print(f"  --> {p_name} is waiting for lock...", flush=True)

    with PROCESS_LOCK:
        print(f"  [LOCK ACQUIRED] by {p_name}", flush=True)

        # Read using a context manager so data is closed cleanly.
        with open(COUNTER_FILE, "r", encoding="utf-8") as file:
            count = int(file.read().strip())

        # Increment + write using another context manager.
        new_count = count + 1
        with open(COUNTER_FILE, "w", encoding="utf-8") as file:
            file.write(str(new_count))

        print(f"  [WRITE DONE] {p_name} updated count to {new_count}", flush=True)

    print(f"  <-- {p_name} has released lock.", flush=True)


def main():
    base_dir = Path(__file__).resolve().parent
    counter_file = base_dir / "demofile.txt"
    counter_file.write_text("0", encoding="utf-8")

    shared_lock = multiprocessing.Lock()
    with multiprocessing.Pool(
        processes=50, initializer=init_worker, initargs=(shared_lock, str(counter_file))
    ) as pool:
        jobs = [pool.apply_async(add_count) for _ in range(100)]
        for job in jobs:
            job.wait()

    content = counter_file.read_text(encoding="utf-8").strip()
    print("Final Count:", content)


if __name__ == "__main__":
    main()
