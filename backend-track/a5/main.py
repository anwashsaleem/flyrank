import os
import re
import json
import time
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin
from typing import Optional
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, Field, ValidationError

BASE_URL = "https://books.toscrape.com/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/anwashsaleem/flyrank)"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class ScrapedBook(BaseModel):
    title: str = Field(..., min_length=1)
    product_url: HttpUrl
    price_text: str
    price_gbp: float = Field(..., ge=0)
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: HttpUrl
    fetched_at: str

class ScraperReport:
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.pages_fetched = 0
        self.cache_hits = 0
        self.valid_records = 0
        self.invalid_records = 0
        self.failed_pages = 0
        self.errors = []

    def export(self, filepath: str):
        end_time = datetime.now(timezone.utc)
        duration_sec = (end_time - self.start_time).total_seconds()
        report = {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": round(duration_sec, 2),
            "pages_fetched": self.pages_fetched,
            "cache_hits": self.cache_hits,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "failed_pages": self.failed_pages,
            "errors": self.errors
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return report

report = ScraperReport()

def get_cache_path(url: str) -> str:
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{url_hash}.html")

def fetch_page(url: str, delay: float = 0.5) -> Optional[str]:
    cache_file = get_cache_path(url)
    if os.path.exists(cache_file):
        report.cache_hits += 1
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    headers = {"User-Agent": USER_AGENT}
    time.sleep(delay)
    
    for attempt in range(2):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                report.pages_fetched += 1
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                return resp.text
            elif resp.status_code in (404, 403):
                report.failed_pages += 1
                report.errors.append({"url": url, "status": resp.status_code, "reason": "Client Error / Not Found"})
                return None
        except Exception as e:
            if attempt == 1:
                report.failed_pages += 1
                report.errors.append({"url": url, "error": str(e)})
                return None
            time.sleep(1)
    return None

def normalize_price(price_text: str) -> float:
    match = re.search(r"[\d\.]+", price_text)
    return float(match.group()) if match else 0.0

def discover_catalogue(max_pages: int = 3):
    current_url = START_URL
    book_urls = []
    catalogue_pages = 0

    while current_url and catalogue_pages < max_pages:
        html = fetch_page(current_url)
        if not html:
            break
        catalogue_pages += 1
        soup = BeautifulSoup(html, "html.parser")
        
        for article in soup.select("article.product_pod"):
            link_tag = article.select_one("h3 a")
            if link_tag and "href" in link_tag.attrs:
                abs_url = urljoin(current_url, link_tag["href"])
                if abs_url not in book_urls:
                    book_urls.append(abs_url)

        next_tag = soup.select_one("li.next a")
        if next_tag and "href" in next_tag.attrs:
            current_url = urljoin(current_url, next_tag["href"])
        else:
            current_url = None

    return book_urls

def extract_book(url: str) -> Optional[dict]:
    html = fetch_page(url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    main_pod = soup.select_one(".product_main")
    if not main_pod:
        return None

    title_elem = main_pod.select_one("h1")
    title = title_elem.get_text(strip=True) if title_elem else "Unknown"

    price_elem = main_pod.select_one(".price_color")
    price_text = price_elem.get_text(strip=True) if price_elem else "£0.00"

    avail_elem = main_pod.select_one(".availability")
    availability_text = avail_elem.get_text(strip=True) if avail_elem else "Unknown"

    rating_tag = main_pod.select_one("p.star-rating")
    rating_classes = rating_tag.get("class", []) if rating_tag else []
    rating_text = [c for c in rating_classes if c != "star-rating"]
    rating = rating_text[0] if rating_text else "None"

    desc_elem = soup.select_one("#product_description ~ p")
    description = desc_elem.get_text(strip=True) if desc_elem else None

    return {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "price_gbp": normalize_price(price_text),
        "availability_text": availability_text,
        "rating_text": rating,
        "description": description,
        "source_page": url,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }

def main():
    print("[1/4] Discovering first 3 catalogue pages...")
    book_urls = discover_catalogue(max_pages=3)
    print(f"-> Discovered {len(book_urls)} unique book URLs across 3 catalogue pages.")

    # Deliberately inject 1 broken URL to prove error handling / resilience (Stage 5)
    test_urls = list(book_urls)
    test_urls.append("https://books.toscrape.com/catalogue/non-existent-page-test-404.html")

    validated_books = []
    failed_records = []

    print("[2/4] Fetching detail pages, extracting, and validating records...")
    for idx, url in enumerate(test_urls, start=1):
        raw_data = extract_book(url)
        if not raw_data:
            continue

        try:
            record = ScrapedBook(**raw_data)
            validated_books.append(record.model_dump(mode="json"))
            report.valid_records += 1
        except ValidationError as ve:
            report.invalid_records += 1
            failed_records.append({"data": raw_data, "errors": ve.errors()})

    print(f"[3/4] Writing {len(validated_books)} valid records to output/books.json...")
    books_file = os.path.join(OUTPUT_DIR, "books.json")
    with open(books_file, "w", encoding="utf-8") as f:
        json.dump(validated_books, f, indent=2)

    if failed_records:
        with open(os.path.join(OUTPUT_DIR, "errors.json"), "w", encoding="utf-8") as f:
            json.dump(failed_records, f, indent=2)

    print("[4/4] Writing run report to output/run-report.json...")
    report_file = os.path.join(OUTPUT_DIR, "run-report.json")
    final_report = report.export(report_file)
    print("\n--- RUN REPORT SUMMARY ---")
    print(json.dumps(final_report, indent=2))

if __name__ == "__main__":
    main()