"""
Build script for fig 3 · Text-Reuse & Mentions Heatmap (Author × Topic)
Reads code_fig3.py and generates the notebook.
"""
import nbformat, os
from nbclient import NotebookClient

HERE = os.path.dirname(os.path.abspath(__file__))
CODE_FILE = f'{HERE}/code_fig3.py'
OUT_NB = os.path.join(HERE, '..', 'notebooks', 'fig3_TextReuseHeatmap.ipynb')

with open(CODE_FILE, encoding='utf-8') as f:
    code = f.read()

MD = """# fig 3 · Text-Reuse & Mentions Heatmap

- Rows: authors (grouped by school — Buddhist ordered by floruit; Non-Buddhist grouped by tradition)
- Columns: four topics (column width proportional to kārikā range)
- Cell color intensity: combined count of `<q>` (text-reuse) and `<rs>` (mentions)
- Data source: `TSP-17-tei-v2.0.0.xml`
"""

nb = nbformat.v4.new_notebook()
nb.cells = [
    nbformat.v4.new_markdown_cell(MD),
    nbformat.v4.new_code_cell(code),
]
client = NotebookClient(nb, timeout=300, kernel_name='python3', resources={'metadata': {'path': os.path.join(HERE, os.pardir)}})
client.execute()
nbformat.write(nb, OUT_NB)
print(f'Notebook: {OUT_NB}')
