# AIPM·瞭望台 · Agent 复刻手册（搭建网站 + 生成报告）

> 用途：给一个新 agent（或开发者）一份**可直接照做**的说明书，让它从零搭出本产品（网站 + 报告生成），并内附**全部提示词**。
> 关联：`PRD.md`（产品定义）、`内容架构.md`（报告内容设计）。
> 仓库：`https://github.com/Averymeng/rival-in-AI` → `ai-pm-research-system/`

---

## 0. 产品一句话

输入一个 AI 产品/赛道研究目标（自然语言）→ 系统实时联网检索 → 按固定 10 维框架撰写 → 渲染成**带证据来源的可视化报告网页**。本质是一条**固定顺序的流水线（workflow）**，不是多智能体。

---

## 1. 技术栈与架构

| 层 | 选型 | 职责 |
|---|---|---|
| 前端 | 原生 HTML/CSS/JS（单页） | 输入框、生成按钮、状态栏、报告展示、历史列表 |
| 后端 | Python + FastAPI + uvicorn | 接收目标、跑研究闭环、返回/托管报告 |
| LLM | DeepSeek（兼容 OpenAI 接口） | 意图解析 + 报告撰写 |
| 检索 | Tavily Search API | 实时联网检索公开信息 |
| 渲染 | 自研 `build_report.py` | 约定写法 Markdown → 自包含 ECharts HTML |
| 存储 | 本地文件系统（reports/ + reports/output/） | 报告 Markdown 与 HTML；无数据库 |

**架构链路**
```
用户输入(自然语言)
   → [后端] parse_intent()  意图解析 (DeepSeek, JSON)
   → [后端] retrieve()      实时检索 (Tavily)  → {query: [{title,url,content}]}
   → [后端] draft()         报告撰写 (DeepSeek) → 约定写法 Markdown
   → [渲染] build_report.render(md, html)  → 自包含 ECharts HTML
   → [前端] 打开 /reports/output/xxx.html  + 首页历史列表
```

> 关键纪律：**内容（Markdown 约定写法）与呈现（渲染器）解耦**。改视觉效果只动 `build_report.py`；改分析逻辑只动 `draft.py` 提示词。

---

## 2. 项目结构（照此创建）

```
ai-pm-research-system/
├─ docs/
│  ├─ PRD.md
│  ├─ 内容架构.md
│  └─ AGENT_HANDOFF.md        # 本文
├─ scripts/
│  └─ build_report.py         # 渲染器（Markdown → ECharts HTML），唯一可运行视觉代码
├─ references/                # 维度/证据/流程/可视化规范（供 agent 读取上下文）
│  ├─ dimensions.md
│  ├─ evidence-rules.md
│  ├─ flow.md
│  ├─ preset-competitors.md
│  └─ visualization.md
├─ reports/
│  ├─ *.md                    # 生成的报告源（约定写法）
│  └─ output/*.html           # 渲染产物
└─ web/
   ├─ backend/
   │  ├─ app.py               # FastAPI：/ 、/api/research(POST)、/report/{file}、/api/reports
   │  ├─ config.py            # BASE_DIR、读取 .env 的 API KEY
   │  ├─ llm_client.py        # DeepSeek 调用封装（OpenAI 兼容）
   │  ├─ parse_intent.py      # 意图解析（提示词见 §4.1）
   │  ├─ retrieve.py          # Tavily 检索封装（见 §4.2）
   │  ├─ draft.py             # 报告撰写（提示词见 §4.3）
   │  ├─ pipeline.py          # 串联上述四步（见 §3）
   │  ├─ requirements.txt
   │  └─ .env                 # DEEPSEEK_API_KEY= / TAVILY_API_KEY=
   └─ frontend/
      ├─ index.html
      ├─ app.js
      └─ style.css
```

---

## 3. 研究闭环（pipeline.py 逻辑）

```python
def run(goal):
    intent = parse_intent(goal)                 # 1. 解析
    retrieved = gather(goal, intent, objects)   # 2. 检索
    md = draft(goal, intent, objects, retrieved)# 3. 撰写
    save md -> reports/<slug>.md                # 4. 存档源
    render(md_path, html_path)                  # 5. 渲染
    return {name, file, title, intent, objects}
```

- `slug` = 目标清洗 + 时间戳，保证文件名唯一。
- 渲染失败要抛明确异常，前端据此提示。

---

## 4. 提示词（直接复制使用）

### 4.1 意图解析提示词（parse_intent.py）

```text
你是「AIPM·瞭望台」的意图解析器。用户会输入一个关于 AI 产品/赛道/公司的研究目标。
请把它解析成严格 JSON，字段如下：
- intent: 只能是以下之一：产品分析 / 竞品对比 / 市场扫描 / 产品选型 / 机会探索
    · 提到「对比/比/vs/和 X 和 Y」→ 竞品对比；提到「赛道/行业/市场有哪些」→ 市场扫描；
    · 提到「选型/怎么选/选哪个」→ 产品选型；提到「机会/空白/未满足」→ 机会探索；
    · 仅指名一个产品且无明显对比/赛道/选型/机会意图 → 产品分析。
- objects: 字符串数组，列出被点名的实体（产品/公司/赛道名）。竞品对比时填所有被比对象；
  单品分析时填 1 个；市场扫描填赛道名（可空，后续由检索补充）。
- mode: 竞品对比模式（用户点名多个对象正面比）/ 竞品分析模式（单主体+默认竞品）/ 单品模式（仅深析单个）。
- scope: 用户显式限定的维度关键词（如「长文本」「定价」），无则空字符串。
- depth: 快/标准/深，默认「标准」。
只输出 JSON，不要解释。
```

调用：`chat(messages, json_mode=True)` → `json.loads`。

### 4.2 检索策略（retrieve.py，无需 LLM）

用 Tavily `https://api.tavily.com/search`，POST `{api_key, query, max_results, search_depth:"advanced", include_answer:false}`。

**自动生成 queries（去重后 ≤8 条）**：
```python
for obj in objects:
    queries += [f"{obj} 产品 功能 官网",
                f"{obj} 定价 收费 价格",
                f"{obj} 用户 评价 体验"]
    if scope: queries.append(f"{obj} {scope}")
# 无对象（市场扫描/机会探索）时：queries = [goal, goal+" 主要玩家 排名"]
```
返回结构：`{query: [{"title","url","content"}]}`。检索失败不中断，单条标"检索失败"。

### 4.3 报告撰写提示词（draft.py）

```text
你是「AIPM·瞭望台」的研究分析师。基于下方检索材料，产出一份面向 AI 产品决策者的研究报告。
严格使用 Markdown，并遵守以下渲染约定（决定图表能否正确生成）：
1. 第一行是报告大标题（# 标题），含研究对象名。
2. 紧接着写「## 本次假设」，下面用「键：值」列出：分析对象、研究意图、选用维度、研究深度。
   （例如：分析对象：Cursor、Dify｜研究意图：竞品对比｜选用维度：全 10 维｜研究深度：标准）
3. 「## 执行摘要」：下面用 - 项目符号列出 4-6 条最关键结论（一句一结论）。
4. 后续章节固定顺序：市场概览、产品定位、功能矩阵、AI 能力、商业模式、增长、竞争格局、
   SWOT、[机会、]来源。（机会仅在意图为 机会探索/产品分析/产品选型 时出现）
5. 必须有一个「## 能力雷达」章节，紧接评分矩阵表格：第一列「维度」，后续列是每个对比对象；
   必须额外保留「行业平均」列作为基准。表头至少 维度/主体/行业平均 三列。单元格只填 1-5 数字。
6. 在「## 市场地图」章节放表格，表头必须含「X」「Y」「规模」（如 名称|X|Y|规模），
   每行一个对象，X/Y 为 0-10 数值，用于定位散点图。
7. 「## 时间线」章节：每条「- 年份或日期：事件」（如 - 2023：成立）。
8. 「## 用户口碑」章节：每条「- 正面：…」或「- 负面：…」。
9. 「## 来源」章节：表格 来源｜链接，每行一个引用（来源名 + 真实 URL）。不编造 URL；无来源写「未查证」。
10. SWOT 或文末可用「Must：…」「Should：…」「Could：…」列行动建议。
纪律：结论分 事实 / 洞察 / 建议；无法核实处明示「未查证」，严禁编造数据、份额、融资。
用中文。不要输出代码块、不要额外解释，直接输出报告正文。
```

调用：`chat(messages, temperature=0.4, timeout=180)`。

> 关键：上述"渲染约定"是内容与渲染的契约。渲染器 `build_report.py` 必须能识别这些标题与表格（见 §5）。

---

## 5. 渲染器契约（build_report.py）

输入：约定写法 Markdown；输出：自包含 HTML（加载 ECharts CDN，本地可直接打开）。

渲染映射（标题/表格 → 可视化）：

| 章节 / 约定 | 渲染为 |
|---|---|
| `## 执行摘要` 下 `-` 列表 | 核心判断卡 + 编号发现卡 |
| `## 市场概览` | 导语 + 竞争梯队金字塔 |
| `## 产品定位` | 产品档案卡 |
| `## 功能矩阵` 表格 | 能力覆盖矩阵 + 覆盖率 |
| `## AI 能力` + 评分矩阵表 | 能力模块卡（含矩阵时渲染雷达） |
| `## 商业模式` | 会员体系卡 + 变现结构对照 |
| `## 增长` | KPI 指标卡（抽取关键数字） |
| `## 竞争格局` | 中心-竞品辐射关系图（SVG） |
| `## SWOT` | 2×2 象限矩阵 |
| `## 能力雷达` + 评分矩阵表 | 雷达图 + 综合评分条形 |
| 含"地图"标题 + `X/Y/规模` 表 | 面积气泡定位图 |
| `## 时间线` 列表 | 编年轨 |
| `## 用户口碑` | 好评率条 + 引述卡 |
| `Must:/Should:/Could:` | 优先级看板 |
| `## 来源` 表格 | 编号参考文献卡片 |

实现要点（已在现版验证）：
- 分区作用域渲染：每个图表在其所属 section 内构建，避免错位移位。
- 表格分类：`is_scatter`（要求真实的 X/Y 维度列，避免产品名含 X/Y 误判）、`is_score_matrix`（首列为维度、单元格为 1–5 数字）。
- 评分口径 1–5，雷达须保留"行业平均"基准列。
- 单产品变体兼容：功能矩阵用 是/否/强/中；SWOT/增长为要点；行动建议内联。

调用：`python3 scripts/build_report.py reports/xxx.md --output reports/output/xxx.html`

---

## 6. 后端骨架（FastAPI，app.py 要点）

```python
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio, os
from pipeline import run

app = FastAPI()
REPORTS_OUT = "reports/output"

@app.get("/")                       # 返回前端 index.html
@app.post("/api/research")          # body: {goal} → 跑 run(goal) → 返回 {file,title,...}
@app.get("/api/reports")            # 列出 output/ 下 html
@app.get("/report/{filename}")      # FileResponse 返回对应 html
app.mount("/static", StaticFiles(directory="web/frontend"), name="static")
```

- 前端 `POST /api/research` 后轮询/等待返回 `file`，再 `window.open('/report/'+file)`。
- 状态栏文案："正在实时检索并生成报告（通常需要 30–90 秒）…"。

---

## 7. 前端骨架（index.html + app.js 要点）

- 一个输入框 + 「生成报告」按钮。
- 点击 → `fetch('/api/research',{method:'POST',body:JSON.stringify({goal})})` → 展示状态 → 拿到 `file` 后打开报告。
- 首页 `/` 展示历史报告列表（拉 `/api/reports`）。
- 纯静态，无框架；报告页是自包含 HTML，离线可开。

---

## 8. API Key 配置（.env）

```env
DEEPSEEK_API_KEY=sk-xxxx
TAVILY_API_KEY=tvly-xxxx
```
- DeepSeek 用 OpenAI 兼容端点（base_url + api_key）。
- Tavily 注册：https://tavily.com → 控制台拿 key。

---

## 9. 运行 / 部署

本地：
```bash
cd web/backend
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8787
```
部署（原项目规划）：CloudStudio 全栈一体托管，代码仓仍在 GitHub。本手册只保证"能本地跑通 + 能生成报告"。

---

## 10. 让 agent 复刻的最小指令（可整段喂给新 agent）

> "请基于 `ai-pm-research-system/` 的内容，从零搭一个 AI 竞品研究网站：
> 1) 用 FastAPI 做后端，提供 `POST /api/research`(接收自然语言目标) 与 `GET /report/{file}`；
> 2) 后端接 DeepSeek(意图解析+报告撰写) 与 Tavily(实时检索)，流水线见 `docs/AGENT_HANDOFF.md` §3，提示词见 §4；
> 3) 报告用固定 Markdown 约定写法（§4.3 + `内容架构.md` §6），由 `scripts/build_report.py` 渲染成 ECharts HTML；
> 4) 前端一个输入框 + 生成按钮 + 历史列表；
> 5) 全程遵守证据纪律：结论分事实/洞察/建议，来源可溯源，绝不编造数据。
> 先读 `docs/PRD.md`、`docs/内容架构.md`、`docs/AGENT_HANDOFF.md` 再开工。"

---

## 11. 边界与诚实表达（写进任何对外材料前必读）

- 状态写"原型 / 离线验证"，不写"上线系统"。
- 不写"服务了 N 位用户"（无真实用户记录）。
- 量化评测体系未建，相关能力标"待验证"。
- 每个技术词都能答"解决哪个节点、为何不用更简单方法、怎么失败"。
