"""Parse a free-text search query like "ayam in Jakarta Selatan" into scraper inputs."""

import re

# words to drop from the "what" half of the query so only the food keyword(s) remain
FILLER_WORDS = {
    "find", "restaurant", "restaurants", "that", "which", "who", "serve",
    "serves", "serving", "have", "has", "having", "with", "for", "search",
    "searching", "look", "looking", "please", "some", "any", "a", "an", "the",
    "me",
}


def parse_query(query_text, area_arr, districts_dict):
    """Parse "<keyword(s)> in <area or district>" into scraper inputs.

    Returns (area_str, area_link, district_str, district_link, keyword_arr).
    district_str/district_link are empty strings for an area-wide (overview) search.
    Raises ValueError with a user-facing message if the query can't be understood.
    """
    what_text, in_text = _split_on_in(query_text)
    if in_text is None:
        raise ValueError(
            'Please include a location with "in", e.g. "ayam in Jakarta Selatan".'
        )

    keyword_arr = _extract_keywords(what_text)
    if not keyword_arr:
        raise ValueError(
            'Please include what you\'re looking for, e.g. "ayam in Jakarta Selatan".'
        )

    location = _match_location(in_text, area_arr, districts_dict)
    if location is None:
        raise ValueError(
            'Could not find "{}" in the list of areas/districts. '
            "Try just the area name, e.g. \"Jakarta\" or \"Jakarta Selatan\".".format(in_text.strip())
        )
    area_str, district_str = location

    area_link = area_str.lower().replace(" ", "-")
    district_link = district_str.lower().replace(" ", "-") if district_str else ""
    return area_str, area_link, district_str, district_link, keyword_arr


def _split_on_in(query_text):
    """Split "<what> in <where>" on the first standalone "in". Returns (what, where|None)."""
    match = re.search(r"\bin\b", query_text, flags=re.IGNORECASE)
    if not match:
        return query_text, None
    return query_text[: match.start()], query_text[match.end():]


def _extract_keywords(what_text):
    words = re.findall(r"[^\s,]+", what_text)
    kept = [w for w in words if w.strip(".,").lower() not in FILLER_WORDS]
    cleaned = " ".join(kept).strip()
    if not cleaned:
        return []
    parts = re.split(r",|\band\b|\bor\b|;", cleaned, flags=re.IGNORECASE)
    return [p.strip().lower() for p in parts if p.strip()]


def _clean(text):
    return re.sub(r"[^a-zA-Z0-9 ]+", "", text).strip().lower()


def _area_link_key(area_str):
    return re.sub("[^a-zA-Z]+", "", area_str.lower())


def _match_location(location_text, area_arr, districts_dict):
    """Match free text against known districts first, then areas. Returns (area_str, district_str)."""
    location_clean = _clean(location_text)
    if not location_clean:
        return None
    location_key = re.sub("[^a-zA-Z]+", "", location_clean)

    def area_str_for(area_idx):
        return next((a for a in area_arr if _area_link_key(a) == area_idx), None)

    # exact matches (district, then area) win over partial ones, regardless of iteration order
    for area_idx, district_list in districts_dict.items():
        for district_str in district_list:
            if _clean(district_str) == location_clean:
                area_str = area_str_for(area_idx)
                if area_str:
                    return area_str, district_str

    for area_str in area_arr:
        if _area_link_key(area_str) == location_key:
            return area_str, ""

    # fall back to substring matches
    for area_idx, district_list in districts_dict.items():
        for district_str in district_list:
            district_clean = _clean(district_str)
            if location_clean in district_clean or district_clean in location_clean:
                area_str = area_str_for(area_idx)
                if area_str:
                    return area_str, district_str

    return None
