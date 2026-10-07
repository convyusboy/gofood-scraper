"""Selenium WebDriver setup."""

import queue
import threading

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from gofood_scraper.config import DRIVER_RESOLVE_TIMEOUT

_service = None


def _resolve_driver_path(timeout=DRIVER_RESOLVE_TIMEOUT):
    """Resolve the chromedriver binary path, bounded by timeout.

    webdriver-manager's version check can hang indefinitely if its update
    endpoint is slow or unreachable (a known pain point of the library), with
    no built-in timeout of its own. Run it on a daemon thread so a stall there
    can't hang the whole scraper forever.
    """
    result = queue.Queue(maxsize=1)

    def resolve():
        try:
            result.put(("ok", ChromeDriverManager().install()))
        except Exception as exc:  # noqa: BLE001 - forwarded to the caller below
            result.put(("error", exc))

    threading.Thread(target=resolve, daemon=True).start()
    try:
        status, value = result.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError(
            "Timed out after {}s resolving chromedriver (webdriver-manager's online "
            "version check appears to be stuck). Check your network/proxy, or clear "
            "~/.wdm and try again.".format(timeout)
        ) from None
    if status == "error":
        raise value
    return value


def new_driver():
    """Return a fresh Chrome WebDriver, reusing the resolved driver binary across calls."""
    global _service
    if _service is None:
        _service = ChromeService(_resolve_driver_path())
    return webdriver.Chrome(service=_service)
