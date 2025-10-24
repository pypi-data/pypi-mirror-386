"""入門用サンプル: リストの最小値を求める。"""

from __future__ import annotations


def min_of_list(items: list[int]) -> int:
    """Return the minimum value in items.

    Raises:
        ValueError: if items is empty.
    """

    if not items:
        raise ValueError("items must not be empty")
    m = items[0]
    for x in items[1:]:
        if x < m:
            m = x
    return m


if __name__ == "__main__":  # pragma: no cover
    data = [5, 3, 8, 1, 4]
    print(min_of_list(data))  # -> 1
