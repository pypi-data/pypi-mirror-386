"""超入門サンプル: 整数が正/負/ゼロのどれかを判定する練習問題。"""

from __future__ import annotations


def check_sign(value: int) -> str:
    """Return a label describing the sign of value."""

    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"


if __name__ == "__main__":  # pragma: no cover - manual study aid
    import sys

    target = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print(f"{target} は {check_sign(target)} です")
