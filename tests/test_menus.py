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


def test_get_menus_gives_up_after_max_retries_instead_of_hanging(monkeypatch, capsys):
    call_count = 0

    def always_fails(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise NoSuchElementException("simulated bot/CAPTCHA challenge")

    monkeypatch.setattr(menus_module, "_get_menus_for_category", always_fails)

    get_menus("outputs", "jakarta", "", ["near_me"], ["ayam"])

    assert call_count == MAX_RETRY_COUNT
    assert "giving up on near_me" in capsys.readouterr().out


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
