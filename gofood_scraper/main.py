"""Entry point: asks for a free-text search query, then scrapes matching restaurants."""

import os

from gofood_scraper.cities import get_cities
from gofood_scraper.cli import input_search_query
from gofood_scraper.config import DEFAULT_CATEGORY_LINK, OUTPUT_DIR
from gofood_scraper.menus import get_menus
from gofood_scraper.query import parse_query
from gofood_scraper.restaurants import get_restaurants


def run():
    print("================= Welcome to gofood scraper ==================")
    area_arr, districts_dict = get_cities()

    while True:
        query = input_search_query()
        try:
            area_str, area_link, district_str, district_link, keyword_arr = parse_query(
                query, area_arr, districts_dict
            )
            break
        except ValueError as exc:
            print(exc)

    location_str = district_str or area_str
    print('\nSearching for "{}" in {}'.format(", ".join(keyword_arr), location_str))

    print("\nStart scraping")
    print("Please wait until the process is done, don't close any google chrome window opened")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    category_links = [DEFAULT_CATEGORY_LINK]
    get_restaurants(OUTPUT_DIR, area_link, district_link, category_links)
    get_menus(OUTPUT_DIR, area_link, district_link, category_links, keyword_arr)

    print("================= The scraping process is done ===============")
    print("=========== Check the xlsx file(s) in the {} folder ===========".format(OUTPUT_DIR))
    print("=========== Thank you for using the gofood scraper ===========")


if __name__ == "__main__":
    run()
