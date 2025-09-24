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

## 中文快速上手

以下步驟示範如何在可以連到 `www.computex.biz` 的電腦上執行爬蟲：

1. **安裝環境**
   - 安裝 Python 3.9 以上版本。
   - 下載或 clone 這個專案到本機，例如 `git clone https://github.com/<your-account>/aien12webserver.git`。
   - 在專案資料夾建立虛擬環境並安裝套件：

     ```bash
     python -m venv .venv
     # macOS / Linux
     source .venv/bin/activate
     # Windows PowerShell
     .venv\Scripts\Activate.ps1
     pip install -r requirements.txt
     ```

2. **使用命令列執行爬蟲**
   - 保持虛擬環境啟用，在專案根目錄輸入：

     ```bash
     python -m computex_crawler \
       --output exhibitors.txt \
       --start-page 1 \
       --delay 1.0
     ```

   - 預設會從官方目錄首頁開始抓取並自動翻頁。
   - `--output` 可以指定成 `.txt` 或 `.csv`，預設輸出檔案會是 `computex_exhibitors.csv`，以 UTF-8 編碼儲存，可直接用 Excel 開啟。
   - `--delay` 可以調整每頁之間的等待秒數，避免對官網造成過多負載。

3. **使用網頁介面**
   - 啟動 Flask 伺服器：

     ```bash
     export FLASK_APP=computex_crawler.webapp:create_app  # Windows 可改用 set 指令
     flask run --reload
     ```

   - 在瀏覽器開啟 <http://127.0.0.1:5000/>，輸入想爬的頁面網址與延遲秒數。
   - 按下開始後，爬蟲會執行並自動下載 `tab` 分隔的 `.txt` 檔，可直接匯入 Excel。

4. **Excel 匯入小技巧**
   - 若 Excel 開啟時未自動分欄，可使用「資料」→「自文字/CSV」功能，編碼選擇 UTF-8、分隔符號選擇 `Tab`。
   - 下載的檔案預設帶有 UTF-8 BOM，Excel 一般會自動辨識。

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
