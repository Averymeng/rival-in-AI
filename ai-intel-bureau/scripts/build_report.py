#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI情报局 · 可视化渲染脚本（零依赖，自包含 HTML）
把带「约定写法」的 Markdown 报告转为美观的可视化页面。

约定写法见 references/visualization.md：
  - 评分矩阵（首列「维度」）        → 雷达图 + 热力矩阵
  - 市场地图（含 X轴/Y轴/规模）     → 定位散点图
  - 含 → 的步骤行                  → 流程图
  - Must:/Should:/Could: 开头行     → 优先级看板
  - 「结论/核心发现」下的 bullet     → 摘要卡片
  - 含 来源/链接/说明 的表格        → 来源卡片
"""
import argparse
import re
import html
import math

PALETTE = ['#6366f1', '#14b8a6', '#f59e0b', '#ef4444', '#8b5cf6', '#0ea5e9', '#ec4899']


# --------------------------- 表格解析 ---------------------------
def parse_table(rows):
    data = []
    for r in rows:
        cells = [c.strip() for c in r.strip().strip('|').split('|')]
        data.append(cells)
    if len(data) < 1:
        return [], []
    header = data[0]
    if len(data) > 1 and all(set(c) <= set('-: ') for c in data[1] if c != ''):
        body = data[2:]
    else:
        body = data[1:]
    return header, body


def classify_table(header):
    h0 = header[0] if header else ''
    if h0 == '维度':
        return 'score'
    if any('X轴' in c for c in header) and any('Y轴' in c for c in header):
        return 'market'
    if any('来源' in c for c in header) and any('链接' in c for c in header):
        return 'source'
    return 'normal'


# --------------------------- 图表：雷达 ---------------------------
def render_radar(objects, dims, matrix):
    n = len(dims)
    if n < 3:
        return ''
    cx, cy, R = 260, 240, 180
    step = 2 * math.pi / n
    start = -math.pi / 2

    def pt(angle, r):
        return (cx + r * math.cos(angle), cy + r * math.sin(angle))

    # 网格
    grid = ''
    for lvl in range(1, 6):
        pts = [pt(start + i * step, R * lvl / 5) for i in range(n)]
        poly = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        grid += f'<polygon points="{poly}" fill="none" stroke="#e2e8f0" stroke-width="1"/>'
    axes = ''
    labels = ''
    for i in range(n):
        ang = start + i * step
        x, y = pt(ang, R)
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#e2e8f0"/>'
        lx, ly = pt(ang, R + 22)
        anchor = 'middle'
        if lx < cx - 10:
            anchor = 'end'
        elif lx > cx + 10:
            anchor = 'start'
        labels += f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="12" fill="#475569" text-anchor="{anchor}">{html.escape(dims[i])}</text>'

    series = ''
    legend = ''
    for oi, obj in enumerate(objects):
        color = PALETTE[oi % len(PALETTE)]
        vals = [matrix[di][oi] if oi < len(matrix[di]) else None for di in range(n)]
        pts = []
        for i in range(n):
            v = vals[i]
            if v is None:
                v = 0
            pts.append(pt(start + i * step, R * v / 5))
        poly = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        series += f'<polygon points="{poly}" fill="{color}22" stroke="{color}" stroke-width="2"/>'
        for (x, y), v in zip(pts, vals):
            if v is not None:
                series += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>'
        legend += f'<span class="legend"><i style="background:{color}"></i>{html.escape(obj)}</span>'

    return f'''
    <div class="chart-card">
      <h4>能力雷达图</h4>
      <div class="chart-flex">
        <svg viewBox="0 0 520 480" width="100%" style="max-width:460px">
          {grid}{axes}{labels}{series}
        </svg>
        <div class="legend-box">{legend}</div>
      </div>
    </div>'''


# --------------------------- 图表：热力矩阵 ---------------------------
def heat_color(v):
    # 1(浅) -> 5(深蓝)
    if v is None:
        return '#f1f5f9'
    t = (v - 1) / 4.0
    r = int(224 - t * (224 - 37))
    g = int(231 - t * (231 - 99))
    b = int(242 - t * (242 - 235))
    return f'rgb({r},{g},{b})'


def render_heat(objects, dims, matrix):
    head = '<th></th>' + ''.join(f'<th>{html.escape(o)}</th>' for o in objects)
    rows = ''
    for i, d in enumerate(dims):
        cells = f'<th class="rowh">{html.escape(d)}</th>'
        for oi in range(len(objects)):
            v = matrix[i][oi] if oi < len(matrix[i]) else None
            if v is None:
                cells += f'<td style="background:{heat_color(None)};color:#94a3b8">未查证</td>'
            else:
                cells += f'<td style="background:{heat_color(v)};color:{"#fff" if v>=4 else "#1e293b"}">{v}</td>'
        rows += f'<tr>{cells}</tr>'
    return f'''
    <div class="chart-card">
      <h4>维度热力矩阵</h4>
      <table class="heat"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>
    </div>'''


# --------------------------- 图表：市场地图 ---------------------------
def render_market(header, body):
    name_i = next((i for i, c in enumerate(header) if '产品' in c), 0)
    x_i = next(i for i, c in enumerate(header) if 'X轴' in c)
    y_i = next(i for i, c in enumerate(header) if 'Y轴' in c)
    size_i = next((i for i, c in enumerate(header) if '规模' in c), None)

    W, H, pad = 560, 420, 50
    def sx(v):
        return pad + (float(v) - 1) / 9.0 * (W - 2 * pad)
    def sy(v):
        return H - pad - (float(v) - 1) / 9.0 * (H - 2 * pad)

    grid = f'<line x1="{pad}" y1="{H-pad}" x2="{W-pad}" y2="{H-pad}" stroke="#cbd5e1"/>' \
           f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{H-pad}" stroke="#cbd5e1"/>'
    # 刻度
    for t in range(1, 11, 2):
        grid += f'<text x="{sx(t)}" y="{H-pad+16}" font-size="10" fill="#94a3b8" text-anchor="middle">{t}</text>'
        grid += f'<text x="{pad-8}" y="{sy(t)+4}" font-size="10" fill="#94a3b8" text-anchor="end">{t}</text>'

    bubbles = ''
    for row in body:
        try:
            name = row[name_i]
            x = sx(row[x_i]); y = sy(row[y_i])
            r = 8 + (float(row[size_i]) - 1) / 9.0 * 16 if size_i is not None else 10
            bubbles += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#6366f1" fill-opacity="0.55" stroke="#4338ca"/>'
            bubbles += f'<text x="{x:.1f}" y="{y-r-4:.1f}" font-size="11" fill="#1e293b" text-anchor="middle">{html.escape(name)}</text>'
        except (ValueError, IndexError):
            continue
    return f'''
    <div class="chart-card">
      <h4>市场地图（定位散点）</h4>
      <svg viewBox="0 0 {W} {H}" width="100%" style="max-width:600px;background:#fafbff;border-radius:12px">
        {grid}{bubbles}
      </svg>
    </div>'''


# --------------------------- 图表：流程图 ---------------------------
def render_flow(text):
    parts = [p.strip() for p in re.split(r'→|->', text) if p.strip()]
    if len(parts) < 2:
        return ''
    boxes = ''.join(f'<div class="flow-node">{html.escape(p)}</div>' for p in parts)
    return f'''
    <div class="chart-card">
      <h4>关键路径</h4>
      <div class="flow">{boxes}</div>
    </div>'''


# --------------------------- 图表：优先级看板 ---------------------------
def render_priority(must, should, could):
    def col(title, items, cls):
        lis = ''.join(f'<li>{html.escape(i)}</li>' for i in items)
        return f'<div class="prio {cls}"><h5>{title}</h5><ul>{lis}</ul></div>'
    return f'''
    <div class="chart-card">
      <h4>优先级看板</h4>
      <div class="prio-row">
        {col('Must 必做', must, 'm')}
        {col('Should 应做', should, 's')}
        {col('Could 可做', could, 'c')}
      </div>
    </div>'''


# --------------------------- 来源卡片 ---------------------------
def render_sources(header, body):
    try:
        li = header.index('来源'); ki = header.index('链接'); di = header.index('说明')
    except ValueError:
        li, ki, di = 0, 1, 2
    cards = ''
    for row in body:
        if len(row) <= max(li, ki, di):
            continue
        link = row[ki]
        link_html = f'<a href="{html.escape(link)}" target="_blank">{html.escape(link)}</a>' if link.startswith('http') else html.escape(link)
        cards += f'''<div class="src-card">
          <div class="src-name">{html.escape(row[li])}</div>
          <div class="src-link">{link_html}</div>
          <div class="src-desc">{html.escape(row[di])}</div>
        </div>'''
    return f'<div class="src-row">{cards}</div>'


# --------------------------- 主渲染 ---------------------------
def render(md_text):
    lines = md_text.split('\n')
    out = []
    i = 0
    n = len(lines)
    cur_section = ''
    bullet_buffer = []
    flow_buffer = []
    prio = {'Must': [], 'Should': [], 'Could': []}

    def flush_bullets():
        nonlocal bullet_buffer
        if not bullet_buffer:
            return
        is_card = any(k in cur_section for k in ('结论', '核心发现', '摘要'))
        if is_card:
            cards = ''.join(f'<div class="summary-card">{html.escape(b)}</div>' for b in bullet_buffer)
            out.append(f'<div class="card-row">{cards}</div>')
        else:
            out.append('<ul>' + ''.join(f'<li>{html.escape(b)}</li>' for b in bullet_buffer) + '</ul>')
        bullet_buffer = []

    def flush_flow():
        nonlocal flow_buffer
        for f in flow_buffer:
            out.append(render_flow(f))
        flow_buffer = []

    def flush_prio():
        if any(prio.values()):
            out.append(render_priority(prio['Must'], prio['Should'], prio['Could']))
            prio['Must'] = prio['Should'] = prio['Could'] = []

    while i < n:
        line = lines[i]
        # 标题
        if line.startswith('# '):
            flush_bullets(); flush_flow(); flush_prio()
            out.append(f'<h1>{html.escape(line[2:].strip())}</h1>')
            cur_section = line[2:].strip()
            i += 1; continue
        if line.startswith('## '):
            flush_bullets(); flush_flow(); flush_prio()
            out.append(f'<h2>{html.escape(line[3:].strip())}</h2>')
            cur_section = line[3:].strip()
            i += 1; continue
        if line.startswith('### '):
            flush_bullets(); flush_flow(); flush_prio()
            out.append(f'<h3>{html.escape(line[4:].strip())}</h3>')
            cur_section = line[4:].strip()
            i += 1; continue
        # 优先级行
        m = re.match(r'^\s*(Must|Should|Could)\s*[:：]\s*(.*)$', line, re.I)
        if m:
            flush_bullets(); flush_flow()
            prio[m.group(1).title()].append(m.group(2).strip())
            i += 1; continue
        # 表格
        if line.strip().startswith('|'):
            tbl = []
            while i < n and lines[i].strip().startswith('|'):
                tbl.append(lines[i]); i += 1
            header, body = parse_table(tbl)
            kind = classify_table(header)
            if kind == 'score':
                objects = header[1:]
                dims = [r[0] for r in body]
                matrix = []
                for r in body:
                    vals = []
                    for v in r[1:]:
                        if re.match(r'^\d+(\.\d+)?$', v):
                            vals.append(float(v))
                        else:
                            vals.append(None)
                    while len(vals) < len(objects):
                        vals.append(None)
                    matrix.append(vals)
                out.append(render_radar(objects, dims, matrix))
                out.append(render_heat(objects, dims, matrix))
            elif kind == 'market':
                out.append(render_market(header, body))
            elif kind == 'source':
                out.append(render_sources(header, body))
            else:
                out.append(render_normal_table(header, body))
            continue
        # 流程图行
        if ('→' in line or '->' in line) and not line.strip().startswith('-'):
            flush_bullets()
            flow_buffer.append(line.strip())
            i += 1; continue
        # 列表
        if re.match(r'^\s*[-*]\s+', line):
            flush_flow()
            bullet_buffer.append(re.sub(r'^\s*[-*]\s+', '', line).strip())
            i += 1; continue
        # 空行
        if line.strip() == '':
            flush_bullets(); flush_flow()
            i += 1; continue
        # 普通段落
        flush_bullets(); flush_flow()
        out.append(f'<p>{html.escape(line.strip())}</p>')
        i += 1

    flush_bullets(); flush_flow(); flush_prio()
    return '\n'.join(out)


def render_normal_table(header, body):
    head = ''.join(f'<th>{html.escape(c)}</th>' for c in header)
    rows = ''
    for r in body:
        rows += '<tr>' + ''.join(f'<td>{html.escape(c)}</td>' for c in r) + '</tr>'
    return f'<table class="normal"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>'


CSS = """
:root{--bg:#f8fafc;--card:#fff;--ink:#1e293b;--muted:#64748b;--line:#e2e8f0;--brand:#6366f1;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.7;}
.wrap{max-width:960px;margin:0 auto;padding:32px 20px 80px;}
h1{font-size:28px;margin:8px 0 20px;padding-bottom:12px;border-bottom:3px solid var(--brand);}
h2{font-size:21px;margin:34px 0 14px;color:#334155;}
h3{font-size:17px;margin:22px 0 10px;color:#475569;}
p{margin:10px 0;color:#334155;}
.chart-card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin:18px 0;box-shadow:0 1px 3px rgba(15,23,42,.06);}
.chart-card h4{margin:0 0 12px;font-size:15px;color:#334155;}
.chart-flex{display:flex;gap:18px;align-items:center;flex-wrap:wrap;}
.legend-box{display:flex;flex-direction:column;gap:6px;font-size:13px;color:var(--muted);}
.legend{display:inline-flex;align-items:center;gap:6px;}
.legend i{width:12px;height:12px;border-radius:3px;display:inline-block;}
table.heat{border-collapse:collapse;width:100%;font-size:14px;}
table.heat th,table.heat td{border:1px solid var(--line);padding:10px 12px;text-align:center;}
table.heat th{background:#f1f5f9;color:#475569;font-weight:600;}
table.heat td.rowh{background:#f1f5f9;color:#475569;font-weight:600;text-align:left;}
table.normal{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px;}
table.normal th,table.normal td{border:1px solid var(--line);padding:9px 12px;}
table.normal th{background:#f1f5f9;}
.card-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin:14px 0;}
.summary-card{background:linear-gradient(135deg,#eef2ff,#faf5ff);border:1px solid #e0e7ff;border-radius:14px;padding:14px 16px;font-size:14px;color:#3730a3;}
.flow{display:flex;align-items:center;flex-wrap:wrap;gap:6px;}
.flow-node{background:var(--brand);color:#fff;padding:8px 14px;border-radius:20px;font-size:13px;}
.flow-node:not(:last-child)::after{content:"→";margin-left:10px;color:var(--muted);}
.prio-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.prio{background:#f8fafc;border-radius:12px;padding:12px 14px;border-top:4px solid #cbd5e1;}
.prio.m{border-top-color:#ef4444;}.prio.s{border-top-color:#f59e0b;}.prio.c{border-top-color:#14b8a6;}
.prio h5{margin:0 0 8px;font-size:14px;}.prio ul{margin:0;padding-left:18px;font-size:13px;color:#475569;}
.src-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;}
.src-card{background:#f8fafc;border:1px solid var(--line);border-radius:12px;padding:12px 14px;}
.src-name{font-weight:600;font-size:14px;}.src-link{font-size:12px;color:var(--brand);word-break:break-all;margin:4px 0;}.src-desc{font-size:13px;color:var(--muted);}
ul{margin:10px 0;padding-left:22px;color:#334155;}
@media(max-width:640px){.prio-row{grid-template-columns:1fr;}}
"""

TPL = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI情报局 · 竞品分析报告</title><style>{css}</style></head>
<body><div class="wrap">{body}</div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('--output', '-o', default=None)
    args = ap.parse_args()
    with open(args.input, encoding='utf-8') as f:
        md = f.read()
    body = render(md)
    out = TPL.format(css=CSS, body=body)
    out_path = args.output or (args.input.rsplit('.', 1)[0] + '.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(out)
    print('OK ->', out_path)


if __name__ == '__main__':
    main()
