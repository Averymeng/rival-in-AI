# 预置竞品清单（仅作竞品分析模式种子）

非 RAG、非向量库，仅为**静态种子表**，用于给用户快速建议「同品类竞品」。确认后实时检索扩充，**不限制搜索范围**。

## 取种子规则

竞品分析模式下，用户输入 1 个主体时：
1. 在下方按**产品类别**找到该主体所在类。
2. 取同类别中**其余产品**作为默认竞品（默认上限 5 个；同类不足则跨相邻品类补足）。
3. 主体不在表中 → 不硬塞，改为实时检索建议，或轻问用户「想对比哪类」。
4. 厂商仅作括号内标注，不作为竞品建议（避免"OpenAI vs 豆包"这种层级错配）。

> 每类产品只列**代表选手**，非穷举；真实检索开放联网，远多于此表。

---

## 1. AI 对话 / 大模型助手
ChatGPT（OpenAI）、Claude（Anthropic）、Gemini（Google）、Kimi（月之暗面）、豆包（字节）、元宝（腾讯）、文心一言（百度）、通义千问（阿里）、智谱清言（智谱）、海螺 AI（MiniMax）

## 2. AI 图像 / 视频生成
即梦（字节）、可灵（快手）、Runway、Pika、PixVerse、海螺视频（MiniMax）、Midjourney、Stable Diffusion（Stability AI）

## 3. AI 办公 / 效率
Notion AI、飞书智能伙伴（字节）、钉钉 AI（阿里）、WPS AI（金山）、Microsoft 365 Copilot（微软）、Gemini for Workspace（Google）

## 4. AI 营销 / 内容创作
小云雀 Pippit（字节）、即创（字节）、腾讯智影（腾讯）、Adobe Firefly（Adobe）、Canva Magic（Canva）

## 5. AI 编程
Cursor（Anysphere）、GitHub Copilot（微软）、Claude Code（Anthropic）、通义灵码（阿里）、Codeium / Windsurf（Codeium→Cognition）、Trae（字节）

## 6. AI 搜索
Perplexity、秘塔、Genspark、Felo

---

## 厂商速查（仅标注用，不作竞品）
OpenAI｜Anthropic｜Google｜微软｜Meta｜字节｜腾讯｜阿里｜百度｜快手｜月之暗面｜智谱｜MiniMax｜金山｜Adobe｜Canva｜Stability AI｜Anysphere｜Cognition
