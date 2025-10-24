"""入門用サンプル: 文字列の長さを返す。"""

from __future__ import annotations


def string_length(s: str) -> int:
    """Return length of string s without using len() (学習用)。"""

    count = 0
    for _ in s:
        count += 1
    return count


if __name__ == "__main__":  # pragma: no cover
    import sys

    s = sys.argv[1] if len(sys.argv) > 1 else "hello"
    print(string_length(s))
