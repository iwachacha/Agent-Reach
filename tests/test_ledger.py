# -*- coding: utf-8 -*-
"""Tests for evidence ledger JSONL helpers."""

import json

import pytest

from agent_reach.ledger import (
    append_ledger_record,
    build_ledger_record,
    default_run_id,
    ledger_input_paths,
    merge_ledger_inputs,
    save_collection_result,
    save_collection_result_sharded,
    shard_ledger_path,
)
from agent_reach.results import build_error, build_item, build_result


def _success_result():
    item = build_item(
        item_id="item-1",
        kind="page",
        title="Example",
        url="https://example.com",
        text="hello",
        author="alice",
        published_at="2026-04-10T00:00:00Z",
        source="web",
    )
    return build_result(
        ok=True,
        channel="web",
        operation="read",
        items=[item],
        raw={"ok": True},
        meta={"input": "https://example.com"},
        error=None,
    )


def _error_result():
    return build_result(
        ok=False,
        channel="github",
        operation="read",
        raw=None,
        meta={"input": "missing"},
        error=build_error(
            code="unknown_channel",
            message="Unknown channel",
            details={},
        ),
    )


def test_build_ledger_record_success_shape():
    payload = _success_result()
    record = build_ledger_record(payload, run_id="run-1", input_value="example.com")

    assert record["schema_version"]
    assert record["record_type"] == "collection_result"
    assert record["run_id"] == "run-1"
    assert record["channel"] == "web"
    assert record["operation"] == "read"
    assert record["input"] == "example.com"
    assert record["ok"] is True
    assert record["count"] == 1
    assert record["item_ids"] == ["item-1"]
    assert record["urls"] == ["https://example.com"]
    assert record["error_code"] is None
    assert record["result"] == payload


def test_build_ledger_record_preserves_relevance_metadata():
    payload = _success_result()
    record = build_ledger_record(
        payload,
        run_id="run-1",
        intent="official_docs",
        query_id="q01",
        source_role="web_discovery",
    )

    assert record["intent"] == "official_docs"
    assert record["query_id"] == "q01"
    assert record["source_role"] == "web_discovery"


def test_build_ledger_record_error_shape():
    payload = _error_result()
    record = build_ledger_record(payload, run_id="run-2")

    assert record["run_id"] == "run-2"
    assert record["input"] == "missing"
    assert record["ok"] is False
    assert record["count"] == 0
    assert record["item_ids"] == []
    assert record["urls"] == []
    assert record["error_code"] == "unknown_channel"
    assert record["result"] == payload


def test_append_ledger_record_writes_jsonl(tmp_path):
    path = tmp_path / ".agent-reach" / "evidence.jsonl"
    first = build_ledger_record(_success_result(), run_id="run-1")
    second = build_ledger_record(_error_result(), run_id="run-1")

    append_ledger_record(path, first)
    append_ledger_record(path, second)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["ok"] is True
    assert json.loads(lines[1])["error_code"] == "unknown_channel"


def test_save_collection_result_surfaces_invalid_path(tmp_path):
    directory_path = tmp_path / "already-a-directory"
    directory_path.mkdir()

    with pytest.raises(OSError):
        save_collection_result(directory_path, _success_result(), run_id="run-1")


def test_default_run_id_prefers_environment(monkeypatch):
    monkeypatch.setenv("AGENT_REACH_RUN_ID", "configured-run")

    assert default_run_id() == "configured-run"


def test_default_run_id_falls_back_to_timestamp(monkeypatch):
    monkeypatch.delenv("AGENT_REACH_RUN_ID", raising=False)

    assert default_run_id().startswith("run-")


def test_shard_ledger_path_uses_requested_strategy(tmp_path):
    assert shard_ledger_path(tmp_path, channel="web", operation="read", shard_by="channel").name == "web.jsonl"
    assert shard_ledger_path(tmp_path, channel="web", operation="read", shard_by="operation").name == "read.jsonl"
    assert shard_ledger_path(tmp_path, channel="web", operation="read", shard_by="channel-operation").name == "web__read.jsonl"


def test_save_collection_result_sharded_writes_expected_file(tmp_path):
    record, shard_path = save_collection_result_sharded(
        tmp_path / "ledger",
        _success_result(),
        run_id="run-3",
        shard_by="channel-operation",
    )

    assert record["run_id"] == "run-3"
    assert shard_path.name == "web__read.jsonl"
    assert shard_path.exists()


def test_ledger_input_paths_reads_directory(tmp_path):
    source_dir = tmp_path / "ledger"
    source_dir.mkdir()
    (source_dir / "web.jsonl").write_text("{}", encoding="utf-8")
    (source_dir / "rss.jsonl").write_text("{}", encoding="utf-8")

    paths = ledger_input_paths(source_dir)

    assert [path.name for path in paths] == ["rss.jsonl", "web.jsonl"]


def test_merge_ledger_inputs_combines_shards(tmp_path):
    source_dir = tmp_path / "ledger"
    source_dir.mkdir()
    (source_dir / "web.jsonl").write_text('{"record_type":"collection_result","id":"1"}\n', encoding="utf-8")
    (source_dir / "rss.jsonl").write_text('{"record_type":"collection_result","id":"2"}\n', encoding="utf-8")

    payload = merge_ledger_inputs(source_dir, tmp_path / "merged.jsonl")

    assert payload["files_merged"] == 2
    assert payload["records_written"] == 2
    assert payload["inputs"][0].endswith("rss.jsonl")
