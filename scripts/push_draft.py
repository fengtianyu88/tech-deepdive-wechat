# -*- coding: utf-8 -*-
"""推送 / 更新文章到微信公众号草稿箱，并回读逐字校验。

用法:
    python push_draft.py --dir <文章目录> --title "标题" --digest "摘要" \
        --appid <APPID> --secret <APPSECRET> \
        [--author 算法] [--html article.html] [--cover cover.jpg] \
        [--want-svg 6] [--want-table 1] [--min-cjk 1200] [--new]

APPID / APPSECRET 也可由环境变量 WECHAT_APPID / WECHAT_SECRET 提供。

幂等推送：
    首次运行走 draft/add，把 media_id 写入 <dir>/draft_id.txt；
    之后重跑自动走 draft/update，**原地替换同一篇草稿**，不会在草稿箱堆重复稿；
    --new 强制新建一篇。

回读校验的两个要点：
    1. 微信会剥掉 <head>，比对前必须先删掉，否则会多出 <title> 的文字
    2. 微信会规范化属性，长度会变，所以不要用 MD5 / 长度判等，用纯文本逐字比对
"""
import argparse
import json
import os
import re
import sys

import requests

TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
DRAFT_GET_URL = "https://api.weixin.qq.com/cgi-bin/draft/get"
DRAFT_UPDATE_URL = "https://api.weixin.qq.com/cgi-bin/draft/update"
HEADERS = {"Content-Type": "application/json; charset=utf-8"}


def plain_text(html):
    """去掉 head、全部标签与空白，用于跨端纯文本比对"""
    t = re.sub(r"<head[\s\S]*?</head>", "", html, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", "", t)


def get_token(appid, secret):
    data = json.loads(requests.get(
        TOKEN_URL, params={"grant_type": "client_credential", "appid": appid, "secret": secret},
        timeout=30).content.decode("utf-8"))
    if "access_token" not in data:
        raise SystemExit(f"取 token 失败: {data}")
    print("token OK:", data["access_token"][:8] + "...")
    return data["access_token"]


def upload_cover(token, cover_path):
    with open(cover_path, "rb") as cf:
        data = json.loads(requests.post(
            MATERIAL_URL, params={"access_token": token, "type": "image"},
            files={"media": (os.path.basename(cover_path), cf, "image/jpeg")},
            timeout=60).content.decode("utf-8"))
    if "media_id" not in data:
        raise SystemExit(f"上传封面失败: {data}")
    print("封面 media_id:", data["media_id"])
    return data["media_id"]


def main():
    ap = argparse.ArgumentParser(description="推送/更新文章到微信公众号草稿箱")
    ap.add_argument("--dir", required=True, help="文章目录")
    ap.add_argument("--title", required=True)
    ap.add_argument("--digest", required=True)
    ap.add_argument("--author", default="")
    ap.add_argument("--html", default="article.html")
    ap.add_argument("--cover", default="cover.jpg")
    ap.add_argument("--appid", default=os.environ.get("WECHAT_APPID", ""))
    ap.add_argument("--secret", default=os.environ.get("WECHAT_SECRET", ""))
    ap.add_argument("--want-svg", type=int, default=0, help="期望的 SVG 张数，0 表示不校验")
    ap.add_argument("--want-table", type=int, default=0, help="期望的表格数，0 表示不校验")
    ap.add_argument("--min-cjk", type=int, default=1200, help="中文字符数下限")
    ap.add_argument("--new", action="store_true", help="强制新建草稿，不用 draft_id.txt 更新")
    args = ap.parse_args()

    if not args.appid or not args.secret:
        raise SystemExit("缺少 AppID / AppSecret（用 --appid/--secret 或环境变量 WECHAT_APPID/WECHAT_SECRET）")

    d = os.path.abspath(args.dir)
    html_path = os.path.join(d, args.html)
    cover_path = os.path.join(d, args.cover)
    id_path = os.path.join(d, "draft_id.txt")

    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    token = get_token(args.appid, args.secret)
    thumb_media_id = upload_cover(token, cover_path)

    article = {
        "title": args.title,
        "author": args.author,
        "digest": args.digest,
        "content": html,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }

    draft_id = None
    if os.path.exists(id_path) and not args.new:
        draft_id = open(id_path, encoding="utf-8").read().strip() or None

    if draft_id:
        body = json.dumps({"media_id": draft_id, "index": 0, "articles": article},
                          ensure_ascii=False).encode("utf-8")
        res = json.loads(requests.post(DRAFT_UPDATE_URL + "?access_token=" + token,
                                       data=body, headers=HEADERS, timeout=120).content.decode("utf-8"))
        print("draft/update:", res)
        if res.get("errcode") != 0:
            print("更新失败，改为新建草稿")
            draft_id = None

    if not draft_id:
        body = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
        res = json.loads(requests.post(DRAFT_ADD_URL + "?access_token=" + token,
                                       data=body, headers=HEADERS, timeout=120).content.decode("utf-8"))
        if "media_id" not in res:
            raise SystemExit(f"draft/add 失败: {res}")
        draft_id = res["media_id"]
        with open(id_path, "w", encoding="utf-8") as f:
            f.write(draft_id)
        print("draft/add:", res)

    print("草稿 media_id:", draft_id)

    item = json.loads(requests.post(
        DRAFT_GET_URL + "?access_token=" + token,
        data=json.dumps({"media_id": draft_id}).encode("utf-8"),
        headers=HEADERS, timeout=60).content.decode("utf-8"))["news_item"][0]
    back = item["content"]

    cjk = len(re.findall(r"[\u4e00-\u9fff]", back))
    svg_cnt = len(re.findall(r"<svg", back))
    tbl_cnt = len(re.findall(r"<table", back))

    print("=== 回读验证 ===")
    print("标题:", item["title"], "| 作者:", item.get("author", ""))
    checks = [
        ("标题一致", item["title"] == args.title),
        (f"中文字符>{args.min_cjk}", cjk > args.min_cjk),
        ("封面已设置", bool(item.get("thumb_media_id"))),
        ("纯文本与本地逐字一致", plain_text(back) == plain_text(html)),
    ]
    if args.want_svg:
        checks.append((f"SVG 数量={args.want_svg}", svg_cnt == args.want_svg))
    if args.want_table:
        checks.append((f"表格数量={args.want_table}", tbl_cnt == args.want_table))

    failed = 0
    for name, ok in checks:
        print(("PASS" if ok else "FAIL"), name)
        failed += 0 if ok else 1
    print(f"中文字符: {cjk} | SVG: {svg_cnt} | 表格: {tbl_cnt} | 正文长度: {len(back)}")
    print("（微信端会规范化属性，长度会变，以纯文本比对为准）")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
