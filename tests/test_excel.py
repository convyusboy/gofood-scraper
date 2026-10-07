import os

from gofood_scraper.config import HEADERS
from gofood_scraper.excel import new_results_workbook, output_path


def test_output_path_without_district():
    path = output_path("outputs", "jakarta", "", "near_me")
    assert path == os.path.join("outputs", "jakarta-near_me.xlsx")


def test_output_path_with_district():
    path = output_path("outputs", "jakarta", "menteng", "near_me")
    assert path == os.path.join("outputs", "jakarta-menteng-near_me.xlsx")


def test_output_path_with_suffix():
    path = output_path("outputs", "jakarta", "", "near_me", suffix="-backup")
    assert path == os.path.join("outputs", "jakarta-near_me-backup.xlsx")


def test_set_headers_writes_header_row():
    _, sheet_obj = new_results_workbook()
    for i, header in enumerate(HEADERS):
        assert sheet_obj["{}1".format(chr(i + ord("A")))].value == header


def test_new_results_workbook_names_sheet_results():
    _, sheet_obj = new_results_workbook()
    assert sheet_obj.title == "results"
