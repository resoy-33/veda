"""Sealed credential metadata stored in Hedera File Service."""
from __future__ import annotations

import json

from .core.canonical import canonical_json

MAX_HFS_BYTES = 4096


def compact_values(values: list[dict]) -> list[dict]:
    return [
        {
            "k": row["line_item"],
            "v": int(row["value"]),
            "p": int(row.get("page", 0)),
            "c": round(float(row.get("confidence", 1.0)), 3),
        }
        for row in sorted(values, key=lambda item: item["line_item"])
    ]


def build_hfs_metadata(
    *,
    issuer: str,
    period: str,
    sector: str,
    unit: str,
    doc_sha256: str,
    extraction_sha256: str,
    ratios_sha256: str,
    report_sha256: str,
    verdict: str,
    topic_id: str,
    sequence_range: list[int],
    model: str,
    created_at: str,
    values: list[dict],
) -> dict:
    year = period[:4]
    return {
        "name": f"Dépôt vérifié — {issuer} {year}",
        "description": (
            "États financiers vérifiés et scellés par l'agent d'intégrité."
        ),
        "type": "application/json",
        "properties": {
            "issuer": issuer,
            "period": period,
            "sector": sector,
            "unit": unit,
            "doc_sha256": doc_sha256,
            "extraction_sha256": extraction_sha256,
            "ratios_sha256": ratios_sha256,
            "report_sha256": report_sha256,
            "validation_verdict": verdict,
            "hcs_topic_id": topic_id,
            "hcs_sequence_range": sequence_range,
            "model": model,
            "created_at": created_at,
            "values": compact_values(values),
        },
    }


def hfs_bytes(metadata: dict) -> bytes:
    data = canonical_json(metadata).encode("utf-8")
    if len(data) > MAX_HFS_BYTES:
        raise ValueError(f"HFS metadata is {len(data)} bytes (max {MAX_HFS_BYTES})")
    return data


def values_from_metadata(metadata: dict) -> list[dict]:
    properties = metadata.get("properties", {})
    period = properties.get("period", "")
    unit = properties.get("unit", "TND")
    return [
        {
            "line_item": item["k"],
            "value": int(item["v"]),
            "page": int(item.get("p", 0)),
            "confidence": float(item.get("c", 1.0)),
            "period": period,
            "unit": unit,
        }
        for item in properties.get("values", [])
    ]


def metadata_size(metadata: dict) -> int:
    return len(json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
