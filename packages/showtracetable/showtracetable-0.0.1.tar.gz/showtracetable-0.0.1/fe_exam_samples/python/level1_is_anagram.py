"""入門用サンプル: アナグラム判定。

2つの文字列がアナグラムかどうかを判定します（空白と大文字小文字は無視）。
"""

from __future__ import annotations


def is_anagram(a: str, b: str) -> bool:
    sa = sorted(ch for ch in a.lower() if not ch.isspace())
    sb = sorted(ch for ch in b.lower() if not ch.isspace())
    return sa == sb


if __name__ == "__main__":  # pragma: no cover
    s1 = "Listen"
    s2 = "Silent"
    print(is_anagram(s1, s2))
