# -*- coding: utf-8 -*-
"""成稿共用的行内样式片段：条目式段落与图注。

条目段落自带 style，因此不会被 build_article.py 的 `<p>` 样式替换波及。
"""

LI = ('<p style="font-size:15px;color:#333333;line-height:1.8;margin:14px 0 6px;'
      'text-align:left;padding-left:1.25em;text-indent:-1.25em;">• ')


def bullet(name, body):
    """「• 名称：说明」条目，悬挂缩进使换行后的第二行与首行文字对齐"""
    return f'{LI}<b style="color:#1a3a5c;">{name}</b>：{body}</p>\n'


def cap(text):
    """图注：居中、12px、灰色"""
    return (f'<div style="font-size:12px;color:#888;text-align:center;line-height:1.6;'
            f'margin:2px 0 14px;">{text}</div>\n')
