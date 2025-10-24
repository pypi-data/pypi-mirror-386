"""入門用サンプル: 階乗 (factorial) を計算します。

非負整数 n に対して n! = 1 * 2 * ... * n を返します。n=0 のとき 1 です。
"""

from __future__ import annotations


def factorial(n: int) -> int:
    """Return n! for non-negative integer n.

    Raises:
        ValueError: if n is negative.
    """

    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


if __name__ == "__main__":  # pragma: no cover - manual study aid
    import sys

    target = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"{target}! = {factorial(target)}")
