import asyncio
import random
import time
from dataclasses import dataclass


@dataclass
class Heartbeat:
    node_id: str
    sent_at: float


async def node_sender(
    node_id: str,
    queue: asyncio.Queue,
    interval: float,
    stop_after: float | None = None,
) -> None:
    start = time.monotonic()
    while True:
        elapsed = time.monotonic() - start
        if stop_after is not None and elapsed >= stop_after:
            print(f"[{node_id}] stopped sending heartbeats (simulated failure)")
            return

        await queue.put(Heartbeat(node_id=node_id, sent_at=time.monotonic()))
        print(f"[{node_id}] heartbeat sent")

        jitter = random.uniform(0.0, 0.15)
        await asyncio.sleep(interval + jitter)


async def monitor(
    queue: asyncio.Queue,
    node_ids: list[str],
    timeout: float,
    runtime: float,
) -> None:
    last_seen = {node_id: time.monotonic() for node_id in node_ids}
    marked_dead: set[str] = set()
    start = time.monotonic()

    while True:
        now = time.monotonic()
        if now - start > runtime:
            print("\n[monitor] finished demo runtime")
            return

        try:
            hb = await asyncio.wait_for(queue.get(), timeout=0.5)
            last_seen[hb.node_id] = now
            if hb.node_id in marked_dead:
                marked_dead.remove(hb.node_id)
                print(f"[monitor] RECOVERED: {hb.node_id} heartbeat received again")
            print(f"[monitor] received heartbeat from {hb.node_id}")
        except asyncio.TimeoutError:
            pass

        for node_id, ts in last_seen.items():
            if now - ts > timeout and node_id not in marked_dead:
                marked_dead.add(node_id)
                print(
                    f"[monitor] ALERT: {node_id} missed heartbeats "
                    f"for {now - ts:.1f}s (timeout={timeout}s)"
                )


async def main() -> None:
    queue: asyncio.Queue[Heartbeat] = asyncio.Queue()
    node_ids = ["node-a", "node-b", "node-c"]

    senders = [
        asyncio.create_task(node_sender("node-a", queue, interval=1.0)),
        asyncio.create_task(node_sender("node-b", queue, interval=1.0, stop_after=4.0)),
        asyncio.create_task(node_sender("node-c", queue, interval=1.2)),
    ]

    mon = asyncio.create_task(monitor(queue, node_ids, timeout=3.0, runtime=12.0))
    await mon

    for task in senders:
        task.cancel()
    await asyncio.gather(*senders, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
