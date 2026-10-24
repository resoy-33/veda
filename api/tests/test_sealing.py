"""HFS credential metadata: size, hashes and value round-trip."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.extraction.pdf import extract_values
from app.sealing import (
    MAX_HFS_BYTES,
    build_hfs_metadata,
    compact_values,
    hfs_bytes,
    values_from_metadata,
)

DATA = Path(__file__).resolve().parents[2] / "data" / "lilas"


def _metadata(values: list[dict]) -> dict:
    return build_hfs_metadata(
        issuer="SAH",
        period="2025-12-31",
        sector="industrial",
        unit="TND",
        doc_sha256="a" * 64,
        extraction_sha256="b" * 64,
        ratios_sha256="c" * 64,
        report_sha256="d" * 64,
        verdict="pass",
        topic_id="0.0.11120434",
        sequence_range=[1, 4],
        model="deterministic:pymupdf",
        created_at="2026-10-21T18:02:00Z",
        values=values,
    )


@pytest.fixture(scope="module")
def values() -> list[dict]:
    path = DATA / "LILAS 2025.pdf"
    if not path.exists():
        pytest.skip(f"missing fixture {path}")
    return extract_values(path, 2025)


def test_hfs_fits_limit_and_roundtrips(values):
    metadata = _metadata(values)
    data = hfs_bytes(metadata)
    assert len(data) <= MAX_HFS_BYTES
    parsed = json.loads(data)
    properties = parsed["properties"]
    assert properties["validation_verdict"] == "pass"
    assert properties["report_sha256"] == "d" * 64
    assert len(properties["values"]) == len(values)
    restored = values_from_metadata(parsed)
    assert len(restored) == len(values)
    original = {item["line_item"]: item["value"] for item in values}
    assert {item["line_item"]: item["value"] for item in restored} == original


def test_compact_values_are_sorted_and_typed(values):
    compact = compact_values(values)
    assert [item["k"] for item in compact] == sorted(item["k"] for item in compact)
    assert all(isinstance(item["v"], int) for item in compact)
    assert all(0 <= item["c"] <= 1 for item in compact)
    assert all(isinstance(item["p"], int) for item in compact)


def test_oversized_metadata_is_rejected():
    values = [
        {
            "line_item": f"poste_{index}",
            "value": index,
            "page": 1,
            "confidence": 0.9,
        }
        for index in range(200)
    ]
    with pytest.raises(ValueError):
        hfs_bytes(_metadata(values))
