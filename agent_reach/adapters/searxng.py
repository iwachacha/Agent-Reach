# -*- coding: utf-8 -*-
"""SearXNG collection adapter."""

from __future__ import annotations

import time
import warnings

from agent_reach.results import (
    CollectionResult,
    NormalizedItem,
    build_item,
    build_pagination_meta,
    parse_timestamp,
)
from agent_reach.source_hints import search_result_source_hints

from .base import BaseAdapter

_UA = "agent-reach/1.6.0 (+https://github.com/iwachacha/Agent-Reach)"


def _import_requests():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 .* doesn't match a supported version!",
        )
        import requests

    return requests


def _result_item(entry: dict, idx: int) -> NormalizedItem:
    published_at = parse_timestamp(
        entry.get("publishedDate") or entry.get("published_date") or entry.get("published")
    )
    url = entry.get("url")
    return build_item(
        item_id=url or entry.get("title") or f"searxng-{idx}",
        kind="search_result",
        title=entry.get("title"),
        url=url,
        text=entry.get("content"),
        author=None,
        published_at=published_at,
        source="searxng",
        extras={
            "engines": entry.get("engines") or [],
            "category": entry.get("category"),
            "source_hints": search_result_source_hints(published_at),
        },
    )


class SearXNGAdapter(BaseAdapter):
    """Search a configured SearXNG instance through its JSON API."""

    channel = "searxng"
    operations = ("search",)

    def search(self, query: str, limit: int = 10) -> CollectionResult:
        started_at = time.perf_counter()
        base_url = self.config.get("searxng_base_url")
        if not base_url:
            return self.error_result(
                "search",
                code="missing_configuration",
                message=(
                    "SearXNG base URL is not configured. "
                    "Run agent-reach configure searxng-base-url <INSTANCE_URL>"
                ),
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        requests = _import_requests()
        try:
            response = requests.get(
                f"{base_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "pageno": "1",
                },
                headers={"User-Agent": _UA, "Accept": "application/json"},
                timeout=30,
            )
        except requests.RequestException as exc:
            return self.error_result(
                "search",
                code="http_error",
                message=f"SearXNG search failed: {exc}",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at, base_url=base_url),
            )

        if response.status_code >= 400:
            return self.error_result(
                "search",
                code="http_error",
                message=f"SearXNG search returned HTTP {response.status_code}",
                raw=response.text,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at, base_url=base_url),
            )

        try:
            raw = response.json()
        except ValueError:
            return self.error_result(
                "search",
                code="invalid_response",
                message=(
                    "SearXNG returned a non-JSON payload. "
                    "This instance may not have format=json enabled."
                ),
                raw=response.text,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at, base_url=base_url),
            )

        if not isinstance(raw, dict):
            return self.error_result(
                "search",
                code="invalid_response",
                message="SearXNG search payload was not a JSON object",
                raw=raw,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at, base_url=base_url),
            )

        entries = raw.get("results")
        if not isinstance(entries, list):
            return self.error_result(
                "search",
                code="invalid_response",
                message="SearXNG search payload did not include a results list",
                raw=raw,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at, base_url=base_url),
            )

        items = [_result_item(entry, idx) for idx, entry in enumerate(entries[:limit]) if isinstance(entry, dict)]
        return self.ok_result(
            "search",
            items=items,
            raw=raw,
            meta=self.make_meta(
                value=query,
                limit=limit,
                started_at=started_at,
                base_url=base_url,
                result_count=len(entries),
                **build_pagination_meta(
                    limit=limit,
                    page_size=len(entries),
                    pages_fetched=1,
                    has_more=True if len(entries) > len(items) else None,
                ),
            ),
        )
