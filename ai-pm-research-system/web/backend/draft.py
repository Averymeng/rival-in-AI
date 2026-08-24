#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报告撰写：把检索上下文交给大模型，产出符合渲染约定的 Markdown。"""
from llm_client import chat, LLMError

DIMENSIONS = [
    "市场与定位", "产品与核心功能", "AI 能力", "数据壁垒",
    "技术与生态", "商业模式与定价", "用户体验", "增长与运营", "机会点", "风险与短板",
]


def _build_context(retrieved):
    blocks = []
    for q, items in retrieved.items():
        blocks.append("【检索问题】" + q)
        for it in items:
            blocks.append("- 《%s》 %s  %s" % (it.get("title", ""), it.get("url", ""), it.get("content", "")))
    return "\n".join(blocks)


def draft(goal, intent, objects, retrieved):
    """返回报告 Markdown 全文（符合 scripts/build_report.py 的约定写法）。"""
    objtxt = "、".join(objects) if objects else goal
    ctx = _build_context(retrieved)
    sys = (
        "你是「AIPM·瞭望台」的研究分析师。基于下方检索材料，产出一份面向 AI 产品决策者的研究报告。"
        "严格使用 Markdown，并遵守以下渲染约定（决定图表能否正确生成）：\n"
        "1. 第一行是报告大标题（# 标题），含研究对象名。\n"
        "2. 紧接着写「## 本次假设」，下面用「键：值」列出：分析对象、研究意图、选用维度、研究深度。"
        "（例如：分析对象：Cursor、Dify｜研究意图：竞品对比｜选用维度：全 10 维｜研究深度：标准）\n"
        "3. 「## 执行摘要」：下面用 - 项目符号列出 4-6 条最关键结论（一句一结论）。\n"
        "4. 后续章节固定顺序：市场概览、产品定位、功能矩阵、AI 能力、商业模式、增长、竞争格局、"
        "SWOT、" + ("机会、" if intent in ("机会探索", "产品分析", "产品选型") else "") + "来源。\n"
        "5. 必须有一个「## 能力雷达」章节，紧接一个评分矩阵表格（Markdown 表格）："
        "第一列名为「维度」，后续列是每个对比对象；必须额外保留「行业平均」列作为基准。"
        "表头至少要有 维度、主体、行业平均 三列。单元格只填 1-5 数字（5=领先、3=平均、1=基本不覆盖）。\n"
        "6. 在「## 市场地图」章节放一个表格，表头必须包含「X」「Y」「规模」三列（如 名称|X|Y|规模），"
        "每行一个对象，X/Y 为 0-10 数值，用于定位散点图。\n"
        "7. 「## 时间线」章节：每个条目用「- 年份或日期：事件」格式（如 - 2023：成立）。\n"
        "8. 「## 用户口碑」章节：每条用「- 正面：…」或「- 负面：…」格式举例。\n"
        "9. 「## 来源」章节：用一个表格，表头为「来源｜链接」，每行一个引用（来源名 + 真实 URL）。"
        "不要编造 URL；无确切来源时写「未查证」。\n"
        "10. SWOT 或文末可用形如「Must：…」「Should：…」「Could：…」列行动建议。\n"
        "纪律：结论分事实 / 洞察 / 建议；无法核实处明示「未查证」，严禁编造数据、份额、融资。"
        "用中文。不要输出代码块、不要额外解释，直接输出报告正文。"
    )
    user = (
        "研究目标：%s\n研究意图：%s\n研究对象：%s\n\n==== 检索材料 ====\n%s"
        % (goal, intent, objtxt, ctx)
    )
    try:
        return chat([
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ], temperature=0.4, timeout=180)
    except LLMError:
        raise
