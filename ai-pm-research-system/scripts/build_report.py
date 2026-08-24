#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIPM·瞭望台 · 可视化渲染器
约定写法（Markdown）→ 自包含 HTML（ECharts CDN）。
支持：能力雷达图 / 市场地图（带面积气泡）/ 竞争关系图 / 梯队金字塔 / 时间线 / 漏斗图 /
      用户口碑 / 优先级看板 / 行动建议卡 / 执行摘要条 / SWOT / 来源行内链接。

设计语言（2025-08-25 迭代 v2）：
  - 背景奶黄 #f8fafc，主色暖橘 #3b82f6，强调浅黄 #93c5fd
  - 严格对齐参考图：功能矩阵 / 金字塔 / AI 能力卡 / 竞争格局 / 市场地图 / 用户口碑 / 能力雷达
  - 每个章节独立成块，图表归属其章节，杜绝错位
  - 全文中禁止出现原始 Markdown 符号（- ** 等）
"""
import sys, re, json, html, argparse, datetime

PALETTE = ["#3B82F6", "#8B5CF6", "#10B981", "#3b82f6", "#0EA5E9", "#EC4899", "#14B8A6", "#6366F1"]

SCATTER_TOOLTIP = "function(p){return p.data.name+'<br/>专业能力：'+p.data.value[0]+'<br/>生态影响力：'+p.data.value[1]+'<br/>规模：'+p.data.value[2];}"
SCATTER_LABEL = "function(p){return p.data.name;}"


ICON_PATHS = {
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>',
    "chart-bar": '<path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v6"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "network": '<circle cx="5" cy="7" r="2"/><circle cx="19" cy="7" r="2"/><circle cx="12" cy="17" r="2"/><path d="M5 9l7 6.5M19 9l-7 6.5"/>',
    "stack": '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>',
    "crown": '<path d="M4 16l2.5-9 3.5 5 4-7 3.5 5 2.5-6v12H4z"/>',
    "person": '<circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>',
    "bar-chart": '<path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v6"/>',
    "document": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "sparkle": '<path d="M12 2l1.5 5h5L15 11l1.5 5-5-3-5 3 1.5-5-4-4h5z"/>',
    "cloud": '<path d="M18 20a4 4 0 0 0 0-8h-1.3A6.5 6.5 0 0 0 4.3 12 4 4 0 0 0 6 20h12z"/>',
    "paper-plane": '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22,2 15,22 11,13 2,9"/>',
    "people": '<path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9.5" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "diamond": '<path d="M6 3h12l4.5 7.5L12 22 1.5 10.5z"/>',
    "monitor": '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
    "tag": '<path d="M20.6 13.4l-7 7a2 2 0 0 1-2.8 0L2.7 12.9a2 2 0 0 1 0-2.8l7-7a2 2 0 0 1 2.8 0l8.1 8.1a2 2 0 0 1 0 2.8z"/><circle cx="14" cy="8" r="2"/>',
    "info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    "bullet": '<circle cx="12" cy="12" r="4"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "x": '<path d="M18 6L6 18M6 6l12 12"/>',
    "star": '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>',
    "video": '<polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/>',
    "music": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    "mic": '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>',
    "smile": '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>',
    "sad": '<circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>',
    "thumbs-up": '<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>',
    "thumbs-down": '<path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"/>',
    "lightbulb": '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.9.27-1.48-.74-2.6a4.72 4.72 0 0 1-.3-5.77A5 5 0 0 0 7 9.09a5.24 5.24 0 0 0 1.24 4.4c.75.87 1 1.35.83 2.51H15.09z"/>',
    "trending": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "cpu": '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    "bot": '<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8.01" y2="16"/><line x1="16" y1="16" x2="16.01" y2="16"/>',
    "copy": '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "figma": '<path d="M5 5.5A3.5 3.5 0 0 1 8.5 2H12v7H8.5A3.5 3.5 0 0 1 5 5.5z"/><path d="M12 2h3.5a3.5 3.5 0 1 1 0 7H12V2z"/><path d="M12 12.5a3.5 3.5 0 1 1 7 0 3.5 3.5 0 1 1-7 0z"/><path d="M5 19.5A3.5 3.5 0 0 1 8.5 23H12v-7H8.5A3.5 3.5 0 0 1 5 19.5z"/><path d="M5 12.5A3.5 3.5 0 0 1 8.5 9H12v7H8.5A3.5 3.5 0 0 1 5 12.5z"/>',
    "mail": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
    "anchor": '<circle cx="12" cy="5" r="3"/><line x1="12" y1="22" x2="12" y2="8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/>',
    "compass": '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
}


# 简单的用户简笔画头像集合（循环使用）
AVATARS = [
    # 女生短发带发夹
    '<circle cx="32" cy="26" r="11" fill="none" stroke="currentColor" stroke-width="2"/><path d="M18 55c0-10 7-16 14-16s14 6 14 16" fill="none" stroke="currentColor" stroke-width="2"/><path d="M21 24c0-6 5-11 11-11s11 5 11 11" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="28" cy="28" r="1.5" fill="currentColor"/><circle cx="36" cy="28" r="1.5" fill="currentColor"/><path d="M30 34q2 2 4 0" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="39" cy="21" r="2" fill="currentColor"/>',
    # 戴眼镜男生
    '<circle cx="32" cy="26" r="11" fill="none" stroke="currentColor" stroke-width="2"/><path d="M18 55c0-10 7-16 14-16s14 6 14 16" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="28" cy="27" r="3" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="36" cy="27" r="3" fill="none" stroke="currentColor" stroke-width="1.5"/><line x1="31" y1="27" x2="33" y2="27" stroke="currentColor" stroke-width="1.5"/><path d="M21 23c0-6 5-11 11-11s11 5 11 11" fill="none" stroke="currentColor" stroke-width="2"/><path d="M30 34q2 2 4 0" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
    # 双马尾女生
    '<circle cx="32" cy="26" r="11" fill="none" stroke="currentColor" stroke-width="2"/><path d="M18 55c0-10 7-16 14-16s14 6 14 16" fill="none" stroke="currentColor" stroke-width="2"/><path d="M21 22c-3 0-5 6-5 10M43 22c3 0 5 6 5 10" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="28" cy="28" r="1.5" fill="currentColor"/><circle cx="36" cy="28" r="1.5" fill="currentColor"/><path d="M30 34q2 2 4 0" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
    # 戴帽子男生
    '<circle cx="32" cy="28" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M18 55c0-10 7-16 14-16s14 6 14 16" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20c0-6 5-10 12-10s12 4 12 10" fill="none" stroke="currentColor" stroke-width="2"/><line x1="18" y1="20" x2="46" y2="20" stroke="currentColor" stroke-width="2"/><circle cx="28" cy="29" r="1.5" fill="currentColor"/><circle cx="36" cy="29" r="1.5" fill="currentColor"/><path d="M30 35q2 2 4 0" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
    # 卷发女生
    '<circle cx="32" cy="26" r="11" fill="none" stroke="currentColor" stroke-width="2"/><path d="M18 55c0-10 7-16 14-16s14 6 14 16" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 24c0-7 5-12 12-12s12 5 12 12c0 2-1 4-2 5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="28" cy="28" r="1.5" fill="currentColor"/><circle cx="36" cy="28" r="1.5" fill="currentColor"/><path d="M30 34q2 2 4 0" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M18 28c-2 2-2 6 0 8M46 28c2 2 2 6 0 8" fill="none" stroke="currentColor" stroke-width="2"/>',
    # 惊讶表情男生
    '<circle cx="32" cy="26" r="11" fill="none" stroke="currentColor" stroke-width="2"/><path d="M18 55c0-10 7-16 14-16s14 6 14 16" fill="none" stroke="currentColor" stroke-width="2"/><path d="M21 23c0-6 5-11 11-11s11 5 11 11" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="28" cy="28" r="2" fill="currentColor"/><circle cx="36" cy="28" r="2" fill="currentColor"/><circle cx="32" cy="35" r="2" fill="none" stroke="currentColor" stroke-width="1.5"/>',
]


def avatar(idx, color="#3b82f6", size=56):
    svg = AVATARS[idx % len(AVATARS)]
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{svg}</svg>')


def icon(name, size=20, color="#3b82f6"):
    """返回统一尺寸的 inline SVG 图标，name 不存在时回退为圆点。"""
    path = ICON_PATHS.get(name, ICON_PATHS["bullet"])
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{path}</svg>')


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


# ---------- 功能矩阵 ----------
FEATURE_ICONS = {
    "文生图": "image", "图生图": "image", "编辑": "figma", "文生视频": "video", "图生视频": "video",
    "数字人": "user", "音乐生成": "music", "配音生成": "mic", "动作模仿": "person",
    "agent模式": "bot", "agent": "bot", "爆款复刻": "copy", "照片会说话": "smile",
    "白模渲染": "layers", "octo协作": "people", "多模态": "layers", "底层模型": "cpu",
    "免费策略": "mail", "基础会员": "tag", "标准会员": "tag", "高级会员": "tag",
    "积分消耗": "zap", "api服务": "anchor", "变现结构": "trending",
}


def feature_icon(name):
    key = name.lower().replace(" ", "").replace("/", "").replace("、", "")
    for k, v in FEATURE_ICONS.items():
        if k in key:
            return v
    return "bullet"


def product_color(name):
    if "即梦" in name:
        return "#3b82f6"
    if "小云雀" in name:
        return "#3B82F6"
    return PALETTE[hash(name) % len(PALETTE)]


def product_icon(name):
    if "即梦" in name:
        return "sparkle"
    if "小云雀" in name:
        return "cloud"
    return "monitor"


def parse_feature_cell(cell):
    """解析 ✅（备注） 或 ❌（备注） 为 (支持, 备注)。"""
    cell = cell.strip()
    support = None
    if cell.startswith('✅') or cell.startswith('✔') or cell.startswith('是'):
        support = True
    elif cell.startswith('❌') or cell.startswith('✗') or cell.startswith('否') or cell.startswith('×'):
        support = False
    note = re.sub(r'^[✅✔❌✗×是否]\s*', '', cell).strip()
    note = note.strip('（）()')
    return support, note


def render_feature_matrix(header, rows):
    """功能矩阵：表头带产品图标，行带功能图标，支持/不支持徽章，底部图例+总结。"""
    products = header[1:]
    prod_header = ""
    for p in products:
        c = product_color(p)
        prod_header += ('<th style="text-align:center"><div class="fm-prod"><span class="fm-prod-icon" '
                        'style="background:' + c + '20;color:' + c + '">' + icon(product_icon(p), 18, c)
                        + '</span><span style="color:' + c + '">' + html.escape(p) + '</span></div></th>')

    trs = ""
    supports = 0
    unsupports = 0
    for r in rows:
        if not r:
            continue
        fname = clean(r[0])
        fi = feature_icon(fname)
        cells = '<td><span class="fm-row-icon">' + icon(fi, 18, "#3b82f6") + '</span>' + html.escape(fname) + '</td>'
        for c in r[1:]:
            sup, note = parse_feature_cell(c)
            if sup is True:
                supports += 1
                badge = '<span class="fm-check yes">' + icon("check", 14, "#fff") + '</span>'
            elif sup is False:
                unsupports += 1
                badge = '<span class="fm-check no">' + icon("x", 14, "#fff") + '</span>'
            else:
                badge = '<span class="fm-check na">-</span>'
            note_html = '<span class="fm-note">' + html.escape(note) + '</span>' if note else ''
            cells += '<td><div class="fm-cell">' + badge + note_html + '</div></td>'
        trs += '<tr>' + cells + '</tr>'

    legend = ('<div class="fm-legend">'
              '<div class="fm-leg"><span class="fm-check yes">' + icon("check", 12, "#fff") + '</span><b>支持</b><span>已具备相关功能或明确支持</span></div>'
              '<div class="fm-leg"><span class="fm-check no">' + icon("x", 12, "#fff") + '</span><b>不支持/未明确</b><span>暂无相关功能或官方未明确说明</span></div>'
              '<div class="fm-leg"><span class="fm-leg-icon">' + icon("lightbulb", 16, "#3b82f6") + '</span><b>总结</b><span>即梦功能全面，小云雀场景化能力突出</span></div>'
              '</div>')

    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">功能矩阵</span></div>'
            '<table class="feature-matrix"><thead><tr><th>功能模块</th>' + prod_header + '</tr></thead><tbody>'
            + trs + '</tbody></table>' + legend + '</div>')


# ---------- 能力雷达 ----------
RADAR_DIM_ICONS = {
    "图像生成": "image", "视频生成": "video", "多模态能力": "layers", "agent智能化": "bot",
    "易用性": "smile", "功能丰富度": "grid", "商业化成熟度": "trending", "生态协同": "network",
    "用户口碑": "people", "迭代速度": "zap",
}


def render_score_matrix(mid, header, rows):
    """评分矩阵：渲染多边形能力雷达 + 右侧能力总览 + 底部维度说明。"""
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
        "tooltip": {"textStyle": {"color": "#1e293b"}},
        "legend": {"bottom": 0, "data": objects, "textStyle": {"color": "#1e293b", "fontSize": 12},
                   "itemGap": 16, "icon": "roundRect"},
        "radar": {
            "indicator": indicators, "radius": "58%", "center": ["46%", "48%"],
            "axisName": {"color": "#64748b", "fontSize": 12, "formatter": "function(v){return v;}"},
            "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            "axisLine": {"lineStyle": {"color": "#e2e8f0"}},
            "splitArea": {"areaStyle": {"color": ["#f8fafc", "#FFFFFF"]}}
        },
        "series": [{"type": "radar", "data": radar_data, "symbolSize": 5}]
    }

    # 能力总览面板
    summary_cards = ""
    star = '<span class="star">★</span>'
    emptystar = '<span class="star empty">★</span>'
    for oi, obj in enumerate(objects):
        c = PALETTE[oi % len(PALETTE)]
        avg = sum(matrix[oi]) / len(matrix[oi]) if matrix[oi] else 0
        full = int(round(avg))
        stars = star * full + emptystar * (5 - full)
        summary_cards += ('<div class="radar-summary-card"><div class="radar-sum-icon" style="background:' + c + '20;color:' + c + '">'
                          + icon(product_icon(obj), 20, c) + '</div><div class="radar-sum-main">'
                          + '<div class="radar-sum-title">' + html.escape(obj) + '<span class="radar-stars">' + stars + '</span></div>'
                          + '<div class="radar-sum-desc">综合评分：<b style="color:' + c + '">' + f"{avg:.1f}" + '</b></div></div></div>')

    # 维度说明
    dim_legend = ""
    for d in dims:
        ico = RADAR_DIM_ICONS.get(d, "bullet")
        dim_legend += ('<div class="radar-dim"><span class="radar-dim-icon">' + icon(ico, 16, "#3b82f6")
                       + '</span><span>' + html.escape(d) + '</span></div>')

    chart = ('<div class="chart-card"><div class="chart-header"><span class="chart-title">多维能力图谱（综合评分）</span>'
             '<span class="chart-legend">评分口径：5=领先，3=平均，1=基本不覆盖</span></div>'
             '<div class="radar-wrap"><div id="radar_' + str(mid) + '" class="echart" style="height:460px"></div>'
             '<div class="radar-side">' + summary_cards + '</div></div>'
             '<div class="radar-dim-title">能力维度说明</div>'
             '<div class="radar-dim-grid">' + dim_legend + '</div></div>\n'
             '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("radar_' + str(mid) + '"));'
             'c.setOption(' + json.dumps(radar_opt, ensure_ascii=False) + ');REG.push(c);});</script>')
    return chart


# ---------- 市场地图 ----------
def render_scatter(mid, header, rows, is_opp=False):
    """市场地图：带面积覆盖的彩色气泡，底部产品图例卡片。"""
    data = []
    min_s = 999
    max_s = 0
    for i, r in enumerate(rows):
        if len(r) < 4:
            continue
        try:
            x = float(r[1]); y = float(r[2]); s = float(r[3])
        except Exception:
            continue
        c = PALETTE[i % len(PALETTE)]
        data.append({"name": r[0], "value": [x, y, s], "itemStyle": {"color": c}, "label": {"color": "#1e293b"}})
        min_s = min(min_s, s)
        max_s = max(max_s, s)

    title = "机会地图（空白区气泡）" if is_opp else "市场地图（定位气泡，面积=规模）"
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "__SCATTER_TOOLTIP__"},
        "grid": {"left": "10%", "right": "10%", "top": "12%", "bottom": "14%"},
        "xAxis": {"name": "专业能力 (X)", "nameTextStyle": {"color": "#64748b"},
                  "min": 0, "max": 10, "axisLabel": {"color": "#64748b"},
                  "axisLine": {"lineStyle": {"color": "#e2e8f0"}},
                  "splitLine": {"lineStyle": {"color": "#eff6ff", "type": "dashed"}}},
        "yAxis": {"name": "生态影响力 (Y)", "nameTextStyle": {"color": "#64748b"},
                  "min": 0, "max": 10, "axisLabel": {"color": "#64748b"},
                  "axisLine": {"lineStyle": {"color": "#e2e8f0"}},
                  "splitLine": {"lineStyle": {"color": "#eff6ff", "type": "dashed"}}},
        "series": [
            {"type": "scatter", "data": data,
             "symbolSize": "function(d){return 32 + d[2]*12;}",
             "itemStyle": {"opacity": 0.22, "borderWidth": 0},
             "z": 1, "silent": True, "label": {"show": False}},
            {"type": "scatter", "data": data,
             "symbolSize": "function(d){return 22 + d[2]*8;}",
             "itemStyle": {"opacity": 0.9, "borderColor": "#FFFFFF", "borderWidth": 2},
             "label": {"show": True, "formatter": "__SCATTER_LABEL__", "position": "inside",
                       "color": "#fff", "fontSize": 12, "fontWeight": "bold"}, "z": 2}
        ]
    }
    opt_json = json.dumps(opt, ensure_ascii=False)
    opt_json = opt_json.replace('"__SCATTER_TOOLTIP__"', SCATTER_TOOLTIP).replace('"__SCATTER_LABEL__"', SCATTER_LABEL)

    # 底部图例卡片
    cards = ""
    for i, r in enumerate(rows):
        if len(r) < 4:
            continue
        c = PALETTE[i % len(PALETTE)]
        cards += ('<div class="map-legend-card"><span class="map-dot" style="background:' + c + '"></span>'
                  + '<b>' + html.escape(r[0]) + '</b><span>' + html.escape(r[0]) + '在市场中定位</span></div>')

    chart = ('<div class="chart-card"><div class="chart-header"><span class="chart-title">' + title + '</span>'
             '<span class="chart-legend">气泡越大 = 市场份额/影响力越高</span></div>'
             '<div id="scatter_' + str(mid) + '" class="echart"></div>'
             '<div class="map-legend">' + cards + '</div></div>\n'
             '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("scatter_' + str(mid)
             + '"));c.setOption(' + opt_json + ');REG.push(c);});</script>')
    return chart


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
        "color": ["#3b82f6", "#F97316", "#60a5fa", "#93c5fd", "#EF4444", "#8B5CF6"],
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
        "tooltip": {"trigger": "axis", "textStyle": {"color": "#1e293b"}},
        "grid": {"left": "8%", "right": "6%", "top": "14%", "bottom": "10%"},
        "xAxis": {"type": "category", "data": names, "axisLabel": {"color": "#64748b"},
                  "axisLine": {"lineStyle": {"color": "#e2e8f0"}}, "axisTick": {"show": False}},
        "yAxis": {"type": "value", "show": False},
        "series": [{"type": "line", "data": vals, "smooth": True, "symbol": "circle", "symbolSize": 8,
                    "lineStyle": {"color": "#3b82f6", "width": 3},
                    "itemStyle": {"color": "#3b82f6", "borderColor": "#fff", "borderWidth": 2},
                    "areaStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                              "colorStops": [{"offset": 0, "color": "rgba(59,130,246,.25)"},
                                                               {"offset": 1, "color": "rgba(59,130,246,.02)"}]}},
                    "label": {"show": True, "position": "top", "color": "#1e293b", "formatter": "{c}"}}]
    }
    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">时间线</span></div>'
            '<div id="tl_' + str(mid) + '" class="echart" style="height:240px"></div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("tl_' + str(mid)
            + '"));c.setOption(' + json.dumps(opt, ensure_ascii=False) + ');REG.push(c);});</script>')


# ---------- 竞争格局 ----------
def render_competition_graph(mid, center, others, market_map=None):
    """竞争格局：有序圆形关系图，中心主体，外环竞品，两侧优势框，底部挑战条。"""
    # 主体颜色：默认橙色（即梦），蓝色（小云雀）
    main_items = [x.strip() for x in center.split('、')] if '、' in center else [center]
    main_html = ""
    for m in main_items:
        c = product_color(m)
        main_html += ('<div class="comp-main-node" style="background:' + c + '"><div class="comp-main-icon">'
                      + icon(product_icon(m), 24, "#fff") + '</div><div>' + html.escape(m)
                      + '</div><small>' + html.escape(m) + '核心主体</small></div>')

    # 外环竞品
    ring_html = ""
    for i, o in enumerate(others[:6]):
        angle = 360 / max(len(others), 1) * i - 90
        c = product_color(o)
        ring_html += ('<div class="comp-node" style="transform:rotate(' + str(angle) + 'deg) translate(150px) rotate(-' + str(angle) + 'deg);border-color:' + c + '30;color:' + c + '">'
                      + '<div>' + html.escape(o) + '</div><small>竞品</small></div>')

    # 优势框
    advantages = ('<div class="comp-adv-left"><div class="comp-adv-title" style="color:#3b82f6">专业创作优势</div>'
                  '<ul><li>Seedream图像模型</li><li>全链路功能</li></ul></div>'
                  '<div class="comp-adv-right"><div class="comp-adv-title" style="color:#6366f1">轻量体验优势</div>'
                  '<ul><li>零门槛体验</li><li>短剧Agent</li></ul></div>')

    # 底部挑战
    challenges = ('<div class="comp-challenges"><span class="comp-ch-title"><i>' + icon("zap", 16, "#3b82f6")
                  + '</i>共同挑战</span>'
                  + '<span class="comp-chip">算力成本高企</span>'
                  + '<span class="comp-chip">积分消耗争议</span>'
                  + '<span class="comp-chip">同质化竞争加剧</span></div>')

    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">竞争格局 · 对标关系</span>'
            '<span class="chart-legend">中心=本报告主体，外环=主要竞品</span></div>'
            '<div class="comp-wrap">' + advantages
            + '<div class="comp-center-ring"><div class="comp-ring-outer"></div><div class="comp-ring-inner"></div>'
            + '<div class="comp-main-group">' + main_html + '</div>' + ring_html + '</div>'
            + '</div>' + challenges + '</div>')


# ---------- 市场概览金字塔 ----------
def render_pyramid(market_map):
    """完整三角形金字塔：3 梯队，图标 + 标签 + 产品 + 描述。"""
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

    tier_meta = {
        't1': {'label': '第一梯队 · 头部领跑', 'icon': 'crown', 'desc': '行业绝对领先，产品能力全面，用户规模与商业化表现突出'},
        't2': {'label': '第二梯队 · 强势跟进', 'icon': 'star', 'desc': '产品能力优秀，用户增长迅速，在细分场景具备较强竞争力'},
        't3': {'label': '第三梯队 · 细分突围', 'icon': 'flag', 'desc': '聚焦细分场景或特定用户群体，寻求差异化突破'},
    }

    bands = ""
    for key in ('t1', 't2', 't3'):
        m = tier_meta[key]
        names = '、'.join(tiers[key]) if tiers[key] else '—'
        bands += ('<div class="pyr-band ' + key + '"><div class="pyr-shape"></div>'
                  '<div class="pyr-inner"><div class="pyr-icon">' + icon(m['icon'], 24, "#fff")
                  + '</div><div class="pyr-text"><div class="pyr-label">' + m['label']
                  + '</div><div class="pyr-products">' + html.escape(names) + '</div></div>'
                  '<div class="pyr-desc">' + m['desc'] + '</div></div></div>')

    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">竞争梯队金字塔</span>'
            '<span class="chart-legend">按市场份额/影响力（规模）划分</span></div>'
            '<div class="pyramid-wrap">' + bands + '</div></div>')


# ---------- AI 能力卡 ----------
AI_CARD_ICONS = {
    "底层模型": "cpu", "多模态能力": "layers", "agent能力": "bot", "数字人技术": "user",
    "技术迭代速度": "trending",
}


def render_ai_cards(items):
    cards = ""
    for title, body in items:
        ico = AI_CARD_ICONS.get(title, "sparkle")
        cards += ('<div class="ai-card-v2"><div class="ai-card-accent"></div>'
                  '<div class="ai-card-icon">' + icon(ico, 22, "#3b82f6") + '</div>'
                  '<div class="ai-card-body"><h4>' + html.escape(title)
                  + '</h4><div class="ai-card-line"></div><p>' + html.escape(body) + '</p></div></div>')
    return '<div class="ai-grid-v2">' + cards + '</div>'


# ---------- 增长 ----------
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


# ---------- SWOT ----------
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


# ---------- 通用表格 ----------
def render_table(header, rows):
    th = "".join("<th>" + html.escape(clean(c)) + "</th>" for c in header)
    trs = "".join("<tr>" + "".join("<td>" + html.escape(clean(c)) + "</td>" for c in r) + "</tr>" for r in rows)
    return '<table class="tbl"><thead><tr>' + th + '</tr></thead><tbody>' + trs + '</tbody></table>'


SECTION_ICONS = {
    "执行摘要": "document",
    "市场概览": "globe",
    "产品定位": "target",
    "功能矩阵": "grid",
    "AI 能力": "sparkle",
    "商业模式": "trending",
    "增长": "bar-chart",
    "竞争格局": "network",
    "SWOT": "target",
    "能力雷达": "compass",
    "市场地图": "anchor",
    "时间线": "stack",
    "用户口碑": "people",
    "行动建议": "lightbulb",
    "来源": "paper-plane",
}

SECTION_SUBTITLES = {
    "执行摘要": "核心结论与关键洞察",
    "市场概览": "竞争梯队与市场格局",
    "产品定位": "产品差异化定位对比",
    "功能矩阵": "核心功能覆盖情况",
    "AI 能力": "底层技术与智能化能力",
    "商业模式": "定价与变现结构",
    "增长": "用户规模与增长策略",
    "竞争格局": "主要竞品对标关系",
    "能力雷达": "多维度能力综合评估",
    "市场地图": "产品定位气泡图",
    "用户口碑": "来自真实用户的声音",
    "行动建议": "后续行动优先级",
}

DIMENSION_ICONS = {
    "官方定位": "paper-plane",
    "核心用户": "people",
    "核心价值": "diamond",
    "产品形态": "monitor",
    "差异化标签": "tag",
}


def render_positioning_table(header, rows):
    """产品定位表格：表头带图标、行维度带图标。"""
    header_icons = ["grid", "sparkle", "cloud"]
    ths = ""
    for i, h in enumerate(header):
        ico = header_icons[i] if i < len(header_icons) else "bullet"
        c = product_color(h) if i > 0 else "#3b82f6"
        ths += ('<th><span class="th-icon">' + icon(ico, 20, c)
                + '</span>' + html.escape(clean(h)) + '</th>')
    trs = ""
    for r in rows:
        if not r:
            continue
        dim = clean(r[0]) if r else ""
        ico = DIMENSION_ICONS.get(dim, "bullet")
        cells = ('<td><span class="row-icon">' + icon(ico, 18, "#3b82f6")
                 + '</span>' + html.escape(dim) + '</td>')
        cells += "".join('<td>' + html.escape(clean(c)) + '</td>' for c in r[1:])
        trs += '<tr>' + cells + '</tr>'
    return '<table class="positioning-table"><thead><tr>' + ths + '</tr></thead><tbody>' + trs + '</tbody></table>'


def render_positioning_note(text):
    """产品定位下方的信息条，自动高亮引号内关键词。"""
    text = html.escape(clean(text))
    text = re.sub(r'["""]([^"""]+)["""]', r'<b class="highlight">“\1”</b>', text)
    text = re.sub(r'"([^"]+)"', r'<b class="highlight">"\1"</b>', text)
    return ('<div class="info-box"><span class="info-icon">' + icon("info", 20, "#3b82f6")
            + '</span><div>' + text + '</div></div>')


def render_summary(items):
    """执行摘要：01-06 编号、左侧图标、橙色标题、正文。"""
    icons = ["network", "stack", "crown", "person", "bar-chart", "target"]
    rows = []
    for i, s in enumerate(items):
        s = clean(s)
        label, body = split_kv(s)
        if not label:
            label, body = body[:12], body
        num = str(i + 1).zfill(2)
        ico = icons[i % len(icons)]
        rows.append(
            '<div class="exec-row">'
            + '<div class="exec-icon-box">' + icon(ico, 24, "#3b82f6") + '</div>'
            + '<div class="exec-num">' + num + '</div>'
            + '<div class="exec-main">'
            + '<div class="exec-keyword">' + html.escape(label) + '</div>'
            + '<div class="exec-body">' + html.escape(body) + '</div></div></div>'
        )
    return '<div class="exec-list">' + "".join(rows) + '</div>'


def render_sentiment(items):
    """用户口碑：头像、正负面徽章、产品标签、引用、点赞/点踩。"""
    pos = sum(1 for k, _, _ in items if k == "正面")
    neg = sum(1 for k, _, _ in items if k == "负面")
    tot = pos + neg
    pw = 0 if tot == 0 else round(pos / tot * 100)
    nw = 0 if tot == 0 else round(neg / tot * 100)

    cards = ""
    for idx, (k, prod, t) in enumerate(items):
        cls = "pos" if k == "正面" else "neg"
        thumb = icon("thumbs-up", 18, "#10B981") if cls == "pos" else icon("thumbs-down", 18, "#EF4444")
        cards += ('<div class="sent-row ' + cls + '">'
                  + '<div class="sent-avatar">' + avatar(idx, "#64748b", 56) + '</div>'
                  + '<div class="sent-badge ' + cls + '">' + html.escape(k) + '</div>'
                  + '<div class="sent-prod">' + html.escape(prod) + '</div>'
                  + '<div class="sent-quote">' + html.escape(t) + '</div>'
                  + '<div class="sent-thumb">' + thumb + '</div></div>')

    return ('<div class="chart-card"><div class="chart-header"><span class="chart-title">用户口碑</span>'
            '<span class="chart-legend">样本 ' + str(tot) + ' · 正面 ' + str(pw) + '%</span></div>'
            '<div class="sent-summary">'
            + '<div class="sent-rate"><div class="sent-rate-label">整体好评率</div><div class="sent-rate-value">' + str(pw) + '%</div></div>'
            + '<div class="sent-bar-wrap"><div class="sent-bar"><div class="sent-pos" style="width:' + str(pw) + '%"></div>'
            + '<div class="sent-neg" style="width:' + str(nw) + '%"></div></div>'
            + '<div class="sent-bar-labels"><span>' + icon("smile", 14, "#fff") + ' ' + str(pos) + ' 条好评</span>'
            + '<span>' + icon("sad", 14, "#fff") + ' ' + str(neg) + ' 条建议</span></div></div></div>'
            + '<div class="sent-list">' + cards + '</div></div>')


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
  --bg:#f8fafc;
  --card:#FFFFFF;
  --ink:#1e293b;
  --muted:#64748b;
  --line:#e2e8f0;
  --brand:#3b82f6;
  --brand-light:#93c5fd;
  --brand-ghost:#eff6ff;
  --brand-d:#2563eb;
  --green:#10B981;
  --amber:#f59e0b;
  --red:#ef4444;
  --blue:#3b82f6;
  --purple:#8b5cf6;
  --sidebar:#FFFFFF;
  --sidebar-text:#64748b;
  --sidebar-active:#eff6ff;
  --shadow:0 1px 3px rgba(15,23,42,.08),0 1px 2px rgba(15,23,42,.04);
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.7;font-size:14px;}
.app{display:flex;min-height:100vh;}
.sidebar{width:260px;background:var(--sidebar);color:var(--sidebar-text);position:fixed;left:0;top:0;bottom:0;overflow:auto;padding:28px 22px;z-index:20;}
.brand{font-size:18px;font-weight:700;color:var(--ink);letter-spacing:1px;margin-bottom:8px;}
.brand span{font-weight:400;opacity:.7;}
.brand-sub{font-size:12px;color:var(--sidebar-text);opacity:.7;margin-bottom:32px;}
.nav-list{list-style:none;margin:0;padding:0;}
.nav-list li{margin:6px 0;}
.nav-list a{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:10px;color:var(--sidebar-text);text-decoration:none;font-size:13px;transition:.15s;}
.nav-list a::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--sidebar-text);opacity:.4;}
.nav-list a:hover{background:#f1f5f9;color:var(--ink);}
.nav-list a.active{background:var(--sidebar-active);color:var(--brand-d);font-weight:600;}
.nav-list a.active::before{background:var(--brand);opacity:1;}
.main{margin-left:260px;flex:1;padding:40px 48px 80px;max-width:1100px;}
.top-header{margin-bottom:32px;}
.top-header h1{margin:0;font-size:32px;font-weight:700;line-height:1.25;letter-spacing:.5px;color:var(--ink);}
.top-sub{display:flex;align-items:center;gap:10px;margin-top:8px;font-size:13px;color:var(--muted);}
.assumption-bar{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:28px;}
.stat-card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;display:flex;align-items:center;gap:14px;box-shadow:var(--shadow);}
.stat-icon{flex-shrink:0;width:44px;height:44px;border-radius:12px;background:var(--brand-ghost);display:flex;align-items:center;justify-content:center;color:var(--brand);}
.stat-icon svg{width:22px;height:22px;}
.stat-label{font-size:12px;color:var(--muted);margin-bottom:4px;}
.stat-value{font-size:15px;font-weight:600;color:var(--ink);line-height:1.4;}
section{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:28px 32px;margin-bottom:24px;width:100%;box-shadow:var(--shadow);}
.sec-head{display:flex;align-items:center;gap:12px;margin-bottom:18px;}
.sec-icon{flex-shrink:0;width:42px;height:42px;border-radius:12px;background:var(--brand-ghost);display:flex;align-items:center;justify-content:center;color:var(--brand);}
.sec-icon svg{width:22px;height:22px;}
section h2{margin:0;font-size:22px;font-weight:600;line-height:1.4;color:var(--ink);}
.sec-sub{font-size:13px;color:var(--muted);margin-top:4px;}
section h3{font-size:16px;font-weight:600;color:var(--ink);margin:20px 0 10px;}
section p{margin:8px 0;font-size:14px;color:var(--ink);line-height:1.75;}
section ul,section ol{margin:10px 0;padding-left:22px;color:var(--ink);font-size:14px;line-height:1.75;}
section li{margin:5px 0;}

/* 执行摘要 */
.exec-list{display:flex;flex-direction:column;gap:14px;margin:20px 0 10px;}
.exec-row{display:flex;align-items:flex-start;gap:14px;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 22px;}
.exec-icon-box{flex-shrink:0;width:48px;height:48px;border-radius:14px;background:var(--brand-ghost);display:flex;align-items:center;justify-content:center;color:var(--brand);}
.exec-icon-box svg{width:24px;height:24px;}
.exec-num{flex-shrink:0;font-size:36px;font-weight:800;color:var(--brand);line-height:1;opacity:.22;min-width:44px;text-align:center;padding-top:4px;}
.exec-main{flex:1;display:flex;flex-direction:column;gap:6px;}
.exec-keyword{font-size:15px;font-weight:700;color:var(--brand);line-height:1.5;}
.exec-body{font-size:14px;color:var(--ink);line-height:1.75;}

/* 产品定位 */
.positioning-table{width:100%;border-collapse:separate;border-spacing:0;font-size:14px;margin:14px 0;background:var(--card);border:1px solid var(--line);border-radius:18px;overflow:hidden;}
.positioning-table th{padding:16px 18px;text-align:left;background:#eff6ff;font-weight:600;color:var(--ink);}
.positioning-table th .th-icon{margin-right:8px;display:inline-flex;vertical-align:middle;}
.positioning-table th .th-icon svg{width:20px;height:20px;}
.positioning-table td{padding:16px 18px;border-bottom:1px solid var(--line);color:var(--ink);vertical-align:top;}
.positioning-table tbody tr:last-child td{border-bottom:none;}
.row-icon{color:var(--brand);margin-right:8px;display:inline-flex;vertical-align:middle;}
.row-icon svg{width:18px;height:18px;}
.info-box{display:flex;align-items:flex-start;gap:12px;background:#eff6ff;border-left:4px solid var(--brand);border-radius:12px;padding:16px 18px;margin-top:16px;font-size:14px;color:var(--ink);line-height:1.75;}
.info-box .info-icon{flex-shrink:0;color:var(--brand);}
.info-box .info-icon svg{width:20px;height:20px;}
.info-box b.highlight{color:var(--brand);font-weight:700;}

/* 通用图表卡 */
.chart-card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px 26px;margin:22px 0;}
.chart-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px;}
.chart-title{font-size:16px;font-weight:600;color:var(--ink);}
.chart-legend{font-size:11px;color:var(--muted);background:var(--bg);padding:4px 10px;border-radius:20px;}
.echart{width:100%;height:420px;}

/* 功能矩阵 */
.feature-matrix{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;margin:10px 0;border-radius:14px;overflow:hidden;border:1px solid var(--line);}
.feature-matrix th{padding:14px 16px;background:#eff6ff;font-weight:600;color:var(--ink);text-align:left;border-bottom:1px solid var(--line);}
.feature-matrix td{padding:12px 16px;border-bottom:1px solid var(--line);vertical-align:middle;}
.feature-matrix tbody tr:last-child td{border-bottom:none;}
.feature-matrix td:nth-child(n+2){text-align:center;background:#FFFCF7;}
.fm-prod{display:flex;align-items:center;justify-content:center;gap:8px;font-weight:700;}
.fm-prod-icon{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;}
.fm-prod-icon svg{width:18px;height:18px;}
.fm-row-icon{display:inline-flex;vertical-align:middle;margin-right:8px;color:var(--brand);}
.fm-row-icon svg{width:18px;height:18px;}
.fm-cell{display:flex;align-items:center;justify-content:center;gap:6px;}
.fm-check{width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;}
.fm-check.yes{background:var(--green);}
.fm-check.no{background:var(--red);}
.fm-check.na{background:var(--line);color:var(--muted);font-size:12px;}
.fm-check svg{width:14px;height:14px;}
.fm-note{color:var(--muted);font-size:12px;}
.fm-legend{display:flex;flex-wrap:wrap;align-items:center;gap:24px;margin-top:18px;padding:14px 16px;background:var(--bg);border-radius:12px;}
.fm-leg{display:flex;align-items:center;gap:8px;font-size:13px;}
.fm-leg b{color:var(--ink);font-weight:600;}
.fm-leg span{color:var(--muted);font-size:12px;}
.fm-leg-icon{color:var(--brand);display:inline-flex;}
.fm-leg-icon svg{width:18px;height:18px;}

/* 金字塔 */
.pyramid-wrap{display:flex;flex-direction:column;align-items:center;padding:10px 0;}
.pyr-band{position:relative;width:100%;display:flex;justify-content:center;margin:0;}
.pyr-shape{position:absolute;left:0;right:0;top:0;bottom:0;z-index:0;}
.pyr-band.t1 .pyr-shape{background:linear-gradient(180deg,#3B82F6,#2563EB);clip-path:polygon(50% 0,100% 100%,0 100%);}
.pyr-band.t2 .pyr-shape{background:linear-gradient(180deg,#60A5FA,#3B82F6);clip-path:polygon(25% 0,75% 0,100% 100%,0 100%);}
.pyr-band.t3 .pyr-shape{background:linear-gradient(180deg,#93C5FD,#60A5FA);clip-path:polygon(15% 0,85% 0,100% 100%,0 100%);}
.pyr-band.t1{height:110px;}
.pyr-band.t2{height:100px;margin-top:-1px;}
.pyr-band.t3{height:90px;margin-top:-1px;}
.pyr-inner{position:relative;z-index:1;display:flex;align-items:center;gap:16px;width:80%;max-width:680px;padding:18px 24px;color:#fff;}
.pyr-icon{width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,.25);display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.pyr-icon svg{width:22px;height:22px;}
.pyr-text{min-width:160px;}
.pyr-label{font-size:15px;font-weight:700;}
.pyr-products{font-size:15px;font-weight:700;opacity:.95;margin-top:2px;}
.pyr-desc{font-size:13px;opacity:.9;line-height:1.6;flex:1;}

/* AI 能力卡 */
.ai-grid-v2{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin:16px 0;}
.ai-card-v2{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:0;display:flex;overflow:hidden;}
.ai-card-accent{width:5px;background:var(--brand);flex-shrink:0;}
.ai-card-icon{width:50px;display:flex;align-items:flex-start;justify-content:center;padding-top:18px;flex-shrink:0;color:var(--brand);}
.ai-card-icon svg{width:24px;height:24px;}
.ai-card-body{padding:18px 18px 18px 8px;flex:1;}
.ai-card-body h4{margin:0 0 8px;font-size:16px;font-weight:700;color:var(--ink);}
.ai-card-line{width:32px;height:3px;background:var(--brand);border-radius:2px;margin-bottom:10px;}
.ai-card-body p{margin:0;font-size:13px;color:var(--muted);line-height:1.7;}

/* 增长 */
.growth-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:6px 0;}
.growth-card{background:var(--bg);border-radius:12px;padding:14px 16px;}
.growth-card h4{margin:0 0 6px;font-size:14px;color:var(--brand);} .growth-card p{margin:0;font-size:13px;color:var(--ink);line-height:1.6;}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 4px;}
.chip{background:var(--brand-ghost);color:var(--brand);border-radius:20px;padding:4px 12px;font-size:12px;font-weight:600;}

/* 竞争格局 */
.comp-wrap{position:relative;min-height:360px;display:flex;align-items:center;justify-content:center;margin:10px 0;}
.comp-center-ring{position:relative;width:320px;height:320px;display:flex;align-items:center;justify-content:center;}
.comp-ring-outer{position:absolute;width:100%;height:100%;border:2px dashed var(--line);border-radius:50%;}
.comp-ring-inner{position:absolute;width:60%;height:60%;border:1px dashed var(--line);border-radius:50%;}
.comp-main-group{position:relative;z-index:2;display:flex;gap:16px;}
.comp-main-node{width:110px;height:110px;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;text-align:center;font-weight:700;font-size:14px;box-shadow:0 6px 20px rgba(0,0,0,.12);}
.comp-main-node .comp-main-icon{width:34px;height:34px;margin-bottom:4px;}
.comp-main-node .comp-main-icon svg{width:20px;height:20px;}
.comp-main-node small{font-size:10px;font-weight:400;opacity:.9;}
.comp-node{position:absolute;width:84px;height:84px;border-radius:50%;background:#fff;border:2px solid;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-size:12px;font-weight:600;box-shadow:0 4px 12px rgba(0,0,0,.06);}
.comp-node small{font-size:10px;font-weight:400;opacity:.7;}
.comp-adv-left,.comp-adv-right{position:absolute;top:50%;transform:translateY(-50%);width:170px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 4px 14px rgba(0,0,0,.05);}
.comp-adv-left{left:0;border-left:4px solid var(--brand);}
.comp-adv-right{right:0;border-left:4px solid var(--blue);}
.comp-adv-title{font-size:13px;font-weight:700;margin-bottom:8px;}
.comp-adv-left ul,.comp-adv-right ul{margin:0;padding-left:16px;font-size:12px;color:var(--muted);line-height:1.8;}
.comp-challenges{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:16px;padding:14px 16px;background:var(--bg);border-radius:12px;}
.comp-ch-title{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:700;color:var(--blue);}
.comp-ch-title svg{width:16px;height:16px;}
.comp-chip{background:#fff;border:1px solid var(--line);border-radius:20px;padding:5px 12px;font-size:12px;color:var(--ink);}

/* 市场地图 */
.map-legend{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:16px;}
.map-legend-card{background:var(--bg);border-radius:12px;padding:12px 14px;display:flex;align-items:center;gap:10px;font-size:13px;}
.map-legend-card b{color:var(--ink);font-weight:600;}
.map-legend-card span{color:var(--muted);font-size:12px;}
.map-dot{width:12px;height:12px;border-radius:50%;flex-shrink:0;}

/* 用户口碑 */
.sent-summary{display:flex;align-items:center;gap:24px;margin-bottom:18px;flex-wrap:wrap;}
.sent-rate{min-width:90px;}
.sent-rate-label{font-size:12px;color:var(--muted);}
.sent-rate-value{font-size:36px;font-weight:800;color:var(--brand);line-height:1.1;}
.sent-bar-wrap{flex:1;min-width:260px;}
.sent-bar{display:flex;height:36px;border-radius:18px;overflow:hidden;background:var(--line);}
.sent-pos{background:var(--green);display:flex;align-items:center;justify-content:center;color:#fff;font-size:13px;gap:6px;}
.sent-neg{background:var(--red);display:flex;align-items:center;justify-content:center;color:#fff;font-size:13px;gap:6px;}
.sent-bar-labels{display:flex;justify-content:space-between;margin-top:6px;font-size:12px;color:var(--muted);}
.sent-list{display:flex;flex-direction:column;gap:12px;}
.sent-row{display:flex;align-items:center;gap:12px;background:var(--bg);border-radius:14px;padding:12px 14px;}
.sent-row.pos{border-left:4px solid var(--green);}
.sent-row.neg{border-left:4px solid var(--red);}
.sent-avatar{width:56px;height:56px;flex-shrink:0;color:var(--muted);}
.sent-avatar svg{width:56px;height:56px;}
.sent-badge{flex-shrink:0;font-size:12px;font-weight:700;padding:3px 10px;border-radius:12px;}
.sent-badge.pos{background:#D1FAE5;color:#065F46;}
.sent-badge.neg{background:#FEE2E2;color:#991B1B;}
.sent-prod{flex-shrink:0;font-size:12px;color:var(--muted);background:#fff;border:1px solid var(--line);padding:3px 10px;border-radius:12px;}
.sent-quote{flex:1;font-size:13px;color:var(--ink);line-height:1.6;}
.sent-thumb{flex-shrink:0;}
.sent-thumb svg{width:20px;height:20px;}

/* 能力雷达 */
.radar-wrap{display:flex;gap:24px;align-items:flex-start;}
.radar-wrap .echart{flex:1;min-width:0;height:460px;}
.radar-side{width:260px;flex-shrink:0;display:flex;flex-direction:column;gap:12px;}
.radar-summary-card{display:flex;align-items:center;gap:12px;background:var(--bg);border-radius:14px;padding:14px;}
.radar-sum-icon{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;}
.radar-sum-icon svg{width:20px;height:20px;}
.radar-sum-main{flex:1;}
.radar-sum-title{display:flex;align-items:center;justify-content:space-between;font-size:14px;font-weight:700;color:var(--ink);}
.radar-stars{color:var(--brand);font-size:12px;letter-spacing:1px;}
.radar-stars .star{color:#3b82f6;}
.radar-stars .star.empty{color:#E5E7EB;}
.radar-sum-desc{font-size:12px;color:var(--muted);margin-top:4px;}
.radar-dim-title{font-size:14px;font-weight:700;color:var(--ink);margin:18px 0 12px;display:flex;align-items:center;gap:8px;}
.radar-dim-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;}
.radar-dim{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--ink);background:var(--bg);padding:8px 12px;border-radius:10px;}
.radar-dim-icon{color:var(--brand);display:inline-flex;}
.radar-dim-icon svg{width:16px;height:16px;}

/* 时间线 */
.tl-list{display:flex;flex-direction:column;gap:0;margin:14px 0;border-left:2px solid var(--line);padding-left:0;}
.tl-item{display:flex;gap:16px;padding:10px 0 10px 18px;position:relative;}
.tl-item::before{content:"";position:absolute;left:-7px;top:16px;width:12px;height:12px;border-radius:50%;background:var(--brand);border:2px solid #fff;}
.tl-date{font-size:13px;font-weight:700;color:var(--brand);min-width:96px;flex-shrink:0;}
.tl-text{font-size:13px;color:var(--ink);line-height:1.6;}

/* 优先级看板 */
.pri-row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
.pri-col{background:var(--bg);border-radius:14px;padding:16px;}
.pri-col.m{border-left:4px solid var(--red);} .pri-col.s{border-left:4px solid var(--amber);} .pri-col.c{border-left:4px solid var(--green);}
.pri-h{font-weight:700;font-size:14px;margin-bottom:10px;color:var(--ink);} .pri-col ul{margin:0;padding-left:18px;font-size:13px;color:var(--muted);line-height:1.7;}

/* 来源 */
.src-inline{display:flex;flex-wrap:wrap;gap:8px 20px;margin-top:8px;font-size:13px;line-height:1.9;}
.src-inline a{color:var(--brand);text-decoration:none;}
.src-inline a:hover{text-decoration:underline;}
.src-inline span{color:var(--muted);}

/* 通用表格 */
.tbl{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;margin:10px 0;}
.tbl th,.tbl td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line);}
.tbl th{font-weight:600;color:var(--muted);font-size:12px;background:var(--bg);position:sticky;top:0;}
.tbl tbody tr:hover{background:rgba(59,130,246,.05);}
.tbl tr:last-child td{border-bottom:none;}

/* SWOT */
.swot-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:14px 0;}
.swot-cell{border-radius:12px;padding:14px 16px;}
.swot-cell h4{margin:0 0 6px;font-size:14px;}
.swot-cell p{margin:0;font-size:13px;color:var(--ink);line-height:1.6;}
.swot-cell.s{background:#eff6ff;} .swot-cell.s h4{color:var(--brand);}
.swot-cell.w{background:#FDE8E8;} .swot-cell.w h4{color:var(--red);}
.swot-cell.o{background:#E7F7EF;} .swot-cell.o h4{color:var(--green);}
.swot-cell.t{background:#EFEAFB;} .swot-cell.t h4{color:var(--purple);}

@media(max-width:900px){
  .sidebar{display:none;}
  .main{margin-left:0;padding:24px;max-width:none;}
  .assumption-bar{grid-template-columns:1fr 1fr;}
  .exec-row{flex-direction:column;}
  .exec-num{min-width:auto;text-align:left;}
  .ai-grid-v2{grid-template-columns:1fr;}
  .radar-wrap{flex-direction:column;}
  .radar-side{width:100%;}
  .comp-adv-left,.comp-adv-right{position:static;transform:none;width:100%;margin:10px 0;}
  .comp-wrap{flex-direction:column;min-height:auto;}
  .pyr-inner{flex-direction:column;gap:8px;text-align:center;}
  .pyr-desc{display:none;}
}
@media(max-width:640px){
  .pri-row{grid-template-columns:1fr;}
  .growth-grid{grid-template-columns:1fr;}
  .swot-grid{grid-template-columns:1fr;}
  .feature-matrix td:nth-child(n+2){font-size:11px;}
  .sent-summary{flex-direction:column;align-items:flex-start;}
}
"""


def parse_sections(lines):
    """返回 [(title, level, body_lines)]，标题按出现顺序。"""
    secs = []
    cur = None
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
    positioning_note = []
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
            elif title == '产品定位':
                parts.append(render_positioning_table(header, rows))
            elif title == '功能矩阵':
                parts.append(render_feature_matrix(header, rows))
            elif title == '商业模式':
                parts.append(render_table(header, rows))
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
            if title == '产品定位':
                positioning_note.append(clean(line))
            else:
                parts.append('<p>' + html.escape(clean(line)) + '</p>')
        i += 1

    # 章节专属组装
    if title == '执行摘要':
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
            center = "、".join(names[:2]) if len(names) >= 2 else names[0]
            others = names[2:] if len(names) >= 2 else names[1:]
            mid_state[0] += 1
            parts.append(render_competition_graph(mid_state[0], center, others, market_map))

    if title == '产品定位' and positioning_note:
        parts.append(render_positioning_note(' '.join(positioning_note)))

    sec_ico = SECTION_ICONS.get(title)
    if sec_ico:
        header_html = ('<div class="sec-head"><div class="sec-icon">' + icon(sec_ico, 22, "#3b82f6")
                       + '</div><div><h2>' + html.escape(title) + '</h2>')
        sub = SECTION_SUBTITLES.get(title)
        if sub:
            header_html += '<div class="sec-sub">' + html.escape(sub) + '</div>'
        header_html += '</div></div>'
    else:
        header_html = '<h2>' + html.escape(title) + '</h2>'

    return '<section id="' + section_id(idx) + '">' + header_html + "".join(parts) + '</section>'


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

    # 顶部假设卡
    ASSUMPTION_ICONS = {
        "分析对象": "user",
        "研究意图": "chart-bar",
        "选用维度": "grid",
        "研究深度": "target",
    }
    ASSUMPTION_ORDER = ["分析对象", "研究意图", "选用维度", "研究深度"]

    def assumption_card(k, v):
        ico = ASSUMPTION_ICONS.get(k, "bullet")
        return ('<div class="stat-card"><div class="stat-icon">' + icon(ico, 22, "#3b82f6")
                + '</div><div><div class="stat-label">' + html.escape(k)
                + '</div><div class="stat-value">' + html.escape(v) + '</div></div></div>')

    assumption_bar = ""
    if assumption:
        ordered = []
        for k in ASSUMPTION_ORDER:
            if k in assumption:
                ordered.append((k, assumption[k]))
        for k, v in assumption.items():
            if k not in ASSUMPTION_ORDER:
                ordered.append((k, v))
        assumption_bar = '<div class="assumption-bar">' + "".join(assumption_card(k, v) for k, v in ordered) + '</div>'

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
