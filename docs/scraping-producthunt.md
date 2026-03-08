# Scraping ProductHunt — Complete Investigation & Guide

## Overview

This document covers everything discovered while building `scripts/scraper.py` — a fully async scraper for ProductHunt categories and products. It documents the API structure, the dead ends hit, the breakthroughs found, and actionable patterns for anyone building on top of this.

---

## 1. Site Architecture

ProductHunt is a **Next.js + Apollo Client** app. Key implications:

| Property | Detail |
|---|---|
| Rendering | **Client-side** for product listings (no `__NEXT_DATA__`), **SSR** only for viewer/session data |
| GraphQL | Apollo Client with **Automatic Persisted Queries (APQ)** |
| Protection | Cloudflare (browser challenge on HTML pages, cookie-based auth) |
| API endpoint | `https://www.producthunt.com/frontend/graphql` |

There is **no embedded JSON** in the HTML for product data. Everything is fetched client-side via GraphQL after page load.

---

## 2. Authentication

All API requests require valid session cookies. Without them, the HTML page returns 403 and the GraphQL API returns empty or error responses.

**Required cookies (from an active browser session):**

| Cookie | Purpose |
|---|---|
| `cf_clearance` | Cloudflare clearance — expires, must be refreshed |
| `_producthunt_session_production` | Rails session — expires ~3 months |
| `csrf_token` | CSRF protection for POST requests |
| `visitor_id` | Anonymous visitor tracking |

**How to obtain:**
1. Open DevTools → Application → Cookies on `producthunt.com`
2. Copy all cookies as a single string
3. Paste into `COOKIE_STR` in `scripts/scraper.py`

**Cookie lifetime:** `cf_clearance` typically lasts 24–48 hours. `_producthunt_session_production` lasts until the session expires (weeks/months). When scraping fails with 403 or empty data, refresh `cf_clearance` first.

---

## 3. The Two GraphQL Queries

### 3.1 `CategoryPageQuery` — Category Metadata (NOT for products)

This is the query visible in the network tab when navigating to a category page.

```
GET /frontend/graphql?operationName=CategoryPageQuery
  &variables={"slug":"ai-meeting-notetakers","path":"/categories/ai-meeting-notetakers"}
  &extensions={"persistedQuery":{"version":1,"sha256Hash":"eeaa942691c4ef61705f6147c8f0cc2e74beef7638f8c68fb2569fb30e020287"}}
```

**What it returns:**

```json
{
  "data": {
    "productCategory": {
      "id": "1288",
      "name": "AI notetakers",
      "description": "...",
      "slug": "ai-meeting-notetakers",
      "path": "/categories/ai-meeting-notetakers",
      "snapshot": { "reviewsCount": 2567, "lastUpdatedAt": "..." },
      "heroProducts": { "totalCount": 114, "edges": [ /* only 6 items */ ] },
      "recentLaunches": { "totalCount": 112 },
      "discussions": { "edges": [...], "pageInfo": { "hasNextPage": true } },
      "questions": [...],
      "subCategories": { "edges": [...] }
    }
  }
}
```

**Critical discovery:** `heroProducts` always returns exactly **6 products** regardless of the `page` variable. The `recentLaunches` collection only returns `totalCount` — no edges. The `page` variable has **no effect** on this query's product data.

**Use this query for:** category metadata (id, name, description, slug, reviewsCount).
**Do NOT use this query for:** paginated product listings.

---

### 3.2 `CategoryPageListQuery` — Paginated Product Listings ✓

This is the actual query that loads ranked products. It is **not easily visible** in the network tab because it fires client-side after hydration.

**Found by:** searching `8c49b1d4ec0e985b.js` (JS bundle) for the string `"CategoryPageListQuery"` — the full AST is embedded as a JavaScript object literal.

**Variables:**

| Variable | Type | Description |
|---|---|---|
| `slug` | `String!` | Category slug (e.g. `ai-meeting-notetakers`) |
| `order` | `CategoryProductsOrder!` | Sort order (see valid values below) |
| `page` | `Int` | Page number (1-based) |
| `pageSize` | `Int!` | Items per page (max ~20 with `featuredOnly: true`) |
| `featuredOnly` | `Boolean` | Default `true` — only show products with at least 1 PH launch |
| `tags` | `[String!]` | Optional tag filter |

**Valid `order` values:**
```
most_recent       – chronological, newest first
most_followed     – by follower count
best_rated        – by review rating (used in scraper.py)
recent_launches   – recent PH launch activity
highest_rated     – by aggregate rating
trending          – trending score
top_free          – free products ranked by usage
experiment        – A/B experiment variant
```

**Key response fields per product:**

```json
{
  "id": "471885",
  "name": "Fathom",
  "slug": "fathom",
  "tagline": "Never take notes again",
  "logoUuid": "1d94b262-dcbf-444d-b187-f25fabb01d54.jpeg",
  "reviewsRating": 4.96,
  "reviewsCount": 284,
  "detailedReviewsCount": 284,
  "followersCount": 1865,
  "postsCount": 2,
  "isTopProduct": false,
  "isNoLongerOnline": false,
  "structuredData": { "@type": "WebApplication", "url": "...", "description": "..." },
  "categories": [{ "id": "...", "name": "...", "slug": "...", "path": "..." }],
  "tags": ["productivity", "artificial intelligence", ...],
  "badges": { "edges": [{ "node": { /* GoldenKitty / TopPost badge */ } }] },
  "founderShoutouts": [ /* shoutout reviews from other founders */ ]
}
```

**Pagination via `pageInfo`:**
```json
"pageInfo": { "hasNextPage": true, "endCursor": "..." }
```

---

## 4. The APQ (Automatic Persisted Queries) Challenge

### What APQ is

Apollo Client computes a SHA-256 hash of the full printed query document and sends it in `extensions.persistedQuery.sha256Hash`. The server looks up the query by hash. If found → execute it. If not → return `{"errors": [{"message": "PersistedQueryNotFound"}]}`.

### Why the known hash didn't match

The server's stored hash for `CategoryPageListQuery` was pre-computed at build time from the source `.graphql` file (before compilation). The hash I computed from the bundle's AST representation produced a different result because:
- The printed query format (`graphql-js print()`) may differ slightly from the source
- Fragment ordering may differ
- The server may have stored the hash from a different build version

### The Breakthrough

The server **also accepts POST requests** that include both the query text AND the hash in extensions (standard APQ registration):

```python
payload = {
    "operationName": "CategoryPageListQuery",
    "variables": { ... },
    "query": "<full query text>",                      # ← full GQL text
    "extensions": {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": "<sha256 of query text>"     # ← self-computed hash
        }
    }
}
response = session.post("https://www.producthunt.com/frontend/graphql", json=payload)
```

**This registers the query on the server** and returns data immediately. The server validates the hash matches the query text, then executes it. Subsequent GET requests with the same hash also work (the query is now cached server-side).

### What does NOT work

| Attempt | Result |
|---|---|
| GET with wrong hash | `{"errors": [{"message": "PersistedQueryNotFound"}]}` |
| POST with query but NO hash | `{"errors": [{"message": "This request could not be processed"}]}` |
| POST with custom ad-hoc query (not from bundle) | `{"errors": [{"message": "This request could not be processed"}]}` |
| HTML scraping of category pages | No product data (CSR only) |
| Playwright headless (without valid cf_clearance) | Cloudflare challenge blocks navigation |

**Key rule:** The query text must be a **real query that exists in the ProductHunt JS bundle**. The server validates that the submitted query matches the expected structure. You cannot invent new queries.

---

## 5. Extracting Queries from the JS Bundle

When you need a query whose persisted hash is unknown, extract it from the bundle:

### Step 1 — Find the bundle file

Search all `/_next/static/chunks/*.js` files for the operation name string:

```python
async with session.get(chunk_url) as r:
    text = await r.text()
if "CategoryPageListQuery" in text:
    print(f"Found in: {chunk_url}")
```

The query AST will be embedded as a minified JS object literal:
```js
{kind:"Document",definitions:[{kind:"OperationDefinition",operation:"query",
  name:{kind:"Name",value:"CategoryPageListQuery"},...}]}
```

**Current bundle containing category queries:** `8c49b1d4ec0e985b.js`
(Bundle names change on each deployment — always search dynamically.)

### Step 2 — Extract and print to GraphQL format

```js
// Node.js — requires: npm install graphql
const { print } = require('graphql');
const crypto = require('crypto');

// Extract the {kind:"Document"...} object from bundle text
// (brace-counting extraction — see scripts/extract_hash2.js)
const doc = eval('(' + docStr.replace(/!0/g, 'true').replace(/!1/g, 'false') + ')');
const queryText = print(doc);
const hash = crypto.createHash('sha256').update(queryText).digest('hex');
```

The extracted queries are saved to `scripts/category_page_list_query.graphql`.

### Step 3 — Use in requests

```python
import hashlib

query_text = open("scripts/category_page_list_query.graphql").read()
query_hash = hashlib.sha256(query_text.encode()).hexdigest()

payload = {
    "operationName": "CategoryPageListQuery",
    "variables": { ... },
    "query": query_text,
    "extensions": {"persistedQuery": {"version": 1, "sha256Hash": query_hash}},
}
response = session.post(GRAPHQL_URL, json=payload, headers=headers)
```

---

## 6. Other Queries in the Bundle

The file `8c49b1d4ec0e985b.js` contains these operations (in addition to `CategoryPageListQuery`):

| Operation | Purpose |
|---|---|
| `CategoryPageQuery` | Category page metadata + 6 hero products |
| `CategoryRelatedProductsQuery` | Related/alternative products for a category |
| `ModerationProductSearchQuery` | Internal moderation tool (admin only, likely) |
| `CategoryPageListQuery` | **Paginated ranked product list ← main scraping query** |

---

## 7. Categories Page Scraping

The `/categories` page returns HTML with `<a href="/categories/{slug}">` links. This works with session cookies:

```python
async with session.get("https://www.producthunt.com/categories", headers=headers) as resp:
    html = await resp.text()

soup = BeautifulSoup(html, "html.parser")
for a in soup.find_all("a", href=True):
    href = a["href"]
    if href.startswith("/categories/"):
        slug = href.removeprefix("/categories/").split("?")[0].strip("/")
        name = a.get_text(separator=" ", strip=True)
```

**Result:** 248 categories as of March 2026.

---

## 8. Request Headers

Required headers to avoid 403/blocks:

```python
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "x-ph-timezone": "Asia/Baku",
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://www.producthunt.com/categories/{slug}",
    "x-ph-referer": "https://www.producthunt.com/categories/{slug}",
}
```

The `referer` and `x-ph-referer` headers should match the category being scraped. For page > 1, append `?page={page}`.

---

## 9. Rate Limiting & Performance

- **No hard rate limits observed** at concurrency=5 with 50ms page delay
- The API handles ~5 concurrent POST requests without errors
- Larger categories (productivity, engineering-development, design-creative) have 200+ pages
- Expected full scrape time: ~15–30 minutes for all 248 categories

**Async architecture:**
```python
semaphore = asyncio.Semaphore(5)        # max 5 categories in parallel
out_lock  = asyncio.Lock()              # protect shared output list
tasks = [scrape_category(session, cat, ...) for cat in categories]
await asyncio.gather(*tasks)            # all categories concurrently
```

---

## 10. Data Output

### `data/categories.csv`
| Column | Description |
|---|---|
| `name` | Display name (e.g. "AI notetakers") |
| `slug` | URL slug (e.g. `ai-meeting-notetakers`) |
| `url` | Full URL |

### `data/products.csv`
| Column | Description |
|---|---|
| `category_name` | Parent category display name |
| `category_slug` | Parent category slug |
| `id` | ProductHunt internal product ID |
| `name` | Product name |
| `tagline` | Short description |
| `slug` | Product slug (for URL: `/products/{slug}`) |
| `url` | Full ProductHunt product URL |
| `logo_url` | `https://ph-files.imgix.net/{logoUuid}?auto=format` |
| `reviews_rating` | Average review rating (0–5) |
| `reviews_count` | Total reviews |
| `detailed_reviews_count` | Detailed text reviews count |
| `followers_count` | Product followers |
| `posts_count` | Number of PH launches |
| `is_top_product` | Boolean — marked as top product |
| `is_no_longer_online` | Boolean — product discontinued |
| `website` | Official website URL (from structured data) |

---

## 11. Common Failure Modes & Fixes

| Symptom | Cause | Fix |
|---|---|---|
| HTTP 403 on `/categories` | Expired `cf_clearance` | Refresh cookies from browser |
| `PersistedQueryNotFound` | Using GET with an unregistered hash | Switch to POST with `query` + `extensions` |
| `This request could not be processed` | POST without hash, or invented query | Must include `extensions.persistedQuery` AND real query text from bundle |
| `Variable $order provided invalid value` | Wrong enum value for `order` | Use: `most_recent`, `best_rated`, `most_followed`, etc. |
| Empty `products.edges` | `featuredOnly: true` + no launched products | Try `featuredOnly: false` |
| Products stop at page 1 | `hasNextPage: false` | Category has fewer than `pageSize` products (normal) |
| Cloudflare challenge in Playwright | Missing `cf_clearance` in browser context | Inject cookies before navigation, or use `--no-sandbox` flags |

---

## 12. Re-running / Maintenance

When ProductHunt deploys a new version:
1. JS bundle filenames change → re-run the bundle search to find the new file containing `CategoryPageListQuery`
2. The query AST might gain new fields → re-extract with `node scripts/extract_hash2.js`
3. New hash is auto-computed — no manual work needed
4. Refresh browser cookies if `cf_clearance` expired

**Scripts (in `scripts/`):**
- `scraper.py` — main scraper (categories + products)
- `extract_hash2.js` — re-extracts `CategoryPageListQuery` from a downloaded bundle when PH deploys a new version
- `category_page_list_query.graphql` — extracted canonical query text (read by `scraper.py` at runtime)
- `package.json` / `package-lock.json` — Node deps for `extract_hash2.js` (`graphql` package)
