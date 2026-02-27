# Lock Management Notes

## Challenge summary
- 50 processes run 100 jobs.
- Each job reads `demofile.txt`, adds `1`, and writes it back.
- Without a lock, read-modify-write races corrupt the final value.

## Visualizing lock behavior
- Use `multiprocessing.current_process().name` to print which worker is running.
- Print before lock and inside lock:
  - `--> ... waiting for lock`
  - `[LOCK ACQUIRED] ...`
  - `[WRITE DONE] ...`
  - `<-- ... has released lock`

## What to look for in terminal output
- Many workers can print "waiting" around the same time.
- Only one worker should appear between `[LOCK ACQUIRED]` and `[WRITE DONE]` at any moment.
- `[WRITE DONE]` values should increase cleanly from `1` to `100` with no duplicates.
- Final line should be `Final Count: 100`.

## Why the earlier approach gave wrong numbers
- `with open(...)` auto-closes correctly when the block ends.
- The issue came from splitting operations and manually opening for write (outside a context manager), which can leave writes buffered/not flushed immediately.
- In concurrent code, that stale/partial state can be read by another worker and produce wrong totals.
- Fix: keep the whole read -> increment -> write sequence in the lock, and use context managers for both read and write.
