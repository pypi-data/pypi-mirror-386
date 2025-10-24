"""中級サンプル: アナグラムの分組。"""

from __future__ import annotations

from collections import defaultdict
from typing import List


def group_anagrams(words: List[str]) -> List[List[str]]:
    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for w in words:
        key = tuple(sorted(w))
        groups[key].append(w)
    return list(groups.values())


if __name__ == "__main__":  # pragma: no cover
    words = ["eat", "tea", "tan", "ate", "nat", "bat"]
    print(group_anagrams(words))
