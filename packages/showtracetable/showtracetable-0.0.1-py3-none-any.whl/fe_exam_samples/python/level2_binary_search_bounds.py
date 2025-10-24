"""中級サンプル: 二分探索の境界 (lower_bound / upper_bound)。"""

from __future__ import annotations

from typing import List


def lower_bound(a: List[int], x: int) -> int:
    """最初に x 以上が現れる最小インデックスを返す。見つからなければ len(a)。"""

    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(a: List[int], x: int) -> int:
    """最初に x より大きい値が現れる最小インデックスを返す。見つからなければ len(a)。"""

    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo


if __name__ == "__main__":  # pragma: no cover
    arr = [1, 2, 2, 2, 3, 5]
    print(lower_bound(arr, 2), upper_bound(arr, 2))  # -> 1 4
