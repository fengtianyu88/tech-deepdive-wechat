# -*- coding: utf-8 -*-
"""把成稿里的 SVG 抽出来拼成预览页，供无头浏览器截图做目视复核。

几何自检（check_svg.py）抓不到的视觉问题——箭头穿过文字、并列关系被画成先后、
配色对比不足——只能靠看图发现，这一步不能省。

用法:
    python render_svg_sheet.py <成稿.html> [--out _svg_sheet.html]

接着截图（路径按本机调整）:
    & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --headless=new --disable-gpu `
      --hide-scrollbars --force-device-scale-factor=1.6 --window-size=1064,3000 `
      --screenshot="./_svg_sheet.png" "file:///<绝对路径>/_svg_sheet.html"
"""
import argparse
import os
import re


def main():
    ap = argparse.ArgumentParser(description="抽出 SVG 拼预览页")
    ap.add_argument("html", help="成稿 HTML 路径")
    ap.add_argument("--out", default="_svg_sheet.html", help="预览页输出路径")
    args = ap.parse_args()

    with open(args.html, encoding="utf-8") as f:
        html = f.read()
    svgs = re.findall(r"<svg[\s\S]*?</svg>", html)

    parts = ['<!DOCTYPE html><html><head><meta charset="utf-8"></head>',
             '<body style="margin:0;padding:12px;background:#ffffff;width:664px;">']
    for i, s in enumerate(svgs, 1):
        parts.append(f'<p style="font:14px sans-serif;color:#333;margin:8px 0 4px;">图 {i}</p>')
        parts.append(s)
    parts.append("</body></html>")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("".join(parts))

    print(f"图数量: {len(svgs)} | 预览页: {os.path.abspath(args.out)}")
    print("下一步：用 Chrome headless --screenshot 截图后目视检查每张图")


if __name__ == "__main__":
    main()
