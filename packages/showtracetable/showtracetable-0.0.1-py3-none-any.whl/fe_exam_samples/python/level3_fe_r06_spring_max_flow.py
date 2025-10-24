"""
Level 3: Maximum Flow (Edmonds-Karp)

Compute max flow on a small directed graph. Prints the max flow value and one flow assignment.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, Tuple

Graph = Dict[str, Dict[str, int]]  # capacity graph


def edmonds_karp(cap: Graph, s: str, t: str) -> Tuple[int, Graph]:
    # residual capacity
    res: Graph = {u: dict(v) for u, v in cap.items()}
    for u in list(cap.keys()):
        for v in list(cap[u].keys()):
            res.setdefault(v, {})
            res[v].setdefault(u, 0)
    max_flow = 0
    parent: Dict[str, str] = {}

    def bfs() -> int:
        nonlocal parent
        parent = {s: ''}
        q = deque([(s, 10**18)])
        while q:
            u, flow = q.popleft()
            for v, c in res.get(u, {}).items():
                if c > 0 and v not in parent:
                    parent[v] = u
                    new_flow = min(flow, c)
                    if v == t:
                        return new_flow
                    q.append((v, new_flow))
        return 0

    while True:
        f = bfs()
        if f == 0:
            break
        max_flow += f
        v = t
        while v != s:
            u = parent[v]
            res[u][v] -= f
            res[v][u] += f
            v = u
    # derive actual flow from residuals and capacities
    flow: Graph = {u: {} for u in cap}
    for u in cap:
        for v in cap[u]:
            used = cap[u][v] - res[u][v]
            if used:
                flow[u][v] = used
    return max_flow, flow


def sample_cap_graph() -> Graph:
    return {
        'S': {'A': 10, 'C': 10},
        'A': {'B': 4, 'C': 2, 'D': 8},
        'B': {'T': 10},
        'C': {'D': 9},
        'D': {'B': 6, 'T': 10},
        'T': {},
    }


if __name__ == "__main__":
    cap = sample_cap_graph()
    value, flow = edmonds_karp(cap, 'S', 'T')
    print("max flow:", value)
    for u in flow:
        for v in flow[u]:
            print(f"{u}->{v}: {flow[u][v]}")
