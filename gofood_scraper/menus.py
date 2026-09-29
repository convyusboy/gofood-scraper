"""Visit each scraped restaurant page and fill in menu, hours, rating and price data."""

import time

import openpyxl
from bs4 import BeautifulSoup
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By

from gofood_scraper.browser import new_driver
from gofood_scraper.config import (
    CLASS_BIG_MENU_CARD,
    CLASS_MENU_CARD,
    CLASS_OPEN_HOURS_ROW,
    CLASS_RESTAURANT_ADDRESS,
    CLASS_RESTAURANT_PRICE,
    CLASS_RESTAURANT_PRICE_LEVEL,
    CLASS_SMALL_MENU_CARD,
    GET_PAGE_HEIGHT,
    MAX_RETRY_COUNT,
    SCROLL_PAUSE_TIME,
    SCROLL_TO_BOTTOM,
    SCROLL_TO_TOP,
    XPATH_BACK_BUTTON,
    XPATH_MENU_LINK,
    XPATH_REVIEW_LINK,
)
from gofood_scraper.excel import output_path

# column letters for each day, in the order the open-hours rows appear on the page
DAY_COLUMNS = ["J", "K", "L", "M", "N", "O", "P"]


def get_menus(output_dir, area, district, category_links, keyword_arr):
    """Fill in menu/hours/rating/price data for every category, retrying on transient errors."""
    for category_link in category_links:
        for attempt in range(1, MAX_RETRY_COUNT + 1):
            try:
                if _get_menus_for_category(output_dir, area, district, category_link, keyword_arr):
                    break
            except (NoSuchElementException, StaleElementReferenceException):
                if attempt == MAX_RETRY_COUNT:
                    print(
                        "giving up on {} after {} attempts - gofood.co.id may be showing a "
                        "bot/CAPTCHA challenge to automated browsers right now. Progress made "
                        "so far is saved in the .xlsx file; re-run later to fill in the rest."
                        .format(category_link, MAX_RETRY_COUNT)
                    )
                else:
                    print("there's a bot, retrying ({}/{})".format(attempt, MAX_RETRY_COUNT))


def _get_menus_for_category(output_dir, area, district, category_link, keyword_arr):
    path = output_path(output_dir, area, district, category_link)
    wb_obj = openpyxl.load_workbook(path)
    sheet_obj = wb_obj.active

    for row, cell in enumerate(sheet_obj["A"], start=1):
        if row < 2:
            continue
        wb_obj.save(path)
        if sheet_obj["J{}".format(row)].value is not None:
            continue
        print("processing row ", row, " - ", sheet_obj["E{}".format(row)].value)
        _scrape_restaurant_row(sheet_obj, row, cell.value, keyword_arr)
        wb_obj.save(path)

    wb_obj.save(path)
    return True


def _scrape_restaurant_row(sheet_obj, row, url, keyword_arr):
    driver = new_driver()
    try:
        driver.get(url)
        time.sleep(SCROLL_PAUSE_TIME)

        try:
            driver.find_element(By.XPATH, XPATH_REVIEW_LINK).click()
        except (NoSuchElementException, ElementClickInterceptedException):
            pass

        rating_html_content = str(driver.page_source)
        time.sleep(SCROLL_PAUSE_TIME)
        total_rating = _extract_total_rating(rating_html_content)

        time.sleep(SCROLL_PAUSE_TIME)
        try:
            driver.find_element(By.XPATH, XPATH_BACK_BUTTON).click()
        except (NoSuchElementException, ElementClickInterceptedException):
            pass
        time.sleep(SCROLL_PAUSE_TIME)

        _scroll_to_bottom(driver)

        driver.execute_script(SCROLL_TO_TOP)
        time.sleep(SCROLL_PAUSE_TIME)
        try:
            driver.find_element(By.XPATH, XPATH_MENU_LINK).click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            pass

        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    total_menu_with_inputted_keywords, total_menu, menu_with_inputted_keywords = _extract_menus(soup, keyword_arr)

    sheet_obj["D{}".format(row)] = total_rating
    sheet_obj["G{}".format(row)] = "{}/{}".format(total_menu_with_inputted_keywords, total_menu)
    sheet_obj["H{}".format(row)] = menu_with_inputted_keywords

    address = soup.find("div", class_=CLASS_RESTAURANT_ADDRESS)
    if address is not None:
        sheet_obj["I{}".format(row)] = address.text.strip()

    _fill_open_hours(sheet_obj, row, soup)
    _fill_price(sheet_obj, row, soup)


def _extract_total_rating(rating_html_content):
    find_rating_count_idx = rating_html_content.find("ratingCount")
    if find_rating_count_idx == -1:
        return "-"
    idx_start = find_rating_count_idx + 13
    idx_end = rating_html_content[idx_start:].find(",") + idx_start
    return rating_html_content[idx_start:idx_end]


def _scroll_to_bottom(driver):
    last_height = driver.execute_script(GET_PAGE_HEIGHT)
    while True:
        driver.execute_script(SCROLL_TO_BOTTOM)
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script(GET_PAGE_HEIGHT)
        if new_height == last_height:
            break
        last_height = new_height


def _extract_menus(soup, keyword_arr):
    menus = soup.find_all("div", class_=CLASS_MENU_CARD)
    total_menu = 0
    total_menu_with_inputted_keywords = 0
    menu_with_inputted_keywords = ""
    for menu in menus:
        total_menu += 1
        big_menu = menu.find("h3", class_=CLASS_BIG_MENU_CARD).text.strip()
        keywords_found = any(x in big_menu.lower() for x in keyword_arr)
        if not keywords_found:
            small_menu_soup = menu.find("p", class_=CLASS_SMALL_MENU_CARD)
            if small_menu_soup is not None and any(x in small_menu_soup.text.strip().lower() for x in keyword_arr):
                keywords_found = True
        if keywords_found:
            if total_menu_with_inputted_keywords > 0:
                menu_with_inputted_keywords = "{}\n".format(menu_with_inputted_keywords)
            menu_with_inputted_keywords = "{}- {}".format(menu_with_inputted_keywords, big_menu)
            total_menu_with_inputted_keywords += 1
    return total_menu_with_inputted_keywords, total_menu, menu_with_inputted_keywords


def _extract_open_hours(soup):
    """Return {column_letter: opening_hours_text} for each day found on the page."""
    open_hours = soup.find_all("div", class_=CLASS_OPEN_HOURS_ROW)
    # each day's label has a different fixed prefix length to strip off ("Monday", "Tuesday", ...)
    prefix_lengths = [5, 6, 4, 5, 5, 5, 6]
    return {
        column: open_hour.text.strip()[prefix_length:]
        for column, prefix_length, open_hour in zip(DAY_COLUMNS, prefix_lengths, open_hours)
    }


def _extract_price(soup):
    """Return the "<level>/4 (<range>)" price string, or None if not present on the page."""
    price_range = soup.find_all("div", class_=CLASS_RESTAURANT_PRICE)
    if not price_range:
        return None
    price_level = len(soup.find(attrs={"data-testid": "priceLevel"}).find_all("div", class_=CLASS_RESTAURANT_PRICE_LEVEL))
    return "{}/4 ({})".format(price_level, price_range[2].text.strip())


def _fill_open_hours(sheet_obj, row, soup):
    for column, value in _extract_open_hours(soup).items():
        sheet_obj["{}{}".format(column, row)] = value


def _fill_price(sheet_obj, row, soup):
    price = _extract_price(soup)
    if price is not None:
        sheet_obj["Q{}".format(row)] = price
