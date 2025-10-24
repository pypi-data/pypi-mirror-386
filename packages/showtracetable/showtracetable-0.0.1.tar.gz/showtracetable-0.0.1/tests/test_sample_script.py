#!/usr/bin/env python3
"""
テスト用のサンプルスクリプト
トレーサーの機能をテストするためのシンプルなコード
"""


def fibonacci(n):
    """フィボナッチ数を計算する再帰関数"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


class Calculator:
    """簡単な計算機クラス"""

    def __init__(self, initial_value=0):
        self.value = initial_value

    def add(self, x):
        self.value += x
        return self.value

    def multiply(self, x):
        self.value *= x
        return self.value


def process_list(items):
    """リストを処理する関数"""
    result = []
    for item in items:
        if isinstance(item, int) and item > 0:
            result.append(item * 2)
        elif isinstance(item, str):
            result.append(item.upper())
        else:
            result.append(None)
    return result


def main():
    """メイン関数"""
    print("トレーサーテスト開始")

    # フィボナッチ数の計算
    fib_result = fibonacci(5)
    print(f"fibonacci(5) = {fib_result}")

    # 計算機クラスの使用
    calc = Calculator(10)
    calc.add(5)
    calc.multiply(2)
    print(f"計算結果: {calc.value}")

    # リスト処理
    data = [1, 2, "hello", -1, 3, "world"]
    processed = process_list(data)
    print(f"処理結果: {processed}")

    # 例外処理
    try:
        10 / 0
    except ZeroDivisionError as e:
        print(f"例外発生: {e}")

    print("トレーサーテスト終了")


if __name__ == "__main__":
    main()
