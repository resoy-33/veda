"""Deterministic coherence checks (contracts v1.0, section 8)."""
from __future__ import annotations

from .core.canonical import canonical_json, sha256_hex

TOLERANCE_RATIO = 0.0001


def _fmt(value: float) -> str:
    return f"{value:.0f}"


def _tolerance(expected: float) -> float:
    return max(1.0, abs(expected) * TOLERANCE_RATIO)


def _check(
    check_id: str, actual: float | None, expected: float | None, formula: str
) -> dict:
    if actual is None:
        return {
            "id": check_id,
            "status": "fail",
            "detail": f"poste manquant pour {formula}",
        }
    if expected is None:
        return {
            "id": check_id,
            "status": "fail",
            "detail": f"composantes manquantes pour {formula}",
        }
    difference = actual - expected
    ok = abs(difference) <= _tolerance(expected)
    detail = (
        f"{_fmt(actual)}={_fmt(expected)}"
        if ok
        else f"{_fmt(actual)} vs {_fmt(expected)} (écart {_fmt(difference)})"
    )
    return {
        "id": check_id,
        "status": "pass" if ok else "fail",
        "detail": detail,
    }


def _n(values: dict, key: str) -> float:
    value = values.get(key)
    return 0.0 if value is None else float(value)


def _has(values: dict, *keys: str) -> bool:
    return all(values.get(key) is not None for key in keys)


def validate(values: dict) -> dict:
    checks: list[dict] = []

    checks.append(
        _check(
            "actif_egal_passif",
            values.get("total_actif"),
            values.get("total_capitaux_propres_et_passifs"),
            "total_actif = total_capitaux_propres_et_passifs",
        )
    )

    somme_actif = (
        _n(values, "total_actifs_non_courants") + _n(values, "total_actifs_courants")
        if _has(values, "total_actifs_non_courants", "total_actifs_courants")
        else None
    )
    checks.append(
        _check(
            "somme_actif",
            values.get("total_actif"),
            somme_actif,
            "total_actif = actifs non courants + actifs courants",
        )
    )

    somme_passif = (
        _n(values, "capitaux_propres_part_groupe")
        + _n(values, "interets_minoritaires_bilan")
        + _n(values, "total_passifs_non_courants")
        + _n(values, "total_passifs_courants")
        if _has(
            values,
            "capitaux_propres_part_groupe",
            "total_passifs_non_courants",
            "total_passifs_courants",
        )
        else None
    )
    checks.append(
        _check(
            "somme_passif",
            values.get("total_capitaux_propres_et_passifs"),
            somme_passif,
            "total passif = capitaux propres + minoritaires + passifs",
        )
    )

    ebit = (
        _n(values, "chiffre_affaires")
        + _n(values, "autres_produits_exploitation")
        + _n(values, "variation_stocks")
        + _n(values, "cout_des_ventes")
        + _n(values, "charges_personnel")
        + _n(values, "autres_charges_exploitation")
        + _n(values, "dotations_amortissements_provisions")
        if _has(values, "chiffre_affaires", "cout_des_ventes")
        else None
    )
    checks.append(
        _check(
            "ebit_recalcule",
            values.get("resultat_exploitation"),
            ebit,
            "EBIT = CA + autres produits + variation stocks + charges",
        )
    )

    ebt = (
        _n(values, "resultat_exploitation")
        + _n(values, "charges_interets")
        + _n(values, "autres_produits_financiers")
        + _n(values, "produits_placements")
        + _n(values, "quote_part_resultat_mee")
        + _n(values, "autres_gains_pertes")
        + _n(values, "elements_non_recurrents")
        if _has(values, "resultat_exploitation")
        else None
    )
    checks.append(
        _check(
            "ebt_recalcule",
            values.get("resultat_avant_impot"),
            ebt,
            "EBT = EBIT + résultat financier + autres gains et pertes",
        )
    )

    rn = (
        _n(values, "resultat_avant_impot")
        + _n(values, "impot_sur_benefices")
        + _n(values, "autres_impots")
        - _n(values, "interets_minoritaires_resultat")
        if _has(values, "resultat_avant_impot")
        else None
    )
    checks.append(
        _check(
            "resultat_net_recalcule",
            values.get("resultat_net_part_groupe"),
            rn,
            "RN part groupe = EBT + impôts − intérêts minoritaires",
        )
    )

    tresorerie = (
        _n(values, "liquidites") - _n(values, "dettes_financieres_courantes")
        if _has(values, "liquidites", "dettes_financieres_courantes")
        else None
    )
    checks.append(
        _check(
            "coherence_tresorerie",
            values.get("tresorerie_cloture"),
            tresorerie,
            "trésorerie de clôture = liquidités − dettes financières courantes",
        )
    )

    return {
        "verdict": "pass" if all(item["status"] == "pass" for item in checks) else "fail",
        "checks": checks,
    }


def extraction_digest(items: list[dict]) -> str:
    payload = [
        {
            "line_item": item["line_item"],
            "value": str(int(item["value"])),
            "page": int(item["page"]),
            "confidence": f"{float(item['confidence']):.3f}",
        }
        for item in sorted(items, key=lambda entry: entry["line_item"])
    ]
    return sha256_hex(canonical_json(payload))
