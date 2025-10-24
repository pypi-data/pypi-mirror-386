"""入門用サンプル: while ループでカウントダウンする練習。

`countdown` 関数は与えられた非負整数から 0 までを一つずつ減らしながら値を記録します。
標準入力を使わずにコマンドライン引数やコードから直接呼び出せる作りにしています。
"""

from __future__ import annotations

from typing import List


def countdown(start: int) -> List[int]:
    """Return a list counting down from start to 0.

    Raises:
        ValueError: if start is negative.
    """

    if start < 0:
        raise ValueError("start must be non-negative")

    result: List[int] = []
    current = start
    while current >= 0:
        result.append(current)
        current -= 1
    return result


if __name__ == "__main__":  # pragma: no cover - manual study aid
    import sys

    start = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print("カウントダウン結果:", countdown(start))
