"""
Build script for fig 1 · Topic Debate Flow
Reads code_fig1.py and generates the notebook.
"""
import nbformat, os
from nbclient import NotebookClient

HERE = os.path.dirname(os.path.abspath(__file__))
CODE_FILE = f'{HERE}/code_fig1.py'
OUT_NB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'notebooks', 'fig1_TopicDebateFlow.ipynb')

with open(CODE_FILE, encoding='utf-8') as f:
    code = f.read()

MD = """# fig 1 · Topic Debate Flow

Vertical alignment of the four topics and each opponent's debate segments.

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
