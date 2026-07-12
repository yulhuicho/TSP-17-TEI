# fig 1 · Topic Debate Flow
# Vertical alignment of the four topics and each opponent's debate segments.
# Used by build_fig1_*.py to generate the notebook.
# After editing, run build_*.py to regenerate the notebook.

"""fig1 — Topic Debate Flow (vertical): kārikā axis runs top→bottom.
Linear scale 1212–1360. Non-debate sections (1212–1263, 1355–1360)
shown as faint stubs; debate bars (1264–1354) shown in full colour.
"""
import os
import pandas as pd
import plotly.graph_objects as go
from lxml import etree

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))
except NameError:
    _cur = os.path.abspath(os.getcwd())
    _ROOT = _cur
    for _ in range(5):
        if os.path.isdir(os.path.join(_cur, 'data')):
            _ROOT = _cur
            break
        _parent = os.path.dirname(_cur)
        if _parent == _cur:
            break
        _cur = _parent
XML_PATH = os.path.join(_ROOT, 'data', 'TSP-17-tei-v2.0.0.xml')
OUT_DIR  = os.path.join(_ROOT, 'figures')
os.makedirs(OUT_DIR, exist_ok=True)
TEI      = '{http://www.tei-c.org/ns/1.0}'
XML_NS   = '{http://www.w3.org/XML/1998/namespace}'
FONT     = 'Menlo, Monaco, Consolas, monospace'

tree = etree.parse(XML_PATH); root = tree.getroot()

# ── pākṣa extraction ──────────────────────────────────────────────────────
rows = []
for d in root.iter(TEI+'div'):
    if d.get('type') not in ('pūrvapakṣa', 'uttarapakṣa'): continue
    xid   = d.get(XML_NS+'id') or ''
    parts = xid.split('_')
    opp   = parts[1] if len(parts) >= 3 else ''
    rng   = parts[-1]
    if '-' in rng:
        a, b = rng.split('-', 1); s, e = int(a), int(b)
    else: s = e = int(rng)
    rows.append({'side': d.get('type'), 'opp': opp, 'start': s, 'end': e})
df_pak = pd.DataFrame(rows).sort_values('start').reset_index(drop=True)

# ── palette (Tableau 10 — designed for perceptual distinctiveness) ────────
OPP_COLOR = {
    'Sumati':         '#4E79A7',  # steel blue
    'Kumārila':       '#E15759',  # coral red
    'Bhāvivikta':     '#59A14F',  # sage green
    'Bauddha':        '#EDC948',  # warm gold
    'Jinendrabuddhi': '#B07AA1',  # dusty mauve
    'Vaiśeṣika':      '#F28E2B',  # amber
    'Śaṅkarasvāmin':  '#76B7B2',  # soft teal
}

# ── section boundaries ────────────────────────────────────────────────────
CHAPTER_START = 1212   # TSP17 chapter start
TOPIC_START   = 1213   # kalpanāpoḍha begins
DEBATE_START  = 1264   # first pūrvapakṣa
DEBATE_END    = 1354   # last uttarapakṣa
CHAPTER_END   = 1360   # TSP17 chapter end

# ── topics: auto-derived from <div type="topic"> in XML ──────────────────
import re as _re
def _get_topic_ranges(root):
    out = []
    for div in root.iter(TEI+'div'):
        if div.get('type') != 'topic': continue
        head = div.find(TEI+'head')
        name = head.text.strip() if head is not None and head.text else None
        karikas = []
        for elem in div.iter():
            xid = elem.get(XML_NS+'id') or ''
            for m in _re.finditer(r'(\d{4})', xid):
                k = int(m.group(1))
                if 1200 <= k <= 1400:
                    karikas.append(k)
        if karikas and name:
            out.append((name, min(karikas), max(karikas)))
    return out
TOPICS = _get_topic_ranges(root)
# (formerly hardcoded as [('kalpanāpoḍha',1213,1310), ('abhrānta',1311,1328),
#  ('sukhādisvasaṃvitti',1329,1342), ('pramāṇaphala',1343,1360)])

BAR_X     = 'debate'
BAR_WIDTH = 0.10
HW        = BAR_WIDTH / 2   # 0.07

# ── x-axis layout (all labels in data coords so they align with the bar) ──
X_LEFT   = -0.56   # reduced left margin
X_RIGHT  =  0.72   # further trimmed
LABEL_LEFT_X   = -HW - 0.02   # right-anchored label edge, closer to the bar

# topic bar (right next to the debate bar)
TOPIC_BAR_X0 = HW + 0.03    # just right of the debate bar
TOPIC_BAR_X1 = HW + 0.10    # width 0.07 (thin)

# bracket: overlaid on the right edge of the topic bar
BRACKET_X0     =  TOPIC_BAR_X1          # vertical line = right edge of the bar
BRACKET_X1     =  TOPIC_BAR_X1 + 0.05  # horizontal tick slightly protrudes
LABEL_RIGHT_X  =  TOPIC_BAR_X1 + 0.08  # label just right of the tick

FIG_W = 780
FIG_H = 1480

fig = go.Figure()

# ── topic bar (same palette as fig3 STRIP_COLORS, alongside the debate bar) ──
TOPIC_COLOR = {
    'kalpanāpoḍha':      '#C8DCE8',
    'abhrānta':           '#C4E4C4',
    'sukhādisvasaṃvitti': '#EEE4B8',
    'pramāṇaphala':       '#ECC8C8',
}

# 1212 gray stub (1212–1213: chapter intro before kalpanāpoḍha)
fig.add_shape(
    type='rect', xref='x', yref='y',
    x0=TOPIC_BAR_X0, x1=TOPIC_BAR_X1,
    y0=CHAPTER_START, y1=TOPIC_START,
    fillcolor='rgba(200,200,200,0.18)',
    line=dict(color='#bbb', width=0.6),
    layer='below',
)
for tname, ts, te in TOPICS:
    # kalpanāpoḍha only: y0 starts at 1213 to avoid overlap with 1212 stub
    y0_topic = ts if tname == 'kalpanāpoḍha' else ts - 1
    fig.add_shape(
        type='rect', xref='x', yref='y',
        x0=TOPIC_BAR_X0, x1=TOPIC_BAR_X1,
        y0=y0_topic, y1=te,
        fillcolor=TOPIC_COLOR[tname],
        line=dict(color='#bbb', width=0.6),
        layer='below',
    )

# ── non-debate intro stub  (1212–1263) ────────────────────────────────────
fig.add_shape(
    type='rect', xref='x', yref='y',
    x0=-HW, x1=HW,
    y0=CHAPTER_START, y1=DEBATE_START - 1,
    line=dict(color='#888', width=1.2),
    fillcolor='rgba(200,200,200,0.18)',
    layer='above',
)

# ── non-debate epilogue stub (1355–1360) ──────────────────────────────────
fig.add_shape(
    type='rect', xref='x', yref='y',
    x0=-HW, x1=HW,
    y0=DEBATE_END, y1=CHAPTER_END,
    line=dict(color='#888', width=1.2),
    fillcolor='rgba(200,200,200,0.18)',
    layer='above',
)

# ── mid-debate non-debate gaps: faint gray stubs ─────────────────────────
_segs = sorted(df_pak[['start','end']].itertuples(index=False), key=lambda x: x.start)
_prev_end = DEBATE_START - 1
for _seg in _segs:
    if _seg.start > _prev_end + 1:
        _gs, _ge = _prev_end + 1, _seg.start - 1
        fig.add_shape(
            type='rect', xref='x', yref='y',
            x0=-HW, x1=HW,
            y0=_gs - 1, y1=_ge,
            line=dict(color='#bbb', width=0.8),
            fillcolor='rgba(200,200,200,0.18)',
            layer='below',
        )
    _prev_end = max(_prev_end, _seg.end)

# ── debate bars (1264–1354, full colour) ──────────────────────────────────
# Merge consecutive segments of the same opponent into one rectangle (removes inner seams)
_sorted = df_pak.sort_values('start').to_dict('records')
_runs = []
_i = 0
while _i < len(_sorted):
    opp = _sorted[_i]['opp']
    start = _sorted[_i]['start']
    end   = _sorted[_i]['end']
    _j = _i + 1
    while _j < len(_sorted) and _sorted[_j]['opp'] == opp and _sorted[_j]['start'] <= end + 1:
        end = max(end, _sorted[_j]['end'])
        _j += 1
    _runs.append((opp, start, end))
    _i = _j

for opp, start, end in _runs:
    color = OPP_COLOR.get(opp, '#888')
    fig.add_shape(
        type='rect', xref='x', yref='y',
        x0=-HW, x1=HW,
        y0=start - 1, y1=end,
        fillcolor=color,
        line=dict(color='#888', width=1.2),
        layer='above',
    )


# ── topic brackets (xref='x' — data coords, always aligned with bar) ─────
for tname, ts, te in TOPICS:
    # kalpanāpoḍha: bracket top also starts at 1213 (aligned with light-blue start)
    y0_bracket = ts if tname == 'kalpanāpoḍha' else ts - 1
    fig.add_shape(type='line', xref='x', yref='y',
        x0=BRACKET_X0, x1=BRACKET_X0, y0=y0_bracket, y1=te,
        line=dict(color='#888', width=1.2), layer='above')
    fig.add_shape(type='line', xref='x', yref='y',
        x0=BRACKET_X0, x1=BRACKET_X1, y0=y0_bracket, y1=y0_bracket,
        line=dict(color='#888', width=1.2), layer='above')
    fig.add_shape(type='line', xref='x', yref='y',
        x0=BRACKET_X0, x1=BRACKET_X1, y0=te, y1=te,
        line=dict(color='#888', width=1.2), layer='above')
    fig.add_annotation(
        x=LABEL_RIGHT_X, y=(y0_bracket+te)/2, xref='x', yref='y',
        text=f"{tname}",
        showarrow=False, xanchor='left', yanchor='middle',
        font=dict(family=FONT, size=19, color='#444'),
    )

# ── Opponent name labels (left of bar, xref='x') ────────────────────────────
def find_all_blocks(df, gap=3):
    """Return contiguous blocks per opponent: {opp: [{'start':s,'end':e}, ...]}"""
    result = {}
    for _, r in df.sort_values('start').iterrows():
        opp = r['opp']
        if opp not in result:
            result[opp] = [{'start': r['start'], 'end': r['end']}]
        else:
            last = result[opp][-1]
            if r['start'] <= last['end'] + gap:
                last['end'] = max(last['end'], r['end'])
            else:
                result[opp].append({'start': r['start'], 'end': r['end']})
    return result

opp_all_blocks = find_all_blocks(df_pak)

for opp, blocks in opp_all_blocks.items():
    color = OPP_COLOR.get(opp, '#888')
    lbl = opp
    for blk in blocks:
        y_pos = (blk['start'] + blk['end']) / 2
        fig.add_annotation(
            x=LABEL_LEFT_X, y=y_pos, xref='x', yref='y',
            text=f"{lbl}", showarrow=False, xanchor='right', yanchor='middle',
            font=dict(family=FONT, size=18, color=color),
        )

# ── tick marks ────────────────────────────────────────────────────────────
tick_vals = [CHAPTER_START] + list(range(1220, CHAPTER_END + 1, 10))
tick_text = [str(v) for v in tick_vals]

# Explicit grid lines at 1212 and 1360 (yaxis showgrid misses boundary lines)
for _y in (CHAPTER_START, CHAPTER_END):
    fig.add_shape(type='line', xref='paper', yref='y',
        x0=0, x1=1, y0=_y, y1=_y,
        line=dict(color='#f3f3f3', width=1),
        layer='below')

# ── legend traces ─────────────────────────────────────────────────────────
fig.add_trace(go.Bar(y=[None], x=[None], name='debate section',
    marker=dict(color='#888', line=dict(color='#666', width=1))))
for opp, color in OPP_COLOR.items():
    lbl = opp
    fig.add_trace(go.Bar(y=[None], x=[None], name=lbl,
        marker=dict(color=color, line=dict(color=color, width=1)),
        showlegend=False))

# ── layout ────────────────────────────────────────────────────────────────
fig.update_layout(
    title=None,
    font=dict(family=FONT, size=16, color='#222'),
    barmode='overlay',
    plot_bgcolor='white', paper_bgcolor='white',
    width=FIG_W, height=FIG_H,
    margin=dict(l=80, r=20, t=20, b=40),
    showlegend=False,
    legend=dict(
        orientation='v', x=0.04, y=0.99,
        xanchor='left', yanchor='top',
        font=dict(family=FONT, size=15),
        itemsizing='constant',
        bgcolor='rgba(0,0,0,0)',
    ),
    xaxis=dict(
        type='category', categoryarray=[BAR_X],
        visible=False, range=[X_LEFT, X_RIGHT],
    ),
    yaxis=dict(
        title=dict(text='kārikā', font=dict(family=FONT, size=17)),
        tickvals=tick_vals,
        ticktext=tick_text,
        tickfont=dict(family=FONT, size=15),
        showgrid=True, gridcolor='#f3f3f3', gridwidth=1,
        autorange='reversed',
        range=[CHAPTER_START - 2, CHAPTER_END + 2],
    ),
)

out_png = os.path.join(OUT_DIR, 'fig1_TopicDebateFlow.png')
out_svg = os.path.join(OUT_DIR, 'fig1_TopicDebateFlow.svg')
fig.write_image(out_png, width=FIG_W, height=FIG_H, scale=2)
fig.write_image(out_svg, width=FIG_W, height=FIG_H)

print(f'[OK] {out_png}')
print(f'[OK] {out_svg}')

