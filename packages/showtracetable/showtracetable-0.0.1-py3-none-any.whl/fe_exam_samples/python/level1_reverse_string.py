"""入門用サンプル: 文字列を逆順に並べ替えるだけの練習問題。

スライス構文は使わず、for で一文字ずつ取り出して結合することで基礎操作を確認します。
"""

from __future__ import annotations


def reverse_string(text: str) -> str:
    """Return text reversed without using slicing."""

    chars = []
    for ch in text:
        chars.insert(0, ch)
    return "".join(chars)


if __name__ == "__main__":  # pragma: no cover - manual study aid
    sample = "Paiza"
    print("元の文字列:", sample)
    print("逆順:", reverse_string(sample))
