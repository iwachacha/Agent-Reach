# -*- coding: utf-8 -*-
"""External-facing collection adapters."""

from __future__ import annotations

from typing import Type

from agent_reach.config import Config

from .base import BaseAdapter
from .bluesky import BlueskyAdapter
from .exa_search import ExaSearchAdapter
from .github import GitHubAdapter
from .hatena_bookmark import HatenaBookmarkAdapter
from .qiita import QiitaAdapter
from .rss import RSSAdapter
from .twitter import TwitterAdapter
from .web import WebAdapter
from .youtube import YouTubeAdapter

ADAPTERS: dict[str, Type[BaseAdapter]] = {
    "bluesky": BlueskyAdapter,
    "web": WebAdapter,
    "exa_search": ExaSearchAdapter,
    "github": GitHubAdapter,
    "hatena_bookmark": HatenaBookmarkAdapter,
    "qiita": QiitaAdapter,
    "youtube": YouTubeAdapter,
    "rss": RSSAdapter,
    "twitter": TwitterAdapter,
}


def get_adapter(name: str, config: Config | None = None) -> BaseAdapter | None:
    """Return a configured adapter for the requested channel."""

    adapter_cls = ADAPTERS.get(name)
    if adapter_cls is None:
        return None
    return adapter_cls(config=config)


__all__ = [
    "ADAPTERS",
    "BaseAdapter",
    "BlueskyAdapter",
    "ExaSearchAdapter",
    "GitHubAdapter",
    "HatenaBookmarkAdapter",
    "QiitaAdapter",
    "RSSAdapter",
    "TwitterAdapter",
    "WebAdapter",
    "YouTubeAdapter",
    "get_adapter",
]
