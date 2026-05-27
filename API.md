# Website Parsing Service — API Reference

FastAPI service for scraping websites (Crawl4AI) and social profiles (Bright Data), with RAG-ready chunk output.

**Default base URL:** `http://localhost:8000` (see `start.sh` / `PORT` env)

**CORS:** All origins, methods, and headers allowed.  (will change later)

---

## Conventions

### Request parameters

Scrape and crawl endpoints take parameters as **query strings**, not JSON bodies.

```http
POST /crawl?url=https://example.com
```

Process endpoints take a **JSON body** (see `/process/page` and `/process/social` below).

### Errors

Failed requests return FastAPI’s standard shape:

```json
{ "detail": "error message" }
```

| Status | Meaning |
|--------|---------|
| `400` | Missing or invalid input |
| `502` | Scrape or normalization failed (upstream / no content) |
| `500` | Unexpected server error |

---

## Shared types

Scrape endpoints return **input payloads** (paste directly into `/process/*`). Process endpoints return **results with chunks**.

### `Chunk`

Returned only by `/process/page` and `/process/social`. Text is split with chunk size **512** and overlap **50** (see `chunking.py`).

```ts
type Chunk = {
  text: string;
  metadata: {
    source_url: string;
    content_type: string; // "web_page" | "linkedin_record" | "instagram_record" | "facebook_record"
    chunk_index: number;
    // optional — depends on endpoint / record:
    title?: string;
    language?: string;
    description?: string;
    site_seed_url?: string;
    platform?: string;
    record_type?: string;
    parent_field?: string;
    parent_index?: number;
    post_index?: number;
    urn?: string;
  };
};
```

### `CrawlPagePayload`

Returned by `/crawl*` endpoints. Same shape as the `/process/page` request body — paste as-is to get chunks.

```ts
type CrawlPagePayload = {
  markdown: string;
  url: string;
  title?: string;
  language?: string;
  description?: string;
  site_seed_url?: string;  // set on site crawl routes only
};
```

### `PageResult`

Returned by `/process/page` only.

```ts
type PageResult = {
  url: string;       // page URL from scrape metadata
  markdown: string;  // full page markdown
  metadata: {
    title?: string;
    language?: string;
    description?: string;
  };
  chunks: Chunk[];   // metadata.content_type === "web_page"
};
```

When `site_seed_url` was provided to `/process/page`, each chunk includes `metadata.site_seed_url`.

### `SocialScrapePayload`

Returned by `/linkedin`, `/instagram`, and `/facebook`. Same shape as the `/process/social` request body — paste as-is to get chunks.

```ts
type SocialScrapePayload = {
  platform: "linkedin" | "instagram" | "facebook";
  scraper_type: string;   // Bright Data scraper used (e.g. "profiles", "posts")
  request_url: string;
  raw: object | object[]; // Bright Data payload (opaque)
};
```

### `SocialResult`

Returned by `/process/social` only.

```ts
type SocialResult = {
  url: string;
  platform: "linkedin" | "instagram" | "facebook";
  scraper_type: string;
  record_type: string;              // primary type for this scrape (see table below)
  metadata: { title?: string };     // often {}; title when derivable from primary record
  raw: object | object[];
  chunks: Chunk[];                  // metadata.content_type === "{platform}_record"
};
```

Per-chunk `metadata.record_type` may be more granular than top-level `record_type` (e.g. LinkedIn profile scrape yields `profile`, `experience`, `education`, `post` chunks).

---

## Endpoints

### `GET /`

Health check.

**Response `200`:**

```json
{ "status": "ok" }
```

---

### `POST /crawl`

Scrape a single URL to markdown (Crawl4AI / headless Chromium).

| Query param | Required | Description |
|-------------|----------|-------------|
| `url` | yes | Page URL to scrape |

**Response `200`:** `CrawlPagePayload` (no `chunks` — call `/process/page` to chunk)

**Errors:** `400` empty `url`; `502` no markdown or scrape failure; `500` other.

**Round-trip:**

```http
POST /crawl?url=https://example.com
→ copy JSON body as-is →
POST /process/page
Content-Type: application/json
→ PageResult with chunks
```

---

### `POST /crawl/site`

Crawl a site (up to **100** pages, max discovery depth **2**).

| Query param | Required | Description |
|-------------|----------|-------------|
| `url` | yes | Site seed URL |

**Response `200`:** `CrawlPagePayload[]` — one entry per successfully crawled page. Each payload includes `site_seed_url` set to the seed `url`.

**Errors:** `400` empty `url`; `502` / `500` if the crawl fails entirely (no partial wrapper).

---

### `POST /crawl/site/partial`

Same crawl as `/crawl/site`, but failed pages are reported in `failures` instead of failing the whole request. A top-level crawl error may still return partial data.

| Query param | Required | Description |
|-------------|----------|-------------|
| `url` | yes | Site seed URL |

**Response `200`:**

```ts
type PartialCrawlResult = {
  partial: boolean;       // true if top-level error with partial data
  site_seed_url: string;
  pages: CrawlPagePayload[];
  failures: Array<{ url: string; error: string }>;
  error?: string;         // present when crawl threw but pages/failures were collected
};
```

**Errors:** `500` only when the crawl fails and both `pages` and `failures` are empty.

---

### `POST /linkedin`

### `POST /instagram`

### `POST /facebook`

Scrape a social URL via Bright Data. Returns raw payload for `/process/social` — no chunks.

| Query param | Required | Description |
|-------------|----------|-------------|
| `url` | yes | Profile, company, post, or other supported URL for that platform |

**Response `200`:** `SocialScrapePayload`

**Errors:** `400` empty `url`; `502` unsupported URL or Bright Data failure; `500` other.

#### Top-level `record_type` by URL (inferred by `/process/social`, not returned by scrape)

| Platform | URL pattern (simplified) | `record_type` |
|----------|--------------------------|---------------|
| LinkedIn | `/in/`, `/pub/` | `profile` |
| LinkedIn | `/company/` | `company` |
| LinkedIn | `/jobs/view`, `/jobs/...` (not search) | `job` |
| LinkedIn | feed / post URLs | `post` |
| Instagram | single path segment (username) | `profile` |
| Instagram | `/p/` | `post` |
| Instagram | `/reel/`, `/reels/` | `reel` |
| Facebook | profile (default) | `post` |
| Facebook | `/groups/` | `post` |
| Facebook | `/posts/`, `/permalink/`, etc. | `post` |
| Facebook | `/reel` | `reel` |

Unsupported URLs return `502` with a message like `Unsupported LinkedIn URL: ...`.

#### Example scrape response (LinkedIn profile)

```json
{
  "platform": "linkedin",
  "scraper_type": "profiles",
  "request_url": "https://www.linkedin.com/in/jane-doe",
  "raw": { }
}
```

Paste into `/process/social` to get `SocialResult` with `record_type`, `metadata`, and `chunks`.

---

### `POST /process/page`

Split markdown into RAG-ready chunks without scraping. Accepts a JSON body.

**Request body:**

```json
{
  "markdown": "# Hello\n\nWorld",
  "url": "https://example.com/page",
  "title": "Example Page",
  "language": "en",
  "description": "A test page",
  "site_seed_url": "https://example.com"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `markdown` | yes | Page markdown or plain text |
| `url` | yes | Source page URL (stored in chunk metadata) |
| `title` | no | Page title |
| `language` | no | Page language |
| `description` | no | Page description |
| `site_seed_url` | no | Site crawl seed URL (added to chunk metadata when set) |

**Response `200`:** `PageResult`

**Errors:** `422` invalid or empty body; `502` empty markdown after strip; `500` other.

---

### `POST /process/social`

Normalize a Bright Data social payload into RAG-ready chunks without scraping. Accepts a JSON body.

**Request body:**

```json
{
  "platform": "linkedin",
  "scraper_type": "profiles",
  "request_url": "https://www.linkedin.com/in/jane-doe",
  "raw": { }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `platform` | yes | `"linkedin"`, `"instagram"`, or `"facebook"` |
| `scraper_type` | yes | Bright Data scraper type (e.g. `"profiles"`, `"posts"`, `"posts_by_profile"`) |
| `request_url` | yes | Original URL that was scraped |
| `raw` | yes | Bright Data JSON payload (object or array) |

**Response `200`:** `SocialResult`

**Errors:** `422` invalid body; `502` no extractable content; `500` other.

Use `scraper_type` from a prior social scrape response to round-trip stored `raw` payloads through this endpoint.

#### Example process response (LinkedIn profile)

```json
{
  "url": "https://www.linkedin.com/in/jane-doe",
  "platform": "linkedin",
  "scraper_type": "profiles",
  "record_type": "profile",
  "metadata": { "title": "Jane Doe" },
  "raw": { },
  "chunks": [
    {
      "text": "name: Jane Doe\nheadline: ...",
      "metadata": {
        "source_url": "https://www.linkedin.com/in/jane-doe",
        "content_type": "linkedin_record",
        "chunk_index": 0,
        "platform": "linkedin",
        "record_type": "profile"
      }
    }
  ]
}
```

---

## Breaking change

Scrape endpoints (`/crawl*`, `/linkedin`, `/instagram`, `/facebook`) no longer return `chunks`. Clients that read chunks directly from scrape responses must call `/process/page` or `/process/social` instead. Scrape output is now the exact JSON body accepted by the corresponding process endpoint.

---

## Client integration notes

1. **Use query params on scrape POST** — e.g. `fetch(\`${base}/crawl?url=${encodeURIComponent(url)}\`, { method: 'POST' })`.
2. **Use JSON bodies on process POST** — e.g. `fetch(\`${base}/process/page\`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(crawlPayload) })`.
3. **Prefer `chunks` for RAG** — call `/process/*` to get chunks; each chunk is self-contained with `source_url` and indexing metadata for vector stores.
4. **Use `markdown` / `raw` for display** — scrape responses include full page markdown or upstream JSON when you need the complete source.
5. **Two-step pipeline** — scrape once (response is paste-ready for `/process/*`), store the payload, then call `/process/page` or `/process/social` later without re-scraping.
6. **Partial site crawl** — check `partial`, `failures`, and optional `error`; do not assume every discovered page appears in `pages`.
7. **Timeouts** — crawls and social scrapes can take a long time; set generous client timeouts and loading states.

---

## Environment

| Variable | Required | Purpose |
|----------|----------|---------|
| `BRIGHTDATA_API_TOKEN` | yes (social) | Bright Data API token |
| `PORT` | no | Server port (default `8000`) |
| `PLAYWRIGHT_BROWSERS_PATH` | no | Directory for Chromium binaries (set in Docker / `build.sh`) |

Web crawl endpoints use local [Crawl4AI](https://github.com/unclecode/crawl4ai) with Playwright — no API key required. Run `build.sh` or the Docker build step to install Chromium before starting the server.
