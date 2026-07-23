import ast
import json
from pathlib import Path
from unittest import TestCase


NOTEBOOKS = (
    Path("notebooks/01_GOES_true_color.ipynb"),
    Path("notebooks/02_VIIRS_true_color.ipynb"),
    Path("notebooks/03_GOES_ash_rgb.ipynb"),
    Path("notebooks/04_GOES_so2_rgb.ipynb"),
)
GOES_NOTEBOOKS = (NOTEBOOKS[0], NOTEBOOKS[2], NOTEBOOKS[3])
EXPECTED_DOMAINS = {
    NOTEBOOKS[0]: "DOMAIN = (-170.0, 53.0, -160.0, 58.0)",
    NOTEBOOKS[1]: "DOMAIN = (0.0, 35.0, 10.0, 38.0)",
    NOTEBOOKS[2]: "DOMAIN = (-170.0, 53.0, -160.0, 58.0)",
    NOTEBOOKS[3]: "DOMAIN = (-170.0, 53.0, -160.0, 58.0)",
}


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
                self.assertIn(EXPECTED_DOMAINS[path], all_source)
                self.assertIn("display(Image(filename=str(OUTPUT", all_source)
                self.assertIn("save_dataset_with_lonlat_grid", all_source)
                self.assertNotIn("![Reference", all_source)

                embedded_pngs = [
                    output["data"]["image/png"]
                    for cell in notebook["cells"]
                    for output in cell.get("outputs", [])
                    if "image/png" in output.get("data", {})
                ]
                expected_count = 4 if path in GOES_NOTEBOOKS else 1
                self.assertEqual(len(embedded_pngs), expected_count)
                self.assertGreater(max(map(len, embedded_pngs)), 10_000)

    def test_goes_notebooks_show_source_coverages_in_the_requested_order(self):
        expected_headings = (
            "## 1. Full Disk",
            "## 2. CONUS",
            "## 3. Mesoscale 1",
            "## 4. User-defined",
        )

        for path in GOES_NOTEBOOKS:
            with self.subTest(path=path):
                notebook = json.loads(path.read_text(encoding="utf-8"))
                all_source = "\n".join(
                    "".join(cell["source"]) for cell in notebook["cells"]
                )
                positions = [all_source.index(heading) for heading in expected_headings]
                self.assertEqual(positions, sorted(positions))
                self.assertIn('COVERAGES = ("full_disk", "conus", "mesoscale")', all_source)
                self.assertIn("download_coverage", all_source)
                self.assertIn("2023-10-03 19:00 UTC", all_source)

    def test_volcanic_notebooks_document_the_requested_recipes(self):
        ash = json.loads(NOTEBOOKS[2].read_text(encoding="utf-8"))
        so2 = json.loads(NOTEBOOKS[3].read_text(encoding="utf-8"))
        ash_source = "\n".join("".join(cell["source"]) for cell in ash["cells"])
        so2_source = "\n".join("".join(cell["source"]) for cell in so2["cells"])

        self.assertIn("2023-10-03 19:00 UTC", ash_source)
        self.assertIn('COMPOSITE = "ash"', ash_source)
        self.assertIn('PRODUCT_LABEL = "Ash RGB"', ash_source)
        self.assertIn("C15 (12.3 µm) − C13 (10.3 µm)", ash_source)

        self.assertIn("2023-10-03 19:00 UTC", so2_source)
        self.assertIn('COMPOSITE = "volcanic_emissions"', so2_source)
        self.assertIn('PRODUCT_LABEL = "SO₂ RGB"', so2_source)
        self.assertIn("C09 (6.95 µm) − C10 (7.34 µm)", so2_source)

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
