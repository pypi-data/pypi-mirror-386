"""中級サンプル: 区間マージ。

与えられた半開区間のリストをソートし、重なる区間をマージして最小個数にまとめます。
入力例: [(1,3), (2,6), (8,10), (9,12)] -> 出力例: [(1,6), (8,12)]
"""

from __future__ import annotations

from typing import List, Tuple


def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not intervals:
        return []
    intervals = sorted(intervals)
    merged: List[Tuple[int, int]] = [intervals[0]]
    for s, e in intervals[1:]:
        ls, le = merged[-1]
        if s <= le:
            merged[-1] = (ls, max(le, e))
        else:
            merged.append((s, e))
    return merged


if __name__ == "__main__":  # pragma: no cover
    sample = [(1, 3), (2, 6), (8, 10), (9, 12)]
    print(merge_intervals(sample))
