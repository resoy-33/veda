"""Step 4 acceptance: write a 4-event chain + NFT, then verify from Hedera."""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from .core.canonical import canonical_json, sha256_hex
from .core.messages import GENESIS_HASH, build_message, message_hash
from .hedera.client import HederaService
from .verifier import verify_filing


def main() -> int:
    service = HederaService()
    filing_id = str(uuid4())
    doc_sha = sha256_hex("demo filing pdf")
    extraction_sha = sha256_hex("demo extraction")
    ratios_sha = sha256_hex("demo ratios")
    report_sha = sha256_hex("demo report")

    topic_id = service.create_topic("veda-selftest")
    print(f"[ok] topic {topic_id}")

    prev = GENESIS_HASH
    plan = [
        (
            "filing_submitted",
            "issuer",
            {
                "issuer": "SAH",
                "period": "2025-12-31",
                "doc_sha256": doc_sha,
                "mime": "application/pdf",
                "pages": 1,
                "source_url": None,
            },
        ),
        (
            "extracted",
            "agent",
            {
                "extraction_sha256": extraction_sha,
                "model": "selftest",
                "line_count": 1,
                "grounded_verified": 1,
                "grounded_total": 1,
            },
        ),
        (
            "validated",
            "agent",
            {
                "extraction_sha256": extraction_sha,
                "ratios_sha256": ratios_sha,
                "verdict": "pass",
                "checks": [{"id": "selftest", "status": "pass", "detail": "ok"}],
            },
        ),
    ]

    for event, role, payload in plan:
        message = build_message(
            event=event,
            filing_id=filing_id,
            actor=service.operator_id,
            role=role,
            sector="industrial",
            payload=payload,
            prev_hash=prev,
        )
        result = service.submit_message(topic_id, message)
        prev = message_hash(message)
        print(f"[ok] {event} -> sequence {result['sequence']}")

    file_payload = {
        "name": "Dépôt vérifié — SAH 2025",
        "description": "Selftest Step 4",
        "type": "application/json",
        "properties": {
            "issuer": "SAH",
            "period": "2025-12-31",
            "sector": "industrial",
            "doc_sha256": doc_sha,
            "extraction_sha256": extraction_sha,
            "ratios_sha256": ratios_sha,
            "validation_verdict": "pass",
            "hcs_topic_id": topic_id,
            "hcs_sequence_range": [1, 4],
            "model": "selftest",
            "created_at": "2026-10-21T18:00:00Z",
        },
    }
    file_id = service.create_file(canonical_json(file_payload).encode("utf-8"))
    print(f"[ok] metadata file {file_id}")

    token_id = service.create_nft_collection()
    print(f"[ok] token {token_id}")
    serial = service.mint_nft(token_id, file_id.encode("utf-8"))
    print(f"[ok] serial {serial}")

    sealed = build_message(
        event="sealed",
        filing_id=filing_id,
        actor=service.operator_id,
        role="agent",
        sector="industrial",
        payload={
            "report_sha256": report_sha,
            "credential": {
                "token_id": token_id,
                "serial": serial,
                "metadata_file_id": file_id,
            },
        },
        prev_hash=prev,
    )
    result = service.submit_message(topic_id, sealed)
    print(f"[ok] sealed -> sequence {result['sequence']}")

    print("[..] verifying from Hedera (mirror + file)...")
    report = verify_filing(topic_id, token_id, serial)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    out = Path("spike/step4_result.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "topic_id": topic_id,
                "token_id": token_id,
                "serial": serial,
                "file_id": file_id,
                "verified": report["verified"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[done] verified={report['verified']} -> {out}")
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
