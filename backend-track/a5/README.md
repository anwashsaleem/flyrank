# A5: The Polite Scraper

A polite, deterministic web scraping pipeline that extracts 60 book records across 3 catalogue pages from Books to Scrape, normalizes fields, validates records with Pydantic, survives broken pages, and generates structured run reports.

## Target Classification & Ethics
- **Target**: Books to Scrape (`https://books.toscrape.com/`)
- **Purpose**: A public sandbox created specifically for testing web scrapers.
- **Scope**: Exactly the first 3 catalogue pages (60 books).
- **Robots.txt**: Checked `https://books.toscrape.com/robots.txt` (returns 404 / no robots file found).
- **Ethics Pledge**: "I will not reuse this code on another site without checking its rules and terms first."
- **Browserless Rationale**: All required data exists in raw server-rendered HTML; headless browsers like Playwright are unnecessary and waste system memory/compute.

## Politeness Rules
1. **Identifying User-Agent**: Sends `FlyRankInternship-A9/1.0 (+https://github.com/anwashsaleem/flyrank)`.
2. **Rate Limiting**: Enforces a minimum 500ms delay between live network requests.
3. **Local Disk Caching**: HTML responses are hashed and cached to `cache/` to avoid hammering the remote host during development.
4. **Timeouts & Retries**: 10s request timeout with automatic single-retry on network dropouts, skipping 404/403 client errors.

## Record Schema
Each item in `output/books.json` satisfies the following Pydantic schema:
- `title` (str, required)
- `product_url` (HttpUrl, canonical ID)
- `price_text` (str, raw currency text)
- `price_gbp` (float, normalized numeric value)
- `availability_text` (str)
- `rating_text` (str)
- `description` (str or null)
- `source_page` (HttpUrl, provenance tracking)
- `fetched_at` (ISO 8601 UTC timestamp)

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Execute pipeline
python main.py