# ProductHunt GraphQL API Reference

## Endpoint

```
POST https://www.producthunt.com/frontend/graphql
GET  https://www.producthunt.com/frontend/graphql   (persisted queries only)
```

## Authentication

All requests require session cookies. Include them via `aiohttp.ClientSession(cookies=...)`.

Minimum required cookies:
- `cf_clearance`
- `_producthunt_session_production`
- `csrf_token`
- `visitor_id`

---

## CategoryPageListQuery

The primary query for scraping ranked products within a category.

**File:** `scripts/category_page_list_query.graphql`
**Hash method:** `SHA-256(print(document))` using graphql-js canonical format
**How to call:** POST with `query` + `extensions.persistedQuery` (see below)

### Variables

```graphql
query CategoryPageListQuery(
  $slug: String!
  $order: CategoryProductsOrder!
  $page: Int
  $pageSize: Int!
  $featuredOnly: Boolean = true
  $tags: [String!]
)
```

### Valid `CategoryProductsOrder` values

| Value | Description |
|---|---|
| `best_rated` | Highest average review rating |
| `most_followed` | Most product followers |
| `most_recent` | Newest products first |
| `recent_launches` | Most recent PH launch activity |
| `highest_rated` | Aggregate rating score |
| `trending` | Current trending score |
| `top_free` | Free products by usage |
| `experiment` | A/B variant (avoid) |

### Pagination

- `page` is **1-based** integer
- `pageSize` max effective value is **~20** when `featuredOnly: true`
- Stop when `products.pageInfo.hasNextPage === false`

### Example call (Python)

```python
import hashlib, aiohttp, json
from pathlib import Path

query_text = Path("scripts/category_page_list_query.graphql").read_text(encoding="utf-8")
query_hash = hashlib.sha256(query_text.encode()).hexdigest()

payload = {
    "operationName": "CategoryPageListQuery",
    "variables": {
        "slug": "ai-meeting-notetakers",
        "order": "best_rated",
        "page": 1,
        "pageSize": 20,
        "featuredOnly": True,
    },
    "query": query_text,
    "extensions": {
        "persistedQuery": {"version": 1, "sha256Hash": query_hash}
    },
}

async with session.post(
    "https://www.producthunt.com/frontend/graphql",
    json=payload,
    headers=headers,
) as resp:
    data = await resp.json(content_type=None)
```

### Response shape

```json
{
  "data": {
    "productCategory": {
      "id": "1288",
      "name": "AI notetakers",
      "slug": "ai-meeting-notetakers",
      "path": "/categories/ai-meeting-notetakers",
      "description": "...",
      "aiSummary": null,
      "categoryTags": [
        { "name": "productivity", "count": 87 },
        { "name": "artificial intelligence", "count": 84 }
      ],
      "snapshot": { "lastUpdatedAt": "2026-03-06T08:13:58-08:00" },
      "products": {
        "totalCount": 114,
        "pageInfo": {
          "hasNextPage": true,
          "endCursor": "..."
        },
        "edges": [
          {
            "node": {
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
              "founderReviewsCount": 36,
              "latestLaunch": {
                "id": "380138",
                "scheduledAt": "2023-02-22T00:01:00-08:00"
              },
              "categories": [
                {
                  "id": "431",
                  "name": "Meeting software",
                  "slug": "meetings",
                  "path": "/categories/meetings"
                }
              ],
              "tags": ["real-time transcription", "meeting recording", ...],
              "embeddingSummary": null,
              "badges": {
                "edges": [
                  {
                    "node": {
                      "id": "848923",
                      "category": "AI & machine learning",
                      "position": 2,
                      "year": "2021",
                      "post": { "id": "...", "slug": "...", "name": "..." }
                    }
                  }
                ]
              },
              "founderShoutouts": [
                {
                  "id": "299962",
                  "fromPost": { "id": "...", "slug": "...", "name": "..." }
                }
              ],
              "structuredData": {
                "@context": "http://schema.org",
                "@type": ["WebApplication", "Product"],
                "url": "https://www.producthunt.com/products/fathom",
                "name": "Fathom",
                "description": "Full product description...",
                "datePublished": "2022-04-14T...",
                "dateModified": "2026-03-06T...",
                "image": "https://ph-files.imgix.net/...jpeg?auto=format",
                "screenshot": ["https://ph-files.imgix.net/..."],
                "aggregateRating": {
                  "@type": "AggregateRating",
                  "ratingCount": 284,
                  "ratingValue": "4.96"
                },
                "offers": { "@type": "Offer", "price": 0, "priceCurrency": "USD" }
              }
            }
          }
        ]
      }
    }
  }
}
```

---

## CategoryPageQuery

Used to load category page metadata. **Does NOT return paginated product lists.**

```
GET /frontend/graphql
  ?operationName=CategoryPageQuery
  &variables={"slug":"...","path":"/categories/..."}
  &extensions={"persistedQuery":{"version":1,"sha256Hash":"eeaa942691c4ef61705f6147c8f0cc2e74beef7638f8c68fb2569fb30e020287"}}
```

Returns: category id, name, description, hero products (6 only), discussions, questions, subCategories, snapshot.

---

## URL Construction

| Resource | URL Pattern |
|---|---|
| Product page | `https://www.producthunt.com/products/{slug}` |
| Product logo | `https://ph-files.imgix.net/{logoUuid}?auto=format` |
| Product logo (thumbnail) | `https://ph-files.imgix.net/{logoUuid}?auto=format&w=100&h=100&fit=crop` |
| Category page | `https://www.producthunt.com/categories/{slug}` |
| Post page | `https://www.producthunt.com/posts/{post_slug}` |
| User avatar | `https://ph-avatars.imgix.net/{userId}/{uuid}.png?auto=format&w=100&h=100` |

---

## Known Schema Types

### `ProductCategory`
- `id`, `name`, `slug`, `path`, `description`, `expandableHtml`
- `snapshot` → `{ reviewsCount, lastUpdatedAt }`
- `heroProducts(page)` → connection of Product (6 items)
- `recentLaunches` → connection of Product (totalCount only in CategoryPageQuery hash)
- `products(page, first, order, onlyHasFeaturedPosts, liveOnly, tags)` → full paginated connection
- `categoryTags(onlyHasFeaturedPosts, includeTags)` → `[{ name, count }]`
- `subCategories` → nested ProductCategory connection
- `parent` → parent ProductCategory

### `Product`
- `id`, `name`, `slug`, `tagline`, `logoUuid`
- `reviewsRating` (Float), `reviewsCount`, `detailedReviewsCount`, `founderReviewsCount`
- `followersCount`, `postsCount`, `isSubscribed`, `isTopProduct`, `isNoLongerOnline`
- `badges` → connection of `TopPostBadge | GoldenKittyAwardBadge | OrbitAwardBadge`
- `categories` → `[ProductCategory]`
- `tags` → `[String]`
- `founderShoutouts(first)` → `[DetailedReview]`
- `structuredData` → JSON-LD schema.org object
- `embeddingSummary` → AI-generated summary (nullable)
- `latestLaunch` → `{ id, scheduledAt }`
