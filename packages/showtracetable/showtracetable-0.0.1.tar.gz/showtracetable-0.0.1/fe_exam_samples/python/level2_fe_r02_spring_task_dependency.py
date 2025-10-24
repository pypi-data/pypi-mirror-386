"""基本情報技術者試験 科目B Python想定問題 (令和2年度 春季相当)

開発タスクの依存関係を解析し、実行可能な順序を求めるトポロジカルソート問題です。
循環が存在する場合は例外を送出します。
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Sequence, Tuple

Task = str
Dependency = Tuple[Task, Task]  # (predecessor, successor)


def resolve_schedule(tasks: Sequence[Task], dependencies: Iterable[Dependency]) -> List[Task]:
    """Topologically sort tasks respecting the dependency relation."""

    graph: Dict[Task, List[Task]] = defaultdict(list)
    indegree: Dict[Task, int] = {task: 0 for task in tasks}

    for before, after in dependencies:
        graph[before].append(after)
        indegree.setdefault(before, 0)
        indegree.setdefault(after, 0)
        indegree[after] += 1

    queue = deque([task for task, deg in indegree.items() if deg == 0])
    order: List[Task] = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for nxt in graph[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(indegree):
        raise ValueError("Cycle detected in task dependencies")

    return order


if __name__ == "__main__":  # pragma: no cover - manual study aid
    tasks = ["design", "impl", "test", "deploy", "docs"]
    deps = [
        ("design", "impl"),
        ("impl", "test"),
        ("test", "deploy"),
        ("design", "docs"),
    ]
    order = resolve_schedule(tasks, deps)
    print("実行順序:")
    for idx, task in enumerate(order, start=1):
        print(f"{idx}. {task}")
