# Tech Deepdive WeChat Skill

把技术选题做成可直接推送的微信公众号深度文章。覆盖「定选题 → 事实核验 → 写正文 → 画图 → 组装自检 → 出封面 → 幂等推送 → 回读校验」全链路。

## 与其他公众号 skill 的区别

| | `lit-review-wechat` | 本 skill |
|---|---|---|
| 输入 | 研究主题 | 技术事件 / 公告 / 论文 / 已有素材 |
| 内容来源 | scansci-pdf MCP 检索 30–50 篇文献 | 给定信源 + 逐条一手核验 |
| 文章体 | 综述三段式 | 要点式技术拆解四层骨架 |
| 正文组织 | 单个手写 HTML | Python 分片 + build 脚本注入行内样式 |
| 排版约束 | 文档规定，靠人遵守 | **build 脚本自动校验** |
| 推送 | `draft/add`，每次新建草稿 | `draft_id.txt` + `draft/update`，**原地更新** |
| 推送后校验 | 打印长度 | **回读纯文本逐字比对** |
| 引用核查 | 有（`check_citations.py`） | 暂无 |

要写文献综述、需要检索文献 → `lit-review-wechat`；要拆解一个技术、反复改稿、要求幂等推送与逐字校验 → 本 skill。

## 用法

### 在 Trae 中

把 `tech-deepdive-wechat/` 放进 `~/.trae-cn/skills/` 或项目的 `.trae/skills/`，Trae 会自动识别。这样说即可触发：

> 写一篇公众号技术文章，讲 XXX，受众是工程师，写完推到我的草稿箱

### 单独运行脚本

所有脚本都支持命令行参数，可从本目录复制到文章目录后直接跑：

```bash
# 1. 组装成稿（注入行内样式 + 对齐自检）
python scripts/build_article.py --dir <文章目录> --out article.html --title "标题"

# 2. SVG 几何自检
python scripts/check_svg.py <文章目录>/article.html

# 3. 抽出 SVG 拼预览页，再截图目视复核
python scripts/render_svg_sheet.py <文章目录>/article.html

# 4. 生成封面（2.35:1，字号自适应）
python scripts/make_cover.py --bg bg.jpg --out <文章目录>/cover.jpg \
  --main "主标题" --sub "副标题" --tag "标签"

# 5. 推送（首次 add，之后原地 update）
python scripts/push_draft.py --dir <文章目录> --title "标题" --digest "摘要" \
  --appid <APPID> --secret <APPSECRET> --want-svg 6 --want-table 1

# 6. 只读回读校验
python scripts/verify_draft.py --dir <文章目录>
```

`APPID` / `APPSECRET` 也可用环境变量 `WECHAT_APPID` / `WECHAT_SECRET` 提供，避免写进命令行。

## 文章目录约定

```
<文章目录>/
├── style_blocks.py      # bullet() / cap()
├── flowchart.py         # 流程图渲染器
├── article_part1.py     # BODY1：导语 + 第一节
├── article_part2.py     # BODY2
├── article_part3.py     # BODY3 + 参考来源
├── article.html         # build 产物
├── cover.jpg            # 封面
└── draft_id.txt         # 推送后自动生成，用于幂等更新
```

`build_article.py` 依赖 `article_part1/2/3.py` 分别导出 `BODY1 / BODY2 / BODY3`，且目录下有 `style_blocks.py` 与 `flowchart.py`。

## 写作与排版规范

- `references/keypoints-style.md` —— 要点式技术拆解的四层骨架、句式约束、语气分层、自查清单
- `references/wechat-html-rules.md` —— 微信排版硬规则、实测坑、回读校验陷阱

## 实测踩过的坑

1. 段落漏写 `text-align:left`，微信按两端对齐渲染，中英混排（参考文献里的 arXiv 编号）会出现词距过大。build 脚本已自动检测。
2. 并列分支若用流程图渲染器的默认回折连接，会被画成先后顺序。并列必须传 `split_last=True`。
3. 改稿不要手工去后台改，也不要重新建草稿——重跑 `build → push` 即可原地更新。
4. 回读比对失败先查 `<head>`，多半是 `<title>` 被剥掉导致的误判，不是真不一致。

## License

MIT
