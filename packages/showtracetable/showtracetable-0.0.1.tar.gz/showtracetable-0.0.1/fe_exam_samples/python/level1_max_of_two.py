"""入門用サンプル: 2 つの整数の大きい方を返すだけの練習問題。

`max_of_two` 関数は条件分岐の基礎確認を目的としています。Python 組み込みの `max` は使わずに、
if/else のみで実装しています。
"""

from __future__ import annotations


def max_of_two(a: int, b: int) -> int:
    """Return the larger of a and b."""

    if a >= b:
        return a
    return b


if __name__ == "__main__":  # pragma: no cover - manual study aid
    import sys

    if len(sys.argv) >= 3:
        first, second = int(sys.argv[1]), int(sys.argv[2])
    else:
        first, second = 7, 12
    print(f"{first} と {second} の大きい方は {max_of_two(first, second)} です")
