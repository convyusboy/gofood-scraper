import pytest

from gofood_scraper import main


@pytest.fixture
def stubbed(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "get_cities", lambda: (["jakarta"], {"jakarta": ["jakarta-selatan"]}))
    monkeypatch.setattr(
        main, "parse_query", lambda q, a, d: ("Jakarta", "jakarta", "", "", ["ayam"])
    )
    monkeypatch.setattr(main, "get_restaurants", lambda *a, **k: None)
    return tmp_path


def test_run_returns_zero_when_menus_complete(monkeypatch, stubbed):
    monkeypatch.setattr(main, "get_menus", lambda *a, **k: True)
    assert main.run(["-q", "ayam in Jakarta", "-o", str(stubbed)]) == 0


def test_run_returns_one_when_menus_blocked(monkeypatch, stubbed):
    monkeypatch.setattr(main, "get_menus", lambda *a, **k: False)
    assert main.run(["-q", "ayam in Jakarta", "-o", str(stubbed)]) == 1


def test_run_returns_two_on_bad_query_flag(monkeypatch, stubbed):
    def bad(*a):
        raise ValueError("unknown location")

    monkeypatch.setattr(main, "parse_query", bad)
    assert main.run(["-q", "nonsense", "-o", str(stubbed)]) == 2
