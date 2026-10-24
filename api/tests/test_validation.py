"""Coherence checks against the LILAS filings (skipped when fixtures are absent)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.extraction.pdf import extract_values
from app.validation import extraction_digest, validate

DATA = Path(__file__).resolve().parents[2] / "data" / "lilas"
YEARS = (2021, 2022, 2023, 2024, 2025)
CHECK_IDS = (
    "actif_egal_passif",
    "somme_actif",
    "somme_passif",
    "ebit_recalcule",
    "ebt_recalcule",
    "resultat_net_recalcule",
    "coherence_tresorerie",
)


@pytest.fixture(scope="module")
def items_by_year() -> dict[int, list[dict]]:
    result: dict[int, list[dict]] = {}
    for year in YEARS:
        path = DATA / f"LILAS {year}.pdf"
        if not path.exists():
            pytest.skip(f"missing fixture {path}")
        result[year] = extract_values(path, year)
    return result


def _values(items: list[dict]) -> dict[str, int]:
    return {item["line_item"]: item["value"] for item in items}


def test_all_years_pass(items_by_year):
    for year, items in items_by_year.items():
        result = validate(_values(items))
        assert result["verdict"] == "pass", (year, result["checks"])
        assert [check["id"] for check in result["checks"]] == list(CHECK_IDS)
        assert all(check["status"] == "pass" for check in result["checks"])


def test_one_dinar_tolerance(items_by_year):
    values = _values(items_by_year[2025])
    values["total_actif"] += 1
    result = validate(values)
    assert result["verdict"] == "pass"


def test_balance_mutation_fails(items_by_year):
    values = _values(items_by_year[2025])
    values["total_actif"] += 1_000_000
    result = validate(values)
    checks = {check["id"]: check for check in result["checks"]}
    assert checks["actif_egal_passif"]["status"] == "fail"
    assert checks["somme_actif"]["status"] == "fail"
    assert result["verdict"] == "fail"


def test_missing_item_fails(items_by_year):
    values = _values(items_by_year[2025])
    del values["total_actif"]
    result = validate(values)
    checks = {check["id"]: check for check in result["checks"]}
    assert checks["actif_egal_passif"]["status"] == "fail"
    assert "manquant" in checks["actif_egal_passif"]["detail"]
    assert result["verdict"] == "fail"


def test_extraction_digest_stable_and_sensitive():
    items = [
        {
            "line_item": "chiffre_affaires",
            "value": 1000,
            "page": 3,
            "confidence": 0.9,
        },
        {
            "line_item": "resultat_exploitation",
            "value": 100,
            "page": 3,
            "confidence": 0.9,
        },
    ]
    assert extraction_digest(items) == extraction_digest(list(reversed(items)))
    changed = [dict(item) for item in items]
    changed[0]["value"] = 1001
    assert extraction_digest(changed) != extraction_digest(items)
