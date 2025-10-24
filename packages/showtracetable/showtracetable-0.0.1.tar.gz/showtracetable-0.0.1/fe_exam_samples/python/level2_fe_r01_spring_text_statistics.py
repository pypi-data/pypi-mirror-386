"""基本情報技術者試験 科目B Python想定問題 (令和1年度 春季相当)

コールセンターの問い合わせ記録からキーワード出現頻度と平均文長を集計する文字列処理問題です。
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9ぁ-んァ-ン一-龠]+")


@dataclass(frozen=True)
class TextSummary:
    total_messages: int
    avg_tokens: float
    top_keywords: List[tuple[str, int]]


def summarize_messages(messages: Iterable[str], top_n: int = 5) -> TextSummary:
    """Tokenize text and compute frequency statistics."""

    msgs = [msg.strip() for msg in messages if msg.strip()]
    if not msgs:
        raise ValueError("messages must not be empty")

    tokenized = [TOKEN_PATTERN.findall(msg.lower()) for msg in msgs]
    token_counts = Counter(token for tokens in tokenized for token in tokens)
    avg_tokens = sum(len(tokens) for tokens in tokenized) / len(tokenized)

    return TextSummary(
        total_messages=len(msgs),
        avg_tokens=round(avg_tokens, 2),
        top_keywords=token_counts.most_common(top_n),
    )


if __name__ == "__main__":  # pragma: no cover - manual study aid
    logs = [
        "プリンタが印刷できない",
        "ネットワーク遅延が発生している",
        "プリンタの紙詰まりを解消したい",
        "VPN が接続できない",
        "ネットワークがときどき切断される",
    ]
    summary = summarize_messages(logs, top_n=3)
    print(f"件数: {summary.total_messages}")
    print(f"平均トークン数: {summary.avg_tokens}")
    print("上位キーワード:")
    for keyword, count in summary.top_keywords:
        print(f"- {keyword}: {count} 回")
