import asyncio
import time


async def fetch_data(param):
    # Simulate async work that takes `param` seconds.
    print(f"Do something with {param}...")
    await asyncio.sleep(param)
    print(f"Done with {param}")
    return f"Result of {param}"


async def main():
    # Start both coroutines immediately so they run concurrently.
    task1 = asyncio.create_task(fetch_data(1))
    task2 = asyncio.create_task(fetch_data(2))

    # Await task1 first; task2 keeps progressing in the background.
    result1 = await task1
    print("Task 1 fully completed")

    # Await task2 next. If it already finished, this returns right away.
    result2 = await task2
    print("Task 2 fully completed")
    return [result1, result2]


# Measure full wall-clock runtime for the async program.
t1 = time.perf_counter()

results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
print(f"Finished in {t2 - t1:.2f} seconds")
