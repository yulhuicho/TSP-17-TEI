# fig 2 · Pakṣa Length
# Comparison of pūrvapakṣa/uttarapakṣa length (in kārikās) by opponent.
# Used by build_fig2_*.py to generate the notebook.
# After editing, run build_*.py to regenerate the notebook.

"""fig2 — Pakṣa Length: Tableau 10 palette."""
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
TEI = '{http://www.tei-c.org/ns/1.0}'
XML = '{http://www.w3.org/XML/1998/namespace}'
FONT_FAMILY = 'Menlo, Monaco, Consolas, monospace'
FIG_W, FIG_H = 1150, 620

tree = etree.parse(XML_PATH); root = tree.getroot()

rows = []
for d in root.iter(TEI+'div'):
    if d.get('type') not in ('pūrvapakṣa', 'uttarapakṣa'): continue
    xid = d.get(XML+'id') or ''
    parts = xid.split('_')
    opp = parts[1] if len(parts) >= 3 else ''
    rng = parts[-1]
    if '-' in rng:
        a, b = rng.split('-', 1); s, e = int(a), int(b)
    else: s = e = int(rng)
    rows.append({'side': d.get('type'), 'opp': opp, 'start': s, 'end': e,
                 'length': e - s + 1})
df_pak = pd.DataFrame(rows).sort_values('start').reset_index(drop=True)

sections = []
for _, row in df_pak.iterrows():
    if sections and sections[-1]['opp'] == row['opp']:
        sec = sections[-1]
        sec['end'] = max(sec['end'], row['end'])
        sec[f"{row['side']}_len"] += row['length']
    else:
        sections.append({'opp': row['opp'], 'start': row['start'], 'end': row['end'],
                         'pūrvapakṣa_len':  row['length'] if row['side']=='pūrvapakṣa' else 0,
                         'uttarapakṣa_len': row['length'] if row['side']=='uttarapakṣa' else 0})
df_sec = pd.DataFrame(sections)
df_sec['label'] = df_sec.apply(lambda r: f"<b>{r['opp']}</b><br>{r['start']}–{r['end']}", axis=1)
df_sec['ratio'] = df_sec['uttarapakṣa_len'] / df_sec['pūrvapakṣa_len'].replace(0, pd.NA)

# Tableau 10 palette — aligned with fig1/3/4
COLOR_PURVA  = '#E15759'   # Tableau 10 coral red — opponent's position
COLOR_UTTARA = '#4E79A7'   # Tableau 10 steel blue — author's reply
COLOR_GREEN  = '#59A14F'   # Tableau 10 sage green for ▲
COLOR_RED    = '#E15759'   # Tableau 10 coral red for ▼

fig = go.Figure()

fig.add_trace(go.Bar(
    name="pūrvapakṣa (opponent's position)",
    x=df_sec['label'], y=df_sec['pūrvapakṣa_len'],
    marker=dict(color='white', line=dict(color=COLOR_PURVA, width=1.2),
                pattern=dict(shape='/', size=6, solidity=0.5,
                             fgcolor=COLOR_PURVA, bgcolor='white')),
    text=df_sec['pūrvapakṣa_len'], textposition='inside',
    textfont=dict(family=FONT_FAMILY, size=15, color='#333'),
    hovertemplate='<b>%{x}</b><br>pūrvapakṣa: %{y} kārikās<extra></extra>',
))
fig.add_trace(go.Bar(
    name='uttarapakṣa (reply)',
    x=df_sec['label'], y=df_sec['uttarapakṣa_len'],
    marker=dict(color=COLOR_UTTARA, line=dict(color=COLOR_UTTARA, width=0.8)),
    text=df_sec['uttarapakṣa_len'], textposition='inside',
    textfont=dict(family=FONT_FAMILY, size=15, color='white'),
    hovertemplate='<b>%{x}</b><br>uttarapakṣa: %{y} kārikās<extra></extra>',
))

for _, r in df_sec.iterrows():
    arrow = '▲' if r['ratio'] >= 1 else '▼'
    color = COLOR_GREEN if r['ratio'] >= 1 else COLOR_RED
    fig.add_annotation(
        x=r['label'], y=max(r['pūrvapakṣa_len'], r['uttarapakṣa_len']) + 0.5,
        text=f"<span style='color:{color}'><b>{arrow} {r['ratio']:.2f}</b></span>",
        showarrow=False, font=dict(family=FONT_FAMILY, size=13))

tot_p = int(df_sec['pūrvapakṣa_len'].sum())
tot_u = int(df_sec['uttarapakṣa_len'].sum())
fig.add_annotation(
    text=(f"Chapter totals: pūrva {tot_p} · uttara {tot_u}<br>"
          f"overall ratio = <b>{tot_u/tot_p:.2f}</b>"),
    xref='paper', yref='paper', x=0.99, y=0.97,
    xanchor='right', yanchor='top', showarrow=False, align='right',
    bgcolor='rgba(255,255,255,0.88)',
    bordercolor='#ccc', borderwidth=1, borderpad=7,
    font=dict(family=FONT_FAMILY, size=13, color='#333'))

fig.update_layout(
    title=None,
    font=dict(family=FONT_FAMILY, size=13, color='#222'),
    barmode='group', bargap=0.25, bargroupgap=0.08,
    xaxis=dict(
        title=None,
        tickfont=dict(family=FONT_FAMILY, size=13),
    ),
    yaxis=dict(
        title=dict(text='Number of kārikās',
                   font=dict(family=FONT_FAMILY, size=15)),
        tickfont=dict(family=FONT_FAMILY, size=13),
        gridcolor='#f0f0f0',
    ),
    plot_bgcolor='white', paper_bgcolor='white',
    width=FIG_W, height=FIG_H,
    margin=dict(l=75, r=35, t=40, b=50),
    legend=dict(orientation='v', x=0.99, y=0.86, xanchor='right', yanchor='top',
                font=dict(family=FONT_FAMILY, size=13),
                bgcolor='rgba(0,0,0,0)'),
)

out_png = os.path.join(OUT_DIR, 'fig2_PakshaLength.png')
out_svg = os.path.join(OUT_DIR, 'fig2_PakshaLength.svg')
fig.write_image(out_png, width=FIG_W, height=FIG_H, scale=2)
fig.write_image(out_svg, width=FIG_W, height=FIG_H)
print(f'[OK] {out_png}')
print(f'[OK] {out_svg}')
