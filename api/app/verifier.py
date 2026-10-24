"""Standalone verification: rebuild the proof from Hedera, trust no database."""
from __future__ import annotations

import json

from .core.messages import EVENT_ORDER, GENESIS_HASH, message_hash
from .hedera import mirror


def _check(name: str, ok: bool, detail: str) -> dict:
    return {"check": name, "status": "pass" if ok else "fail", "detail": detail}


def verify_messages(messages: list[dict]) -> list[dict]:
    checks: list[dict] = []
    if not messages:
        return [_check("messages_present", False, "no messages on topic")]

    events = [item["message"] for item in messages]
    checks.append(_check("event_count", len(events) >= 4, f"{len(events)} messages"))

    chain_ok = events[0].get("prev_hash") == GENESIS_HASH
    detail = "genesis ok" if chain_ok else "first prev_hash is not 64 zeros"
    for previous, current in zip(events, events[1:]):
        if current.get("prev_hash") != message_hash(previous):
            chain_ok = False
            detail = f"break before {current.get('event')}: prev_hash mismatch"
            break
    checks.append(_check("hash_chain", chain_ok, detail))

    indexes = [
        EVENT_ORDER.index(item["event"])
        for item in events
        if item.get("event") in EVENT_ORDER
    ]
    order_ok = indexes == list(range(len(indexes)))
    checks.append(
        _check("event_order", order_ok, str([item.get("event") for item in events]))
    )

    filing_ids = {item.get("filing_id") for item in events}
    checks.append(_check("filing_consistency", len(filing_ids) == 1, str(filing_ids)))

    validated = [item for item in events if item.get("event") == "validated"]
    verdict = validated[-1].get("payload", {}).get("verdict") if validated else None
    checks.append(_check("validation_verdict", verdict == "pass", str(verdict)))

    sealed = [item for item in events if item.get("event") == "sealed"]
    checks.append(_check("sealed_event", bool(sealed), "present" if sealed else "missing"))

    return checks


def verify_filing(topic_id: str, token_id: str, serial: int) -> dict:
    checks: list[dict] = []
    evidence: dict = {"topic_id": topic_id, "token_id": token_id, "serial": serial}

    try:
        messages = mirror.topic_messages(topic_id, expected_min=len(EVENT_ORDER))
    except Exception as exc:  # noqa: BLE001
        return {
            "verified": False,
            "checks": [_check("mirror_read", False, str(exc))],
            "evidence": evidence,
        }

    evidence["message_count"] = len(messages)
    checks.extend(verify_messages(messages))

    file_id = None
    try:
        file_id = mirror.nft_metadata_bytes(token_id, serial).decode("utf-8")
        evidence["metadata_file_id"] = file_id
        checks.append(_check("nft_metadata", True, file_id))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("nft_metadata", False, str(exc)))

    file_data = None
    if file_id:
        try:
            from .hedera.client import HederaService

            file_data = json.loads(HederaService().read_file(file_id).decode("utf-8"))
            checks.append(_check("file_read", True, file_id))
        except Exception as exc:  # noqa: BLE001
            checks.append(_check("file_read", False, str(exc)))

    if file_data:
        props = file_data.get("properties", {})
        submitted = [
            item["message"]
            for item in messages
            if item["message"].get("event") == "filing_submitted"
        ]
        extracted = [
            item["message"]
            for item in messages
            if item["message"].get("event") == "extracted"
        ]
        sealed = [
            item["message"]
            for item in messages
            if item["message"].get("event") == "sealed"
        ]
        doc_ok = bool(submitted) and props.get("doc_sha256") == submitted[0].get(
            "payload", {}
        ).get("doc_sha256")
        ext_ok = bool(extracted) and props.get(
            "extraction_sha256"
        ) == extracted[0].get("payload", {}).get("extraction_sha256")
        report_ok = bool(sealed) and props.get("report_sha256") == sealed[0].get(
            "payload", {}
        ).get("report_sha256")
        checks.append(_check("doc_hash_match", doc_ok, str(props.get("doc_sha256"))))
        checks.append(
            _check("extraction_hash_match", ext_ok, str(props.get("extraction_sha256")))
        )
        checks.append(
            _check("report_hash_match", report_ok, str(props.get("report_sha256")))
        )
        checks.append(
            _check("topic_match", props.get("hcs_topic_id") == topic_id, str(props.get("hcs_topic_id")))
        )

    verified = bool(checks) and all(item["status"] == "pass" for item in checks)
    return {"verified": verified, "checks": checks, "evidence": evidence}
