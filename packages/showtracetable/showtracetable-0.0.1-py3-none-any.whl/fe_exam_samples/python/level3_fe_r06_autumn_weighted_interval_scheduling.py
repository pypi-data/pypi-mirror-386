"""
Level 3: Weighted interval scheduling

Given jobs (start, end, weight), choose non-overlapping jobs with maximum total weight.
This script prints the optimal value and a selected set of job indices (0-based).
"""

from __future__ import annotations

import bisect
from typing import List, Tuple

Job = Tuple[int, int, int]  # (start, end, weight)


def weighted_interval_scheduling(jobs: List[Job]) -> Tuple[int, List[int]]:
    # sort by end time
    jobs_sorted = sorted(enumerate(jobs), key=lambda x: x[1][1])
    n = len(jobs_sorted)
    ends = [jobs_sorted[i][1][1] for i in range(n)]
    # p[i]: the last job index (in sorted order) that doesn't overlap with i
    p = [0] * n
    for i in range(n):
        s_i = jobs_sorted[i][1][0]
        j = bisect.bisect_right(ends, s_i) - 1
        p[i] = j
    # DP
    dp = [0] * (n + 1)
    take = [False] * n
    for i in range(1, n + 1):
        w_i = jobs_sorted[i - 1][1][2]
        not_take = dp[i - 1]
        take_val = w_i + (dp[p[i - 1] + 1] if p[i - 1] >= 0 else 0)
        if take_val > not_take:
            dp[i] = take_val
            take[i - 1] = True
        else:
            dp[i] = not_take
    # reconstruct
    res_idx: List[int] = []
    i = n
    while i > 0:
        if take[i - 1]:
            res_idx.append(jobs_sorted[i - 1][0])
            i = p[i - 1] + 1
        else:
            i -= 1
    res_idx.reverse()
    return dp[n], res_idx


if __name__ == "__main__":
    sample_jobs: List[Job] = [
        (1, 3, 5),
        (2, 5, 6),
        (4, 6, 5),
        (6, 7, 4),
        (5, 8, 11),
        (7, 9, 2),
    ]
    value, chosen = weighted_interval_scheduling(sample_jobs)
    print("optimal value:", value)
    print("chosen jobs:", chosen)
