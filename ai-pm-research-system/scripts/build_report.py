#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI PM Research System · 可视化渲染器
约定写法（Markdown）→ 自包含 HTML（ECharts CDN）。
支持：能力雷达图 + 维度热力矩阵 / 市场地图·机会地图(scatter) / 时间线 / 用户口碑 / 优先级看板 / 摘要卡 / 来源卡。
仅标准库；输出文件内联数据，加载 ECharts 即可渲染。

设计语言（与首个好看的版本保持一致）：
  - 主色 indigo #6366f1，辅色青/琥珀/红/紫，统一高级感
  - 圆角 16px 卡片 + 极淡阴影 + 渐变摘要卡
  - ECharts 统一透明底、柔和坐标轴、精致 tooltip，避免默认“土味”

注意：ECharts option 中若含 JS 函数（如 formatter），不能用 json.dumps 包裹成字符串，
先放占位 token，json.dumps 后做字符串替换注入原始函数。
"""
import sys, re, json, html, argparse

PALETTE = ["#6366f1", "#14b8a6", "#f59e0b", "#ef4444", "#8b5cf6", "#0ea5e9", "#ec4899"]

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
    if len(header) != 4: return False
    for r in rows:
        if len(r) < 4: continue
        if not re.match(r'^\d+(\.\d+)?$', r[1]) or not re.match(r'^\d+(\.\d+)?$', r[2]):
            return False
    return True


def render_score_matrix(mid, header, rows):
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
        radar_data.append({"name": obj, "value": matrix[oi],
                           "lineStyle": {"color": c, "width": 2},
                           "itemStyle": {"color": c},
                           "areaStyle": {"color": c, "opacity": 0.10}})
    radar_opt = {
        "backgroundColor": "transparent",
        "textStyle": {"color": "#64748b"},
        "tooltip": {},
        "legend": {"bottom": 0, "data": objects, "textStyle": {"color": "#475569"}},
        "radar": {
            "indicator": indicators, "radius": "66%", "center": ["50%", "48%"],
            "axisName": {"color": "#64748b", "fontSize": 12},
            "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            "axisLine": {"lineStyle": {"color": "#e2e8f0"}},
            "splitArea": {"areaStyle": {"color": ["#fbfcff", "#f4f6ff"]}}
        },
        "series": [{"type": "radar", "data": radar_data, "symbolSize": 5}]
    }
    heat = [[xi, yi, matrix[xi][yi]] for yi in range(len(dims)) for xi in range(len(objects))]
    heat_opt = {
        "backgroundColor": "transparent",
        "tooltip": {"position": "top", "textStyle": {"color": "#334155"}},
        "grid": {"height": "66%", "top": "8%", "left": "4%", "right": "4%"},
        "xAxis": {"type": "category", "data": objects, "axisLabel": {"color": "#475569"},
                  "axisLine": {"lineStyle": {"color": "#e2e8f0"}}, "axisTick": {"show": False},
                  "splitArea": {"show": True, "areaStyle": {"color": ["#fbfcff", "#f4f6ff"]}}},
        "yAxis": {"type": "category", "data": dims, "axisLabel": {"color": "#64748b"},
                  "axisLine": {"lineStyle": {"color": "#e2e8f0"}}, "axisTick": {"show": False},
                  "splitArea": {"show": True, "areaStyle": {"color": ["#fbfcff", "#f4f6ff"]}}},
        "visualMap": {"min": 1, "max": 5, "calculable": True, "orient": "horizontal",
                      "left": "center", "bottom": "0", "textStyle": {"color": "#94a3b8"},
                      "inRange": {"color": ["#eef2ff", "#a5b4fc", "#6366f1"]}},
        "series": [{"type": "heatmap", "data": heat, "label": {"show": True, "color": "#1e293b", "fontSize": 12},
                    "itemStyle": {"borderColor": "#fff", "borderWidth": 2},
                    "emphasis": {"itemStyle": {"shadowBlur": 8, "shadowColor": "rgba(99,102,241,.4)"}}}]
    }
    return ('<div class="chart-card"><div class="chart-title">能力雷达图 '
            '<span class="legend-note">评分口径：5=领先，3=平均，1=基本不覆盖</span></div>'
            '<div id="radar_' + str(mid) + '" class="echart"></div></div>\n'
            '<div class="chart-card"><div class="chart-title">维度热力矩阵</div>'
            '<div id="heat_' + str(mid) + '" class="echart"></div></div>\n'
            '<script>(function(){var c=echarts.init(document.getElementById("radar_' + str(mid) + '"));'
            'c.setOption(' + json.dumps(radar_opt, ensure_ascii=False) + ');REG.push(c);'
            'var h=echarts.init(document.getElementById("heat_' + str(mid) + '"));'
            'h.setOption(' + json.dumps(heat_opt, ensure_ascii=False) + ');REG.push(h);})();</script>')


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
    color = "#f59e0b" if is_opp else "#6366f1"
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "__SCATTER_TOOLTIP__"},
        "grid": {"left": "9%", "right": "9%", "top": "12%", "bottom": "14%"},
        "xAxis": {"name": "X · 专业 ←→ 大众", "nameTextStyle": {"color": "#94a3b8"},
                  "min": 0, "max": 10, "axisLabel": {"color": "#64748b"},
                  "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
                  "splitLine": {"lineStyle": {"color": "#eef2f7", "type": "dashed"}}},
        "yAxis": {"name": "Y · 模型能力 ←→ 生态", "nameTextStyle": {"color": "#94a3b8"},
                  "min": 0, "max": 10, "axisLabel": {"color": "#64748b"},
                  "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
                  "splitLine": {"lineStyle": {"color": "#eef2f7", "type": "dashed"}}},
        "series": [{"type": "scatter", "data": data, "symbolSize": "function(d){return 12+d[2]*6;}",
                    "itemStyle": {"color": color, "opacity": 0.78, "borderColor": "#fff", "borderWidth": 1.5},
                    "label": {"show": True, "formatter": "__SCATTER_LABEL__", "position": "top",
                              "color": "#475569", "fontSize": 12}}]
    }
    opt_json = json.dumps(opt, ensure_ascii=False)
    opt_json = opt_json.replace('"__SCATTER_TOOLTIP__"', SCATTER_TOOLTIP).replace('"__SCATTER_LABEL__"', SCATTER_LABEL)
    return ('<div class="chart-card"><div class="chart-title">' + title + '</div>'
            '<div id="scatter_' + str(mid) + '" class="echart"></div></div>\n'
            '<script>(function(){var c=echarts.init(document.getElementById("scatter_' + str(mid)
            + '"));c.setOption(' + opt_json + ');REG.push(c);})();</script>')


def render_timeline(mid, items):
    names = [d for d, _ in items]
    vals = [v for _, v in items]
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis", "textStyle": {"color": "#334155"}},
        "grid": {"left": "10%", "right": "6%", "top": "14%", "bottom": "10%"},
        "xAxis": {"type": "category", "data": names, "axisLabel": {"color": "#64748b"},
                  "axisLine": {"lineStyle": {"color": "#e2e8f0"}}, "axisTick": {"show": False}},
        "yAxis": {"type": "value", "show": False},
        "series": [{"type": "line", "data": vals, "smooth": True, "symbol": "circle", "symbolSize": 9,
                    "lineStyle": {"color": "#6366f1", "width": 3},
                    "itemStyle": {"color": "#6366f1"},
                    "areaStyle": {"color": "rgba(99,102,241,.08)"},
                    "label": {"show": True, "position": "top", "color": "#475569", "formatter": "{c}"}}]
    }
    return ('<div class="chart-card"><div class="chart-title">时间线</div>'
            '<div id="tl_' + str(mid) + '" class="echart" style="height:180px"></div></div>\n'
            '<script>(function(){var c=echarts.init(document.getElementById("tl_' + str(mid)
            + '"));c.setOption(' + json.dumps(opt, ensure_ascii=False) + ');REG.push(c);})();</script>')


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
    return ('<div class="chart-card"><div class="chart-title">用户口碑</div>'
            '<div class="sent-bar"><div class="sent-pos" style="width:' + str(pw) + '%"></div>'
            '<div class="sent-neg" style="width:' + str(nw) + '%"></div></div>'
            '<div class="sent-meta">正面 ' + str(pw) + '% · 负面 ' + str(nw) + '%（样本 ' + str(tot) + '）</div>'
            '<div class="quote-list">' + cards + '</div></div>')


def render_priority(must, should, could):
    def col(title, items, cls):
        lis = "".join("<li>" + html.escape(x) + "</li>" for x in items)
        return '<div class="pri-col ' + cls + '"><div class="pri-h">' + title + '</div><ul>' + lis + '</ul></div>'
    return ('<div class="chart-card"><div class="chart-title">优先级看板（建议分级）</div>'
            '<div class="pri-row">' + col("Must 必做", must, "m") + col("Should 应做", should, "s")
            + col("Could 可做", could, "c") + '</div></div>')


CSS = """
:root{--bg:#f8fafc;--card:#fff;--ink:#1e293b;--muted:#64748b;--line:#e2e8f0;--brand:#6366f1;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.7;}
.wrap{max-width:980px;margin:0 auto;padding:36px 22px 90px;}
header.top{border-bottom:3px solid var(--brand);padding-bottom:18px;margin-bottom:28px;}
header.top h1{margin:0;font-size:27px;letter-spacing:.3px;color:#0f172a;}
header.top .sub{color:var(--muted);font-size:13px;margin-top:6px;letter-spacing:1px;}
.brief{background:linear-gradient(135deg,#eef2ff,#faf5ff);border:1px solid #e0e7ff;border-left:4px solid var(--brand);border-radius:14px;padding:18px 22px;margin-bottom:30px;}
.brief h3{margin:0 0 12px;font-size:14px;color:var(--brand);letter-spacing:1px;font-weight:700;}
.brief table{width:100%;border-collapse:collapse;font-size:13px;}
.brief td{padding:5px 10px;vertical-align:top;}
.brief td.k{color:var(--muted);width:104px;white-space:nowrap;font-weight:600;}
.section{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:24px 26px;margin-bottom:22px;box-shadow:0 1px 3px rgba(15,23,42,.05);}
.section h2{margin:0 0 16px;font-size:19px;color:#334155;border-left:4px solid var(--brand);padding-left:12px;}
.section p{margin:8px 0;font-size:14px;color:#334155;}
.chart-card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin:20px 0;box-shadow:0 1px 3px rgba(15,23,42,.05);}
.chart-title{font-size:15px;font-weight:600;margin-bottom:12px;color:#334155;}
.legend-note{font-size:11px;color:#a5b4d4;font-weight:400;margin-left:8px;}
.echart{width:100%;height:400px;}
.summary-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.summary-card{background:linear-gradient(135deg,#eef2ff,#faf5ff);border:1px solid #e0e7ff;border-radius:14px;padding:14px 16px;font-size:14px;color:#3730a3;line-height:1.6;}
.pri-row{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.pri-col{background:#f8fafc;border:1px solid var(--line);border-radius:14px;padding:14px;}
.pri-col.m{border-top:4px solid #ef4444;} .pri-col.s{border-top:4px solid #f59e0b;} .pri-col.c{border-top:4px solid #14b8a6;}
.pri-h{font-weight:700;font-size:14px;margin-bottom:10px;color:#334155;} .pri-col ul{margin:0;padding-left:18px;font-size:13px;color:#475569;line-height:1.7;}
.sent-bar{display:flex;height:16px;border-radius:8px;overflow:hidden;margin-bottom:8px;box-shadow:inset 0 0 0 1px rgba(15,23,42,.04);}
.sent-pos{background:linear-gradient(90deg,#34d399,#10b981);} .sent-neg{background:linear-gradient(90deg,#fb7185,#ef4444);}
.sent-meta{font-size:12px;color:var(--muted);margin-bottom:12px;}
.quote-list{display:flex;flex-direction:column;gap:8px;}
.quote{font-size:13px;padding:9px 13px;border-radius:10px;background:#f8fafc;border:1px solid #eef0f2;line-height:1.6;}
.quote.pos{border-left:3px solid #10b981;} .quote.neg{border-left:3px solid #ef4444;}
.qtag{display:inline-block;font-size:11px;color:var(--muted);margin-right:6px;font-weight:600;}
.src-card{font-size:12px;color:var(--muted);background:#f8fafc;border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:5px 0;}
.src-card a{color:var(--brand);text-decoration:none;}
ul{margin:10px 0;padding-left:22px;color:#334155;font-size:14px;line-height:1.7;}
@media(max-width:640px){.summary-grid,.pri-row{grid-template-columns:1fr;}}
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
    brief_html = ""
    body_parts = []
    tables = parse_tables(lines)
    table_at = {t[0]: t for t in tables}

    i = 0; mid = 0
    summary_items = []; priority = {"must": [], "should": [], "could": []}
    sentiment = []; timeline = []; evidence = []
    cur_section = ""

    n = len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r"^(#{1,2})\s+(.*)$", line)
        if m:
            level = len(m.group(1)); htext = m.group(2).strip()
            if level == 1:
                title = htext
            else:
                cur_section = htext
                if htext == "执行摘要":
                    body_parts.append('<div class="section"><h2>执行摘要</h2><div class="summary-grid" id="sum"></div></div>')
                elif htext == "来源":
                    body_parts.append('<div class="section"><h2>来源</h2><div id="src"></div></div>')
                else:
                    body_parts.append('<div class="section"><h2>' + html.escape(htext) + '</h2>')
            i += 1; continue
        if "研究简报" in line:
            brief_lines = []
            j = i + 1
            while j < n and lines[j].strip() and not lines[j].lstrip().startswith("#"):
                brief_lines.append(lines[j]); j += 1
            brief_html = '<div class="brief"><h3>研究简报 · RESEARCH BRIEF</h3><table>'
            for bl in brief_lines:
                bl = bl.strip().lstrip("·").strip()
                if "：" in bl:
                    k, v = bl.split("：", 1)
                    brief_html += '<tr><td class="k">' + html.escape(k) + '</td><td>' + html.escape(v) + '</td></tr>'
                elif bl:
                    brief_html += '<tr><td colspan="2">' + html.escape(bl) + '</td></tr>'
            brief_html += '</table></div>'
            i = j; continue
        if i in table_at:
            _, header, rows = table_at[i]
            if is_score_matrix(header, rows):
                mid += 1
                body_parts.append(render_score_matrix(mid, header, rows))
            elif is_scatter(header, rows) and ("地图" in cur_section):
                mid += 1
                body_parts.append(render_scatter(mid, header, rows, "机会" in cur_section))
            elif "来源" in header[0] or "链接" in header[-1] or "链接" in " ".join(header):
                for r in rows:
                    if len(r) >= 2:
                        evidence.append((r[0], r[-1]))
            else:
                th = "".join("<th>" + html.escape(c) + "</th>" for c in header)
                trs = "".join("<tr>" + "".join("<td>" + html.escape(c) + "</td>" for c in r) + "</tr>" for r in rows)
                body_parts.append('<table class="tbl" style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr>' + th + '</tr></thead><tbody>' + trs + '</tbody></table>')
            i = table_at[i][0] + 1
            while i < n and lines[i].lstrip().startswith("|"):
                i += 1
            continue
        if cur_section == "时间线" and line.strip().startswith("-"):
            mm = re.match(r"-\s*([\d]{4}[\d\-]*)\s*[：:]\s*(.*)", line.strip())
            if mm: timeline.append((mm.group(1), mm.group(2)))
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

    if summary_items:
        grid = "".join('<div class="summary-card">' + html.escape(s) + '</div>' for s in summary_items)
        body_parts = [p.replace('<div class="summary-grid" id="sum"></div>', '<div class="summary-grid">' + grid + '</div>') for p in body_parts]
    if timeline:
        mid += 1
        body_parts.append(render_timeline(mid, timeline))
    if sentiment:
        body_parts.append(render_sentiment(sentiment))
    if priority["must"] or priority["should"] or priority["could"]:
        body_parts.append(render_priority(priority["must"], priority["should"], priority["could"]))
    if evidence:
        cards = ""
        for nm, lk in evidence:
            if lk.startswith("http"):
                cards += '<div class="src-card">' + html.escape(nm) + '：<a href="' + lk + '">' + lk + '</a></div>'
            else:
                cards += '<div class="src-card">' + html.escape(nm) + '：' + html.escape(lk) + '</div>'
        body_parts = [p.replace('<div id="src"></div>', '<div>' + cards + '</div>') for p in body_parts]

    html_doc = ('<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + html.escape(title) + '</title>'
        '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>'
        '<style>' + CSS + '</style></head><body><div class="wrap">'
        '<header class="top"><h1>' + html.escape(title) + '</h1>'
        '<div class="sub">AI PM Research System · 可视化研究报告</div></header>'
        + brief_html + "".join(body_parts) +
        '</div><script>var REG=[];window.addEventListener("resize",function(){REG.forEach(function(c){c.resize();});});</script>'
        '</body></html>')
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print("OK -> " + args.output + " (" + str(len(html_doc)) + " bytes)")


if __name__ == "__main__":
    main()
