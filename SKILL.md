---
name: "tech-deepdive-wechat"
description: "把技术选题做成可直接推送的微信公众号深度文章。内置「要点式技术拆解」写作体（分层标题 / 编号步骤 / 术语释义条目 / 收口句）、微信可用的行内样式排版规范、统一 SVG 流程图渲染器、几何与版式自检、幂等草稿推送（原地更新、不产生重复稿）与回读逐字校验。当用户要求写公众号技术文章、把技术原理讲给工程师、按要点式写法出稿，或把已成稿文章推送到微信公众号草稿箱时调用。"
---

# 技术深度文章 · 微信公众号出稿 Skill

把技术选题做成一篇能直接推送的公众号深度文，并把「写 → 画 → 组装 → 自检 → 推送 → 回读校验」整条链路固定下来，让每一次改稿都能一键重跑、且不产生重复草稿。

## 何时调用

- 用户要求写公众号技术文章、技术拆解、原理讲解，受众是工程师
- 用户要求按「要点式技术拆解」的写法出稿
- 用户要求把已写好的文章推送到微信公众号草稿箱
- 用户提到 公众号 / 微信推文 / 草稿箱 / 技术深度长文

## 与 `lit-review-wechat` 的分工

两个 skill 都出公众号文章、都推到草稿箱，但输入和重点不同，**不要混用**：

| | `lit-review-wechat` | 本 skill |
|---|---|---|
| 输入 | 一个研究主题 | 一个技术事件、公告、论文或已有素材 |
| 内容来源 | `scansci-pdf` MCP 检索 30–50 篇 SCI 文献 | 给定的信源（官方公告、报道、论文摘要）+ 逐条核验 |
| 文章体 | 综述三段式：基础 → 影响因素 → 应用 | 要点式技术拆解：是什么 → 机制 → 几条路径 → 证据 → 趋势 |
| 正文组织 | 单个手写 HTML 文件 | Python 分片（part1/2/3）+ build 脚本注入行内样式 |
| 排版约束落地 | 写在 `references/wechat-style-rules.md` 里靠人遵守 | 由 build 脚本**自动校验**（缺 `text-align` 直接报警） |
| 图形 | SVG 示意图 + 公式排版 | 统一渲染器画流程图/圈层图，另有几何自检 |
| 推送 | `draft/add`，**每次新建草稿** | `draft_id.txt` + `draft/update`，**原地更新同一篇** |
| 推送后校验 | 打印标题、作者、内容长度 | 回读**纯文本逐字比对**，不一致就报 |
| 引用核查 | 有 `check_citations.py`（正文 [N] 与文献表一致性） | 暂无（本 skill 的引用是列表式，无正文标记） |
| 封面 | GenerateImage 生成 | PIL 合成，固定 2.35:1，字号按宽度自动收缩 |

**选择原则**：要写文献综述、需要检索文献 → 用 `lit-review-wechat`；要拆解一个技术、迭代改稿、要求推送幂等与逐字校验 → 用本 skill。

两条可互补的能力值得互相移植：本 skill 缺「引用完整性检查」，`lit-review-wechat` 缺「幂等推送」和「行内样式自动校验」。

## 七阶段工作流

### 阶段 1 · 定选题与事实核验

1. 明确受众与篇长。面向工程师时，机制、边界、成本结构优先，不要写成新闻复述。
2. **凡是要写进文章的每个数字、每个名称，都必须回到一手来源核对**。官方公告 > 官方文档 > 权威报道 > 二手转述。
3. 引用论文前必须逐个核实是否存在：标题、arXiv 编号、来源链接都要拿到。名称写错会直接毁掉面向工程师文章的可信度。
4. 记录一份「事实清单」：数字 → 出处。写作时只从这份清单取数。

### 阶段 2 · 建目录骨架

在目标目录下建这套文件（以本篇为例，目录名随意）：

```
<article_dir>/
├── style_blocks.py       ← 公共样式片段（bullet / cap）
├── flowchart.py          ← 流程图渲染器
├── article_part1.py      ← 正文第一段（导语 + 第一节）
├── article_part2.py      ← 正文第二段
├── article_part3.py      ← 正文第三段 + 参考来源
├── build_article.py      ← 组装成稿 + 自检
├── make_cover.py         ← 生成封面
├── push_draft.py         ← 幂等推送 + 回读校验
├── verify_draft.py       ← 只读回读比对
├── check_svg.py          ← SVG 几何自检
└── render_svg_sheet.py   ← 抽出 SVG 做目视复核
```

**第一步是复制脚本，别跳过**：把本 skill `scripts/` 下的 `style_blocks.py` 与 `flowchart.py` 先复制到文章目录——`article_part1/2/3.py` 会 import 它们，缺了 build 会直接报 `ModuleNotFoundError`。其余脚本（`build_article` / `check_svg` / `render_svg_sheet` / `make_cover` / `push_draft` / `verify_draft`）也一并复制过去，全部支持命令行参数。

### 阶段 3 · 写正文

**先读** `references/keypoints-style.md`，按其中的四层骨架写。

正文分三片存到 `article_part1/2/3.py`，每片是一个 Python 字符串。**只写裸标签**（`<p>`、`<h2>`、`<section>`），行内样式交给 build 脚本统一注入；但条目式段落要用 `style_blocks.bullet()` 生成，它的样式自带悬挂缩进，不会被 build 的替换波及。

### 阶段 4 · 画图

- 流程图用 `flowchart.flow()`，按「若干行 → 每行若干内容框」的规格声明，不要手写坐标。
- **并列分支必须用 `split_last=True` 出 T 型分叉**；用默认的蛇形回折会把并列关系画成先后顺序，读起来完全变味。
- 圈层/同心圆这类图仍需手写 SVG，写完必须跑 `check_svg.py` 几何自检 + 出图目视确认。
- 图内文字与正文一样用弯引号 `“ ”`。

### 阶段 5 · 组装与自检

```bash
python build_article.py --dir <article_dir>
python check_svg.py <article_dir>/<out>.html
python render_svg_sheet.py <article_dir>/<out>.html      # 出预览页，再截图目视
```

`build_article.py` 会打印中文字符数、SVG 数、表格数，并做两项自检：

1. SVG 内部出现裸 `<p>` 会直接报错退出（避免样式替换破坏图形）
2. 扫全文未声明 `text-align` 的 `p/h2/div` 并报警——**这是最容易踩的排版坑**

### 阶段 6 · 封面

```bash
python make_cover.py --bg <底图.jpg> --out <article_dir>/cover.jpg \
  --main "主标题" --sub "副标题" --tag "标签"
```

封面按 2.35:1 裁切，字号按可用宽度自动收缩，不会出血。没有底图时用纯色底也行。

### 阶段 7 · 推送与回读校验

```bash
python push_draft.py --dir <article_dir> --title "标题" --digest "摘要" \
  --appid <APPID> --secret <APPSECRET>
python verify_draft.py --dir <article_dir>
```

推送逻辑是**幂等**的：

- 首次运行走 `draft/add`，把 `media_id` 写进 `draft_id.txt`
- 之后再跑走 `draft/update`，**原地替换同一篇草稿**，不会堆积重复稿
- 加 `--new` 可强制新建一篇

回读校验会做纯文本逐字比对。注意：微信端会剥掉 `<head>`，比对前必须先去掉 head，否则会误判不一致；中文字符数阈值也要按实际篇长调整（精简版用 >1200，长版用 >2500）。

## 硬规则速查

| 项目 | 规则 |
|---|---|
| 样式 | 一律行内 `style`，禁用 `<style>` / class / flex / position / `@media` |
| 对齐 | **每个文本段落显式写 `text-align:left`**，居中段落写 `center`；成稿前由 build 脚本自动扫 |
| 标题 | 用 `<p>` 或 `<h2>` 加行内样式，不依赖默认字号；大标题要直白，禁设问式与比喻式 |
| 链接 | 微信剥 `<a>`，用带颜色的 `<span>` 展示 URL |
| 表格 | 每个 `<th>` 自带 `background` 和 `color`，微信会剥 `<tr>` 的样式 |
| 列表 | 用带悬挂缩进的 `<p>`（`padding-left` + `text-indent` 负值），不用 `<ol>`（空行会断号） |
| 引号 | 全文弯引号 `“ ”`（U+201C / U+201D），含图内文字 |
| 图 | 内联 SVG 可在微信渲染；导出后仍需逐张目视确认 |
| 编码 | API 推送用 `ensure_ascii=False` + UTF-8 |

## 已知坑（都是实测踩过的）

1. **微信默认两端对齐**。段落漏写 `text-align:left` 时，中英混排的短行（参考文献、含 arXiv 编号的行）会被拉开词距。build 脚本已自动检测。
2. **成稿前的自查顺序**：先跑到字数/SVG/表格统计，再跑几何自检，最后出图目视。视觉问题几何自检抓不到（比如把并列画成先后），必须看图。
3. **改稿后不要重新建草稿**。改了正文就重跑 `build → push`，靠 `draft_id.txt` 原地更新。
4. **回读比对失败先查 `<head>`**，八成是标题被剥掉导致的，不是真不一致。
5. **纯文本一致不等于渲染一致**。属性规范化会让长度变化几百字符，属正常。
6. **两个已知缺口（待补，不要当已完成）**：
   - 没有引用完整性检查。`lit-review-wechat` 的 `check_citations.py` 可补，但它依赖正文里的 `[N]` 标记，而本 skill 的参考文献是列表式、正文不标序号，机制不同，需要另写
   - 几何自检只覆盖「文字溢出所属框」与「出血」，**不覆盖元素之间的重叠**。`lit-review-wechat` 的 `detect_svg_overlaps.py` 可并入

## 目录结构

```
tech-deepdive-wechat/
├── SKILL.md
├── README.md
├── references/
│   ├── keypoints-style.md      # 「要点式技术拆解」写作体：四层骨架与细则
│   └── wechat-html-rules.md    # 微信排版硬规则与实测坑
└── scripts/
    ├── style_blocks.py         # bullet() / cap() 公共样式片段
    ├── flowchart.py            # 统一 SVG 流程图渲染器（含 T 型分叉）
    ├── build_article.py        # 组装成稿 + 对齐与标签自检
    ├── check_svg.py            # SVG 几何自检（文字溢出所属框 / 出血）
    ├── render_svg_sheet.py     # 抽出 SVG 拼预览页，供截图目视
    ├── make_cover.py           # 封面生成（2.35:1，字号自适应）
    ├── push_draft.py           # 幂等推送（add / update）+ 回读校验
    └── verify_draft.py         # 只读回读比对
```

## 参考实现

本 skill 的全部脚本与流程来自一个真实项目：一篇拆解 DeepSeek V4.1-Flash-1017 自反馈强化学习的公众号文章（6 张自绘 SVG、1 张表、约 2600 中文字符）。该项目目录可作为端到端样例对照。
