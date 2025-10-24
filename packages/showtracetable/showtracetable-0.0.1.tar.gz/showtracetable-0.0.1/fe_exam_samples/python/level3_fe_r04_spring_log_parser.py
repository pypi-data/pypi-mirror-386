"""基本情報技術者試験 科目B Python想定問題 (令和4年度 春季相当)

APIアクセスログから、利用制限を超えたユーザを抽出し、時系列サマリを作成する処理。
データのフィルタリングと辞書集計を中心とした問題をイメージしています。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class AccessLog:
    user_id: str
    timestamp: datetime
    status: int


RateLimitSummary = List[Tuple[str, int]]


def parse_log(line: str) -> AccessLog:
    """Convert a CSV line into an AccessLog."""

    user_id, ts, status = line.strip().split(",")
    return AccessLog(user_id=user_id, timestamp=datetime.fromisoformat(ts), status=int(status))


def summarize_rate_limit(logs: Iterable[AccessLog], threshold: int) -> RateLimitSummary:
    """Count consecutive error responses per user and report offenders."""

    errors: defaultdict[str, int] = defaultdict(int)
    offenders: defaultdict[str, int] = defaultdict(int)

    for log in sorted(logs, key=lambda log_: log_.timestamp):
        if log.status == 429:
            errors[log.user_id] += 1
            if errors[log.user_id] >= threshold:
                offenders[log.user_id] += 1
        else:
            errors[log.user_id] = 0

    return sorted(offenders.items(), key=lambda kv: kv[1], reverse=True)


if __name__ == "__main__":  # pragma: no cover - manual study aid
    raw_lines = [
        "alice,2024-05-20T09:00:00,200",
        "alice,2024-05-20T09:00:30,429",
        "alice,2024-05-20T09:01:10,429",
        "bob,2024-05-20T09:01:30,200",
        "alice,2024-05-20T09:01:40,429",
        "bob,2024-05-20T09:01:50,429",
        "bob,2024-05-20T09:02:10,429",
        "bob,2024-05-20T09:02:30,429",
    ]

    logs = [parse_log(line) for line in raw_lines]
    summary = summarize_rate_limit(logs, threshold=2)

    print("制限超過が疑われる利用者")
    for user, count in summary:
        print(f"{user}: {count} 回の連続超過")
