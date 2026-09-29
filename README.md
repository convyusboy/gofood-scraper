# Gofood Scraper

A CLI tool that scrapes restaurant listings from [gofood.co.id](https://gofood.co.id) for a free-text search like "ayam in Jakarta Selatan", then visits each restaurant page to collect its rating, opening hours, price level, and menu items matching your keywords. Results are written to Excel files.

## Installation

Requires Python 3.10+ and Google Chrome installed.

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

You'll be prompted for a single search query in the form `<keyword(s)> in <area or district>`:

```
ayam in Jakarta Selatan
nila bakar or nila goreng in Bandung
find restaurants that have nasi padang in Jakarta
```

- The area/district is matched (fuzzily, case-insensitively) against gofood's real area/district list. Just the area name (e.g. `Jakarta`) searches the whole area; naming a district (e.g. `Jakarta Selatan`) narrows it down.
- Multiple keywords can be separated with `,`, `and`, or `or`, e.g. `nila bakar or nila goreng`.
- Filler words like "find", "restaurants", "that have" are ignored, so natural phrasing works.
- If the location can't be matched, you'll be asked again with a hint.

The scraper always searches gofood's "Near me" listing (the broadest single listing for an area). The scraper opens Chrome windows to do its work — don't close them while it's running. Results are saved to `outputs/<area>[-<district>]-near_me.xlsx`.

## Project layout

```
main.py               entry point
gofood_scraper/
  config.py            constants: URLs, CSS/XPath selectors, timing
  browser.py            Selenium WebDriver setup
  cli.py                interactive prompt for the search query
  query.py              parses the free-text query into area/district/keywords
  cities.py             scrapes the areas/districts list
  restaurants.py         scrapes restaurant listings into Excel
  menus.py               visits each restaurant page for menu/hours/price/rating
  excel.py               Excel workbook helpers
outputs/                generated .xlsx files (gitignored)
```

## Development

```bash
pip install -r requirements-dev.txt
pytest              # offline unit tests (fixture-based, no network/browser)
pytest -m live      # opt-in tests that hit the real gofood.co.id site
```

## Known limitation

`get_cities` (area/district listing) and `get_restaurants` (listing pages) are confirmed working against the live site. The `menus` stage, which visits each restaurant's own page, is currently met with a CAPTCHA/bot challenge from gofood.co.id on every visit from an automated browser. When that happens the scraper retries a few times, prints a message, and moves on — progress already written to the `.xlsx` file is preserved, but that category's menu/hours/price columns will stay blank until the site stops challenging automated requests.

This scraper also depends on gofood.co.id's current page structure and CSS class names in general, so it may break again if the site changes.

## License

MIT — see [LICENSE](LICENSE).
