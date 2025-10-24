"""基本情報技術者試験 科目B Python想定問題 (令和5年度 秋季相当)

配送ロボットが倉庫内のポイント間を移動する際、最小ステップで目的地に到達する経路を求めよ。
有向グラフを BFS で探索する典型問題をサンプル化しました。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional

Graph = Dict[str, List[str]]


@dataclass
class PathResult:
    steps: int
    route: List[str]


def shortest_route(graph: Graph, start: str, goal: str) -> Optional[PathResult]:
    """Breadth-first search to obtain the shortest path between two nodes."""

    if start == goal:
        return PathResult(steps=0, route=[start])

    queue = deque([[start]])
    visited = {start}

    while queue:
        route = queue.popleft()
        current = route[-1]
        for neighbor in graph.get(current, []):
            if neighbor in visited:
                continue
            next_route = route + [neighbor]
            if neighbor == goal:
                return PathResult(steps=len(next_route) - 1, route=next_route)
            visited.add(neighbor)
            queue.append(next_route)
    return None


WAREHOUSE_GRAPH: Graph = {
    "A": ["B", "C"],
    "B": ["D", "E"],
    "C": ["F"],
    "D": ["G"],
    "E": ["G", "H"],
    "F": ["E"],
    "G": ["I"],
    "H": ["I"],
    "I": [],
}


if __name__ == "__main__":  # pragma: no cover - manual study aid
    result = shortest_route(WAREHOUSE_GRAPH, "A", "I")
    if result:
        print("最短経路を発見しました")
        print(f"手数: {result.steps}")
        print(" -> ".join(result.route))
    else:
        print("目的地に到達できませんでした")
