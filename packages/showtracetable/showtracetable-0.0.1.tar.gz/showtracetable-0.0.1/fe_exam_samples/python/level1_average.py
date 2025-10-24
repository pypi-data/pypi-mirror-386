"""超入門サンプル: 数値リストの平均値を計算する練習問題。

`simple_average` 関数は空リストのときに 0 を返すよう設計し、エラーを避けつつ
for 文と累積加算の練習ができるようにしています。
"""

from __future__ import annotations

from typing import Iterable


def simple_average(values: Iterable[float]) -> float:
    """Return the arithmetic mean of values or 0.0 when empty."""

    total = 0.0
    count = 0
    for v in values:
        total += float(v)
        count += 1
    if count == 0:
        return 0.0
    return total / count


if __name__ == "__main__":  # pragma: no cover - manual study aid
    data = [10, 20, 30]
    print("データ:", data)
    print("平均:", simple_average(data))
