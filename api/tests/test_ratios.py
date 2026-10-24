"""Ratio engine against the LILAS filings (skipped when fixtures are absent)."""
from __future__ import annotations

from math import isfinite
from pathlib import Path

import pytest

from app.extraction.pdf import extract_values
from app.ratios import LABELS, compute_ratios, ratios_digest

DATA = Path(__file__).resolve().parents[2] / "data" / "lilas"


def _load(year: int) -> dict[str, int]:
    path = DATA / f"LILAS {year}.pdf"
    if not path.exists():
        pytest.skip(f"missing fixture {path}")
    return {item["line_item"]: item["value"] for item in extract_values(path, year)}


@pytest.fixture(scope="module")
def values() -> dict[int, dict[str, int]]:
    return {year: _load(year) for year in (2024, 2025)}


def _rows(year: int, prior: dict | None = None) -> dict[str, dict]:
    data = _load(year)
    return {
        row["code"]: row for row in compute_ratios(data, year, prior or {})
    }


def test_aggregates_2025(values):
    rows = {
        row["code"]: row
        for row in compute_ratios(values[2025], 2025, values[2024])
    }
    expected = {
        "marge_brute": 437012584,
        "ebitda": 175337498,
        "total_dettes": 113704727,
        "dette_nette": 44862425,
        "fonds_roulement": 66787889,
        "bfr_exploitation": 433583645,
        "tresorerie_nette_gestion": 52938087,
        "capitaux_investis": 603830751,
        "free_cash_flow": 48456230,
    }
    assert {code: rows[code]["value"] for code in expected} == expected


def test_margins_liquidity_and_efficiency_2025(values):
    rows = _rows(2025)
    assert rows["marge_brute_pct"]["value"] == pytest.approx(437012584 / 983194664)
    assert rows["marge_exploitation"]["value"] == pytest.approx(114064710 / 983194664)
    assert rows["liquidite_generale"]["value"] == pytest.approx(927250182 / 860462293)
    assert rows["dio"]["value"] == pytest.approx(392559284 / 546182080 * 365)
    assert rows["dso"]["value"] == pytest.approx(340703426 / 983194664 * 365)
    assert rows["ccc"]["value"] == pytest.approx(
        rows["dio"]["value"] + rows["dso"]["value"] - rows["dpo"]["value"]
    )


def test_growth_uses_prior_year(values):
    rows = {
        row["code"]: row
        for row in compute_ratios(values[2025], 2025, values[2024])
    }
    current = values[2025]
    prior = values[2024]
    assert rows["croissance_ca"]["value"] == pytest.approx(
        (current["chiffre_affaires"] - prior["chiffre_affaires"])
        / abs(prior["chiffre_affaires"])
    )
    assert rows["croissance_total_actif"]["value"] == pytest.approx(
        (current["total_actif"] - prior["total_actif"]) / abs(prior["total_actif"])
    )


def test_growth_is_null_without_prior():
    rows = _rows(2021)
    assert rows["croissance_ca"]["value"] is None
    assert rows["roe_moyen"]["value"] is None


def test_market_ratios_are_null_without_market_data():
    rows = _rows(2025)
    assert rows["bpa"]["value"] is None
    assert rows["per"]["value"] is None
    assert rows["valeur_graham"]["value"] is None


def test_labels_and_formula_version():
    rows = compute_ratios(_load(2025), 2025)
    for row in rows:
        assert row["code"] in LABELS
        assert row["name"] == LABELS[row["code"]]
        assert row["year"] == 2025
        assert row["formula_version"] == "1.0"


def test_zero_division_yields_null():
    rows = compute_ratios(
        {
            "chiffre_affaires": 0,
            "cout_des_ventes": 0,
            "total_actif": 0,
            "capitaux_propres_part_groupe": 0,
            "resultat_net_part_groupe": 0,
        },
        2025,
    )
    for row in rows:
        assert row["value"] is None or isfinite(row["value"])


def test_digest_is_stable_and_sensitive():
    rows = compute_ratios(_load(2025), 2025)
    assert ratios_digest(rows) == ratios_digest(rows)
    changed = [dict(row) for row in rows]
    changed[0]["value"] = (changed[0]["value"] or 0) + 1
    assert ratios_digest(changed) != ratios_digest(rows)
