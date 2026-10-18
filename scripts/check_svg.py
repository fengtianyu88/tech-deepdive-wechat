# -*- coding: utf-8 -*-
"""SVG 几何自检：估算每个 <text> 的渲染宽度，检查是否溢出所属 <rect> 或画布边界。

用法:
    python check_svg.py <成稿.html>

它能抓到的：文字溢出圆角框、文字出血超出 viewBox。
它抓不到的：箭头穿文字、并列关系画成先后顺序、配色对比不足 —— 这类必须出图目视确认。
"""
import os
import re
import sys


def text_w(s, size):
    """粗估渲染宽度：CJK/全角 1.0em，ASCII 0.55em，空格 0.35em，弯引号按全角保守计"""
    w = 0.0
    for ch in s:
        if ch in "\u201c\u201d\u2018\u2019":
            w += 1.0
        elif ch == " ":
            w += 0.35
        elif ord(ch) > 0x2E80:
            w += 1.0
        else:
            w += 0.55
    return w * size


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法: python check_svg.py <成稿.html>")
    html_path = sys.argv[1]
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    problems = 0
    for si, m in enumerate(re.finditer(r"<svg[\s\S]*?</svg>", html), 1):
        svg = m.group(0)
        vb = re.search(r'viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"', svg)
        vw, vh = float(vb.group(1)), float(vb.group(2))
        rects = []
        for r in re.finditer(r'<rect x="(-?\d+(?:\.\d+)?)" y="(-?\d+(?:\.\d+)?)" '
                             r'width="(\d+(?:\.\d+)?)" height="(\d+(?:\.\d+)?)"', svg):
            rects.append(tuple(float(v) for v in r.groups()))
        print(f"--- SVG {si}  viewBox {vw:.0f}x{vh:.0f}  矩形 {len(rects)} 个 ---")
        for t in re.finditer(r"<text ([^>]*)>([^<]*)</text>", svg):
            attrs, content = t.group(1), t.group(2)
            x = float(re.search(r'x="(-?\d+(?:\.\d+)?)"', attrs).group(1))
            y = float(re.search(r'y="(-?\d+(?:\.\d+)?)"', attrs).group(1))
            size = float(re.search(r'font-size="(\d+(?:\.\d+)?)"', attrs).group(1))
            anchor = re.search(r'text-anchor="(\w+)"', attrs)
            anchor = anchor.group(1) if anchor else "start"
            tw = text_w(content, size)
            x0 = x if anchor == "start" else (x - tw / 2 if anchor == "middle" else x - tw)
            x1 = x0 + tw
            if x0 < 0 or x1 > vw or y - size < 0 or y > vh:
                print(f"  [出血] y={y:.0f} 文字“{content}” 估算 x∈[{x0:.0f},{x1:.0f}]（画布宽 {vw:.0f}）")
                problems += 1
            for (rx, ry, rw, rh) in rects:
                if rx <= x <= rx + rw and ry <= y <= ry + rh:
                    if tw > rw - 8:
                        print(f"  [溢出框] y={y:.0f} 文字“{content}” 估算宽 {tw:.0f} "
                              f"> 框内可用 {rw - 8:.0f}（框 x={rx:.0f} w={rw:.0f}）")
                        problems += 1
    print("问题数:", problems)


if __name__ == "__main__":
    main()
