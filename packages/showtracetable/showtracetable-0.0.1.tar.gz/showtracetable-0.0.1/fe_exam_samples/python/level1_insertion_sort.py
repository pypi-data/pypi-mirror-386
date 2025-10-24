"""入門用サンプル: 挿入ソート。

配列を昇順に並べ替えます（インプレース）。
"""

from __future__ import annotations

from typing import List


def insertion_sort(a: List[int]) -> None:
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key


if __name__ == "__main__":  # pragma: no cover
    arr = [12, 11, 13, 5, 6]
    insertion_sort(arr)
    print(arr)
