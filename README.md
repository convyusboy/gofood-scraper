# Gofood Scraper

A CLI tool that scrapes restaurant listings from [gofood.co.id](https://gofood.co.id) for a chosen area/district and category, then visits each restaurant page to collect its rating, opening hours, price level, and menu items matching your keywords. Results are written to Excel files.

## Installation

Requires Python 3.10+ and Google Chrome installed.

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

You'll be prompted to:

1. Choose an area, and optionally a district within it.
2. Choose a category (Near me, Best sellers, Budget meal, Most loved, 24 hours, Healthy food, Pasti Ada Promo, or all of them).
3. Enter menu keywords to search for (semicolon-separated), e.g. `nila bakar; nila goreng`.

The scraper opens Chrome windows to do its work — don't close them while it's running. Results are saved to `outputs/<area>[-<district>]-<category>.xlsx`.

## Project layout

```
main.py               entry point
gofood_scraper/
  config.py            constants: URLs, CSS/XPath selectors, timing
  browser.py            Selenium WebDriver setup
  cli.py                interactive prompts
  cities.py             scrapes the areas/districts list
  restaurants.py         scrapes restaurant listings into Excel
  menus.py               visits each restaurant page for menu/hours/price/rating
  excel.py               Excel workbook helpers
outputs/                generated .xlsx files (gitignored)
```

## Notes

This scraper depends on gofood.co.id's current page structure and CSS class names, so it may break if the site changes.

## License

MIT — see [LICENSE](LICENSE).
