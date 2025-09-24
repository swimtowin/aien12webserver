import unittest
from typing import Optional

try:
    import flask  # type: ignore  # noqa: F401 - imported for availability check
except ImportError:  # pragma: no cover - dependency guard
    flask = None  # type: ignore

from computex_crawler.crawler import Exhibitor
from computex_crawler.webapp import create_app


class _DummyCrawler:
    def __init__(self, exhibitors, **kwargs):
        self._exhibitors = exhibitors
        self.kwargs = kwargs
        self.scrape_args: Optional[tuple[int, Optional[int]]] = None

    def scrape(self, start_page: int, max_pages: Optional[int]):
        self.scrape_args = (start_page, max_pages)
        return self._exhibitors


@unittest.skipIf(flask is None, "Flask is not available")
class WebAppTestCase(unittest.TestCase):
    def _make_factory(self, exhibitors):
        instances = {}

        def factory(**kwargs):
            crawler = _DummyCrawler(exhibitors, **kwargs)
            instances["crawler"] = crawler
            return crawler

        factory.instances = instances  # type: ignore[attr-defined]
        return factory

    def test_form_display(self):
        app = create_app(testing=True, crawler_factory=self._make_factory([]))
        client = app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"COMPUTEX \xe5%b1%95\xe5%95%86\xe5%90%8d\xe9%8c%84\xe7%88%ac\xe8%9f%b2", response.data)

    def test_successful_download_returns_tab_delimited_txt(self):
        exhibitors = [
            Exhibitor(
                name="測試公司",
                website="https://example.com",
                phone="02-1234-5678",
                address="台北市信義區",
                detail_url="https://example.com/detail",
            )
        ]
        factory = self._make_factory(exhibitors)
        app = create_app(testing=True, crawler_factory=factory)
        client = app.test_client()

        response = client.post(
            "/",
            data={
                "directory_url": "",  # should fallback to default URL
                "start_page": "2",
                "max_pages": "3",
                "delay": "0.1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "text/plain; charset=utf-8")
        content_disposition = response.headers.get("Content-Disposition", "")
        self.assertIn("attachment", content_disposition)
        self.assertTrue(content_disposition.endswith(".txt"))

        # BOM should be present for Excel compatibility
        self.assertTrue(response.data.startswith("\ufeff".encode("utf-8")))
        decoded = response.data.decode("utf-8-sig")
        self.assertIn("company_name\twebsite\tphone\taddress\tdetail_url", decoded)
        self.assertIn("測試公司\thttps://example.com\t02-1234-5678\t台北市信義區\thttps://example.com/detail", decoded)

        crawler = factory.instances["crawler"]
        self.assertEqual(crawler.kwargs["base_url"], "https://www.computex.biz/2025/ExhibitorDirectory.aspx")
        self.assertEqual(crawler.kwargs["delay"], 0.1)
        self.assertEqual(crawler.scrape_args, (2, 3))

    def test_invalid_inputs_display_error(self):
        app = create_app(testing=True, crawler_factory=self._make_factory([]))
        client = app.test_client()

        response = client.post(
            "/",
            data={
                "directory_url": "https://example.com",
                "start_page": "零",
                "max_pages": "",
                "delay": "0.5",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("請輸入有效的起始頁碼".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
