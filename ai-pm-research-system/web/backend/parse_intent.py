#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""意图解析：把自然语言研究目标解析为结构化意图。"""
import json
from llm_client import chat, LLMError

_INTENT_TYPES = ["产品分析", "竞品对比", "市场扫描", "产品选型", "机会探索"]


def parse_intent(goal):
    """返回 dict：{intent, objects, mode, scope, depth}。
    - intent: 5 类之一
    - objects: 研究对象列表（对比模式/竞品分析模式下为多个）
    - mode: 对比模式 / 竞品分析模式 / 单品模式
    - scope: 限定的维度关键词（可能为空）
    - depth: 快/标准/深
    """
    sys = (
        "你是「AIPM·瞭望台」的意图解析器。用户会输入一个关于 AI 产品/赛道/公司的研究目标。"
        "请把它解析成严格 JSON，字段如下：\n"
        "- intent: 只能是以下之一：产品分析 / 竞品对比 / 市场扫描 / 产品选型 / 机会探索\n"
        "    · 提到「对比/比/vs/和 X 和 Y」→ 竞品对比；提到「赛道/行业/市场有哪些」→ 市场扫描；\n"
        "    · 提到「选型/怎么选/选哪个」→ 产品选型；提到「机会/空白/未满足」→ 机会探索；\n"
        "    · 仅指名一个产品且无明显对比/赛道/选型/机会意图 → 产品分析。\n"
        "- objects: 字符串数组，列出被点名的实体（产品/公司/赛道名）。竞品对比时填所有被比对象；"
        "单品分析时填 1 个；市场扫描填赛道名（可空，后续由检索补充）。\n"
        "- mode: 竞品对比模式（用户点名多个对象正面比）/ 竞品分析模式（单主体+默认竞品）/ 单品模式（仅深析单个）。\n"
        "- scope: 用户显式限定的维度关键词（如「长文本」「定价」），无则空字符串。\n"
        "- depth: 快/标准/深，默认「标准」。\n"
        "只输出 JSON，不要解释。"
    )
    user = "研究目标：" + goal
    try:
        raw = chat([
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ], json_mode=True)
        data = json.loads(raw)
    except LLMError as e:
        raise
    except Exception as e:
        raise LLMError("意图解析失败：" + str(e))

    intent = data.get("intent", "产品分析")
    if intent not in _INTENT_TYPES:
        intent = "产品分析"
    objects = data.get("objects") or []
    mode = data.get("mode", "单品模式")
    if not objects and intent in ("市场扫描", "机会探索"):
        mode = "单品模式" if mode in ("单品模式",) else mode
    return {
        "intent": intent,
        "objects": [str(o).strip() for o in objects if str(o).strip()],
        "mode": mode,
        "scope": data.get("scope", "") or "",
        "depth": data.get("depth", "标准"),
    }
