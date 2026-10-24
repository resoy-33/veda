"""Run the extractor on a filing PDF and report coverage/identities."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .pdf import extract_values

CORE = (
    "chiffre_affaires",
    "autres_produits_exploitation",
    "variation_stocks",
    "cout_des_ventes",
    "charges_personnel",
    "dotations_amortissements_provisions",
    "autres_charges_exploitation",
    "resultat_exploitation",
    "charges_interets",
    "produits_placements",
    "resultat_avant_impot",
    "impot_sur_benefices",
    "resultat_net_part_groupe",
    "immobilisations_incorporelles",
    "immobilisations_corporelles",
    "immobilisations_financieres",
    "autres_actifs_non_courants",
    "total_actifs_non_courants",
    "stocks",
    "clients_comptes_rattaches",
    "autres_actifs_courants",
    "placements_actifs_financiers",
    "liquidites",
    "total_actifs_courants",
    "total_actif",
    "capitaux_propres_part_groupe",
    "interets_minoritaires_bilan",
    "emprunts_dettes_financieres_non_courants",
    "autres_passifs_non_courants",
    "fournisseurs_comptes_rattaches",
    "autres_passifs_courants",
    "dettes_financieres_courantes",
    "total_passifs_non_courants",
    "total_passifs_courants",
    "total_capitaux_propres_et_passifs",
    "flux_tresorerie_exploitation",
    "acquisitions_immobilisations",
    "cessions_immobilisations",
    "dividendes_verses",
    "variation_nette_emprunts",
    "tresorerie_cloture",
)


def _matches(computed, expected) -> bool:
    if expected is None:
        return False
    return abs(computed - expected) <= max(1, round(abs(expected) * 0.0001))


def main(argv: list[str]) -> int:
    path = Path(argv[1])
    year = int(argv[2])
    values = extract_values(path, year)
    by_key = {item["line_item"]: item["value"] for item in values}
    missing = [key for key in CORE if key not in by_key]
    print(f"{path.name} ({year}): {len(values)} line items, {len(missing)} core missing")
    if missing:
        print("missing:", ", ".join(missing))
    for item in sorted(values, key=lambda entry: entry["line_item"]):
        print(f"  {item['line_item']:45s} {item['value']:>15,d}  p{item['page']}")

    actif = by_key.get("total_actif")
    passif = by_key.get("total_capitaux_propres_et_passifs")
    print(f"actif == passif: {actif == passif} ({actif} vs {passif})")
    liquidites = by_key.get("liquidites")
    concours = by_key.get("dettes_financieres_courantes")
    cloture = by_key.get("tresorerie_cloture")
    if None not in (liquidites, concours, cloture):
        print(
            "tresorerie: "
            f"{liquidites} - {concours} = {liquidites - concours} "
            f"vs cloture {cloture} -> {liquidites - concours == cloture}"
        )

    income_keys = (
        "chiffre_affaires",
        "autres_produits_exploitation",
        "variation_stocks",
        "cout_des_ventes",
        "charges_personnel",
        "dotations_amortissements_provisions",
        "autres_charges_exploitation",
    )
    if all(key in by_key for key in income_keys):
        ebit = (
            by_key["chiffre_affaires"]
            + by_key["autres_produits_exploitation"]
            + by_key["variation_stocks"]
            + by_key["cout_des_ventes"]
            + by_key["charges_personnel"]
            + by_key["dotations_amortissements_provisions"]
            + by_key["autres_charges_exploitation"]
        )
        expected_ebit = by_key.get("resultat_exploitation")
        print(f"ebit: {ebit} vs {expected_ebit} -> {_matches(ebit, expected_ebit)}")
        ebt = (
            ebit
            + by_key.get("produits_placements", 0)
            + by_key.get("autres_gains_pertes", 0)
            + by_key.get("charges_interets", 0)
        )
        expected_ebt = by_key.get("resultat_avant_impot")
        print(f"ebt: {ebt} vs {expected_ebt} (diff {None if expected_ebt is None else ebt - expected_ebt}) -> {_matches(ebt, expected_ebt)}")

    out = Path("spike") / f"extraction_{year}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(values, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
