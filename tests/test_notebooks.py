import ast
import json
from pathlib import Path
from unittest import TestCase


NOTEBOOKS = (
    Path("notebooks/01_GOES_true_color.ipynb"),
    Path("notebooks/02_VIIRS_true_color.ipynb"),
)
DECIMAL_DOMAIN = "DOMAIN = (-166.0, 54.0, -162.0, 56.0)"


class NotebookTests(TestCase):
    def test_notebooks_have_valid_structure_and_unique_cell_ids(self):
        for path in NOTEBOOKS:
            with self.subTest(path=path):
                notebook = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(notebook["nbformat"], 4)
                self.assertGreaterEqual(notebook["nbformat_minor"], 5)
                self.assertTrue(notebook["cells"])

                cell_ids = [cell["id"] for cell in notebook["cells"]]
                self.assertEqual(len(cell_ids), len(set(cell_ids)))

    def test_notebooks_use_decimal_domains_and_display_the_output(self):
        for path in NOTEBOOKS:
            with self.subTest(path=path):
                notebook = json.loads(path.read_text(encoding="utf-8"))
                all_source = "\n".join(
                    "".join(cell["source"]) for cell in notebook["cells"]
                )
                self.assertIn(DECIMAL_DOMAIN, all_source)
                self.assertIn("display(Image(filename=str(OUTPUT)))", all_source)

    def test_python_cells_compile(self):
        for path in NOTEBOOKS:
            notebook = json.loads(path.read_text(encoding="utf-8"))
            for cell in notebook["cells"]:
                if cell["cell_type"] != "code":
                    continue
                source = "".join(cell["source"])
                if source.lstrip().startswith("%"):
                    continue
                with self.subTest(path=path, cell=cell["id"]):
                    ast.parse(source)
