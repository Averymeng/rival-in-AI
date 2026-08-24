#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIPM·瞭望台 Web 后端。

提供：首页、历史报告列表、报告浏览，以及 /api/research 研究闭环
（意图解析 → Tavily 检索 → DeepSeek 撰写 → 渲染 → 存档）。
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../ai-pm-research-system
FRONTEND_DIR = BASE_DIR / "web" / "frontend"
REPORTS_DIR = BASE_DIR / "reports" / "output"

app = FastAPI(title="AIPM·瞭望台")


@app.post("/api/research")
def research(goal: dict):
    """接收研究目标，跑完整研究闭环，返回报告访问信息。"""
    goal_text = (goal or {}).get("goal", "").strip()
    if not goal_text:
        raise HTTPException(status_code=400, detail="缺少研究目标")
    try:
        from pipeline import run
        info = run(goal_text)
    except Exception as e:  # 研究链路任意环节失败都回显原因，不静默吞掉
        raise HTTPException(status_code=500, detail="研究失败：" + str(e))
    return {
        "ok": True,
        "name": info["name"],
        "file": info["file"],
        "title": info["title"],
        "intent": info["intent"],
        "objects": info["objects"],
        "url": "/report/" + info["file"],
    }


def _title_of(name):
    md = REPORTS_MD / (name + ".md")
    if md.exists():
        with open(md, encoding="utf-8") as f:
            for ln in f:
                if ln.startswith("# "):
                    return ln[2:].strip()
    return name


REPORTS_MD = BASE_DIR / "reports"


@app.get("/api/reports")
def list_reports():
    """列出已生成的报告（按文件名），前端据此展示历史报告。"""
    if not REPORTS_DIR.exists():
        return {"reports": []}
    files = sorted(
        (p for p in REPORTS_DIR.glob("*.html") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    reports = [
        {
            "name": p.stem,
            "file": p.name,
            "title": _title_of(p.stem),
            "updated": p.stat().st_mtime,
        }
        for p in files
    ]
    return {"reports": reports}


@app.get("/report/{filename}")
def get_report(filename: str):
    """直接打开某份报告 HTML。"""
    # 仅允许当前目录下的 html，防路径穿越
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="bad filename")
    target = REPORTS_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(str(target), media_type="text/html")


@app.get("/static/{filename}")
def get_static(filename: str):
    target = FRONTEND_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(str(target))


@app.get("/")
def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"), media_type="text/html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
