import asyncio
import time


async def fetch_data(param):
    # This is intentionally a bad async pattern for demonstration:
    # `time.sleep` blocks the event loop thread, so other Tasks cannot run.
    print(f"Do something with {param}...")
    time.sleep(param)
    print(f"Done with {param}")
    return f"Result of {param}"


async def main():
    # Tasks are scheduled concurrently...
    task1 = asyncio.create_task(fetch_data(1))
    task2 = asyncio.create_task(fetch_data(2))

    # ...but they cannot make progress concurrently because `time.sleep` blocks.
    result1 = await task1
    print("Task 1 fully completed")
    result2 = await task2
    print("Task 2 fully completed")
    return [result1, result2]


# Runtime timer for showing blocking impact.
t1 = time.perf_counter()

results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
# Expected ~3s (effectively sequential) despite using create_task.
print(f"Finished in {t2 - t1:.2f} seconds")
