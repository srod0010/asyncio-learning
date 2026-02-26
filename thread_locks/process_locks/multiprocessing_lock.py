import multiprocessing
import sys
import time

stdout_lock = None


def init_worker(lock):
    """
    Pool initializer: every child process receives the SAME shared lock object.
    """
    global stdout_lock
    stdout_lock = lock

def print_cat(i):
    # Add some randomness by waiting a bit
    time.sleep(0.1)
    with stdout_lock:
        # One write call keeps each worker's block contiguous on stdout.
        block = (
            f"Worker {i} printing\n"
            " /\\_/\\\n"
            "( o.o )\n"
            " > ^ <\n"
            f"Worker {i} complete\n"
        )
        sys.stdout.write(block)
        sys.stdout.flush()



if __name__ == "__main__":
    lock = multiprocessing.Lock()
    with multiprocessing.Pool(processes=3, initializer=init_worker, initargs=(lock,)) as pool:
        jobs = []
        for i in range(5):
            jobs.append(pool.apply_async(print_cat,(i,)))
        for job in jobs:
            job.wait()
