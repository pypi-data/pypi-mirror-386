"""入門用サンプル: 文字列のユニーク文字判定。

文字列に重複文字がないか（すべてユニークか）を返します。
"""

from __future__ import annotations


def has_all_unique_chars(s: str) -> bool:
    seen = set()
    for ch in s:
        if ch in seen:
            return False
        seen.add(ch)
    return True


if __name__ == "__main__":  # pragma: no cover
    print(has_all_unique_chars("abcdefg"))
