# COMPUTEX 2025 Exhibitor Directory Crawler

This repository contains a Python crawler that collects exhibitor information from the [COMPUTEX 2025 exhibitor directory](https://www.computex.biz/2025/ExhibitorDirectory.aspx). It extracts the company name, website, telephone number and address from every listing and follows the pagination automatically.

> ⚠️ The execution environment for this repository does not have outbound internet access. To run the crawler successfully you will need to execute it on a machine that can reach `www.computex.biz` and install the dependencies listed in [`requirements.txt`](requirements.txt).

## Features

- Automatically walks through every directory page starting from an arbitrary page number.
- Extracts company name, website, phone number, address and (when available) the detail page URL for each exhibitor.
- Provides a reusable Python API, command line interface and web UI.
- Writes the collected data to a UTF-8 CSV or tab-delimited TXT file.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\\Scripts\\activate`
pip install -r requirements.txt
```

## Command line usage

```bash
python -m computex_crawler --output exhibitors.csv --start-page 1 --delay 1.0
```

Arguments:

- `--output` / `-o`: Path of the CSV file to create. Defaults to `computex_exhibitors.csv`.
- `--start-page`: Page number (1-indexed) where the crawl should begin. Defaults to `1`.
- `--max-pages`: Maximum number of pages to visit. If omitted the crawler continues until no further pages are detected.
- `--delay`: Sleep time (seconds) between page requests.
- `--log-level`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).

## Using the crawler from Python

```python
from computex_crawler import scrape_computex

exhibitors = scrape_computex(output_csv="exhibitors.csv", delay=1.0)
for exhibitor in exhibitors:
    print(exhibitor.name, exhibitor.website, exhibitor.phone, exhibitor.address)
```

The helper returns a list of `Exhibitor` dataclass instances. If `output_csv` is provided the data is also written to a CSV file.

## Web interface

You can launch a lightweight web interface that accepts the directory URL and
automatically produces a tab-delimited `.txt` file that can be opened in Excel:

```bash
export FLASK_APP=computex_crawler.webapp:create_app
flask run --reload
```

Open <http://127.0.0.1:5000/> in your browser and provide the COMPUTEX
directory URL. Submitting the form will trigger the crawler and download a
UTF-8 (with BOM) text file using tab separation so Excel can import the data
without additional configuration.

## Testing

Unit tests rely only on the Python standard library. Run them with:

```bash
python -m unittest
```

## Notes on responsible crawling

- Respect the website's terms of service and robots.txt rules.
- Keep the default `--delay` or increase it to avoid sending too many requests in a short period of time.
- Avoid running the crawler in parallel.
