"""入門用サンプル: 選択ソート。

配列を昇順に並べ替えます（インプレース）。
"""

from __future__ import annotations

from typing import List


def selection_sort(a: List[int]) -> None:
    n = len(a)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if a[j] < a[min_idx]:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]


if __name__ == "__main__":  # pragma: no cover
    arr = [64, 25, 12, 22, 11]
    selection_sort(arr)
    print(arr)
