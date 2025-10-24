"""入門用サンプル: 各位和（digit sum）。

整数の各桁の合計を返します。
"""

from __future__ import annotations


def digit_sum(n: int) -> int:
    n = abs(n)
    s = 0
    while n:
        s += n % 10
        n //= 10
    return s


if __name__ == "__main__":  # pragma: no cover
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12345
    print(digit_sum(n))
