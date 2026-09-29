from gofood_scraper.cities import parse_cities_html

CARD_CLASS = "transition-all duration-500 visible relative top-0 block opacity-100 btn-area"


def _card(text, href):
    return '<a class="{}" href="{}">{}</a>'.format(CARD_CLASS, href, text)


def test_area_without_districts():
    html = "<html><body>{}</body></html>".format(_card("Bontang", "/en/bontang/restaurants"))
    area_arr, districts_dict = parse_cities_html(html)
    assert area_arr == ["Bontang"]
    assert districts_dict == {"bontang": []}


def test_area_with_districts():
    html = "<html><body>{}{}{}</body></html>".format(
        _card("Jakarta", "/en/jakarta/restaurants"),
        _card("Menteng", "/en/jakarta/menteng"),
        _card("Kemang", "/en/jakarta/kemang"),
    )
    area_arr, districts_dict = parse_cities_html(html)
    assert area_arr == ["Jakarta"]
    assert districts_dict == {"jakarta": ["Menteng", "Kemang"]}


def test_multiple_areas_each_with_own_districts():
    html = "<html><body>{}{}{}{}</body></html>".format(
        _card("Jakarta", "/en/jakarta/restaurants"),
        _card("Menteng", "/en/jakarta/menteng"),
        _card("Bandung", "/en/bandung/restaurants"),
        _card("Dago", "/en/bandung/dago"),
    )
    area_arr, districts_dict = parse_cities_html(html)
    assert area_arr == ["Jakarta", "Bandung"]
    assert districts_dict == {"jakarta": ["Menteng"], "bandung": ["Dago"]}
