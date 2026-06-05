"""Inject Cloudflare CDP Authorization headers into crawl4ai Playwright connections."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

_patch_applied = False
_original_connect_over_cdp: Callable[..., Any] | None = None


def cdp_auth_headers(token: str | None = None) -> dict[str, str]:
    value = token if token is not None else os.getenv("CF_API_TOKEN")
    if not value:
        raise ValueError("CF_API_TOKEN is not set")
    return {"Authorization": f"Bearer {value}"}


def apply_cdp_auth_patch(*, token: str | None = None) -> None:
    """Patch Playwright connect_over_cdp to send Bearer auth (idempotent)."""
    global _patch_applied, _original_connect_over_cdp
    if _patch_applied:
        return

    from playwright.async_api import BrowserType

    _original_connect_over_cdp = BrowserType.connect_over_cdp
    headers = cdp_auth_headers(token)

    async def connect_over_cdp(
        self,
        endpoint_url: str,
        **kwargs: Any,
    ):
        kwargs.setdefault("headers", headers)
        return await _original_connect_over_cdp(self, endpoint_url, **kwargs)

    BrowserType.connect_over_cdp = connect_over_cdp
    _patch_applied = True
