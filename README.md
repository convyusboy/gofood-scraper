# Gofood Scraper

[![CI](https://github.com/convyusboy/gofood-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/convyusboy/gofood-scraper/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

A CLI tool that scrapes restaurant listings from [gofood.co.id](https://gofood.co.id) for a free-text search like "ayam in Jakarta Selatan", then visits each restaurant page to collect its rating, opening hours, price level, and menu items matching your keywords. Results are written to Excel files.

## Why this project

I built this to practice scraping a JavaScript-heavy, frequently changing site in a way that stays maintainable. Things it demonstrates:

- Separating pure HTML parsing from Selenium I/O, so the parsers are covered by fast offline fixture tests (36 tests, no browser or network needed).
- A free-text query parser that turns phrases like `nila bakar or nila goreng in Bandung` into keywords plus a fuzzy-matched location.
- Resumable output: the workbook is saved after every row, so an interrupted run picks up where it left off.
- Being upfront about limits: see [Known limitation](#known-limitation) and [Responsible use](#responsible-use).

## How it works

```
free-text query ──► parse_query ──► get_cities ──► get_restaurants ──► get_menus ──► .xlsx
 "ayam in Jakarta    keywords +      validate       listing page        per-restaurant   outputs/
  Selatan"           location        location       cards               detail pages
```

## Installation

Requires Python 3.10+ and Google Chrome installed.

```bash
pip install .
```

## Usage

```bash
gofood-scraper                              # prompts for a query
gofood-scraper -q "ayam in Jakarta Selatan"  # non-interactive
gofood-scraper -q "ayam in Jakarta" -f csv -f json   # also export CSV/JSON
gofood-scraper --help                       # -o/--output-dir, -f/--format, -v/--verbose
```

(`python -m gofood_scraper` works too.) The exit code is 0 on success, 1 if the menus stage was blocked, and 2 for an unrecognised `--query`.

Without `-q` you'll be prompted for a single search query in the form `<keyword(s)> in <area or district>`:

```
ayam in Jakarta Selatan
nila bakar or nila goreng in Bandung
find restaurants that have nasi padang in Jakarta
```

- The area/district is matched (fuzzily, case-insensitively) against gofood's real area/district list. Just the area name (e.g. `Jakarta`) searches the whole area; naming a district (e.g. `Jakarta Selatan`) narrows it down.
- Multiple keywords can be separated with `,`, `and`, or `or`, e.g. `nila bakar or nila goreng`.
- Filler words like "find", "restaurants", "that have" are ignored, so natural phrasing works.
- If the location can't be matched, you'll be asked again with a hint.

The scraper always searches gofood's "Near me" listing (the broadest single listing for an area). The scraper opens Chrome windows to do its work — don't close them while it's running. Results are saved to `outputs/<area>[-<district>]-near_me.xlsx` (plus `.csv`/`.json` with `-f`). After scraping, a one-line summary logs the restaurant count, mean rating and most common types.

## Project layout

```
gofood_scraper/
  main.py               entry point and argument parsing
  config.py            constants: URLs, CSS/XPath selectors, timing
  browser.py            Selenium WebDriver setup
  cli.py                interactive prompt for the search query
  query.py              parses the free-text query into area/district/keywords
  cities.py             scrapes the areas/districts list
  restaurants.py         scrapes restaurant listings into Excel
  menus.py               visits each restaurant page for menu/hours/price/rating
  excel.py               Excel workbook helpers
  export.py              CSV/JSON export and a rating/type summary
outputs/                generated .xlsx files (gitignored)
```

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest --cov=gofood_scraper   # offline unit tests (fixture-based, no network/browser)
pytest -m live      # opt-in tests that hit the real gofood.co.id site
```

## Known limitation

`get_cities` (area/district listing) and `get_restaurants` (listing pages) are confirmed working against the live site. The `menus` stage, which visits each restaurant's own page, is currently met with a CAPTCHA/bot challenge from gofood.co.id on every visit from an automated browser.

The scraper detects this (`BotChallengeError` in `menus.py`) and stops immediately instead of retrying. Progress already written to the `.xlsx` file is preserved, the menu/hours/price columns stay blank, and the process exits with code 1. Detection is a heuristic: it looks for CAPTCHA markers on a page that lacks the expected restaurant content. A weekly [live smoke test](.github/workflows/live-smoke.yml) flags selector drift on the listing pages.

This scraper also depends on gofood.co.id's current page structure and CSS class names in general, so it may break again if the site changes.

## Responsible use

This is a personal, educational project. It is not affiliated with GoFood or Gojek.

- Check gofood.co.id's Terms of Service and `robots.txt` before running it, and only scrape what you are allowed to.
- Keep request volume low. The tool paces itself with fixed pauses and is not meant for bulk or commercial collection.
- It deliberately does **not** attempt to bypass CAPTCHAs or other bot protection. When the site challenges the browser, the right behaviour is to stop, not to evade.

## License

MIT — see [LICENSE](LICENSE).
