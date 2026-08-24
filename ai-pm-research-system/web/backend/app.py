#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIPM·瞭望台 Web 后端（P0 骨架）。

阶段目标：能跑通首页 + 列出历史报告（读取现有 reports/output/*.html）。
后续阶段（P1+）在此挂载 /api/research 研究闭环。
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../ai-pm-research-system
FRONTEND_DIR = BASE_DIR / "web" / "frontend"
REPORTS_DIR = BASE_DIR / "reports" / "output"

app = FastAPI(title="AIPM·瞭望台")


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
    return fastapi_respond_html(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
