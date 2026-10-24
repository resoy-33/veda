"""Payload contract tests (offline)."""
from __future__ import annotations

from app.core.canonical import sha256_bytes
from app.core.payloads import filing_submitted_payload


def test_filing_submitted_payload_matches_contract():
    payload = filing_submitted_payload(
        issuer="SAH",
        period="2025-12-31",
        doc_sha256="a" * 64,
        mime="application/pdf",
        pages=65,
    )
    assert payload == {
        "issuer": "SAH",
        "period": "2025-12-31",
        "doc_sha256": "a" * 64,
        "mime": "application/pdf",
        "pages": 65,
        "source_url": None,
    }


def test_source_url_is_optional():
    payload = filing_submitted_payload(
        issuer="SAH",
        period="2025-12-31",
        doc_sha256="b" * 64,
        mime="application/pdf",
        pages=1,
        source_url="https://example.test/f.pdf",
    )
    assert payload["source_url"] == "https://example.test/f.pdf"


def test_sha256_bytes_is_stable():
    assert sha256_bytes(b"veda") == sha256_bytes(b"veda")
    assert sha256_bytes(b"veda") != sha256_bytes(b"veda ")
    assert len(sha256_bytes(b"veda")) == 64
