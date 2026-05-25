"""Extract RAG-ready records from Bright Data social scrape payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from chunking import build_rag_chunks

Extractor = Callable[[str, list[dict[str, Any]]], list["SocialRecord"]]

PRIMARY_RECORD_TYPE: dict[tuple[str, str], str] = {
    ("linkedin", "profiles"): "profile",
    ("linkedin", "companies"): "company",
    ("linkedin", "jobs"): "job",
    ("linkedin", "posts"): "post",
    ("instagram", "profiles"): "profile",
    ("instagram", "posts"): "post",
    ("instagram", "reels"): "reel",
    ("facebook", "posts_by_profile"): "post",
    ("facebook", "posts_by_group"): "post",
    ("facebook", "posts_by_url"): "post",
    ("facebook", "reels"): "reel",
}


@dataclass(frozen=True)
class ScrapeContext:
    platform: str
    scraper_type: str
    request_url: str
    raw: Any


@dataclass
class SocialRecord:
    text: str
    record_type: str
    source_url: str
    extra_metadata: dict[str, Any] = field(default_factory=dict)


def normalize_raw(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def first_str(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def kv_lines(fields: dict[str, str | None]) -> str:
    lines: list[str] = []
    seen_values: set[str] = set()
    for key, value in fields.items():
        if not value or value in seen_values:
            continue
        seen_values.add(value)
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def record_url(request_url: str, item: dict[str, Any]) -> str:
    return first_str(item, "url", "input_url", "post_url", "link") or request_url


def _append_post_records(
    records: list[SocialRecord],
    *,
    request_url: str,
    items: list[Any],
    parent_field: str,
    record_type: str = "post",
) -> None:
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        text = first_str(item, "text", "content", "post_text", "caption", "title", "description")
        if not text:
            continue
        extra: dict[str, Any] = {
            "parent_field": parent_field,
            "post_index": index,
        }
        if urn := first_str(item, "urn", "activity_urn", "post_id", "id"):
            extra["urn"] = urn
        records.append(
            SocialRecord(
                text=f"text: {text}",
                record_type=record_type,
                source_url=record_url(request_url, item),
                extra_metadata=extra,
            )
        )


def extract_linkedin_profile(request_url: str, items: list[dict[str, Any]]) -> list[SocialRecord]:
    records: list[SocialRecord] = []
    for item in items:
        profile_text = kv_lines({
            "name": first_str(item, "name", "full_name"),
            "headline": first_str(item, "headline", "position", "title"),
            "about": first_str(item, "about", "summary"),
            "location": first_str(item, "location", "city", "country_code"),
        })
        if profile_text:
            records.append(
                SocialRecord(
                    text=profile_text,
                    record_type="profile",
                    source_url=record_url(request_url, item),
                )
            )

        for index, exp in enumerate(item.get("experience") or []):
            if not isinstance(exp, dict):
                continue
            text = kv_lines({
                "title": first_str(exp, "title", "position"),
                "company": first_str(exp, "company", "company_name"),
                "location": first_str(exp, "location"),
                "description": first_str(exp, "description", "summary"),
                "dates": first_str(exp, "duration", "date_range", "start_date"),
            })
            if not text:
                continue
            records.append(
                SocialRecord(
                    text=text,
                    record_type="experience",
                    source_url=record_url(request_url, item),
                    extra_metadata={"parent_field": "experience", "parent_index": index},
                )
            )

        for index, edu in enumerate(item.get("education") or []):
            if not isinstance(edu, dict):
                continue
            text = kv_lines({
                "school": first_str(edu, "school", "title", "institution"),
                "degree": first_str(edu, "degree", "degree_name"),
                "field": first_str(edu, "field", "field_of_study"),
                "dates": first_str(edu, "duration", "date_range", "start_date"),
            })
            if not text:
                continue
            records.append(
                SocialRecord(
                    text=text,
                    record_type="education",
                    source_url=record_url(request_url, item),
                    extra_metadata={"parent_field": "education", "parent_index": index},
                )
            )

        _append_post_records(records, request_url=request_url, items=item.get("posts") or [], parent_field="posts")
        _append_post_records(records, request_url=request_url, items=item.get("activity") or [], parent_field="activity")

    return records


def extract_linkedin_company(request_url: str, items: list[dict[str, Any]]) -> list[SocialRecord]:
    records: list[SocialRecord] = []
    for item in items:
        specialties = item.get("specialties")
        specialty_text = None
        if isinstance(specialties, list):
            names = [s for s in specialties if isinstance(s, str) and s.strip()]
            if names:
                specialty_text = ", ".join(names)

        text = kv_lines({
            "name": first_str(item, "name"),
            "about": first_str(item, "about", "description"),
            "slogan": first_str(item, "slogan"),
            "industry": first_str(item, "industries", "industry"),
            "headquarters": first_str(item, "headquarters"),
            "company_size": first_str(item, "company_size"),
            "organization_type": first_str(item, "organization_type"),
            "specialties": specialty_text,
        })
        if text:
            records.append(
                SocialRecord(
                    text=text,
                    record_type="company",
                    source_url=record_url(request_url, item),
                )
            )
    return records


def extract_linkedin_job(request_url: str, items: list[dict[str, Any]]) -> list[SocialRecord]:
    records: list[SocialRecord] = []
    for item in items:
        text = kv_lines({
            "title": first_str(item, "title", "job_title", "position"),
            "company": first_str(item, "company", "company_name"),
            "location": first_str(item, "location", "job_location"),
            "description": first_str(item, "description", "job_description", "about"),
        })
        if text:
            records.append(
                SocialRecord(
                    text=text,
                    record_type="job",
                    source_url=record_url(request_url, item),
                )
            )
    return records


def extract_linkedin_post(request_url: str, items: list[dict[str, Any]]) -> list[SocialRecord]:
    records: list[SocialRecord] = []
    _append_post_records(records, request_url=request_url, items=items, parent_field="posts")
    return records


def extract_instagram_profile(request_url: str, items: list[dict[str, Any]]) -> list[SocialRecord]:
    records: list[SocialRecord] = []
    for item in items:
        text = kv_lines({
            "name": first_str(item, "full_name", "name"),
            "username": first_str(item, "username", "user_name"),
            "bio": first_str(item, "biography", "bio", "about"),
            "category": first_str(item, "category", "business_category"),
        })
        if text:
            records.append(
                SocialRecord(
                    text=text,
                    record_type="profile",
                    source_url=record_url(request_url, item),
                )
            )
    return records


def extract_instagram_post(request_url: str, items: list[dict[str, Any]]) -> list[SocialRecord]:
    records: list[SocialRecord] = []
    _append_post_records(records, request_url=request_url, items=items, parent_field="posts", record_type="post")
    return records


def extract_instagram_reel(request_url: str, items: list[dict[str, Any]]) -> list[SocialRecord]:
    records: list[SocialRecord] = []
    _append_post_records(records, request_url=request_url, items=items, parent_field="reels", record_type="reel")
    return records


def extract_facebook_posts(request_url: str, items: list[dict[str, Any]]) -> list[SocialRecord]:
    records: list[SocialRecord] = []
    _append_post_records(records, request_url=request_url, items=items, parent_field="posts", record_type="post")
    return records


def extract_facebook_reels(request_url: str, items: list[dict[str, Any]]) -> list[SocialRecord]:
    records: list[SocialRecord] = []
    _append_post_records(records, request_url=request_url, items=items, parent_field="reels", record_type="reel")
    return records


EXTRACTORS: dict[tuple[str, str], Extractor] = {
    ("linkedin", "profiles"): extract_linkedin_profile,
    ("linkedin", "companies"): extract_linkedin_company,
    ("linkedin", "jobs"): extract_linkedin_job,
    ("linkedin", "posts"): extract_linkedin_post,
    ("instagram", "profiles"): extract_instagram_profile,
    ("instagram", "posts"): extract_instagram_post,
    ("instagram", "reels"): extract_instagram_reel,
    ("facebook", "posts_by_profile"): extract_facebook_posts,
    ("facebook", "posts_by_group"): extract_facebook_posts,
    ("facebook", "posts_by_url"): extract_facebook_posts,
    ("facebook", "reels"): extract_facebook_reels,
}


def extract_records(ctx: ScrapeContext) -> list[SocialRecord]:
    extractor = EXTRACTORS.get((ctx.platform, ctx.scraper_type))
    if extractor is None:
        raise ValueError(f"No extractor for {ctx.platform}/{ctx.scraper_type}")
    return extractor(ctx.request_url, normalize_raw(ctx.raw))


def records_to_chunks(records: list[SocialRecord], platform: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for record in records:
        if not record.text.strip():
            continue
        chunks.extend(
            build_rag_chunks(
                record.text,
                source_url=record.source_url,
                content_type=f"{platform}_record",
                platform=platform,
                record_type=record.record_type,
                **record.extra_metadata,
            )
        )
    return chunks


def primary_record_type(ctx: ScrapeContext) -> str:
    record_type = PRIMARY_RECORD_TYPE.get((ctx.platform, ctx.scraper_type))
    if record_type is None:
        raise ValueError(f"Unknown primary record type for {ctx.platform}/{ctx.scraper_type}")
    return record_type


def top_level_metadata(records: list[SocialRecord], ctx: ScrapeContext) -> dict[str, Any]:
    primary = primary_record_type(ctx)
    for record in records:
        if record.record_type != primary:
            continue
        for key in ("name", "title"):
            if key in record.extra_metadata:
                return {"title": record.extra_metadata[key]}
        first_line = record.text.split("\n", 1)[0]
        if first_line.startswith("name: "):
            return {"title": first_line.removeprefix("name: ")}
        if first_line.startswith("title: "):
            return {"title": first_line.removeprefix("title: ")}
    return {}
