"""Utilities for crawling the COMPUTEX 2025 exhibitor directory."""

from __future__ import annotations

import csv
import logging
import re
import time
from dataclasses import dataclass
from html import unescape
from typing import Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urljoin

try:  # pragma: no cover - dependency guard
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover - dependency guard
    requests = None  # type: ignore
    HTTPAdapter = None  # type: ignore
    Retry = None  # type: ignore

try:  # pragma: no cover - dependency guard
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - dependency guard
    BeautifulSoup = None  # type: ignore

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://www.computex.biz/2025/ExhibitorDirectory.aspx"

PHONE_LABELS = ("tel", "phone", "電話")
ADDRESS_LABELS = ("address", "add", "地址")
WEBSITE_LABELS = ("website", "web", "網址", "官網")


@dataclass
class Exhibitor:
    """Structured representation of a single exhibitor entry."""

    name: str
    website: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    detail_url: Optional[str] = None

    def as_row(self) -> List[str]:
        """Return the exhibitor as a row for CSV writing."""

        return [
            self.name,
            self.website or "",
            self.phone or "",
            self.address or "",
            self.detail_url or "",
        ]


class ComputexCrawler:
    """Crawler for the COMPUTEX exhibitor directory."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        delay: float = 0.5,
        session: Optional[requests.Session] = None,
    ) -> None:
        if BeautifulSoup is None:
            raise RuntimeError(
                "beautifulsoup4 is required to use ComputexCrawler. "
                "Install it with: pip install beautifulsoup4"
            )

        if session is None:
            if requests is None:
                raise RuntimeError(
                    "requests is required to create a ComputexCrawler session. "
                    "Install it with: pip install requests"
                )
            session = self._build_session()

        self.base_url = base_url
        self.delay = delay
        self.session = session

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=5,
            read=5,
            connect=5,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0 Safari/537.36"
                ),
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            }
        )
        return session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_page(self, page: int) -> str:
        """Fetch a page from the directory and return HTML."""

        params = {"cPage": page} if page > 1 else None
        LOGGER.debug("Fetching %s page %s", self.base_url, page)
        response = self.session.get(self.base_url, params=params, timeout=30)
        response.raise_for_status()
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding
        return response.text

    def scrape(
        self,
        start_page: int = 1,
        max_pages: Optional[int] = None,
    ) -> List[Exhibitor]:
        """Scrape the exhibitor directory and return collected data."""

        page = start_page
        collected: List[Exhibitor] = []
        pages_scraped = 0

        while True:
            if max_pages is not None and pages_scraped >= max_pages:
                break

            html = self.fetch_page(page)
            exhibitors, has_next = self.parse_page(html, page)
            LOGGER.info("Page %s: found %s exhibitors", page, len(exhibitors))
            if not exhibitors:
                LOGGER.info("No exhibitors found on page %s, stopping.", page)
                break
            collected.extend(exhibitors)
            pages_scraped += 1
            if not has_next:
                break
            page += 1
            if self.delay:
                time.sleep(self.delay)

        return collected

    def parse_page(self, html: str, page_number: int) -> Tuple[List[Exhibitor], bool]:
        """Parse the HTML of a single page and return exhibitors and next-page flag."""

        soup = BeautifulSoup(html, "html.parser")
        exhibitors = self._parse_cards(soup)
        if not exhibitors:
            exhibitors = self._parse_table(soup)
        has_next = self._has_next_page(soup, page_number) if exhibitors else False
        return exhibitors, has_next

    # ------------------------------------------------------------------
    # CSV helper
    # ------------------------------------------------------------------
    def save_to_csv(self, exhibitors: Sequence[Exhibitor], csv_path: str) -> None:
        """Write exhibitors to a CSV file."""

        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["company_name", "website", "phone", "address", "detail_url"])
            for exhibitor in exhibitors:
                writer.writerow(exhibitor.as_row())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _parse_cards(self, soup: BeautifulSoup) -> List[Exhibitor]:
        cards = self._find_card_candidates(soup)
        exhibitors: List[Exhibitor] = []
        seen_names: set[str] = set()
        for card in cards:
            exhibitor = self._parse_exhibitor_card(card)
            if exhibitor and exhibitor.name not in seen_names:
                exhibitors.append(exhibitor)
                seen_names.add(exhibitor.name)
        return exhibitors

    def _find_card_candidates(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        selectors = [
            ".exhibitor-list .exhibitor-item",
            "ul.exhibitor-list > li",
            ".exhibitors-list .item",
            ".companyList .listItem",
            "div.exhibitor-item",
            "div.company-list-item",
            "li.exhibitor",
            "div[class*='exhibitor']",
        ]
        for selector in selectors:
            matches = soup.select(selector)
            if matches:
                filtered = [m for m in matches if self._looks_like_card(m)]
                if filtered:
                    return filtered
        # fallback - look for sections that contain telephone info
        candidates = []
        for container in soup.find_all(["div", "li", "article"], recursive=True):
            text = self._normalize_whitespace(container.get_text(" ", strip=True))
            if not text:
                continue
            if any(keyword in text.lower() for keyword in PHONE_LABELS + ADDRESS_LABELS):
                candidates.append(container)
        return candidates

    def _looks_like_card(self, element: BeautifulSoup) -> bool:
        text = self._normalize_whitespace(element.get_text(" ", strip=True))
        if not text:
            return False
        if any(keyword in text.lower() for keyword in PHONE_LABELS + ADDRESS_LABELS):
            return True
        link = element.find("a", href=True)
        if link:
            href = link.get("href", "")
            if "Exhibitor" in href or "exhibitor" in href:
                return True
        return False

    def _parse_exhibitor_card(self, card: BeautifulSoup) -> Optional[Exhibitor]:
        name = self._find_name(card)
        if not name:
            return None
        website = self._find_website(card)
        phone = self._find_field(card, PHONE_LABELS)
        address = self._find_field(card, ADDRESS_LABELS)
        detail_url = self._find_detail_url(card)
        return Exhibitor(name=name, website=website, phone=phone, address=address, detail_url=detail_url)

    def _find_name(self, card: BeautifulSoup) -> Optional[str]:
        selectors = [
            ".companyName",
            ".company-name",
            ".CompanyName",
            ".company\ name",
            "h2 a",
            "h3 a",
            "h4 a",
            "h5 a",
            "h2",
            "h3",
            "h4",
            "h5",
        ]
        for selector in selectors:
            node = card.select_one(selector)
            if node:
                text = self._normalize_whitespace(node.get_text(" ", strip=True))
                if text:
                    return text
        # fallback: first anchor with detail link
        for anchor in card.find_all("a", href=True):
            href = anchor.get("href", "")
            if "Exhibitor" in href and anchor.get_text(strip=True):
                return self._normalize_whitespace(anchor.get_text(" ", strip=True))
        text = card.get_text(" ", strip=True)
        return self._normalize_whitespace(text.split(" ", 1)[0]) if text else None

    def _find_website(self, card: BeautifulSoup) -> Optional[str]:
        for anchor in card.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href:
                continue
            href_lower = href.lower()
            if href_lower.startswith("mailto:") or href_lower.startswith("javascript"):
                continue
            if href_lower.startswith("http") and "computex.biz" not in href_lower:
                return href
            text = self._normalize_whitespace(anchor.get_text(" ", strip=True))
            if any(label in text.lower() for label in WEBSITE_LABELS) and href_lower.startswith("http"):
                return href
        return None

    def _find_field(self, card: BeautifulSoup, labels: Iterable[str]) -> Optional[str]:
        label_patterns = [re.compile(rf"{re.escape(label)}", re.IGNORECASE) for label in labels]
        for element in card.find_all(["li", "div", "p", "span"], recursive=True):
            text = self._normalize_whitespace(element.get_text(" ", strip=True))
            if not text:
                continue
            lower = text.lower()
            if any(label in lower for label in labels):
                cleaned = text
                for pattern in label_patterns:
                    cleaned = pattern.sub("", cleaned)
                cleaned = cleaned.lstrip(" :：-、")
                return cleaned or None
        return None

    def _find_detail_url(self, card: BeautifulSoup) -> Optional[str]:
        for anchor in card.find_all("a", href=True):
            href = anchor.get("href", "")
            if "Exhibitor" in href:
                return urljoin(self.base_url, href)
        return None

    def _parse_table(self, soup: BeautifulSoup) -> List[Exhibitor]:
        tables = soup.find_all("table")
        exhibitors: List[Exhibitor] = []
        for table in tables:
            headers = [self._normalize_whitespace(th.get_text(" ", strip=True)).lower() for th in table.find_all("th")]
            if headers and "company" not in " ".join(headers) and "公司" not in " ".join(headers):
                continue
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if not cells:
                    continue
                name = self._normalize_whitespace(cells[0].get_text(" ", strip=True)) if cells else None
                if not name:
                    continue
                website = self._extract_link_from_cell(cells)
                phone = self._extract_field_from_cells(cells, PHONE_LABELS)
                address = self._extract_field_from_cells(cells, ADDRESS_LABELS)
                exhibitors.append(
                    Exhibitor(
                        name=name,
                        website=website,
                        phone=phone,
                        address=address,
                        detail_url=self._extract_detail_from_cells(cells),
                    )
                )
        return exhibitors

    def _extract_link_from_cell(self, cells: Sequence[BeautifulSoup]) -> Optional[str]:
        for cell in cells:
            for anchor in cell.find_all("a", href=True):
                href = anchor.get("href", "")
                if href.lower().startswith("http") and "computex.biz" not in href.lower():
                    return href
        return None

    def _extract_detail_from_cells(self, cells: Sequence[BeautifulSoup]) -> Optional[str]:
        for cell in cells:
            for anchor in cell.find_all("a", href=True):
                href = anchor.get("href", "")
                if "Exhibitor" in href:
                    return urljoin(self.base_url, href)
        return None

    def _extract_field_from_cells(self, cells: Sequence[BeautifulSoup], labels: Iterable[str]) -> Optional[str]:
        label_patterns = [re.compile(rf"{re.escape(label)}", re.IGNORECASE) for label in labels]
        for cell in cells:
            text = self._normalize_whitespace(cell.get_text(" ", strip=True))
            if not text:
                continue
            lower = text.lower()
            if any(label in lower for label in labels):
                cleaned = text
                for pattern in label_patterns:
                    cleaned = pattern.sub("", cleaned)
                cleaned = cleaned.lstrip(" :：-、")
                return cleaned or None
        return None

    def _has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        next_page = current_page + 1
        pattern = re.compile(rf"cPage={next_page}(?:&|$)", re.IGNORECASE)
        link = soup.find("a", href=pattern)
        if link:
            return True
        for text in ("next", "下一頁", ">", "»"):
            anchor = soup.find("a", string=re.compile(text, re.IGNORECASE))
            if anchor and anchor.get("href"):
                return True
        return False

    @staticmethod
    def _normalize_whitespace(value: Optional[str]) -> str:
        if not value:
            return ""
        return re.sub(r"\s+", " ", unescape(value)).strip()


def scrape_computex(
    output_csv: Optional[str] = None,
    start_page: int = 1,
    max_pages: Optional[int] = None,
    delay: float = 0.5,
) -> List[Exhibitor]:
    """Convenience wrapper around :class:`ComputexCrawler`."""

    crawler = ComputexCrawler(delay=delay)
    exhibitors = crawler.scrape(start_page=start_page, max_pages=max_pages)
    if output_csv:
        crawler.save_to_csv(exhibitors, output_csv)
    return exhibitors
