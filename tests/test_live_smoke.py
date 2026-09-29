"""Opt-in tests that hit the real gofood.co.id site to catch markup/selector drift.

Run explicitly with: pytest -m live

Note: there's no live test for gofood_scraper.menus here. Visiting individual
restaurant pages is currently met with a Tencent WAF CAPTCHA challenge from
gofood.co.id, so a test against it would be flaky/non-deterministic rather
than a real signal. See the README's "Known limitation" section.
"""

import pytest

from gofood_scraper.cities import get_cities
from gofood_scraper.restaurants import get_restaurants


@pytest.mark.live
def test_get_cities_returns_known_area():
    area_arr, districts_dict = get_cities()
    assert len(area_arr) > 0
    assert "jakarta" in districts_dict


@pytest.mark.live
def test_get_restaurants_scrapes_a_listing_page(tmp_path):
    get_restaurants(str(tmp_path), "jakarta", "", ["near_me"])
    output_file = tmp_path / "jakarta-near_me.xlsx"
    assert output_file.exists()

    import openpyxl

    wb = openpyxl.load_workbook(output_file)
    sheet = wb.active
    assert sheet["A1"].value == "Link"
    assert sheet["A2"].value is not None
