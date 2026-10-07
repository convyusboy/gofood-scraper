import csv
import json

import pytest

from gofood_scraper.config import HEADERS
from gofood_scraper.excel import column, new_results_workbook
from gofood_scraper.export import export, read_rows, summarize


@pytest.fixture
def xlsx(tmp_path):
    wb, sheet = new_results_workbook()
    data = [("A", "4.8", "Ayam"), ("B", "4.2", "Ayam"), ("C", "-", "Bakso")]
    for row, (name, rating, kind) in enumerate(data, start=2):
        sheet[column("Name") + str(row)] = name
        sheet[column("Rating") + str(row)] = rating
        sheet[column("Type") + str(row)] = kind
    path = tmp_path / "jakarta-near_me.xlsx"
    wb.save(path)
    return str(path)


def test_read_rows_keys_by_header(xlsx):
    rows = read_rows(xlsx)
    assert len(rows) == 3
    assert list(rows[0]) == HEADERS
    assert rows[0]["Name"] == "A" and rows[0]["Address"] == ""


def test_export_writes_csv_and_json(xlsx):
    paths = export(xlsx, ["csv", "json"])
    assert [p.rsplit(".", 1)[1] for p in paths] == ["csv", "json"]
    with open(paths[0], encoding="utf-8") as handle:
        assert [r["Name"] for r in csv.DictReader(handle)] == ["A", "B", "C"]
    with open(paths[1], encoding="utf-8") as handle:
        assert json.load(handle)[1]["Rating"] == "4.2"


def test_export_rejects_unknown_format(xlsx):
    with pytest.raises(ValueError):
        export(xlsx, ["xml"])


def test_summarize_ignores_unrated_rows(xlsx):
    stats = summarize(read_rows(xlsx))
    assert stats["count"] == 3 and stats["rated"] == 2
    assert stats["mean_rating"] == 4.5
    assert stats["top_types"][0] == ("Ayam", 2)


def test_summarize_empty():
    assert summarize([]) == {"count": 0, "rated": 0, "mean_rating": None, "top_types": []}
