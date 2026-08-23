# HANDOFF.md — AIPM·瞭望台 项目交接单

> 用途：开新对话时让 AI 先读这个文件，即可无缝接上「AIPM·瞭望台」项目。
> 新对话首句建议粘贴：
> 「继续 AIPM·瞭望台 项目。先读 ~/.workbuddy/skills/ai-pm-research-system/ 下的 HANDOFF.md、SKILL.md、产品需求文档.md，再告诉我当前进度并等我下一步指令。」

## 1. 项目是什么
- 中文名：**AIPM·瞭望台**（文件夹代号 ai-pm-research-system，不要改）。
- 一个「AI 竞品研究」产品：输入一个研究目标（某 AI 产品 / 竞品对比 / 市场扫描 / 机会探索），产出结构化、带证据来源的可视化研究报告（Markdown → 自包含 ECharts HTML）。
- 领域限定：仅 AI 相关；单次研究闭环（输入→解析→检索→分析→可视化报告）；**不建数据库 / RAG / LangGraph / 评测系统**。
- 仓库：`https://github.com/Averymeng/rival-in-AI` 下的 `ai-pm-research-system/` 目录（owner：Averymeng）。
- 兄弟项目保留：`ai-intel-bureau/`（AI情报局），互不混用。

## 2. 唯一可运行代码
- `scripts/build_report.py`：把约定写法的 Markdown 报告渲染成自包含 ECharts HTML。
- 约定写法见 SKILL.md 与 references/visualization.md；改渲染效果只动这个脚本，然后重新 `python3 scripts/build_report.py reports/xxx.md` 生成 HTML。

## 3. 工作流（零确认直跑，plan B）
- 解析研究目标 → 仅当「单对象模式」歧义（竞品分析 vs 深析单主体）时才弹 A/B 让用户选 → 直接跑 → 报告顶部「本次假设」明示口径。
- 检索用 LLM 联网搜索工具（不是爬虫）；Instagram / 微博登录墙连不上，属已知限制。
- 预置竞品清单 = 静态种子（references/preset-competitors.md），只影响建议、不影响检索。

## 4. 当前视觉状态（2026-08-23 定稿，commit 24dacd0）
- 配色：奶黄/橘黄系 —— 背景 `#FFF9F0`、主色 `#F59E0B`、浅黄 `#FCD34D`、边框 `#F3E6D0`、深色文本 `#2E2E38`。
- 对比维度只出现一遍：能力雷达图（radar）保留，**维度热力矩阵已删除**（避免重复）。
- 报告头部日期 = 实际完整日期（如 2026年8月23日），产品名 = AIPM·瞭望台。
- 执行摘要：上下排列的全宽长条，关键词小标题橘色、正文深色区分。
- 图表类型：radar（能力雷达）、scatter（市场/机会地图）、timeline（时间线）、KPI 卡、功能点阵、机会 icon 卡。

## 5. 已修过的渲染坑（别再踩）
- `<section>` 标签必须成对闭合，否则预览整页文字往下缩。
- 散点图判定需同时有 X/Y 列，否则被误判成热力矩阵。
- 热力矩阵索引注意 `[xi][yi]` 顺序。
- 雷达图只有「主体」填 areaStyle，竞品只描边，避免灰色叠黑。
- 来源链接用「标签文字」做超链接，不要整条 URL 当链接文本。

## 6. 长期约定（来自 MEMORY.md）
- 所有回复用**中文**；AI/技术术语按专业讲即可，用户听不懂会主动问。
- 用户自认 AI 小白：技术操作步骤给可复制命令 + 预期输出 + 易踩坑提示；**不要甩代码文件路径/行号**给用户（用大白话描述网页本身）。
- 用户一次给多需求 → 先建任务清单逐条打勾，每条独立改+验证再标记完成。
- 每完成一项任务 git 提交（必要时 push）；交接文档不再自动更新，除非用户要求。

## 7. 待办 / 未决（开新对话时确认是否要推进）
- 未来可能把这个本地 Python 渲染器升级成正式网站（当前设计语言/图表规范可复用，届时只丢胶水代码）。
- 后续可能按用户复审再微调配色 / 间距。
- 真实数据跑真实研究任务（目前是 demo 报告）。

## 8. 上次已渲染的报告
- `reports/Cursor_竞品分析.md`、`reports/可灵_竞品分析.md`、`reports/sample_report.md`；HTML 在 `reports/output/`。
