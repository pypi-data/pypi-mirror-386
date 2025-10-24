"""入門用サンプル: 2番目に大きい値。

配列中の2番目に大きい値を返します（重複ありでも対応）。
"""

from __future__ import annotations

from typing import List, Optional


def second_largest(a: List[int]) -> Optional[int]:
    if len(a) < 2:
        return None
    first = second = None
    for x in a:
        if first is None or x > first:
            if first is not None:
                second = first
            first = x
        elif x != first and (second is None or x > second):
            second = x
    return second


if __name__ == "__main__":  # pragma: no cover
    arr = [2, 1, 2, 5, 3]
    print(second_largest(arr))
