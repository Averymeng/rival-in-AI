#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究闭环：意图解析 → 检索 → 撰写 → 渲染 → 存档。"""
import datetime
import re
import sys
from pathlib import Path

# 载入仓库顶层 scripts 下的渲染器（build_report.py），复用既有可视化引擎
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from build_report import render  # noqa: E402

from config import BASE_DIR  # noqa: E402
from parse_intent import parse_intent  # noqa: E402
from retrieve import gather  # noqa: E402
from draft import draft  # noqa: E402

REPORTS_MD = BASE_DIR / "reports"
REPORTS_OUT = BASE_DIR / "reports" / "output"
REPORTS_MD.mkdir(exist_ok=True)
REPORTS_OUT.mkdir(exist_ok=True)


def _slug(goal):
    s = re.sub(r"[^\w一-龥]+", "_", goal).strip("_")
    return (s[:40] or "report") + "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def _first_line_title(md):
    for ln in md.split("\n"):
        if ln.startswith("# "):
            return ln[2:].strip()
    return "研究报告"


def run(goal):
    """完整跑一遍研究，返回报告元信息字典。失败时抛出异常。"""
    intent = parse_intent(goal)
    objects = intent["objects"]
    retrieved = gather(goal, intent["intent"], objects, intent.get("scope", ""))
    md = draft(goal, intent["intent"], objects, retrieved)

    name = _slug(goal)
    md_path = REPORTS_MD / (name + ".md")
    html_path = REPORTS_OUT / (name + ".html")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    try:
        render(str(md_path), str(html_path))
    except Exception as e:
        raise RuntimeError("报告渲染失败：" + str(e))

    return {
        "name": name,
        "file": html_path.name,
        "title": _first_line_title(md),
        "intent": intent["intent"],
        "objects": objects,
    }
