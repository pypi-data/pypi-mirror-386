"""基本情報技術者試験 科目B Python想定問題 (令和1年度 秋季相当)

在庫管理システムの受注数データから指数平滑法で翌週の需要を予測するサンプルです。
単純移動平均では遅れが生じるケースを題材に、平滑化係数を調整して敏感さを再現します。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class ForecastResult:
    smoothed: List[float]
    next_forecast: float


def single_exponential_smoothing(values: Iterable[float], alpha: float) -> ForecastResult:
    """Compute single exponential smoothing for the demand series.

    Args:
        values: Historical demand values.
        alpha: Smoothing factor between 0 and 1.

    Returns:
        ForecastResult containing smoothed series and the one-step-ahead forecast.
    """

    if not 0 < alpha <= 1:
        raise ValueError("alpha must be in (0, 1]")

    data = list(values)
    if not data:
        raise ValueError("values must not be empty")

    smoothed: List[float] = [data[0]]
    for obs in data[1:]:
        smoothed.append(alpha * obs + (1 - alpha) * smoothed[-1])

    next_forecast = smoothed[-1]
    return ForecastResult(smoothed=smoothed, next_forecast=round(next_forecast, 2))


if __name__ == "__main__":  # pragma: no cover - manual study aid
    weekly_orders = [120, 135, 128, 150, 160, 158, 170]
    alpha = 0.4
    result = single_exponential_smoothing(weekly_orders, alpha)

    print("=== 指数平滑結果 ===")
    for week, smooth in enumerate(result.smoothed, start=1):
        print(f"週{week}: 平滑値 {smooth:.2f}")

    print("\n翌週予測")
    print(f"alpha={alpha} の設定では、翌週需要は {result.next_forecast:.2f} 件と予測")
