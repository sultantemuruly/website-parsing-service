from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
