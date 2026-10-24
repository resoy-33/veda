"""HCS envelope and hash chain."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .canonical import canonical_json, sha256_hex

GENESIS_HASH = "0" * 64
SCHEMA_VERSION = "1.0"
EVENT_ORDER = ("filing_submitted", "extracted", "validated", "sealed")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_message(
    *,
    event: str,
    filing_id: str,
    actor: str,
    role: str,
    sector: str,
    payload: dict,
    prev_hash: str = GENESIS_HASH,
    event_id: str | None = None,
    ts: str | None = None,
    version: str = SCHEMA_VERSION,
) -> dict:
    if event not in EVENT_ORDER:
        raise ValueError(f"unknown event: {event}")
    return {
        "v": version,
        "event_id": event_id or str(uuid4()),
        "filing_id": filing_id,
        "event": event,
        "actor": actor,
        "role": role,
        "sector": sector,
        "ts": ts or _utc_now(),
        "prev_hash": prev_hash,
        "payload": payload,
    }


def message_hash(message: dict) -> str:
    """Hash of the canonical JSON of a full message (no self-reference)."""
    return sha256_hex(canonical_json(message))


def event_index(event: str) -> int:
    return EVENT_ORDER.index(event)
