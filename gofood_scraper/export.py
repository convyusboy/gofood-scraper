"""Export the scraped .xlsx workbook to CSV/JSON and summarise it."""

import csv
import json
import os
from collections import Counter

import openpyxl

from gofood_scraper.config import HEADERS

FORMATS = ("csv", "json")


def read_rows(xlsx_path):
    """Return the workbook's data rows as dicts keyed by the HEADERS names ("" for empty cells)."""
    sheet = openpyxl.load_workbook(xlsx_path, read_only=True).active
    rows = []
    for values in sheet.iter_rows(min_row=2, values_only=True):
        if not any(values):
            continue
        padded = list(values) + [None] * (len(HEADERS) - len(values))
        rows.append({header: ("" if value is None else value) for header, value in zip(HEADERS, padded)})
    return rows


def export(xlsx_path, formats):
    """Write <xlsx_path minus extension>.<format> for each requested format; return the paths written."""
    rows = read_rows(xlsx_path)
    base = os.path.splitext(xlsx_path)[0]
    written = []
    for fmt in formats:
        if fmt not in FORMATS:
            raise ValueError("unsupported format {!r}; choose from {}".format(fmt, ", ".join(FORMATS)))
        path = "{}.{}".format(base, fmt)
        if fmt == "csv":
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=HEADERS)
                writer.writeheader()
                writer.writerows(rows)
        else:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(rows, handle, ensure_ascii=False, indent=2)
        written.append(path)
    return written


def _parse_rating(value):
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def summarize(rows, top_types=5):
    """Return {count, rated, mean_rating, top_types} for the listing data."""
    ratings = [r for r in (_parse_rating(row["Rating"]) for row in rows) if r is not None]
    types = Counter(row["Type"] for row in rows if row["Type"])
    return {
        "count": len(rows),
        "rated": len(ratings),
        "mean_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
        "top_types": types.most_common(top_types),
    }
