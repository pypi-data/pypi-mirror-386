"""中級サンプル: ランレングス圧縮 (RLE) と伸長。"""

from __future__ import annotations


def rle_encode(s: str) -> str:
    if not s:
        return ""
    out: list[str] = []
    prev = s[0]
    cnt = 1
    for ch in s[1:]:
        if ch == prev:
            cnt += 1
        else:
            out.append(f"{prev}{cnt}")
            prev, cnt = ch, 1
    out.append(f"{prev}{cnt}")
    return "".join(out)


def rle_decode(s: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        i += 1
        num = 0
        while i < len(s) and s[i].isdigit():
            num = num * 10 + int(s[i])
            i += 1
        out.append(ch * (num or 1))
    return "".join(out)


if __name__ == "__main__":  # pragma: no cover
    text = "aaabccccdd"
    enc = rle_encode(text)
    dec = rle_decode(enc)
    print(enc, dec)
