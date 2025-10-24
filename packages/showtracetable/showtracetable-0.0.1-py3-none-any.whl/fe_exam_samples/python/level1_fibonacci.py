"""入門用サンプル: フィボナッチ数列の n 番目を返す。

F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2) (n>=2) の定義に従います。
"""

from __future__ import annotations


def fib(n: int) -> int:
    """Return the n-th Fibonacci number using an iterative approach.

    Raises:
        ValueError: if n is negative.
    """

    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


if __name__ == "__main__":  # pragma: no cover - manual study aid
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"F({n}) = {fib(n)}")
