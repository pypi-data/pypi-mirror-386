#!/usr/bin/env python3
"""
テスト用のサンプルスクリプト2
トレーサーの機能をテストするための追加コード
ジェネレーター、デコレーター、コンテキストマネージャーなどを含む
"""

import contextlib
import time


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


def timing_decorator(func):
    """実行時間を計測するデコレーター"""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result

    return wrapper


def fibonacci_generator(n):
    """フィボナッチ数を生成するジェネレーター"""
    a, b = 0, 1
    count = 0
    while count < n:
        yield a
        a, b = b, a + b
        count += 1


class Stack:
    """スタックの実装"""

    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None

    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        return None

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)


class AdvancedCalculator(Calculator):
    """Calculatorを継承した高度な計算機"""

    def __init__(self, initial_value=0):
        super().__init__(initial_value)
        self.history = []

    def add(self, x):
        result = super().add(x)
        self.history.append(f"add({x}) -> {result}")
        return result

    def power(self, exponent):
        self.value **= exponent
        self.history.append(f"power({exponent}) -> {self.value}")
        return self.value


@contextlib.contextmanager
def timer_context(name):
    """実行時間を計測するコンテキストマネージャー"""
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        print(f"{name} took {end_time - start_time:.4f} seconds")


def process_dict(data):
    """辞書を処理する関数"""
    result = {}
    for key, value in data.items():
        if isinstance(value, int):
            result[key] = value * 3
        elif isinstance(value, str):
            result[key] = value[::-1]  # 文字列を反転
        elif isinstance(value, list):
            result[key] = [x**2 for x in value if isinstance(x, int)]
        else:
            result[key] = str(type(value).__name__)
    return result


@timing_decorator
def complex_computation():
    """複雑な計算を行う関数"""
    result = 0
    for i in range(1000):
        if i % 2 == 0:
            result += i**2
        else:
            result -= i // 2
    return result


def main():
    """メイン関数"""
    print("トレーサーテスト2開始")

    # ジェネレーターのテスト
    print("ジェネレーター:")
    fib_gen = fibonacci_generator(10)
    fib_list = list(fib_gen)
    print(f"フィボナッチ数列: {fib_list}")

    # スタッククラスのテスト
    print("\nスタック:")
    stack = Stack()
    for item in [1, 2, 3, 4, 5]:
        stack.push(item)
    print(f"スタックサイズ: {stack.size()}")
    while not stack.is_empty():
        print(f"ポップ: {stack.pop()}")

    # 継承クラスのテスト
    print("\n高度な計算機:")
    adv_calc = AdvancedCalculator(5)
    adv_calc.add(10)
    adv_calc.power(2)
    print(f"最終値: {adv_calc.value}")
    print(f"履歴: {adv_calc.history}")

    # コンテキストマネージャーのテスト
    print("\nコンテキストマネージャー:")
    with timer_context("辞書処理"):
        data = {'numbers': [1, 2, 3, 4], 'text': 'hello', 'count': 42, 'other': None}
        processed = process_dict(data)
        print(f"処理結果: {processed}")

    # デコレーター付き関数のテスト
    print("\nデコレーター付き関数:")
    result = complex_computation()
    print(f"計算結果: {result}")

    # 例外処理
    try:
        with timer_context("例外テスト"):
            raise ValueError("テスト例外")
    except ValueError as e:
        print(f"例外捕捉: {e}")

    print("トレーサーテスト2終了")


if __name__ == "__main__":
    main()
