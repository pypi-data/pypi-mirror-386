"""入門用サンプル: リストから重複を取り除く (順序保持)。"""

from __future__ import annotations


def unique_elements(items: list[int]) -> list[int]:
    """Return a new list with duplicates removed while preserving order."""

    seen: set[int] = set()
    result: list[int] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


if __name__ == "__main__":  # pragma: no cover
    data = [1, 2, 2, 3, 1, 4, 3]
    print(unique_elements(data))  # -> [1, 2, 3, 4]
