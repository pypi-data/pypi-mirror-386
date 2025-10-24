"""
Level 3: Weighted shortest path (Dijkstra)

Small directed weighted graph. Find the shortest path from A to G.
This script prints the path cost and the path itself.
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Tuple

Graph = Dict[str, List[Tuple[str, int]]]


def dijkstra(graph: Graph, start: str, goal: str) -> Tuple[int, List[str]]:
    INF = 10**18
    dist: Dict[str, int] = {v: INF for v in graph}
    prev: Dict[str, str | None] = {v: None for v in graph}
    dist[start] = 0
    pq: List[Tuple[int, str]] = [(0, start)]
    visited = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        if u == goal:
            break
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if dist.get(goal, INF) == INF:
        return INF, []
    # reconstruct
    path: List[str] = []
    cur: str | None = goal
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
    path.reverse()
    return dist[goal], path


def build_sample_graph() -> Graph:
    # A small graph with positive weights
    return {
        'A': [('B', 4), ('C', 2)],
        'B': [('C', 5), ('D', 10)],
        'C': [('E', 3)],
        'D': [('F', 11)],
        'E': [('D', 4)],
        'F': [('G', 1)],
        'G': [],
    }


if __name__ == "__main__":
    g = build_sample_graph()
    cost, path = dijkstra(g, 'A', 'G')
    if cost >= 10**17:
        print("no path")
    else:
        print(f"shortest cost: {cost}")
        print("path:", "->".join(path))
