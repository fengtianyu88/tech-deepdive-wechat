# -*- coding: utf-8 -*-
"""组装公众号成稿：把裸标签补成微信可用的行内样式，并做排版自检。

用法:
    python build_article.py --dir <文章目录> [--out article.html] [--title "标题"]

约定：<文章目录> 下需有 article_part1.py / article_part2.py / article_part3.py，
分别导出 BODY1 / BODY2 / BODY3；同目录还需有 style_blocks.py 与 flowchart.py。

自检两项：
1. SVG 内部若出现裸 <p>，样式替换会破坏图形 → 直接报错退出
2. 扫描未声明 text-align 的 p / h2 / div → 报警（微信默认两端对齐，会造成词距不均）
"""
import argparse
import os
import re
import sys

P_STYLE = '<p style="font-size:15px;color:#333333;line-height:1.8;margin:10px 0;text-align:left;">'
H2_STYLE = ('<h2 style="font-size:19px;color:#1a3a5c;margin:28px 0 12px;padding:8px 0 8px 10px;'
            'border-left:4px solid #2a6f97;background:#f4f7fa;font-weight:bold;text-align:left;">')


def build(article_dir, out_name, title):
    d = os.path.abspath(article_dir)
    if d not in sys.path:
        sys.path.insert(0, d)
    from article_part1 import BODY1
    from article_part2 import BODY2
    from article_part3 import BODY3

    body = BODY1 + BODY2 + BODY3

    for m in re.finditer(r"<svg[\s\S]*?</svg>", body):
        if "<p>" in m.group(0):
            raise SystemExit("ERROR: SVG 内部出现裸 <p> 标签，样式替换会破坏图形")

    body = body.replace("<section>", '<section style="margin:16px 0;">')
    body = body.replace("<p>", P_STYLE)
    body = body.replace("<h2>", H2_STYLE)

    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title}</title></head>"
        '<body style="margin:0;padding:16px 14px;background:#ffffff;'
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;"
        'max-width:677px;margin:0 auto;">'
        + body
        + "</body></html>"
    )

    out_path = os.path.join(d, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
    print(f"输出: {out_path}")
    print(f"中文字符: {cjk} | SVG: {body.count('<svg')} | <img>: {body.count('<img')} | "
          f"表格: {body.count('<table')} | 总长度: {len(html)}")
    if title:
        print(f"标题: {title} | 长度: {len(title)} 字")

    for tag in ("<p>", "<h2>", "<section>"):
        n = body.count(tag)
        if n:
            print(f"警告：仍有 {n} 个裸 {tag}")

    no_align = []
    for tag in ("p", "h2", "div"):
        for m in re.finditer(rf'<{tag} style="([^"]*)"', body):
            if "text-align" not in m.group(1):
                no_align.append(f"<{tag}> {m.group(1)[:46]}")
    if no_align:
        print(f"警告：{len(no_align)} 处未声明 text-align（无文字的容器 div 可忽略，文本段落必须补）")
        for item in no_align:
            print("   ", item)
    else:
        print("对齐自检: 全部段落均已声明 text-align")
    return out_path


def main():
    ap = argparse.ArgumentParser(description="组装公众号成稿并自检")
    ap.add_argument("--dir", required=True, help="文章目录")
    ap.add_argument("--out", default="article.html", help="输出文件名")
    ap.add_argument("--title", default="", help="文章标题（写入 <title>）")
    args = ap.parse_args()
    build(args.dir, args.out, args.title)


if __name__ == "__main__":
    main()
