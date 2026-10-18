# 微信公众号 HTML 排版硬规则（实测版）

微信编辑器会剥掉或改写一部分 HTML/CSS，所以**一切样式必须写在行内 `style` 上**。以下规则全部来自真实推送与回读验证。

## 1. 禁用项

| 禁用 | 原因 | 替代 |
|---|---|---|
| `<style>` 标签 | 被剥掉 | 行内 `style` |
| `class` | 被剥掉，样式不生效 | 行内 `style` |
| `<a>` 标签 | 被剥掉 | 带颜色的 `<span>` 展示 URL |
| `<ol>` 自动编号 | 空行会断号 | 带悬挂缩进的 `<p>` 手动编号 |
| `display:flex` / `position` / `@media` / `var()` | 支持不稳定 | 表格或简单块级布局 |

## 2. 每个文本段落必须显式声明对齐（最容易踩的坑）

微信对**未声明对齐**的段落按**两端对齐**渲染。段落里若有中英混排、又在空格处换行，多余空间就会被摊到词间距上，出现“两个词之间空格特别大”的现象——最明显的场景是参考文献行（含 `arXiv:2602.09000` 这类编号）和表注。

```html
<!-- 错：依赖默认对齐，中英混排会被拉开 -->
<p style="font-size:12.5px;color:#666;line-height:1.7;margin:0 0 4px;">2. iGRPO: Self-Feedback-Driven LLM Reasoning，arXiv:2602.09000</p>

<!-- 对：显式左对齐 -->
<p style="font-size:12.5px;color:#666;line-height:1.7;margin:0 0 4px;text-align:left;">…</p>
```

- 正文段落写 `text-align:left`
- 图注、封面说明写 `text-align:center`
- **`<h1>`–`<h6>` 也要写**，标题同样会被两端对齐
- 无文字的容器 `div` 可以省略，但它内部装文字的 `<p>` 必须有

`build_article.py` 会自动扫描并列出所有未声明 `text-align` 的 `p / h2 / div`，成稿前必须跑到零告警（无文字容器除外）。

## 3. 表格：颜色必须落在叶子元素上

微信会剥掉 `<tr>` 上的 `style`。凡是必须生效的背景色 / 字色，都要写在 `<th>` / `<td>` 上。

```html
<!-- 错：th 的白色字色丢失，白字落在白底上 -->
<tr style="background:#1a3a5c;color:#ffffff;"><th style="padding:9px 8px;">基准</th></tr>

<!-- 对：每个 th 自带背景与字色 -->
<tr>
  <th style="padding:9px 8px;background:#1a3a5c;color:#ffffff;text-align:left;">基准</th>
  <th style="padding:9px 8px;background:#1a3a5c;color:#ffffff;text-align:center;">变化</th>
</tr>
```

原则：任何要渲染出来的颜色，都写在叶子元素（`<th>` `<td>` `<span>`）上，不要靠父级继承。

## 4. 条目式段落：悬挂缩进

用 `padding-left` 配负 `text-indent`，让换行的第二行与首行文字对齐（而不是与项目符号对齐）。

```html
<p style="font-size:15px;color:#333333;line-height:1.8;margin:14px 0 6px;text-align:left;padding-left:1.25em;text-indent:-1.25em;">• <b style="color:#1a3a5c;">名称</b>：说明</p>
```

参考文献同理，用 `[1]` 或 `1.` 配同样的悬挂缩进。

## 5. 引号

全文用**弯引号** `“ ”`（U+201C / U+201D），不用直角引号 `「 」`。替换时必须分别处理左右引号，不能统一成一个字符。**SVG 图内文字同样适用**——图内也常被用来做强调，格式要和正文一致。

## 6. SVG 内联图

- 微信推送后**内联 SVG 会被保留**，可正常渲染；推送后可用 `draft/get` 回读，检查 `count("<svg")` 是否为预期张数
- 每张图给 `viewBox` 与 `style="width:100%;max-width:640px;display:block;margin:10px auto;…"`
- 图内**不要出现裸 `<p>` 标签**——build 脚本的样式替换会误伤它，本 skill 的 build 脚本对此有硬校验
- 图注放在图下方，用 `text-align:center` 的 `div`，字号 12px、颜色 `#888`

## 7. API 推送编码

```python
json_data = json.dumps(draft_data, ensure_ascii=False).encode("utf-8")
headers = {"Content-Type": "application/json; charset=utf-8"}
```

## 8. 回读校验的两个陷阱

1. **微信会剥掉 `<head>`**，所以要拿回读内容与本地成稿做纯文本比对时，必须**先删掉 `<head>…</head>`**，否则会多出 `<title>` 里的一段文字，误判为不一致。
2. **微信会规范化属性**，正文长度通常会变化几百字符（常见是变短）。因此**不要用 MD5 或长度判等**，用「去掉全部标签与空白后逐字比对」为准。

## 9. 推荐配色（技术类）

| 用途 | 色值 |
|---|---|
| 主标题 / 表头底 | `#1a3a5c` |
| 次级蓝（框线、箭头） | `#2a6f97` |
| 强调 / 焦点 | `#c0392b` |
| 浅底（引用块、图注条） | `#f4f7fa` |
| 焦点底色 | `#fff3cd` |
| 正文 | `#333333` |
| 次要文字 / 图注 | `#666666` / `#888888` |

## 10. 稿子迭代的正确姿势

改稿后**不要重新建草稿**，也不要手工去后台改。流程是：

```
改正文 → python build_article.py → python push_draft.py
```

`push_draft.py` 靠同目录的 `draft_id.txt` 判断是 `draft/add` 还是 `draft/update`，第二次起都是**原地替换同一篇草稿**，不会在草稿箱里堆出重复稿。
