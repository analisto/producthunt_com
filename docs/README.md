# ProductHunt Scraper — Documentation Index

## Quick Start

```bash
# Step 1: Install dependencies
pip install aiohttp beautifulsoup4

# Step 2: Update COOKIE_STR in scripts/scraper.py with fresh browser cookies

# Step 3: Ensure the query file exists
node scripts/extract_hash2.js   # requires: cd scripts && npm install

# Step 4: Run
python scripts/scraper.py                  # full scrape (categories + products)
python scripts/scraper.py --categories-only  # categories only
```

**Output files:**
- `data/categories.csv` — 248 categories (name, slug, url)
- `data/products.csv` — all ranked products per category

---

## Documents

| File | What it covers |
|---|---|
| [scraping-producthunt.md](scraping-producthunt.md) | Full investigation writeup — architecture, findings, dead ends, what works |
| [graphql-api-reference.md](graphql-api-reference.md) | API reference for both GraphQL queries, full response schemas |
| [apq-bypass-technique.md](apq-bypass-technique.md) | How to bypass Apollo Persisted Queries — the core technical trick |
| [cookies-and-auth.md](cookies-and-auth.md) | Cookie management, auth flow, Cloudflare handling |

---

## Key Discoveries (TL;DR for future scrapers)

### 1. The visible network request is NOT the products query

`CategoryPageQuery` (visible in the network tab on category pages) returns only **6 hero products** and category metadata. It **cannot** be used for bulk product scraping.

The real query is `CategoryPageListQuery` — it fires client-side after hydration and is not easily visible unless you monitor all network requests.

### 2. POST with query text + self-computed hash works

ProductHunt uses APQ (Apollo Persisted Queries). Even though direct query POST is blocked, you can register any legitimate bundle query by sending:
```json
{ "query": "<text>", "extensions": { "persistedQuery": { "sha256Hash": "<sha256 of text>" } } }
```
The hash must equal `SHA-256(query_text_utf8)` and the query must come from the JS bundle.

### 3. Queries live in JS bundle as AST objects

All GraphQL query documents are embedded in the Next.js chunks as minified JS AST objects:
```js
{kind:"Document",definitions:[...]}
```
They can be extracted and converted to canonical GraphQL using `graphql-js print()`.

**Current bundle:** `/_next/static/chunks/8c49b1d4ec0e985b.js`
(Filename changes on deployment — always search dynamically.)

### 4. Valid order values for CategoryPageListQuery

```
best_rated | most_followed | most_recent | recent_launches
highest_rated | trending | top_free | experiment
```
The string `RANKING` (which looks plausible) is **invalid** and returns a variable error.

### 5. Pagination is page-based, not cursor-based

Despite `pageInfo.endCursor` being present in responses, `CategoryPageListQuery` uses integer `page` (1-based). Maximum ~20 items per page with `featuredOnly: true`.

---

## Maintenance Checklist

When the scraper stops working:

- [ ] **403 on /categories** → Refresh `cf_clearance` cookie
- [ ] **Null productCategory** → Refresh `_producthunt_session_production` cookie
- [ ] **PersistedQueryNotFound** → Bundle changed, re-run `node scripts/extract_hash2.js`
- [ ] **Variable invalid value** → Check enum values for `order` parameter
- [ ] **Empty products** → Try `featuredOnly: false` in scraper config
