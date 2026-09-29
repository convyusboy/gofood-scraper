"""Fetch the list of areas and their districts from gofood.co.id/cities."""

import re

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from gofood_scraper.browser import new_driver
from gofood_scraper.config import CITIES_URL, CLASS_CITY_CARD, LOADING_TIME, XPATH_CITIES_LOADED


def get_cities():
    """Return (area_arr, districts_dict) scraped from the gofood cities page."""
    driver = new_driver()
    try:
        driver.get(CITIES_URL)
        element_present = EC.presence_of_element_located((By.XPATH, XPATH_CITIES_LOADED))
        WebDriverWait(driver, LOADING_TIME).until(element_present)
        html_content = driver.page_source
    finally:
        driver.quit()

    return parse_cities_html(html_content)


def parse_cities_html(html_content):
    """Parse the cities page HTML into (area_arr, districts_dict)."""
    soup = BeautifulSoup(html_content, "html.parser")
    cities = soup.find_all("a", class_=CLASS_CITY_CARD)

    area_arr = []
    districts_dict = {}
    for city in cities:
        city_text = city.text
        city_href_elems = city.attrs.get("href").split("/")
        clean_area_text = re.sub("[^a-zA-Z]+", "", city_href_elems[2].lower())
        if city_href_elems[3] == "restaurants":
            area_arr.append(city_text)
            districts_dict.setdefault(clean_area_text, [])
        else:
            districts_dict.setdefault(clean_area_text, []).append(city_text)

    return area_arr, districts_dict
