import asyncio
import json
import re
import time
from dataclasses import dataclass
from email.message import Message
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from crawl.config import (
    CF_API_TOKEN,
    CF_BROWSER_RUN_BASE_URL,
    CF_CRAWL_PURPOSES,
    CRAWL_JOB_POLL_INTERVAL_MS,
    CRAWL_JOB_TIMEOUT_MS,
    MAX_CRAWL_PAGES,
    MAX_DISCOVERY_DEPTH,
)

_REQUEST_TIMEOUT_SECONDS = 60
_MAX_RATE_LIMIT_RETRIES = 3
_CRAWL_TERMINAL_STATUSES = {
    "completed",
    "errored",
    "cancelled_by_user",
    "cancelled_due_to_timeout",
    "cancelled_due_to_limits",
}

_LINKED_IMAGE_RE = re.compile(r"\[!\[([^\]]*)\]\([^)]*\)\]\(([^)]+)\)")
_BARE_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")


@dataclass
class CrawledPage:
    markdown: str
    metadata: dict[str, Any]


class _RateLimitError(RuntimeError):
    def __init__(self, message: str, retry_after_seconds: float):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


def _normalize_image_markdown(text: str) -> str:
    text = _LINKED_IMAGE_RE.sub(r"[\1](\2)", text)
    return _BARE_IMAGE_RE.sub("", text)


def _metadata_dict(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        return metadata
    return {}


def _record_url(record: dict[str, Any], fallback: str) -> str:
    metadata = _metadata_dict(record)
    return (
        str(record.get("url") or "")
        or str(metadata.get("source_url") or "")
        or str(metadata.get("sourceURL") or "")
        or fallback
    )


def _markdown_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _normalize_image_markdown(value)
    if isinstance(value, dict):
        text = value.get("markdown") or value.get("raw_markdown") or value.get("rawMarkdown")
        if text is None:
            return ""
        return _normalize_image_markdown(str(text))
    return _normalize_image_markdown(str(value))


def record_to_page(record: dict[str, Any]) -> CrawledPage:
    metadata = _metadata_dict(record)
    page_metadata: dict[str, Any] = {
        "source_url": _record_url(record, ""),
    }
    for key in ("title", "language", "description"):
        value = metadata.get(key) or record.get(key)
        if value:
            page_metadata[key] = value
    return CrawledPage(
        markdown=_markdown_text(record.get("markdown")),
        metadata=page_metadata,
    )


def _record_status(record: dict[str, Any]) -> str:
    status = record.get("status")
    if status:
        return str(status)
    metadata = _metadata_dict(record)
    if metadata.get("status"):
        return str(metadata["status"])
    return ""


def _record_error(record: dict[str, Any]) -> str:
    metadata = _metadata_dict(record)
    for key in ("error", "message"):
        value = record.get(key)
        if value:
            return str(value)
    for key in ("error", "message", "statusText"):
        value = metadata.get(key)
        if value:
            return str(value)
    status = _record_status(record)
    if status:
        return f"Crawl status: {status}"
    return "Crawl failed"


def _classify_site_record(
    record: dict[str, Any], seed_url: str
) -> tuple[CrawledPage | None, dict[str, str] | None]:
    page_url = _record_url(record, seed_url)
    if _record_status(record) not in {"", "completed"}:
        return None, {"url": page_url, "error": _record_error(record)}

    markdown = _markdown_text(record.get("markdown"))
    if not markdown.strip():
        return None, {"url": page_url, "error": "No markdown"}

    page = record_to_page({**record, "url": page_url, "markdown": markdown})
    return page, None


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }


def _request_url(path: str, query: dict[str, Any] | None = None) -> str:
    url = f"{CF_BROWSER_RUN_BASE_URL}{path}"
    if not query:
        return url
    encoded = urlencode({k: v for k, v in query.items() if v is not None})
    return f"{url}?{encoded}" if encoded else url


def _load_json_bytes(raw: bytes) -> Any:
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _error_message(payload: Any, fallback: str) -> str:
    if isinstance(payload, dict):
        errors = payload.get("errors")
        if isinstance(errors, list):
            messages = []
            for item in errors:
                if isinstance(item, dict) and item.get("message"):
                    messages.append(str(item["message"]))
                elif item:
                    messages.append(str(item))
            if messages:
                return "; ".join(messages)

        for key in ("message", "error"):
            value = payload.get(key)
            if value:
                return str(value)

        result = payload.get("result")
        if isinstance(result, dict):
            for key in ("message", "error"):
                value = result.get(key)
                if value:
                    return str(value)

    return fallback


def _retry_after_seconds(headers: Message | None) -> float:
    if headers is None:
        return 1.0
    value = headers.get("Retry-After")
    if not value:
        return 1.0
    try:
        return max(float(value), 0.1)
    except ValueError:
        return 1.0


def _unwrap_result(payload: Any) -> Any:
    if isinstance(payload, dict):
        if payload.get("success") is False:
            raise ValueError(_error_message(payload, "Cloudflare Browser Run request failed"))
        if "result" in payload:
            return payload["result"]
    return payload


def _browser_run_request_sync(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> Any:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        _request_url(path, query),
        data=body,
        headers=_auth_headers(),
        method=method,
    )

    try:
        with urlopen(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
            return _unwrap_result(_load_json_bytes(response.read()))
    except HTTPError as exc:
        payload = _load_json_bytes(exc.read())
        message = _error_message(payload, f"Cloudflare Browser Run error ({exc.code})")
        if exc.code == 429:
            raise _RateLimitError(message, _retry_after_seconds(exc.headers)) from exc
        raise ValueError(message) from exc
    except URLError as exc:
        raise ValueError(f"Cloudflare Browser Run request failed: {exc.reason}") from exc


async def _browser_run_request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> Any:
    for attempt in range(_MAX_RATE_LIMIT_RETRIES):
        try:
            return await asyncio.to_thread(
                _browser_run_request_sync,
                method,
                path,
                payload=payload,
                query=query,
            )
        except _RateLimitError as exc:
            if attempt == _MAX_RATE_LIMIT_RETRIES - 1:
                raise ValueError(str(exc)) from exc
            await asyncio.sleep(exc.retry_after_seconds)

    raise RuntimeError("unreachable")


def _markdown_request_payload(url: str) -> dict[str, Any]:
    return {
        "url": url,
        "gotoOptions": {"waitUntil": "networkidle2"},
    }


def _crawl_request_payload(url: str, limit: int) -> dict[str, Any]:
    return {
        "url": url,
        "limit": limit,
        "depth": MAX_DISCOVERY_DEPTH,
        "render": True,
        "source": "all",
        "formats": ["markdown"],
        "crawlPurposes": CF_CRAWL_PURPOSES,
        "gotoOptions": {"waitUntil": "networkidle2"},
    }


def _crawl_job_status(result: dict[str, Any]) -> str:
    return str(result.get("status") or "")


def _crawl_job_error(result: dict[str, Any]) -> str:
    for key in ("error", "message"):
        value = result.get(key)
        if value:
            return str(value)
    status = _crawl_job_status(result)
    if status:
        return f"Crawl job ended with status: {status}"
    return "Crawl job failed"


async def _cancel_crawl_job(job_id: str) -> None:
    try:
        await _browser_run_request("DELETE", f"/crawl/{job_id}")
    except ValueError:
        return


async def _start_crawl_job(url: str, limit: int) -> str:
    result = await _browser_run_request("POST", "/crawl", payload=_crawl_request_payload(url, limit))
    job_id = result.get("id") if isinstance(result, dict) else None
    if not job_id:
        raise ValueError("Cloudflare Browser Run did not return a crawl job id")
    return str(job_id)


async def _wait_for_crawl_job(job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + (CRAWL_JOB_TIMEOUT_MS / 1000)

    while True:
        result = await _browser_run_request("GET", f"/crawl/{job_id}", query={"limit": 1})
        if not isinstance(result, dict):
            raise ValueError("Cloudflare Browser Run returned an invalid crawl job payload")

        if _crawl_job_status(result) in _CRAWL_TERMINAL_STATUSES:
            return result

        if time.monotonic() >= deadline:
            await _cancel_crawl_job(job_id)
            raise ValueError(f"Crawl job timed out after {CRAWL_JOB_TIMEOUT_MS}ms")

        await asyncio.sleep(CRAWL_JOB_POLL_INTERVAL_MS / 1000)


async def _fetch_all_crawl_records(job_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cursor: str | None = None
    records: list[dict[str, Any]] = []
    final_result: dict[str, Any] | None = None

    while True:
        query: dict[str, Any] = {"limit": MAX_CRAWL_PAGES}
        if cursor:
            query["cursor"] = cursor

        result = await _browser_run_request("GET", f"/crawl/{job_id}", query=query)
        if not isinstance(result, dict):
            raise ValueError("Cloudflare Browser Run returned an invalid crawl result payload")

        final_result = result
        page_records = result.get("records")
        if isinstance(page_records, list):
            for item in page_records:
                if isinstance(item, dict):
                    records.append(item)

        cursor = result.get("cursor")
        if not cursor:
            return final_result, records


async def scrape_page(url: str) -> CrawledPage:
    result = await _browser_run_request("POST", "/markdown", payload=_markdown_request_payload(url))
    markdown = _markdown_text(result)
    if not markdown.strip():
        raise ValueError("No markdown")
    return CrawledPage(markdown=markdown, metadata={"source_url": url})


async def crawl_site_with_outcomes(
    url: str, *, limit: int = MAX_CRAWL_PAGES
) -> tuple[list[CrawledPage], list[dict[str, str]]]:
    capped_limit = min(max(limit, 1), MAX_CRAWL_PAGES)
    job_id = await _start_crawl_job(url, capped_limit)
    terminal_result = await _wait_for_crawl_job(job_id)
    final_result, records = await _fetch_all_crawl_records(job_id)

    pages: list[CrawledPage] = []
    failures: list[dict[str, str]] = []
    for record in records:
        page, failure = _classify_site_record(record, url)
        if page is not None:
            pages.append(page)
        elif failure is not None:
            failures.append(failure)

    terminal_status = _crawl_job_status(terminal_result)
    if terminal_status != "completed":
        job_failure = {"url": url, "error": _crawl_job_error(final_result)}
        if job_failure not in failures:
            failures.append(job_failure)

    return pages, failures


async def crawl_site(url: str, *, limit: int = MAX_CRAWL_PAGES) -> list[CrawledPage]:
    pages, _ = await crawl_site_with_outcomes(url, limit=limit)
    return pages
