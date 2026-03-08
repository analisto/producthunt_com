#!/usr/bin/env python3
"""
ProductHunt Scraper
  Step 1  – GET /categories  -> parse all category slugs -> data/categories.csv
  Step 2  – GraphQL CategoryPageListQuery for every category / every page
           -> data/products.csv

Usage:
    python scripts/scraper.py                  # full run
    python scripts/scraper.py --categories-only  # only step 1
"""

import asyncio
import aiohttp
import csv
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlencode

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL    = "https://www.producthunt.com"
GRAPHQL_URL = f"{BASE_URL}/frontend/graphql"

# Order for product ranking — valid values:
# most_recent | most_followed | best_rated | recent_launches
# highest_rated | trending | top_free | experiment
ORDER    = "best_rated"
PAGE_SIZE = 20   # max the API reliably returns with featuredOnly=True

# Max concurrent category requests in flight at once
CONCURRENCY = 5
# Seconds to wait between pages within a single category
PAGE_DELAY  = 0.05

# Paste the full cookie string from your browser here.
COOKIE_STR = (
    "first_visit=1772913542; first_referer=; "
    "_ga=GA1.1.224203124.1772913543; "
    "ajs_anonymous_id=875fe9ec-15a5-4576-84bc-411f3fb6c30d; "
    "visitor_id=8985d4f2-adb4-4491-b6ac-f5dee479dff7; "
    "track_code=5caff0dd41; "
    'g_state={"i_l":0,"i_ll":1772914470995,"i_b":"T0ci00jGWDf0DMIFTHg5LUvCjuMnefAiXjUm/0PETfA","i_e":{"enable_itp_optimization":0}}; '
    "homepageOnboardingCard-onboarding=2026-03-07+12%3A14%3A37+-0800; "
    "cf_clearance=pCfkP1tcaMPAScvBFzksKJXcDAC19X5An86a8sFSipQ-1772940363-1.2.1.1-96HIsCMSgAqtcHZ7rARcrqEDHqh_7Bqy5WONDz4tiziRB4SS9QJV92lZgNFcYbHwoYI6fg.IZKZwgNxoqdDjHj9iN680gdi6kx6yZ7C0WWIg02M3IHzqRVEHdIkFqO7CIDEUu00JRm3JhHyE9IuaC26dIOy0Km6c1Vv9Dd12MpWsON2GGrTvBQ6eAnWIBZ7nM76b53K9c1.ph4FsKiMXU7pzzVpX7K3HurhdLL6iH.8s_YsE3eOJnwOYyCOaTAfQ; "
    "__cf_bm=rrHl9YTNg0OSIOJ8ltQOFJH5o5QoUvSQh3xX4yNljIY-1772940363.0604696-1.0.1.1-czCND.iBwJorBJgis5xxpFhdT7tRheM2Rk99OKjMbayhVJAJ6La1s9RH3pczukMY3ltVl0O.ouNCrMslY_wIFRXFYyhvNG4TUNAv_wyD4sFqxZSdAisVuFh.OcAlwCdw; "
    "_ga_WZ46833KH9=GS2.1.s1772940362$o2$g1$t1772940375$j47$l0$h0; "
    "csrf_token=1gAvFgKAt8QInujrfs2CzVTNB9DabPWsdwO2LSJbaMZYgKYDjWMgeUXoJ6c8a31o50Npuv-QrBQVhtYXUInE6A; "
    "_producthunt_session_production=ac0wCgAxryoIRlugV1pyBR%2FCxYbtleCwiXhPAf9F5Y7HyBrOeARVvSqO5hSPRTdWjVQW%2Fh5mTNO60LMMds3VwmccnIG1xeIUvrjI1obOmJQa4Udks6sGUImO3nkZAS59KinnswWXBxHOHi9ofCHlPvb0xLhohvMIjF1l3%2B0Toxj24id1oBXr6%2FeJklGub%2FqS5uVG9RYvh%2Bc4zQDaphRuFsug7HCAzl0fhQSfCpUWZNblHtwfm3Qs6f%2B1beZLJ61dmfX2%2Fg18OcYPWfqRavDlmutNEOG51%2BtDcKXXHr5fcUOKdUB%2B7ePEQllgymt6SB8ic51bXeWkGjLHpYoJVA%3D%3D--mv6O8GFHyhWl0B5s--j273tt4YZ45nDSFxEo6SyA%3D%3D; "
    "_dd_s=aid=daaed056-4b0c-49fb-ae53-4b71cf81a225&rum=0&expire=1772941317252"
)

HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6",
    "content-type": "application/json",
    "dnt": "1",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
    "x-ph-timezone": "Asia/Baku",
    "x-requested-with": "XMLHttpRequest",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_cookie_str(cookie_str: str) -> dict:
    cookies: dict = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def load_query() -> tuple[str, str]:
    """Load CategoryPageListQuery from file, return (query_text, sha256_hash)."""
    query_file = Path("scripts/category_page_list_query.graphql")
    if not query_file.exists():
        raise FileNotFoundError(
            "scripts/category_page_list_query.graphql not found.\n"
            "Run: node scripts/extract_hash2.js  (requires: cd scripts && npm install)"
        )
    query_text = query_file.read_text(encoding="utf-8")
    query_hash = hashlib.sha256(query_text.encode("utf-8")).hexdigest()
    return query_text, query_hash


# ---------------------------------------------------------------------------
# Step 1 – categories
# ---------------------------------------------------------------------------

async def fetch_categories(session: aiohttp.ClientSession) -> list[dict]:
    url = f"{BASE_URL}/categories"
    headers = {**HEADERS, "referer": BASE_URL, "x-ph-referer": ""}
    async with session.get(url, headers=headers) as resp:
        resp.raise_for_status()
        html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")
    seen: set = set()
    categories: list[dict] = []

    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        if not href.startswith("/categories/"):
            continue
        slug = href.removeprefix("/categories/").split("?")[0].strip("/")
        if not slug or slug in seen:
            continue
        seen.add(slug)
        name = a.get_text(separator=" ", strip=True)
        categories.append({
            "name": name,
            "slug": slug,
            "url": f"{BASE_URL}/categories/{slug}",
        })

    return categories


# ---------------------------------------------------------------------------
# Step 2 – products via CategoryPageListQuery (POST with full query text)
# ---------------------------------------------------------------------------

async def gql_category_page(
    session: aiohttp.ClientSession,
    slug: str,
    page: int,
    query_text: str,
    query_hash: str,
    order: str = ORDER,
) -> dict:
    variables = {
        "slug":        slug,
        "order":       order,
        "page":        page,
        "pageSize":    PAGE_SIZE,
        "featuredOnly": True,
    }
    payload = {
        "operationName": "CategoryPageListQuery",
        "variables":     variables,
        "query":         query_text,
        "extensions":    {"persistedQuery": {"version": 1, "sha256Hash": query_hash}},
    }
    ref = f"{BASE_URL}/categories/{slug}" + (f"?page={page}" if page > 1 else "")
    headers = {**HEADERS, "referer": ref, "x-ph-referer": ref}

    async with session.post(GRAPHQL_URL, json=payload, headers=headers) as resp:
        resp.raise_for_status()
        return await resp.json(content_type=None)


def parse_response(data: dict, slug: str, cat_name: str) -> tuple[list[dict], bool]:
    """Return (rows, has_next_page)."""
    try:
        products_conn = data["data"]["productCategory"]["products"]
    except (KeyError, TypeError):
        return [], False

    edges    = products_conn.get("edges", [])
    has_next = products_conn.get("pageInfo", {}).get("hasNextPage", False)

    rows: list[dict] = []
    for edge in edges:
        node = edge.get("node") or {}
        if not node:
            continue

        logo_uuid = node.get("logoUuid") or ""
        logo_url  = f"https://ph-files.imgix.net/{logo_uuid}?auto=format" if logo_uuid else ""

        # structured data may contain website URL
        sd = node.get("structuredData") or {}
        website = sd.get("url", "")

        rows.append({
            "category_name":          cat_name,
            "category_slug":          slug,
            "id":                     node.get("id"),
            "name":                   node.get("name"),
            "tagline":                node.get("tagline"),
            "slug":                   node.get("slug"),
            "url":                    f"{BASE_URL}/products/{node.get('slug')}",
            "logo_url":               logo_url,
            "reviews_rating":         node.get("reviewsRating"),
            "reviews_count":          node.get("reviewsCount"),
            "detailed_reviews_count": node.get("detailedReviewsCount"),
            "followers_count":        node.get("followersCount"),
            "posts_count":            node.get("postsCount"),
            "is_top_product":         node.get("isTopProduct"),
            "is_no_longer_online":    node.get("isNoLongerOnline"),
            "website":                website,
        })
    return rows, has_next


async def scrape_category(
    session:    aiohttp.ClientSession,
    category:   dict,
    semaphore:  asyncio.Semaphore,
    out_rows:   list,
    out_lock:   asyncio.Lock,
    query_text: str,
    query_hash: str,
) -> None:
    slug     = category["slug"]
    cat_name = category["name"]
    page     = 1
    total    = 0

    async with semaphore:
        while True:
            try:
                data = await gql_category_page(
                    session, slug, page, query_text, query_hash
                )
            except Exception as exc:
                print(f"  [ERROR] {slug} page={page}: {exc}", flush=True)
                break

            rows, has_next = parse_response(data, slug, cat_name)

            if not rows and page == 1:
                print(f"  [WARN]  {slug}: no products on page 1", flush=True)
                break

            async with out_lock:
                out_rows.extend(rows)

            total += len(rows)
            print(f"  {slug:40s}  page={page:3d}  +{len(rows):3d}  total={total:4d}", flush=True)

            if not has_next:
                break

            page += 1
            await asyncio.sleep(PAGE_DELAY)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

PRODUCT_FIELDS = [
    "category_name", "category_slug",
    "id", "name", "tagline", "slug", "url", "logo_url",
    "reviews_rating", "reviews_count", "detailed_reviews_count",
    "followers_count", "posts_count",
    "is_top_product", "is_no_longer_online", "website",
]


async def main() -> None:
    categories_only = "--categories-only" in sys.argv

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    cookies   = parse_cookie_str(COOKIE_STR)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY + 5, ssl=True)
    timeout   = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(
        cookies=cookies, connector=connector, timeout=timeout
    ) as session:

        # ── Step 1: categories ──────────────────────────────────────────────
        print("Fetching /categories page …", flush=True)
        categories = await fetch_categories(session)
        print(f"Found {len(categories)} categories", flush=True)

        with open(data_dir / "categories.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "slug", "url"])
            writer.writeheader()
            writer.writerows(categories)
        print(f"Saved data/categories.csv  ({len(categories)} rows)", flush=True)

        if categories_only:
            return

        # ── Step 2: products ────────────────────────────────────────────────
        query_text, query_hash = load_query()
        print(f"\nCategoryPageListQuery hash: {query_hash}", flush=True)
        print(f"Scraping products ({CONCURRENCY} concurrent, order={ORDER}) …\n", flush=True)

        semaphore = asyncio.Semaphore(CONCURRENCY)
        out_rows: list[dict] = []
        out_lock  = asyncio.Lock()

        tasks = [
            scrape_category(
                session, cat, semaphore, out_rows, out_lock, query_text, query_hash
            )
            for cat in categories
        ]
        await asyncio.gather(*tasks)

        # Sort by category then rating descending
        out_rows.sort(
            key=lambda r: (r["category_slug"], -(float(r["reviews_rating"] or 0)))
        )

        with open(data_dir / "products.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=PRODUCT_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(out_rows)

        print(
            f"\nDone!  {len(out_rows)} total products saved to data/products.csv",
            flush=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
