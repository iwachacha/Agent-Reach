# -*- coding: utf-8 -*-
"""Bluesky collection adapter."""

from __future__ import annotations

import time
import warnings
from urllib.parse import urlencode

from agent_reach.results import (
    CollectionResult,
    NormalizedItem,
    build_item,
    derive_title_from_text,
    parse_timestamp,
)

from .base import BaseAdapter

_UA = "agent-reach/1.4.0 (+https://github.com/iwachacha/Agent-Reach)"
_SEARCH_HOSTS = (
    "https://public.api.bsky.app",
    "https://api.bsky.app",
)


def _import_requests():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 .* doesn't match a supported version!",
        )
        import requests

    return requests


def _post_url(post: dict) -> str | None:
    author = post.get("author") or {}
    handle = author.get("handle")
    uri = post.get("uri") or ""
    rkey = uri.rstrip("/").split("/")[-1] if uri else None
    if handle and rkey:
        return f"https://bsky.app/profile/{handle}/post/{rkey}"
    return None


class BlueskyAdapter(BaseAdapter):
    """Search public Bluesky posts through the AppView API."""

    channel = "bluesky"
    operations = ("search",)

    def search(self, query: str, limit: int = 10) -> CollectionResult:
        started_at = time.perf_counter()
        requests = _import_requests()
        params = {"q": query, "limit": str(limit)}
        headers = {"User-Agent": _UA, "Accept": "application/json"}
        last_error: tuple[str, str, object | None] | None = None

        for base_url in _SEARCH_HOSTS:
            url = f"{base_url}/xrpc/app.bsky.feed.searchPosts?{urlencode(params)}"
            try:
                response = requests.get(url, headers=headers, timeout=30)
            except requests.RequestException as exc:
                last_error = ("http_error", f"Bluesky search failed: {exc}", None)
                continue

            raw_text = response.text
            if response.status_code >= 400:
                last_error = (
                    "http_error",
                    f"Bluesky search returned HTTP {response.status_code}",
                    raw_text,
                )
                continue

            try:
                raw = response.json()
            except ValueError:
                last_error = (
                    "invalid_response",
                    "Bluesky search returned a non-JSON payload",
                    raw_text,
                )
                continue

            posts = raw.get("posts")
            if not isinstance(posts, list):
                return self.error_result(
                    "search",
                    code="invalid_response",
                    message="Bluesky search payload did not include a posts list",
                    raw=raw,
                    meta=self.make_meta(
                        value=query,
                        limit=limit,
                        started_at=started_at,
                        api_base_url=base_url,
                    ),
                )

            items: list[NormalizedItem] = []
            for idx, post in enumerate(posts):
                author = post.get("author") or {}
                record = post.get("record") or {}
                external = ((post.get("embed") or {}).get("external") or {})
                title = derive_title_from_text(
                    record.get("text"),
                    fallback=external.get("title") or f"Bluesky post {idx + 1}",
                )
                items.append(
                    build_item(
                        item_id=post.get("uri") or post.get("cid") or f"bluesky-{idx}",
                        kind="post",
                        title=title,
                        url=_post_url(post),
                        text=record.get("text"),
                        author=author.get("handle"),
                        published_at=parse_timestamp(record.get("createdAt") or post.get("indexedAt")),
                        source=self.channel,
                        extras={
                            "author_display_name": author.get("displayName"),
                            "like_count": post.get("likeCount"),
                            "reply_count": post.get("replyCount"),
                            "repost_count": post.get("repostCount"),
                            "quote_count": post.get("quoteCount"),
                            "bookmark_count": post.get("bookmarkCount"),
                            "labels": post.get("labels") or [],
                            "external_uri": external.get("uri"),
                            "external_title": external.get("title"),
                        },
                    )
                )

            return self.ok_result(
                "search",
                items=items,
                raw=raw,
                meta=self.make_meta(
                    value=query,
                    limit=limit,
                    started_at=started_at,
                    api_base_url=base_url,
                ),
            )

        if last_error is None:
            return self.error_result(
                "search",
                code="http_error",
                message="Bluesky search failed before any request could complete",
                meta=self.make_meta(value=query, limit=limit, started_at=started_at),
            )

        code, message, raw = last_error
        return self.error_result(
            "search",
            code=code,
            message=message,
            raw=raw,
            meta=self.make_meta(value=query, limit=limit, started_at=started_at),
        )
