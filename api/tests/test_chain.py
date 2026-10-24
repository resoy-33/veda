"""Offline tests for the hash chain and verifier (no network, no model)."""
from __future__ import annotations

import copy

from app.core.canonical import canonical_json
from app.core.messages import GENESIS_HASH, build_message, message_hash
from app.verifier import verify_messages


def _chain() -> list[dict]:
    prev = GENESIS_HASH
    messages: list[dict] = []
    plan = [
        ("filing_submitted", "issuer", {"doc_sha256": "a" * 64}),
        ("extracted", "agent", {"extraction_sha256": "b" * 64}),
        ("validated", "agent", {"verdict": "pass"}),
        ("sealed", "agent", {"report_sha256": "c" * 64}),
    ]
    for event, role, payload in plan:
        message = build_message(
            event=event,
            filing_id="filing-1",
            actor="0.0.1",
            role=role,
            sector="industrial",
            payload=payload,
            prev_hash=prev,
            event_id=f"event-{event}",
            ts="2026-01-01T00:00:00Z",
        )
        messages.append({"message": message})
        prev = message_hash(message)
    return messages


def test_canonical_json_is_stable():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_valid_chain_passes():
    checks = verify_messages(_chain())
    assert all(check["status"] == "pass" for check in checks)


def test_tampering_breaks_the_chain():
    tampered = copy.deepcopy(_chain())
    tampered[1]["message"]["payload"]["extraction_sha256"] = "0" * 64
    checks = verify_messages(tampered)
    assert any(
        check["check"] == "hash_chain" and check["status"] == "fail"
        for check in checks
    )


def test_wrong_order_fails():
    messages = _chain()
    messages[1], messages[2] = messages[2], messages[1]
    checks = verify_messages(messages)
    assert any(
        check["check"] == "event_order" and check["status"] == "fail"
        for check in checks
    )
