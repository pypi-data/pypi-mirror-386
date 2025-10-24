"""入門用サンプル: バブルソート。

配列を昇順に並べ替えます（インプレース）。
"""

from __future__ import annotations

from typing import List


def bubble_sort(a: List[int]) -> None:
    n = len(a)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break


if __name__ == "__main__":  # pragma: no cover
    arr = [5, 1, 4, 2, 8]
    bubble_sort(arr)
    print(arr)
