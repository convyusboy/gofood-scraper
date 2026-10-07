"""Scrape restaurant listing pages into per-category Excel workbooks."""

import logging
import time

from bs4 import BeautifulSoup
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.by import By

from gofood_scraper.browser import new_driver
from gofood_scraper.config import (
    CLASS_RESTAURANT_CARD,
    CLASS_RESTAURANT_IMAGE,
    CLASS_RESTAURANT_NAME,
    CLASS_RESTAURANT_RATING,
    CLASS_RESTAURANT_TYPE,
    GET_PAGE_HEIGHT,
    MAX_RETRY_COUNT,
    RESTAURANT_URL,
    RESTAURANTS_URL_WITH_DISTRICT,
    RESTAURANTS_URL_WITHOUT_DISTRICT,
    SCROLL_PAUSE_TIME,
    SCROLL_TO_BOTTOM,
    SCROLL_UP,
    XPATH_LOAD_MORE_LINK,
)
from gofood_scraper.excel import column, new_results_workbook, output_path

log = logging.getLogger(__name__)


def _load_full_listing(driver, url):
    """Load url and keep scrolling/clicking "load more" until the page stops growing."""
    driver.get(url)
    # need to request twice to be able to scroll down
    driver.get(url)

    driver.execute_script(SCROLL_TO_BOTTOM)
    init_height = driver.execute_script(GET_PAGE_HEIGHT)
    stuck_once = False
    stuck_twice = False
    new_height = -1
    last_height = -2
    retry_count = 0

    while not stuck_twice and (new_height != last_height or stuck_once):
        last_height = driver.execute_script(GET_PAGE_HEIGHT)
        driver.execute_script(SCROLL_UP, "")
        time.sleep(SCROLL_PAUSE_TIME)
        if stuck_once:
            try:
                driver.find_element(By.XPATH, XPATH_LOAD_MORE_LINK).click()
            except (NoSuchElementException, ElementClickInterceptedException):
                retry_count += 1
            finally:
                driver.execute_script(SCROLL_TO_BOTTOM)
                new_height = driver.execute_script(GET_PAGE_HEIGHT)
                if new_height == last_height and retry_count == MAX_RETRY_COUNT:
                    stuck_twice = True
        else:
            driver.execute_script(SCROLL_TO_BOTTOM)
            new_height = driver.execute_script(GET_PAGE_HEIGHT)
            # when the restaurant list's page is unscrollable from the beginning
            if init_height == new_height:
                break
            if last_height == new_height:
                stuck_once = True


def get_restaurants(output_dir, area, district, category_links):
    """Scrape the restaurant listing for each category into <output_dir>/<area>[-<district>]-<category>.xlsx."""
    for category_link in category_links:
        log.debug("area=%s district=%s category=%s", area, district, category_link)
        url = (
            RESTAURANTS_URL_WITHOUT_DISTRICT.format(area, category_link)
            if district == ""
            else RESTAURANTS_URL_WITH_DISTRICT.format(area, district, category_link)
        )

        driver = new_driver()
        try:
            _load_full_listing(driver, url)
            html_content = driver.page_source
        finally:
            driver.quit()

        path = output_path(output_dir, area, district, category_link)
        wb_obj, sheet_obj = new_results_workbook()

        rows = extract_restaurant_rows(html_content)
        log.info("total restaurants: %d", len(rows))

        for i, restaurant_row in enumerate(rows, start=2):
            sheet_obj[column("Link") + str(i)] = restaurant_row["link"]
            sheet_obj[column("Image") + str(i)] = restaurant_row["image"]
            sheet_obj[column("Rating") + str(i)] = restaurant_row["rating"]
            sheet_obj[column("Name") + str(i)] = restaurant_row["name"]
            sheet_obj[column("Type") + str(i)] = restaurant_row["type"]

        wb_obj.save(path)


def extract_restaurant_rows(html_content):
    """Parse a restaurant listing page's HTML into a list of {link, image, rating, name, type} dicts."""
    soup = BeautifulSoup(html_content, "html.parser")
    restaurants = soup.find_all("a", class_=CLASS_RESTAURANT_CARD)

    rows = []
    for restaurant in restaurants:
        name_soup = restaurant.find("p", class_=CLASS_RESTAURANT_NAME)
        if name_soup is None or not restaurant.get("href"):
            log.warning("skipping a restaurant card with no name or link; selectors may be out of date")
            continue
        rating_soup = restaurant.find("div", class_=CLASS_RESTAURANT_RATING)
        type_soup = restaurant.find("p", class_=CLASS_RESTAURANT_TYPE)
        image_soup = restaurant.find("img", class_=CLASS_RESTAURANT_IMAGE)
        rows.append({
            "link": RESTAURANT_URL.format(restaurant["href"]),
            "image": image_soup.get("src", "") if image_soup is not None else "",
            "rating": rating_soup.text.strip() if rating_soup is not None else "-",
            "name": name_soup.text.strip(),
            "type": type_soup.text.strip() if type_soup is not None else "",
        })
    return rows
