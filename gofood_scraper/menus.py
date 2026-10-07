"""Visit each scraped restaurant page and fill in menu, hours, rating and price data."""

import logging
import re
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
from gofood_scraper.excel import column, output_path

# column letters for each day, in the order the open-hours rows appear on the page
log = logging.getLogger(__name__)

DAY_COLUMNS = [column(day) for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")]

# Lower-case markers that suggest a CAPTCHA / bot-challenge page. They are only trusted when the
# page also lacks the restaurant content we expect (see _is_bot_challenge), since a normal page
# may legitimately ship a captcha script.
BOT_CHALLENGE_MARKERS = (
    "captcha",
    "cf-challenge",
    "verify you are human",
    "are you a robot",
    "unusual traffic",
)


class BotChallengeError(Exception):
    """gofood.co.id served a CAPTCHA/bot challenge instead of the restaurant page."""


def get_menus(output_dir, area, district, category_links, keyword_arr):
    """Fill in menu/hours/rating/price data for every category, retrying on transient errors.

    Returns True if every category was completed, False if any was abandoned
    (typically because gofood.co.id served a bot/CAPTCHA challenge).
    """
    all_done = True
    for category_link in category_links:
        for attempt in range(1, MAX_RETRY_COUNT + 1):
            try:
                if _get_menus_for_category(output_dir, area, district, category_link, keyword_arr):
                    break
            except BotChallengeError as exc:
                # retrying a challenge only hammers the site, so stop right away
                all_done = False
                log.error("%s Stopping; rows already scraped are saved in the .xlsx file.", exc)
                break
            except (NoSuchElementException, StaleElementReferenceException):
                if attempt == MAX_RETRY_COUNT:
                    all_done = False
                    log.error(
                        "giving up on %s after %d attempts - gofood.co.id may be showing a "
                        "bot/CAPTCHA challenge to automated browsers right now. Progress made "
                        "so far is saved in the .xlsx file; re-run later to fill in the rest.",
                        category_link,
                        MAX_RETRY_COUNT,
                    )
                else:
                    log.warning("there's a bot, retrying (%d/%d)", attempt, MAX_RETRY_COUNT)
    return all_done


def _get_menus_for_category(output_dir, area, district, category_link, keyword_arr):
    path = output_path(output_dir, area, district, category_link)
    wb_obj = openpyxl.load_workbook(path)
    sheet_obj = wb_obj.active

    for row, cell in enumerate(sheet_obj["A"], start=1):
        if row < 2:
            continue
        wb_obj.save(path)
        if sheet_obj["{}{}".format(column("Monday"), row)].value is not None:
            continue
        log.info("processing row %d - %s", row, sheet_obj["{}{}".format(column("Name"), row)].value)
        _scrape_restaurant_row(sheet_obj, row, cell.value, keyword_arr)
        wb_obj.save(path)

    wb_obj.save(path)
    return True


def _scrape_restaurant_row(sheet_obj, row, url, keyword_arr):
    driver = new_driver()
    try:
        driver.get(url)
        time.sleep(SCROLL_PAUSE_TIME)
        _raise_if_bot_challenge(driver.page_source, url)

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
        except NoSuchElementException:
            # a challenge page has none of the expected elements; tell it apart from a transient miss
            _raise_if_bot_challenge(driver.page_source, url)
            raise

        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    _raise_if_bot_challenge(str(soup), url)

    total_menu_with_inputted_keywords, total_menu, menu_with_inputted_keywords = _extract_menus(soup, keyword_arr)

    sheet_obj[column("Total Rating") + str(row)] = total_rating
    sheet_obj[column("Total Menu with Inputted Keywords") + str(row)] = "{}/{}".format(
        total_menu_with_inputted_keywords, total_menu
    )
    sheet_obj[column("Menu with Inputted Keywords") + str(row)] = menu_with_inputted_keywords

    address = soup.find("div", class_=CLASS_RESTAURANT_ADDRESS)
    if address is not None:
        sheet_obj[column("Address") + str(row)] = address.text.strip()

    _fill_open_hours(sheet_obj, row, soup)
    _fill_price(sheet_obj, row, soup)


def _is_bot_challenge(html):
    """True if the page looks like a CAPTCHA/bot challenge rather than a restaurant page."""
    if CLASS_MENU_CARD in html:
        return False
    html_lower = html.lower()
    return any(marker in html_lower for marker in BOT_CHALLENGE_MARKERS)


def _raise_if_bot_challenge(html, url):
    if _is_bot_challenge(html):
        raise BotChallengeError("gofood.co.id served a CAPTCHA/bot challenge for {}.".format(url))


def _extract_total_rating(rating_html_content):
    match = re.search(r'ratingCount"\s*:\s*([^,}\s]+)', rating_html_content)
    return match.group(1) if match else "-"


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
        big_menu_soup = menu.find("h3", class_=CLASS_BIG_MENU_CARD)
        if big_menu_soup is None:
            log.debug("skipping a menu card without a name")
            continue
        total_menu += 1
        big_menu = big_menu_soup.text.strip()
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
    price_level_soup = soup.find(attrs={"data-testid": "priceLevel"})
    if len(price_range) < 3 or price_level_soup is None:
        return None
    price_level = len(price_level_soup.find_all("div", class_=CLASS_RESTAURANT_PRICE_LEVEL))
    return "{}/4 ({})".format(price_level, price_range[2].text.strip())


def _fill_open_hours(sheet_obj, row, soup):
    for col, value in _extract_open_hours(soup).items():
        sheet_obj["{}{}".format(col, row)] = value


def _fill_price(sheet_obj, row, soup):
    price = _extract_price(soup)
    if price is not None:
        sheet_obj[column("Gofood Price Level") + str(row)] = price
