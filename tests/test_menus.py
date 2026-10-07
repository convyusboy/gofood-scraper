from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException

import gofood_scraper.menus as menus_module
from gofood_scraper.config import (
    CLASS_BIG_MENU_CARD,
    CLASS_MENU_CARD,
    CLASS_OPEN_HOURS_ROW,
    CLASS_RESTAURANT_PRICE,
    CLASS_RESTAURANT_PRICE_LEVEL,
    CLASS_SMALL_MENU_CARD,
    MAX_RETRY_COUNT,
)
from gofood_scraper.menus import (
    _extract_menus,
    _extract_open_hours,
    _extract_price,
    _extract_total_rating,
    get_menus,
)


def test_extract_total_rating_found():
    html = '{"ratingCount":128,"other":1}'
    assert _extract_total_rating(html) == "128"


def test_extract_total_rating_missing():
    assert _extract_total_rating("{}") == "-"


def _menu_card(big_menu, small_menu=None):
    small_html = '<p class="{}">{}</p>'.format(CLASS_SMALL_MENU_CARD, small_menu) if small_menu else ""
    return '<div class="{}"><h3 class="{}">{}</h3>{}</div>'.format(
        CLASS_MENU_CARD, CLASS_BIG_MENU_CARD, big_menu, small_html
    )


def test_extract_menus_matches_big_menu_name():
    soup = BeautifulSoup(_menu_card("Nasi Goreng Spesial"), "html.parser")
    total_matched, total_menu, matched_text = _extract_menus(soup, ["nasi goreng"])
    assert (total_matched, total_menu) == (1, 1)
    assert matched_text == "- Nasi Goreng Spesial"


def test_extract_menus_matches_small_menu_description_only():
    soup = BeautifulSoup(_menu_card("Paket Hemat", small_menu="Nasi + Ayam Goreng"), "html.parser")
    total_matched, total_menu, matched_text = _extract_menus(soup, ["ayam goreng"])
    assert (total_matched, total_menu) == (1, 1)
    assert matched_text == "- Paket Hemat"


def test_extract_menus_no_match():
    soup = BeautifulSoup(_menu_card("Es Teh Manis"), "html.parser")
    total_matched, total_menu, matched_text = _extract_menus(soup, ["nasi goreng"])
    assert (total_matched, total_menu, matched_text) == (0, 1, "")


def test_extract_menus_multiple_matches_joined_by_newline():
    html = _menu_card("Nila Bakar") + _menu_card("Nila Goreng") + _menu_card("Es Teh")
    soup = BeautifulSoup(html, "html.parser")
    total_matched, total_menu, matched_text = _extract_menus(soup, ["nila bakar", "nila goreng"])
    assert (total_matched, total_menu) == (2, 3)
    assert matched_text == "- Nila Bakar\n- Nila Goreng"


def test_extract_open_hours():
    # each day's label has a different fixed prefix length ([5, 6, 4, 5, 5, 5, 6]) to strip
    prefix_lengths = [5, 6, 4, 5, 5, 5, 6]
    rows = "".join(
        '<div class="{}">{}09:00 - 22:00</div>'.format(CLASS_OPEN_HOURS_ROW, "X" * length)
        for length in prefix_lengths
    )
    soup = BeautifulSoup(rows, "html.parser")
    hours = _extract_open_hours(soup)
    assert hours == {col: "09:00 - 22:00" for col in ["J", "K", "L", "M", "N", "O", "P"]}


def test_extract_price_present():
    html = (
        '<div data-testid="priceLevel">'
        '<div class="{level_class}"></div><div class="{level_class}"></div>'
        "</div>"
        '<div class="{price_class}">A</div>'
        '<div class="{price_class}">B</div>'
        '<div class="{price_class}">Rp10.000-Rp30.000</div>'
    ).format(level_class=CLASS_RESTAURANT_PRICE_LEVEL, price_class=CLASS_RESTAURANT_PRICE)
    soup = BeautifulSoup(html, "html.parser")
    assert _extract_price(soup) == "2/4 (Rp10.000-Rp30.000)"


def test_extract_price_missing():
    soup = BeautifulSoup("<html><body></body></html>", "html.parser")
    assert _extract_price(soup) is None


def test_get_menus_gives_up_after_max_retries_instead_of_hanging(monkeypatch, caplog):
    call_count = 0

    def always_fails(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise NoSuchElementException("simulated bot/CAPTCHA challenge")

    monkeypatch.setattr(menus_module, "_get_menus_for_category", always_fails)

    completed = get_menus("outputs", "jakarta", "", ["near_me"], ["ayam"])

    assert completed is False
    assert call_count == MAX_RETRY_COUNT
    assert "giving up on near_me" in caplog.text


def test_get_menus_stops_retrying_once_a_category_succeeds(monkeypatch):
    call_count = 0

    def succeeds_on_second_try(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise NoSuchElementException("transient")
        return True

    monkeypatch.setattr(menus_module, "_get_menus_for_category", succeeds_on_second_try)

    get_menus("outputs", "jakarta", "", ["near_me"], ["ayam"])

    assert call_count == 2


# --- Selenium flow with a fake driver -------------------------------------------------------

import openpyxl  # noqa: E402
import pytest  # noqa: E402

from gofood_scraper.excel import column, new_results_workbook, output_path  # noqa: E402
from gofood_scraper.menus import BotChallengeError, _scrape_restaurant_row  # noqa: E402


class _Clickable:
    def click(self):
        pass


class FakeDriver:
    def __init__(self, page_source):
        self.page_source = page_source
        self.quit_called = False

    def get(self, url):
        pass

    def find_element(self, *args):
        return _Clickable()

    def execute_script(self, script):
        return 1000

    def quit(self):
        self.quit_called = True


@pytest.fixture
def fake_browser(monkeypatch):
    drivers = []

    def install(page_source):
        def factory():
            drivers.append(FakeDriver(page_source))
            return drivers[-1]

        monkeypatch.setattr(menus_module, "new_driver", factory)
        monkeypatch.setattr(menus_module.time, "sleep", lambda _s: None)
        return drivers

    return install


def _restaurant_page():
    hours = "".join(
        '<div class="{}">{}09:00 - 22:00</div>'.format(CLASS_OPEN_HOURS_ROW, "X" * n)
        for n in [5, 6, 4, 5, 5, 5, 6]
    )
    price = (
        '<div data-testid="priceLevel"><div class="{lvl}"></div></div>'
        '<div class="{p}">A</div><div class="{p}">B</div><div class="{p}">Rp10.000-Rp30.000</div>'
    ).format(lvl=CLASS_RESTAURANT_PRICE_LEVEL, p=CLASS_RESTAURANT_PRICE)
    return '{"ratingCount":42,"x":1}' + _menu_card("Nasi Goreng") + _menu_card("Es Teh") + hours + price


def test_scrape_restaurant_row_fills_sheet_and_quits_driver(fake_browser):
    drivers = fake_browser(_restaurant_page())
    _, sheet = new_results_workbook()

    _scrape_restaurant_row(sheet, 2, "https://example.com/r", ["nasi goreng"])

    assert drivers[0].quit_called
    assert sheet[column("Total Rating") + "2"].value == "42"
    assert sheet[column("Total Menu with Inputted Keywords") + "2"].value == "1/2"
    assert sheet[column("Menu with Inputted Keywords") + "2"].value == "- Nasi Goreng"
    assert sheet[column("Monday") + "2"].value == "09:00 - 22:00"
    assert sheet[column("Gofood Price Level") + "2"].value == "1/4 (Rp10.000-Rp30.000)"


def test_scrape_restaurant_row_raises_on_captcha_page(fake_browser):
    drivers = fake_browser("<html><body><div id='captcha'>Please verify</div></body></html>")
    _, sheet = new_results_workbook()

    with pytest.raises(BotChallengeError):
        _scrape_restaurant_row(sheet, 2, "https://example.com/r", ["ayam"])
    assert drivers[0].quit_called


def test_captcha_script_on_a_real_page_is_not_a_challenge(fake_browser):
    fake_browser("<script src='recaptcha.js'></script>" + _restaurant_page())
    _, sheet = new_results_workbook()

    _scrape_restaurant_row(sheet, 2, "https://example.com/r", ["nasi goreng"])

    assert sheet[column("Total Rating") + "2"].value == "42"


def test_get_menus_does_not_retry_after_bot_challenge(monkeypatch, caplog):
    calls = []

    def blocked(*args, **kwargs):
        calls.append(1)
        raise BotChallengeError("blocked.")

    monkeypatch.setattr(menus_module, "_get_menus_for_category", blocked)

    assert get_menus("outputs", "jakarta", "", ["near_me"], ["ayam"]) is False
    assert len(calls) == 1
    assert "Stopping" in caplog.text


def test_get_menus_skips_rows_already_scraped_and_saves(monkeypatch, tmp_path, fake_browser):
    fake_browser(_restaurant_page())
    wb, sheet = new_results_workbook()
    for row, name in [(2, "Done"), (3, "Todo")]:
        sheet[column("Link") + str(row)] = "https://example.com/" + name
        sheet[column("Name") + str(row)] = name
    sheet[column("Monday") + "2"] = "already scraped"
    wb.save(output_path(str(tmp_path), "jakarta", "", "near_me"))

    assert get_menus(str(tmp_path), "jakarta", "", ["near_me"], ["nasi goreng"]) is True

    saved = openpyxl.load_workbook(output_path(str(tmp_path), "jakarta", "", "near_me")).active
    assert saved[column("Monday") + "2"].value == "already scraped"
    assert saved[column("Monday") + "3"].value == "09:00 - 22:00"


def test_extract_menus_skips_cards_without_a_name():
    html = '<div class="{}"></div>'.format(CLASS_MENU_CARD) + _menu_card("Nasi Goreng")
    soup = BeautifulSoup(html, "html.parser")
    assert _extract_menus(soup, ["nasi"])[:2] == (1, 1)


def test_extract_price_missing_range_does_not_crash():
    html = '<div data-testid="priceLevel"></div><div class="{}">A</div>'.format(CLASS_RESTAURANT_PRICE)
    assert _extract_price(BeautifulSoup(html, "html.parser")) is None
