from gofood_scraper.cli import input_search_query


def test_input_search_query_returns_raw_input(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda: "ayam in Jakarta Selatan")
    assert input_search_query() == "ayam in Jakarta Selatan"
    assert "Example: ayam in Jakarta Selatan" in capsys.readouterr().out
