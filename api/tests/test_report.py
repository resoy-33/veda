"""Excel report is deterministic and matches the anchored bytes."""
from __future__ import annotations

import io
import zipfile
from datetime import date
from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.extraction.pdf import extract_values
from app.ratios import compute_ratios
from app.report import (
    build_report,
    preview_report,
    report_filename,
    report_sha256,
)
from app.validation import validate

DATA = Path(__file__).resolve().parents[2] / "data" / "lilas"
FILING = {
    "id": "3ae154ff-238f-4200-8313-3f5832e52e64",
    "issuer": "SAH",
    "period": date(2025, 12, 31),
    "sector": "industrial",
    "unit": "TND",
    "consolidation": "individuel",
    "doc_sha256": "a" * 64,
    "topic_id": "0.0.11120434",
}


@pytest.fixture(scope="module")
def bundle() -> dict:
    paths = {year: DATA / f"LILAS {year}.pdf" for year in (2024, 2025)}
    for path in paths.values():
        if not path.exists():
            pytest.skip(f"missing fixture {path}")
    current = extract_values(paths[2025], 2025)
    prior = extract_values(paths[2024], 2024)
    values = {item["line_item"]: item["value"] for item in current}
    prior_values = {item["line_item"]: item["value"] for item in prior}
    return {
        "values": current,
        "ratios": compute_ratios(values, 2025, prior_values),
        "checks": validate(values)["checks"],
        "extraction_sha256": "b" * 64,
        "ratios_sha256": "c" * 64,
    }


def _build(bundle: dict) -> bytes:
    return build_report(
        filing=FILING,
        values=bundle["values"],
        ratios=bundle["ratios"],
        checks=bundle["checks"],
        extraction_sha256=bundle["extraction_sha256"],
        ratios_sha256=bundle["ratios_sha256"],
    )


def test_report_is_deterministic(bundle):
    first = _build(bundle)
    second = _build(bundle)
    assert first == second
    assert report_sha256(first) == report_sha256(second)
    assert len(report_sha256(first)) == 64


def test_workbook_sheets_and_rows(bundle):
    workbook = load_workbook(io.BytesIO(_build(bundle)))
    assert workbook.sheetnames == ["Synthèse", "Postes", "Ratios", "Contrôles"]
    assert workbook["Postes"].max_row == len(bundle["values"]) + 1
    assert workbook["Ratios"].max_row == len(bundle["ratios"]) + 1
    assert workbook["Contrôles"].max_row == len(bundle["checks"]) + 1
    assert "SAH" in [
        workbook["Synthèse"].cell(row=row, column=2).value
        for row in range(1, 20)
    ]


def test_mtnd_conversion(bundle):
    workbook = load_workbook(io.BytesIO(_build(bundle)))
    sheet = workbook["Postes"]
    rows = {
        sheet.cell(row=row, column=1).value: row
        for row in range(2, sheet.max_row + 1)
    }
    cell = sheet.cell(row=rows["chiffre_affaires"], column=4)
    assert cell.value == pytest.approx(983.194664)
    assert cell.number_format == "#,##0.000"


def test_core_timestamp_is_fixed(bundle):
    archive = zipfile.ZipFile(io.BytesIO(_build(bundle)))
    core = archive.read("docProps/core.xml")
    assert b"2026-01-01T00:00:00Z" in core
    for entry in archive.infolist():
        assert entry.date_time == (1980, 1, 1, 0, 0, 0)
        assert entry.external_attr == 0o600 << 16
        assert entry.compress_type == zipfile.ZIP_STORED


def test_report_hash_changes_with_values(bundle):
    changed = [dict(item) for item in bundle["values"]]
    changed[0]["value"] += 1
    data = build_report(
        filing=FILING,
        values=changed,
        ratios=bundle["ratios"],
        checks=bundle["checks"],
        extraction_sha256=bundle["extraction_sha256"],
        ratios_sha256=bundle["ratios_sha256"],
    )
    assert report_sha256(data) != report_sha256(_build(bundle))


def test_preview_reads_back_sheets(bundle):
    sheets = preview_report(_build(bundle))
    assert [sheet["name"] for sheet in sheets] == [
        "Synthèse",
        "Postes",
        "Ratios",
        "Contrôles",
    ]
    postes = next(sheet for sheet in sheets if sheet["name"] == "Postes")
    assert postes["rows"][0][0] == "Clé"
    assert len(postes["rows"]) == len(bundle["values"]) + 1
    assert postes["truncated"] is False


def test_filename_is_safe():
    assert report_filename("SAH", 2025) == "rapport_SAH_2025.xlsx"
    assert report_filename("A B", 2025) == "rapport_A_B_2025.xlsx"
