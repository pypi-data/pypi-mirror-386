"""基本情報技術者試験 科目B Python想定問題 (令和3年度 秋季相当)

クラウド上で実行するバッチジョブの選択問題を題材とした、ナップサック型の最適化サンプルです。
CPU 時間の上限内で収益が最大となるジョブの組み合わせを求めます。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class BatchJob:
    name: str
    cpu_hours: int
    revenue: int


def maximize_revenue(jobs: Sequence[BatchJob], cpu_budget: int) -> Tuple[int, List[BatchJob]]:
    """0/1 ナップサック法で最大収益を求める。

    Args:
        jobs: 候補ジョブのシーケンス。
        cpu_budget: 使用できる CPU 時間の総量。

    Returns:
        (最大収益, 採用したジョブのリスト)
    """

    if cpu_budget < 0:
        raise ValueError("cpu_budget must be non-negative")

    n = len(jobs)
    dp = [[0] * (cpu_budget + 1) for _ in range(n + 1)]

    for i, job in enumerate(jobs, start=1):
        for capacity in range(cpu_budget + 1):
            if job.cpu_hours > capacity:
                dp[i][capacity] = dp[i - 1][capacity]
            else:
                without_job = dp[i - 1][capacity]
                with_job = dp[i - 1][capacity - job.cpu_hours] + job.revenue
                dp[i][capacity] = max(without_job, with_job)

    selected: List[BatchJob] = []
    capacity = cpu_budget
    for i in range(n, 0, -1):
        if dp[i][capacity] != dp[i - 1][capacity]:
            job = jobs[i - 1]
            selected.append(job)
            capacity -= job.cpu_hours
    selected.reverse()
    return dp[n][cpu_budget], selected


if __name__ == "__main__":  # pragma: no cover - manual study aid
    candidates = [
        BatchJob("daily-report", cpu_hours=3, revenue=250),
        BatchJob("fraud-detect", cpu_hours=4, revenue=380),
        BatchJob("model-train", cpu_hours=6, revenue=610),
        BatchJob("log-archive", cpu_hours=2, revenue=150),
    ]
    budget = 7
    best_value, chosen = maximize_revenue(candidates, budget)
    print(f"CPU 予算 {budget}h での最大収益: {best_value}")
    print("採用ジョブ:")
    for job in chosen:
        print(f"- {job.name} ({job.cpu_hours}h, revenue={job.revenue})")
