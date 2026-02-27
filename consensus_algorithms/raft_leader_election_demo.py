"""
Raft Leader Election Demo (Simplified)
======================================

This example is intentionally small and focuses on *election + heartbeats* only.
It is useful for learning Raft's control flow, but it is NOT a full Raft implementation.

What this demo includes:
1) Follower -> Candidate transition on election timeout
2) RequestVote / VoteResponse exchange
3) Majority-based leader election
4) Leader heartbeats (AppendEntries without log data)
5) Re-election after simulated leader failure

What this demo omits:
- Log replication
- Commit index / state machine apply
- Persistent state and crash recovery
- Log consistency checks (last log index/term)
"""

from __future__ import annotations

import queue
import random
import threading
import time
from dataclasses import dataclass


FOLLOWER = "Follower"
CANDIDATE = "Candidate"
LEADER = "Leader"


@dataclass(frozen=True)
class RequestVote:
    term: int
    candidate_id: int


@dataclass(frozen=True)
class VoteResponse:
    term: int
    voter_id: int
    vote_granted: bool


@dataclass(frozen=True)
class AppendEntries:
    # In real Raft this carries log entries + prev_log checks.
    # Here it acts only as heartbeat.
    term: int
    leader_id: int


class Cluster:
    """
    Tiny in-memory transport.
    Each node has an inbox queue, and messages are delivered by putting items into queues.
    """

    def __init__(self, node_ids: list[int]) -> None:
        self.inboxes = {node_id: queue.Queue() for node_id in node_ids}

    def send(self, target_id: int, message: object) -> None:
        self.inboxes[target_id].put(message)

    def broadcast(self, sender_id: int, message: object) -> None:
        for target_id in self.inboxes:
            if target_id != sender_id:
                self.send(target_id, message)


class RaftNode(threading.Thread):
    """
    One node in the cluster.
    Thread loop:
    - process inbound messages
    - check election timeout
    - if leader, send periodic heartbeats
    """

    def __init__(self, node_id: int, all_node_ids: list[int], cluster: Cluster):
        super().__init__(daemon=True)
        self.node_id = node_id
        self.all_node_ids = all_node_ids
        self.cluster = cluster
        self.inbox = cluster.inboxes[node_id]

        self.role = FOLLOWER
        self.current_term = 0
        self.voted_for: int | None = None
        self.votes_received: set[int] = set()

        self.heartbeat_interval = 0.5
        self.last_heartbeat_sent = 0.0
        self.election_deadline = self._next_election_deadline()

        self.running = True

    def _next_election_deadline(self) -> float:
        # Randomized timeout reduces chance of split votes.
        return time.monotonic() + random.uniform(1.5, 3.0)

    def _majority(self) -> int:
        return len(self.all_node_ids) // 2 + 1

    def run(self) -> None:
        self._log(f"started as {self.role}")
        while self.running:
            self._drain_inbox()
            self._check_timers()
            time.sleep(0.05)

    def stop(self) -> None:
        self.running = False

    def _drain_inbox(self) -> None:
        while True:
            try:
                msg = self.inbox.get_nowait()
            except queue.Empty:
                return

            if isinstance(msg, RequestVote):
                self._on_request_vote(msg)
            elif isinstance(msg, VoteResponse):
                self._on_vote_response(msg)
            elif isinstance(msg, AppendEntries):
                self._on_append_entries(msg)

    def _check_timers(self) -> None:
        now = time.monotonic()

        # Followers/Candidates start election when timeout expires.
        if self.role in (FOLLOWER, CANDIDATE) and now >= self.election_deadline:
            self._start_election()

        # Leaders send heartbeats at fixed interval.
        if self.role == LEADER and (now - self.last_heartbeat_sent) >= self.heartbeat_interval:
            self.cluster.broadcast(
                self.node_id,
                AppendEntries(term=self.current_term, leader_id=self.node_id),
            )
            self.last_heartbeat_sent = now

    def _start_election(self) -> None:
        self.role = CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self.election_deadline = self._next_election_deadline()

        self._log(f"timeout -> starts election for term {self.current_term}")
        self.cluster.broadcast(
            self.node_id,
            RequestVote(term=self.current_term, candidate_id=self.node_id),
        )

    def _become_follower(self, new_term: int) -> None:
        self.role = FOLLOWER
        self.current_term = new_term
        self.voted_for = None
        self.votes_received.clear()
        self.election_deadline = self._next_election_deadline()

    def _become_leader(self) -> None:
        self.role = LEADER
        self.last_heartbeat_sent = 0.0  # send heartbeat immediately next loop
        self._log(f"wins term {self.current_term} -> becomes LEADER")

    def _on_request_vote(self, msg: RequestVote) -> None:
        # If we see a newer term, step down.
        if msg.term > self.current_term:
            self._become_follower(msg.term)

        grant = False
        if msg.term == self.current_term:
            # Simplified vote rule: one vote per term.
            if self.voted_for is None or self.voted_for == msg.candidate_id:
                self.voted_for = msg.candidate_id
                grant = True
                self.election_deadline = self._next_election_deadline()

        self.cluster.send(
            msg.candidate_id,
            VoteResponse(
                term=self.current_term,
                voter_id=self.node_id,
                vote_granted=grant,
            ),
        )

    def _on_vote_response(self, msg: VoteResponse) -> None:
        # Ignore stale terms.
        if msg.term > self.current_term:
            self._become_follower(msg.term)
            return

        if self.role != CANDIDATE or msg.term != self.current_term:
            return

        if msg.vote_granted:
            self.votes_received.add(msg.voter_id)
            if len(self.votes_received) >= self._majority():
                self._become_leader()

    def _on_append_entries(self, msg: AppendEntries) -> None:
        # Heartbeat from leader.
        if msg.term < self.current_term:
            return

        # Newer/same term heartbeat => follow that leader.
        if msg.term > self.current_term or self.role != FOLLOWER:
            self._become_follower(msg.term)
        self.election_deadline = self._next_election_deadline()

    def _log(self, text: str) -> None:
        print(f"[node {self.node_id}] {text}", flush=True)


def find_current_leader(nodes: list[RaftNode]) -> RaftNode | None:
    leaders = [n for n in nodes if n.role == LEADER and n.running]
    return leaders[0] if leaders else None


def main() -> None:
    """
    Demo plan:
    - Start 5 nodes
    - Wait for leader election
    - Stop leader once to force a re-election
    - Stop all nodes
    """
    random.seed(42)
    node_ids = [0, 1, 2, 3, 4]
    cluster = Cluster(node_ids)
    nodes = [RaftNode(node_id=i, all_node_ids=node_ids, cluster=cluster) for i in node_ids]

    print("Starting Raft leader-election demo...\n", flush=True)
    for n in nodes:
        n.start()

    time.sleep(4)
    leader = find_current_leader(nodes)
    if leader is not None:
        print(f"\nSimulating leader failure: stopping node {leader.node_id}\n", flush=True)
        leader.stop()
    else:
        print("\nNo leader found yet at 4s (rare timing case). Continuing...\n", flush=True)

    time.sleep(5)

    print("\nStopping cluster...", flush=True)
    for n in nodes:
        n.stop()
    for n in nodes:
        n.join(timeout=1)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
