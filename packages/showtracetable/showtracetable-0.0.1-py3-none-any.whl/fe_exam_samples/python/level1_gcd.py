"""入門用サンプル: 最大公約数 (GCD)。

ユークリッドの互除法で 2 整数の最大公約数を求めます。
"""

from __future__ import annotations


def gcd(a: int, b: int) -> int:
    """Return greatest common divisor of a and b."""

    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


if __name__ == "__main__":  # pragma: no cover
    import sys

    a = int(sys.argv[1]) if len(sys.argv) > 1 else 54
    b = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    print(gcd(a, b))
