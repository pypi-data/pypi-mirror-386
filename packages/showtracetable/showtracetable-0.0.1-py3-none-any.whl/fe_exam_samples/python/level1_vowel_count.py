"""入門用サンプル: 文字列の母音(a, i, u, e, o)の個数を数える。"""

from __future__ import annotations


def vowel_count(s: str) -> int:
    """Return the number of vowels in s (case-insensitive)."""

    vowels = set("aiueo")
    return sum(1 for ch in s.lower() if ch in vowels)


if __name__ == "__main__":  # pragma: no cover
    import sys

    s = sys.argv[1] if len(sys.argv) > 1 else "Programming"
    print(vowel_count(s))
