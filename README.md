# TSP-17 · Tattvasaṅgrahapañjikā chapter 17 (*pratyakṣalakṣaṇaparīkṣā*)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21321381.svg)](https://doi.org/10.5281/zenodo.21321381)

A TEI/XML encoding of the 17th chapter of Kamalaśīla's *Tattvasaṅgrahapañjikā*
(kārikās 1212–1360). The encoding annotates the chapter's debate structure
(*vāda* sections with *pūrvapakṣa*/*uttarapakṣa* divisions), text reuse,
and referring strings for persons, schools, and works. Jupyter notebooks and build scripts
reproduce four visualizations of the debate structure and the text-reuse
and mention network.

**Author**: Yulhui Cho · yulhuicho@gmail.com
**Version**: 2.0.0 · **Released**: 2026-07-12
**License**: [CC BY 4.0](LICENSE) (data & figures) · [MIT](LICENSE) (code)

---

## Repository layout

```
.
├── data/
│   └── TSP-17-tei-v2.0.0.xml       TEI-encoded text (kārikās 1212–1360)
├── schema/
│   ├── TSP-17-schema.odd           TEI ODD schema (source; defines encoding conventions)
│   └── TSP-17-schema.dtd           Generated DTD (for XML validation)
├── notebooks/
│   ├── fig1_TopicDebateFlow.ipynb        Vertical kārikā flow with debates & topics
│   ├── fig2_PakshaLength.ipynb           pūrvapakṣa/uttarapakṣa length by opponent
│   ├── fig3_TextReuseHeatmap.ipynb       Author × Topic text-reuse and mentions heatmap
│   └── fig4_HistoricalNetwork.ipynb      5th–8th c. text-reuse and commentary network
├── scripts/                         Build scripts (regenerate notebooks from code)
│   ├── build_fig1.py  + code_fig1.py
│   ├── build_fig2.py  + code_fig2.py
│   ├── build_fig3.py  + code_fig3.py
│   └── build_fig4.py  + code_fig4.py
├── figures/                         Pre-rendered PNG + SVG (fig3–4 also interactive HTML)
├── requirements.txt                 Python dependencies
├── CITATION.cff                     Citation metadata (GitHub-recognized)
├── LICENSE                          CC BY 4.0 + MIT dual license
└── README.md                        This file
```

---

## Text and encoding

- **Text**: *Tattvasaṅgrahapañjikā* chapter 17 (*pratyakṣalakṣaṇaparīkṣā*)
- **Author**: Kamalaśīla (8th c. CE)
- **Base text**: Reconstituted from published editions
  (Shastri 1968 · Krishnamacharya 1926), with editorial variants between
  these editions recorded in `<app>` elements
- **Note on manuscript readings**: This encoding is *not* a full
  collation of the Sanskrit manuscript tradition. Manuscript readings
  from the Jaisalmer (`#Jms`) and Pāṭaṇ (`#Pams`) codices are included
  only in exceptional cases — for instance, where a manuscript reading
  is adopted in the `<lem>` (e.g., `eva sa bruvan` at TS1235) or where a
  marginal note provides a scholarly identification of a pronominal
  referent (e.g., `sa = sumatiḥ` at TSP1266, `tad = kumārilaḥ` at
  TSP1296).
- **Encoding**: TEI P5 (Text Encoding Initiative), UTF-8
- **Scope**: 149 kārikās (1212–1360)
- **Schema**: Project-specific ODD in `schema/TSP-17-schema.odd` (with generated
  DTD `schema/TSP-17-schema.dtd`), extending TEI P5 with the semantic
  attributes and value lists used in this edition

### Semantic annotations

| element | purpose | count |
|---|---|---|
| `<div type="topic">` | four philosophical topics | 4 |
| `<div type="vāda">` | debate section grouped by opponent | 9 |
| `<div type="pūrvapakṣa">` | opponent's position | 12 |
| `<div type="uttarapakṣa">` | Śāntarakṣita's reply verses | 12 |
| `<q>` | text reuse (quotation, reference, emendation, internal) | 74 |
| `<rs>` | referring string for persons, groups, works, and pronominal substitutes | 122 |
| `<person>` | historical scholar registered in header | 17 |
| `<org>` | philosophical school/tradition | 12 |
| `<bibl>` | source text or manuscript witness registered in header | 16 primary + 2 secondary |
| `<relation>` | commentary / membership / alias relations | 16 |
| `<app>` | text-critical apparatus with `<lem>` and `<rdg>` variants | 64 |

### Attribute conventions

- `@type` on `<q>`: `quotation` / `reference` / `emendation` / `internal`
- `@ana` on `<q>` and `<rs>`: `authoritative` / `neutral` / `critical` / `affirmative`
- `@cert` on `<rs>` and `<q>`: `high` / `medium` / `low` / `unknown`
  (TEI standard `teidata.certainty`; project convention: `medium` for
  generalizing suffixes such as `-ādi`; `low` for identifications based
  on marginal evidence or contextual inference alone)
- `@source` on `<q>` and `<lem>`/`<rdg>`: `#<bibl-id>` (possibly multiple,
  space-separated)
- Sentinel value `unknown` on `@source` and `@key`: unidentified source or
  referent (project convention — a literal string, not a pointer; documents
  validate against the project DTD, but strict TEI RELAX NG schemas will
  flag these values)
- `@who` on `<q>`: `#<person-id>` (semantic author; overrides `@source` in counting;
  supports multi-token)
- `@key` on `<rs>`: entity id (possibly multiple, space-separated)
- `@n` on `<q>`: locus within source (`SRC:LOCUS` prefix for multi-source)
- `@resp` on `<rs>`: attribution of identification to a witness or scholar
  (e.g., `resp="#Jms #Pams"` for identifications supported by marginal notes
  in the Jaisalmer and Pāṭaṇ manuscripts)

---

## Figures

### fig 1 · Topic Debate Flow
Vertical `kārikā` axis (1212–1360). Left bar shows debate segments by
opponent; right bar shows the four topical divisions
(*kalpanāpoḍha* · *abhrānta* · *sukhādisvasaṃvitti* · *pramāṇaphala*).

### fig 2 · Pakṣa Length
Bar chart comparing the length (in kārikās) of each opponent's `pūrvapakṣa`
and Śāntarakṣita's `uttarapakṣa`. Ratios (uttara / pūrva) shown above each
pair.

### fig 3 · Text-Reuse & Mentions Heatmap
Author × Topic matrix. Rows = authors and schools grouped by affiliation
(Buddhist / uncertain / non-Buddhist); columns = the four topics (width
proportional to `kārikā` range). Cell intensity = combined count of `<q>`
(text-reuse) and `<rs>` (mentions).

### fig 4 · Historical Network of Text-Reuse and Commentary
Time-ordered network of intellectuals referenced in TSP-17. Y-axis = century;
x-position carries no semantic meaning (arranged only for visual readability).
Node size ∝ text-reuse and mention count. Edge styles distinguish commentary
relations, TS/P text-reuse, indirect parallels, and parallels, matching the
in-figure legend.

---

## Counting conventions

**fig 3 (topic-restricted)**
- `<q>` counted only if `@type ∈ {quotation, reference, emendation}` AND inside
  a `<div type="topic">`
- `<rs>` counted only if `@key` present AND inside a topic
- Author resolution: `@who` (with multi-token support) overrides `@source`;
  otherwise `@source` tokens are resolved via `TEXT_TO_PERSON` (bibl → author),
  then deduplicated as a set

**fig 4 (chapter-wide)**
- All `<q>` counted regardless of `@type`
- All `<rs>` counted regardless of location
- Same author-resolution logic as fig 3
- Ego authors (Śāntarakṣita, Kamalaśīla) removed from text-reuse and mention counts

**Multi-source deduplication**
- `source="#PS #PV"` where PS→Dignāga, PV→Dharmakīrti → each counted +1
- `source="#PV #PVin"` where both → Dharmakīrti → counted +1 (dedup)

---

## Reproducing the figures

### Requirements
- Python ≥ 3.9
- Dependencies in `requirements.txt`

### Setup
```bash
git clone https://github.com/yulhuicho/TSP-17-TEI
cd TSP-17-TEI
pip install -r requirements.txt
```

### Two ways to regenerate

**(A) Run the notebooks directly (recommended for readers)**
```bash
jupyter lab notebooks/
```
Or execute headlessly:
```bash
cd notebooks
jupyter nbconvert --to notebook --execute fig3_TextReuseHeatmap.ipynb
```

**(B) Rebuild via scripts (recommended for editing)**

The `scripts/` folder contains build scripts that regenerate the notebooks from
plain Python source (`code_figN.py`). This is convenient for version control
(smaller diffs than `.ipynb` JSON) and for automated workflows.

```bash
cd scripts
python build_fig1.py    # → notebooks/fig1_TopicDebateFlow.ipynb (regenerated + executed)
python build_fig2.py
python build_fig3.py
python build_fig4.py
```

`code_figN.py` are ordinary Python files that can be edited with any editor,
with syntax highlighting and linting support. Running the corresponding
`build_figN.py` produces the notebook and its outputs. The notebooks themselves
can be re-run to regenerate the PNG/SVG figures in `figures/`.

---

## Citation

If you use this data or code, please cite as:

> Cho, Yulhui. (2026). *Tattvasaṅgrahapañjikā chapter 17
> (pratyakṣalakṣaṇaparīkṣā): TEI-Encoded Reference Dataset*
> (Version 2.0.0) [Dataset]. Zenodo.
> https://doi.org/10.5281/zenodo.21321381

A machine-readable [`CITATION.cff`](CITATION.cff) is included for automatic
citation-metadata extraction (BibTeX, APA, RIS, etc.).

---

## License

- **Data, schema, and figures** (`data/`, `schema/`, `figures/`):
  licensed under the Creative Commons Attribution 4.0 International License
  ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)). The ODD file
  incorporates material from the TEI P5 Guidelines, which are dually licensed
  under CC BY and BSD-2-Clause by the TEI Consortium.
- **Code** (`scripts/`, notebook code cells): licensed under the
  [MIT License](https://opensource.org/licenses/MIT).

See [`LICENSE`](LICENSE) for the full text of both.

Attribution requires citing the author, project title, version, and a link
to this repository.

---

## Acknowledgments

- TEI Consortium for the P5 guidelines
- Editorial base texts:
  - Shastri, D. (ed.). 1968. *Tattvasaṅgraha of Ācārya Shāntarakṣita with the
    Commentary 'Pañjikā' of Shrī Kamalashīla* (Bauddha Bharati Series).
  - Krishnamacharya, E. (ed.). 1926. *Tattvasaṅgraha of Śāntarakṣita with the
    Commentary of Kamalaśīla* (Gaekwad's Oriental Series).
- Visualization stack: `lxml` · `plotly` · `nbformat` · `nbclient` · `kaleido`

---

## Contact

For questions, corrections, or contributions:
- Open a GitHub issue on this repository, or
- Contact **Yulhui Cho** — <yulhuicho@gmail.com>
