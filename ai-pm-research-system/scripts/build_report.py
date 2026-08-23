#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIPM·瞭望台 · 可视化渲染器
约定写法（Markdown）→ 自包含 HTML（ECharts CDN）。
支持：核心结论 KPI / 关键洞察 / 市场地图 / 能力雷达图 / 维度热力矩阵 /
      功能点阵图 / 机会卡片 / 时间线 / 用户口碑 / 优先级看板 / 来源。

设计语言（按 2025-08-23 设计评审迭代）：
  - 信息密度收敛：每张图只讲一个问题，默认 Top-3/Top-4
  - 细左侧导航 Rail + 大内容区，减少导航占用
  - 浅灰背景 #F7F7FA，主色 indigo #6366f1，强调浅紫 #CCCEFF
  - 少边框、少阴影、大留白、强字体层级
"""
import sys, re, json, html, argparse, datetime

PALETTE = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#0ea5e9", "#ec4899", "#14b8a6", "#f97316"]

# 需要在 json.dumps 之后以原始 JS 注入的函数（占位 token -> 真实函数源码）
SCATTER_TOOLTIP = "function(p){return p.data.name+'<br/>X：'+p.data.value[0]+'　Y：'+p.data.value[1];}"
SCATTER_LABEL = "function(p){return p.data.name;}"

# 定性评级 → 数值（用于功能点阵图）
QUALITY_MAP = {
    "强": 3, "是": 3, "有": 3, "独立": 3, "好": 3, "高": 3, "快": 3,
    "中": 2, "部分": 2, "有限": 2, "一般": 2, "平均": 2,
    "弱": 1, "否": 1, "无": 1, "差": 1, "低": 1, "慢": 1,
}


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
    # 市场/机会地图：必须含 X / Y 坐标轴列
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


def select_top_objects(matrix, objects, n=4):
    """保留第一个对象（主体）+ 综合评分最高的 n-1 个对象。
    matrix: list[list[float|None]]，与 objects 同序。
    """
    if len(objects) <= n:
        return list(range(len(objects)))
    avgs = []
    for idx, vals in enumerate(matrix):
        clean = [v for v in vals if v is not None]
        avgs.append((sum(clean) / len(clean) if clean else 0, idx))
    # 第一个固定为主体
    rest = [x for _, x in sorted(avgs[1:], key=lambda x: -x[0])[:n-1]]
    return [0] + sorted(rest)


def render_score_matrix(mid, header, rows):
    dims = header[1:]
    objects = [r[0] for r in rows]
    matrix = []
    for r in rows:
        vals = [float(v) if re.match(r'^\d+(\.\d+)?$', v) else None for v in r[1:]]
        matrix.append(vals)

    # 雷达只保留主体 + Top-3，避免 8 条线重叠成糊
    radar_idx = select_top_objects(matrix, objects, n=4)
    radar_dims = dims
    radar_objects = [objects[i] for i in radar_idx]
    indicators = [{"name": d, "max": 5} for d in radar_dims]
    radar_data = []
    for rank, oi in enumerate(radar_idx):
        obj = objects[oi]
        c = PALETTE[rank % len(PALETTE)]
        vals = matrix[oi]
        d = {"name": obj, "value": vals,
             "lineStyle": {"color": c, "width": rank == 0 and 3 or 2.2},
             "itemStyle": {"color": c}}
        # 仅主体填充淡色，竞品仅描边，避免中心阴影反复叠加变深
        if rank == 0:
            d["areaStyle"] = {"color": c, "opacity": 0.12}
        radar_data.append(d)

    radar_opt = {
        "backgroundColor": "transparent",
        "textStyle": {"color": "#6c6c88"},
        "tooltip": {"textStyle": {"color": "#2e2e38"}},
        "legend": {"bottom": 0, "data": radar_objects, "textStyle": {"color": "#2e2e38", "fontSize": 12},
                   "itemGap": 16, "icon": "roundRect"},
        "radar": {
            "indicator": indicators, "radius": "64%", "center": ["50%", "44%"],
            "axisName": {"color": "#6c6c88", "fontSize": 11},
            "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            "axisLine": {"lineStyle": {"color": "#e2e8f0"}},
            "splitArea": {"areaStyle": {"color": ["#f7f7fa", "#ffffff"]}}
        },
        "series": [{"type": "radar", "data": radar_data, "symbolSize": 5}]
    }

    # 热力矩阵保留全部对象，但用更淡的色阶和更干净的格子
    heat = [[xi, yi, matrix[xi][yi]] for yi in range(len(dims)) for xi in range(len(objects))]
    heat_opt = {
        "backgroundColor": "transparent",
        "tooltip": {"position": "top", "textStyle": {"color": "#2e2e38"}},
        "grid": {"height": "68%", "top": "4%", "left": "2%", "right": "4%"},
        "xAxis": {"type": "category", "data": objects, "axisLabel": {"color": "#2e2e38", "fontSize": 11},
                  "axisLine": {"show": False}, "axisTick": {"show": False},
                  "splitArea": {"show": True, "areaStyle": {"color": ["#ffffff", "#f7f7fa"]}}},
        "yAxis": {"type": "category", "data": dims, "axisLabel": {"color": "#6c6c88", "fontSize": 11},
                  "axisLine": {"show": False}, "axisTick": {"show": False},
                  "splitArea": {"show": True, "areaStyle": {"color": ["#ffffff", "#f7f7fa"]}}},
        "visualMap": {"min": 1, "max": 5, "calculable": False, "show": False,
                      "inRange": {"color": ["#f7f7fa", "#ccceff", "#6366f1"]}},
        "series": [{"type": "heatmap", "data": heat, "label": {"show": True, "color": "#2e2e38", "fontSize": 11},
                    "itemStyle": {"borderColor": "#ffffff", "borderWidth": 2},
                    "emphasis": {"itemStyle": {"shadowBlur": 8, "shadowColor": "rgba(99,102,241,.3)"}}}]
    }
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">核心能力对比（Top 4）</span>'
            '<span class="chart-legend">评分口径：5=领先，3=平均，1=基本不覆盖</span></div>'
            '<div id="radar_' + str(mid) + '" class="echart"></div></div>\n'
            '<div class="chart-card"><div class="chart-header"><span class="chart-title">维度热力矩阵</span></div>'
            '<div id="heat_' + str(mid) + '" class="echart" style="height:360px"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("radar_' + str(mid) + '"));'
            'c.setOption(' + json.dumps(radar_opt, ensure_ascii=False) + ');REG.push(c);'
            'var h=echarts.init(document.getElementById("heat_' + str(mid) + '"));'
            'h.setOption(' + json.dumps(heat_opt, ensure_ascii=False) + ');REG.push(h);});</script>')


def render_scatter(mid, header, rows, is_opp):
    data = []
    for r in rows:
        if len(r) < 4: continue
        try:
            x = float(r[1]); y = float(r[2]); s = float(r[3])
        except Exception:
            continue
        data.append({"name": r[0], "value": [x, y, s]})
    # 限制气泡数量，避免过密
    data = sorted(data, key=lambda d: -d["value"][2])[:6]
    title = "机会地图（空白区）" if is_opp else "市场格局地图"
    color = "#f59e0b" if is_opp else "#6366f1"
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "__SCATTER_TOOLTIP__"},
        "grid": {"left": "10%", "right": "10%", "top": "10%", "bottom": "16%"},
        "xAxis": {"name": "X · 专业 ←→ 大众", "nameTextStyle": {"color": "#9ca3af", "fontSize": 11},
                  "min": 0, "max": 10, "axisLabel": {"show": False},
                  "axisLine": {"lineStyle": {"color": "#e2e8f0"}},
                  "splitLine": {"lineStyle": {"color": "#f7f7fa", "type": "dashed"}}},
        "yAxis": {"name": "Y · 模型能力 ←→ 生态", "nameTextStyle": {"color": "#9ca3af", "fontSize": 11},
                  "min": 0, "max": 10, "axisLabel": {"show": False},
                  "axisLine": {"lineStyle": {"color": "#e2e8f0"}},
                  "splitLine": {"lineStyle": {"color": "#f7f7fa", "type": "dashed"}}},
        "series": [{"type": "scatter", "data": data,
                    "symbolSize": "function(d){return 32+d[2]*12;}",
                    "itemStyle": {"color": color, "opacity": 0.18, "borderColor": color, "borderWidth": 2},
                    "label": {"show": True, "formatter": "__SCATTER_LABEL__", "position": "top",
                              "color": "#2e2e38", "fontSize": 12, "fontWeight": 600}}]
    }
    opt_json = json.dumps(opt, ensure_ascii=False)
    opt_json = opt_json.replace('"__SCATTER_TOOLTIP__"', SCATTER_TOOLTIP).replace('"__SCATTER_LABEL__"', SCATTER_LABEL)
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">' + title + '</span>'
            '<span class="chart-legend">气泡大小 = 综合影响力</span></div>'
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
        "color": ["#6366f1", "#8b5cf6", "#0ea5e9", "#22c55e", "#f59e0b", "#ef4444"],
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
        "tooltip": {"trigger": "axis", "textStyle": {"color": "#2e2e38"}},
        "grid": {"left": "8%", "right": "6%", "top": "14%", "bottom": "10%"},
        "xAxis": {"type": "category", "data": names, "axisLabel": {"color": "#6c6c88"},
                  "axisLine": {"lineStyle": {"color": "#e2e8f0"}}, "axisTick": {"show": False}},
        "yAxis": {"type": "value", "show": False},
        "series": [{"type": "line", "data": vals, "smooth": True, "symbol": "circle", "symbolSize": 8,
                    "lineStyle": {"color": "#6366f1", "width": 3},
                    "itemStyle": {"color": "#6366f1", "borderColor": "#fff", "borderWidth": 2},
                    "areaStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                              "colorStops": [{"offset": 0, "color": "rgba(99,102,241,.22)"},
                                                               {"offset": 1, "color": "rgba(99,102,241,.02)"}]}},
                    "label": {"show": True, "position": "top", "color": "#2e2e38", "formatter": "{c}"}}]
    }
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">时间线</span></div>'
            '<div id="tl_' + str(mid) + '" class="echart" style="height:220px"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("tl_' + str(mid)
            + '"));c.setOption(' + json.dumps(opt, ensure_ascii=False) + ');REG.push(c);});</script>')


def _quality_score(v):
    """把「强(云端)」这类带备注的值也映射到 1-3。"""
    v = str(v)
    for k, s in [("强", 3), ("是", 3), ("高", 3), ("快", 3), ("中", 2), ("部分", 2), ("弱", 1), ("否", 1), ("无", 1)]:
        if k in v:
            return s
    return 0


def render_dot_matrix(header, rows):
    """功能/特性定性表 → 点阵图。保留主体 + Top-3 竞品。"""
    objects = header[1:]
    features = [r[0] for r in rows]
    scores = []
    for r in rows:
        row_scores = [_quality_score(v) for v in r[1:]]
        scores.append(row_scores)

    # 主体固定为第一个对象，其余按平均分取 Top-3
    obj_avgs = []
    for ci, obj in enumerate(objects):
        col = [scores[ri][ci] for ri in range(len(features))]
        col = [s for s in col if s > 0]
        obj_avgs.append((sum(col) / len(col) if col else 0, ci))
    chosen = [0] + [x for _, x in sorted(obj_avgs[1:], key=lambda x: -x[0])[:3]]
    chosen = sorted(chosen)

    rows_html = ""
    for ri, feat in enumerate(features):
        cells = '<td class="dm-feat">' + html.escape(feat) + '</td>'
        for ci in chosen:
            s = scores[ri][ci]
            cls = "s3" if s == 3 else ("s2" if s == 2 else ("s1" if s == 1 else "s0"))
            cells += '<td class="dm-cell"><span class="dm-dot ' + cls + '"></span></td>'
        rows_html += '<tr>' + cells + '</tr>'

    head_html = '<tr><th class="dm-feat"></th>' + "".join('<th>' + html.escape(objects[ci]) + '</th>' for ci in chosen) + '</tr>'
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">核心功能对比（Top 4）</span>'
            '<span class="chart-legend">● 强　● 中　● 弱</span></div>'
            '<table class="dot-matrix">' + head_html + rows_html + '</table></div>')


def render_opportunity_cards(rows):
    """机会点表格 → 3 张 icon 卡片。"""
    cards = ""
    for i, r in enumerate(rows[:3]):
        name = r[0] if r else ""
        scale = r[3] if len(r) > 3 else ""
        icon = name[0] if name else "?"
        c = PALETTE[i % len(PALETTE)]
        cards += ('<div class="opp-card">'
                  '<div class="opp-icon" style="background:' + c + '">' + html.escape(icon) + '</div>'
                  '<div class="opp-title">' + html.escape(name) + '</div>'
                  '<div class="opp-meta">潜力 ' + html.escape(scale) + '/5</div></div>')
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">机会点（Top 3）</span></div>'
            '<div class="opp-row">' + cards + '</div></div>')


def parse_kpi(text):
    """把摘要项解析成 KPI 卡或洞察卡。"""
    text = text.strip()
    # 数字/符号开头：$2B+ / 50%+ / #1 / 200% / 1.2x
    m = re.match(r'^([\$¥€]?\s*[\d\.,]+\s*[%x倍万亿KMB+\-]*|[\#]\s*\d+|\d+\s*[%x倍万亿KMB+\-]*)\s+(.+)$', text)
    if m:
        return ('metric', m.group(1).strip(), m.group(2).strip(), '')
    # 标签：内容 模式
    m = re.match(r'^([^：]{1,10})[：:]\s*(.+)$', text)
    if m:
        return ('insight', '', m.group(1).strip(), m.group(2).strip())
    return ('insight', '', text, '')


def render_summary(items):
    """核心结论：前 4 项为 KPI 大卡，其余为关键洞察面板。"""
    kpi_items = items[:4]
    insight_items = items[4:]
    kpi_html = ""
    for s in kpi_items:
        t, big, label, note = parse_kpi(s)
        if t == 'metric':
            kpi_html += ('<div class="kpi-card">'
                         '<div class="kpi-big">' + html.escape(big) + '</div>'
                         '<div class="kpi-label">' + html.escape(label) + '</div></div>')
        else:
            # 非数字也渲染成大标签卡
            kpi_html += ('<div class="kpi-card insight-kpi">'
                         '<div class="kpi-big">' + html.escape(label or s[:12]) + '</div>'
                         '<div class="kpi-label">' + html.escape(note or '') + '</div></div>')
    out = '<div class="kpi-grid">' + kpi_html + '</div>'
    if insight_items:
        lis = "".join('<li>' + html.escape(s.lstrip("-").strip()) + '</li>' for s in insight_items)
        out += '<div class="insight-panel"><div class="insight-h">关键洞察</div><ul>' + lis + '</ul></div>'
    return out


def render_insights(items):
    """关键洞察面板。"""
    if not items:
        return ""
    lis = "".join('<li>' + html.escape(s.lstrip("-").strip()) + '</li>' for s in items)
    return '<div class="insight-panel"><div class="insight-h">关键洞察</div><ul>' + lis + '</ul></div>'


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
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">优先级看板</span></div>'
            '<div class="pri-row">' + col("Must 必做", must, "m") + col("Should 应做", should, "s")
            + col("Could 可做", could, "c") + '</div></div>')


CSS = """
:root{
  --bg:#f7f7fa;
  --card:#ffffff;
  --ink:#2e2e38;
  --muted:#6c6c88;
  --line:#e8e8f0;
  --brand:#6366f1;
  --brand-light:#ccceff;
  --brand-ghost:#f2f3ff;
  --green:#22c55e;
  --amber:#f59e0b;
  --red:#ef4444;
  --sidebar:#2e2e38;
  --sidebar-text:#b8bbd4;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.65;font-size:14px;}
.app{display:flex;min-height:100vh;}
.sidebar{width:64px;background:var(--sidebar);color:var(--sidebar-text);position:fixed;left:0;top:0;bottom:0;overflow:auto;padding:20px 8px;z-index:20;display:flex;flex-direction:column;align-items:center;}
.brand{font-size:12px;font-weight:700;color:#fff;letter-spacing:2px;writing-mode:vertical-rl;text-orientation:mixed;margin-bottom:24px;}
.nav-list{list-style:none;margin:0;padding:0;width:100%;}
.nav-list li{margin:6px 0;text-align:center;}
.nav-list a{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:10px;color:var(--sidebar-text);text-decoration:none;font-size:13px;font-weight:600;transition:.15s;}
.nav-list a:hover,.nav-list a.active{background:rgba(255,255,255,.1);color:#fff;}
.main{margin-left:64px;flex:1;padding:40px 56px 100px;max-width:1200px;}
.top-header{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;margin-bottom:24px;}
.top-header h1{margin:0;font-size:36px;font-weight:700;line-height:1.2;letter-spacing:.5px;color:var(--ink);}
.top-meta{text-align:right;font-size:13px;color:var(--muted);line-height:1.6;}
.top-meta .brand-line{font-weight:600;color:var(--ink);}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}
.tag{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid var(--line);border-radius:20px;padding:5px 12px;font-size:12px;color:var(--muted);}
.tag b{color:var(--ink);font-weight:600;}
section{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px 32px;margin-bottom:20px;width:100%;}
section h2{margin:0 0 18px;font-size:20px;font-weight:600;line-height:1.4;color:var(--ink);}
section h3{font-size:15px;font-weight:600;color:var(--ink);margin:18px 0 10px;}
section p{margin:8px 0;font-size:14px;color:var(--ink);line-height:1.75;}
section ul,section ol{margin:10px 0;padding-left:22px;color:var(--ink);font-size:14px;line-height:1.75;}
section li{margin:5px 0;}
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0 16px;}
.kpi-card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;min-height:110px;display:flex;flex-direction:column;justify-content:center;}
.kpi-card:nth-child(1){background:linear-gradient(135deg,var(--brand-ghost),#fff);border-color:var(--brand-light);}
.kpi-big{font-size:30px;font-weight:700;color:var(--brand);line-height:1.15;margin-bottom:6px;}
.kpi-card.insight-kpi .kpi-big{font-size:18px;line-height:1.3;}
.kpi-label{font-size:12px;color:var(--ink);font-weight:500;line-height:1.5;}
.insight-panel{background:var(--bg);border-left:3px solid var(--brand-light);border-radius:0 12px 12px 0;padding:14px 18px;margin:10px 0 6px;}
.insight-h{font-size:13px;font-weight:600;color:var(--brand);margin-bottom:8px;}
.insight-panel ul{margin:0;padding-left:18px;font-size:13px;color:var(--muted);line-height:1.8;}
.insight-panel li{margin:4px 0;}
.chart-card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px 26px;margin:20px 0;}
.chart-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px;}
.chart-title{font-size:16px;font-weight:600;color:var(--ink);}
.chart-legend{font-size:11px;color:var(--muted);}
.echart{width:100%;height:420px;}
.pri-row{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.pri-col{background:var(--bg);border-radius:14px;padding:16px;}
.pri-col.m{border-left:4px solid var(--red);} .pri-col.s{border-left:4px solid var(--amber);} .pri-col.c{border-left:4px solid var(--green);}
.pri-h{font-weight:700;font-size:14px;margin-bottom:10px;color:var(--ink);} .pri-col ul{margin:0;padding-left:18px;font-size:13px;color:var(--muted);line-height:1.7;}
.sent-bar{display:flex;height:12px;border-radius:6px;overflow:hidden;margin-bottom:12px;background:var(--line);}
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
.tbl tbody tr:hover{background:rgba(99,102,241,.03);}
.tbl tr:last-child td{border-bottom:none;}
.dot-matrix{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;margin:6px 0 0;}
.dot-matrix th,.dot-matrix td{padding:10px 8px;text-align:center;border-bottom:1px solid var(--line);}
.dot-matrix th{font-weight:600;color:var(--muted);font-size:12px;}
.dot-matrix td.dm-feat{text-align:left;color:var(--ink);font-weight:500;}
.dm-dot{display:inline-block;width:14px;height:14px;border-radius:50%;}
.dm-dot.s3{background:var(--brand);}
.dm-dot.s2{background:var(--brand-light);}
.dm-dot.s1{background:#e2e8f0;}
.dm-dot.s0{background:transparent;border:1px dashed #e2e8f0;}
.opp-row{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.opp-card{background:var(--bg);border-radius:14px;padding:18px;display:flex;flex-direction:column;gap:10px;}
.opp-icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;font-weight:700;}
.opp-title{font-size:14px;font-weight:600;color:var(--ink);line-height:1.4;}
.opp-meta{font-size:12px;color:var(--muted);}
@media(max-width:900px){
  .sidebar{display:none;}
  .main{margin-left:0;padding:24px;max-width:none;}
  .kpi-grid{grid-template-columns:repeat(2,1fr);}
  .opp-row,.pri-row{grid-template-columns:1fr;}
}
@media(max-width:640px){
  .kpi-grid{grid-template-columns:1fr;}
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
    summary_items = []; insight_items = []; priority = {"must": [], "should": [], "could": []}
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
            if htext in ("核心结论", "执行摘要"):
                body_parts.append(close_prev + '<section id="' + sid + '"><h2>核心结论</h2><div class="summary-grid" id="sum"></div></section>')
            elif htext == "关键洞察":
                body_parts.append(close_prev + '<section id="' + sid + '"><h2>关键洞察</h2><div id="insights"></div></section>')
            elif htext == "来源":
                body_parts.append(close_prev + '<section id="' + sid + '"><h2>来源</h2><div id="src"></div></section>')
            elif htext in ("用户口碑", "时间线"):
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
            # 机会点表格 → 卡片
            if cur_section == "机会点":
                body_parts.append(render_opportunity_cards(rows))
            # 市场/机会地图
            elif is_scatter(header, rows):
                mid += 1
                body_parts.append(render_scatter(mid, header, rows, "机会" in cur_section))
            elif is_score_matrix(header, rows):
                mid += 1
                body_parts.append(render_score_matrix(mid, header, rows))
            elif "功能" in cur_section or "矩阵" in cur_section:
                body_parts.append(render_dot_matrix(header, rows))
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
        if cur_section in ("核心结论", "执行摘要") and line.strip().startswith("-"):
            txt = line.strip().lstrip("-").strip()
            if txt: summary_items.append(txt)
            i += 1; continue
        if cur_section == "关键洞察" and line.strip().startswith("-"):
            txt = line.strip().lstrip("-").strip()
            if txt: insight_items.append(txt)
            i += 1; continue
        mm = re.match(r"^(Must|Should|Could)\s*[：:]\s*(.*)", line.strip())
        if mm:
            priority[mm.group(1).lower()].append(mm.group(2))
            i += 1; continue
        if line.strip() and not line.lstrip().startswith("#"):
            body_parts.append("<p>" + html.escape(line.strip()) + "</p>")
        i += 1

    if open_section:
        body_parts.append("</section>")

    # 注入核心结论、洞察、口碑、时间线、来源
    if summary_items:
        body_parts = [p.replace('<div class="summary-grid" id="sum"></div>', render_summary(summary_items)) for p in body_parts]
    if insight_items:
        body_parts = [p.replace('<div id="insights"></div>', render_insights(insight_items)) for p in body_parts]
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
                cards += '<div class="src-card"><a href="' + lk + '" target="_blank" rel="noopener">' + html.escape(nm) + '</a></div>'
            else:
                cards += '<div class="src-card">' + html.escape(nm) + '：' + html.escape(lk) + '</div>'
        cards = '<div class="src-grid">' + cards + '</div>'
        body_parts = [p.replace('<div id="src"></div>', cards) for p in body_parts]

    # 构建导航（Rail 显示首字）
    nav_items = ""
    for sid, stitle in sections:
        label = html.escape(stitle[:1])
        nav_items += '<li><a href="#' + sid + '" title="' + html.escape(stitle) + '">' + label + '</a></li>'

    # 构建顶部标签
    tag_html = ""
    for k, v in assumption.items():
        if k == "备注":
            continue
        tag_html += '<span class="tag"><b>' + html.escape(k) + '</b>：' + html.escape(v) + '</span>'
    if not tag_html:
        tag_html = '<span class="tag"><b>模式</b>：默认</span>'

    today = datetime.datetime.now().strftime("%Y 年 %-m 月")

    html_doc = ('<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + html.escape(title) + '</title>'
        '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>'
        '<style>' + CSS + '</style></head><body>'
        '<div class="app">'
        '<aside class="sidebar">'
        '<div class="brand">瞭望台</div>'
        '<ul class="nav-list">' + nav_items + '</ul>'
        '</aside>'
        '<main class="main">'
        '<header class="top-header">'
        '<h1>' + html.escape(title) + '</h1>'
        '<div class="top-meta"><div class="brand-line">AIPM·竞品研究院</div><div>' + today + '</div></div>'
        '</header>'
        '<div class="tags">' + tag_html + '</div>'
        + "".join(body_parts) +
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
