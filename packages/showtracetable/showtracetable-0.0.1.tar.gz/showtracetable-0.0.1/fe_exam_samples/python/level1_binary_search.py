"""入門用サンプル: 二分探索。

昇順配列に対して目標値のインデックスを返します（見つからなければ -1）。
"""

from __future__ import annotations

from typing import List


def binary_search(a: List[int], x: int) -> int:
    lo, hi = 0, len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


if __name__ == "__main__":  # pragma: no cover
    arr = [1, 3, 5, 7, 9, 11]
    print(binary_search(arr, 7))
