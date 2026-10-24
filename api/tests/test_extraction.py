"""End-to-end extraction against the LILAS filings (skipped when absent)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.extraction.eval import CORE
from app.extraction.pdf import extract_values

DATA = Path(__file__).resolve().parents[2] / "data" / "lilas"
YEARS = (2021, 2022, 2023, 2024, 2025)


def _path(year: int) -> Path:
    return DATA / f"LILAS {year}.pdf"


@pytest.fixture(scope="module")
def values_by_year() -> dict[int, dict[str, dict]]:
    result: dict[int, dict[str, dict]] = {}
    for year in YEARS:
        path = _path(year)
        if not path.exists():
            pytest.skip(f"missing fixture {path}")
        result[year] = {
            item["line_item"]: item for item in extract_values(path, year)
        }
    return result


def _matches(computed: int, expected: int) -> bool:
    return abs(computed - expected) <= max(1, round(abs(expected) * 0.0001))


def test_all_core_items_present(values_by_year):
    for year, values in values_by_year.items():
        missing = set(CORE) - set(values)
        assert not missing, (year, missing)


def test_balance_identity(values_by_year):
    for year, values in values_by_year.items():
        actif = values["total_actif"]["value"]
        passif = values["total_capitaux_propres_et_passifs"]["value"]
        assert actif == passif, year
        assert actif > 0


def test_cash_identity(values_by_year):
    for year, values in values_by_year.items():
        cash = values["liquidites"]["value"]
        overdraft = values["dettes_financieres_courantes"]["value"]
        closing = values["tresorerie_cloture"]["value"]
        assert _matches(cash - overdraft, closing), year


def test_income_identities(values_by_year):
    for year, values in values_by_year.items():
        ebit = (
            values["chiffre_affaires"]["value"]
            + values["autres_produits_exploitation"]["value"]
            + values["variation_stocks"]["value"]
            + values["cout_des_ventes"]["value"]
            + values["charges_personnel"]["value"]
            + values["dotations_amortissements_provisions"]["value"]
            + values["autres_charges_exploitation"]["value"]
        )
        assert _matches(ebit, values["resultat_exploitation"]["value"]), year

        ebt = (
            ebit
            + values["produits_placements"]["value"]
            + values["autres_gains_pertes"]["value"]
            + values["charges_interets"]["value"]
        )
        assert _matches(ebt, values["resultat_avant_impot"]["value"]), year


def test_2025_known_values(values_by_year):
    values = values_by_year[2025]
    expected = {
        "chiffre_affaires": 983194664,
        "charges_personnel": -118082557,
        "variation_stocks": -5854131,
        "resultat_exploitation": 114064710,
        "resultat_net_part_groupe": 63286733,
        "liquidites": 68842302,
        "dettes_financieres_courantes": 15904215,
        "tresorerie_cloture": 52938087,
        "acquisitions_immobilisations": -55433568,
        "total_actif": 1452997177,
    }
    assert {key: values[key]["value"] for key in expected} == expected


def test_2021_three_columns(values_by_year):
    values = values_by_year[2021]
    assert values["total_actif"]["value"] == 1033984914
    assert values["total_actifs_non_courants"]["value"] == 432710822
    assert values["autres_actifs_non_courants"]["value"] == 14309554
    assert values["immobilisations_corporelles"]["value"] == 408262174


def test_2024_angle_bracket_negatives(values_by_year):
    values = values_by_year[2024]
    assert values["cout_des_ventes"]["value"] == -575935735
    assert values["impot_sur_benefices"]["value"] == -4938357
    assert values["variation_stocks"]["value"] == 22886299


def test_metadata(values_by_year):
    for year, values in values_by_year.items():
        for item in values.values():
            assert item["unit"] == "TND"
            assert item["period"] == f"{year}-12-31"
            assert 2 <= item["page"] <= 7
            assert item["confidence"] > 0
            assert item["bbox"]["x1"] > item["bbox"]["x0"]
            assert item["bbox"]["bottom"] > item["bbox"]["top"]


def test_deterministic():
    path = _path(2025)
    if not path.exists():
        pytest.skip(f"missing fixture {path}")
    assert extract_values(path, 2025) == extract_values(path, 2025)
