"""中級サンプル: 貪欲法によるコイン両替。

日本の硬貨 [500, 100, 50, 10, 5, 1] を使って最小枚数で金額を構成します。
"""

from __future__ import annotations

from typing import List, Tuple


def greedy_coin_change(amount: int, coins: List[int] | None = None) -> List[Tuple[int, int]]:
    if coins is None:
        coins = [500, 100, 50, 10, 5, 1]
    result: List[Tuple[int, int]] = []
    for c in coins:
        cnt, amount = divmod(amount, c)
        if cnt:
            result.append((c, cnt))
    return result


if __name__ == "__main__":  # pragma: no cover
    print(greedy_coin_change(999))
