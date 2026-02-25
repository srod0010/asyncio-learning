import asyncio
import time

# Same coroutine as example_3.py: it yields at `await asyncio.sleep(...)`
# so other tasks can run while this one is waiting.
async def fetch_data(param):
    print(f"Do something with {param}...")
    await asyncio.sleep(param)
    print(f"Done with {param}")
    return f"Result of {param}"


async def main():
    # Difference from example_3.py:
    # - example_3.py creates task1/task2 explicitly, then awaits each task separately.
    # - here, gather schedules both coroutines and awaits all of them together.
    # gather returns results in the SAME ORDER as inputs, not completion order.
    results = await asyncio.gather(
        fetch_data(10),
        fetch_data(2),
    )

    print("Both tasks fully completed")
    return results


# Wall-clock timing includes loop setup + async execution + loop teardown.
t1 = time.perf_counter()

# asyncio.run creates an event loop, runs main(), then closes the loop.
results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
# Expected ~10s, not ~12s, because both sleeps overlap on the same event loop.
print(f"Finished in {t2 - t1:.2f} seconds")
