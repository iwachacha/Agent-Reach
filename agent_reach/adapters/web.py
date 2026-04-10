# -*- coding: utf-8 -*-
"""Web collection adapter."""

from __future__ import annotations

import re
import time
import warnings
from urllib.parse import urlparse

from agent_reach.results import (
    CollectionResult,
    build_item,
    derive_title_from_text,
    parse_timestamp,
)
from agent_reach.source_hints import web_source_hints

from .base import BaseAdapter

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
_MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)")
_BARE_URL_RE = re.compile(r"(?<!\()https?://[^\s)]+")
_NAV_HEAVY_LINK_THRESHOLD = 25
_NAV_HEAVY_MAX_CHARS_PER_LINK = 120


def _import_requests():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 .* doesn't match a supported version!",
        )
        import requests

    return requests


def _normalize_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else f"https://{url}"


def _extract_reader_metadata(markdown: str) -> tuple[str | None, str | None, str]:
    title_match = re.search(r"^Title:\s*(.+)$", markdown, re.MULTILINE)
    published_match = re.search(r"^Published Time:\s*(.+)$", markdown, re.MULTILINE)
    body_marker = "Markdown Content:"

    title = title_match.group(1).strip() if title_match else None
    published_at = parse_timestamp(published_match.group(1).strip()) if published_match else None
    if body_marker in markdown:
        body = markdown.split(body_marker, 1)[1].strip()
    else:
        body = markdown.strip()
    return title, published_at, body


def _title_from_markdown(url: str, markdown: str, fallback_title: str | None = None) -> str | None:
    if fallback_title:
        return fallback_title
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or derive_title_from_text(markdown, fallback=url)
    parsed = urlparse(url)
    return derive_title_from_text(markdown, fallback=parsed.netloc or url)


def _link_count(markdown: str) -> int:
    return len(_MARKDOWN_LINK_RE.findall(markdown)) + len(_BARE_URL_RE.findall(markdown))


def _extraction_warning(text_length: int, link_count: int) -> str | None:
    if link_count < _NAV_HEAVY_LINK_THRESHOLD:
        return None
    if text_length <= link_count * _NAV_HEAVY_MAX_CHARS_PER_LINK:
        return "navigation_heavy"
    return None


def _web_hygiene_meta(text: str) -> dict[str, int | str | None]:
    link_count = _link_count(text)
    text_length = len(text)
    return {
        "text_length": text_length,
        "link_count": link_count,
        "extraction_warning": _extraction_warning(text_length, link_count),
    }


class WebAdapter(BaseAdapter):
    """Read generic web pages through Jina Reader."""

    channel = "web"
    operations = ("read",)

    def read(self, url: str, limit: int | None = None) -> CollectionResult:
        started_at = time.perf_counter()
        normalized = _normalize_url(url)
        requests = _import_requests()
        try:
            response = requests.get(
                f"https://r.jina.ai/{normalized}",
                headers={"User-Agent": _UA, "Accept": "text/plain"},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return self.error_result(
                "read",
                code="http_error",
                message=f"Web read failed: {exc}",
                meta=self.make_meta(value=normalized, limit=limit, started_at=started_at),
            )

        markdown = response.text
        title, published_at, body = _extract_reader_metadata(markdown)
        hygiene_meta = _web_hygiene_meta(body)
        item = build_item(
            item_id=normalized,
            kind="page",
            title=_title_from_markdown(normalized, body, fallback_title=title),
            url=normalized,
            text=body,
            author=None,
            published_at=published_at,
            source=self.channel,
            extras={
                "reader_url": f"https://r.jina.ai/{normalized}",
                "source_hints": web_source_hints(published_at),
            },
        )
        return self.ok_result(
            "read",
            items=[item],
            raw=markdown,
            meta=self.make_meta(value=normalized, limit=limit, started_at=started_at, **hygiene_meta),
        )
