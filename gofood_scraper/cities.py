"""Fetch the list of areas and their districts from gofood.co.id/cities."""

import re

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from gofood_scraper.browser import new_driver
from gofood_scraper.config import BASE_AREA, CITIES_URL, CLASS_CITY_CARD, LOADING_TIME, XPATH_CITIES_LOADED


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

    soup = BeautifulSoup(html_content, "html.parser")
    cities = soup.find_all("a", class_=CLASS_CITY_CARD)

    area_arr = []
    districts_dict = {}
    area_city_arr = []
    current_area = BASE_AREA
    for city in cities:
        city_text = city.text
        city_href_elems = city.attrs.get("href").split("/")
        clean_area_text = re.sub("[^a-zA-Z]+", "", city_href_elems[2].lower())
        if city_href_elems[3] == "restaurants":
            area_arr.append(city_text)
            districts_dict.setdefault(clean_area_text, [])
        else:
            if current_area != clean_area_text:
                districts_dict[current_area] = area_city_arr
                current_area = clean_area_text
                if current_area in districts_dict:
                    area_city_arr = districts_dict[current_area]
                    area_city_arr.append(city_text)
                else:
                    area_city_arr = [city_text]
            else:
                area_city_arr.append(city_text)

    return area_arr, districts_dict
