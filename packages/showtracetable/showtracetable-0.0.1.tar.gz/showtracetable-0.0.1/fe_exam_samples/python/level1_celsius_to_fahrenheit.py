"""入門用サンプル: 摂氏(°C)から華氏(°F)への変換。"""

from __future__ import annotations


def c_to_f(celsius: float) -> float:
    """Return Fahrenheit from Celsius using F = C * 9/5 + 32."""

    return celsius * 9.0 / 5.0 + 32.0


if __name__ == "__main__":  # pragma: no cover
    import sys

    c = float(sys.argv[1]) if len(sys.argv) > 1 else 25.0
    print(f"{c}°C = {c_to_f(c)}°F")
