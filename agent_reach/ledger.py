# -*- coding: utf-8 -*-
"""Evidence ledger helpers for collection runs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TypedDict

from agent_reach.results import CollectionResult
from agent_reach.schemas import SCHEMA_VERSION, utc_timestamp


class EvidenceLedgerRecord(TypedDict):
    """A JSONL record preserving one collection result envelope."""

    schema_version: str
    record_type: str
    run_id: str
    created_at: str
    channel: str
    operation: str
    input: str | None
    ok: bool
    count: int
    item_ids: list[str]
    urls: list[str]
    error_code: str | None
    result: CollectionResult


def default_run_id() -> str:
    """Return the run ID for this command invocation."""

    configured = os.environ.get("AGENT_REACH_RUN_ID")
    if configured:
        return configured
    return f"run-{utc_timestamp().replace(':', '').replace('-', '')}"


def build_ledger_record(
    result: CollectionResult,
    *,
    run_id: str,
    input_value: str | None = None,
) -> EvidenceLedgerRecord:
    """Build a compact ledger record around a full collection result."""

    items = result.get("items") or []
    error = result.get("error")
    meta = result.get("meta") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "collection_result",
        "run_id": run_id,
        "created_at": utc_timestamp(),
        "channel": result["channel"],
        "operation": result["operation"],
        "input": input_value if input_value is not None else meta.get("input"),
        "ok": bool(result["ok"]),
        "count": int(meta.get("count", len(items)) or 0),
        "item_ids": [str(item.get("id")) for item in items if item.get("id")],
        "urls": [str(item.get("url")) for item in items if item.get("url")],
        "error_code": error["code"] if error else None,
        "result": result,
    }


def append_ledger_record(path: str | Path, record: EvidenceLedgerRecord) -> None:
    """Append a ledger record as JSON Lines, creating parent directories."""

    ledger_path = Path(path)
    if ledger_path.parent != Path("."):
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False))
        handle.write("\n")


def save_collection_result(
    path: str | Path,
    result: CollectionResult,
    *,
    run_id: str,
    input_value: str | None = None,
) -> EvidenceLedgerRecord:
    """Build and append a collection result ledger record."""

    record = build_ledger_record(result, run_id=run_id, input_value=input_value)
    append_ledger_record(path, record)
    return record
