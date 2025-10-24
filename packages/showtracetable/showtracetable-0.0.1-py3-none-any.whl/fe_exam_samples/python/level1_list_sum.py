"""入門用サンプル: リスト内の合計を計算。"""

from __future__ import annotations


def list_sum(items: list[int]) -> int:
    """Return the sum of integers in items."""

    total = 0
    for x in items:
        total += x
    return total


if __name__ == "__main__":  # pragma: no cover
    data = [1, 2, 3, 4]
    print(list_sum(data))
