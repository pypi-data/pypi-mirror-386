"""入門用サンプル: 回文判定。

与えられた文字列が前から読んでも後ろから読んでも同じかどうかを返します。
"""

from __future__ import annotations


def is_palindrome(s: str) -> bool:
    """Return True if s is a palindrome, else False."""

    t = s.lower()
    return t == t[::-1]


if __name__ == "__main__":  # pragma: no cover
    import sys

    s = sys.argv[1] if len(sys.argv) > 1 else "level"
    print(is_palindrome(s))
