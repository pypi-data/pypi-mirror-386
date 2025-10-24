"""入門用サンプル: 線形探索。

リスト内にターゲットが存在するかどうかのブールを返します。
"""

from __future__ import annotations


def linear_search(items: list[int], target: int) -> bool:
    """Return True if target is in items, else False."""

    for x in items:
        if x == target:
            return True
    return False


if __name__ == "__main__":  # pragma: no cover
    data = [3, 1, 4, 1, 5]
    print(linear_search(data, 4))  # -> True
    print(linear_search(data, 9))  # -> False
