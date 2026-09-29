"""Entry point: walks the user through choosing an area/district/category/keywords, then scrapes."""

import os

from gofood_scraper.cities import get_cities
from gofood_scraper.cli import choose_category, choose_city_and_district, input_menu_keywords
from gofood_scraper.config import OUTPUT_DIR
from gofood_scraper.menus import get_menus
from gofood_scraper.restaurants import get_restaurants


def run():
    print("================= Welcome to gofood scraper ==================")
    print("\nHere are the list of the areas that you can explore in gofood:")
    area_arr, districts_dict = get_cities()
    area_str, area_link, district_str, district_link = choose_city_and_district(area_arr, districts_dict)
    category_str, category_links = choose_category()
    keyword_arr = input_menu_keywords()

    print("\nStart scraping")
    print("Please wait until the process is done, don't close any google chrome window opened")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    get_restaurants(OUTPUT_DIR, area_link, district_link, category_links)
    get_menus(OUTPUT_DIR, area_link, district_link, category_links, keyword_arr)

    print("================= The scraping process is done ===============")
    print("=========== Check the xlsx file(s) in the {} folder ===========".format(OUTPUT_DIR))
    print("=========== Thank you for using the gofood scraper ===========")


if __name__ == "__main__":
    run()
