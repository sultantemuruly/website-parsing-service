# Website Parsing Service — API Reference

FastAPI service for scraping websites (Crawl4AI) and social profiles (Bright Data), with RAG-ready chunk output.

**Default base URL:** `http://localhost:8000` (see `start.sh` / `PORT` env)

**CORS:** All origins, methods, and headers allowed.  (will change later)

---

## Conventions

### Request parameters

All `POST` endpoints take parameters as **query strings**, not JSON bodies.

```http
POST /crawl?url=https://example.com
POST /chunk?text=Hello%20world
```

### Errors

Failed requests return FastAPI’s standard shape:

```json
{ "detail": "error message" }
```

| Status | Meaning |
|--------|---------|
| `400` | Missing or invalid input (`url` / `text` required) |
| `502` | Scrape or normalization failed (upstream / no content) |
| `500` | Unexpected server error |

---

## Shared types

### `Chunk`

Used by crawl and social endpoints. Text is split with chunk size **512** and overlap **50** (see `chunking.py`).

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

### `PageResult`

Single crawled web page.

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

Site-wide crawl responses also set `metadata.site_seed_url` on each chunk to the seed URL passed to the endpoint.

### `SocialResult`

Normalized social scrape (LinkedIn, Instagram, Facebook).

```ts
type SocialResult = {
  url: string;
  platform: "linkedin" | "instagram" | "facebook";
  record_type: string;              // primary type for this scrape (see table below)
  metadata: { title?: string };     // often {}; title when derivable from primary record
  raw: object | object[];           // Bright Data payload (opaque)
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

**Response `200`:** `PageResult`

**Errors:** `400` empty `url`; `502` no markdown or scrape failure; `500` other.

---

### `POST /crawl/site`

Crawl a site (up to **100** pages, max discovery depth **2**).

| Query param | Required | Description |
|-------------|----------|-------------|
| `url` | yes | Site seed URL |

**Response `200`:** `PageResult[]` — one entry per successfully serialized page. Each chunk includes `metadata.site_seed_url` set to the seed `url`.

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
  partial: boolean;       // true if any page failed, or top-level error with partial data
  site_seed_url: string;
  pages: PageResult[];
  failures: Array<{ url: string; error: string }>;
  error?: string;         // present when crawl threw but pages/failures were collected
};
```

**Errors:** `500` only when the crawl fails and both `pages` and `failures` are empty.

---

### `POST /linkedin`

### `POST /instagram`

### `POST /facebook`

Scrape a social URL via Bright Data and return normalized chunks.

| Query param | Required | Description |
|-------------|----------|-------------|
| `url` | yes | Profile, company, post, or other supported URL for that platform |

**Response `200`:** `SocialResult`

**Errors:** `400` empty `url`; `502` unsupported URL, Bright Data failure, or no extractable content; `500` other.

#### Top-level `record_type` by URL (inferred server-side)

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

#### Example success shape (LinkedIn profile)

```json
{
  "url": "https://www.linkedin.com/in/jane-doe",
  "platform": "linkedin",
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

### `POST /chunk`

Split arbitrary markdown/text into chunks (no scraping).

| Query param | Required | Description |
|-------------|----------|-------------|
| `text` | yes | Markdown or plain text to chunk |

**Response `200`:** `string[]` — plain text segments only (not `Chunk` objects).

**Errors:** `400` empty or whitespace-only `text`; `500` on unexpected failure.

---

## Client integration notes

1. **Use query params on POST** — e.g. `fetch(\`${base}/crawl?url=${encodeURIComponent(url)}\`, { method: 'POST' })`.
2. **Prefer `chunks` for RAG** — each chunk is self-contained with `source_url` and indexing metadata for vector stores.
3. **Use `markdown` / `raw` for display** — full page markdown or upstream JSON when you need the complete source.
4. **Partial site crawl** — check `partial`, `failures`, and optional `error`; do not assume every discovered page appears in `pages`.
5. **Timeouts** — crawls and social scrapes can take a long time; set generous client timeouts and loading states.

---

## Environment

| Variable | Required | Purpose |
|----------|----------|---------|
| `BRIGHTDATA_API_TOKEN` | yes (social) | Bright Data API token |
| `PORT` | no | Server port (default `8000`) |
| `PLAYWRIGHT_BROWSERS_PATH` | no | Directory for Chromium binaries (set in Docker / `build.sh`) |

Web crawl endpoints use local [Crawl4AI](https://github.com/unclecode/crawl4ai) with Playwright — no API key required. Run `build.sh` or the Docker build step to install Chromium before starting the server.
