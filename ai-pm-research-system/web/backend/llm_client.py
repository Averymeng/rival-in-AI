#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LLM 调用助手：封装 DeepSeek（OpenAI 兼容）的请求。"""
import json
import requests
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


class LLMError(Exception):
    pass


def chat(messages, *, json_mode=False, temperature=0.3, timeout=120):
    """调用 DeepSeek Chat。messages 为 [{"role":..,"content":..}]。
    json_mode=True 时要求模型输出 JSON（response_format）。"""
    if not DEEPSEEK_API_KEY:
        raise LLMError("缺少 DEEPSEEK_API_KEY，无法调用大模型。请在 .env 配置后重试。")
    url = DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        resp = requests.post(url, json=payload, headers={
            "Authorization": "Bearer " + DEEPSEEK_API_KEY,
            "Content-Type": "application/json",
        }, timeout=timeout)
    except requests.exceptions.ConnectionError as e:
        raise LLMError("无法连接大模型服务：" + str(e))
    if resp.status_code != 200:
        raise LLMError("大模型返回 %d：%s" % (resp.status_code, resp.text[:500]))
    data = resp.json()
    return data["choices"][0]["message"]["content"]
