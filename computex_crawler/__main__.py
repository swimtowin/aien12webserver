"""Command line interface for the COMPUTEX crawler."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .crawler import ComputexCrawler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape the COMPUTEX exhibitor directory")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("computex_exhibitors.csv"),
        help="Path to the CSV file that will store the results.",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="Page number to start scraping from (1-indexed).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to scrape. If omitted all available pages are processed.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between page requests to be polite to the server.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")

    crawler = ComputexCrawler(delay=args.delay)
    exhibitors = crawler.scrape(start_page=args.start_page, max_pages=args.max_pages)
    crawler.save_to_csv(exhibitors, str(args.output))
    logging.info("Saved %s exhibitors to %s", len(exhibitors), args.output)


if __name__ == "__main__":
    main()
