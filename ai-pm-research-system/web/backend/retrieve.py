#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实时检索：封装 Tavily 搜索，返回带来源的结果。"""
import requests
from config import TAVILY_API_KEY

SEARCH_URL = "https://api.tavily.com/search"


class RetrieveError(Exception):
    pass


def search(query, max_results=5):
    """调用 Tavily。返回 list of {title, url, content}。"""
    if not TAVILY_API_KEY:
        raise RetrieveError("缺少 TAVILY_API_KEY，无法联网检索。请在 .env 配置后重试。")
    try:
        resp = requests.post(SEARCH_URL, json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_answer": False,
        }, timeout=60)
    except requests.exceptions.ConnectionError as e:
        raise RetrieveError("无法连接搜索服务：" + str(e))
    if resp.status_code != 200:
        raise RetrieveError("搜索返回 %d：%s" % (resp.status_code, resp.text[:300]))
    data = resp.json()
    results = []
    for r in data.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": (r.get("content") or "").strip(),
        })
    return results


def gather(goal, intent, objects, scope=""):
    """为本次研究生成检索 queries 并执行，返回 {query: [results]}。"""
    queries = []
    if objects:
        for obj in objects:
            queries.append("%s 产品 功能 官网" % obj)
            queries.append("%s 定价 收费 价格" % obj)
            queries.append("%s 用户 评价 体验" % obj)
            if scope:
                queries.append("%s %s" % (obj, scope))
    else:
        queries.append(goal)
        queries.append(goal + " 主要玩家 排名")
    # 去重并限制总量，控制成本
    seen, final = set(), []
    for q in queries:
        if q not in seen:
            seen.add(q); final.append(q)
    final = final[:8]

    out = {}
    for q in final:
        try:
            out[q] = search(q, max_results=4)
        except RetrieveError as e:
            out[q] = [{"title": "检索失败", "url": "", "content": str(e)}]
    return out
