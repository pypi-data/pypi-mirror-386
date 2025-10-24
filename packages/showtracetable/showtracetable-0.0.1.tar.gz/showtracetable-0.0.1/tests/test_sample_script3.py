#!/usr/bin/env python3
"""
テスト用のサンプルスクリプト3
さまざまな Python 機能（データクラス、デコレーター、非同期処理、コンテキストマネージャーなど）の動作確認用。
"""

from __future__ import annotations

import asyncio
import contextlib
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List


def trace_call(prefix: str = "TRACE") -> Callable[[Callable], Callable]:
    """シンプルなデコレーター: 呼び出しと戻り値を表示する"""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            print(f"{prefix}: calling {func.__name__} with args={args}, kwargs={kwargs}")
            result = func(*args, **kwargs)
            print(f"{prefix}: {func.__name__} returned {result}")
            return result

        return wrapper

    return decorator


@dataclass
class ScoreBoard:
    """スコア管理用のデータクラス"""

    name: str
    scores: List[int] = field(default_factory=list)

    def add(self, value: int) -> None:
        self.scores.append(value)

    @property
    def average(self) -> float:
        if not self.scores:
            return 0.0
        return sum(self.scores) / len(self.scores)


@trace_call("CALC")
def harmonic_mean(values: Iterable[int]) -> float:
    """調和平均を計算する"""
    values = list(values)
    if not values:
        return 0.0
    return len(values) / sum(1 / v for v in values if v != 0)


async def async_double(value: int) -> int:
    """疑似的な非同期計算"""
    await asyncio.sleep(0.01)
    return value * 2


@contextlib.contextmanager
def temp_workspace(label: str):
    """一時的なディレクトリを作成するコンテキストマネージャー"""
    base = Path.cwd() / "tmp_samples"
    base.mkdir(exist_ok=True)
    target = base / label
    target.mkdir(exist_ok=True)
    try:
        print(f"created workspace: {target}")
        yield target
    finally:
        print(f"workspace ready for cleanup: {target}")


def number_stream(limit: int) -> Iterable[int]:
    for i in range(1, limit + 1):
        if i % 2 == 0:
            yield i


def summarize_numbers(values: Iterable[int]) -> Dict[str, float]:
    filtered = list(values)
    return {
        "count": len(filtered),
        "sum": float(sum(filtered)),
        "mean": float(sum(filtered) / len(filtered)) if filtered else 0.0,
        "rms": math.sqrt(sum(v * v for v in filtered) / len(filtered)) if filtered else 0.0,
    }


def main() -> None:
    print("トレーサーテスト3開始")

    board = ScoreBoard("daily")
    for value in [7, 12, 3, 9]:
        board.add(value)
    print(f"scores: {board.scores}")
    print(f"average: {board.average:.2f}")

    hm = harmonic_mean(board.scores)
    print(f"harmonic mean: {hm:.2f}")

    with temp_workspace("analysis") as root:
        data_file = root / "summary.txt"
        metrics = summarize_numbers(number_stream(10))
        lines = [f"{key}={value}\n" for key, value in metrics.items()]
        data_file.write_text("".join(lines), encoding="utf-8")
        print(f"saved metrics to {data_file}")

    async def run_async_jobs() -> List[int]:
        tasks = [async_double(v) for v in board.scores]
        return await asyncio.gather(*tasks)

    doubled = asyncio.run(run_async_jobs())
    print(f"async doubled scores: {doubled}")

    print("トレーサーテスト3終了")


if __name__ == "__main__":
    main()
