#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIPM·瞭望台 · 可视化渲染器
约定写法（Markdown）→ 自包含 HTML（ECharts CDN）。
支持：能力雷达图 / 市场地图·机会地图 / 时间线 / 漏斗图 / 用户口碑 / 优先级看板 / 执行摘要条 / 来源卡。

设计语言（2025-08-23 迭代）：
  - 背景奶黄 #FFF9F0，主色暖橘 #F59E0B，强调浅黄 #FCD34D
  - 少边框、大留白、强字体层级
  - 执行摘要为全宽横向条，关键词与正文分色
"""
import sys, re, json, html, argparse, datetime

PALETTE = ["#F59E0B", "#F97316", "#EF4444", "#8B5CF6", "#6366F1", "#0EA5E9", "#10B981", "#EC4899", "#14B8A6"]

# 需要在 json.dumps 之后以原始 JS 注入的函数（占位 token -> 真实函数源码）
SCATTER_TOOLTIP = "function(p){return p.data.name+'<br/>X：'+p.data.value[0]+'　Y：'+p.data.value[1];}"
SCATTER_LABEL = "function(p){return p.data.name;}"


def parse_tables(lines):
    """返回 (start_idx, header, rows) 列表，表格为连续 | 行。"""
    tables = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].lstrip().startswith('|'):
            block = [lines[i]]
            j = i + 1
            while j < n and lines[j].lstrip().startswith('|'):
                block.append(lines[j]); j += 1
            if len(block) >= 3 and re.match(r'^\s*\|[\s:|-]+\|\s*$', block[1]):
                header = [c.strip() for c in block[0].strip().strip('|').split('|')]
                rows = []
                for r in block[2:]:
                    rows.append([c.strip() for c in r.strip().strip('|').split('|')])
                tables.append((i, header, rows))
            i = j
        else:
            i += 1
    return tables


def is_score_matrix(header, rows):
    if len(header) < 3: return False
    for r in rows:
        if len(r) < len(header): continue
        for v in r[1:]:
            if not re.match(r'^\d+(\.\d+)?$', v): return False
    return True


def is_scatter(header, rows):
    # 市场/机会地图：必须含 X / Y 坐标轴列，避免与评分矩阵（维度×对象）混淆
    if len(header) < 4: return False
    if not ('X' in header and 'Y' in header): return False
    for r in rows:
        if len(r) < 3: continue
        if not re.match(r'^\d+(\.\d+)?$', r[1]) or not re.match(r'^\d+(\.\d+)?$', r[2]):
            return False
    return True


def is_funnel(header, rows):
    """阶段 数值 表，视为漏斗。"""
    if len(header) < 2: return False
    if not re.match(r'^(阶段|环节|步骤|漏斗|层级)', header[0]): return False
    for r in rows:
        if len(r) < 2: continue
        if not re.match(r'^\d+(\.\d+)?$', r[1]): return False
    return True


def render_score_matrix(mid, header, rows):
    """评分矩阵仅渲染能力雷达图，避免维度重复出现。"""
    dims = header[1:]
    objects = [r[0] for r in rows]
    matrix = []
    for r in rows:
        vals = [float(v) if re.match(r'^\d+(\.\d+)?$', v) else None for v in r[1:]]
        matrix.append(vals)
    indicators = [{"name": d, "max": 5} for d in dims]
    radar_data = []
    for oi, obj in enumerate(objects):
        c = PALETTE[oi % len(PALETTE)]
        d = {"name": obj, "value": matrix[oi],
             "lineStyle": {"color": c, "width": 2.5},
             "itemStyle": {"color": c}}
        # 只对主体（首个对象）填充淡色，竞品仅描边，避免中心阴影重复叠加变深
        if oi == 0:
            d["areaStyle"] = {"color": c, "opacity": 0.12}
        radar_data.append(d)
    radar_opt = {
        "backgroundColor": "transparent",
        "textStyle": {"color": "#7C6F5D"},
        "tooltip": {"textStyle": {"color": "#2E2E38"}},
        "legend": {"bottom": 0, "data": objects, "textStyle": {"color": "#2E2E38", "fontSize": 12},
                   "itemGap": 16, "icon": "roundRect"},
        "radar": {
            "indicator": indicators, "radius": "62%", "center": ["50%", "46%"],
            "axisName": {"color": "#8A7D6B", "fontSize": 12},
            "splitLine": {"lineStyle": {"color": "#F3E6D0"}},
            "axisLine": {"lineStyle": {"color": "#F3E6D0"}},
            "splitArea": {"areaStyle": {"color": ["#FFF9F0", "#FFFFFF"]}}
        },
        "series": [{"type": "radar", "data": radar_data, "symbolSize": 4}]
    }
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">能力雷达图</span>'
            '<span class="chart-legend">评分口径：5=领先，3=平均，1=基本不覆盖</span></div>'
            '<div id="radar_' + str(mid) + '" class="echart"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("radar_' + str(mid) + '"));'
            'c.setOption(' + json.dumps(radar_opt, ensure_ascii=False) + ');REG.push(c);});</script>')


def render_scatter(mid, header, rows, is_opp):
    data = []
    for r in rows:
        if len(r) < 4: continue
        try:
            x = float(r[1]); y = float(r[2]); s = float(r[3])
        except Exception:
            continue
        data.append({"name": r[0], "value": [x, y, s]})
    title = "机会地图（空白区气泡）" if is_opp else "市场地图（定位散点）"
    color = "#F97316" if is_opp else "#F59E0B"
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "__SCATTER_TOOLTIP__"},
        "grid": {"left": "8%", "right": "8%", "top": "12%", "bottom": "14%"},
        "xAxis": {"name": "X · 专业 ←→ 大众", "nameTextStyle": {"color": "#8A7D6B"},
                  "min": 0, "max": 10, "axisLabel": {"color": "#8A7D6B"},
                  "axisLine": {"lineStyle": {"color": "#F3E6D0"}},
                  "splitLine": {"lineStyle": {"color": "#FFF3D9", "type": "dashed"}}},
        "yAxis": {"name": "Y · 模型能力 ←→ 生态", "nameTextStyle": {"color": "#8A7D6B"},
                  "min": 0, "max": 10, "axisLabel": {"color": "#8A7D6B"},
                  "axisLine": {"lineStyle": {"color": "#F3E6D0"}},
                  "splitLine": {"lineStyle": {"color": "#FFF3D9", "type": "dashed"}}},
        "series": [{"type": "scatter", "data": data, "symbolSize": "function(d){return 16+d[2]*7;}",
                    "itemStyle": {"color": color, "opacity": 0.75, "borderColor": "#FFFFFF", "borderWidth": 2},
                    "label": {"show": True, "formatter": "__SCATTER_LABEL__", "position": "top",
                              "color": "#2E2E38", "fontSize": 12}}]
    }
    opt_json = json.dumps(opt, ensure_ascii=False)
    opt_json = opt_json.replace('"__SCATTER_TOOLTIP__"', SCATTER_TOOLTIP).replace('"__SCATTER_LABEL__"', SCATTER_LABEL)
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">' + title + '</span></div>'
            '<div id="scatter_' + str(mid) + '" class="echart"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("scatter_' + str(mid)
            + '"));c.setOption(' + opt_json + ');REG.push(c);});</script>')


def render_funnel(mid, header, rows):
    stages = []
    for r in rows:
        if len(r) < 2: continue
        try:
            v = float(r[1])
        except Exception:
            continue
        stages.append({"value": v, "name": r[0]})
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "{b} : {c}"},
        "color": ["#F59E0B", "#F97316", "#FBBF24", "#FCD34D", "#EF4444", "#8B5CF6"],
        "series": [{"type": "funnel", "left": "10%", "top": 20, "bottom": 20,
                    "width": "80%", "min": 0, "max": max([s["value"] for s in stages]) if stages else 100,
                    "label": {"show": True, "position": "inside", "color": "#fff", "fontSize": 12,
                              "formatter": "{b}\n{c}"},
                    "itemStyle": {"borderColor": "#fff", "borderWidth": 2},
                    "data": stages}]
    }
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">转化漏斗</span></div>'
            '<div id="funnel_' + str(mid) + '" class="echart"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("funnel_' + str(mid)
            + '"));c.setOption(' + json.dumps(opt, ensure_ascii=False) + ');REG.push(c);});</script>')


def render_timeline(mid, items):
    names = [d for d, _ in items]
    vals = [v for _, v in items]
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis", "textStyle": {"color": "#2E2E38"}},
        "grid": {"left": "8%", "right": "6%", "top": "14%", "bottom": "10%"},
        "xAxis": {"type": "category", "data": names, "axisLabel": {"color": "#8A7D6B"},
                  "axisLine": {"lineStyle": {"color": "#F3E6D0"}}, "axisTick": {"show": False}},
        "yAxis": {"type": "value", "show": False},
        "series": [{"type": "line", "data": vals, "smooth": True, "symbol": "circle", "symbolSize": 8,
                    "lineStyle": {"color": "#F59E0B", "width": 3},
                    "itemStyle": {"color": "#F59E0B", "borderColor": "#fff", "borderWidth": 2},
                    "areaStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                              "colorStops": [{"offset": 0, "color": "rgba(245,158,11,.25)"},
                                                               {"offset": 1, "color": "rgba(245,158,11,.02)"}]}},
                    "label": {"show": True, "position": "top", "color": "#2E2E38", "formatter": "{c}"}}]
    }
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">时间线</span></div>'
            '<div id="tl_' + str(mid) + '" class="echart" style="height:220px"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("tl_' + str(mid)
            + '"));c.setOption(' + json.dumps(opt, ensure_ascii=False) + ');REG.push(c);});</script>')


def parse_kpi(text):
    """把摘要项解析成 KPI 条或洞察条。
    返回 (type, big, label, note)
    type: 'metric' | 'insight'
    """
    text = text.strip()
    # 1) 数字/符号开头：$2B+ / 50%+ / #1 / 200% / 1.2x
    m = re.match(r'^[\$¥€]?\s*[\d\.,]+\s*[%x倍万亿KMB+\-]*|[\#]\s*\d+|\d+\s*[%x倍万亿KMB+\-]*\s+(.+)$', text)
    if m:
        # 重新精确匹配：数字部分 + 空格 + 正文
        m2 = re.match(r'^([\$¥€]?\s*[\d\.,]+\s*[%x倍万亿KMB+\-]*|[\#]\s*\d+|\d+\s*[%x倍万亿KMB+\-]*)\s+(.+)$', text)
        if m2:
            return ('metric', m2.group(1).strip(), m2.group(2).strip(), '')
    # 2) 标签：内容 模式（优先短标签；若无短标签则取首个全角/半角冒号前作为标签）
    m = re.match(r'^([^：:]{1,8})[：:]\s*(.+)$', text)
    if m:
        return ('insight', '', m.group(1).strip(), m.group(2).strip())
    m = re.match(r'^(.+?)[：:]\s*(.+)$', text)
    if m:
        return ('insight', '', m.group(1).strip(), m.group(2).strip())
    return ('insight', '', text, '')


def render_summary(items):
    rows = []
    for s in items:
        t, big, label, note = parse_kpi(s)
        if t == 'metric':
            rows.append('<div class="sum-row metric">'
                        '<div class="sum-big">' + html.escape(big) + '</div>'
                        '<div class="sum-body"><div class="sum-label">' + html.escape(label) + '</div>'
                        + ('<div class="sum-note">' + html.escape(note) + '</div>' if note else '')
                        + '</div></div>')
        else:
            body = html.escape(note) if note else html.escape(label)
            kw = html.escape(label) if note else ''
            rows.append('<div class="sum-row insight">'
                        + ('<div class="sum-keyword">' + kw + '</div>' if kw else '')
                        + '<div class="sum-body">' + body + '</div></div>')
    return '<div class="sum-list">' + "".join(rows) + '</div>'


def render_sentiment(items):
    pos = sum(1 for k, _ in items if k == "正面")
    neg = sum(1 for k, _ in items if k == "负面")
    tot = pos + neg
    pw = 0 if tot == 0 else round(pos / tot * 100)
    nw = 0 if tot == 0 else round(neg / tot * 100)
    cards = ""
    for k, t in items:
        cls = "pos" if k == "正面" else "neg"
        cards += '<div class="quote ' + cls + '"><span class="qtag">' + k + '</span>' + html.escape(t) + '</div>'
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">用户口碑</span>'
            '<span class="chart-legend">样本 ' + str(tot) + ' · 正面 ' + str(pw) + '%</span></div>'
            '<div class="sent-bar"><div class="sent-pos" style="width:' + str(pw) + '%"></div>'
            '<div class="sent-neg" style="width:' + str(nw) + '%"></div></div>'
            '<div class="quote-list">' + cards + '</div></div>')


def render_priority(must, should, could):
    def col(title, items, cls):
        lis = "".join("<li>" + html.escape(x) + "</li>" for x in items)
        return '<div class="pri-col ' + cls + '"><div class="pri-h">' + title + '</div><ul>' + lis + '</ul></div>'
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">优先级看板（建议分级）</span></div>'
            '<div class="pri-row">' + col("Must 必做", must, "m") + col("Should 应做", should, "s")
            + col("Could 可做", could, "c") + '</div></div>')


CSS = """
:root{
  --bg:#FFF9F0;
  --card:#FFFFFF;
  --ink:#2E2E38;
  --muted:#8A7D6B;
  --line:#F3E6D0;
  --brand:#F59E0B;
  --brand-light:#FCD34D;
  --brand-ghost:#FFF3D9;
  --green:#10B981;
  --amber:#F59E0B;
  --red:#EF4444;
  --sidebar:#2D2A24;
  --sidebar-text:#CFC8BC;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.7;font-size:14px;}
.app{display:flex;min-height:100vh;}
.sidebar{width:260px;background:var(--sidebar);color:var(--sidebar-text);position:fixed;left:0;top:0;bottom:0;overflow:auto;padding:28px 22px;z-index:20;}
.brand{font-size:18px;font-weight:700;color:#fff;letter-spacing:1px;margin-bottom:8px;}
.brand span{font-weight:400;opacity:.7;}
.brand-sub{font-size:12px;color:var(--sidebar-text);opacity:.7;margin-bottom:32px;}
.nav-list{list-style:none;margin:0;padding:0;}
.nav-list li{margin:6px 0;}
.nav-list a{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:10px;color:var(--sidebar-text);text-decoration:none;font-size:13px;transition:.15s;}
.nav-list a::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--sidebar-text);opacity:.4;}
.nav-list a:hover,.nav-list a.active{background:rgba(255,255,255,.08);color:#fff;}
.nav-list a.active::before{background:var(--brand-light);opacity:1;}
.main{margin-left:260px;flex:1;padding:40px 48px 80px;max-width:1100px;}
.top-header{margin-bottom:32px;}
.top-header h1{margin:0;font-size:32px;font-weight:700;line-height:1.25;letter-spacing:.5px;color:var(--ink);}
.top-sub{display:flex;align-items:center;gap:10px;margin-top:8px;font-size:13px;color:var(--muted);}
.tags{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px;}
.tag{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid var(--line);border-radius:20px;padding:6px 14px;font-size:12px;color:var(--muted);}
.tag b{color:var(--ink);font-weight:600;}
.assumption-bar{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin-bottom:28px;font-size:13px;color:var(--muted);display:flex;flex-wrap:wrap;gap:12px 24px;}
.assumption-bar span{white-space:nowrap;}
.assumption-bar b{color:var(--ink);font-weight:600;margin-right:4px;}
section{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px 32px;margin-bottom:24px;width:100%;}
section h2{margin:0 0 18px;font-size:22px;font-weight:600;line-height:1.4;color:var(--ink);}
section h3{font-size:16px;font-weight:600;color:var(--ink);margin:20px 0 10px;}
section p{margin:8px 0;font-size:14px;color:var(--ink);line-height:1.75;}
section ul,section ol{margin:10px 0;padding-left:22px;color:var(--ink);font-size:14px;line-height:1.75;}
section li{margin:5px 0;}
.sum-list{display:flex;flex-direction:column;gap:14px;margin:20px 0 10px;}
.sum-row{display:flex;align-items:flex-start;gap:16px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 20px;}
.sum-row.metric{align-items:center;}
.sum-big{font-size:30px;font-weight:700;color:var(--brand);line-height:1;min-width:90px;text-align:left;}
.sum-keyword{font-size:14px;font-weight:600;color:var(--brand);min-width:120px;flex-shrink:0;line-height:1.6;}
.sum-body{flex:1;font-size:14px;color:var(--ink);line-height:1.7;}
.sum-label{font-size:14px;font-weight:600;color:var(--brand);}
.sum-note{font-size:12px;color:var(--muted);margin-top:4px;}
.chart-card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px 26px;margin:22px 0;}
.chart-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px;}
.chart-title{font-size:16px;font-weight:600;color:var(--ink);}
.chart-legend{font-size:11px;color:var(--muted);}
.echart{width:100%;height:420px;}
.pri-row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
.pri-col{background:var(--bg);border-radius:14px;padding:16px;}
.pri-col.m{border-left:4px solid var(--red);} .pri-col.s{border-left:4px solid var(--amber);} .pri-col.c{border-left:4px solid var(--green);}
.pri-h{font-weight:700;font-size:14px;margin-bottom:10px;color:var(--ink);} .pri-col ul{margin:0;padding-left:18px;font-size:13px;color:var(--muted);line-height:1.7;}
.sent-bar{display:flex;height:14px;border-radius:7px;overflow:hidden;margin-bottom:10px;background:var(--line);}
.sent-pos{background:var(--green);} .sent-neg{background:var(--red);}
.quote-list{display:flex;flex-direction:column;gap:10px;}
.quote{font-size:13px;padding:12px 14px;border-radius:10px;background:var(--bg);line-height:1.6;}
.quote.pos{border-left:3px solid var(--green);} .quote.neg{border-left:3px solid var(--red);}
.qtag{display:inline-block;font-size:11px;color:var(--muted);margin-right:8px;font-weight:600;}
.src-grid{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;}
.src-card{font-size:12px;color:var(--muted);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 10px;}
.src-card a{color:var(--brand);text-decoration:none;}
.src-card a:hover{text-decoration:underline;}
.tbl{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;margin:10px 0;}
.tbl th,.tbl td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line);}
.tbl th{font-weight:600;color:var(--muted);font-size:12px;background:var(--bg);position:sticky;top:0;}
.tbl tbody tr:hover{background:rgba(245,158,11,.05);}
.tbl tr:last-child td{border-bottom:none;}
@media(max-width:900px){
  .sidebar{display:none;}
  .main{margin-left:0;padding:24px;max-width:none;}
  .sum-row{flex-direction:column;}
  .sum-big{min-width:auto;}
}
@media(max-width:640px){
  .pri-row{grid-template-columns:1fr;}
  .tags{display:none;}
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    with open(args.input, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")

    title = "AI PM 研究报告"
    assumption = {}
    body_parts = []
    sections = []  # (id, title)
    tables = parse_tables(lines)
    table_at = {t[0]: t for t in tables}

    i = 0; mid = 0; sec_idx = 0
    summary_items = []; priority = {"must": [], "should": [], "could": []}
    sentiment = []; timeline = []; evidence = []; special_sid = {}
    cur_section = ""
    open_section = False
    n = len(lines)

    # 第一遍先收集所有 h2 作为导航
    for ln in lines:
        m = re.match(r"^##\s+(.*)$", ln.strip())
        if m:
            sec_idx += 1
            sections.append(("sec-" + str(sec_idx), m.group(1).strip()))
    sec_idx = 0

    while i < n:
        line = lines[i]
        m = re.match(r"^(#{1,2})\s+(.*)$", line)
        if m:
            level = len(m.group(1)); htext = m.group(2).strip()
            if level == 1:
                title = htext
                i += 1; continue
            sec_idx += 1
            cur_section = htext
            sid = "sec-" + str(sec_idx)
            close_prev = "</section>" if open_section else ""
            open_section = False
            if htext == "执行摘要":
                body_parts.append(close_prev + '<section id="' + sid + '"><h2>执行摘要</h2><div class="summary-grid" id="sum"></div></section>')
            elif htext == "来源":
                body_parts.append(close_prev + '<section id="' + sid + '"><h2>来源</h2><div id="src"></div></section>')
            elif htext in ("用户口碑", "时间线"):
                # 口碑/时间线由专用卡片渲染，用插槽占位，避免「空标题段 + 重复卡片」
                body_parts.append(close_prev + '<div id="' + sid + '" class="slot"></div>')
                special_sid[htext] = sid
            else:
                body_parts.append(close_prev + '<section id="' + sid + '"><h2>' + html.escape(htext) + '</h2>')
                open_section = True
            i += 1; continue

        # 研究简报 / 本次假设 → 顶部标签
        if "研究简报" in line or "本次假设" in line:
            brief_lines = []
            j = i + 1
            while j < n and lines[j].strip() and not lines[j].lstrip().startswith("#"):
                brief_lines.append(lines[j]); j += 1
            for bl in brief_lines:
                bl = bl.strip().lstrip("·-").strip()
                if "：" in bl:
                    k, v = bl.split("：", 1)
                    assumption[k.strip()] = v.strip()
                elif bl:
                    assumption["备注"] = bl
            i = j; continue

        if i in table_at:
            _, header, rows = table_at[i]
            # 优先识别 4 列散点/气泡表（市场地图/机会地图），避免被 score_matrix 误吞
            if is_scatter(header, rows):
                mid += 1
                body_parts.append(render_scatter(mid, header, rows, "机会" in cur_section))
            elif is_score_matrix(header, rows):
                mid += 1
                body_parts.append(render_score_matrix(mid, header, rows))
            elif is_funnel(header, rows) or ("漏斗" in cur_section and len(header) >= 2):
                mid += 1
                body_parts.append(render_funnel(mid, header, rows))
            elif "来源" in header[0] or "链接" in header[-1] or "链接" in " ".join(header):
                for r in rows:
                    if len(r) >= 2:
                        evidence.append((r[0], r[-1]))
            else:
                th = "".join("<th>" + html.escape(c) + "</th>" for c in header)
                trs = "".join("<tr>" + "".join("<td>" + html.escape(c) + "</td>" for c in r) + "</tr>" for r in rows)
                body_parts.append('<table class="tbl"><thead><tr>' + th + '</tr></thead><tbody>' + trs + '</tbody></table>')
            i = table_at[i][0] + 1
            while i < n and lines[i].lstrip().startswith("|"):
                i += 1
            continue

        if cur_section == "时间线" and line.strip().startswith("-"):
            mm = re.match(r"-\s*([\d]{4}[\d\-]*)\s*[：:]\s*(.*)", line.strip())
            if mm: timeline.append((mm.group(1), float(mm.group(2)) if re.match(r'^\d+(\.\d+)?$', mm.group(2)) else len(timeline)+1))
            i += 1; continue
        if cur_section == "用户口碑" and line.strip().startswith("-"):
            mm = re.match(r"-\s*(正面|负面)\s*[：:]\s*(.*)", line.strip())
            if mm: sentiment.append((mm.group(1), mm.group(2)))
            i += 1; continue
        mm = re.match(r"^(Must|Should|Could)\s*[：:]\s*(.*)", line.strip())
        if mm:
            priority[mm.group(1).lower()].append(mm.group(2))
            i += 1; continue
        if cur_section == "执行摘要" and line.strip().startswith("-"):
            txt = line.strip().lstrip("-").strip()
            if txt: summary_items.append(txt)
            i += 1; continue
        if line.strip() and not line.lstrip().startswith("#"):
            body_parts.append("<p>" + html.escape(line.strip()) + "</p>")
        i += 1

    if open_section:
        body_parts.append("</section>")

    # 处理执行摘要 KPI 卡
    if summary_items:
        body_parts = [p.replace('<div class="summary-grid" id="sum"></div>', render_summary(summary_items)) for p in body_parts]

    if timeline:
        mid += 1
        tid = special_sid.get("时间线")
        if tid:
            body_parts = [p.replace('<div id="' + tid + '" class="slot"></div>', render_timeline(mid, timeline)) for p in body_parts]
    if sentiment:
        sid_ = special_sid.get("用户口碑")
        if sid_:
            body_parts = [p.replace('<div id="' + sid_ + '" class="slot"></div>', render_sentiment(sentiment)) for p in body_parts]
    if priority["must"] or priority["should"] or priority["could"]:
        body_parts.append(render_priority(priority["must"], priority["should"], priority["could"]))
    if evidence:
        cards = ""
        for nm, lk in evidence:
            if lk.startswith("http"):
                # 只显示来源名作为可点击链接，不堆砌原始 URL
                cards += '<div class="src-card"><a href="' + lk + '" target="_blank" rel="noopener">' + html.escape(nm) + '</a></div>'
            else:
                cards += '<div class="src-card">' + html.escape(nm) + '：' + html.escape(lk) + '</div>'
        cards = '<div class="src-grid">' + cards + '</div>'
        body_parts = [p.replace('<div id="src"></div>', cards) for p in body_parts]

    # 构建导航
    nav_items = ""
    for sid, stitle in sections:
        nav_items += '<li><a href="#' + sid + '">' + html.escape(stitle) + '</a></li>'

    # 构建顶部标签
    tag_html = ""
    for k, v in assumption.items():
        if k == "备注":
            continue
        tag_html += '<span class="tag"><b>' + html.escape(k) + '</b>：' + html.escape(v) + '</span>'
    if not tag_html:
        tag_html = '<span class="tag"><b>模式</b>：默认</span>'

    # 假设条
    assumption_bar = ""
    if assumption:
        assumption_bar = '<div class="assumption-bar">' + "".join(
            '<span><b>' + html.escape(k) + '</b>' + html.escape(v) + '</span>' for k, v in assumption.items()
        ) + '</div>'

    today = datetime.datetime.now().strftime("%Y年%-m月%-d日")

    html_doc = ('<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + html.escape(title) + '</title>'
        '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>'
        '<style>' + CSS + '</style></head><body>'
        '<div class="app">'
        '<aside class="sidebar">'
        '<div class="brand">AIPM<span>·瞭望台</span></div>'
        '<div class="brand-sub">AI PM 研究与报告系统</div>'
        '<ul class="nav-list">' + nav_items + '</ul>'
        '</aside>'
        '<main class="main">'
        '<header class="top-header">'
        '<h1>' + html.escape(title) + '</h1>'
        '<div class="top-sub"><span>' + today + '</span><span>AIPM·瞭望台</span></div>'
        '<div class="tags">' + tag_html + '</div>'
        '</header>'
        + assumption_bar + "".join(body_parts) +
        '</main></div>'
        '<script>var REG=[];window.addEventListener("resize",function(){REG.forEach(function(c){c.resize();});});'
        'document.querySelectorAll(".nav-list a").forEach(function(a){'
        'a.addEventListener("click",function(e){document.querySelectorAll(".nav-list a").forEach(function(x){x.classList.remove("active");});'
        'this.classList.add("active");});});'
        '</script>'
        '</body></html>')
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print("OK -> " + args.output + " (" + str(len(html_doc)) + " bytes)")


if __name__ == "__main__":
    main()
