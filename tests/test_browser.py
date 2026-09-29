import time

import pytest

from gofood_scraper import browser


class _StubManager:
    def __init__(self, install_fn):
        self._install_fn = install_fn

    def install(self):
        return self._install_fn()


def test_resolve_driver_path_returns_result_promptly(monkeypatch):
    monkeypatch.setattr(browser, "ChromeDriverManager", lambda: _StubManager(lambda: "/fake/chromedriver"))
    assert browser._resolve_driver_path(timeout=2) == "/fake/chromedriver"


def test_resolve_driver_path_times_out_instead_of_hanging(monkeypatch):
    def hang_forever():
        time.sleep(10)

    monkeypatch.setattr(browser, "ChromeDriverManager", lambda: _StubManager(hang_forever))
    with pytest.raises(TimeoutError):
        browser._resolve_driver_path(timeout=0.2)


def test_resolve_driver_path_propagates_install_errors(monkeypatch):
    def boom():
        raise RuntimeError("network unreachable")

    monkeypatch.setattr(browser, "ChromeDriverManager", lambda: _StubManager(boom))
    with pytest.raises(RuntimeError, match="network unreachable"):
        browser._resolve_driver_path(timeout=2)
