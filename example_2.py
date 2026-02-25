import asyncio
import time


async def fetch_data(param):
    # Non-blocking wait point: this coroutine pauses and lets the loop run others.
    print(f"Do something with {param}...")
    await asyncio.sleep(param)
    print(f"Done with {param}")
    return f"Result of {param}"


async def main():
    # These are coroutine objects, not scheduled Tasks yet.
    # They begin only when awaited.
    task1 = fetch_data(1)
    task2 = fetch_data(2)

    # Sequential awaiting means no overlap here.
    result1 = await task1
    print("Task 1 fully completed")
    result2 = await task2
    print("Task 2 fully completed")
    return [result1, result2]


# `asyncio.run` creates an event loop, runs `main`, and closes the loop.
t1 = time.perf_counter()

results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
# Expected ~3s (1s + 2s) because coroutines were awaited one after another.
print(f"Finished in {t2 - t1:.2f} seconds")
