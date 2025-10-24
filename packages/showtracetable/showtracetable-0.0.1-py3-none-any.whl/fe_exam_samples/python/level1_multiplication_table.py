"""入門用サンプル: 指定した数の九九（乗法表）を表示する練習問題。

`multiplication_table` 関数は 1 から 9 までとの積を計算したリストを返します。繰り返し処理と
簡単な整形を学ぶ目的のサンプルです。
"""

from __future__ import annotations

from typing import List


def multiplication_table(n: int) -> List[int]:
    """Return the multiplication table (n × 1..9)."""

    if n <= 0:
        raise ValueError("n must be positive")

    result: List[int] = []
    for i in range(1, 10):
        result.append(n * i)
    return result


if __name__ == "__main__":  # pragma: no cover - manual study aid
    import sys

    target = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    products = multiplication_table(target)
    print(f"{target} の九九:")
    for idx, value in enumerate(products, start=1):
        print(f"{target} × {idx} = {value}")
