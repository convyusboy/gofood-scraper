"""Selenium WebDriver setup."""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

_service = None


def new_driver():
    """Return a fresh Chrome WebDriver, reusing the resolved driver binary across calls."""
    global _service
    if _service is None:
        _service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=_service)
