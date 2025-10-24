"""入門用サンプル: 1 から N までの合計を計算するだけの練習問題。

基本情報技術者試験の準備段階でウォームアップとして使えるように、ループと条件分岐をほぼ使わない
シンプルな例を用意しました。`sum_to_n` 関数は入力値のバリデーションも兼ねています。
"""

from __future__ import annotations


def sum_to_n(n: int) -> int:
    """Return 1 + 2 + ... + n.

    Raises:
        ValueError: if n is negative.
    """

    if n < 0:
        raise ValueError("n must be non-negative")
    total = 0
    for value in range(1, n + 1):
        total += value
    return total


if __name__ == "__main__":  # pragma: no cover - manual study aid
    import sys

    if len(sys.argv) > 1:
        target = int(sys.argv[1])
    else:
        target = 10
    print(f"1 から {target} までの合計は {sum_to_n(target)} です")
