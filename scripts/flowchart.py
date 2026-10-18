# -*- coding: utf-8 -*-
"""把「若干行 → 每行若干内容框」的流程规格，渲染成微信公众号可用的内联 SVG 流程图。

行内从左到右串箭头；行与行之间默认用「下探 - 左折 - 再下探」的虚线回折连接，
表示**先后关系**；末行若是与前一行并列的分支，必须传 `split_last=True`，
改用 T 型分叉，否则会把并列画成先后，语义就错了。

只输出 <rect>/<text>/<polygon>/<path>/<line>，不会与 build 脚本的 <p> 样式替换冲突。
"""

VB_W = 640
MARGIN = 20
BOX_H = 58
BOX_GAP = 20
ROW_GAP = 46
FIRST_Y = 76
SVG_STYLE = ("width:100%;max-width:640px;display:block;margin:10px auto;"
             "background:#ffffff;border:1px solid #e0e0e0;border-radius:8px;")


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def flow(title, rows, highlight=(), note=None, split_last=False):
    """rows: [[(主标题, 副标题), ...], ...]

    highlight: ((行, 列), ...) 高亮焦点框
    split_last: 末行与前一行是并列分支而非先后关系，改用 T 型分叉连接
    """
    n_rows = len(rows)
    last_top = FIRST_Y + (n_rows - 1) * (BOX_H + ROW_GAP)
    last_bottom = last_top + BOX_H
    height = last_bottom + (46 if note else 22)
    out = [f'<svg viewBox="0 0 {VB_W} {height}" style="{SVG_STYLE}" xmlns="http://www.w3.org/2000/svg">']
    out.append(f'<text x="{VB_W / 2:.0f}" y="32" text-anchor="middle" font-size="24" '
               f'font-weight="bold" fill="#1a3a5c">{_esc(title)}</text>')

    centers, tops = [], []
    for ri, row in enumerate(rows):
        top = FIRST_Y + ri * (BOX_H + ROW_GAP)
        tops.append(top)
        k = len(row)
        bw = (VB_W - 2 * MARGIN - (k - 1) * BOX_GAP) / k
        row_centers = []
        for bi, (main, sub) in enumerate(row):
            x = MARGIN + bi * (bw + BOX_GAP)
            cx = x + bw / 2
            row_centers.append(cx)
            hot = (ri, bi) in highlight
            fill, stroke = ("#fff3cd", "#c0392b") if hot else ("#eaf1f8", "#1a3a5c")
            out.append(f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{BOX_H}" rx="8" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="{"2.5" if hot else "1.5"}"/>')
            out.append(f'<text x="{cx:.1f}" y="{top + 26}" text-anchor="middle" font-size="16" '
                       f'font-weight="bold" fill="{"#a03020" if hot else "#1a3a5c"}">{_esc(main)}</text>')
            out.append(f'<text x="{cx:.1f}" y="{top + 46}" text-anchor="middle" font-size="13" '
                       f'fill="{"#8a5a1a" if hot else "#557a94"}">{_esc(sub)}</text>')
        for bi in range(k - 1):
            gx = MARGIN + bi * (bw + BOX_GAP) + bw + BOX_GAP / 2
            cy = top + BOX_H / 2
            out.append(f'<polygon points="{gx - 6:.1f},{cy - 6:.1f} {gx + 6:.1f},{cy:.1f} '
                       f'{gx - 6:.1f},{cy + 6:.1f}" fill="#2a6f97"/>')
        centers.append(row_centers)

    for ri in range(n_rows - 1):
        x_to, y_to = centers[ri + 1][0], tops[ri + 1]

        def _tip(cx, y_tip):
            return (f'<polygon points="{cx - 6:.1f},{y_tip - 12:.1f} {cx + 6:.1f},{y_tip - 12:.1f} '
                    f'{cx:.1f},{y_tip:.1f}" fill="#2a6f97"/>')

        if split_last and ri == n_rows - 2:
            x_src = centers[ri][-1]
            y_src = tops[ri] + BOX_H
            bend = y_to - ROW_GAP / 2
            xs = centers[ri + 1] + [x_src]
            out.append(f'<line x1="{min(xs):.1f}" y1="{bend:.1f}" x2="{max(xs):.1f}" y2="{bend:.1f}" '
                       f'stroke="#2a6f97" stroke-width="2" stroke-dasharray="6 4"/>')
            out.append(f'<line x1="{x_src:.1f}" y1="{y_src}" x2="{x_src:.1f}" y2="{bend:.1f}" '
                       f'stroke="#2a6f97" stroke-width="2" stroke-dasharray="6 4"/>')
            for cx in centers[ri + 1]:
                out.append(f'<line x1="{cx:.1f}" y1="{bend:.1f}" x2="{cx:.1f}" y2="{y_to - 10:.1f}" '
                           f'stroke="#2a6f97" stroke-width="2" stroke-dasharray="6 4"/>')
                out.append(_tip(cx, y_to))
        else:
            top = tops[ri]
            y_bend = top + BOX_H + ROW_GAP / 2
            x_from = centers[ri][-1]
            out.append(f'<path d="M{x_from:.1f},{top + BOX_H} L{x_from:.1f},{y_bend:.1f} '
                       f'L{x_to:.1f},{y_bend:.1f} L{x_to:.1f},{y_to - 10:.1f}" fill="none" '
                       f'stroke="#2a6f97" stroke-width="2" stroke-dasharray="6 4"/>')
            out.append(_tip(x_to, y_to))

    if note:
        out.append(f'<text x="{VB_W / 2:.0f}" y="{last_bottom + 30:.0f}" text-anchor="middle" '
                   f'font-size="13" fill="#666">{_esc(note)}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"
