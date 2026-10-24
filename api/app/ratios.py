"""Deterministic ratio engine (contracts v1.0, section 8)."""
from __future__ import annotations

from math import sqrt

from .core.canonical import canonical_json, sha256_hex

FORMULA_VERSION = "1.0"
DAYS = 365.0

LABELS: dict[str, str] = {
    "marge_brute": "Marge brute",
    "ebitda": "EBITDA",
    "total_dettes": "Dettes financières totales",
    "dette_nette": "Dette nette",
    "fonds_roulement": "Fonds de roulement",
    "bfr_exploitation": "BFR d'exploitation",
    "tresorerie_nette_gestion": "Trésorerie nette de gestion",
    "capitaux_investis": "Capitaux investis",
    "free_cash_flow": "Free cash flow",
    "fcff": "FCFF",
    "capitalisation_boursiere": "Capitalisation boursière",
    "valeur_entreprise": "Valeur d'entreprise",
    "croissance_ca": "Croissance du chiffre d'affaires",
    "croissance_ebitda": "Croissance de l'EBITDA",
    "croissance_ebit": "Croissance de l'EBIT",
    "croissance_resultat_net": "Croissance du résultat net",
    "croissance_bpa": "Croissance du BPA",
    "croissance_cfo": "Croissance du flux de trésorerie d'exploitation",
    "croissance_dpa": "Croissance du dividende par action",
    "croissance_total_actif": "Croissance du total actif",
    "marge_brute_pct": "Marge brute sur chiffre d'affaires",
    "marge_ebitda": "Marge EBITDA",
    "marge_exploitation": "Marge d'exploitation",
    "marge_avant_impot": "Marge avant impôt",
    "marge_nette": "Marge nette",
    "marge_fcf": "Marge de free cash flow",
    "cout_ventes_ca": "Coût des ventes sur chiffre d'affaires",
    "charges_personnel_ca": "Charges de personnel sur chiffre d'affaires",
    "autres_charges_ca": "Autres charges d'exploitation sur chiffre d'affaires",
    "dotations_ca": "Dotations aux amortissements sur chiffre d'affaires",
    "roe": "Rentabilité des capitaux propres (ROE)",
    "roe_moyen": "ROE sur capitaux propres moyens",
    "roa": "Rentabilité de l'actif (ROA)",
    "roa_moyen": "ROA sur actif moyen",
    "roce": "ROCE",
    "dupont_effet_impot": "DuPont — effet impôt",
    "dupont_effet_financier": "DuPont — effet financier",
    "dupont_marge_exploitation": "DuPont — marge d'exploitation",
    "dupont_rotation_actif": "DuPont — rotation de l'actif",
    "dupont_levier_financier": "DuPont — levier financier",
    "liquidite_generale": "Liquidité générale",
    "liquidite_reduite": "Liquidité réduite",
    "liquidite_reduite_stricte": "Liquidité réduite stricte",
    "liquidite_immediate": "Liquidité immédiate",
    "liquidite_immediate_elargie": "Liquidité immédiate élargie",
    "couverture_cfo_passifs_courants": "Couverture des passifs courants par le CFO",
    "dio": "Délai de rotation des stocks (DIO)",
    "dso": "Délai de règlement clients (DSO)",
    "dpo": "Délai de règlement fournisseurs (DPO)",
    "ccc": "Cycle de conversion de trésorerie (CCC)",
    "rotation_stocks": "Rotation des stocks",
    "rotation_creances": "Rotation des créances clients",
    "rotation_dettes": "Rotation des dettes fournisseurs",
    "dettes_actif": "Dettes financières sur total actif",
    "autonomie_financiere": "Autonomie financière",
    "dette_sur_fonds_propres": "Dette sur fonds propres",
    "gearing": "Gearing",
    "dette_nette_ebitda": "Dette nette sur EBITDA",
    "couverture_interets_ebit": "Couverture des intérêts par l'EBIT",
    "couverture_interets_ebitda": "Couverture des intérêts par l'EBITDA",
    "couverture_interets_ebitda_capex": "Couverture des intérêts par l'EBITDA moins Capex",
    "cfo_dette_brute": "CFO sur dette brute",
    "fcf_sur_resultat_net": "FCF sur résultat net",
    "cfo_sur_ebitda": "CFO sur EBITDA",
    "cfo_sur_resultat_net": "CFO sur résultat net",
    "capex_sur_ca": "Capex sur chiffre d'affaires",
    "capex_sur_da": "Capex sur dotations aux amortissements",
    "accruals": "Accruals",
    "bpa": "Bénéfice par action (BPA)",
    "dpa": "Dividende par action (DPA)",
    "taux_distribution": "Taux de distribution",
    "vcpa": "Valeur comptable par action (VCPA)",
    "cfo_par_action": "CFO par action",
    "fcf_par_action": "FCF par action",
    "per": "PER",
    "rendement_benefice": "Rendement du bénéfice",
    "pb": "P/B",
    "ps": "P/S",
    "p_cfo": "P/CFO",
    "p_fcf": "P/FCF",
    "valeur_graham": "Valeur de Graham",
}


def _v(values: dict, key: str) -> float | None:
    value = values.get(key)
    return None if value is None else float(value)


def _div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _add(*items: float | None) -> float | None:
    present = [item for item in items if item is not None]
    if not present:
        return None
    return sum(present)


def _sub(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def _growth(current: float | None, prior: float | None) -> float | None:
    if current is None or prior is None or prior == 0:
        return None
    return (current - prior) / abs(prior)


def _average(current: float | None, prior: float | None) -> float | None:
    if current is None or prior is None:
        return None
    return (current + prior) / 2


def _interest_expense(values: dict) -> float | None:
    charges = _v(values, "charges_interets")
    if charges is None:
        return None
    return max(0.0, -charges)


def _tax_rate(values: dict) -> float:
    ebt = _v(values, "resultat_avant_impot")
    tax = _v(values, "impot_sur_benefices")
    if ebt is None or ebt <= 0 or tax is None:
        return 0.0
    return min(max(-tax / ebt, 0.0), 1.0)


def _aggregates(values: dict) -> dict[str, float | None]:
    ca = _v(values, "chiffre_affaires")
    cout = _v(values, "cout_des_ventes")
    ebit = _v(values, "resultat_exploitation")
    dotations = _v(values, "dotations_amortissements_provisions")
    liquidites = _v(values, "liquidites")
    dettes_courantes = _v(values, "dettes_financieres_courantes")
    cp = _v(values, "capitaux_propres_part_groupe")
    minoritaires = _v(values, "interets_minoritaires_bilan")
    cfo = _v(values, "flux_tresorerie_exploitation")
    acquisitions = _v(values, "acquisitions_immobilisations")
    cessions = _v(values, "cessions_immobilisations")
    actions = _v(values, "nombre_actions")
    cours = _v(values, "cours_cloture")

    marge_brute = None if ca is None or cout is None else ca + cout
    ebitda = _sub(ebit, dotations)
    emprunts = _v(values, "emprunts_dettes_financieres_non_courants")
    total_dettes = (
        None if emprunts is None or dettes_courantes is None
        else emprunts + dettes_courantes
    )
    dette_nette = _sub(total_dettes, liquidites)
    fonds_roulement = _sub(
        _v(values, "total_actifs_courants"), _v(values, "total_passifs_courants")
    )
    stocks = _v(values, "stocks")
    clients = _v(values, "clients_comptes_rattaches")
    fournisseurs = _v(values, "fournisseurs_comptes_rattaches")
    bfr = (
        None
        if stocks is None or clients is None or fournisseurs is None
        else stocks + clients - fournisseurs
    )
    tresorerie_nette = _sub(liquidites, dettes_courantes)
    capitaux_investis = _add(cp, minoritaires, total_dettes)
    fcf = (
        None
        if cfo is None or acquisitions is None
        else cfo + acquisitions + (cessions or 0.0)
    )
    interest = _interest_expense(values)
    fcff = _add(fcf, None if interest is None else interest * (1 - _tax_rate(values)))
    capitalisation = None
    if actions is not None and cours is not None:
        capitalisation = actions * cours
    valeur_entreprise = _add(capitalisation, dette_nette)

    return {
        "marge_brute": marge_brute,
        "ebitda": ebitda,
        "total_dettes": total_dettes,
        "dette_nette": dette_nette,
        "fonds_roulement": fonds_roulement,
        "bfr_exploitation": bfr,
        "tresorerie_nette_gestion": tresorerie_nette,
        "capitaux_investis": capitaux_investis,
        "free_cash_flow": fcf,
        "fcff": fcff,
        "capitalisation_boursiere": capitalisation,
        "valeur_entreprise": valeur_entreprise,
    }


def compute_ratios(
    values: dict, year: int, prior_values: dict | None = None
) -> list[dict]:
    prior = prior_values or {}
    agg = _aggregates(values)
    prior_agg = _aggregates(prior) if prior else {}

    ca = _v(values, "chiffre_affaires")
    cout = _v(values, "cout_des_ventes")
    cogs = abs(cout) if cout is not None else None
    ebit = _v(values, "resultat_exploitation")
    ebt = _v(values, "resultat_avant_impot")
    rn = _v(values, "resultat_net_part_groupe")
    cfo = _v(values, "flux_tresorerie_exploitation")
    fcf = agg["free_cash_flow"]
    ebitda = agg["ebitda"]
    cp = _v(values, "capitaux_propres_part_groupe")
    total_actif = _v(values, "total_actif")
    total_dettes = agg["total_dettes"]
    liquidites = _v(values, "liquidites")
    dettes_courantes = _v(values, "dettes_financieres_courantes")
    passifs_courants = _v(values, "total_passifs_courants")
    actifs_courants = _v(values, "total_actifs_courants")
    stocks = _v(values, "stocks")
    clients = _v(values, "clients_comptes_rattaches")
    fournisseurs = _v(values, "fournisseurs_comptes_rattaches")
    interest = _interest_expense(values)
    dotations = _v(values, "dotations_amortissements_provisions")
    da = abs(dotations) if dotations is not None else None
    actions = _v(values, "nombre_actions")
    cours = _v(values, "cours_cloture")
    dpa = _v(values, "dividende_par_action")
    capex = None if _v(values, "acquisitions_immobilisations") is None else -_v(
        values, "acquisitions_immobilisations"
    )
    bpa = _div(rn, actions)
    vcpa = _div(cp, actions)
    capitalisation = agg["capitalisation_boursiere"]
    dio = _div(stocks, cogs)
    dio = dio * DAYS if dio is not None else None
    dso = _div(clients, ca)
    dso = dso * DAYS if dso is not None else None
    dpo = _div(fournisseurs, cogs)
    dpo = dpo * DAYS if dpo is not None else None
    ccc = (
        None if dio is None or dso is None or dpo is None else dio + dso - dpo
    )
    graham = None
    if bpa is not None and vcpa is not None and bpa > 0 and vcpa > 0:
        graham = sqrt(22.5 * bpa * vcpa)
    prior_cp = _v(prior, "capitaux_propres_part_groupe") if prior else None
    prior_actif = _v(prior, "total_actif") if prior else None

    ratios = {
        **agg,
        "croissance_ca": _growth(ca, _v(prior, "chiffre_affaires") if prior else None),
        "croissance_ebitda": _growth(
            ebitda, prior_agg.get("ebitda") if prior else None
        ),
        "croissance_ebit": _growth(
            ebit, _v(prior, "resultat_exploitation") if prior else None
        ),
        "croissance_resultat_net": _growth(
            rn, _v(prior, "resultat_net_part_groupe") if prior else None
        ),
        "croissance_bpa": _growth(
            bpa, _div(_v(prior, "resultat_net_part_groupe"), _v(prior, "nombre_actions"))
            if prior else None,
        ),
        "croissance_cfo": _growth(
            cfo, _v(prior, "flux_tresorerie_exploitation") if prior else None
        ),
        "croissance_dpa": _growth(
            dpa, _v(prior, "dividende_par_action") if prior else None
        ),
        "croissance_total_actif": _growth(total_actif, prior_actif),
        "marge_brute_pct": _div(agg["marge_brute"], ca),
        "marge_ebitda": _div(ebitda, ca),
        "marge_exploitation": _div(ebit, ca),
        "marge_avant_impot": _div(ebt, ca),
        "marge_nette": _div(rn, ca),
        "marge_fcf": _div(fcf, ca),
        "cout_ventes_ca": _div(cogs, ca),
        "charges_personnel_ca": _div(
            None
            if _v(values, "charges_personnel") is None
            else -_v(values, "charges_personnel"),
            ca,
        ),
        "autres_charges_ca": _div(
            None
            if _v(values, "autres_charges_exploitation") is None
            else -_v(values, "autres_charges_exploitation"),
            ca,
        ),
        "dotations_ca": _div(da, ca),
        "roe": _div(rn, cp),
        "roe_moyen": _div(rn, _average(cp, prior_cp)),
        "roa": _div(rn, total_actif),
        "roa_moyen": _div(rn, _average(total_actif, prior_actif)),
        "roce": _div(ebit, agg["capitaux_investis"]),
        "dupont_effet_impot": _div(rn, ebt),
        "dupont_effet_financier": _div(ebt, ebit),
        "dupont_marge_exploitation": _div(ebit, ca),
        "dupont_rotation_actif": _div(ca, total_actif),
        "dupont_levier_financier": _div(total_actif, cp),
        "liquidite_generale": _div(actifs_courants, passifs_courants),
        "liquidite_reduite": _div(
            _sub(actifs_courants, stocks), passifs_courants
        ),
        "liquidite_reduite_stricte": _div(_add(clients, liquidites), passifs_courants),
        "liquidite_immediate": _div(liquidites, passifs_courants),
        "liquidite_immediate_elargie": _div(
            _add(liquidites, _v(values, "placements_actifs_financiers")),
            passifs_courants,
        ),
        "couverture_cfo_passifs_courants": _div(cfo, passifs_courants),
        "dio": dio,
        "dso": dso,
        "dpo": dpo,
        "ccc": ccc,
        "rotation_stocks": _div(cogs, stocks),
        "rotation_creances": _div(ca, clients),
        "rotation_dettes": _div(cogs, fournisseurs),
        "dettes_actif": _div(total_dettes, total_actif),
        "autonomie_financiere": _div(cp, total_actif),
        "dette_sur_fonds_propres": _div(total_dettes, cp),
        "gearing": _div(agg["dette_nette"], cp),
        "dette_nette_ebitda": _div(agg["dette_nette"], ebitda),
        "couverture_interets_ebit": _div(ebit, interest),
        "couverture_interets_ebitda": _div(ebitda, interest),
        "couverture_interets_ebitda_capex": _div(
            _sub(ebitda, capex), interest
        ),
        "cfo_dette_brute": _div(cfo, total_dettes),
        "fcf_sur_resultat_net": _div(fcf, rn),
        "cfo_sur_ebitda": _div(cfo, ebitda),
        "cfo_sur_resultat_net": _div(cfo, rn),
        "capex_sur_ca": _div(capex, ca),
        "capex_sur_da": _div(capex, da),
        "accruals": _div(_sub(rn, cfo), total_actif),
        "bpa": bpa,
        "dpa": dpa,
        "taux_distribution": _div(dpa, bpa),
        "vcpa": vcpa,
        "cfo_par_action": _div(cfo, actions),
        "fcf_par_action": _div(fcf, actions),
        "per": _div(cours, bpa),
        "rendement_benefice": _div(bpa, cours),
        "pb": _div(cours, vcpa),
        "ps": _div(capitalisation, ca),
        "p_cfo": _div(capitalisation, cfo),
        "p_fcf": _div(capitalisation, fcf),
        "valeur_graham": graham,
    }

    return [
        {
            "code": code,
            "name": LABELS[code],
            "year": year,
            "value": ratios[code],
            "formula_version": FORMULA_VERSION,
        }
        for code in sorted(ratios)
    ]


def ratios_digest(rows: list[dict]) -> str:
    payload = [
        {
            "code": row["code"],
            "year": int(row["year"]),
            "value": None if row["value"] is None else f"{row['value']:.6f}",
        }
        for row in sorted(rows, key=lambda item: (item["code"], item["year"]))
    ]
    return sha256_hex(canonical_json(payload))
