import time


def fetch_data(param):
    # Blocking call: this stops the entire program for `param` seconds.
    print(f"Do something with {param}...")
    time.sleep(param)
    print(f"Done with {param}")
    return f"Result of {param}"


def main():
    # Purely sequential: second call starts only after first fully completes.
    result1 = fetch_data(1)
    print("Fetch 1 fully completed")
    result2 = fetch_data(2)
    print("Fetch 2 fully completed")
    return [result1, result2]


# Wall-clock timer for the whole synchronous program.
t1 = time.perf_counter()

results = main()
print(results)

t2 = time.perf_counter()
# Expected ~3s (1s + 2s), because there is no overlap.
print(f"Finished in {t2 - t1:.2f} seconds")
