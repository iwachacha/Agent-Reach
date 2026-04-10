# -*- coding: utf-8 -*-
"""RSS collection adapter."""

from __future__ import annotations

import time

import feedparser

from agent_reach.results import (
    CollectionResult,
    NormalizedItem,
    build_item,
    build_pagination_meta,
    parse_timestamp,
)
from agent_reach.source_hints import rss_source_hints

from .base import BaseAdapter


class RSSAdapter(BaseAdapter):
    """Read RSS and Atom feeds through feedparser."""

    channel = "rss"
    operations = ("read",)

    def read(self, url: str, limit: int = 10) -> CollectionResult:
        started_at = time.perf_counter()
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:
            return self.error_result(
                "read",
                code="parse_failed",
                message=f"RSS read failed: {exc}",
                meta=self.make_meta(value=url, limit=limit, started_at=started_at),
            )

        entries = [dict(entry) for entry in parsed.entries[:limit]]
        raw = {
            "feed": dict(parsed.feed),
            "entries": entries,
            "bozo": bool(getattr(parsed, "bozo", False)),
            "status": getattr(parsed, "status", None),
        }
        items: list[NormalizedItem] = []
        for idx, entry in enumerate(entries):
            published_at = parse_timestamp(
                entry.get("published_parsed")
                or entry.get("updated_parsed")
                or entry.get("published")
                or entry.get("updated")
            )
            items.append(
                build_item(
                    item_id=entry.get("id")
                    or entry.get("link")
                    or entry.get("title")
                    or f"rss-{idx}",
                    kind="feed_item",
                    title=entry.get("title"),
                    url=entry.get("link"),
                    text=entry.get("summary") or entry.get("description"),
                    author=entry.get("author"),
                    published_at=published_at,
                    source=self.channel,
                    extras={
                        "feed_title": parsed.feed.get("title"),
                        "source_hints": rss_source_hints(published_at),
                    },
                )
            )
        return self.ok_result(
            "read",
            items=items,
            raw=raw,
            meta=self.make_meta(
                value=url,
                limit=limit,
                started_at=started_at,
                feed_title=parsed.feed.get("title"),
                **build_pagination_meta(
                    limit=limit,
                    page_size=len(getattr(parsed, "entries", [])),
                    pages_fetched=1,
                    has_more=len(getattr(parsed, "entries", [])) > len(entries),
                    total_available=len(getattr(parsed, "entries", [])),
                ),
            ),
        )
