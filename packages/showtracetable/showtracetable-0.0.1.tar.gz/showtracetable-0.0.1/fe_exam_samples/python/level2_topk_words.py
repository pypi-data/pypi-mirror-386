"""中級サンプル: 文字列中の単語を数えて上位Kを求める。"""

from __future__ import annotations

from collections import Counter
from typing import List


def top_k_words(text: str, k: int) -> List[tuple[str, int]]:
    words = [w for w in text.lower().split() if w.isalpha()]
    cnt = Counter(words)
    return cnt.most_common(k)


if __name__ == "__main__":  # pragma: no cover
    text = "to be or not to be that is the question"
    print(top_k_words(text, 3))
