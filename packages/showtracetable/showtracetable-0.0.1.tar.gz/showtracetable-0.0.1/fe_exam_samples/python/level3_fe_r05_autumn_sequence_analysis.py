"""基本情報技術者試験 科目B Python想定問題 (令和5年度 秋季相当)

交通系ICカードの改札通過ログから、連続する一定枚数の平均利用者数を求める処理を実装せよ、
という形式のサンプルです。実際の過去問を再現したものではなく、学習用にアレンジしています。

実装のポイント
----------------
- スライディングウィンドウで連続区間の合計を更新する
- 小数第2位までを四捨五入する
- 最頻出区間（最大平均値）とその開始インデックスを求める
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def sliding_window_average(values: Iterable[int], window: int) -> list[float]:
    """Compute moving averages for the given window size.

    Raises:
        ValueError: if window <= 0 or the data size is smaller than the window.
    """

    data = list(values)
    if window <= 0:
        raise ValueError("window must be positive")
    if len(data) < window:
        raise ValueError("not enough data for the specified window")

    window_sum = sum(data[:window])
    avgs: list[float] = [round(window_sum / window, 2)]
    for idx in range(window, len(data)):
        window_sum += data[idx] - data[idx - window]
        avgs.append(round(window_sum / window, 2))
    return avgs


@dataclass(frozen=True)
class PeakWindow:
    average: float
    start_index: int
    window: int


def find_peak_window(values: Iterable[int], window: int) -> PeakWindow:
    """Find the window with the highest moving average."""

    averages = sliding_window_average(values, window)
    max_avg = max(averages)
    start_idx = averages.index(max_avg)
    return PeakWindow(average=max_avg, start_index=start_idx, window=window)


if __name__ == "__main__":  # pragma: no cover - manual study aid
    morning_counts = [
        421,
        398,
        455,
        472,
        465,
        481,
        500,
        488,
        476,
        470,
        495,
        530,
        544,
        552,
    ]
    window = 3
    averages = sliding_window_average(morning_counts, window)
    peak = find_peak_window(morning_counts, window)

    print("=== 移動平均の結果 ===")
    for idx, avg in enumerate(averages):
        print(f"{idx + 1:2d}～{idx + window:2d}日目: {avg:5.2f} 人")

    print("\n最高平均値")
    print(f"最も混雑した連続{window}日は {peak.start_index + 1}～{peak.start_index + window} 日目で、平均 {peak.average:.2f} 人")
