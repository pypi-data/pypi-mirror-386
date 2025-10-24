"""入門用サンプル: 最小公倍数 (LCM)。

2 整数の最小公倍数を求めます。
"""

from __future__ import annotations


def gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a // gcd(a, b) * b)


if __name__ == "__main__":  # pragma: no cover
    import sys

    a = int(sys.argv[1]) if len(sys.argv) > 1 else 21
    b = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    print(lcm(a, b))
