# -*- coding: utf-8 -*-
"""只读校验：把线上草稿与本地成稿做纯文本逐字比对，不推送。

用法:
    python verify_draft.py --dir <文章目录> [--html article.html] \
        [--appid <APPID>] [--secret <APPSECRET>]

草稿 media_id 从 <文章目录>/draft_id.txt 读取。
比对前会去掉 <head>，因为微信端会剥掉它，否则会多出 <title> 的文字而误判。
"""
import argparse
import difflib
import json
import os
import re

import requests

from push_draft import DRAFT_GET_URL, HEADERS, get_token, plain_text


def main():
    ap = argparse.ArgumentParser(description="回读校验线上草稿")
    ap.add_argument("--dir", required=True)
    ap.add_argument("--html", default="article.html")
    ap.add_argument("--appid", default=os.environ.get("WECHAT_APPID", ""))
    ap.add_argument("--secret", default=os.environ.get("WECHAT_SECRET", ""))
    args = ap.parse_args()

    d = os.path.abspath(args.dir)
    media_id = open(os.path.join(d, "draft_id.txt"), encoding="utf-8").read().strip()
    token = get_token(args.appid, args.secret)

    item = json.loads(requests.post(
        DRAFT_GET_URL + "?access_token=" + token,
        data=json.dumps({"media_id": media_id}).encode("utf-8"),
        headers=HEADERS, timeout=60).content.decode("utf-8"))["news_item"][0]
    back = item["content"]

    with open(os.path.join(d, args.html), encoding="utf-8") as f:
        local = f.read()

    lb, la = plain_text(back), plain_text(local)
    print("微信端纯文本长度:", len(lb), "| 本地:", len(la))
    print("逐字一致:", lb == la)
    if lb != la:
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, la, lb, autojunk=False).get_opcodes():
            if op != "equal":
                print(f"[{op}] 本地={la[i1:i2][:80]!r} -> 微信={lb[j1:j2][:80]!r}")

    print("标题:", item["title"])
    print("中文字符:", len(re.findall(r"[\u4e00-\u9fff]", back)),
          "| SVG:", len(re.findall(r"<svg", back)),
          "| 表格:", len(re.findall(r"<table", back)),
          "| 封面:", (item.get("thumb_media_id") or "(空)")[:16] + "...")


if __name__ == "__main__":
    main()
