#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配置：从环境变量 / .env 读取（不进仓库）。"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass  # 无 python-dotenv 时退化为纯环境变量

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../ai-pm-research-system

# 研究引擎依赖（P1+ 真实检索 / 撰写时使用）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# 可选：模型名 / Base URL（默认走 DeepSeek 官方端点）
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
