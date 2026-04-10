# -*- coding: utf-8 -*-
"""Qiita collection adapter."""

from __future__ import annotations

import time
import warnings

from agent_reach.results import CollectionResult, NormalizedItem, build_item, parse_timestamp

from .base import BaseAdapter

_UA = "agent-reach/1.4.0 (+https://github.com/iwachacha/Agent-Reach)"
_ITEMS_API = "https://qiita.com/api/v2/items"


def _import_requests():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 .* doesn't match a supported version!",
        )
        import requests

    return requests


class QiitaAdapter(BaseAdapter):
    """Search public Qiita items through Qiita API v2."""

    channel = "qiita"
    operations = ("search",)

    def search(self, query: str, limit: int = 10) -> CollectionResult:
        started_at = time.perf_counter()
        requests = _import_requests()
        headers = {
            "User-Agent": _UA,
            "Accept": "application/json",
        }
        qiita_token = self.runtime_env().get("QIITA_TOKEN")
        if qiita_token:
            headers["Authorization"] = f"Bearer {qiita_token}"

        try:
            response = requests.get(
                _ITEMS_API,
                params={
                    "query": query,
                    "page": "1",
                    "per_page": str(min(max(limit, 1), 100)),
                },
                headers=headers,
                timeout=30,
            )
        except requests.RequestException as exc:
            return self.error_result(
                "search",
                code="http_error",
                message=f"Qiita search failed: {exc}",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        if response.status_code >= 400:
            return self.error_result(
                "search",
                code="http_error",
                message=f"Qiita search returned HTTP {response.status_code}",
                raw=response.text,
                meta=self.make_meta(
                    value=query,
                    limit=limit,
                    started_at=started_at,
                    total_count=response.headers.get("Total-Count"),
                ),
            )

        try:
            raw = response.json()
        except ValueError:
            return self.error_result(
                "search",
                code="invalid_response",
                message="Qiita search returned a non-JSON payload",
                raw=response.text,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        if not isinstance(raw, list):
            return self.error_result(
                "search",
                code="invalid_response",
                message="Qiita search payload was not a list",
                raw=raw,
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        items: list[NormalizedItem] = [
            build_item(
                item_id=entry.get("id") or f"qiita-{idx}",
                kind="article",
                title=entry.get("title"),
                url=entry.get("url"),
                text=entry.get("body"),
                author=(entry.get("user") or {}).get("id"),
                published_at=parse_timestamp(entry.get("created_at") or entry.get("updated_at")),
                source=self.channel,
                extras={
                    "likes_count": entry.get("likes_count"),
                    "stocks_count": entry.get("stocks_count"),
                    "comments_count": entry.get("comments_count"),
                    "reactions_count": entry.get("reactions_count"),
                    "page_views_count": entry.get("page_views_count"),
                    "private": entry.get("private"),
                    "tags": [tag.get("name") for tag in entry.get("tags") or [] if tag.get("name")],
                    "updated_at": parse_timestamp(entry.get("updated_at")),
                },
            )
            for idx, entry in enumerate(raw)
        ]

        return self.ok_result(
            "search",
            items=items,
            raw=raw,
            meta=self.make_meta(
                value=query,
                limit=limit,
                started_at=started_at,
                total_count=response.headers.get("Total-Count"),
            ),
        )
