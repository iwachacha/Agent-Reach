# -*- coding: utf-8 -*-
"""Registry of channels supported by the Windows/Codex fork."""

from __future__ import annotations

from typing import Dict, List, Optional

from .base import Channel
from .bluesky import BlueskyChannel
from .crawl4ai import Crawl4AIChannel
from .exa_search import ExaSearchChannel
from .github import GitHubChannel
from .hatena_bookmark import HatenaBookmarkChannel
from .qiita import QiitaChannel
from .rss import RSSChannel
from .searxng import SearXNGChannel
from .twitter import TwitterChannel
from .web import WebChannel
from .youtube import YouTubeChannel

ALL_CHANNELS: List[Channel] = [
    WebChannel(),
    ExaSearchChannel(),
    GitHubChannel(),
    HatenaBookmarkChannel(),
    BlueskyChannel(),
    QiitaChannel(),
    YouTubeChannel(),
    RSSChannel(),
    SearXNGChannel(),
    Crawl4AIChannel(),
    TwitterChannel(),
]


def get_channel(name: str) -> Optional[Channel]:
    """Return a channel by its stable name."""

    for channel in ALL_CHANNELS:
        if channel.name == name:
            return channel
    return None


def get_all_channels() -> List[Channel]:
    """Return all registered channels."""

    return ALL_CHANNELS


def get_channel_contract(name: str) -> Optional[dict]:
    """Return a machine-readable contract for one channel."""

    channel = get_channel(name)
    if channel is None:
        return None
    return channel.to_contract()


def get_all_channel_contracts() -> List[dict]:
    """Return channel contracts for all registered channels."""

    return [channel.to_contract() for channel in ALL_CHANNELS]


def get_all_channel_contracts_by_name() -> Dict[str, dict]:
    """Return channel contracts keyed by stable channel name."""

    return {channel.name: channel.to_contract() for channel in ALL_CHANNELS}


__all__ = [
    "Channel",
    "ALL_CHANNELS",
    "get_channel",
    "get_all_channels",
    "get_channel_contract",
    "get_all_channel_contracts",
    "get_all_channel_contracts_by_name",
]
