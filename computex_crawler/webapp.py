"""Flask application that provides a simple interface for the crawler."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Callable, Optional, TYPE_CHECKING

try:  # pragma: no cover - dependency guard
    from flask import Flask, render_template, request, send_file
except ImportError:  # pragma: no cover - dependency guard
    Flask = None  # type: ignore
    render_template = request = send_file = None  # type: ignore

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from flask import Flask as FlaskType

from .crawler import BASE_URL, ComputexCrawler, Exhibitor


def create_app(
    testing: bool = False,
    crawler_factory: Optional[Callable[..., ComputexCrawler]] = None,
) -> "FlaskType":
    """Create and configure the Flask application."""

    if Flask is None:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "Flask is required to use the web interface. Install it with: pip install Flask"
        )

    app = Flask(__name__, template_folder="templates")
    if testing:
        app.config["TESTING"] = True

    if crawler_factory is None:
        crawler_factory = ComputexCrawler

    default_form = {
        "directory_url": BASE_URL,
        "start_page": "1",
        "max_pages": "",
        "delay": "0.5",
    }

    def _sanitize_field(value: str) -> str:
        return value.replace("\t", " ").replace("\r", " ").replace("\n", " ")

    @app.route("/", methods=["GET", "POST"])
    def index():  # type: ignore[override]
        form_data = dict(default_form)
        error: Optional[str] = None
        delay_value = float(default_form["delay"])

        if request.method == "POST":
            form_data = {
                "directory_url": request.form.get("directory_url", "").strip() or BASE_URL,
                "start_page": request.form.get("start_page", "").strip() or default_form["start_page"],
                "max_pages": request.form.get("max_pages", "").strip(),
                "delay": request.form.get("delay", "").strip() or default_form["delay"],
            }

            try:
                start_page = int(form_data["start_page"])
                if start_page < 1:
                    raise ValueError
            except ValueError:
                error = "請輸入有效的起始頁碼（1 以上的整數）。"
            else:
                max_pages: Optional[int]
                if form_data["max_pages"]:
                    try:
                        parsed_max_pages = int(form_data["max_pages"])
                        if parsed_max_pages < 1:
                            raise ValueError
                    except ValueError:
                        error = "最大頁數必須是 1 以上的整數或留空。"
                        max_pages = None
                    else:
                        max_pages = parsed_max_pages
                else:
                    max_pages = None

                if error is None:
                    try:
                        delay_value = float(form_data["delay"])
                        if delay_value < 0:
                            raise ValueError
                    except ValueError:
                        error = "延遲秒數必須是 0 或正數。"

            if error is None:
                try:
                    crawler = crawler_factory(
                        base_url=form_data["directory_url"],
                        delay=delay_value,
                    )
                    exhibitors = crawler.scrape(start_page=start_page, max_pages=max_pages)
                except Exception as exc:  # pragma: no cover - exercised through manual usage
                    error = f"爬蟲失敗：{exc}"
                else:
                    if not exhibitors:
                        error = "沒有抓到任何資料，請確認頁面是否有展商資訊。"
                    else:
                        return _build_txt_response(exhibitors)

        return render_template("index.html", form=form_data, error=error)

    def _build_txt_response(exhibitors: list[Exhibitor]):
        output = io.StringIO()
        output.write("company_name\twebsite\tphone\taddress\tdetail_url\n")
        for exhibitor in exhibitors:
            columns = [
                exhibitor.name,
                exhibitor.website or "",
                exhibitor.phone or "",
                exhibitor.address or "",
                exhibitor.detail_url or "",
            ]
            output.write("\t".join(_sanitize_field(value) for value in columns))
            output.write("\n")
        filename = f"computex_exhibitors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        data = output.getvalue().encode("utf-8-sig")
        output.close()
        return send_file(
            io.BytesIO(data),
            mimetype="text/plain; charset=utf-8",
            as_attachment=True,
            download_name=filename,
        )

    return app


__all__ = ["create_app"]

