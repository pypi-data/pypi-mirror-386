"""入門用サンプル: リストから偶数だけを取り出す練習問題。

基本構文の復習を目的に、`filter_even` 関数は while も list comprehension も
使わず for 文で丁寧に書いています。
"""

from __future__ import annotations

from typing import Iterable, List


def filter_even(values: Iterable[int]) -> List[int]:
    """Return all even integers from values."""

    evens: List[int] = []
    for value in values:
        if value % 2 == 0:
            evens.append(value)
    return evens


if __name__ == "__main__":  # pragma: no cover - manual study aid
    data = [1, 2, 3, 4, 10, 11]
    print("対象データ:", data)
    print("偶数のみ:", filter_even(data))
