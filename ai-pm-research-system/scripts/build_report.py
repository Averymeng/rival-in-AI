#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIPM·瞭望台 · 可视化渲染器（v4 · AI 研究操作系统视觉）

约定写法（Markdown） → 自包含 HTML（ECharts CDN）。

设计语言（v3 · Editorial Strategy Brief）：
  - 暖中性底色 + 深蓝主色（#1E40AF），Inter/PingFang 字体，卡片化、克制的 AI 研究操作系统视觉（Linear / Notion AI / Stripe 风格）
  - 每个章节：编号 + 英文 eyebrow + 中文标题 + 副标题，发丝分隔线
  - 左侧细窄目录（编号 + 标题，无图标），顶部报头（标题 + 研究范围 + 日期）
  - 板块呈现形式严格匹配业务语义：
      执行摘要      → 核心判断 + 编号发现卡
      市场概览      → 导语段 + 竞争梯队金字塔
      产品定位      → 产品档案卡（逐维度对照）
      功能矩阵      → 能力覆盖矩阵 + 覆盖率小结
      AI 能力       → 能力模块卡（含评分矩阵时渲染雷达）
      商业模式      → 会员体系卡 + 变现结构对照
      增长          → KPI 指标卡（抽取关键数字）
      竞争格局      → 中心-竞品辐射关系图
      SWOT          → 2×2 象限矩阵
      能力雷达      → 多边形雷达 + 综合评分条形
      市场地图/机会 → 面积气泡定位图
      时间线        → 编年轨
      用户口碑      → 好评率 + 引述卡
      行动建议      → Must/Should/Could 优先级看板
      来源          → 编号参考文献
  - 全文中禁止出现原始 Markdown 符号（- ** 等）
"""
import sys, re, json, html, argparse, datetime, math

# 分类色板（竞品/维度区分，克制且专业）
CAT = ["#1E40AF", "#14B8A6", "#8B5CF6", "#0EA5E9", "#F59E0B"]

SCATTER_TOOLTIP = "function(p){return p.data.name+'<br/>专业能力：'+p.data.value[0]+'<br/>功能深度：'+p.data.value[1]+'<br/>规模：'+p.data.value[2];}"
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
    "compass": '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "anchor": '<circle cx="12" cy="5" r="3"/><line x1="12" y1="22" x2="12" y2="8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/>',
}

# 功能/维度 -> 图标 映射
FEATURE_ICONS = {
    "文生图": "image", "图生图": "image", "编辑": "figma", "文生视频": "video", "图生视频": "video",
    "数字人": "user", "音乐生成": "music", "配音生成": "mic", "动作模仿": "person",
    "agent模式": "bot", "agent": "bot", "爆款复刻": "copy", "照片会说话": "smile",
    "白模渲染": "layers", "octo协作": "people", "多模态": "layers", "底层模型": "cpu",
    "免费策略": "mail", "基础会员": "tag", "标准会员": "tag", "高级会员": "tag",
    "积分消耗": "zap", "api服务": "anchor", "变现结构": "trending",
    "运动": "zap", "物理仿真": "cpu", "4k": "monitor", "镜头控制": "target",
}
RADAR_DIM_ICONS = {
    "图像生成": "image", "视频生成": "video", "多模态能力": "layers", "agent智能化": "bot",
    "易用性": "smile", "功能丰富度": "grid", "商业化成熟度": "trending", "生态协同": "network",
    "用户口碑": "people", "迭代速度": "zap", "ai能力": "cpu", "产品与核心功能": "star",
    "数据壁垒": "shield", "技术与生态": "compass", "商业模式与定价": "trending", "用户体验": "smile",
    "增长与运营": "trending",
}
DIMENSION_ICONS = {
    "官方定位": "paper-plane", "核心用户": "people", "核心价值": "diamond",
    "产品形态": "monitor", "差异化标签": "tag",
}
AI_CARD_ICONS = {
    "底层模型": "cpu", "多模态能力": "layers", "agent能力": "bot", "数字人技术": "user",
    "技术迭代速度": "trending",
}
SECTION_EN = {
    "执行摘要": "EXECUTIVE SUMMARY", "市场概览": "MARKET OVERVIEW", "产品定位": "POSITIONING",
    "功能矩阵": "CAPABILITY MATRIX", "AI 能力": "AI CAPABILITIES", "商业模式": "BUSINESS MODEL",
    "增长": "GROWTH & TRACTION", "增长与运营": "GROWTH & OPERATIONS",
    "竞争格局": "COMPETITIVE LANDSCAPE", "SWOT": "SWOT ANALYSIS", "能力雷达": "CAPABILITY RADAR",
    "市场地图": "MARKET MAP", "机会": "OPPORTUNITY MAP", "时间线": "TIMELINE",
    "用户口碑": "USER VOICE", "行动建议": "RECOMMENDATIONS", "来源": "SOURCES",
}
SECTION_SUBTITLES = {
    "执行摘要": "核心结论与关键洞察", "市场概览": "赛道格局与竞争梯队",
    "产品定位": "差异化定位对照", "功能矩阵": "核心能力覆盖情况",
    "AI 能力": "底层技术与智能化能力", "商业模式": "定价结构与变现路径",
    "增长": "用户规模与增长动能", "增长与运营": "用户规模与增长动能",
    "竞争格局": "主要竞品对标关系", "SWOT": "优势 / 劣势 / 机会 / 威胁",
    "能力雷达": "多维度能力综合评估", "市场地图": "产品定位气泡图",
    "机会": "待填补的空白方向", "时间线": "关键节点编年", "用户口碑": "来自真实用户的声音",
    "行动建议": "后续行动优先级", "来源": "数据来源与参考",
}


def icon(name, size=18, color="#1E40AF"):
    path = ICON_PATHS.get(name, ICON_PATHS["bullet"])
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{path}</svg>')


def clean(s):
    s = s.strip()
    s = re.sub(r'^[-·*]\s*', '', s)
    s = s.replace('**', '').replace('`', '').replace('*', '')
    return s.strip()


def split_kv(s):
    m = re.match(r'^([^：:]{1,24})[：:]\s*(.*)$', s.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return '', s.strip()


# ---------- 表格解析 ----------
def parse_tables(lines):
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
                rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in block[2:]]
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

    def is_x(h):
        h = h.strip()
        return h == 'X' or re.match(r'^X[（(]', h) is not None

    def is_y(h):
        h = h.strip()
        return h == 'Y' or re.match(r'^Y[（(]', h) is not None

    if not (any(is_x(h) for h in header) and any(is_y(h) for h in header)):
        return False
    xi = next(i for i, h in enumerate(header) if is_x(h))
    yi = next(i for i, h in enumerate(header) if is_y(h))
    for r in rows:
        if len(r) <= max(xi, yi):
            continue
        if not re.match(r'^\d+(\.\d+)?$', r[xi]) or not re.match(r'^\d+(\.\d+)?$', r[yi]):
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


# ---------- 颜色 ----------
def product_color(name):
    return CAT[abs(hash(name)) % len(CAT)]


def product_icon(name):
    for k, v in (("即梦", "sparkle"), ("小云雀", "cloud"), ("可灵", "video"),
                 ("runway", "film"), ("sora", "sparkle"), ("cursor", "monitor"),
                 ("dify", "layers"), ("codex", "cpu")):
        if k.lower() in name.lower():
            return v
    return "monitor"


def score_bg(v):
    if v >= 4:
        return "#EFF6FF", "#1E3A8A"
    if v >= 2.5:
        return "#F1F5F9", "#475569"
    return "#FEE2E2", "#B91C1C"


# ---------- 功能矩阵 ----------
def parse_feature_cell(cell):
    """返回 (state, note)，state ∈ yes/partial/no/na。
    放宽匹配：不再只看首字，而是在整格中检索关键词，兼容「支持/有/有限/高/低/英文」等真实写法。"""
    raw = cell.strip()
    note = re.sub(r'^[✅✔❌✗×是否强中弱部分半一般无未]+\s*', '', raw).strip()
    note = note.strip('（）()（）')
    if not raw:
        return None, note
    if re.search(r'不支持|无|未|否|缺少|缺失|不提供|不具备|没', raw):
        return 'no', note
    if re.search(r'部分|有限|中|弱|半|一般|基础|初步|轻度', raw):
        return 'partial', note
    if re.search(r'支持|有|强|高|✓|✔|具备|提供|完整|是|可用|覆盖', raw):
        return 'yes', note
    return None, note


def render_feature_matrix(header, rows):
    products = [clean(h) for h in header[1:]]
    cov = [0] * len(products)
    total = 0
    ths = '<th class="fm-feat">功能模块</th>'
    for p in products:
        c = product_color(p)
        ths += (f'<th style="color:{c}"><span class="fm-ph" style="background:{c}1a;color:{c}">'
                + html.escape(p) + '</span></th>')
    trs = ""
    for r in rows:
        if not r:
            continue
        total += 1
        fname = clean(r[0])
        ico = FEATURE_ICONS.get(fname, "bullet")
        cells = ('<td class="fm-feat"><span class="fm-fi">' + icon(ico, 16, "#1E40AF")
                 + '</span>' + html.escape(fname) + '</td>')
        for pi, c in enumerate(r[1:]):
            st, note = parse_feature_cell(c)
            if st == 'yes':
                cov[pi] += 1
                mark = '<span class="fm-dot yes">' + icon("check", 12, "#fff") + '</span>'
            elif st == 'partial':
                mark = '<span class="fm-dot partial">' + icon("star", 12, "#fff") + '</span>'
            elif st == 'no':
                mark = '<span class="fm-dot no">' + icon("x", 12, "#fff") + '</span>'
            else:
                mark = '<span class="fm-dot na">–</span>'
            note_html = f'<span class="fm-note">{html.escape(note)}</span>' if note else ''
            stcls = st if st else 'na'
            cells += f'<td class="fm-cell {stcls}">{mark}{note_html}</td>'
        trs += '<tr>' + cells + '</tr>'

    # 覆盖率小结
    cov_html = ""
    for pi, p in enumerate(products):
        c = product_color(p)
        pct = round(cov[pi] / total * 100) if total else 0
        cov_html += ('<div class="fm-cov"><span class="fm-cov-name" style="color:{0}">{1}</span>'
                     '<span class="fm-cov-bar"><i style="width:{2}%;background:{0}"></i></span>'
                     '<span class="fm-cov-pct">{2}%</span></div>').format(c, html.escape(p), pct)

    return ('<div class="matrix-card"><table class="feature-matrix"><thead><tr>' + ths
            + '</tr></thead><tbody>' + trs + '</tbody></table>'
            + '<div class="fm-cov-wrap"><span class="fm-cov-title">功能覆盖率</span>' + cov_html + '</div>'
            + '<div class="fm-legend"><span><i class="lg yes"></i>强</span>'
            + '<span><i class="lg partial"></i>中</span>'
            + '<span><i class="lg no"></i>小</span></div></div>')


# ---------- 能力雷达 ----------
def render_score_matrix(mid, header, rows):
    dims = header[1:]
    objects = [clean(r[0]) for r in rows]
    matrix = []
    for r in rows:
        vals = [float(v) if re.match(r'^\d+(\.\d+)?$', v) else 0 for v in r[1:]]
        matrix.append(vals)
    indicators = [{"name": d, "max": 5} for d in dims]

    # 颜色层级：主体高识别度 AI 紫，竞品降饱和
    MAIN_C = "#1E40AF"
    COMP_C = ["#94A3B8", "#CBD5E1", "#93C5FD"]
    def obj_color(oi):
        return MAIN_C if oi == 0 else COMP_C[(oi - 1) % len(COMP_C)]

    radar_data = []
    for oi, obj in enumerate(objects):
        c = obj_color(oi)
        d = {"name": obj, "value": matrix[oi],
             "lineStyle": {"color": c, "width": 3 if oi == 0 else 1.8},
             "itemStyle": {"color": c}, "symbolSize": 7 if oi == 0 else 4}
        if oi == 0:
            d["areaStyle"] = {"color": c, "opacity": 0.18}
        radar_data.append(d)

    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item"},
        "radar": {
            "indicator": indicators, "radius": "72%", "center": ["50%", "48%"],
            "axisName": {"color": "#666666", "fontSize": 12},
            "splitNumber": 4,
            "splitLine": {"lineStyle": {"color": "#ECECEC"}},
            "axisLine": {"lineStyle": {"color": "#ECECEC"}},
            "splitArea": {"areaStyle": {"color": ["rgba(255,255,255,0)", "rgba(0,0,0,0.018)"]}}
        },
        "series": [{"type": "radar", "data": radar_data}]
    }
    avg0 = sum(matrix[0]) / len(matrix[0]) if matrix else 0
    opt["graphic"] = [{"type": "text", "left": "center", "top": "40%",
                       "style": {"text": f"{avg0:.1f}", "fontSize": 34, "fontWeight": "bold",
                                 "fill": "#1E40AF", "textAlign": "center"}},
                      {"type": "text", "left": "center", "top": "50%",
                       "style": {"text": "AI 能力分", "fontSize": 11, "fill": "#999999", "textAlign": "center"}}]

    # 右侧：主体对象各能力维度评分（进度条 + 分数 + 状态色）
    score_items = ""
    main_obj = objects[0] if objects else ""
    for j, d in enumerate(dims):
        v = matrix[0][j] if matrix else 0
        bg, fg = score_bg(v)
        pct = (v / 5.0) * 100
        score_items += ('<div class="score-item">'
                        '<div class="si-top"><span class="si-name">' + html.escape(d)
                        + '</span><span class="si-score" style="color:' + fg + '">' + f'{v:.1f}' + '</span></div>'
                        '<div class="si-bar"><i style="width:' + f'{pct:.0f}' + '%;background:' + fg + '"></i></div>'
                        '</div>')

    # 底部：竞品对象图例（全局对比索引）
    legend_items = ""
    for oi, obj in enumerate(objects):
        c = obj_color(oi)
        tag = "分析主体" if oi == 0 else "竞品"
        legend_items += ('<span class="cmp-chip"><i style="background:' + c + '"></i>'
                         + html.escape(obj) + '<small>' + tag + '</small></span>')

    return ('<div class="chart-card"><div class="chart-head"><span class="chart-title">多维能力图谱</span>'
            '<span class="chart-note">5=领先 · 3=平均 · 1=基本不覆盖</span></div>'
            '<div class="radar-dash">'
            '<div class="radar-main"><div id="radar_' + str(mid) + '" class="echart"></div></div>'
            '<div class="score-panel"><div class="sp-title">能力评分 · ' + html.escape(main_obj) + '</div>'
            + score_items + '</div>'
            '</div>'
            '<div class="cmp-legend">' + legend_items + '</div></div>\n'
            '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("radar_'
            + str(mid) + '"));c.setOption(' + json.dumps(opt, ensure_ascii=False)
            + ');REG.push(c);});</script>')


# ---------- 市场地图 / 机会地图（四象限定位图） ----------
def _quadrant_labels(xs, ys):
    """四象限标签随坐标轴语义自适应：避免换轴后仍显示『领先区/规模区』等错位文案。"""
    s = (xs or "") + "·" + (ys or "")
    if "广度" in s or "深度" in s:
        return ("全能型", "专精型", "广度型", "缝隙型")          # 右·上 / 左·上 / 右·下 / 左·下
    if any(k in s for k in ("规模", "份额", "市场")):
        return ("领先区", "潜力区", "规模区", "利基区")
    # 通用兜底：按轴方向描述，保证永不出现语义错位的固定词
    return (f"高{ys}·高{xs}", f"低{xs}·高{ys}", f"高{xs}·低{ys}", f"低{xs}·低{ys}")


def render_scatter(mid, header, rows, title):
    xs = header[1] if len(header) > 1 and header[1] else "X 维度"
    ys = header[2] if len(header) > 2 and header[2] else "Y 维度"
    pts = []
    for i, r in enumerate(rows):
        if len(r) < 3:
            continue
        try:
            x = float(r[1]); y = float(r[2])
            s = float(r[3]) if len(r) > 3 and str(r[3]).strip() != "" else 1
        except Exception:
            continue
        c = "#1E40AF" if i == 0 else "#CBD5E1"
        pts.append({"name": r[0], "value": [x, y],
                    "symbolSize": 24 + (s or 1) * 9,
                    "itemStyle": {"color": c, "opacity": 0.92, "borderColor": "#fff", "borderWidth": 2},
                    "label": {"show": True, "formatter": "{b}", "position": "bottom",
                              "color": "#171717", "fontSize": 11, "fontWeight": "600"}})
    if not pts:
        return ('<div class="chart-card"><div class="chart-head"><span class="chart-title">' + html.escape(title)
                + '</span></div><div class="chart-empty">暂无可定位的产品数据——请检查市场地图表格是否包含「名称 / '
                + html.escape(xs) + ' / ' + html.escape(ys) + '」三列数值。</div></div>')
    opt = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "{b}<br/>{c}"},
        "grid": {"left": "10%", "right": "8%", "top": "11%", "bottom": "13%"},
        "xAxis": {"type": "value", "name": xs, "nameLocation": "middle", "nameGap": 30,
                  "nameTextStyle": {"color": "#666666"}, "min": 0, "max": 10,
                  "axisLabel": {"color": "#666666"}, "axisLine": {"lineStyle": {"color": "#E8E6E1"}},
                  "splitLine": {"lineStyle": {"color": "#EFEFEF", "type": "dashed"}}},
        "yAxis": {"type": "value", "name": ys, "nameTextStyle": {"color": "#666666"},
                  "min": 0, "max": 10, "axisLabel": {"color": "#666666"},
                  "axisLine": {"lineStyle": {"color": "#E8E6E1"}},
                  "splitLine": {"lineStyle": {"color": "#EFEFEF", "type": "dashed"}}},
        "series": [{
            "type": "scatter", "data": pts,
            "markLine": {"silent": True, "symbol": "none",
                         "lineStyle": {"color": "#E8E6E1", "type": "solid", "width": 1.5},
                         "data": [{"xAxis": 5}, {"yAxis": 5}]},
            "markArea": {"silent": True, "itemStyle": {"color": "rgba(30,64,175,0.05)"},
                         "data": [[{"coord": [5, 5]}, {"coord": [10, 10]}]]}
        }]
    }
    _ql = _quadrant_labels(xs, ys)
    opt["graphic"] = [
        {"type": "text", "right": "7%", "top": "9%", "style": {"text": _ql[0], "fontSize": 12, "fill": "#999999"}},
        {"type": "text", "left": "10%", "top": "9%", "style": {"text": _ql[1], "fontSize": 12, "fill": "#999999"}},
        {"type": "text", "right": "7%", "bottom": "11%", "style": {"text": _ql[2], "fontSize": 12, "fill": "#999999"}},
        {"type": "text", "left": "10%", "bottom": "11%", "style": {"text": _ql[3], "fontSize": 12, "fill": "#999999"}}
    ]
    opt_json = json.dumps(opt, ensure_ascii=False)
    return ('<div class="chart-card"><div class="chart-head"><span class="chart-title">' + html.escape(title)
            + '</span><span class="chart-note">气泡位置 = 定位 · 主分析对象深蓝高亮，竞品灰色</span></div>'
            + '<div id="scatter_' + str(mid) + '" class="echart"></div></div>\n'
            + '<script>window.addEventListener("load",function(){var c=echarts.init(document.getElementById("scatter_'
            + str(mid) + '"));c.setOption(' + opt_json + ');REG.push(c);});</script>')


# ---------- 市场概览金字塔（梯队） ----------
def render_pyramid(market_map):
    try:
        items = [(r[0], float(r[3])) for r in market_map[2] if len(r) >= 4]
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
    meta = {
        't1': ('第一梯队', '头部领跑', '行业绝对领先，能力全面、规模与商业化突出'),
        't2': ('第二梯队', '强势跟进', '能力优秀、增长迅速，细分场景具强竞争力'),
        't3': ('第三梯队', '细分突围', '聚焦特定场景或用户群，寻求差异化突破'),
    }
    bands = ""
    for key in ('t1', 't2', 't3'):
        label, tag, desc = meta[key]
        names = '、'.join(tiers[key]) if tiers[key] else '—'
        bands += ('<div class="pyr-band ' + key + '"><div class="pyr-txt">'
                  + '<div class="pyr-label">' + label + '<span>' + tag + '</span></div>'
                  + '<div class="pyr-names">' + html.escape(names) + '</div>'
                  + '<div class="pyr-desc">' + desc + '</div></div></div>')
    return ('<div class="chart-card"><div class="chart-head"><span class="chart-title">竞争梯队金字塔</span>'
            '<span class="chart-note">按市场规模 / 影响力划分</span></div>'
            '<div class="pyramid">' + bands + '</div></div>')


# ---------- AI 能力卡 ----------
def render_ai_cards(items):
    cards = ""
    for i, (title, body) in enumerate(items):
        ico = AI_CARD_ICONS.get(title, "sparkle")
        cards += ('<div class="ai-card"><span class="ai-idx">' + str(i + 1).zfill(2) + '</span>'
                  + '<div class="ai-icon">' + icon(ico, 20, "#1E40AF") + '</div>'
                  + '<div class="ai-body"><h4>' + html.escape(title) + '</h4><p>' + html.escape(body) + '</p></div></div>')
    return '<div class="ai-grid">' + cards + '</div>'


# ---------- 商业模式：会员体系卡 + 变现结构 ----------
TIER_LABELS = ['免费策略', '基础会员', '标准会员', '高级会员']
TIER_TAG = {'免费策略': '免费', '基础会员': '入门', '标准会员': '标准', '高级会员': '高级'}


def render_business_model(header, rows):
    products = [clean(h) for h in header[1:]]
    tiers = {p: {} for p in products}
    extras = []
    for r in rows:
        if not r:
            continue
        dim = clean(r[0])
        vals = [clean(v) for v in r[1:]]
        if dim in TIER_LABELS:
            for pi, p in enumerate(products):
                tiers[p][dim] = vals[pi] if pi < len(vals) else ''
        else:
            extras.append((dim, vals))
    cols = ""
    for p in products:
        c = product_color(p)
        tier_cards = ""
        for t in TIER_LABELS:
            v = tiers[p].get(t, '')
            if not v:
                continue
            tier_cards += ('<div class="plan"><span class="plan-tag" style="background:{0}1a;color:{0}">{1}</span>'
                           '<span class="plan-val">{2}</span></div>').format(c, TIER_LABELS.index(t) and TIER_TAG[t] or TIER_TAG[t], html.escape(v))
        cols += ('<div class="biz-col"><div class="biz-ph" style="border-color:{0}"><span class="biz-dot" style="background:{0}"></span>{1}</div>'
                 '{2}</div>').format(c, html.escape(p), tier_cards)
    extra_html = ""
    if extras:
        rows_html = ""
        for dim, vals in extras:
            cells = "".join('<td>' + html.escape(vals[pi] if pi < len(vals) else '') + '</td>'
                            for pi in range(len(products)))
        extra_html = ('<div class="biz-extra"><div class="biz-extra-title">变现结构对照</div>'
                      '<table class="biz-table"><thead><tr><th>' + html.escape(clean('维度'))
                      + '</th>' + ''.join('<th>' + html.escape(p) + '</th>' for p in products)
                      + '</tr></thead><tbody>'
                      + ''.join('<tr><td class="bk">' + html.escape(dim) + '</td>' + cells + '</tr>' for dim, vals in extras)
                      + '</tbody></table></div>')
    return '<div class="biz-wrap">' + cols + '</div>' + extra_html


# ---------- 增长：KPI 指标卡 ----------
NUM_RE = re.compile(r'(\d+(?:\.\d+)?\s*(?:万|亿|%|次|万次|万月|万+|个|倍|元|月))')


def render_growth(items):
    cards = ""
    for title, body in items:
        m = NUM_RE.search(body)
        num = m.group(1) if m else ''
        cards += ('<div class="kpi"><div class="kpi-num">' + html.escape(num) + '</div>'
                  + '<div class="kpi-label">' + html.escape(title) + '</div>'
                  + '<div class="kpi-desc">' + html.escape(body) + '</div></div>')
    return '<div class="kpi-grid">' + cards + '</div>'


# ---------- 竞争格局：中心-竞品辐射图 ----------
def render_competition_graph(mid, center, others):
    mains = [x.strip() for x in center.split('、')] if '、' in center else [center]
    items = [("m", x) for x in mains] + [("c", x) for x in others]
    N = len(items)
    if N < 2:
        return ''
    W = H = 420
    cx = cy = W // 2
    R = 165
    positions = []
    for i, (kind, name) in enumerate(items):
        ang = -90 + 360.0 * i / N
        rad = math.radians(ang)
        x = cx + R * math.cos(rad)
        y = cy + R * math.sin(rad)
        positions.append((kind, name, x, y))
    line_elems = []
    for kind, name, x, y in positions:
        if kind == 'm':
            continue
        line_elems.append('<line x1="%d" y1="%d" x2="%.1f" y2="%.1f" stroke="#E2E8F0" stroke-width="1.5"/>'
                          % (cx, cy, x, y))
    svg = ('<svg class="comp-svg" viewBox="0 0 %d %d" width="%d" height="%d">%s'
           '<circle cx="%d" cy="%d" r="6" fill="#1E40AF"/></svg>'
           % (W, H, W, H, ''.join(line_elems), cx, cy))
    nodes = ""
    for kind, name, x, y in positions:
        if kind == 'm':
            nodes += ('<div class="comp-core" style="left:{0:.1f}px;top:{1:.1f}px">{2}<small>本报告主体</small></div>'
                      .format(x, y, html.escape(name)))
        else:
            nodes += ('<div class="comp-sat" style="left:{0:.1f}px;top:{1:.1f}px">{2}</div>'
                      .format(x, y, html.escape(name)))
    return ('<div class="chart-card"><div class="chart-head"><span class="chart-title">竞争辐射关系</span>'
            '<span class="chart-note">中心 = 主体 · 外环 = 主要竞品</span></div>'
            '<div class="comp-stage">' + svg + nodes + '</div></div>')


# ---------- SWOT 2x2 ----------
SWOT_MAP = {'优势': 's', '劣势': 'w', '机会': 'o', '威胁': 't',
            's': 's', 'w': 'w', 'o': 'o', 't': 't'}


def render_swot_table(header, rows):
    cells = {'s': '', 'w': '', 'o': '', 't': ''}
    for r in rows:
        if len(r) < 2:
            continue
        dim = clean(r[0])
        key = None
        for k, v in SWOT_MAP.items():
            if k in dim:
                key = v
                break
        if not key:
            continue
        body = ''.join('<div class="sw-line">' + html.escape(clean(x)) + '</div>' for x in r[1:] if clean(x))
        cells[key] += ('<div class="sw-cell ' + key + '"><div class="sw-h">' + html.escape(clean(dim))
                       + '</div>' + body + '</div>')
    if not any(cells.values()):
        return ''
    return ('<div class="swot"><div class="swot-grid">'
            + (cells['s'] or '<div class="sw-cell s"><div class="sw-h">优势</div></div>')
            + (cells['w'] or '<div class="sw-cell w"><div class="sw-h">劣势</div></div>')
            + (cells['o'] or '<div class="sw-cell o"><div class="sw-h">机会</div></div>')
            + (cells['t'] or '<div class="sw-cell t"><div class="sw-h">威胁</div></div>')
            + '</div></div>')


def render_swot_bullets(items):
    cells = {'s': '', 'w': '', 'o': '', 't': ''}
    for raw in items:
        m = re.match(r'^(优势|劣势|机会|威胁)\s*[（(]?\s*([SsWwOoTt]?)\s*[）)]?\s*[：:]?\s*(.*)$', raw)
        if not m:
            continue
        key = {'优势': 's', '劣势': 'w', '机会': 'o', '威胁': 't'}.get(m.group(1), 's')
        cells[key] += '<div class="sw-line">' + html.escape(clean(m.group(3))) + '</div>'
    grid = ('<div class="sw-cell s"><div class="sw-h">优势 S</div>' + (cells['s'] or '<div class="sw-line">—</div>') + '</div>'
            + '<div class="sw-cell w"><div class="sw-h">劣势 W</div>' + (cells['w'] or '<div class="sw-line">—</div>') + '</div>'
            + '<div class="sw-cell o"><div class="sw-h">机会 O</div>' + (cells['o'] or '<div class="sw-line">—</div>') + '</div>'
            + '<div class="sw-cell t"><div class="sw-h">威胁 T</div>' + (cells['t'] or '<div class="sw-line">—</div>') + '</div>')
    return '<div class="swot"><div class="swot-grid">' + grid + '</div></div>'


# ---------- 通用 ----------
def render_table(header, rows):
    th = "".join("<th>" + html.escape(clean(c)) + "</th>" for c in header)
    trs = "".join("<tr>" + "".join("<td>" + html.escape(clean(c)) + "</td>" for c in r) + "</tr>" for r in rows)
    return '<div class="tbl-wrap"><table class="tbl"><thead><tr>' + th + '</tr></thead><tbody>' + trs + '</tbody></table></div>'


def render_positioning_table(header, rows):
    ths = '<th class="pos-dim">维度</th>'
    for h in header[1:]:
        c = product_color(clean(h))
        ths += '<th style="color:{0}"><span class="pos-ph" style="background:{0}1a;color:{0}">{1}</span></th>'.format(c, html.escape(clean(h)))
    trs = ""
    for r in rows:
        if not r:
            continue
        dim = clean(r[0])
        ico = DIMENSION_ICONS.get(dim, "bullet")
        cells = '<td class="pos-dim"><span class="pos-di">' + icon(ico, 16, "#1E40AF") + '</span>' + html.escape(dim) + '</td>'
        cells += "".join('<td>' + html.escape(clean(c)) + '</td>' for c in r[1:])
        trs += '<tr>' + cells + '</tr>'
    return '<div class="tbl-wrap"><table class="pos-table"><thead><tr>' + ths + '</tr></thead><tbody>' + trs + '</tbody></table></div>'


def render_positioning_note(text):
    text = html.escape(clean(text))
    text = re.sub(r'["""]([^"""]+)["""]', r'<b>\1</b>', text)
    return '<div class="callout"><span class="callout-bar"></span><div>' + text + '</div></div>'


def render_summary(items):
    """执行摘要：首条作核心判断，其余作编号 Insight Card。"""
    cards = ""
    for i, s in enumerate(items):
        s = clean(s)
        label, body = split_kv(s)
        text = body if body else s
        kw = label if label else ''
        cards += ('<div class="finding"><span class="find-num">' + str(i + 1).zfill(2) + '</span>'
                  + '<div class="find-body"><span class="find-kw">' + html.escape(kw) + '</span>'
                  + '<span class="find-text">' + html.escape(text) + '</span></div>'
                  + '<div class="find-ev"><span class="ev-badge high">公开检索</span>'
                  + '<span class="ev-conf">来源可溯源</span></div></div>')
    return '<div class="findings">' + cards + '</div>'


def render_sentiment(items):
    pos = sum(1 for k, _, _ in items if k == '正面')
    neg = sum(1 for k, _, _ in items if k == '负面')
    tot = pos + neg
    pw = 0 if tot == 0 else round(pos / tot * 100)
    nw = 100 - pw
    cards = ""
    for idx, (k, prod, t) in enumerate(items):
        cls = 'pos' if k == '正面' else 'neg'
        mono = (prod[:1] if prod else (k[:1]))
        cards += ('<div class="voice ' + cls + '">'
                  + '<div class="voice-mono" style="background:' + ('#14B8A6' if cls == 'pos' else '#EF4444') + '20;color:'
                  + ('#14B8A6' if cls == 'pos' else '#EF4444') + '">' + html.escape(mono) + '</div>'
                  + '<div class="voice-main"><div class="voice-meta"><span class="voice-badge ' + cls + '">'
                  + html.escape(k) + '</span>' + (('<span class="voice-prod">' + html.escape(prod) + '</span>') if prod else '')
                  + '</div><div class="voice-quote">' + html.escape(t) + '</div></div></div>')
    return ('<div class="chart-card"><div class="chart-head"><span class="chart-title">用户口碑</span>'
            '<span class="chart-note">样本 ' + str(tot) + ' 条</span></div>'
            '<div class="sent-bar"><i class="sent-pos" style="width:' + str(pw) + '%"></i>'
            '<i class="sent-neg" style="width:' + str(nw) + '%"></i></div>'
            '<div class="sent-legend"><span><i class="dot pos"></i>正面 ' + str(pos) + '</span>'
            '<span><i class="dot neg"></i>负面 / 建议 ' + str(neg) + '</span>'
            '<span class="sent-pw">好评率 ' + str(pw) + '%</span></div>'
            '<div class="voice-list">' + cards + '</div></div>')


def render_priority(must, should, could):
    def col(title, items, cls, color):
        lis = "".join('<li>' + html.escape(x) + '</li>' for x in items)
        return ('<div class="pri-col ' + cls + '"><div class="pri-h" style="border-color:' + color + ';color:' + color + '">'
                + title + '</div><ul>' + lis + '</ul></div>')
    return ('<div class="pri"><div class="pri-row">'
            + col("Must · 必做", must, "m", "#1E40AF")
            + col("Should · 应做", should, "s", "#F59E0B")
            + col("Could · 可做", could, "c", "#7C3AED") + '</div></div>')


def render_source_inline(rows):
    cred_map = {'高': 'high', '中': 'mid', '低': 'low'}
    links = ""
    for i, r in enumerate(rows):
        if len(r) < 2:
            continue
        nm = clean(r[0]); lk = r[-1].strip()
        cred = 'mid'
        mm = re.search(r'[（(\[]\s*(高|中|低)\s*[）)\]]', nm)
        if mm:
            cred = cred_map[mm.group(1)]
            nm = (nm[:mm.start()] + nm[mm.end():]).strip()
        dom = ''
        m = re.match(r'https?://([^/]+)', lk)
        if m:
            dom = m.group(1)
        badge = '<span class="cred ' + cred + '">' + ('高' if cred == 'high' else '中' if cred == 'mid' else '低') + '</span>'
        if lk.startswith('http'):
            links += ('<div class="ref"><span class="ref-no">' + str(i + 1) + '</span>'
                      + '<a href="' + lk + '" target="_blank" rel="noopener">' + html.escape(nm) + '</a>'
                      + '<span class="ref-dom">' + html.escape(dom) + '</span>' + badge + '</div>')
        else:
            links += ('<div class="ref"><span class="ref-no">' + str(i + 1) + '</span>'
                      + '<span>' + html.escape(nm) + '</span>' + badge + '</div>')
    return '<div class="ref-list">' + links + '</div>'


def render_timeline(items):
    nodes = ""
    last_year = ""
    for d, t in items:
        yr = re.match(r'(\d{4})', d)
        yr = yr.group(1) if yr else ''
        year_tag = ''
        if yr and yr != last_year:
            year_tag = '<div class="tl-year">' + yr + '</div>'
            last_year = yr
        nodes += ('<div class="tl-node">' + year_tag
                  + '<span class="tl-dot"></span>'
                  + '<div class="tl-card"><div class="tl-date">' + html.escape(d) + '</div>'
                  + '<div class="tl-text">' + html.escape(t) + '</div></div></div>')
    return '<div class="timeline-h"><div class="tl-track">' + nodes + '</div></div>'


# ---------- 样式 ----------
CSS = """
:root{
  --bg:#F8F7F4;
  --surface:#FFFFFF;
  --surface-2:#F1F5F9;
  --border:#E8E6E1;
  --ink:#171717;
  --ink-2:#666666;
  --muted:#999999;
  --accent:#1E40AF;
  --accent-ink:#1E3A8A;
  --accent-soft:#EFF6FF;
  --teal:#14B8A6;
  --amber:#F59E0B;
  --danger:#EF4444;
  --opp:#8B5CF6;
  --grid:#E5E7EB;
  --sans:'Inter','PingFang SC','Microsoft YaHei',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --shadow-sm:0 1px 2px rgba(0,0,0,.04);
  --shadow:0 4px 20px rgba(0,0,0,.04);
  --radius:16px;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;font-family:var(--sans);background:var(--bg);color:var(--ink);font-size:14px;line-height:1.6;-webkit-font-smoothing:antialiased;}

/* layout */
.app{display:flex;min-height:100vh;}
.side{width:248px;background:var(--surface);border-right:1px solid var(--border);position:fixed;left:0;top:0;bottom:0;overflow:auto;padding:32px 22px;z-index:20;}
.brand{display:flex;align-items:center;gap:11px;font-size:18px;font-weight:700;color:var(--ink);letter-spacing:.3px;}
.brand .logo{width:30px;height:30px;border-radius:9px;background:linear-gradient(135deg,var(--accent),var(--opp));display:flex;align-items:center;justify-content:center;color:#fff;font-size:15px;font-weight:700;flex-shrink:0;}
.brand small{display:block;font-size:10px;font-weight:500;color:var(--muted);letter-spacing:2px;margin-top:3px;text-transform:uppercase;}
.nav{list-style:none;margin:28px 0 0;padding:0;}
.nav li{margin:1px 0;}
.nav a{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;color:var(--ink-2);text-decoration:none;font-size:13px;transition:.15s;}
.nav a .n{font-size:11px;font-weight:700;color:var(--muted);min-width:20px;font-variant-numeric:tabular-nums;}
.nav a:hover{background:#F2F0EB;color:var(--ink);}
.nav a.active{background:var(--accent-soft);color:var(--accent-ink);font-weight:600;}
.nav a.active .n{color:var(--accent);}

.main{margin-left:248px;flex:1;padding:48px 80px 100px;}
.content{max-width:1200px;margin:0 auto;}

/* masthead / Research Header */
.masthead{display:flex;flex-direction:column;gap:18px;padding-bottom:28px;margin-bottom:36px;border-bottom:1px solid var(--border);}
.masthead .kicker{display:inline-flex;align-items:center;gap:8px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--accent);font-weight:600;}
.k-dot{width:6px;height:6px;border-radius:50%;background:var(--accent);display:inline-block;}
.masthead h1{margin:0;font-size:48px;font-weight:700;line-height:1.15;color:var(--ink);letter-spacing:-.8px;}
/* 顶部文档元信息：纯灰文字，无组件装饰 */
.docmeta{margin-top:14px;display:flex;flex-direction:column;gap:7px;font-size:13px;line-height:1.7;color:var(--ink-2);}
.docmeta .dm-line{display:flex;flex-wrap:wrap;gap:6px 22px;}
.docmeta .dm-item{display:inline-flex;align-items:baseline;gap:6px;}
.docmeta .dm-k{color:var(--muted);font-weight:500;}
.docmeta .dm-v{color:var(--ink-2);font-weight:500;}

/* sections */
section{margin-bottom:56px;scroll-margin-top:24px;}
.sec-head{display:flex;align-items:flex-start;gap:18px;padding-bottom:16px;border-bottom:1px solid var(--border);margin-bottom:24px;}
.sec-no{font-size:13px;font-weight:700;color:#fff;background:var(--accent);border-radius:9px;min-width:34px;height:34px;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px;font-variant-numeric:tabular-nums;}
.sec-eyebrow{font-size:10.5px;letter-spacing:2.5px;text-transform:uppercase;color:var(--muted);font-weight:700;margin-bottom:5px;}
.sec-head h2{margin:0;font-size:24px;font-weight:600;color:var(--ink);letter-spacing:-.3px;}
.sec-sub{font-size:13px;color:var(--ink-2);margin-top:4px;}
section p{margin:8px 0;font-size:14px;line-height:1.7;color:var(--ink);}
.lead{font-size:15px;line-height:1.8;color:var(--ink-2);}

/* Insight Card (exec summary / opportunity / recommendations) */
.findings{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;}
.finding{display:flex;flex-direction:column;gap:12px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:24px;box-shadow:var(--shadow-sm);transition:.2s;}
.finding:hover{box-shadow:var(--shadow);transform:translateY(-2px);}
.find-num{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:9px;background:var(--accent-soft);color:var(--accent);font-size:13px;font-weight:700;}
.find-body{display:flex;flex-direction:column;gap:6px;}
.find-kw{font-size:15px;font-weight:600;color:var(--ink);line-height:1.5;}
.find-text{font-size:13.5px;color:var(--ink-2);line-height:1.7;}
.find-ev{display:flex;align-items:center;gap:8px;margin-top:2px;}
.ev-badge{font-size:11px;font-weight:600;padding:3px 10px;border-radius:999px;display:inline-flex;align-items:center;gap:5px;}
.ev-badge.high{background:#DCFCE7;color:#15803D;}
.ev-badge.med{background:#FEF3C7;color:#92660A;}
.ev-badge.low{background:#FEE2E2;color:#B91C1C;}
.ev-conf{font-size:11px;color:var(--muted);}

/* Product Card (positioning note) */
.callout{display:flex;gap:14px;background:var(--accent-soft);border:1px solid #DDDDFB;border-radius:var(--radius);padding:18px 20px;margin-top:18px;font-size:14px;color:var(--ink);line-height:1.8;}
.callout-bar{width:4px;background:var(--accent);border-radius:2px;flex-shrink:0;}
.callout b{color:var(--accent-ink);}

/* feature matrix heatmap */
.matrix-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:8px;box-shadow:var(--shadow-sm);}
.feature-matrix{width:100%;border-collapse:separate;border-spacing:6px;font-size:13px;}
.feature-matrix th{padding:10px;border-radius:10px;font-weight:600;color:var(--ink);text-align:center;background:#FAFAF9;}
.feature-matrix th.fm-feat{text-align:left;background:transparent;}
.fm-ph{padding:4px 12px;border-radius:999px;font-weight:700;white-space:nowrap;font-size:12.5px;}
.feature-matrix td{padding:0;border-radius:8px;text-align:center;vertical-align:middle;}
.feature-matrix td.fm-feat{background:transparent;text-align:left;color:var(--ink);font-weight:500;padding:0 4px;}
.fm-fi{display:inline-flex;vertical-align:middle;margin-right:7px;color:var(--accent);}
.fm-fi svg{width:16px;height:16px;}
.fm-dot{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:8px;vertical-align:middle;}
.fm-dot.yes{background:var(--accent);}
.fm-dot.partial{background:#93C5FD;}
.fm-dot.no{background:#E5E7EB;}
.fm-dot.na{background:#F8FAFC;color:var(--muted);font-size:12px;border:1px solid var(--border);}
.fm-dot svg{width:12px;height:12px;}
.fm-cell.yes{background:rgba(30,64,175,0.12);}
.fm-cell.partial{background:rgba(165,180,252,0.35);}
.fm-cell.no{background:#F1F5F9;}
.fm-cell.na{background:#F8FAFC;}
.fm-note{display:block;font-size:11px;color:var(--muted);margin-top:3px;line-height:1.4;}
.fm-cov-wrap{display:flex;flex-wrap:wrap;align-items:center;gap:10px 22px;padding:14px 12px 6px;}
.fm-cov-title{font-size:12px;font-weight:700;color:var(--ink-2);letter-spacing:.5px;}
.fm-cov{display:flex;align-items:center;gap:8px;font-size:12px;}
.fm-cov-name{font-weight:600;color:var(--ink);}
.fm-cov-bar{width:84px;height:6px;background:#F1EFEA;border-radius:999px;overflow:hidden;}
.fm-cov-bar i{display:block;height:100%;border-radius:999px;}
.fm-cov-pct{color:var(--muted);}
.fm-legend{display:flex;gap:20px;flex-wrap:wrap;padding:6px 12px 12px;font-size:12px;color:var(--ink-2);}
.fm-legend .lg{display:inline-block;width:11px;height:11px;border-radius:4px;margin-right:5px;vertical-align:middle;}
.lg.yes{background:var(--accent);} .lg.partial{background:#93C5FD;} .lg.no{background:#E5E7EB;}

/* chart card */
.chart-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:22px 24px;margin:18px 0;box-shadow:var(--shadow-sm);}
.chart-head{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:6px;}
.chart-title{font-size:18px;font-weight:700;color:var(--ink);}
.chart-note{font-size:11.5px;color:var(--ink-2);background:#F4F3F0;border:1px solid var(--border);padding:3px 11px;border-radius:999px;}
.echart{width:100%;height:430px;}

/* AI cards */
.ai-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;}
.ai-card{display:flex;gap:14px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;align-items:flex-start;position:relative;box-shadow:var(--shadow-sm);}
.ai-card::before{content:"";position:absolute;left:0;top:16px;bottom:16px;width:3px;background:var(--accent);border-radius:2px;}
.ai-idx{font-size:13px;color:var(--accent);font-weight:700;}
.ai-icon{color:var(--accent);margin-top:1px;}
.ai-body h4{margin:0 0 6px;font-size:16px;font-weight:600;color:var(--ink);}
.ai-body p{margin:0;font-size:13px;color:var(--ink-2);line-height:1.7;}

/* business model */
.biz-wrap{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:8px 0;}
.biz-col{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:0 0 14px;overflow:hidden;box-shadow:var(--shadow-sm);}
.biz-ph{display:flex;align-items:center;gap:8px;padding:15px 16px;font-weight:700;font-size:15px;border-bottom:1px solid var(--border);border-top:3px solid;}
.biz-dot{width:9px;height:9px;border-radius:50%;}
.plan{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 16px;border-bottom:1px solid #F3F1EC;}
.plan:last-child{border-bottom:none;}
.plan-tag{font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;white-space:nowrap;}
.plan-val{font-size:13px;color:var(--ink);font-weight:500;text-align:right;}
.biz-extra{margin-top:18px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;box-shadow:var(--shadow-sm);}
.biz-extra-title{font-size:12px;font-weight:700;letter-spacing:.5px;color:var(--ink-2);margin-bottom:8px;}
.biz-table{width:100%;border-collapse:collapse;font-size:13px;}
.biz-table th{padding:9px 12px;text-align:left;color:var(--ink-2);font-weight:600;border-bottom:1px solid var(--border);}
.biz-table td{padding:9px 12px;border-bottom:1px solid #F3F1EC;color:var(--ink);vertical-align:top;}
.biz-table td.bk{font-weight:600;color:var(--ink);}
.biz-table tr:last-child td{border-bottom:none;}

/* KPI */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:8px 0;}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:20px 20px;box-shadow:var(--shadow-sm);}
.kpi-num{font-size:32px;font-weight:700;color:var(--accent);line-height:1.1;font-variant-numeric:tabular-nums;letter-spacing:-1px;}
.kpi-label{font-size:12px;font-weight:600;color:var(--ink);margin:10px 0 4px;}
.kpi-desc{font-size:12.5px;color:var(--ink-2);line-height:1.6;}

/* competition */
.comp-stage{position:relative;width:420px;height:420px;margin:10px auto;max-width:100%;}
.comp-svg{position:absolute;inset:0;}
.comp-core{position:absolute;transform:translate(-50%,-50%);background:linear-gradient(135deg,var(--accent),var(--accent-ink));color:#fff;border-radius:50%;width:112px;height:112px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-weight:700;font-size:14px;box-shadow:0 8px 24px rgba(30,64,175,.35);z-index:3;}
.comp-core small{font-size:9px;font-weight:500;opacity:.85;margin-top:2px;}
.comp-sat{position:absolute;transform:translate(-50%,-50%);background:#fff;border:2px solid #CBD5E1;width:84px;height:84px;border-radius:50%;display:flex;align-items:center;justify-content:center;text-align:center;font-size:12px;font-weight:600;color:#475569;box-shadow:0 3px 10px rgba(0,0,0,.05);z-index:2;padding:4px;}

/* SWOT */
.swot-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.sw-cell{border-radius:20px;padding:18px 20px;border:1px solid var(--border);}
.sw-cell.s{background:#ECFDF5;border-color:#BBF7D0;}
.sw-cell.w{background:#F8FAFC;border-color:#E2E8F0;}
.sw-cell.o{background:#F5F3FF;border-color:#DDD6FE;}
.sw-cell.t{background:#FFFBEB;border-color:#FDE68A;}
.sw-h{font-size:14px;font-weight:700;margin-bottom:10px;color:var(--ink);display:flex;align-items:center;gap:8px;}
.sw-h::before{content:"";width:9px;height:9px;border-radius:3px;}
.sw-cell.s .sw-h::before{background:#10B981;}
.sw-cell.w .sw-h::before{background:#94A3B8;}
.sw-cell.o .sw-h::before{background:#8B5CF6;}
.sw-cell.t .sw-h::before{background:#F59E0B;}
.sw-line{font-size:13px;color:var(--ink-2);line-height:1.7;margin:5px 0;padding-left:13px;position:relative;}
.sw-line::before{content:"";position:absolute;left:0;top:9px;width:5px;height:5px;border-radius:50%;background:currentColor;opacity:.35;}

/* radar / 多维能力图谱 dashboard */
.radar-dash{display:flex;gap:32px;align-items:stretch;}
.radar-main{flex:1.35;min-width:0;background:#FFFFFF;border:1px solid var(--border);border-radius:var(--radius);padding:18px;display:flex;align-items:center;justify-content:center;box-shadow:var(--shadow-sm);}
.radar-main .echart{width:100%;height:460px;}
.score-panel{flex:1;min-width:0;display:flex;flex-direction:column;gap:12px;background:#FFFFFF;border:1px solid var(--border);border-radius:var(--radius);padding:20px 22px;box-shadow:var(--shadow-sm);}
.sp-title{font-size:13px;font-weight:700;letter-spacing:.4px;color:var(--ink-2);margin-bottom:4px;}
.score-item{display:flex;flex-direction:column;gap:7px;}
.si-top{display:flex;align-items:baseline;justify-content:space-between;}
.si-name{font-size:13px;color:var(--ink);font-weight:500;}
.si-score{font-size:15px;font-weight:700;font-variant-numeric:tabular-nums;}
.si-bar{height:7px;background:#F1EFEA;border-radius:999px;overflow:hidden;}
.si-bar i{display:block;height:100%;border-radius:999px;transition:width .4s ease;}
.cmp-legend{display:flex;flex-wrap:wrap;gap:10px 16px;margin-top:16px;padding-top:16px;border-top:1px solid var(--border);}
.cmp-chip{display:inline-flex;align-items:center;gap:7px;font-size:12.5px;color:var(--ink-2);}
.cmp-chip i{width:10px;height:10px;border-radius:3px;display:inline-block;}
.cmp-chip small{color:var(--muted);font-size:11px;margin-left:1px;}

/* empty state */
.chart-empty{padding:42px 0;text-align:center;color:var(--muted);font-size:13px;line-height:1.6;}
/* pyramid */
.pyramid{display:flex;flex-direction:column;gap:6px;align-items:center;}
.pyr-band{width:100%;display:flex;justify-content:center;}
.pyr-band.t1{width:55%;}
.pyr-band.t2{width:78%;}
.pyr-band.t3{width:100%;}
.pyr-txt{display:flex;flex-direction:column;gap:3px;width:100%;padding:18px 24px;color:#fff;border-radius:14px;}
.pyr-band.t1 .pyr-txt{background:linear-gradient(90deg,#1E40AF,#3B82F6);}
.pyr-band.t2 .pyr-txt{background:#94A3B8;}
.pyr-band.t3 .pyr-txt{background:#CBD5E1;}
.pyr-label{font-size:15px;font-weight:700;display:flex;align-items:center;gap:8px;}
.pyr-label span{font-size:12px;font-weight:500;opacity:.9;background:rgba(255,255,255,.22);padding:2px 10px;border-radius:999px;}
.pyr-names{font-size:14px;font-weight:600;margin-top:2px;}
.pyr-desc{font-size:12px;opacity:.92;line-height:1.5;}

/* market map legend */
.mp-legs{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:12px;}
.mp-leg{display:inline-flex;align-items:center;gap:7px;font-size:12px;color:var(--ink-2);}
.mp-leg i{width:11px;height:11px;border-radius:50%;}

/* timeline · 横向 Roadmap */
.timeline-h{overflow-x:auto;padding:30px 2px 14px;margin:6px 0;}
.tl-track{display:flex;align-items:flex-start;gap:0;min-width:max-content;position:relative;}
.tl-node{position:relative;flex:0 0 230px;padding:0 16px;box-sizing:border-box;}
.tl-node::before{content:"";position:absolute;top:14px;left:0;right:0;height:2px;background:var(--border);z-index:0;}
.tl-node:first-child::before{left:50%;}
.tl-node:last-child::before{right:50%;}
.tl-year{position:absolute;top:-24px;left:50%;transform:translateX(-50%);font-size:11px;font-weight:700;color:var(--accent);background:var(--bg);padding:1px 8px;white-space:nowrap;z-index:2;}
.tl-dot{position:relative;z-index:1;display:block;width:13px;height:13px;border-radius:50%;background:var(--accent);border:2px solid #fff;box-shadow:0 0 0 1px var(--border);margin:7px auto 14px;}
.tl-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 14px;box-shadow:var(--shadow-sm);}
.tl-date{font-size:12px;font-weight:700;color:var(--accent-ink);margin-bottom:6px;}
.tl-text{font-size:11.5px;color:var(--ink-2);line-height:1.55;}

/* sentiment */
.sent-bar{display:flex;height:30px;border-radius:10px;overflow:hidden;background:#F1EFEA;}
.sent-pos{background:var(--teal);}
.sent-neg{background:#EF4444;}
.sent-legend{display:flex;align-items:center;gap:16px;margin-top:8px;font-size:12px;color:var(--ink-2);}
.sent-legend .dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:5px;vertical-align:middle;}
.dot.pos{background:var(--teal);} .dot.neg{background:#EF4444;}
.sent-pw{margin-left:auto;font-weight:700;color:var(--ink);}
.voice-list{display:flex;flex-direction:column;gap:10px;margin-top:16px;}
.voice{display:flex;gap:12px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 14px;align-items:flex-start;box-shadow:var(--shadow-sm);}
.voice.pos{border-left:3px solid var(--teal);}
.voice.neg{border-left:3px solid #EF4444;}
.voice-mono{width:38px;height:38px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;}
.voice-main{flex:1;}
.voice-meta{display:flex;align-items:center;gap:10px;margin-bottom:5px;}
.voice-badge{font-size:11px;font-weight:700;padding:2px 10px;border-radius:999px;}
.voice-badge.pos{background:#ECFDF5;color:#15803D;}
.voice-badge.neg{background:#FEF2F2;color:#B91C1C;}
.voice-prod{font-size:12px;color:var(--ink-2);background:#F4F3F0;padding:2px 10px;border-radius:999px;}
.voice-quote{font-size:13px;color:var(--ink);line-height:1.65;}

/* priority */
.pri-row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
.pri-col{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:0 0 14px;overflow:hidden;box-shadow:var(--shadow-sm);}
.pri-h{border-top:3px solid;padding:14px 16px;font-size:14px;font-weight:700;margin-bottom:6px;}
.pri-col ul{margin:0;padding:0 16px;list-style:none;}
.pri-col li{font-size:13px;color:var(--ink);line-height:1.65;padding:9px 0 9px 16px;position:relative;border-bottom:1px solid #F3F1EC;}
.pri-col li:last-child{border-bottom:none;}
.pri-col li::before{content:"";position:absolute;left:0;top:16px;width:6px;height:6px;border-radius:50%;background:currentColor;opacity:.5;}

/* sources */
.ref-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:8px 20px;}
.ref{display:flex;align-items:baseline;gap:10px;padding:9px 0;border-bottom:1px solid #F3F1EC;font-size:13px;}
.ref-no{color:var(--accent);font-weight:700;min-width:18px;}
.ref a{color:var(--accent-ink);text-decoration:none;font-weight:500;}
.ref a:hover{text-decoration:underline;}
.ref-dom{color:var(--muted);font-size:11px;margin-left:auto;}
.cred{font-size:10.5px;font-weight:700;border-radius:999px;padding:2px 9px;margin-left:8px;flex-shrink:0;}
.cred.high{background:#DCFCE7;color:#15803D;}
.cred.mid{background:#FEF3C7;color:#B45309;}
.cred.low{background:#FEE2E2;color:#B91C1C;}

/* generic tables */
.tbl-wrap{overflow-x:auto;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow-sm);}
.tbl{width:100%;border-collapse:collapse;font-size:13px;}
.tbl th,.tbl td{padding:11px 14px;text-align:left;border-bottom:1px solid #F3F1EC;}
.tbl th{font-weight:600;color:var(--ink-2);font-size:12px;background:#FAFAF9;}
.tbl tbody tr:hover{background:var(--accent-soft);}
.tbl tr:last-child td{border-bottom:none;}
.pos-table th,.pos-table td{padding:13px 16px;}
.pos-dim{font-weight:600;color:var(--ink);white-space:nowrap;}
.pos-ph{padding:4px 12px;border-radius:999px;font-weight:700;white-space:nowrap;font-size:12.5px;}
.pos-di{display:inline-flex;vertical-align:middle;margin-right:8px;color:var(--accent);}

/* score badge */
.score-badge{display:inline-flex;flex-direction:column;align-items:center;justify-content:center;min-width:54px;height:54px;border-radius:50%;font-weight:700;flex-shrink:0;}
.score-badge .sb-num{font-size:19px;line-height:1;font-variant-numeric:tabular-nums;}
.score-badge .sb-lab{font-size:9px;font-weight:600;opacity:.75;margin-top:2px;}

/* footer / evidence footer */
.ev-footer{margin-top:48px;padding:24px 0 0;border-top:1px solid var(--border);color:var(--muted);font-size:12px;display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;}
.ev-footer .ef-brand{font-weight:700;color:var(--ink);}
.ev-footer .ef-sep{width:1px;height:14px;background:var(--border);}

@media(max-width:920px){
  .side{display:none;}
  .main{margin-left:0;padding:32px 24px 80px;}
  .content{max-width:none;}
  .ai-grid{grid-template-columns:1fr;}
  .radar-dash{flex-direction:column;}
  .comp-stage{width:340px;height:340px;}
}
@media(max-width:640px){
  .pri-row{grid-template-columns:1fr;}
  .swot-grid{grid-template-columns:1fr;}
  .findings{grid-template-columns:1fr;}
  .masthead h1{font-size:28px;}
}
"""


def parse_sections(lines):
    secs = []
    cur = None
    for ln in lines:
        m = re.match(r"^(#{1,3})\s+(.*)$", ln)
        if m:
            if cur is not None:
                secs.append(cur)
            cur = {"title": m.group(2).strip(), "level": len(m.group(1)), "body": []}
            continue
        # 支持【研究简报】形式的小节标题
        mb = re.match(r"^【([^】]+)】\s*$", ln.strip())
        if mb:
            if cur is not None:
                secs.append(cur)
            cur = {"title": mb.group(1).strip(), "level": 2, "body": []}
            continue
        if cur is not None:
            cur["body"].append(ln)
    if cur is not None:
        secs.append(cur)
    return secs


def section_id(idx):
    return "sec-" + str(idx)


def render_section(sec, mid_state, market_map, idx):
    title = sec["title"]
    body = sec["body"]
    tables = parse_tables(body)
    table_at = {t[0]: t for t in tables}
    parts = []
    positioning_note = []
    sentiment = []; timeline = []; 
    priority = {"must": [], "should": [], "could": []}
    ai_cards = []; growth = []
    swot_bullets = []
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
                parts.append(render_scatter(mid_state[0], header, rows,
                                            "机会地图" if title == '机会' else "市场地图"))
            elif kind == 'source':
                parts.append(render_source_inline(rows))
            elif title == '产品定位':
                parts.append(render_positioning_table(header, rows))
            elif title == '功能矩阵':
                parts.append(render_feature_matrix(header, rows))
            elif title == '商业模式':
                parts.append(render_business_model(header, rows))
            elif title == 'SWOT':
                parts.append(render_swot_table(header, rows))
            else:
                parts.append(render_table(header, rows))
            i = table_at[i][0] + 1
            while i < n and body[i].lstrip().startswith('|'):
                i += 1
            continue

        if line.strip().startswith('-') or line.strip().startswith('·'):
            bl = clean(line)
            mk = re.match(r'^(正面|负面|中立)\s*[（(]?([^）)]*?)[）)]?\s*[：:]?\s*(.*)$', bl)
            if title == '用户口碑' and mk:
                sentiment.append((mk.group(1), mk.group(2).strip(), mk.group(3).strip()))
            elif title == '时间线':
                mm = re.match(r'^(\d{4}(?:[\d\-年/]*\s+[^\s：:]+)?)\s*[：:]\s*(.*)$', bl)
                if mm:
                    timeline.append((mm.group(1).strip(), mm.group(2).strip()))
            elif title == '行动建议':
                mm = re.match(r'^(Must|Should|Could)\s*[：:]\s*(.*)$', bl)
                if mm:
                    priority[mm.group(1).lower()].append(mm.group(2).strip())
            elif title == 'AI 能力':
                t, b = split_kv(bl)
                ai_cards.append((t, b if b else bl))
            elif title == '增长' or title == '增长与运营':
                t, b = split_kv(bl)
                growth.append((t, b if b else bl))
            elif title == 'SWOT':
                swot_bullets.append(bl)
            else:
                # 任意位置出现的 Must/Should/Could 也收集（兼容内联写法）
                mm = re.match(r'^(Must|Should|Could)\s*[：:]\s*(.*)$', bl)
                if mm:
                    priority[mm.group(1).lower()].append(mm.group(2).strip())
                else:
                    parts.append('<p>' + html.escape(bl) + '</p>')
            i += 1
            continue

        if line.strip() and not line.lstrip().startswith('#'):
            if title == '产品定位':
                positioning_note.append(clean(line))
            elif title == 'SWOT':
                swot_bullets.append(clean(line))
            else:
                parts.append('<p>' + html.escape(clean(line)) + '</p>')
        i += 1

    # 章节专属组装
    if title == '执行摘要':
        summary_items = [ln for ln in body if ln.strip().startswith('-') or ln.strip().startswith('·')]
        if summary_items:
            parts = [render_summary(summary_items)]
    elif title == '用户口碑' and sentiment:
        parts = [render_sentiment(sentiment)]
    elif title == '时间线' and timeline:
        parts = [render_timeline(timeline)]
    elif title == '市场概览' and market_map:
        parts.append(render_pyramid(market_map))
    elif title == 'AI 能力':
        # 若本段含评分矩阵则优先雷达，否则展示能力卡
        has_matrix = any(classify_table(t[1], t[2]) == 'matrix' for t in tables)
        if ai_cards and not has_matrix:
            parts = [render_ai_cards(ai_cards)]
    elif (title == '增长' or title == '增长与运营') and growth:
        parts = [render_growth(growth)]
    elif title == 'SWOT' and (swot_bullets or any(classify_table(t[1], t[2]) == 'table' for t in tables)):
        if swot_bullets:
            parts = [render_swot_bullets(swot_bullets)]
    elif title == '竞争格局':
        if market_map and market_map[2]:
            names = [r[0] for r in market_map[2] if r]
            center = "、".join(names[:2]) if len(names) >= 2 else names[0]
            others = names[2:] if len(names) >= 2 else names[1:]
            mid_state[0] += 1
            parts.append(render_competition_graph(mid_state[0], center, others))
    elif (title == '能力雷达') and any(classify_table(t[1], t[2]) == 'matrix' for t in tables):
        pass  # 已在表格分支渲染

    if priority["must"] or priority["should"] or priority["could"]:
        parts.append(render_priority(priority["must"], priority["should"], priority["could"]))

    if title == '产品定位' and positioning_note:
        parts.append(render_positioning_note(' '.join(positioning_note)))

    en = SECTION_EN.get(title, title.upper())
    sub = SECTION_SUBTITLES.get(title, '')
    header_html = ('<div class="sec-head"><div class="sec-no">' + str(idx).zfill(2) + '</div>'
                   + '<div><div class="sec-eyebrow">' + html.escape(en) + '</div>'
                   + '<h2>' + html.escape(title) + '</h2>'
                   + ('<div class="sec-sub">' + html.escape(sub) + '</div>' if sub else '') + '</div></div>')

    return '<section id="' + section_id(idx) + '">' + header_html + "".join(parts) + '</section>'


def render(input_path, output_path):
    with open(input_path, encoding="utf-8") as f:
        text = f.read()
    text = text.replace('｜', '|')
    lines = text.split("\n")

    title = "AI PM 研究报告"
    assumption = {}
    sections = parse_sections(lines)
    for s in sections:
        if s["level"] == 1:
            title = s["title"]

    mid_state = [0]
    market_map = None
    for s in sections:
        for t in parse_tables(s["body"]):
            if classify_table(t[1], t[2]) == 'scatter':
                market_map = t
                break
        if market_map:
            break

    body_parts = []
    sec_idx = 0
    nav_items = ""
    for s in sections:
        if s["level"] == 1:
            continue
        if s["title"] in ('本次假设', '研究简报'):
            for ln in s["body"]:
                bl = clean(ln)
                if not bl:
                    continue
                bl = re.sub(r'^[-·•]\s*', '', bl)  # 去掉可能的列表前缀
                for seg in re.split(r'[｜|]', bl):
                    seg = seg.strip()
                    if '：' in seg or ':' in seg:
                        k, v = re.split(r'[：:]', seg, maxsplit=1)
                        assumption[k.strip()] = v.strip()
                    elif seg:
                        assumption.setdefault('备注', seg)
            continue
        sec_idx += 1
        nav_items += ('<li><a href="#' + section_id(sec_idx) + '"><span class="n">'
                      + str(sec_idx).zfill(2) + '</span>' + html.escape(s["title"]) + '</a></li>')
        body_parts.append(render_section(s, mid_state, market_map, sec_idx))

    ASSUMPTION_ORDER = ["分析对象", "研究意图", "选用维度", "研究深度", "对比对象", "深度", "输出"]
    ASSUMPTION_LABEL = {"分析对象": "分析对象", "研究意图": "研究意图", "选用维度": "选用维度",
                        "研究深度": "研究深度", "对比对象": "对比对象", "深度": "研究深度", "输出": "输出形式"}
    today = datetime.datetime.now().strftime("%Y年%-m月%-d日")

    # 顶部文档元信息：纯灰文字，置于大标题下（无组件装饰）
    _dm_line1, _dm_line2 = [], []
    def _dm_add(lst, label, val):
        if val:
            lst.append((label, val))
    _dm_add(_dm_line1, "分析对象", assumption.get("分析对象"))
    _dm_add(_dm_line1, "研究意图", assumption.get("研究意图"))
    _dm_add(_dm_line1, "对比对象", assumption.get("对比对象"))
    _dm_add(_dm_line1, "数据可信等级", "高（公开来源检索）")
    _dm_add(_dm_line1, "日期", today)
    _dm_add(_dm_line2, "选用维度", assumption.get("选用维度"))
    _dm_add(_dm_line2, "研究深度", assumption.get("研究深度") or assumption.get("深度"))
    _dm_add(_dm_line2, "输出报告", assumption.get("输出") or assumption.get("输出形式"))
    for ak, av in assumption.items():
        if ak not in ("分析对象", "研究意图", "对比对象", "选用维度",
                      "研究深度", "深度", "输出", "输出形式"):
            _dm_add(_dm_line2, ak, av)

    def _dm_render(lst):
        if not lst:
            return ""
        parts = []
        for label, val in lst:
            parts.append('<span class="dm-item"><span class="dm-k">'
                         + html.escape(label) + '</span><span class="dm-v">'
                         + html.escape(val) + '</span></span>')
        return '<div class="dm-line">' + "".join(parts) + '</div>'

    docmeta_html = '<div class="docmeta">' + _dm_render(_dm_line1) + _dm_render(_dm_line2) + '</div>'

    html_doc = ('<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + html.escape(title) + '</title>'
        '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>'
        '<style>' + CSS + '</style></head><body>'
        '<div class="app">'
        '<aside class="side">'
        '<div class="brand"><span class="logo">瞭</span><div>瞭望台<small>AIPM Watchtower</small></div></div>'
        '<ul class="nav">' + nav_items + '</ul>'
        '</aside>'
        '<main class="main">'
        '<header class="masthead">'
        '<div class="kicker"><span class="k-dot"></span>AI PM · 竞品研究报告</div>'
        '<h1>' + html.escape(title) + '</h1>'
        + docmeta_html +
        '</header>'
        + '<div class="content">' + "".join(body_parts) + '</div>'
        + '<footer class="ev-footer"><span class="ef-brand">AIPM·瞭望台</span><span class="ef-sep"></span><span>本报告由 AI 实时检索公开来源生成，结论可溯源</span><span class="ef-sep"></span><span>更新于 ' + today + '</span></footer>'
        '</main></div>'
        '<script>var REG=[];window.addEventListener("load",function(){REG.forEach(function(c){c.resize();});});'
        'window.addEventListener("resize",function(){REG.forEach(function(c){c.resize();});});'
        'var navs=document.querySelectorAll(".nav a");'
        'navs.forEach(function(a){a.addEventListener("click",function(){navs.forEach(function(x){x.classList.remove("active");});this.classList.add("active");});});'
        'var secs=[].slice.call(document.querySelectorAll("section"));'
        'window.addEventListener("scroll",function(){'
        'var pos=window.scrollY+120;'
        'secs.forEach(function(s){if(s.offsetTop<=pos){navs.forEach(function(x){x.classList.remove("active");});'
        'var a=document.querySelector(\'.nav a[href="#\'+s.id+\'"]\');if(a)a.classList.add("active");}});});'
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
