"""入門用サンプル: 桁数カウント。

整数の桁数を数えます（負数は符号を除いた桁数）。
"""

from __future__ import annotations


def count_digits(n: int) -> int:
    n = abs(n)
    if n == 0:
        return 1
    c = 0
    while n:
        c += 1
        n //= 10
    return c


if __name__ == "__main__":  # pragma: no cover
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1002003
    print(count_digits(n))
