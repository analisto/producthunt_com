# Bypassing Apollo Persisted Queries (APQ) on ProductHunt

## The Problem

ProductHunt uses Apollo's **Automatic Persisted Queries (APQ)**. This means:

1. Every GraphQL request sends only a **hash** (not the full query text)
2. The server looks up the query by hash and executes it
3. If you send an **unknown or incorrect hash** → `{"errors": [{"message": "PersistedQueryNotFound"}]}`
4. You **cannot** POST arbitrary queries → `{"errors": [{"message": "This request could not be processed"}]}`

This makes scraping hard because:
- You need the exact hash for each query
- Hashes are not stored in the JS bundle as readable strings
- The hash computed from the printed query AST doesn't match the server's stored hash (different build-time serialization)

---

## The Solution: APQ Registration via POST

The standard APQ protocol allows clients to **register a new query** by sending both the query text and the hash together. ProductHunt's server supports this.

### How it works

```
Client → POST /frontend/graphql
  body: {
    operationName: "CategoryPageListQuery",
    variables: { ... },
    query: "<full GraphQL query text>",         ← include the query
    extensions: {
      persistedQuery: {
        version: 1,
        sha256Hash: "<sha256 of the query text>" ← must match
      }
    }
  }

Server → validates hash matches query → executes → returns data
Server → caches query by hash for future GET requests
```

**Key rules:**
1. `sha256Hash` must be `SHA-256(query_text_utf8)` — must match exactly
2. The `query` must be a **real query from the ProductHunt JS bundle** — invented queries are rejected
3. This works because `query + hash` proves you know the legitimate query structure

### Python implementation

```python
import hashlib
from pathlib import Path

def load_query(path: str) -> tuple[str, str]:
    """Returns (query_text, sha256_hash)."""
    text = Path(path).read_text(encoding="utf-8")
    h    = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text, h

query_text, query_hash = load_query("scripts/category_page_list_query.graphql")

payload = {
    "operationName": "CategoryPageListQuery",
    "variables": {
        "slug":        "ai-meeting-notetakers",
        "order":       "best_rated",
        "page":        1,
        "pageSize":    20,
        "featuredOnly": True,
    },
    "query":      query_text,
    "extensions": {"persistedQuery": {"version": 1, "sha256Hash": query_hash}},
}

async with session.post(GRAPHQL_URL, json=payload, headers=headers) as resp:
    data = await resp.json(content_type=None)
```

---

## Extracting Query Text from the JS Bundle

Since the query text must come from the bundle, here is the extraction process:

### Step 1 — Find the bundle file

```python
# Search all JS chunks for the operation name
chunk_urls = [...]  # extracted from page HTML

async with session.get(chunk_url) as r:
    text = await r.text()

if '"CategoryPageListQuery"' in text:
    print(f"Found in: {chunk_url}")
    # Bundle: /_next/static/chunks/8c49b1d4ec0e985b.js (as of March 2026)
```

### Step 2 — Extract the AST object

The query is embedded as a minified JS object:
```js
{kind:"Document",definitions:[{kind:"OperationDefinition",...}]}
```

Extract by counting braces:
```js
// scripts/extract_hash2.js
const { print } = require('graphql');   // npm install graphql
const crypto = require('crypto');

const bundle = fs.readFileSync('scripts/debug_bundle.js', 'utf-8');
const idx = bundle.indexOf('"CategoryPageListQuery"');
const docStart = bundle.lastIndexOf('{kind:"Document"', idx);

// Brace-counting extraction
let depth = 0, end = docStart, inStr = false, strChar = '';
for (let i = docStart; i < bundle.length; i++) {
    const c = bundle[i];
    if (inStr) {
        if (c === strChar && bundle[i-1] !== '\\') inStr = false;
    } else if (c === '"' || c === "'") {
        inStr = true; strChar = c;
    } else if (c === '{') depth++;
    else if (c === '}') {
        depth--;
        if (depth === 0) { end = i; break; }
    }
}

const docStr = bundle.slice(docStart, end + 1);
const doc = eval('(' + docStr.replace(/!0/g, 'true').replace(/!1/g, 'false') + ')');
```

### Step 3 — Print and hash

```js
const queryText = print(doc);   // graphql-js canonical format
const hash = crypto.createHash('sha256').update(queryText).digest('hex');

fs.writeFileSync('scripts/category_page_list_query.graphql', queryText);
console.log('Hash:', hash);
```

---

## Why Computing the Hash Locally Doesn't Match the Server

The server stores a hash that was computed **at build time** from the `.graphql` source file. When I computed the hash from the bundle's printed AST, it didn't match because:

1. The build-time source file had different whitespace/formatting than `graphql-js print()` output
2. Fragment order in the source may differ from the bundle's evaluation order
3. The server may have cached a hash from an older build

**This is why the APQ registration approach is necessary** — instead of guessing the server's pre-stored hash, we register our own hash for the same query text.

---

## Alternative: Finding Hashes via Playwright

If the APQ registration doesn't work in future (server adds additional validation), use Playwright to capture real network requests:

```js
// scripts/capture_hash.js
const { chromium } = require('playwright');

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.addCookies(parsedCookies);

const page = await context.newPage();
page.on('request', req => {
    if (req.url().includes('/frontend/graphql')) {
        const url = new URL(req.url());
        const op   = url.searchParams.get('operationName');
        const ext  = JSON.parse(url.searchParams.get('extensions') || '{}');
        const hash = ext?.persistedQuery?.sha256Hash;
        console.log(`${op}: ${hash}`);
    }
});

await page.goto('https://www.producthunt.com/categories/ai-meeting-notetakers',
    { waitUntil: 'networkidle' });
```

**Requires:** valid `cf_clearance` cookie (Cloudflare clearance) in the browser context.

---

## Summary Decision Tree

```
Need to call a ProductHunt GraphQL query?
│
├─ Do you have the exact server-side hash?
│   ├─ YES → Use GET request with hash in extensions
│   └─ NO → Continue below
│
├─ Can you find the query in the JS bundle?
│   ├─ YES → Extract AST → print → compute hash → POST with query+hash
│   └─ NO → Use Playwright to capture the real network request
│
└─ Does the server reject your POST?
    ├─ "This request could not be processed" → query not from bundle, cannot proceed
    └─ "Variable X invalid value" → fix the variable value (check enum types)
```
