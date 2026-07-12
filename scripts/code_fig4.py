# fig 4 · Historical Network of Text-Reuse and Commentary
# Network of 5th–8th century Indian intellectuals.
# Used by build_fig4_*.py to generate the notebook.
# After editing, run build_*.py to regenerate the notebook.

import os, math
from collections import Counter
from lxml import etree
import plotly.graph_objects as go

# ----------------------------------------------------------------------
# 0. paths (autodetect)
# ----------------------------------------------------------------------
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
XML = XML_PATH
OUT = OUT_DIR
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
TEI = '{http://www.tei-c.org/ns/1.0}'
XML_ID = '{http://www.w3.org/XML/1998/namespace}id'
tree = etree.parse(XML); root = tree.getroot()

# ----------------------------------------------------------------------
# 1. text-reuse (q) + mention (rs) counts
# ----------------------------------------------------------------------
# Method C: derive TEXT_TO_PERSON from <listBibl> in TEI header.
# Supplemented with hardcoded entries for ids not present in <listBibl>
# (e.g. NB→Dharmakīrti for Nyāyabindu, NV→Uddyotakara for Nyāyavārttika,
# and internal pointers like TS/TSP).
def _derive_text_to_person(root):
    out = {}
    for b in root.iter(TEI+'bibl'):
        xid = b.get(XML_ID)
        a = b.find(TEI+'author')
        if a is not None and xid:
            key = (a.get('key') or '').lstrip('#') or a.text
            if key:
                out[xid] = key
    return out
TEXT_TO_PERSON = _derive_text_to_person(root)
# Supplement: ids not registered in <listBibl> but referenced in <q @source>
TEXT_TO_PERSON.update({
    'NB':'Dharmakīrti',
    'PSṬ':'Jinendrabuddhi',
    'Nyāyamukha':'Dignāga',
    'TS':'Śāntarakṣita',
    'TSP':'Kamalaśīla',
    'NV':'Uddyotakara',
})
# Sort keys by length descending so longest-prefix wins
# (e.g., "TSP1220" matches "TSP" before "TS").
_PREFIX_KEYS = sorted(TEXT_TO_PERSON, key=len, reverse=True)

# Alias resolution: normalize surface-form ids (e.g., Bhāradvāja) to
# canonical ids (e.g., Uddyotakara) via <relation name="aliasOf">.
ALIAS_TO_CANONICAL = {}
for rel in root.iter(TEI+'relation'):
    if rel.get('name') == 'aliasOf':
        active = (rel.get('active') or '').lstrip('#')
        passive = (rel.get('passive') or '').lstrip('#')
        if active and passive:
            ALIAS_TO_CANONICAL[active] = passive

def resolve_one(raw):
    raw = raw.lstrip('#')
    if raw in TEXT_TO_PERSON: return ALIAS_TO_CANONICAL.get(TEXT_TO_PERSON[raw], TEXT_TO_PERSON[raw])
    for k in _PREFIX_KEYS:
        if raw.startswith(k): return ALIAS_TO_CANONICAL.get(TEXT_TO_PERSON[k], TEXT_TO_PERSON[k])
    return ALIAS_TO_CANONICAL.get(raw, raw) or None

def resolve_authors(elem):
    """Set of authors for a <q>. @who has priority (multi-token); fallback to @source (multi-token)."""
    who = elem.get('who') or ''
    src = elem.get('source') or ''
    authors = set()
    # @who has priority (multi-token supported)
    who_tokens = [t for t in who.split() if t.startswith('#')]
    if who_tokens:
        for tok in who_tokens:
            a = tok[1:]  # who directly references person id
            if a: authors.add(a)
        return authors
    # Fallback to @source (multi-source → deduplicated author set)
    if src and src != 'unknown':
        for tok in src.split():
            a = resolve_one(tok)
            if a: authors.add(a)
    return authors

cnt = Counter()
for q in root.findall('.//tei:q', NS):
    for author in resolve_authors(q):
        cnt[author] += 1
# rs: count each token of a multi-token @key (e.g., "Bharga Bhāradvāja").
# If type="text", resolve author via TEXT_TO_PERSON.
# Aliases (e.g., Bhāradvāja → Uddyotakara) are normalized to canonical ids.
for r in root.findall('.//tei:rs', NS):
    k = (r.get('key') or r.get('ref') or '').lstrip('#')
    if not k: continue
    is_text = (r.get('type') == 'text')
    seen = set()
    for tok in k.split():
        tok = tok.lstrip('#')
        if not tok: continue
        if is_text:
            tok = TEXT_TO_PERSON.get(tok, tok)
        tok = ALIAS_TO_CANONICAL.get(tok, tok)
        if tok not in seen:
            seen.add(tok); cnt[tok] += 1

cnt.pop('Śāntarakṣita', None)
cnt.pop('Kamalaśīla', None)

# ----------------------------------------------------------------------
# 2. node table
# ----------------------------------------------------------------------
def year_to_y(year):
    return -((year - 400) / 80.0)

# ─── Method A: derive year + school per person from <listPerson> ────────
# Method B: derive COMMENTARY from <listRelation type="commentaries">.
# Visual choices (x position, hollow flag, label offsets) stay in code —
# they are presentation, not data.

VISUAL = {
    'Dignāga':         dict(x=-3.0),
    'Dharmakīrti':     dict(x=-3.0),
    'Devendrabuddhi':  dict(x=-3.0),
    'Śākyabuddhi':     dict(x=-3.8, hollow=True, y_override=-4.2),
    'Vinītadeva':      dict(x=-5.5, hollow=True, y_override=-4.3),
    'Jinendrabuddhi':  dict(x=-7.0, hollow=True, y_override=-4.6),
    'Dharmottara':     dict(x=-5.5, hollow=True),
    'Śāntarakṣita':    dict(x=-1.5),
    'Kamalaśīla':      dict(x= 0.0, label_below=True),
    'Bhartṛhari':      dict(x= 4.0),
    'Uddyotakara':     dict(x= 1.6, y_override=-2.5),
    'Śaṅkarasvāmin':   dict(x= 3.1, y_override=-3.3),
    'Bhāvivikta':      dict(x= 3.5, y_override=-2.5),
    'Kumārila':        dict(x= 5.7),
    'Sumati':          dict(x= 6.7),
    'Bharga':          dict(x= 1.6, y_override=-1.8),
}

# Author identity for 'Ego' visual school is the dissertation's focal authors:
EGO_PERSONS = {'Śāntarakṣita', 'Kamalaśīla'}

# Map TEI affiliation key → visual school category.
# BUDDHIST_ORGS derived from <listOrg>: any <org> with @type="Buddhist".
BUDDHIST_ORGS = {org.get(XML_ID) for org in root.iter(TEI+'org')
                 if org.get('type') == 'Buddhist' and org.get(XML_ID)}

def _school_of(pid, aff_key):
    if pid in EGO_PERSONS: return 'Ego'
    if aff_key in BUDDHIST_ORGS: return 'Buddhist'
    return 'Non-Buddhist'

NODES = []
for person in root.iter(TEI+'person'):
    pid = person.get(XML_ID)
    if not pid or pid not in VISUAL: continue       # skip alias stubs etc.
    floruit = person.find(TEI+'floruit')
    if floruit is not None:
        nb = int(floruit.get('notBefore', '0500'))
        na = int(floruit.get('notAfter', nb))
        year = (nb + na) // 2
    else:
        year = None
    aff = person.find(TEI+'affiliation')
    aff_key = (aff.get('key') if aff is not None else '').lstrip('#')
    school = _school_of(pid, aff_key)
    node = dict(id=pid, year=year, school=school, **VISUAL[pid])
    NODES.append(node)

# Stable presentation order (matches original)
_ORDER = ['Dignāga','Dharmakīrti','Devendrabuddhi','Śākyabuddhi','Vinītadeva',
          'Jinendrabuddhi','Dharmottara','Śāntarakṣita','Kamalaśīla','Bhartṛhari',
          'Uddyotakara','Śaṅkarasvāmin','Bhāvivikta','Kumārila','Sumati','Bharga']
NODES.sort(key=lambda n: _ORDER.index(n['id']) if n['id'] in _ORDER else 99)

def year_to_y(year):
    if year is None: return 0
    return -((year - 400) / 80.0)

for n in NODES:
    n['count'] = cnt.get(n['id'], 0)
    n['hollow'] = n.get('hollow', False)
    n['y'] = n['y_override'] if n.get('y_override') is not None else year_to_y(n['year'])

idx = {n['id']: n for n in NODES}

TEXT_REUSE_AND_MENTIONS = [(p['id'], p['count']) for p in NODES
             if p['count'] > 0 and not p.get('hollow', False)
             and p['id'] not in EGO_PERSONS]
SCHOLARLY_PARALLEL = [p['id'] for p in NODES if p.get('hollow', False)]

# Method B: derive COMMENTARY from <listRelation>
def _derive_commentary(root):
    out = []
    for rel in root.iter(TEI+'relation'):
        if rel.get('name') != 'commentaryOn': continue
        a = (rel.get('active') or '').lstrip('#')
        p = (rel.get('passive') or '').lstrip('#')
        if a and p:
            out.append((a, p))
    return out
COMMENTARY = _derive_commentary(root)

# Visual push override for the Kamalaśīla→Śāntarakṣita arc (aesthetic)
PUSH_OVERRIDES = {('Kamalaśīla', 'Śāntarakṣita'): 0.25}

# ----------------------------------------------------------------------
# 3. visual constants
# ----------------------------------------------------------------------
FONT  = 'Menlo, Monaco, Consolas, monospace'
COLOR = {
    'Buddhist'    : '#4E79A7',
    'Non-Buddhist': '#E15759',
    'Ego'         : '#76B7B2',
}
YELLOW           = '#B8860B'
YELLOW_EDGE_NODES = {'Jinendrabuddhi', 'Dharmottara'}    # render their edges in yellow
SKIP_EGOSANTARAKSITA = {'Jinendrabuddhi', 'Dharmottara', 'Devendrabuddhi'} # skip Śāntarakṣita connection
SKIP_ALL_EGO = {'Śākyabuddhi', 'Vinītadeva'}             # no XML basis — skip all ego connections

def add_curve(fig, p0, p1, color, dash='solid', width=1.5,
              opacity=0.85, ctrl=None):
    fig.add_trace(go.Scatter(
        x=[p0[0], p1[0]], y=[p0[1], p1[1]], mode='lines',
        line=dict(color=color, width=width, dash=dash),
        opacity=opacity, hoverinfo='skip', showlegend=False))

fig = go.Figure()

# ----- text-reuse & mention edges (→ Kamalaśīla & → Śāntarakṣita) ----
ego_K = idx['Kamalaśīla']; ego_S = idx['Śāntarakṣita']
for pid, c in TEXT_REUSE_AND_MENTIONS:
    p = idx[pid]
    # → Kamalaśīla (solid, as before)
    add_curve(fig, (p['x'], p['y']), (ego_K['x'], ego_K['y']),
              color='rgba(0,0,0,0.75)', width=1.5, opacity=0.85)
    # → Śāntarakṣita: skip specific nodes; use different dashed pattern (fine dots)
    # Dignāga, Dharmakīrti, Sumati rendered as solid
    if pid not in SKIP_EGOSANTARAKSITA:
        _dash = 'solid' if pid in {'Dignāga','Dharmakīrti','Kumārila'} else '2px,3px'
        add_curve(fig, (p['x'], p['y']), (ego_S['x'], ego_S['y']),
                  color='rgba(0,0,0,0.75)', dash=_dash,
                  width=1.5, opacity=0.85)

# ----- scholarly-parallel edges (yellow for Jinendrabuddhi, Dharmottara) -----
for pid in SCHOLARLY_PARALLEL:
    if pid in SKIP_ALL_EGO:
        continue                # skip ego connection when there is no XML basis
    p = idx[pid]
    edge_color = YELLOW if pid in YELLOW_EDGE_NODES else 'rgba(0,0,0,0.75)'
    add_curve(fig, (p['x'], p['y']), (ego_K['x'], ego_K['y']),
              color=edge_color, dash='4px,3px', width=1.5, opacity=0.90)
    if pid not in SKIP_EGOSANTARAKSITA:
        add_curve(fig, (p['x'], p['y']), (ego_S['x'], ego_S['y']),
                  color='rgba(0,0,0,0.75)', dash='2px,3px',
                  width=1.5, opacity=0.85)

# ----- commentary edges -----------------------------------------------
def commentary_outer_ctrl(s, d, side, push=0.7):
    cx = (min if side=='Buddhist' else max)(s['x'], d['x']) + (-push if side=='Buddhist' else push)
    cy = (s['y'] + d['y']) / 2
    return (cx, cy)

for entry in COMMENTARY:
    src, dst = entry[0], entry[1]
    push = PUSH_OVERRIDES.get((src, dst), 0.9)
    s = idx[src]; d = idx[dst]
    is_ego = ('Kamalaśīla' in (src,dst)) or ('Śāntarakṣita' in (src,dst))
    col = COLOR['Ego'] if is_ego else COLOR['Buddhist']
    side = 'Non-Buddhist' if (s['school']=='Non-Buddhist' and d['school']=='Non-Buddhist') else 'Buddhist'
    ctrl = commentary_outer_ctrl(s, d, side, push=push)
    add_curve(fig, (s['x'], s['y']), (d['x'], d['y']),
              color=col, dash='4px,3px', width=1.5, opacity=0.95, ctrl=ctrl)

# ----- nodes ----------------------------------------------------------
def node_size(c, hollow=False):
    return 20 if hollow else 18 + 6*math.sqrt(c)

for school in ['Buddhist','Non-Buddhist','Ego']:
    filled = [n for n in NODES if n['school']==school and not n['hollow']]
    if filled:
        fig.add_trace(go.Scatter(
            x=[n['x'] for n in filled], y=[n['y'] for n in filled],
            mode='markers',
            marker=dict(size=[node_size(n['count']) for n in filled],
                        color=COLOR[school],
                        line=dict(color='white', width=2), opacity=0.95),
            hovertext=[f"{n['id']} · {n['count']} text-reuse + mention(s)" for n in filled],
            hoverinfo='text', showlegend=False))

hollow_nodes = [n for n in NODES if n['hollow']]
if hollow_nodes:
    fig.add_trace(go.Scatter(
        x=[n['x'] for n in hollow_nodes], y=[n['y'] for n in hollow_nodes],
        mode='markers',
        marker=dict(size=[node_size(n['count'], hollow=True) for n in hollow_nodes],
                    color='white',
                    line=dict(color=[COLOR[n['school']] for n in hollow_nodes], width=1.4),
                    opacity=0.95),
        hovertext=[f"{n['id']} · indirect parallel" for n in hollow_nodes],
        hoverinfo='text', showlegend=False))

# ----- node labels ----------------------------------------------------
for n in NODES:
    sz  = node_size(n['count'], hollow=n['hollow'])
    # Uniform visual spacing for all nodes (node radius + constant gap)
    node_r = sz / 320.0    # data unit
    LABEL_GAP = 0.05
    if n.get('label_below'):
        ly, ya = n['y'] - node_r - LABEL_GAP, 'top'
    else:
        ly, ya = n['y'] + node_r + LABEL_GAP, 'bottom'
    fig.add_annotation(x=n['x'], y=ly, text=n['id'],
                       showarrow=False, xanchor='center', yanchor=ya,
                       font=dict(family=FONT, size=13, color='#111'),
                       bgcolor='rgba(255,255,255,0.88)',
                       bordercolor='rgba(0,0,0,0)', borderpad=1)
    if n['count'] > 0 and not n['hollow']:
        fs = max(11, min(17, sz * 0.38))
        fig.add_annotation(x=n['x'], y=n['y'], text=f"<b>{n['count']}</b>",
                           showarrow=False, xanchor='center', yanchor='middle',
                           font=dict(family=FONT, size=fs, color='white'))

# ----- century guides -------------------------------------------------
CENTURY_BANDS = [(5,-0.625),(6,-1.875),(7,-3.125),(8,-4.375)]
for y_sep in [0,-1.25,-2.5,-3.75,-5.0]:
    fig.add_shape(type='line', x0=-8.0, x1=7.5, y0=y_sep, y1=y_sep,
                  line=dict(color='#eee', width=1, dash='dot'), layer='below')
for c, ym in CENTURY_BANDS:
    fig.add_annotation(x=-8.2, y=ym, text=f"<b>{c}th C.E.</b>",
                       showarrow=False, xanchor='right', yanchor='middle',
                       font=dict(family=FONT, size=12, color='#666'))

# ----- Bharga "unknown" irregular ellipse (cubic bezier, dashed) -------------
b = idx['Bharga']
bx, by = b['x'], b['y']
rx, ry = 0.55, 0.40
k = 0.55
fig.add_shape(type='path',
    path=(f"M {bx},{by-ry} "
          f"C {bx+rx*k*1.05},{by-ry*1.02} {bx+rx*1.02},{by-ry*k*0.96} {bx+rx},{by} "
          f"C {bx+rx*0.98},{by+ry*k*1.04} {bx+rx*k*0.97},{by+ry} {bx},{by+ry*1.02} "
          f"C {bx-rx*k*1.03},{by+ry*0.98} {bx-rx*1.01},{by+ry*k*1.02} {bx-rx},{by} "
          f"C {bx-rx*0.99},{by-ry*k*0.97} {bx-rx*k*1.02},{by-ry} {bx},{by-ry} Z"),
    line=dict(color='#bbb', width=0.9, dash='dot'),
    fillcolor='rgba(0,0,0,0)', layer='below')
fig.add_annotation(x=bx, y=by+ry+0.08, text="unknown",
                   showarrow=False, xanchor='center', yanchor='bottom',
                   font=dict(family=FONT, size=11, color='#888'))

# ----- inline legend (5th CE band; edges row + nodes row) --------------------
fig.add_annotation(
    xref='x', yref='y', x=0.0, y=-0.38,
    xanchor='center', yanchor='middle', showarrow=False, align='center',
    text=(f"<span style='color:{COLOR['Buddhist']}'>┄┄┄</span> commentary relation"
          " &nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp; "
          "<span style='color:rgba(0,0,0,0.85)'>───</span> TS/P text-reuse"
          " &nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp; "
          "<span style='color:rgba(0,0,0,0.85)'>┄┄┄</span> indirect parallel"
          " &nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp; "
          f"<span style='color:{YELLOW}'>┄┄┄</span> parallel"
          "<br>"
          "● text-reused or mentioned &nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp; ○ parallel only"
          " &nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp; "
          "<span style='color:#888'>node size ∝ count</span>"),
    font=dict(family=FONT, size=15, color='#222'),
    bgcolor='rgba(255,255,255,0.82)',
    bordercolor='rgba(180,180,180,0.4)', borderpad=8)

# ----- layout ---------------------------------------------------------
fig.update_layout(
    font=dict(family=FONT, size=11),
    title=None,
    xaxis=dict(visible=False, range=[-9.0, 7.6]),
    yaxis=dict(visible=False, range=[-5.3, 0.15]),
    plot_bgcolor='white',
    width=1200, height=900,
    margin=dict(l=55, r=10, t=10, b=20),
    showlegend=False,
)

# save outputs
html = os.path.join(OUT, 'fig4_HistoricalNetwork.html')
png  = os.path.join(OUT, 'fig4_HistoricalNetwork.png')
svg  = os.path.join(OUT, 'fig4_HistoricalNetwork.svg')
fig.write_html(html, include_plotlyjs='cdn')
fig.write_image(png,  width=1200, height=900, scale=2)
fig.write_image(svg,  width=1200, height=900)
print('saved:', html); print('saved:', png); print('saved:', svg)
fig.show()

# ── fig4 final output ──────────────────────────────────────────────────────
out_png = os.path.join(OUT, 'fig4_HistoricalNetwork.png')
out_svg = os.path.join(OUT, 'fig4_HistoricalNetwork.svg')
fig.write_image(out_png, width=1200, height=900, scale=2)
fig.write_image(out_svg, width=1200, height=900)
print(f'[OK] {out_png}')
print(f'[OK] {out_svg}')
