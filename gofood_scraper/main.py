"""Entry point: scrapes restaurants matching a free-text search query."""

import argparse
import logging
import os
import sys

from gofood_scraper.cities import get_cities
from gofood_scraper.cli import input_search_query
from gofood_scraper.config import DEFAULT_CATEGORY_LINK, OUTPUT_DIR
from gofood_scraper.excel import output_path
from gofood_scraper.export import FORMATS, export, read_rows, summarize
from gofood_scraper.menus import get_menus
from gofood_scraper.query import parse_query
from gofood_scraper.restaurants import get_restaurants

log = logging.getLogger(__name__)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="gofood-scraper",
        description="Scrape gofood.co.id restaurants for a query like 'ayam in Jakarta Selatan'.",
    )
    parser.add_argument(
        "-q", "--query", help="search query; if omitted you will be prompted for one"
    )
    parser.add_argument("-o", "--output-dir", default=OUTPUT_DIR, help="folder for .xlsx output")
    parser.add_argument(
        "-f", "--format", action="append", choices=FORMATS, default=[],
        help="also export the results as csv and/or json (repeatable); .xlsx is always written",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug logging")
    return parser


def run(argv=None):
    """Run the scraper. Returns a process exit code (0 on success, 1 if menus were blocked)."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s"
    )

    log.info("Welcome to gofood scraper")
    area_arr, districts_dict = get_cities()

    query = args.query
    while True:
        if query is None:
            query = input_search_query()
        try:
            area_str, area_link, district_str, district_link, keyword_arr = parse_query(
                query, area_arr, districts_dict
            )
            break
        except ValueError as exc:
            if args.query is not None:
                log.error("%s", exc)
                return 2
            log.warning("%s", exc)
            query = None

    location_str = district_str or area_str
    log.info('Searching for "%s" in %s', ", ".join(keyword_arr), location_str)
    log.info("Start scraping; don't close any Google Chrome window that opens.")

    os.makedirs(args.output_dir, exist_ok=True)
    category_links = [DEFAULT_CATEGORY_LINK]
    get_restaurants(args.output_dir, area_link, district_link, category_links)
    completed = get_menus(args.output_dir, area_link, district_link, category_links, keyword_arr)

    xlsx_path = output_path(args.output_dir, area_link, district_link, category_links[0])
    stats = summarize(read_rows(xlsx_path))
    log.info(
        "%d restaurants (%d rated), mean rating %s; top types: %s",
        stats["count"], stats["rated"], stats["mean_rating"] or "n/a",
        ", ".join("{} ({})".format(name, n) for name, n in stats["top_types"]) or "n/a",
    )
    for path in export(xlsx_path, args.format):
        log.info("Wrote %s", path)

    if not completed:
        log.error("Finished with incomplete menu data; see the message above.")
        return 1
    log.info("Done. Check the .xlsx file(s) in the %s folder.", args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(run())
