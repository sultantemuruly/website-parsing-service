# Website Parsing Service — API Reference

FastAPI service that scrapes websites (Crawl4AI + Cloudflare Browser Run over CDP) and social profiles (Bright Data), optionally splits content into RAG-ready chunks, and can summarize business context via an LLM.

Web crawl responses return **image-stripped markdown** with **hyperlinks preserved** (product pages, news, YouTube, partner sites, etc.) — cleaning happens at crawl time, not in `/process/page`.

**Source layout:** application code lives under `src/` (see `.cursor/skills/layered-service/SKILL.md`). Run via `start.sh` (`PYTHONPATH=src`, `uvicorn main:app`).

**Base URL:** `http://localhost:8000` (override with `PORT` in `start.sh`)

**OpenAPI / Swagger:** `GET /docs` on the running server

**CORS:** All origins, methods, and headers are allowed today (may be restricted later).

---

## Quick start (frontend)

Most ingestion flows are **two steps**: **scrape** (query param) → **process** (JSON body). Scrape responses are shaped so you can POST the same JSON to the matching process endpoint without reshaping fields.

**Business summary** is a separate one-step flow: `POST /business_profile` with page or site markdown in the JSON body.

### Single web page

```ts
const base = "http://localhost:8000";

// 1. Scrape
const scrapeRes = await fetch(
  `${base}/crawl?url=${encodeURIComponent("https://example.com")}`,
  { method: "POST" },
);
if (!scrapeRes.ok) throw new Error(await scrapeRes.text());
const crawlPayload = await scrapeRes.json(); // CrawlPagePayload

// 2. Chunk for RAG
const processRes = await fetch(`${base}/process/page`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(crawlPayload),
});
const pageResult = await processRes.json(); // PageResult — use pageResult.chunks
```

### Single social profile / post

```ts
const scrapeRes = await fetch(
  `${base}/linkedin?url=${encodeURIComponent("https://www.linkedin.com/in/jane-doe")}`,
  { method: "POST" },
);
const socialPayload = await scrapeRes.json(); // SocialScrapePayload

const processRes = await fetch(`${base}/process/social`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(socialPayload),
});
const socialResult = await processRes.json(); // SocialResult — use socialResult.chunks
```

### Site crawl (many pages)

| Goal | Endpoint |
|------|----------|
| Only successful pages | `POST /crawl/site?url=...` → `CrawlPagePayload[]` |
| Successes + per-URL failures | `POST /crawl/site/partial?url=...` → `PartialCrawlResult` |

Use `POST /crawl/site/partial` by default for user-facing flows. It preserves successful pages and exposes crawl failures when the shared browser is recycled mid-run.

Then call `POST /process/page` once per item in `pages` (or batch in your app).

### Business profile summary

```ts
const processRes = await fetch(`${base}/process/page`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(crawlPayload),
});
const pageResult = await processRes.json();

const summaryRes = await fetch(`${base}/business_profile`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ context: pageResult.markdown }),
});
const summary = await summaryRes.json(); // SummaryModel
```

You can pass any text in `context` — full site markdown, a single page, or manually curated copy.

---

## Endpoint overview

| Method | Path | Input | Output |
|--------|------|--------|--------|
| `GET` | `/` | — | `{ status: "ok" }` |
| `POST` | `/crawl` | query `url` | `CrawlPagePayload` |
| `POST` | `/crawl/site` | query `url` | `CrawlPagePayload[]` |
| `POST` | `/crawl/site/partial` | query `url` | `PartialCrawlResult` |
| `POST` | `/linkedin` | query `url` | `SocialScrapePayload` |
| `POST` | `/instagram` | query `url` | `SocialScrapePayload` |
| `POST` | `/facebook` | query `url` | `SocialScrapePayload` |
| `POST` | `/process/page` | JSON body | `PageResult` |
| `POST` | `/process/social` | JSON body | `SocialResult` |
| `POST` | `/business_profile` | JSON body | `SummaryModel` |

**Scrape routes:** `url` is a **query parameter** (even though the method is `POST`).

**Process and summary routes:** **JSON body**, `Content-Type: application/json`.

---

## Errors

All error responses use FastAPI’s default shape:

```json
{ "detail": "human-readable message" }
```

`detail` may be a string or a validation error list (for `422`).

| Status | When |
|--------|------|
| `400` | Empty / whitespace-only `markdown` on `/process/page`; explicitly empty `url` query value on scrape routes |
| `422` | Missing required query params or invalid JSON body (missing required fields, wrong types, whitespace-only or over-length `context` on `/business_profile`) on `/process/*` or `/business_profile` |
| `429` | Crawler is saturated and could not acquire a slot in time (`/crawl*`) |
| `502` | Scrape failed, unsupported social URL, Bright Data error, no extractable social content, or LLM / summary failure |
| `500` | Unexpected server error (e.g. site crawl engine threw before returning any results) |

---

## Types

### `Chunk` (only on process responses)

Text is split with **512** characters and **50** overlap (`chunking.py`). Boundaries prefer paragraphs, then lines, then sentences.

```ts
type Chunk = {
  text: string;
  metadata: {
    source_url: string;
    content_type:
      | "web_page"
      | "linkedin_record"
      | "instagram_record"
      | "facebook_record";
    chunk_index: number;

    // Web (`/process/page`) — optional on each chunk:
    title?: string;
    language?: string;
    site_seed_url?: string; // only when request included site_seed_url

    // Social (`/process/social`) — optional on each chunk:
    platform?: string;
    record_type?: string; // may differ per chunk (e.g. profile vs experience vs post)
    parent_field?: string;
    parent_index?: number;
    post_index?: number;
    urn?: string;
  };
};
```

`description` is **not** copied onto web chunks; it lives on `PageResult.metadata` only.

---

### `CrawlPagePayload`

Returned by `/crawl` and entries in `/crawl/site*`. **Same shape as** `POST /process/page` body.

`markdown` is **cleaned at crawl time** for RAG: image references (`![alt](url)`) are removed; text hyperlinks (`[label](url)`) are kept, including external links (e.g. YouTube, partner sites). The same cleaned string is what `/process/page` chunks when you pass a scrape payload through unchanged.

```ts
type CrawlPagePayload = {
  markdown: string; // image-stripped; navigation/content links preserved
  url: string;
  title?: string;
  language?: string;
  description?: string;
  site_seed_url?: string; // present on site crawl routes (seed URL)
};
```

---

### `PageResult`

Returned by `POST /process/page`.

```ts
type PageResult = {
  url: string;
  markdown: string;
  metadata: {
    title?: string;
    language?: string;
    description?: string;
  };
  chunks: Chunk[]; // metadata.content_type === "web_page"
};
```

---

### `SocialScrapePayload`

Returned by `/linkedin`, `/instagram`, `/facebook`. **Same shape as** `POST /process/social` body.

```ts
type SocialScrapePayload = {
  platform: "linkedin" | "instagram" | "facebook";
  scraper_type: string; // see scraper_type tables below
  request_url: string;
  raw: object | object[];
};
```

No `chunks`, `record_type`, or `metadata` on scrape responses — only after `/process/social`.

---

### `SocialResult`

Returned by `POST /process/social`.

```ts
type SocialResult = {
  url: string;
  platform: "linkedin" | "instagram" | "facebook";
  scraper_type: string;
  record_type: string; // primary type for this scrape
  metadata: { title?: string }; // often {}
  raw: object | object[];
  chunks: Chunk[]; // metadata.content_type === "{platform}_record"
};
```

Top-level `record_type` is the primary type for the scrape. Individual chunks may have a more specific `metadata.record_type` (e.g. LinkedIn profile scrape: `profile`, `experience`, `education`, `post`).

---

### `PartialCrawlResult`

Returned by `POST /crawl/site/partial` only.

```ts
type PartialCrawlResult = {
  partial: boolean; // true when failures.length > 0
  site_seed_url: string;
  pages: CrawlPagePayload[];
  failures: Array<{ url: string; error: string }>;
};
```

- **`pages`:** crawled successfully and had non-empty markdown.
- **`failures`:** URL was visited but failed (`Crawl failed`, `No markdown`, etc.).
- **`partial`:** shorthand for “there were failures”; always `failures.length > 0` when `true`.
- URLs that were never attempted are not listed.
- If the crawl engine throws before returning results → **`500`** (no wrapper).

Use this endpoint when the UI should show “12 pages OK, 3 failed” instead of failing the whole job.

---

### `SummaryModel`

Returned by `POST /business_profile`.

```ts
type SummaryModel = {
  tone_style: "friendly" | "professional" | "formal" | "casual" | "empathetic" | "assertive" | "humorous";
  product_name: string;        // official product or brand name from the source
  general_description: string; // 1-2 factual sentences: what the business is, who it serves, what it does
  key_advantages: string;      // main selling points as short phrases separated by periods
  main_goal: string;           // primary conversion or business objective inferred from the site
  agent_description: string;   // third-person description of the agent (profile copy, not instructions)
  topics: string[];            // permissible conversation topics evidenced in the source
};
```

Request body for `POST /business_profile`:

```ts
type BusinessProfileRequest = {
  context: string;        // required
  agent_name?: string;    // optional — display name; used in agent_description when provided
  agent_role?: string;    // optional — role label (e.g. sales, support); tailors agent fields when provided
  industry?: string;      // optional — business industry label; helps tone selection and phrasing
};
```

---

## Web endpoints

Crawl routes produce markdown optimized for vector DB ingest:

| Removed at crawl | Preserved |
|------------------|-----------|
| `<img>` elements and `![alt](url)` image markdown (including same-domain CDN assets) | `[text](url)` hyperlinks — internal pages, products, news, docs, YouTube, etc. |
| Non-HTML URLs during site BFS discovery (images, PDFs, downloads) | HTML pages only are enqueued and crawled |

**Not cleaned:** markdown sent directly to `POST /process/page` without scraping (manual paste or stored payloads from other sources) — only `/crawl*` responses are filtered.

Linked-image patterns (`[![thumb](img.png)](real-url)`) are normalized to `[thumb](real-url)` when present.

---

### `GET /`

Health check.

```json
{ "status": "ok" }
```

---

### `POST /crawl`

Scrape one URL to markdown (images stripped, links preserved — see **Web endpoints** above).

| Query | Required | Description |
|-------|----------|-------------|
| `url` | yes | Page URL |

**`200`:** `CrawlPagePayload`

**Errors:** `422` missing `url`; `400` empty `url`; `429` crawler is saturated and could not acquire a slot in time; `502` scrape failed, browser recovery was exhausted, or no markdown; `500` other.

---

### `POST /crawl/site`

BFS site crawl: up to **`CRAWL_MAX_PAGES`** pages (default **25**), max depth **`CRAWL_MAX_DEPTH`** (default **1**), same origin only. Internal Crawl4AI fan-out is capped by `CRAWL_SITE_SEMAPHORE_COUNT` (default **1**).

Only **HTML** pages are discovered and crawled — asset URLs (images, PDFs, etc.) are skipped so crawl budget is not spent on non-page resources. Markdown on each page is image-stripped with links preserved (same rules as `/crawl`).

| Query | Required | Description |
|-------|----------|-------------|
| `url` | yes | Seed URL |

**`200`:** `CrawlPagePayload[]` — only successful pages. Each item includes `site_seed_url` equal to the seed `url`.

**Empty array:** crawl ran but every page failed or had no markdown.

**Errors:** `422` missing `url`; `400` empty `url`; `429` crawler is saturated and could not acquire a slot in time; `502` if the crawl fails before any usable result can be returned; `500` other.

---

### `POST /crawl/site/partial`

Same limits and markdown cleaning as `/crawl/site`, but returns failures per URL. This is the recommended endpoint for site crawls on constrained deployments because successful pages are preserved even if the browser dies partway through a run.

| Query | Required | Description |
|-------|----------|-------------|
| `url` | yes | Seed URL |

**`200`:** `PartialCrawlResult`

**Errors:** `422` missing `url`; `400` empty `url`; `429` crawler is saturated and could not acquire a slot in time; `502` if crawler recovery is exhausted before any result set can be returned; `500` other.

---

## Social endpoints

### `POST /linkedin` · `POST /instagram` · `POST /facebook`

| Query | Required | Description |
|-------|----------|-------------|
| `url` | yes | Supported profile / post / company / job URL for that platform |

**`200`:** `SocialScrapePayload`

**Errors:** `422` missing `url`; `400` empty `url`; `502` unsupported URL or Bright Data failure; `500` other.

#### Example scrape response

```json
{
  "platform": "linkedin",
  "scraper_type": "profiles",
  "request_url": "https://www.linkedin.com/in/jane-doe",
  "raw": {}
}
```

Pass this object unchanged to `POST /process/social`.

### `scraper_type` values (returned by scrape, required by process)

Use the exact string from the scrape response when re-processing stored `raw` data.

**LinkedIn**

| `scraper_type` | Typical URL signal |
|----------------|-------------------|
| `profiles` | `/in/…`, `/pub/…` |
| `companies` | `/company/…` |
| `jobs` | `/jobs/view…`, `/jobs/…` (not search) |
| `posts` | `/feed/update…`, `/posts/…`, `urn:li:activity` |

**Instagram**

| `scraper_type` | Typical URL signal |
|----------------|-------------------|
| `profiles` | `instagram.com/{username}` (single segment) |
| `posts` | `/p/…` |
| `reels` | `/reel/…`, `/reels/…` |

Unsupported paths (e.g. `/stories/`, `/explore/`) → `502` `Unsupported Instagram URL: …`.

**Facebook**

| `scraper_type` | Typical URL signal |
|----------------|-------------------|
| `posts_by_profile` | Default profile timeline |
| `posts_by_group` | `/groups/…` |
| `posts_by_url` | `/posts/`, `/permalink/`, `/story.php`, `/photo.php`, `/videos/`, `/watch/` |
| `reels` | `/reel…` |

### `record_type` after `/process/social`

Derived from `(platform, scraper_type)`, not returned on scrape.

| Platform | `scraper_type` | `record_type` |
|----------|----------------|---------------|
| linkedin | profiles | profile |
| linkedin | companies | company |
| linkedin | jobs | job |
| linkedin | posts | post |
| instagram | profiles | profile |
| instagram | posts | post |
| instagram | reels | reel |
| facebook | posts_by_profile | post |
| facebook | posts_by_group | post |
| facebook | posts_by_url | post |
| facebook | reels | reel |

Unknown `(platform, scraper_type)` at process time → `502` `No extractor for …`.

---

## Process endpoints

### `POST /process/page`

Chunk page markdown without scraping. Accepts `CrawlPagePayload`.

Does **not** apply crawl-stage image filtering — it chunks the `markdown` you send as-is. Use `/crawl*` first if you want image-stripped markdown; only needed when re-processing a stored scrape payload or when you control the input text yourself.

**Body (example):**

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

| Field | Required | Notes |
|-------|----------|--------|
| `markdown` | yes | Non-empty after `.trim()` |
| `url` | yes | Stored as `source_url` on chunks |
| `title`, `language`, `description` | no | `description` only on `PageResult.metadata` |
| `site_seed_url` | no | Copied to each chunk’s `metadata.site_seed_url` when set |

**`200`:** `PageResult`

**Errors:** `422` validation (missing fields); `400` whitespace-only `markdown`; `502` internal normalization error; `500` other.

---

### `POST /process/social`

Normalize Bright Data JSON into chunks without scraping. Accepts `SocialScrapePayload`.

**Body (example):**

```json
{
  "platform": "linkedin",
  "scraper_type": "profiles",
  "request_url": "https://www.linkedin.com/in/jane-doe",
  "raw": {}
}
```

| Field | Required | Notes |
|-------|----------|--------|
| `platform` | yes | `linkedin`, `instagram`, or `facebook` |
| `scraper_type` | yes | From scrape response |
| `request_url` | yes | Original scraped URL |
| `raw` | yes | Object or array from Bright Data |

**`200`:** `SocialResult`

**Errors:** `422` validation; `502` no extractable content or unknown extractor; `500` other.

**Example `200` (truncated):**

```json
{
  "url": "https://www.linkedin.com/in/jane-doe",
  "platform": "linkedin",
  "scraper_type": "profiles",
  "record_type": "profile",
  "metadata": { "title": "Jane Doe" },
  "raw": {},
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

## Summary endpoints

### `POST /business_profile`

Extract a structured business profile from noisy page or site markdown (or any other text about the business). Uses an OpenAI-backed agent with structured output — no scraping step.

**Body (example):**

```json
{
  "context": "# Acme Corp\n\nWe build widgets for enterprise customers...",
  "agent_name": "Aria",
  "agent_role": "sales",
  "industry": "enterprise software"
}
```

| Field | Required | Notes |
|-------|----------|--------|
| `context` | yes | Non-empty after trim; max **200,000** characters |
| `agent_name` | no | Agent display name; when omitted, inferred only from context |
| `agent_role` | no | Agent role label; when omitted, inferred only from context |
| `industry` | no | Optional industry label; when omitted, inferred only from context |

**`200`:** `SummaryModel`

**Example `200`:**

```json
{
  "tone_style": "professional",
  "product_name": "Acme Corp",
  "general_description": "Acme Corp designs and manufactures enterprise widget systems for industrial automation. The company serves large manufacturers across North America and Europe.",
  "key_advantages": "24/7 support. Same-day shipping on standard orders. ISO 9001 certified. Custom integrations with major ERP platforms.",
  "main_goal": "Request a quote for an enterprise widget deployment.",
  "agent_description": "A sales assistant for Acme Corp that helps enterprise customers explore widget systems and find the right deployment option before requesting a quote.",
  "topics": [
    "Enterprise widget systems",
    "Industrial automation",
    "Pricing and quotes",
    "ERP integrations",
    "Support and shipping"
  ]
}
```

**Errors:** `422` validation (missing fields, whitespace-only `context`, or `context` over 200,000 characters); `502` LLM or structured-output failure (e.g. missing `OPENAI_API_KEY`); `500` other.

Typical flow: scrape → `/process/page` (optional, for chunks) → concatenate or pick `markdown` → `/business_profile`.

---

## Frontend checklist

1. **Encode query URLs** — always `encodeURIComponent(url)` on scrape routes.
2. **Long timeouts** — crawls and social scrapes can take minutes; show loading state.
3. **Store scrape payloads** — you can call `/process/*` later without re-scraping.
4. **RAG ingestion** — use `chunks[]` from process responses; each chunk has `source_url` and `chunk_index`. Scrape payloads from `/crawl*` already have image noise removed from `markdown`.
5. **Full content for UI** — use `markdown` (web) or `raw` (social) from scrape or process responses. Web `markdown` from crawl routes omits images but keeps links.
6. **Site crawl UX** — prefer `/crawl/site/partial` if you need to surface failed URLs; use `/crawl/site` if you only care about successes.
7. **No chunks on scrape** — if an older client expected `chunks` on `/crawl` or `/linkedin`, migrate to the two-step flow above.
8. **Business summary** — `/business_profile` is independent of scrape/process; pass markdown or other text in `context`. Allow extra time for the LLM call.
9. **Crawl backpressure** — `429` on `/crawl*` means the replica is at `CRAWL_MAX_IN_FLIGHT`; retry with backoff.

---

## Server environment

| Variable | Required | Purpose |
|----------|----------|---------|
| `CF_ACCOUNT_ID` | yes for web routes | Cloudflare account ID for Browser Rendering CDP |
| `CF_API_TOKEN` | yes for web routes | API token with **Browser Rendering - Edit** permission |
| `CF_BROWSER_KEEP_ALIVE_MS` | no | CDP session keep-alive in ms (default `600000`, max ~600000) |
| `BRIGHTDATA_API_TOKEN` | yes for social routes | Bright Data API token |
| `OPENAI_API_KEY` | yes for `/business_profile` | OpenAI API key for the summary agent |
| `PORT` | no | HTTP port (default `8000`) |
| `CRAWL_MAX_IN_FLIGHT` | no | Max concurrent crawl requests per replica (default `1`); keep ≤ Cloudflare browser concurrency |
| `CRAWL_QUEUE_TIMEOUT_MS` | no | How long a request waits for a crawl slot before returning `429` (default `1000`) |
| `CRAWL_MAX_PAGES` | no | Max pages returned from a site crawl (default `25`) |
| `CRAWL_MAX_DEPTH` | no | Deep-crawl BFS depth cap (default `1`) |
| `CRAWL_SITE_SEMAPHORE_COUNT` | no | Crawl4AI per-site concurrency cap for site crawls (default `1`) |
| `CRAWL_PAGE_TIMEOUT_MS` | no | Per-page Crawl4AI timeout in milliseconds (default `30000`) |

Web routes use **Cloudflare Browser Run** over CDP (no local Chromium). Set `CF_ACCOUNT_ID` and `CF_API_TOKEN` before starting the server. Social routes use Bright Data. `/business_profile` uses OpenAI (`OPENAI_API_KEY`).

**Startup note:** `crawl/config.py` and `social/scrape/brightdata_adapter.py` validate `CF_*` and `BRIGHTDATA_API_TOKEN` at import time, so the process expects those variables even if you only call summary or process routes. Tests set dummy values via `tests/bootstrap.py`.

## How billing works

Web crawl routes use **Cloudflare Browser Sessions** (Playwright / CDP). Official pricing: [Cloudflare Browser Run — Pricing](https://developers.cloudflare.com/browser-rendering/pricing/).

Cloudflare charges on **two separate metrics** — not per request, and not per “session created”:

| Metric | What you pay for | Workers Paid |
|--------|------------------|--------------|
| **Browser hours** | Total time remote browser sessions exist (active or idle) | 10 hrs/month included, then **$0.09/hr** |
| **Concurrent browsers** | How many sessions run **at the same time** (monthly average of daily peaks) | 10 included, then **$2.00/browser/month** |

### Browser hours (duration)

Usage is totaled in **seconds per day**, summed for the month, then rounded to whole hours (30+ minutes in a month rounds up to 1 hour).

- A session that stays open counts for the **entire time it exists**, not just while a page is loading.
- After a crawl finishes, the remote browser may remain open until its idle timeout (`CF_BROWSER_KEEP_ALIVE_MS`, default 10 minutes). **Those idle minutes are billable.**
- Failed infrastructure errors are not charged; normal session lifetime is.

### Concurrent browsers (overlap)

This is **not** “how many crawls you ran this month.” Cloudflare records your **peak concurrent browser count each day**, then averages those daily peaks over the month.

- `CRAWL_MAX_IN_FLIGHT=1` (default) keeps one browser per replica at a time — good for staying within included concurrency.
- Brief spikes matter less than sustained high parallelism across replicas.

### What this means for this service

| Request | Typical browser usage |
|---------|----------------------|
| `POST /crawl` | One session for one page |
| `POST /crawl/site` / `/crawl/site/partial` | One session for the whole site crawl (all pages in that job) |

**Cost levers:** lower `CF_BROWSER_KEEP_ALIVE_MS` so sessions close sooner after a job; keep `CRAWL_MAX_IN_FLIGHT` ≤ your Cloudflare concurrency limit; avoid running many replicas that each hold an open browser at once.

Workers Paid also has a base Workers plan fee (~$5/month). Workers Free includes **10 minutes of browser time per day** and **3 concurrent browsers** — usually too small for production. Monitor usage in the dashboard under **Compute → Browser Run**.
