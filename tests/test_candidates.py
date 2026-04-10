# -*- coding: utf-8 -*-
"""Tests for evidence-ledger candidate planning."""

import json

import pytest

from agent_reach.candidates import CandidatePlanError, build_candidates_payload
from agent_reach.ledger import build_ledger_record
from agent_reach.results import build_item, build_result


def _result(channel="web", operation="read", items=None, input_value="query"):
    return build_result(
        ok=True,
        channel=channel,
        operation=operation,
        items=items or [],
        raw={"ok": True},
        meta={"input": input_value},
        error=None,
    )


def _item(item_id, url, title, source="web"):
    return build_item(
        item_id=item_id,
        kind="page",
        title=title,
        url=url,
        text=None,
        author=None,
        published_at=None,
        source=source,
    )


def _write_jsonl(path, records):
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def test_candidates_dedupe_by_canonical_url(tmp_path):
    path = tmp_path / "evidence.jsonl"
    first = _result(
        channel="exa_search",
        operation="search",
        items=[_item("exa-1", "HTTPS://Example.com/post/#section", "First", source="exa_search")],
    )
    second = _result(
        channel="web",
        operation="read",
        items=[_item("web-1", "https://example.com/post", "Second", source="web")],
    )
    _write_jsonl(
        path,
        [
            build_ledger_record(first, run_id="run-1", input_value="topic"),
            build_ledger_record(second, run_id="run-1", input_value="https://example.com/post"),
        ],
    )

    payload = build_candidates_payload(path, by="url", limit=20)

    assert payload["summary"]["candidate_count"] == 1
    assert payload["candidates"][0]["title"] == "First"
    assert payload["candidates"][0]["extras"]["seen_in"] == [
        {
            "run_id": "run-1",
            "channel": "exa_search",
            "operation": "search",
            "input": "topic",
            "item_id": "exa-1",
            "url": "HTTPS://Example.com/post/#section",
        },
        {
            "run_id": "run-1",
            "channel": "web",
            "operation": "read",
            "input": "https://example.com/post",
            "item_id": "web-1",
            "url": "https://example.com/post",
        },
    ]


def test_candidates_fallback_dedupe_by_source_and_id(tmp_path):
    path = tmp_path / "evidence.jsonl"
    first = _result(
        channel="github",
        operation="read",
        items=[_item("openai/openai-python", None, "OpenAI Python", source="github")],
    )
    second = _result(
        channel="github",
        operation="read",
        items=[_item("openai/openai-python", None, "Duplicate", source="github")],
    )
    third = _result(
        channel="rss",
        operation="read",
        items=[_item("openai/openai-python", None, "Different source", source="rss")],
    )
    _write_jsonl(
        path,
        [
            build_ledger_record(first, run_id="run-1"),
            build_ledger_record(second, run_id="run-2"),
            build_ledger_record(third, run_id="run-3"),
        ],
    )

    payload = build_candidates_payload(path, by="url", limit=20)

    assert payload["summary"]["candidate_count"] == 2
    assert payload["candidates"][0]["title"] == "OpenAI Python"
    assert len(payload["candidates"][0]["extras"]["seen_in"]) == 2
    assert payload["candidates"][1]["title"] == "Different source"


def test_candidates_limit_keeps_first_seen_order(tmp_path):
    path = tmp_path / "evidence.jsonl"
    result = _result(
        items=[
            _item("1", "https://example.com/1", "One"),
            _item("2", "https://example.com/2", "Two"),
            _item("3", "https://example.com/3", "Three"),
        ],
    )
    _write_jsonl(path, [build_ledger_record(result, run_id="run-1")])

    payload = build_candidates_payload(path, by="url", limit=2)

    assert payload["summary"]["candidate_count"] == 3
    assert payload["summary"]["returned"] == 2
    assert [candidate["title"] for candidate in payload["candidates"]] == ["One", "Two"]


def test_candidates_invalid_jsonl_reports_error(tmp_path):
    path = tmp_path / "evidence.jsonl"
    path.write_text("{broken\n", encoding="utf-8")

    with pytest.raises(CandidatePlanError):
        build_candidates_payload(path)


def test_candidates_accept_raw_collection_result_jsonl(tmp_path):
    path = tmp_path / "raw-results.jsonl"
    result = _result(items=[_item("raw-1", "https://example.com/raw", "Raw")])
    _write_jsonl(path, [{"record_type": "other"}, result])

    payload = build_candidates_payload(path, by="url", limit=20)

    assert payload["summary"]["records"] == 2
    assert payload["summary"]["collection_results"] == 1
    assert payload["summary"]["skipped_records"] == 1
    assert payload["candidates"][0]["title"] == "Raw"
    assert payload["candidates"][0]["extras"]["seen_in"][0]["run_id"] is None
