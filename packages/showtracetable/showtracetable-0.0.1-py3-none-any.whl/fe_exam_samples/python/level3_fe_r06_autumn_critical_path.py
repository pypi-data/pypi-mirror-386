"""
Level 3: Critical Path Method (CPM)

Given a small DAG of tasks with durations, compute earliest start/finish times,
project duration, and list one critical path.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Tuple

Duration = Dict[str, int]
Edges = List[Tuple[str, str]]


def critical_path(nodes: List[str], edges: Edges, dur: Duration) -> Tuple[int, List[str]]:
    # Build graph, indegree, and predecessors
    adj: Dict[str, List[str]] = defaultdict(list)
    pred: Dict[str, List[str]] = defaultdict(list)
    indeg: Dict[str, int] = {u: 0 for u in nodes}
    for u, v in edges:
        adj[u].append(v)
        pred[v].append(u)
        indeg[v] += 1

    # topological order
    q = deque([u for u in nodes if indeg[u] == 0])
    topo: List[str] = []
    while q:
        u = q.popleft()
        topo.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

    # forward pass: earliest finish
    EF: Dict[str, int] = {u: 0 for u in nodes}
    for u in topo:
        # If no predecessors, earliest start is 0
        earliest_start = max((EF[p] for p in pred[u]), default=0)
        EF[u] = earliest_start + dur[u]

    project_duration = max(EF.values()) if EF else 0

    # backward pass: latest start/finish
    LS: Dict[str, int] = {u: project_duration - dur[u] for u in nodes}
    for u in reversed(topo):
        if adj[u]:
            # latest start is min over successors' LS - this task duration
            LS[u] = min(LS[v] - dur[u] for v in adj[u])

    # critical path: tasks with zero slack, follow from start to finish
    slack = {u: LS[u] - (EF[u] - dur[u]) for u in nodes}
    crit: List[str] = []
    # start at a zero-slack start node
    start_candidates = [u for u in topo if slack[u] == 0 and not any(u in adj[p] for p in nodes)]
    cur = start_candidates[0] if start_candidates else (topo[0] if topo else None)
    while cur is not None:
        crit.append(cur)
        nxt = None
        for v in adj[cur]:
            if slack[v] == 0 and EF[v] == EF[cur] + dur[v]:
                nxt = v
                break
        cur = nxt

    return project_duration, crit


if __name__ == "__main__":
    nodes = ['S', 'A', 'B', 'C', 'D', 'E', 'T']
    edges: Edges = [
        ('S', 'A'),
        ('S', 'B'),
        ('A', 'C'),
        ('B', 'C'),
        ('C', 'D'),
        ('C', 'E'),
        ('D', 'T'),
        ('E', 'T'),
    ]
    dur: Duration = {'S': 0, 'A': 3, 'B': 2, 'C': 4, 'D': 3, 'E': 2, 'T': 0}
    total, path = critical_path(nodes, edges, dur)
    print("project duration:", total)
    print("critical path:", "->".join(path))
