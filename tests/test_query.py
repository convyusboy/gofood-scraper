import pytest

from gofood_scraper.query import parse_query

AREA_ARR = ["Jakarta", "Bandung", "Bontang"]
DISTRICTS_DICT = {
    "jakarta": ["Jakarta Selatan", "Jakarta Barat", "Jakarta Pusat"],
    "bandung": ["Dago", "Jatinangor"],
    "bontang": [],
}


def test_basic_query_with_district():
    area_str, area_link, district_str, district_link, keyword_arr = parse_query(
        "ayam in Jakarta Selatan", AREA_ARR, DISTRICTS_DICT
    )
    assert (area_str, area_link) == ("Jakarta", "jakarta")
    assert (district_str, district_link) == ("Jakarta Selatan", "jakarta-selatan")
    assert keyword_arr == ["ayam"]


def test_strips_natural_language_filler_words():
    _, _, _, _, keyword_arr = parse_query(
        "find restaurants that have ayam in Jakarta Selatan", AREA_ARR, DISTRICTS_DICT
    )
    assert keyword_arr == ["ayam"]


def test_area_only_query_is_overview_search():
    area_str, area_link, district_str, district_link, _ = parse_query(
        "nasi padang in Jakarta", AREA_ARR, DISTRICTS_DICT
    )
    assert (area_str, area_link) == ("Jakarta", "jakarta")
    assert (district_str, district_link) == ("", "")


def test_area_without_any_districts():
    area_str, _, district_str, _, keyword_arr = parse_query("nasi in Bontang", AREA_ARR, DISTRICTS_DICT)
    assert area_str == "Bontang"
    assert district_str == ""
    assert keyword_arr == ["nasi"]


def test_multiple_keywords_split_on_conjunctions():
    _, _, _, _, keyword_arr = parse_query("nila bakar or nila goreng in Dago", AREA_ARR, DISTRICTS_DICT)
    assert keyword_arr == ["nila bakar", "nila goreng"]


def test_multiword_district_still_matches():
    _, _, district_str, _, _ = parse_query("ayam in Jatinangor", AREA_ARR, DISTRICTS_DICT)
    assert district_str == "Jatinangor"


def test_missing_in_raises_value_error():
    with pytest.raises(ValueError, match="location"):
        parse_query("ayam", AREA_ARR, DISTRICTS_DICT)


def test_missing_keyword_raises_value_error():
    with pytest.raises(ValueError, match="looking for"):
        parse_query("restaurants in Jakarta", AREA_ARR, DISTRICTS_DICT)


def test_unknown_location_raises_value_error():
    with pytest.raises(ValueError, match="Could not find"):
        parse_query("ayam in Atlantis", AREA_ARR, DISTRICTS_DICT)
