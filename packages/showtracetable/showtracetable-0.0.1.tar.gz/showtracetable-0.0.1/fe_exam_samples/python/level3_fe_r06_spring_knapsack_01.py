"""
Level 3: 0/1 Knapsack (DP)

Given items (value, weight) and capacity W, compute max total value and one item set.
"""

from __future__ import annotations

from typing import List, Tuple

Item = Tuple[int, int]  # (value, weight)


def knapsack_01(items: List[Item], W: int) -> Tuple[int, List[int]]:
    n = len(items)
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        v, w = items[i - 1]
        for cap in range(W + 1):
            dp[i][cap] = dp[i - 1][cap]
            if w <= cap:
                dp[i][cap] = max(dp[i][cap], dp[i - 1][cap - w] + v)
    # reconstruct
    res: List[int] = []
    cap = W
    for i in range(n, 0, -1):
        if dp[i][cap] != dp[i - 1][cap]:
            res.append(i - 1)
            cap -= items[i - 1][1]
    res.reverse()
    return dp[n][W], res


if __name__ == "__main__":
    items: List[Item] = [(6, 2), (10, 2), (12, 3), (7, 1)]
    W = 5
    value, chosen = knapsack_01(items, W)
    print("max value:", value)
    print("chosen indices:", chosen)
