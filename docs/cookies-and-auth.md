# ProductHunt Authentication & Cookie Management

## Cookie Overview

ProductHunt uses a layered auth system with cookies that serve different purposes and have different lifetimes.

| Cookie | Lifetime | Purpose | Required |
|---|---|---|---|
| `cf_clearance` | ~24–48h | Cloudflare bot challenge proof | YES |
| `_producthunt_session_production` | ~3–6 months | Rails app session | YES |
| `csrf_token` | Session | CSRF protection for POST | YES (for POST) |
| `visitor_id` | Persistent | Analytics / anonymous tracking | Soft |
| `ajs_anonymous_id` | Persistent | Segment.io tracking | No |
| `_ga`, `_ga_*` | 2 years | Google Analytics | No |
| `first_visit` | Persistent | Timestamp of first visit | No |
| `track_code` | Persistent | Attribution tracking | No |

---

## Obtaining Cookies

### Method 1 — Browser DevTools (manual, reliable)

1. Log in (or not) to `producthunt.com` in Chrome
2. Open DevTools → Application tab → Cookies → `www.producthunt.com`
3. Copy all cookie values, or use the Network tab to copy a request as cURL and extract the `Cookie:` header
4. Paste the full cookie string into `COOKIE_STR` in `scripts/scraper.py`

### Method 2 — Copy as cURL from Network tab

1. Go to `producthunt.com/categories`
2. Open DevTools → Network tab
3. Find any `graphql` request → right-click → "Copy as cURL"
4. Extract the `-H 'cookie: ...'` value

---

## Cookie Lifetime & Refresh Strategy

### `cf_clearance` — Most Volatile

Cloudflare clearance tokens expire in ~24–48 hours. When expired:
- HTML pages return 403
- The GraphQL API may still work (it's a different path) but category page HTML scraping will fail

**Symptom:** Step 1 (fetching `/categories`) fails with HTTP 403.

**Fix:** Visit `producthunt.com` in a browser (may get a challenge page), solve it, then copy the fresh `cf_clearance` cookie.

### `_producthunt_session_production` — Long-lived

This is a Rails session cookie. It typically lasts 3–6 months without activity. If it expires:
- All requests return empty data or redirect to login

**Symptom:** GraphQL requests return `{"data": {"productCategory": null}}` or viewer-related errors.

**Fix:** Log into ProductHunt in a browser and copy the new session cookie.

### `csrf_token` — Required for POST

POST requests to the GraphQL endpoint require this token. It's validated server-side.

**Symptom:** POST requests return `{"errors": [{"message": "This request could not be processed"}]}` even with correct query.

**Fix:** Copy the fresh `csrf_token` from the browser. It rotates infrequently but can change.

---

## Parsing Cookies in Python

```python
def parse_cookie_str(cookie_str: str) -> dict:
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies

# Usage
cookies = parse_cookie_str(COOKIE_STR)
async with aiohttp.ClientSession(cookies=cookies) as session:
    ...
```

Note: `aiohttp` handles URL-encoding of cookie values automatically.

---

## Headers That Matter for Auth

Beyond cookies, these headers signal "real browser" behavior:

```python
headers = {
    # Required — signals origin
    "referer":         "https://www.producthunt.com/categories/ai-meeting-notetakers",
    "x-ph-referer":    "https://www.producthunt.com/categories/ai-meeting-notetakers",
    # Identifies as XHR (not page load)
    "x-requested-with": "XMLHttpRequest",
    # ProductHunt timezone header — match your session timezone
    "x-ph-timezone":   "Asia/Baku",
    # Standard browser security headers
    "sec-fetch-dest":  "empty",
    "sec-fetch-mode":  "cors",
    "sec-fetch-site":  "same-origin",
}
```

`x-ph-referer` appears to be a ProductHunt-specific header that mirrors the `referer`. Always set it to the page URL being scraped.

---

## Handling Auth Failures

```python
async def gql_category_page(session, slug, page, query_text, query_hash):
    ...
    async with session.post(GRAPHQL_URL, json=payload, headers=headers) as resp:
        data = await resp.json(content_type=None)

    # Detect auth failure
    errors = data.get("errors", [])
    if errors:
        msg = errors[0].get("message", "")
        if "PersistedQueryNotFound" in msg:
            raise RuntimeError("Query not registered — re-run APQ registration")
        if "This request could not be processed" in msg:
            raise RuntimeError("Bad request — check CSRF token or query format")

    # Detect session expiry
    cat = data.get("data", {}).get("productCategory")
    if cat is None:
        raise RuntimeError(f"Null response for {slug} — session may be expired")
```

---

## Cloudflare & Bot Detection Notes

ProductHunt uses Cloudflare with these protections observed:
- **Browser Integrity Check** — HTML pages require valid browser fingerprint
- **Bot Fight Mode** — headless Playwright fails without valid `cf_clearance`

**What works without a browser:**
- GraphQL API calls with valid session cookies — no Cloudflare challenge on API endpoint
- `/categories` HTML page — requires `cf_clearance`

**What requires Playwright or a real browser:**
- Initial `cf_clearance` acquisition
- Pages with heavy JS challenges

**Playwright workaround for cf_clearance:**
```js
const context = await browser.newContext({
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    viewport: { width: 1920, height: 1080 },
    locale: "en-US",
});
// Pre-inject existing cookies first, then navigate
await context.addCookies(existingCookies);
await page.goto("https://www.producthunt.com/");
// After page loads, extract new cf_clearance
const cookies = await context.cookies();
const cfClearance = cookies.find(c => c.name === "cf_clearance");
```
