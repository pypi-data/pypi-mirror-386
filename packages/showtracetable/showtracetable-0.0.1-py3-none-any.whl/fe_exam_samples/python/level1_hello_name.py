"""超入門サンプル: 名前を指定してあいさつ文を生成するだけの練習。

`greet` 関数は文字列結合の基礎を確認するために用意しています。標準入力に依存せず、
コマンドライン引数またはデフォルト値で動作します。
"""

from __future__ import annotations


def greet(name: str) -> str:
    """Return a greeting message for the given name."""

    if not name:
        return "こんにちは"
    return f"こんにちは、{name}さん"


if __name__ == "__main__":  # pragma: no cover - manual study aid
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "Python"
    print(greet(target))
