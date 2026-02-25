import asyncio
import time

# Event-loop model for this file:
# 1) `asyncio.run(main())` creates an event loop and starts running `main`.
# 2) `create_task(...)` registers coroutines as independent Tasks on that loop.
# 3) Each `await` is a yield point: current Task pauses, loop runs other ready Tasks.
# 4) Total runtime is roughly the longest Task, not the sum, because sleeps overlap.
async def fetch_data(param):
    # This function is a coroutine: calling it returns a coroutine object.
    # It does not execute until the event loop schedules it as a Task.
    print(f"Do something with {param}...")

    # Non-blocking sleep:
    # - this Task pauses here and gives control back to the event loop
    # - loop can run other Tasks while waiting `param` seconds
    await asyncio.sleep(param)

    print(f"Done with {param}")
    return f"Result of {param}"


async def main():
    # `create_task` both wraps the coroutine and schedules it immediately.
    # After these lines, task1 and task2 are both known to the event loop.
    task1 = asyncio.create_task(fetch_data(10))
    task2 = asyncio.create_task(fetch_data(2))

    # Waiting for task1 does NOT freeze the loop.
    # While `main` is paused on this await, task2 keeps running.
    result1 = await task1
    print("Task 1 fully completed")

    # By now task2 is usually already done (2s < 10s), so this often returns instantly.
    result2 = await task2
    print("Task 2 fully completed")
    return [result1, result2]


# Start wall-clock timing (includes loop setup/teardown + all async work).
t1 = time.perf_counter()

# Creates loop -> runs `main` to completion -> closes loop.
results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
# Expected ~10s here, not ~12s, because both sleeps overlapped.
print(f"Finished in {t2 - t1:.2f} seconds")
