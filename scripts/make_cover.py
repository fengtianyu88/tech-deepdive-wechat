# -*- coding: utf-8 -*-
"""生成公众号封面图：底图裁成 2.35:1 → 压暗 + 全宽渐变遮罩 → 三行文字居中 → 存 JPEG。

字号按可用宽度自动收缩，保证主/副标题不出血；同时打印行距自检结果。

用法:
    python make_cover.py --bg bg.jpg --out cover.jpg \
        --main "拆解自反馈强化学习" \
        --sub "DeepSeek V4.1-Flash-1017 是怎么变强的" \
        --tag "技术拆解 · 写给一线工程师"

没有底图时，用任意一张纯色或渐变 JPEG 当 --bg 即可。
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def fit(draw, text, font_path, start, maxw):
    """按可用宽度自动缩字号"""
    size = start
    while size > 18:
        f = ImageFont.truetype(font_path, size)
        b = draw.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= maxw:
            return f
        size -= 2
    return ImageFont.truetype(font_path, 18)


def make(bg_path, out_path, main, sub, tag, font_bd, font_rg):
    bg = Image.open(bg_path).convert("RGB")
    w_src, h_src = bg.size
    target_h = int(w_src / 2.35)
    top = (h_src - target_h) // 2
    img = bg.crop((0, top, w_src, top + target_h))
    w, h = img.size

    img = Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.30).convert("RGBA")

    prof = np.zeros(h)
    up = (0.14 * h, 0.34 * h)
    dn = (0.84 * h, 0.99 * h)
    for y in range(h):
        if y < up[0]:
            prof[y] = 0
        elif y < up[1]:
            prof[y] = 212 * (y - up[0]) / (up[1] - up[0])
        elif y <= dn[0]:
            prof[y] = 212
        elif y < dn[1]:
            prof[y] = 212 * (1 - (y - dn[0]) / (dn[1] - dn[0]))
    sa = np.zeros((h, w, 4), dtype=np.uint8)
    sa[:, :, 0], sa[:, :, 1], sa[:, :, 2] = 6, 16, 34
    sa[:, :, 3] = prof[:, None].astype(np.uint8)
    img = Image.alpha_composite(img, Image.fromarray(sa))

    d = ImageDraw.Draw(img)
    maxw = w * 0.86
    f_main = fit(d, main, font_bd, 130, maxw)
    f_sub = fit(d, sub, font_bd, 56, maxw)
    f_tag = fit(d, tag, font_rg, 44, maxw * 0.9)

    y_main, y_sub, y_tag = int(0.28 * h), int(0.52 * h), int(0.74 * h)
    STROKE = (8, 18, 38)

    d.text((w / 2, y_main), main, font=f_main, fill=(255, 255, 255, 255),
           anchor="mm", stroke_width=5, stroke_fill=STROKE)
    d.text((w / 2, y_sub), sub, font=f_sub, fill=(140, 220, 255, 255),
           anchor="mm", stroke_width=4, stroke_fill=STROKE)

    tb = d.textbbox((0, 0), tag, font=f_tag)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    pad_x, pad_y = 46, 24
    px0, px1 = w / 2 - tw / 2 - pad_x, w / 2 + tw / 2 + pad_x
    py0, py1 = y_tag - th / 2 - pad_y, y_tag + th / 2 + pad_y
    d.rounded_rectangle([px0, py0, px1, py1], radius=(py1 - py0) / 2,
                        fill=(10, 22, 44, 255), outline=(140, 220, 255, 200), width=3)
    d.text((w / 2, y_tag - 2), tag, font=f_tag, fill=(225, 240, 250, 255),
           anchor="mm", stroke_width=2, stroke_fill=STROKE)

    img.convert("RGB").save(out_path, quality=92)
    print("saved:", out_path, Image.open(out_path).size)

    a = np.array(img.convert("RGB")).astype(int)
    rr, gg, bb = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    white = (rr > 225) & (gg > 225) & (bb > 225)
    cyan = (gg > 180) & (bb > 210) & (rr < 180)

    def ink_ranges(mask, min_px=25):
        rows, out, s = mask.sum(axis=1), [], None
        for y, c in enumerate(rows):
            if c >= min_px and s is None:
                s = y
            elif c < min_px and s is not None:
                out.append((s, y - 1))
                s = None
        if s is not None:
            out.append((s, len(rows) - 1))
        return out

    wr = [r for r in ink_ranges(white) if r[1] - r[0] > 40]
    cr = [r for r in ink_ranges(cyan) if r[1] - r[0] > 30]
    if wr and cr:
        print(f"主→副间距: {cr[0][0] - wr[0][1]}px（建议 ≥30）")


def main():
    ap = argparse.ArgumentParser(description="生成公众号封面")
    ap.add_argument("--bg", required=True, help="底图路径")
    ap.add_argument("--out", required=True, help="输出 JPEG 路径")
    ap.add_argument("--main", required=True, help="主标题")
    ap.add_argument("--sub", default="", help="副标题")
    ap.add_argument("--tag", default="", help="底部标签")
    ap.add_argument("--font-bd", default=r"C:\Windows\Fonts\msyhbd.ttc", help="粗体字体路径")
    ap.add_argument("--font-rg", default=r"C:\Windows\Fonts\msyh.ttc", help="常规字体路径")
    args = ap.parse_args()
    make(args.bg, args.out, args.main, args.sub, args.tag, args.font_bd, args.font_rg)


if __name__ == "__main__":
    main()
