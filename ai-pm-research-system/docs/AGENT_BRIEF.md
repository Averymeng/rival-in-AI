# AIPM·瞭望台 · 自包含复刻 Brief（无需读取仓库）

> 本文件是单文件版交接说明书，**不依赖任何外部仓库或链接**。Agent 只需读取本文件即可从零搭出本产品（含自行实现的渲染器）。
> **本 Brief 只定义产品「内容与数据结构」，不规定任何 UI 视觉设计**——配色、版式、组件样式由实现者自行决定，请勿照搬任何既有实现。
> 目标产物：一个 AI 竞品研究网站——用户输入自然语言研究目标 → 实时联网检索 → 按固定框架撰写 → 渲染成带证据来源的可视化报告网页。

---

## 1. 产品定义（一句话）

输入一个 AI 产品/赛道研究目标（自然语言）→ 系统实时联网检索公开信息 → 按固定 10 维框架撰写 → 渲染成**带证据来源的可视化报告网页**。本质是一条**固定顺序的流水线（workflow）**，不是多智能体。

领域限定：仅 AI 相关（大模型 / 对话 / 绘画视频 / 办公效率 / 营销 / 编程 / 搜索 / 公司·基建等）。

目标用户：AI 产品经理（0–5 年）、AI 创业者、行业研究员、关注 AI 赛道的投资人。

---

## 2. 技术栈与架构

| 层 | 选型 | 职责 |
|---|---|---|
| 前端 | 原生 HTML/CSS/JS（单页） | 输入框、生成按钮、状态栏、报告展示、历史列表 |
| 后端 | Python + FastAPI + uvicorn | 接收目标、跑研究闭环、返回/托管报告 |
| LLM | DeepSeek（OpenAI 兼容接口） | 意图解析 + 报告撰写 |
| 检索 | Tavily Search API | 实时联网检索公开信息 |
| 渲染 | 自行实现（读取约定写法 Markdown → 自包含 ECharts HTML） | 你实现的渲染器，视觉风格自己定 |
| 存储 | 本地文件系统（reports/ + reports/output/） | 报告 Markdown 与 HTML；无数据库 |

**架构链路**
```
用户输入(自然语言)
   → [后端] 意图解析 (DeepSeek, 返回 JSON)
   → [后端] 实时检索 (Tavily)        → {query: [{title,url,content}]}
   → [后端] 报告撰写 (DeepSeek)      → 约定写法 Markdown
   → [渲染] render(md)              → 自包含 ECharts HTML
   → [前端] 打开 /report/{file}      + 首页历史列表
```

> 关键纪律：**内容（Markdown 约定写法）与呈现（渲染器）解耦**。视觉风格完全由你设计；改分析逻辑只动报告撰写提示词。

---

## 3. 项目结构（照此创建）

```
ai-pm-research-system/
├─ scripts/render.py              # 你实现的渲染器（约定写法 Markdown → HTML）
├─ reports/
│  ├─ *.md                        # 生成的报告源（约定写法）
│  └─ output/*.html               # 渲染产物
└─ web/
   ├─ backend/
   │  ├─ app.py                   # FastAPI 接口
   │  ├─ config.py                # 读 .env 的 API KEY + BASE_DIR
   │  ├─ llm_client.py            # DeepSeek 调用封装（OpenAI 兼容）
   │  ├─ parse_intent.py          # 意图解析（提示词见 §5.1）
   │  ├─ retrieve.py              # Tavily 检索（见 §5.2）
   │  ├─ draft.py                 # 报告撰写（提示词见 §5.3）
   │  ├─ pipeline.py              # 串联四步（见 §4）
   │  ├─ requirements.txt         # fastapi, uvicorn, requests, openai
   │  └─ .env                     # DEEPSEEK_API_KEY= / TAVILY_API_KEY=
   └─ frontend/
      ├─ index.html / app.js / style.css
```

---

## 4. 研究闭环（pipeline.py 逻辑）

```python
def run(goal):
    intent = parse_intent(goal)                 # 1. 解析
    retrieved = gather(goal, intent, objects)   # 2. 检索
    md = draft(goal, intent, objects, retrieved)# 3. 撰写
    save md -> reports/<slug>.md                # 4. 存档源
    render(md_path, html_path)                  # 5. 渲染（调用你实现的渲染器）
    return {name, file, title, intent, objects}
```
- `slug` = 目标清洗 + 时间戳，保证文件名唯一。
- 渲染失败要抛明确异常，前端据此提示。

---

## 5. 提示词（直接复制使用，勿改动语义）

### 5.1 意图解析提示词（parse_intent.py）

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

### 5.2 检索策略（retrieve.py，无需 LLM）

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

### 5.3 报告撰写提示词（draft.py）

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

---

## 6. 内容→图表契约（仅定义内容结构与所需图表类型，**不规定视觉风格**）

输入：约定写法 Markdown；输出：自包含 HTML（加载 ECharts CDN，本地可直接打开）。**渲染器由你自行实现**（`scripts/render.py`）。

> **重要（视觉设计自由）**：本 Brief 只约定「报告必须包含哪些内容、每张图表需要什么数据」，**不规定任何 UI 视觉规范**（配色、版式、组件样式、卡片形态均由你自行设计）。请勿参考或照搬任何既有实现的视觉风格——你做出的界面应与参考实现完全不同。

各章节的内容要求与推荐图表类型（图表的视觉样式由你定）：

| 章节 / 约定 | 必须包含的内容 | 推荐图表 / 区块（样式自定） |
|---|---|---|
| `## 执行摘要` 下 `-` 列表 | 4–6 条最关键结论（一句一结论） | 摘要区块 |
| `## 市场概览` | 赛道规模、竞争梯队、趋势 | 梯队/分层可视化（形式自定） |
| `## 产品定位` | 各对象的定位 / 调性 / 场景对照 | 对照卡片或表格 |
| `## 功能矩阵` 表格 | 功能覆盖度对照 | 覆盖矩阵 |
| `## AI 能力` + 评分矩阵表 | 模型 / 质量 / 速度等能力评分 | 能力模块 + 雷达图 |
| `## 商业模式` | 收费结构 / 价格带 | 定价 / 变现对照 |
| `## 增长` | 获客 / 社区 / 口碑关键数字 | 指标卡 |
| `## 竞争格局` | 谁与谁竞争、强弱关系 | 关系图（形式自定） |
| `## SWOT` | 优势 / 劣势 / 机会 / 威胁 | 2×2 矩阵 |
| `## 能力雷达` + 评分矩阵表 | 多维 1–5 评分（须含「行业平均」基准列） | 雷达图 + 评分条 |
| 含"地图"标题 + `X/Y/规模` 表 | 定位坐标（0–10） | 散点 / 气泡图 |
| `## 时间线` 列表 | 年份 / 日期–事件 | 时间轴 |
| `## 用户口碑` | 正向 / 负向引用 | 口碑区块 |
| `Must:/Should:/Could:` | 行动建议分级 | 优先级看板 |
| `## 来源` 表格 | 来源名 + 真实 URL | 参考文献列表 |

实现要点（与视觉无关，必须遵守以保证图表数据正确）：
- 分区作用域渲染：每个图表在其所属 section 内构建，避免错位移位。
- 表格分类：散点表要求真实的 X/Y 维度列（避免产品名含 X/Y 误判）；评分矩阵首列为维度、单元格为 1–5 数字。
- 评分口径 1–5，雷达须保留「行业平均」基准列。
- 单产品变体兼容：功能矩阵用 是/否/强/中；SWOT/增长为要点；行动建议内联。

调用：`python3 scripts/render.py reports/xxx.md --output reports/output/xxx.html`

---

## 7. 后端骨架（FastAPI，app.py 要点）

```python
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pipeline import run

app = FastAPI()
REPORTS_OUT = "reports/output"

@app.get("/")                       # 返回前端 index.html
@app.post("/api/research")          # body: {goal} → 跑 run(goal) → 返回 {file,title,...}
@app.get("/api/reports")            # 列出 output/ 下 html
@app.get("/report/{filename}")      # FileResponse 返回对应 html
app.mount("/static", StaticFiles(directory="web/frontend"), name="static")
```
- 前端 `POST /api/research` 后拿到 `file`，再 `window.open('/report/'+file)`。
- 状态栏文案："正在实时检索并生成报告（通常需要 30–90 秒）…"。

---

## 8. 前端骨架（index.html + app.js 要点）

- 一个输入框 + 「生成报告」按钮。
- 点击 → `fetch('/api/research',{method:'POST',body:JSON.stringify({goal})})` → 展示状态 → 拿到 `file` 后打开报告。
- 首页 `/` 展示历史报告列表（拉 `/api/reports`）。
- 纯静态，无框架；报告页是自包含 HTML，离线可开。

---

## 9. API Key 配置（.env）

```env
DEEPSEEK_API_KEY=sk-xxxx
TAVILY_API_KEY=tvly-xxxx
```
- DeepSeek 用 OpenAI 兼容端点（base_url + api_key）。
- Tavily 注册：https://tavily.com → 控制台拿 key。

---

## 10. 运行

```bash
cd web/backend
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8787
```

---

---

## 12. 边界与诚实表达（写进任何对外材料前必读）

- 状态写"原型 / 离线验证"，不写"上线系统"。
- 不写"服务了 N 位用户"（无真实用户记录）。
- 量化评测体系未建，相关能力标"待验证"。
- 每个技术词都能答"解决哪个节点、为何不用更简单方法、怎么失败"。