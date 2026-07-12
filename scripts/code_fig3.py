# fig 3 · Text-Reuse & Mentions Heatmap
# Author × Topic matrix. Cell color intensity ∝ <q> + <rs> count.
# Used by build_fig3.py to generate the notebook.
# After editing, run build_fig3.py to regenerate the notebook.

import os, re
from collections import defaultdict
import plotly.graph_objects as go
from lxml import etree

# ----------------------------------------------------------------------
# 0. paths (portable: works both as script and when embedded in a notebook)
# ----------------------------------------------------------------------
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))
except NameError:
    # Embedded in a notebook: walk up from cwd to find a folder containing data/
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
TEI = '{http://www.tei-c.org/ns/1.0}'
XML = '{http://www.w3.org/XML/1998/namespace}'
FONT = 'Menlo, Monaco, Consolas, monospace'

tree = etree.parse(XML_PATH); root = tree.getroot()

# ----------------------------------------------------------------------
# 1. Author → school mapping (consistent with fig4)
# ----------------------------------------------------------------------
def _derive_text_to_person(root):
    out = {}
    for b in root.iter(TEI+'bibl'):
        xid = b.get(XML+'id')
        a = b.find(TEI+'author')
        if a is not None and xid:
            out[xid] = (a.get('key') or '').lstrip('#') or a.text
    return out
TEXT_TO_PERSON = _derive_text_to_person(root)
TEXT_TO_PERSON.update({
    'NB':'Dharmakīrti',
    'PSṬ':'Jinendrabuddhi',
    'Nyāyamukha':'Dignāga',
    'TS':'Śāntarakṣita',
    'TSP':'Kamalaśīla',
    'NV':'Uddyotakara',
})

# Derive SCHOOL mapping from XML:
#   - <org xml:id="X" type="Buddhist|Non-Buddhist"> → ORG_TRADITION[X] = 'Buddhist' / 'Non-Buddhist'
#   - <person xml:id="P"><affiliation key="#X"/></person> → person P inherits X's tradition
#   - EGO_PERSONS (project convention, not XML data) → 'Ego'
#   - 'unknown' sentinel → 'Unknown'
EGO_PERSONS = {'Śāntarakṣita', 'Kamalaśīla'}
ORG_TRADITION = {}
for org in root.iter(TEI+'org'):
    xid = org.get(XML+'id')
    t = org.get('type')
    if xid and t:
        ORG_TRADITION[xid] = t

SCHOOL = {'unknown': 'Unknown'}
# orgs: direct from @type
for xid, t in ORG_TRADITION.items():
    SCHOOL[xid] = t
# persons: inherit tradition from affiliation → org
for person in root.iter(TEI+'person'):
    pid = person.get(XML+'id')
    if not pid: continue
    if pid in EGO_PERSONS:
        SCHOOL[pid] = 'Ego'; continue
    aff = person.find(TEI+'affiliation')
    if aff is not None:
        aff_key = (aff.get('key') or '').lstrip('#')
        if aff_key in ORG_TRADITION:
            SCHOOL[pid] = ORG_TRADITION[aff_key]
            continue
    # fallback: no affiliation registered → Non-Buddhist (safer default;
    # Buddhist scholars in this corpus are all affiliated)
    SCHOOL[pid] = 'Non-Buddhist'

# Alias resolution: normalize surface-form ids (e.g., Bhāradvāja) to
# canonical ids (e.g., Uddyotakara) via <relation name="aliasOf">.
ALIAS_TO_CANONICAL = {}
for rel in root.iter(TEI+'relation'):
    if rel.get('name') == 'aliasOf':
        active = (rel.get('active') or '').lstrip('#')
        passive = (rel.get('passive') or '').lstrip('#')
        if active and passive:
            ALIAS_TO_CANONICAL[active] = passive

def resolve_q_authors(q):
    # @who has priority (multi-token supported); fallback to @source (multi-token)
    w = q.get('who') or ''
    who_tokens = [t for t in w.split() if t.startswith('#')]
    if who_tokens:
        authors, seen = [], set()
        for tok in who_tokens:
            a = tok[1:]  # who directly references person id (no TEXT_TO_PERSON needed)
            if a not in seen:
                seen.add(a); authors.append(a)
        return authors
    s = q.get('source') or ''
    authors, seen = [], set()
    for tok in s.split():
        if not tok.startswith('#'): continue
        raw = tok[1:]
        a = TEXT_TO_PERSON.get(raw, raw)
        if a not in seen:
            seen.add(a); authors.append(a)
    return authors or ['unknown']

def resolve_rs_targets(rs):
    # Return all tokens of rs @key (e.g. "Bharga Bhāradvāja"), with
    # aliases normalized to canonical ids.
    k = rs.get('key') or 'unknown'
    is_text = (rs.get('type') == 'text')
    out, seen = [], set()
    for tok in k.split():
        tok = tok.lstrip('#')
        if not tok: continue
        if is_text:
            tok = TEXT_TO_PERSON.get(tok, tok)
        tok = ALIAS_TO_CANONICAL.get(tok, tok)
        if tok not in seen:
            seen.add(tok); out.append(tok)
    return out or ['unknown']

def local(el):
    return etree.QName(el).localname if isinstance(el.tag, str) else None

def find_topic(el):
    a = el.getparent()
    while a is not None:
        if local(a) == 'div' and a.get('type') == 'topic':
            h = a.find(TEI+'head')
            if h is not None and h.text:
                return h.text.strip()
            return None
        a = a.getparent()
    return None

# Derive TOPICS (ordered list) and TOPIC_RANGES (name -> (kmin, kmax))
# from <div type="topic"> in document order. This replaces earlier hardcoding
# and keeps fig3 in sync with the XML if topics are renamed or renumbered.
def _get_topics_from_xml(root):
    topics = []
    ranges = {}
    for div in root.iter(TEI+'div'):
        if div.get('type') != 'topic': continue
        h = div.find(TEI+'head')
        name = h.text.strip() if h is not None and h.text else None
        if not name: continue
        karikas = []
        for elem in div.iter():
            xid = elem.get(XML+'id') or ''
            for m in re.finditer(r'(\d{4})', xid):
                k = int(m.group(1))
                if 1200 <= k <= 1400:
                    karikas.append(k)
        if karikas:
            topics.append(name)
            ranges[name] = (min(karikas), max(karikas))
    return topics, ranges
TOPICS, TOPIC_RANGES = _get_topics_from_xml(root)
KMAX = max(k1 for _, k1 in TOPIC_RANGES.values())

# ----------------------------------------------------------------------
# 2. Aggregate events → (author, topic) counts
# ----------------------------------------------------------------------
KEEP_TYPES = {'quotation','reference','emendation'}
counts = defaultdict(int)   # (author, topic) → count
authors_seen = set()

for q in root.iter(TEI+'q'):
    if q.get('type') not in KEEP_TYPES: continue
    t = find_topic(q)
    if not t: continue
    for author in resolve_q_authors(q):
        counts[(author, t)] += 1
        authors_seen.add(author)

for rs in root.iter(TEI+'rs'):
    if not rs.get('key'): continue
    t = find_topic(rs)
    if not t: continue
    for target in resolve_rs_targets(rs):
        counts[(target, t)] += 1
        authors_seen.add(target)

# ----------------------------------------------------------------------
# 3. Order authors — grouped by school; within each group, ranked by total count
# ----------------------------------------------------------------------
# per-author totals
author_total = defaultdict(int)
for (a, t), c in counts.items():
    author_total[a] += c

# School grouping (order: Buddhist → Ego → Non-Buddhist → Unknown)
SCHOOL_ORDER = ['Buddhist', 'Ego', 'Unknown', 'Non-Buddhist']
by_school = defaultdict(list)
for a in authors_seen:
    by_school[SCHOOL.get(a, 'Unknown')].append(a)

# Group/school names (not persons): placed after persons
GROUP_LABELS = {
    'Bauddha', 'Yogācāra', 'Sautrāntika', 'Yogācāra Sautrāntika',
    'Vijñānavādin', 'Bāhyārthasadbhāvavādin', 'Nirbhāsijñānapakṣa',
    'Mīmāṃsā', 'Bhinnapramāṇaphalavādin',
    'Vaiśeṣika', 'Nyāya', 'Digambara',
}
def is_group(a): return a in GROUP_LABELS

# Explicit order for Non-Buddhist authors — grouped by school
# Kumārila-Mīmāṃsā, Sumati-Digambara pairs → three Nyāya authors → Bharga (unknown)
# → Vaiśeṣika → Bhartṛhari (affirmative text-reuse, at bottom)
NB_ORDER = [
    'Kumārila', 'Mīmāṃsā', 'Bhinnapramāṇaphalavādin', # Mīmāṃsā group
    'Sumati', 'Digambara',                              # Jaina pair
    'Bharga',                                           # unknown; mentioned as "bhargabhāradvāja..." before Uddyotakara
    'Uddyotakara', 'Bhāvivikta', 'Śaṅkarasvāmin',       # Nyāya group
    'Vaiśeṣika',                                        # Vaiśeṣika
    'Bhartṛhari',                                       # affirmative text-reuse (bottom)
]

# Buddhist scholar order (by floruit = teacher-student lineage)
BUDDHIST_PERSON_ORDER = [
    'Dignāga',            # 480–540 (5–6c)
    'Dharmakīrti',        # 600–660 (7c)
    'Devendrabuddhi',     # 630–690 (7c, direct student of Dharmakīrti)
    'Śākyabuddhi',        # 660–720 (7–8c)
    'Jinendrabuddhi',     # 710–770 (8c, commentator on PS)
    'Dharmottara',        # 740–800 (8c)
]

# Buddhist group order (by school lineage)
BUDDHIST_GROUP_ORDER = [
    'Bauddha',                      # general term
    'Sautrāntika',                  # realist school
    'Yogācāra',                     # idealist school
    'Yogācāra Sautrāntika',         # combined form
    'Bāhyārthasadbhāvavādin',       # affirms external reality
    'Nirbhāsijñānapakṣa',           # representationalist (≈ Sākāra-vāda), grouped with Bāhyārtha
    'Vijñānavādin',                 # affirms consciousness-only
]

def order_buddhist(names):
    # Buddhist: persons (by floruit) -> groups (explicit order)
    person_names = [n for n in names if not is_group(n)]
    persons, remaining_p = [], set(person_names)
    for p in BUDDHIST_PERSON_ORDER:
        if p in remaining_p:
            persons.append(p); remaining_p.discard(p)
    for p in sorted(remaining_p, key=lambda x: (-author_total[x], x)):
        persons.append(p)

    group_names = [n for n in names if is_group(n)]
    groups, remaining_g = [], set(group_names)
    for g in BUDDHIST_GROUP_ORDER:
        if g in remaining_g:
            groups.append(g); remaining_g.discard(g)
    for g in sorted(remaining_g, key=lambda x: (-author_total[x], x)):
        groups.append(g)
    return persons + groups

def order_non_buddhist(names):
    # Apply NB_ORDER first; append remaining authors by count descending
    remaining = set(names)
    out = []
    for name in NB_ORDER:
        if name in remaining:
            out.append(name); remaining.discard(name)
    # Authors not in the explicit order (for future additions)
    for name in sorted(remaining, key=lambda x: (-author_total[x], x)):
        out.append(name)
    return out

# Sort each group
authors_ordered = []
group_boundaries = []   # (school, first_row_idx, last_row_idx) — for group dividers
for school in SCHOOL_ORDER:
    names = by_school.get(school, [])
    if not names: continue
    if school == 'Buddhist':
        grp = order_buddhist(names)
    elif school == 'Non-Buddhist':
        grp = order_non_buddhist(names)
    else:
        grp = sorted(names, key=lambda x: (-author_total[x], x))
    start = len(authors_ordered)
    authors_ordered.extend(grp)
    end = len(authors_ordered) - 1
    group_boundaries.append((school, start, end))

print(f'{len(authors_ordered)} authors, {len(TOPICS)} topics')

# ----------------------------------------------------------------------
# 4. Prepare heatmap data
# ----------------------------------------------------------------------
Z = []          # count matrix (rows: authors, cols: topics)
TEXT = []       # in-cell text (blank if 0)
for a in authors_ordered:
    row_z, row_t = [], []
    for t in TOPICS:
        c = counts.get((a, t), 0)
        row_z.append(c)
        row_t.append(str(c) if c > 0 else '')
    Z.append(row_z)
    TEXT.append(row_t)

# ----------------------------------------------------------------------
# 5. Color scale — a single gradient regardless of school (emphasizes cell intensity)
# ----------------------------------------------------------------------
# Gradient in the Tableau mauve family (anchored at #B07AA1)
# 0 = pale warm-mauve tint; from count=1 the gradient becomes distinct
COLORSCALE = [
    [0.0,   'rgba(250,247,250,1.0)'],   # 0 → #faf7fa (very pale mauve tint)
    [0.001, 'rgba(232,215,228,1.0)'],   # count=1: distinct mauve tint
    [0.15,  'rgba(210,178,201,1.0)'],   # light mauve
    [0.40,  'rgba(176,122,161,1.0)'],   # Tableau mauve #B07AA1
    [0.70,  'rgba(120,80,110,1.0)'],    # deep mauve
    [1.0,   'rgba(70,35,70,1.0)'],      # dark plum
]

Z_MAX = max(max(r) for r in Z)

# ----------------------------------------------------------------------
# kārikā-scale axis + per-cell rectangles (topic width ∝ kārikā range)
# ----------------------------------------------------------------------
# --- Color interpolation helper ---
def _parse_rgba(s):
    m = re.match(r'rgba\(([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)\)', s)
    return tuple(float(g) for g in m.groups())
_STOPS = [(t, _parse_rgba(c)) for t, c in COLORSCALE]
def _mix(c1, c2, f):
    return tuple(c1[i] + f * (c2[i] - c1[i]) for i in range(4))
def color_at(v, vmax):
    # value to rgba string via colorscale interpolation
    t = 0 if vmax <= 0 else v / vmax
    for i in range(len(_STOPS) - 1):
        s1, c1 = _STOPS[i]; s2, c2 = _STOPS[i+1]
        if s1 <= t <= s2:
            frac = 0 if s2 == s1 else (t - s1) / (s2 - s1)
            r, g, b, a = _mix(c1, c2, frac)
            return f'rgba({int(r)},{int(g)},{int(b)},{a})'
    r, g, b, a = _STOPS[-1][1]
    return f'rgba({int(r)},{int(g)},{int(b)},{a})'

fig = go.Figure()

# --- Cell rectangles + text ---
TEXT_LIGHT_THRESHOLD = 0.50
CELL_GAP = 0.05        # gap between cells (y direction)
for r_i, a in enumerate(authors_ordered):
    for topic in TOPICS:
        v = counts.get((a, topic), 0)
        x0, x1 = TOPIC_RANGES[topic]
        # kārikā-scale x range: small gap between cells (~0.5 kārikā)
        cx0 = x0 - 0.5 + 0.3
        cx1 = x1 + 0.5 - 0.3
        cy0 = r_i - 0.5 + CELL_GAP
        cy1 = r_i + 0.5 - CELL_GAP
        fig.add_shape(
            type='rect',
            x0=cx0, x1=cx1, y0=cy0, y1=cy1,
            fillcolor=color_at(v, Z_MAX),
            line=dict(width=0), layer='below',
        )
        if v > 0:
            tc = 'white' if (v / Z_MAX) >= TEXT_LIGHT_THRESHOLD else '#111'
            fig.add_annotation(
                x=(cx0 + cx1) / 2, y=r_i, text=str(v),
                showarrow=False, xanchor='center', yanchor='middle',
                font=dict(family=FONT, size=11, color=tc),
            )

# --- Colorbar (hidden heatmap trace) ---
fig.add_trace(go.Heatmap(
    z=[[0, Z_MAX]], x=[KMAX + 100, KMAX + 101], y=[-100, -99],
    colorscale=COLORSCALE, zmin=0, zmax=Z_MAX,
    showscale=True,
    colorbar=dict(
        thickness=8,
        # 55% of heatmap height; aligned with labels to the heatmap center
        len=len(authors_ordered) / (len(authors_ordered) + 2.5) * 0.55,
        # slightly below the heatmap center (paper y ≈ 0.4445) so the label group aligns
        y=(len(authors_ordered) / (len(authors_ordered) + 2.5)) / 2 - 0.02,
        yanchor='middle',
        tickfont=dict(family=FONT, size=8),
        x=1.02,
    ),
    opacity=0, hoverinfo='skip',
))

# --- Colorbar title: directly above the bar (bar + label group aligns to heatmap center) ---
_hm_top = len(authors_ordered) / (len(authors_ordered) + 2.5)
_cb_center = _hm_top / 2 - 0.02
_cb_len = _hm_top * 0.55
_cb_top_paper = _cb_center + _cb_len / 2
fig.add_annotation(
    xref='paper', yref='paper',
    x=1.035, y=_cb_top_paper + 0.02,
    xanchor='center', yanchor='bottom',
    text='text-reuse &<br>mentions',
    showarrow=False, align='center',
    font=dict(family=FONT, size=10, color='#222'),
)

# --- Topic labels (column-centered; sukhādi-svasaṃvitti wraps to two lines) ---
TOPIC_LABEL_Y = -1.3
TOPIC_DISPLAY = {
    'kalpanāpoḍha':       'kalpanāpoḍha',
    'abhrānta':           'abhrānta',
    'sukhādisvasaṃvitti': 'sukhādi-<br>svasaṃvitti',
    'pramāṇaphala':       'pramāṇa-<br>phala',
}
for topic in TOPICS:
    x0, x1 = TOPIC_RANGES[topic]
    fig.add_annotation(
        x=(x0 + x1) / 2, y=TOPIC_LABEL_Y,
        text=TOPIC_DISPLAY[topic],
        showarrow=False, xanchor='center', yanchor='middle',
        font=dict(family=FONT, size=11, color='#333'),
    )

# --- School-group color bar + labels ---
SCHOOL_COLOR = {
    'Buddhist':     '#4E79A7',
    'Ego':          '#76B7B2',
    'Non-Buddhist': '#E15759',
    'Unknown':      '#9CA3AF',
}
# x coordinates on the kārikā scale (left → right: author name → vertical bar → heatmap)
AUTHOR_LABEL_X = 1209.5     # author name (right-aligned, just left of the bar)
BAR_X_OUTER    = 1210       # bar left edge
BAR_X_INNER    = 1212       # bar right edge (2 unit width)
LABEL_X        = 1211       # group name (bar center, vertical text)

for school, s, e in group_boundaries:
    y_top    = s - 0.5
    y_bottom = e + 0.5
    # Color bar (all groups including Unknown)
    fig.add_shape(
        type='rect',
        x0=BAR_X_OUTER, x1=BAR_X_INNER,
        y0=y_top, y1=y_bottom,
        line=dict(width=0),
        fillcolor=SCHOOL_COLOR[school],
        layer='above',
    )
    # Vertical label (omitted for Unknown)
    if school == 'Unknown':
        continue
    fig.add_annotation(
        x=LABEL_X, y=(s + e) / 2,
        text=f'<b>{school}</b>',
        showarrow=False,
        xanchor='center', yanchor='middle',
        font=dict(family=FONT, size=11, color='white'),
        textangle=-90,
    )
    if e < len(authors_ordered) - 1:
        fig.add_shape(
            type='line',
            x0=1195, x1=KMAX + 0.5,
            y0=e+0.5, y1=e+0.5,
            line=dict(color='#eeeeee', width=0.4),
            layer='above',
        )

# --- Author names (right-aligned, flush against the bar) ---
for r_i, a in enumerate(authors_ordered):
    fig.add_annotation(
        x=AUTHOR_LABEL_X, y=r_i,
        text=a, showarrow=False,
        xanchor='right', yanchor='middle',
        font=dict(family=FONT, size=11, color='#333'),
    )

# ----------------------------------------------------------------------
# 8. Layout
# ----------------------------------------------------------------------
fig.update_layout(
    font=dict(family=FONT, size=11),
    plot_bgcolor='white',
    xaxis=dict(
        range=[1178, KMAX + 3],       # extra left room for long author names
        showticklabels=False,
        showline=False, showgrid=False, zeroline=False,
    ),
    yaxis=dict(
        range=[len(authors_ordered) - 0.5, -3.0],   # extra top room for topic labels
        showticklabels=False,
        showline=False, showgrid=False, zeroline=False,
    ),
    width=1000, height=max(560, 40 + 28*len(authors_ordered)),
    margin=dict(l=20, r=90, t=40, b=20),
)

# ----------------------------------------------------------------------
# 9. Save
# ----------------------------------------------------------------------
OUT = OUT_DIR
html = os.path.join(OUT, 'fig3_TextReuseHeatmap.html')
png  = os.path.join(OUT, 'fig3_TextReuseHeatmap.png')
svg  = os.path.join(OUT, 'fig3_TextReuseHeatmap.svg')
fig.write_html(html, include_plotlyjs='cdn')
w, h = 1000, max(560, 40 + 28*len(authors_ordered))
fig.write_image(png, width=w, height=h, scale=2)
fig.write_image(svg, width=w, height=h)
print('saved:', png)
fig.show()
