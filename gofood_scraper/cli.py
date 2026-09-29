"""Interactive prompts for choosing area, district, category and keywords."""

import re

from gofood_scraper.config import CATEGORY_ARR, CATEGORY_LINK_ARR


def invalid_number_input(input_str, bottom, top):
    """Return True if input_str is not an integer within [bottom, top]."""
    try:
        input_int = int(input_str)
    except ValueError:
        return True
    return input_int < bottom or input_int > top


def choose_city_and_district(area_arr, districts_dict):
    """Prompt the user to choose an area and, optionally, a district.

    Returns (area_str, area_link, district_str, district_link). district_str
    and district_link are empty strings when the user picks the overview.
    """
    for i, area in enumerate(area_arr, start=1):
        print("{}. {}".format(i, area))

    areas_length = len(area_arr)
    area_number = input("Please choose the area number from the list above (1-{}): ".format(areas_length))
    while invalid_number_input(area_number, 1, areas_length):
        area_number = input("Wrong input! Please choose the area number from the list above (1-{}): ".format(areas_length))

    area_str = area_arr[int(area_number) - 1]
    area_link = area_str.lower().replace(" ", "-")
    print("\nYou chose {}".format(area_str))

    area_idx = re.sub("[^a-zA-Z]+", "", area_str.lower())
    district_arr = districts_dict[area_idx]
    if not district_arr:
        return area_str, area_link, "", ""

    print("Here are the list of the cities or districts that you can explore, or you can choose the overview:")
    print("0. Overview")
    for i, district in enumerate(district_arr, start=1):
        print("{}. {}".format(i, district))

    districts_length = len(district_arr)
    district_number = input("Please choose the district number from the list above (0-{}): ".format(districts_length))
    while invalid_number_input(district_number, 0, districts_length):
        district_number = input("Wrong input! Please choose the district number from the list above (0-{}): ".format(districts_length))

    if district_number == "0":
        print("\nYou chose Overview")
        return area_str, area_link, "", ""

    district_str = district_arr[int(district_number) - 1]
    district_link = district_str.lower().replace(" ", "-")
    print("\nYou chose {}".format(district_str))
    return area_str, area_link, district_str, district_link


def choose_category():
    """Prompt the user to choose a category. Returns (category_str, category_links)."""
    for i, category in enumerate(CATEGORY_ARR, start=1):
        print("{}. {}".format(i, category))

    categories_length = len(CATEGORY_ARR)
    category_number = input("Please choose the category number from the list above (1-{}): ".format(categories_length))
    while invalid_number_input(category_number, 1, categories_length):
        category_number = input("Wrong input! Please choose the category number from the list above (0-{}): ".format(categories_length))

    category_int = int(category_number) - 1
    category_str = CATEGORY_ARR[category_int]
    print("\nYou chose {}".format(category_str))
    return category_str, CATEGORY_LINK_ARR[category_int]


def input_menu_keywords():
    """Prompt the user for menu keywords. Returns a list of lowercase keywords."""
    print('Please input the keywords in menu that you want to look for in format "keywords1; key words2; last key words 3":')
    print("Example: Nila bakar; nila goreng")
    keywords = input()
    return keywords.lower().split(";")
