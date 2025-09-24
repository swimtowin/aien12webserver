"""Tests for the HTML parsing helpers."""

from __future__ import annotations

import unittest

import computex_crawler.crawler as crawler


class DummySession:
    """Minimal session stub used in parsing tests."""

    def __getattr__(self, item):  # pragma: no cover - never used but keeps linter quiet
        raise AttributeError(item)


class ParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:  # pragma: no cover - skip logic not subject to coverage
        if crawler.BeautifulSoup is None:
            raise unittest.SkipTest("beautifulsoup4 is not available")

    def setUp(self) -> None:
        self.crawler = crawler.ComputexCrawler(session=DummySession())

    def test_parse_card_layout(self) -> None:
        html = """
        <html>
            <body>
                <ul class="exhibitor-list">
                    <li class="exhibitor-item">
                        <h3 class="companyName"><a href="/2025/ExhibitorDetail.aspx?id=1">ACME Corp.</a></h3>
                        <ul class="info">
                            <li><label>Website</label><a href="https://www.acme.com">https://www.acme.com</a></li>
                            <li><label>Tel</label><span>+886-2-1234-5678</span></li>
                            <li><label>Address</label><span>Taipei, Taiwan</span></li>
                        </ul>
                    </li>
                </ul>
                <ul class="pagination">
                    <li><a href="?cPage=2">Next</a></li>
                </ul>
            </body>
        </html>
        """

        exhibitors, has_next = self.crawler.parse_page(html, 1)
        self.assertTrue(has_next)
        self.assertEqual(len(exhibitors), 1)
        exhibitor = exhibitors[0]
        self.assertEqual(exhibitor.name, "ACME Corp.")
        self.assertEqual(exhibitor.website, "https://www.acme.com")
        self.assertEqual(exhibitor.phone, "+886-2-1234-5678")
        self.assertEqual(exhibitor.address, "Taipei, Taiwan")
        self.assertIn("ExhibitorDetail.aspx", exhibitor.detail_url or "")

    def test_parse_table_layout(self) -> None:
        html = """
        <html>
            <body>
                <table>
                    <thead>
                        <tr>
                            <th>Company</th>
                            <th>Website</th>
                            <th>Tel</th>
                            <th>Address</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><a href="/2025/ExhibitorDetail.aspx?id=2">Beta Ltd.</a></td>
                            <td><a href="https://beta.example.com">https://beta.example.com</a></td>
                            <td>Tel: +1 555 0100</td>
                            <td>Address: Kaohsiung, Taiwan</td>
                        </tr>
                    </tbody>
                </table>
            </body>
        </html>
        """

        exhibitors, has_next = self.crawler.parse_page(html, 1)
        self.assertFalse(has_next)
        self.assertEqual(len(exhibitors), 1)
        exhibitor = exhibitors[0]
        self.assertEqual(exhibitor.name, "Beta Ltd.")
        self.assertEqual(exhibitor.website, "https://beta.example.com")
        self.assertEqual(exhibitor.phone, "+1 555 0100")
        self.assertEqual(exhibitor.address, "Kaohsiung, Taiwan")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
