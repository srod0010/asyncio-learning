import asyncio
import time


async def fetch_data(param):
    # Simulated I/O: yields control while waiting.
    print(f"Do something with {param}...")
    await asyncio.sleep(param)
    print(f"Done with {param}")
    return f"Result of {param}"


async def main():
    # Both tasks are scheduled immediately and run concurrently.
    task1 = asyncio.create_task(fetch_data(1))
    task2 = asyncio.create_task(fetch_data(2))

    # Awaiting task2 first does not block task1 from progressing.
    result2 = await task2
    print("Task 2 fully completed")

    # task1 is likely already done by now, so this often returns immediately.
    result1 = await task1
    print("Task 1 fully completed")
    return [result1, result2]


# Total runtime timer.
t1 = time.perf_counter()

results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
# Expected ~2s (longest task), not ~3s.
print(f"Finished in {t2 - t1:.2f} seconds")
