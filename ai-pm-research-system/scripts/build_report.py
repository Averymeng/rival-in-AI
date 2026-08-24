#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIPM·瞭望台 · 可视化渲染器
约定写法（Markdown）→ 自包含 HTML（ECharts CDN）。
支持：能力雷达图 / 市场地图（带面积气泡）/ 竞争关系图 / 梯队金字塔 / 时间线 / 漏斗图 /
      用户口碑 / 优先级看板 / 行动建议卡 / 执行摘要条 / SWOT / 来源行内链接。

设计语言（2025-08-25 迭代）：
  - 背景奶黄 #FFF9F0，主色暖橘 #F59E0B，强调浅黄 #FCD34D
  - 少边框、大留白、强字体层级
  - 每个章节独立成块，图表归属其章节，杜绝错位
  - 全文中禁止出现原始 Markdown 符号（- ** 等）
"""
import sys, re, json, html, argparse, datetime

PALETTE = ["#F59E0B", "#F97316", "#EF4444", "#8B5CF6", "#6366F1", "#0EA5E9", "#10B981", "#EC4899", "#14B8A6"]

SCATTER_TOOLTIP = "function(p){return p.data.name+'<br/>X：'+p.data.value[0]+'　Y：'+p.data.value[1]+'<br/>规模：'+p.data.value[2];}"
SCATTER_LABEL = "function(p){return p.data.name;}"


def clean(s):
    """去除行首项目符号与 Markdown 加粗/反引号标记，得到纯文本。"""
    s = s.strip()
    s = re.sub(r'^[-*+]\s*', '', s)
    s = s.replace('**', '').replace('`', '').replace('*', '')
    return s.strip()


def split_kv(s):
    """按首个中文/英文冒号拆分标题与正文。"""
    m = re.match(r'^([^：:]{1,20})[：:]\s*(.*)$', s.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return '', s.strip()


def parse_tables(lines):
    """返回 (start_idx, header, rows) 列表，表格为连续 | 行。兼容全角｜分隔符。"""
    tables = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].lstrip().startswith('|'):
            block = [lines[i]]
            j = i + 1
            while j < n and lines[j].lstrip().startswith('|'):
                block.append(lines[j]); j += 1
            if len(block) >= 3 and re.match(r'^\s*\|[\s:｜|-]+\|\s*$', block[1]):
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
    if len(header) < 3:
        return False
    for r in rows:
        if len(r) < len(header):
            continue
        for v in r[1:]:
            if not re.match(r'^\d+(\.\d+)?$', v):
                return False
    return True


def is_scatter(header, rows):
    if len(header) < 4:
        return False
    has_x = any('X' in h.upper() for h in header)
    has_y = any('Y' in h.upper() for h in header)
    if not (has_x and has_y):
        return False
    for r in rows:
        if len(r) < 3:
            continue
        if not re.match(r'^\d+(\.\d+)?$', r[1]) or not re.match(r'^\d+(\.\d+)?$', r[2]):
            return False
    return True


def is_funnel(header, rows):
    if len(header) < 2:
        return False
    if not re.match(r'^(阶段|环节|步骤|漏斗|层级)', header[0]):
        return False
    for r in rows:
        if len(r) < 2:
            continue
        if not re.match(r'^\d+(\.\d+)?$', r[1]):
            return False
    return True


def classify_table(header, rows):
    if is_scatter(header, rows):
        return 'scatter'
    if is_score_matrix(header, rows):
        return 'matrix'
    if is_funnel(header, rows):
        return 'funnel'
    if '链接' in header or header[0] in ('来源', '来源链接', '资料来源'):
        return 'source'
    return 'table'


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


def render_scatter(mid, header, rows, is_opp=False):
    """市场地图：带面积覆盖的气泡（symbolSize 由规模决定，并叠加半透明光晕）。"""
    data = []
    for r in rows:
        if len(r) < 4:
            continue
        try:
            x = float(r[1]); y = float(r[2]); s = float(r[3])
        except Exception:
            continue
        data.append({"name": r[0], "value": [x, y, s]})
    title = "机会地图（空白区气泡）" if is_opp else "市场地图（定位气泡，面积=规模）"
    color = "#F97316" if is_opp else "#F59E0B"
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "__SCATTER_TOOLTIP__"},
        "grid": {"left": "9%", "right": "9%", "top": "12%", "bottom": "14%"},
        "xAxis": {"name": "X · 专业 ←→ 大众", "nameTextStyle": {"color": "#8A7D6B"},
                  "min": 0, "max": 10, "axisLabel": {"color": "#8A7D6B"},
                  "axisLine": {"lineStyle": {"color": "#F3E6D0"}},
                  "splitLine": {"lineStyle": {"color": "#FFF3D9", "type": "dashed"}}},
        "yAxis": {"name": "Y · 模型能力 ←→ 生态", "nameTextStyle": {"color": "#8A7D6B"},
                  "min": 0, "max": 10, "axisLabel": {"color": "#8A7D6B"},
                  "axisLine": {"lineStyle": {"color": "#F3E6D0"}},
                  "splitLine": {"lineStyle": {"color": "#FFF3D9", "type": "dashed"}}},
        "series": [
            {"type": "scatter", "data": data,
             "symbolSize": "function(d){return 26 + d[2]*11;}",
             "itemStyle": {"color": color, "opacity": 0.18, "borderColor": color, "borderWidth": 0},
             "z": 1, "silent": True, "label": {"show": False}},
            {"type": "scatter", "data": data,
             "symbolSize": "function(d){return 18 + d[2]*7;}",
             "itemStyle": {"color": color, "opacity": 0.85, "borderColor": "#FFFFFF", "borderWidth": 2},
             "label": {"show": True, "formatter": "__SCATTER_LABEL__", "position": "top",
                       "color": "#2E2E38", "fontSize": 12}, "z": 2}
        ]
    }
    opt_json = json.dumps(opt, ensure_ascii=False)
    opt_json = opt_json.replace('"__SCATTER_TOOLTIP__"', SCATTER_TOOLTIP).replace('"__SCATTER_LABEL__"', SCATTER_LABEL)
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">' + title + '</span>'
            '<span class="chart-legend">气泡越大=市场份额/影响力越高</span></div>'
            '<div id="scatter_' + str(mid) + '" class="echart"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("scatter_' + str(mid)
            + '"));c.setOption(' + opt_json + ');REG.push(c);});</script>')


def render_funnel(mid, header, rows):
    stages = []
    for r in rows:
        if len(r) < 2:
            continue
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
            '<div id="tl_' + str(mid) + '" class="echart" style="height:240px"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("tl_' + str(mid)
            + '"));c.setOption(' + json.dumps(opt, ensure_ascii=False) + ');REG.push(c);});</script>')


def render_competition_graph(mid, center, others):
    nodes = [{"name": center, "symbolSize": 52, "itemStyle": {"color": "#F59E0B"},
              "label": {"show": True, "color": "#2E2E38", "fontSize": 13, "fontWeight": "bold"}}]
    links = []
    for o in others:
        nodes.append({"name": o, "symbolSize": 34, "itemStyle": {"color": "#F97316"},
                      "label": {"show": True, "color": "#2E2E38", "fontSize": 12}})
        links.append({"source": center, "target": o})
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"show": False},
        "series": [{"type": "graph", "layout": "circular", "center": ["50%", "52%"], "roam": False,
                    "circular": {"rotateLabel": True},
                    "lineStyle": {"color": "#F3E6D0", "width": 2, "curveness": 0.05},
                    "emphasis": {"focus": "adjacency"},
                    "data": nodes, "links": links}]
    }
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">竞争格局 · 对标关系</span>'
            '<span class="chart-legend">中心=本报告主体，外环=主要竞品</span></div>'
            '<div id="comp_' + str(mid) + '" class="comp-graph"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("comp_' + str(mid)
            + '"));c.setOption(' + json.dumps(opt, ensure_ascii=False) + ');REG.push(c);});</script>')


def render_pyramid(market_map):
    """依据市场地图的「规模」列，将产品划分为三个梯队，金字塔呈现。"""
    try:
        items = []
        for r in market_map[2]:
            if len(r) < 4:
                continue
            items.append((r[0], float(r[3])))
    except Exception:
        items = []
    if not items:
        return ''
    tiers = {'t1': [], 't2': [], 't3': []}
    for name, sc in items:
        if sc >= 7:
            tiers['t1'].append(name)
        elif sc >= 4:
            tiers['t2'].append(name)
        else:
            tiers['t3'].append(name)
    label = {'t1': '第一梯队 · 头部领跑', 't2': '第二梯队 · 强势跟进', 't3': '第三梯队 · 细分突围'}
    bands = ''
    for key in ('t1', 't2', 't3'):
        names = '、'.join(tiers[key]) if tiers[key] else '—'
        bands += ('<div class="pyr-tier ' + key + '"><span class="pyr-label">' + label[key]
                  + '</span><span class="pyr-items">' + html.escape(names) + '</span></div>')
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">竞争梯队金字塔</span>'
            '<span class="chart-legend">按市场份额/影响力（规模）划分</span></div>'
            '<div class="pyramid">' + bands + '</div></div>')


def render_ai_cards(items):
    cards = ""
    for title, body in items:
        cards += ('<div class="ai-card"><h4>' + html.escape(title) + '</h4><p>' + html.escape(body) + '</p></div>')
    return '<div class="ai-grid">' + cards + '</div>'


def render_growth(items):
    chips = ""
    for _, body in items:
        for m in re.findall(r'\d+(?:\.\d+)?\s*(?:万|亿|%|次|月|万次|万月|万+)', body):
            chips += '<span class="chip">' + html.escape(m) + '</span>'
    chip_html = ('<div class="chips">' + chips + '</div>') if chips else ''
    cards = ""
    for title, body in items:
        cards += ('<div class="growth-card"><h4>' + html.escape(title) + '</h4><p>' + html.escape(body) + '</p></div>')
    return chip_html + '<div class="growth-grid">' + cards + '</div>'


def render_swot(header, rows):
    label = {'优势': 's', '劣势': 'w', '机会': 'o', '威胁': 't'}
    cells = ""
    for r in rows:
        if len(r) < 3:
            continue
        dim = r[0]
        cls = label.get(dim, 's')
        cells += ('<div class="swot-cell ' + cls + '"><h4>' + html.escape(clean(dim)) + '</h4>'
                  + '<p><b>' + html.escape(clean(r[1])) + '</b>　' + html.escape(clean(r[2])) + '</p></div>')
    return '<div class="swot-grid">' + cells + '</div>'


def render_table(header, rows):
    th = "".join("<th>" + html.escape(clean(c)) + "</th>" for c in header)
    trs = "".join("<tr>" + "".join("<td>" + html.escape(clean(c)) + "</td>" for c in r) + "</tr>" for r in rows)
    return '<table class="tbl"><thead><tr>' + th + '</tr></thead><tbody>' + trs + '</tbody></table>'


def render_summary(items):
    rows = []
    for s in items:
        s = clean(s)
        label, body = split_kv(s)
        if label and body:
            rows.append('<div class="sum-row insight"><div class="sum-keyword">' + html.escape(label)
                        + '</div><div class="sum-body">' + html.escape(body) + '</div></div>')
        else:
            rows.append('<div class="sum-row insight"><div class="sum-body">' + html.escape(s) + '</div></div>')
    return '<div class="sum-list">' + "".join(rows) + '</div>'


def render_sentiment(items):
    """items: (kind, product, text)"""
    pos = sum(1 for k, _, _ in items if k == "正面")
    neg = sum(1 for k, _, _ in items if k == "负面")
    tot = pos + neg
    pw = 0 if tot == 0 else round(pos / tot * 100)
    nw = 0 if tot == 0 else round(neg / tot * 100)
    cards = ""
    for k, prod, t in items:
        cls = "pos" if k == "正面" else "neg"
        tag = k + ("（" + prod + "）" if prod else "")
        cards += '<div class="quote ' + cls + '"><span class="qtag">' + html.escape(tag) + '</span>' + html.escape(t) + '</div>'
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">用户口碑</span>'
            '<span class="chart-legend">样本 ' + str(tot) + ' · 正面 ' + str(pw) + '%</span></div>'
            '<div class="sent-bar"><div class="sent-pos" style="width:' + str(pw) + '%"></div>'
            '<div class="sent-neg" style="width:' + str(nw) + '%"></div></div>'
            '<div class="quote-list">' + cards + '</div></div>')


def render_priority(must, should, could):
    def col(title, items, cls):
        lis = "".join("<li>" + html.escape(x) + "</li>" for x in items)
        return '<div class="pri-col ' + cls + '"><div class="pri-h">' + title + '</div><ul>' + lis + '</ul></div>'
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">行动建议 · 优先级看板</span></div>'
            '<div class="pri-row">' + col("Must 必做", must, "m") + col("Should 应做", should, "s")
            + col("Could 可做", could, "c") + '</div></div>')


def render_source_inline(rows):
    links = ""
    for r in rows:
        if len(r) < 2:
            continue
        nm = clean(r[0]); lk = r[-1].strip()
        if lk.startswith("http"):
            links += '<a href="' + lk + '" target="_blank" rel="noopener">' + html.escape(nm) + '</a>'
        else:
            links += '<span>' + html.escape(nm) + '</span>'
    return '<div class="src-inline">' + links + '</div>'


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
.chart-card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px 26px;margin:22px 0;}
.chart-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px;}
.chart-title{font-size:16px;font-weight:600;color:var(--ink);}
.chart-legend{font-size:11px;color:var(--muted);}
.echart{width:100%;height:420px;}
.tl-list{display:flex;flex-direction:column;gap:0;margin:14px 0;border-left:2px solid var(--line);padding-left:0;}
.tl-item{display:flex;gap:16px;padding:10px 0 10px 18px;position:relative;}
.tl-item::before{content:"";position:absolute;left:-7px;top:16px;width:12px;height:12px;border-radius:50%;background:var(--brand);border:2px solid #fff;}
.tl-date{font-size:13px;font-weight:700;color:var(--brand);min-width:96px;flex-shrink:0;}
.tl-text{font-size:13px;color:var(--ink);line-height:1.6;}
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
.pyramid{display:flex;flex-direction:column;align-items:center;gap:0;margin:6px 0 2px;}
.pyr-tier{display:flex;align-items:center;justify-content:center;gap:14px;color:#fff;font-size:13px;padding:14px 0;}
.pyr-tier.t1{width:70%;background:linear-gradient(90deg,#F59E0B,#F97316);clip-path:polygon(14% 0,86% 0,100% 100%,0 100%);}
.pyr-tier.t2{width:85%;background:linear-gradient(90deg,#FBBF24,#F59E0B);clip-path:polygon(9% 0,91% 0,100% 100%,0 100%);}
.pyr-tier.t3{width:100%;background:linear-gradient(90deg,#FCD34D,#FBBF24);clip-path:polygon(5% 0,95% 0,100% 100%,0 100%);}
.pyr-label{font-weight:700;} .pyr-items{opacity:.95;}
.ai-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin:16px 0;}
.ai-card{background:var(--bg);border-radius:14px;padding:16px 18px;border-left:4px solid var(--brand);}
.ai-card h4{margin:0 0 8px;font-size:15px;color:var(--ink);} .ai-card p{margin:0;font-size:13px;color:var(--muted);line-height:1.7;}
.growth-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:6px 0;}
.growth-card{background:var(--bg);border-radius:12px;padding:14px 16px;}
.growth-card h4{margin:0 0 6px;font-size:14px;color:var(--brand);} .growth-card p{margin:0;font-size:13px;color:var(--ink);line-height:1.6;}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 4px;}
.chip{background:var(--brand-ghost);color:var(--brand);border-radius:20px;padding:4px 12px;font-size:12px;font-weight:600;}
.comp-graph{width:100%;height:360px;}
.swot-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:14px 0;}
.swot-cell{border-radius:12px;padding:14px 16px;}
.swot-cell h4{margin:0 0 6px;font-size:14px;}
.swot-cell p{margin:0;font-size:13px;color:var(--ink);line-height:1.6;}
.swot-cell.s{background:#FFF3D9;} .swot-cell.s h4{color:var(--brand);}
.swot-cell.w{background:#FDE8E8;} .swot-cell.w h4{color:var(--red);}
.swot-cell.o{background:#E7F7EF;} .swot-cell.o h4{color:var(--green);}
.swot-cell.t{background:#EFEAFB;} .swot-cell.t h4{color:#8B5CF6;}
.src-inline{display:flex;flex-wrap:wrap;gap:8px 20px;margin-top:8px;font-size:13px;line-height:1.9;}
.src-inline a{color:var(--brand);text-decoration:none;}
.src-inline a:hover{text-decoration:underline;}
.src-inline span{color:var(--muted);}
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
  .ai-grid{grid-template-columns:1fr;}
  .growth-grid{grid-template-columns:1fr;}
  .swot-grid{grid-template-columns:1fr;}
  .tags{display:none;}
}
"""


def parse_sections(lines):
    """返回 [(title, level, body_lines)]，标题按出现顺序。"""
    secs = []
    cur = None
    buf = []
    for ln in lines:
        m = re.match(r"^(#{1,3})\s+(.*)$", ln)
        if m:
            if cur is not None:
                secs.append(cur)
            cur = {"title": m.group(2).strip(), "level": len(m.group(1)), "body": []}
        else:
            if cur is not None:
                cur["body"].append(ln)
    if cur is not None:
        secs.append(cur)
    return secs


def render_section(sec, mid_state, market_map, idx):
    title = sec["title"]
    body = sec["body"]
    tables = parse_tables(body)
    table_at = {t[0]: t for t in tables}
    parts = []
    sentiment = []; timeline = []; priority = {"must": [], "should": [], "could": []}
    ai_cards = []; growth = []
    i = 0; n = len(body)
    while i < n:
        line = body[i]
        if i in table_at:
            _, header, rows = table_at[i]
            kind = classify_table(header, rows)
            if kind == 'matrix':
                mid_state[0] += 1
                parts.append(render_score_matrix(mid_state[0], header, rows))
            elif kind == 'scatter':
                mid_state[0] += 1
                parts.append(render_scatter(mid_state[0], header, rows, False))
            elif kind == 'funnel':
                mid_state[0] += 1
                parts.append(render_funnel(mid_state[0], header, rows))
            elif kind == 'source':
                parts.append(render_source_inline(rows))
            elif title == 'SWOT':
                parts.append(render_swot(header, rows))
            else:
                parts.append(render_table(header, rows))
            i = table_at[i][0] + 1
            while i < n and body[i].lstrip().startswith('|'):
                i += 1
            continue

        if line.strip().startswith('-'):
            bl = clean(line)
            if title == '用户口碑':
                mm = re.match(r'^(正面|负面)[（(]?([^）)]*)[）)]?[：:]\s*(.*)$', bl)
                if mm:
                    sentiment.append((mm.group(1), mm.group(2).strip(), mm.group(3).strip()))
            elif title == '时间线':
                mm = re.match(r'^([\d]{4}[\d\-年/]*)\s*[：:]\s*(.*)$', bl)
                if mm:
                    timeline.append((mm.group(1), mm.group(2).strip()))
            elif title == '行动建议':
                mm = re.match(r'^(Must|Should|Could)\s*[：:]\s*(.*)$', bl)
                if mm:
                    priority[mm.group(1).lower()].append(mm.group(2).strip())
            elif title == 'AI 能力':
                t, b = split_kv(bl)
                if t:
                    ai_cards.append((t, b))
                else:
                    ai_cards.append((clean(line), ''))
            elif title == '增长':
                t, b = split_kv(bl)
                growth.append((t, b if b else bl))
            else:
                # 普通列表项
                parts.append('<p>' + html.escape(bl) + '</p>')
            i += 1
            continue

        if line.strip() and not line.lstrip().startswith('#'):
            parts.append('<p>' + html.escape(clean(line)) + '</p>')
        i += 1

    # 章节专属组装
    if title == '执行摘要':
        # 收集本段所有列表项作为摘要
        summary_items = []
        for ln in body:
            if ln.strip().startswith('-'):
                summary_items.append(ln)
        if summary_items:
            parts = [render_summary(summary_items)]
    elif title == '用户口碑' and sentiment:
        parts = [render_sentiment(sentiment)]
    elif title == '时间线' and timeline:
        items = "".join(
            '<div class="tl-item"><span class="tl-date">' + html.escape(d) + '</span>'
            + '<span class="tl-text">' + html.escape(t) + '</span></div>'
            for d, t in timeline)
        parts = ['<div class="tl-list">' + items + '</div>']
    elif title == '市场概览' and market_map:
        parts.append(render_pyramid(market_map))
    elif title == 'AI 能力' and ai_cards:
        parts = [render_ai_cards(ai_cards)]
    elif title == '增长' and growth:
        parts = [render_growth(growth)]
    elif title == '行动建议' and (priority["must"] or priority["should"] or priority["could"]):
        parts = [render_priority(priority["must"], priority["should"], priority["could"])]
    elif title == '竞争格局':
        if market_map and market_map[2]:
            names = [r[0] for r in market_map[2] if r]
            center = names[0]
            others = names[1:]
            mid_state[0] += 1
            parts.append(render_competition_graph(mid_state[0], center, others))

    return ('<section id="' + section_id(idx) + '"><h2>' + html.escape(title) + '</h2>'
            + "".join(parts) + '</section>')


def section_id(idx):
    return "sec-" + str(idx)


def render(input_path, output_path):
    """把约定写法 Markdown 渲染为自包含 ECharts HTML（可被 import 调用）。"""
    with open(input_path, encoding="utf-8") as f:
        text = f.read()
    # 兼容全角分隔符
    text = text.replace('｜', '|')
    lines = text.split("\n")

    # 顶层标题与假设
    title = "AI PM 研究报告"
    assumption = {}
    sections = parse_sections(lines)
    for s in sections:
        if s["level"] == 1:
            title = s["title"]

    mid_state = [0]
    # 预扫描市场地图（供金字塔/竞争格局复用）
    market_map = None
    for s in sections:
        for t in parse_tables(s["body"]):
            if classify_table(t[1], t[2]) == 'scatter':
                market_map = t

    body_parts = []
    sec_idx = 0
    nav_items = ""
    for s in sections:
        if s["level"] == 1:
            continue
        if s["level"] == 2:
            sec_idx += 1
            nav_items += '<li><a href="#' + section_id(sec_idx) + '">' + html.escape(s["title"]) + '</a></li>'
        if s["title"] in ('本次假设', '研究简报'):
            for ln in s["body"]:
                if ln.strip().startswith('-'):
                    bl = clean(ln)
                    if '：' in bl or ':' in bl:
                        k, v = re.split(r'[：:]', bl, maxsplit=1)
                        assumption[k.strip()] = v.strip()
                    elif bl:
                        assumption.setdefault('备注', bl)
            continue
        body_parts.append(render_section(s, mid_state, market_map, sec_idx))

    # 顶部标签
    tag_html = ""
    for k, v in assumption.items():
        if k == '备注':
            continue
        tag_html += '<span class="tag"><b>' + html.escape(k) + '</b>：' + html.escape(v) + '</span>'
    if not tag_html:
        tag_html = '<span class="tag"><b>模式</b>：默认</span>'

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
        '<script>var REG=[];window.addEventListener("load",function(){REG.forEach(function(c){c.resize();});});'
        'window.addEventListener("resize",function(){REG.forEach(function(c){c.resize();});});'
        'document.querySelectorAll(".nav-list a").forEach(function(a){'
        'a.addEventListener("click",function(e){document.querySelectorAll(".nav-list a").forEach(function(x){x.classList.remove("active");});'
        'this.classList.add("active");});});'
        '</script>'
        '</body></html>')
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return output_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    out = render(args.input, args.output)
    size = len(open(out, encoding="utf-8").read())
    print("OK -> " + out + " (" + str(size) + " bytes)")


if __name__ == "__main__":
    main()
