"""入門用サンプル: 素数判定。

与えられた整数が素数かどうかを判定します。
"""

from __future__ import annotations

import math


def is_prime(n: int) -> bool:
    """Return True if n is a prime number, else False."""

    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    r = int(math.isqrt(n))
    f = 3
    while f <= r:
        if n % f == 0:
            return False
        f += 2
    return True


if __name__ == "__main__":  # pragma: no cover
    import sys

    x = int(sys.argv[1]) if len(sys.argv) > 1 else 29
    print(is_prime(x))
