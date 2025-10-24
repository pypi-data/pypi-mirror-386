"""中級サンプル: 行列の転置。"""

from __future__ import annotations

from typing import List


def transpose(matrix: List[List[int]]) -> List[List[int]]:
    if not matrix:
        return []
    rows, cols = len(matrix), len(matrix[0])
    return [[matrix[r][c] for r in range(rows)] for c in range(cols)]


if __name__ == "__main__":  # pragma: no cover
    m = [[1, 2, 3], [4, 5, 6]]
    print(transpose(m))  # -> [[1,4,7],[2,5,8],[3,6,9]]
