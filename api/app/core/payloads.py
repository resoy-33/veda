"""Event payload builders (contracts v1.0, section 1.2)."""
from __future__ import annotations


def filing_submitted_payload(
    *,
    issuer: str,
    period: str,
    doc_sha256: str,
    mime: str,
    pages: int,
    source_url: str | None = None,
) -> dict:
    return {
        "issuer": issuer,
        "period": period,
        "doc_sha256": doc_sha256,
        "mime": mime,
        "pages": pages,
        "source_url": source_url,
    }


def extracted_payload(
    *,
    extraction_sha256: str,
    model: str,
    line_count: int,
    grounded_verified: int,
    grounded_total: int,
) -> dict:
    return {
        "extraction_sha256": extraction_sha256,
        "model": model,
        "line_count": line_count,
        "grounded_verified": grounded_verified,
        "grounded_total": grounded_total,
    }


def validated_payload(
    *,
    extraction_sha256: str,
    ratios_sha256: str,
    verdict: str,
    checks: list[dict],
) -> dict:
    return {
        "extraction_sha256": extraction_sha256,
        "ratios_sha256": ratios_sha256,
        "verdict": verdict,
        "checks": checks,
    }


def sealed_payload(
    *,
    report_sha256: str,
    token_id: str,
    serial: int,
    metadata_file_id: str,
) -> dict:
    return {
        "report_sha256": report_sha256,
        "credential": {
            "token_id": token_id,
            "serial": serial,
            "metadata_file_id": metadata_file_id,
        },
    }
