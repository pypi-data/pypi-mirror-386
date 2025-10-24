"""
Level 3: Edit distance (Levenshtein)

Compute minimum edit distance between two strings and reconstruct one optimal alignment.
This script prints the distance and a simple alignment of the two strings.
"""

from __future__ import annotations

from typing import List, Tuple


def edit_distance(a: str, b: str) -> Tuple[int, str, str]:
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # delete
                dp[i][j - 1] + 1,  # insert
                dp[i - 1][j - 1] + cost,  # replace/match
            )
    # reconstruct alignment
    i, j = n, m
    ra: List[str] = []
    rb: List[str] = []
    while i > 0 or j > 0:
        if i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ra.append(a[i - 1])
            rb.append('-')
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            ra.append('-')
            rb.append(b[j - 1])
            j -= 1
        else:
            ra.append(a[i - 1] if i > 0 else '-')
            rb.append(b[j - 1] if j > 0 else '-')
            i -= 1
            j -= 1
    ra.reverse()
    rb.reverse()
    return dp[n][m], ''.join(ra), ''.join(rb)


if __name__ == "__main__":
    s1 = "algorithm"
    s2 = "altruistic"
    dist, al1, al2 = edit_distance(s1, s2)
    print("distance:", dist)
    print(al1)
    print(al2)
