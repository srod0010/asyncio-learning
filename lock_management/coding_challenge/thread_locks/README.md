# Thread Synchronization Comparison

This folder contains three runnable examples:

1. `threading_lock.py`
2. `threading_rlock.py`
3. `threading_event.py`

## Quick comparison

| Primitive | What it does | Best use case | Common pitfall |
|---|---|---|---|
| `threading.Lock` | Mutual exclusion (one thread in critical section) | Protect shared mutable data (counter, file writes) | Expecting lock to enforce global execution order |
| `threading.RLock` | Reentrant mutual exclusion (same thread can re-acquire) | Nested locked calls on the same object | Using `Lock` in nested calls can self-deadlock |
| `threading.Event` | Thread signaling via boolean flag | Start/stop/ready coordination between threads | Using Event instead of a lock for data protection |

## Run all examples

```bash
python3 thread_locks/threading_lock.py
python3 thread_locks/threading_rlock.py
python3 thread_locks/threading_event.py
```

## How to choose

- Start with `Lock` for shared state protection.
- Switch to `RLock` only when re-entrancy is needed.
- Use `Event` for cross-thread signaling (often together with `Lock`).
