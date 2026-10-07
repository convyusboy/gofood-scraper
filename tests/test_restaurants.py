from gofood_scraper.config import (
    CLASS_RESTAURANT_CARD,
    CLASS_RESTAURANT_IMAGE,
    CLASS_RESTAURANT_NAME,
    CLASS_RESTAURANT_RATING,
    CLASS_RESTAURANT_TYPE,
)
from gofood_scraper.restaurants import extract_restaurant_rows


def _restaurant_card(name, restaurant_type=None, rating=None):
    type_html = '<p class="{}">{}</p>'.format(CLASS_RESTAURANT_TYPE, restaurant_type) if restaurant_type else ""
    rating_html = '<div class="{}">{}</div>'.format(CLASS_RESTAURANT_RATING, rating) if rating else ""
    return (
        '<a class="{card_class}" href="/en/some-restaurant">'
        '  <img class="{image_class}" src="https://example.com/image.jpg">'
        '  {rating_html}'
        '  <p class="{name_class}">{name}</p>'
        '  {type_html}'
        "</a>"
    ).format(
        card_class=CLASS_RESTAURANT_CARD,
        image_class=CLASS_RESTAURANT_IMAGE,
        name_class=CLASS_RESTAURANT_NAME,
        name=name,
        rating_html=rating_html,
        type_html=type_html,
    )


def test_extracts_full_restaurant_row():
    html = "<html><body>{}</body></html>".format(
        _restaurant_card("Warung Nasi Padang", restaurant_type="Padang, Indonesian", rating="4.8")
    )
    rows = extract_restaurant_rows(html)
    assert rows == [{
        "link": "https://gofood.co.id/en/some-restaurant",
        "image": "https://example.com/image.jpg",
        "rating": "4.8",
        "name": "Warung Nasi Padang",
        "type": "Padang, Indonesian",
    }]


def test_missing_rating_and_type_default_gracefully():
    html = "<html><body>{}</body></html>".format(_restaurant_card("Warung Nasi Padang"))
    rows = extract_restaurant_rows(html)
    assert rows[0]["rating"] == "-"
    assert rows[0]["type"] == ""


def test_multiple_restaurants():
    html = "<html><body>{}{}</body></html>".format(
        _restaurant_card("Restaurant A", rating="4.5"),
        _restaurant_card("Restaurant B", rating="4.0"),
    )
    rows = extract_restaurant_rows(html)
    assert [row["name"] for row in rows] == ["Restaurant A", "Restaurant B"]


def test_no_restaurants_returns_empty_list():
    assert extract_restaurant_rows("<html><body></body></html>") == []


def test_extract_restaurant_rows_skips_malformed_cards():
    html = _restaurant_card("Good Place") + '<a class="{}" href="/en/broken"></a>'.format(CLASS_RESTAURANT_CARD)
    rows = extract_restaurant_rows(html)
    assert [row["name"] for row in rows] == ["Good Place"]
