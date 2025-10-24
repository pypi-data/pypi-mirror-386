"""中級サンプル: 括弧列の妥当性判定。

丸()、角[]、波{} の3種括弧が正しく対応・入れ子になっているかを判定します。
"""

from __future__ import annotations


def is_valid_brackets(s: str) -> bool:
    pairs = {')': '(', ']': '[', '}': '{'}
    stack: list[str] = []
    for ch in s:
        if ch in '([{':
            stack.append(ch)
        elif ch in ')]}':
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return not stack


if __name__ == "__main__":  # pragma: no cover
    tests = ["()[]{}", "([{}])", "(]", "([)]", "(("]
    for t in tests:
        print(t, is_valid_brackets(t))
