import asyncio
import time


async def fetch_data(param):
    # Simulated async I/O task.
    await asyncio.sleep(param)
    return f"Result of {param}"


async def main():
    # Pattern 1: manual Task creation + manual awaiting.
    task1 = asyncio.create_task(fetch_data(1))
    task2 = asyncio.create_task(fetch_data(2))
    result1 = await task1
    result2 = await task2
    print(f"Task 1 and 2 awaited results: {[result1, result2]}")

    # Pattern 2: gather coroutine objects directly.
    # `gather` schedules them and waits for all at once.
    coroutines = [fetch_data(i) for i in range(1, 3)]
    results = await asyncio.gather(*coroutines, return_exceptions=True)
    print(f"Coroutine Results: {results}")

    # Pattern 3: gather already-created Tasks.
    tasks = [asyncio.create_task(fetch_data(i)) for i in range(1, 3)]
    results = await asyncio.gather(*tasks)
    print(f"Task Results: {results}")

    # Pattern 4: TaskGroup (structured concurrency, Python 3.11+).
    # Exiting the context ensures all created tasks finished or failed together.
    async with asyncio.TaskGroup() as tg:
        results = [tg.create_task(fetch_data(i)) for i in range(1, 3)]
    print(f"Task Group Results: {[result.result() for result in results]}")

    return "Main Coroutine Done"


# Overall runtime for all four patterns.
t1 = time.perf_counter()

results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
print(f"Finished in {t2 - t1:.2f} seconds")
