"""基本情報技術者試験 科目B Python想定問題 (令和3年度 春季相当)

IoT センサーの状態ログを解析し、短時間に連続した異常が発生した区間を検出する問題です。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Sequence


@dataclass(frozen=True)
class SensorLog:
    timestamp: datetime
    status: str  # "OK", "WARN", "ERROR" など


@dataclass(frozen=True)
class AlertWindow:
    start: datetime
    end: datetime
    count: int


VALID_STATUSES = {"OK", "WARN", "ERROR"}


def parse_log(line: str) -> SensorLog:
    ts_str, status = line.strip().split(",")
    if status not in VALID_STATUSES:
        raise ValueError(f"Unknown status: {status}")
    return SensorLog(timestamp=datetime.fromisoformat(ts_str), status=status)


def detect_alert_windows(logs: Sequence[SensorLog], window_seconds: int, min_errors: int) -> List[AlertWindow]:
    """滑動時間窓内の ERROR 回数を集計し、閾値を超えた区間を返す。"""

    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    if min_errors <= 0:
        raise ValueError("min_errors must be positive")

    result: List[AlertWindow] = []
    left = 0
    errors = 0
    logs_sorted = sorted(logs, key=lambda log: log.timestamp)
    for right, current in enumerate(logs_sorted):
        if current.status == "ERROR":
            errors += 1
        window_start = current.timestamp - timedelta(seconds=window_seconds)
        while logs_sorted[left].timestamp < window_start:
            if logs_sorted[left].status == "ERROR":
                errors -= 1
            left += 1
        if errors >= min_errors:
            result.append(
                AlertWindow(
                    start=logs_sorted[left].timestamp,
                    end=current.timestamp,
                    count=errors,
                )
            )
    return result


if __name__ == "__main__":  # pragma: no cover - manual study aid
    lines = [
        "2024-06-01T09:00:00,OK",
        "2024-06-01T09:00:05,WARN",
        "2024-06-01T09:00:08,ERROR",
        "2024-06-01T09:00:10,ERROR",
        "2024-06-01T09:00:14,OK",
        "2024-06-01T09:00:18,ERROR",
        "2024-06-01T09:00:22,ERROR",
    ]
    windows = detect_alert_windows([parse_log(line) for line in lines], window_seconds=10, min_errors=2)
    print("警戒区間を検出")
    for w in windows:
        print(f"{w.start.isoformat()} - {w.end.isoformat()} : {w.count} errors")
