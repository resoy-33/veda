"""French line-item registry and label matching (contracts section 7)."""
from __future__ import annotations

import unicodedata
from difflib import SequenceMatcher

CANONICAL: dict[str, str] = {
    "chiffre_affaires": "Chiffre d'affaires (revenus)",
    "autres_produits_exploitation": "Autres produits d'exploitation",
    "variation_stocks": "Variation de stocks de produits finis et encours",
    "cout_des_ventes": "Achats consommés de matières et d'emballages",
    "charges_personnel": "Charges de personnel",
    "autres_charges_exploitation": "Autres charges d'exploitation",
    "dotations_amortissements_provisions": "Dotations aux amortissements et provisions",
    "resultat_exploitation": "Résultat d'exploitation",
    "charges_interets": "Charges financières nettes",
    "autres_produits_financiers": "Autres produits financiers",
    "produits_placements": "Produits des placements",
    "quote_part_resultat_mee": "Quote-part de résultat des mises en équivalence",
    "autres_gains_pertes": "Autres gains et pertes",
    "resultat_avant_impot": "Résultat avant impôt",
    "impot_sur_benefices": "Impôt sur les sociétés",
    "autres_impots": "Autres impôts",
    "interets_minoritaires_resultat": "Intérêts minoritaires (résultat)",
    "resultat_net_part_groupe": "Résultat net (part du groupe)",
    "elements_non_recurrents": "Éléments non récurrents",
    "immobilisations_incorporelles": "Immobilisations incorporelles (nettes)",
    "ecarts_acquisition": "Écarts d'acquisition (nets)",
    "immobilisations_corporelles": "Immobilisations corporelles (nettes)",
    "immobilisations_financieres": "Immobilisations financières",
    "titres_mise_en_equivalence": "Titres mis en équivalence",
    "autres_actifs_non_courants": "Autres actifs non courants",
    "total_actifs_non_courants": "Total des actifs non courants",
    "stocks": "Stocks (nets)",
    "clients_comptes_rattaches": "Clients et comptes rattachés (nets)",
    "autres_actifs_courants": "Autres actifs courants (nets)",
    "placements_actifs_financiers": "Placements et autres actifs financiers",
    "liquidites": "Liquidités et équivalents",
    "total_actifs_courants": "Total des actifs courants",
    "total_actif": "Total des actifs",
    "capitaux_propres_part_groupe": "Capitaux propres (part du groupe)",
    "reserves_resultats_reportes": "Réserves et résultats reportés",
    "interets_minoritaires_bilan": "Intérêts minoritaires (bilan)",
    "emprunts_dettes_financieres_non_courants": "Emprunts et dettes financières non courants",
    "autres_passifs_non_courants": "Autres passifs non courants",
    "fournisseurs_comptes_rattaches": "Fournisseurs et comptes rattachés",
    "dettes_financieres_courantes": "Concours bancaires (dettes financières courantes)",
    "autres_passifs_courants": "Autres passifs courants",
    "total_passifs_non_courants": "Total des passifs non courants",
    "total_passifs_courants": "Total des passifs courants",
    "total_capitaux_propres_et_passifs": "Total des capitaux propres et passifs",
    "flux_tresorerie_exploitation": "Flux de trésorerie d'exploitation",
    "acquisitions_immobilisations": "Acquisitions d'immobilisations",
    "cessions_immobilisations": "Cessions d'immobilisations",
    "acquisitions_financieres": "Acquisitions financières",
    "dividendes_verses": "Dividendes versés",
    "variation_nette_emprunts": "Variation nette des emprunts",
    "augmentation_capital": "Augmentation de capital",
    "tresorerie_cloture": "Trésorerie à la clôture",
}

NOTE_MAP: dict[str, str] = {
    "III.1": "immobilisations_incorporelles",
    "III.2": "immobilisations_corporelles",
    "III.3": "immobilisations_financieres",
    "III.4": "autres_actifs_non_courants",
    "III.5": "stocks",
    "III.6": "clients_comptes_rattaches",
    "III.7": "autres_actifs_courants",
    "III.8": "placements_actifs_financiers",
    "III.9": "liquidites",
    "III.11": "emprunts_dettes_financieres_non_courants",
    "III.12": "autres_passifs_non_courants",
    "III.13": "fournisseurs_comptes_rattaches",
    "III.14": "autres_passifs_courants",
    "III.16": "dettes_financieres_courantes",
}

EXACT: dict[str, str] = {
    "revenus": "chiffre_affaires",
    "chiffre d affaires": "chiffre_affaires",
    "autres produits d exploitation": "autres_produits_exploitation",
    "achats consommes de matieres et d emballages": "cout_des_ventes",
    "charges de personnel": "charges_personnel",
    "autres charges d exploitation": "autres_charges_exploitation",
    "resultat d exploitation": "resultat_exploitation",
    "charges financieres nettes": "charges_interets",
    "produits des placements": "produits_placements",
    "autres gains ordinaires": "autres_gains_pertes",
    "autres pertes ordinaires": "autres_gains_pertes",
    "resultat des activites ordinaires avant impot": "resultat_avant_impot",
    "impot sur les societes": "impot_sur_benefices",
    "resultat consolide part du groupe": "resultat_net_part_groupe",
    "resultat net part du groupe": "resultat_net_part_groupe",
    "ecart d acquisition": "ecarts_acquisition",
    "immobilisations incorporelles": "immobilisations_incorporelles",
    "immobilisations corporelles": "immobilisations_corporelles",
    "immobilisations financieres": "immobilisations_financieres",
    "titre mis en equivalence": "titres_mise_en_equivalence",
    "titres mis en equivalence": "titres_mise_en_equivalence",
    "autres actifs non courants": "autres_actifs_non_courants",
    "total des actifs non courants": "total_actifs_non_courants",
    "stocks": "stocks",
    "clients et comptes rattaches": "clients_comptes_rattaches",
    "autres actifs courants": "autres_actifs_courants",
    "placements et autres actifs financiers": "placements_actifs_financiers",
    "liquidites et equivalents de liquidites": "liquidites",
    "total des actifs courants": "total_actifs_courants",
    "total des actifs": "total_actif",
    "total des capitaux propres part du groupe": "capitaux_propres_part_groupe",
    "emprunts": "emprunts_dettes_financieres_non_courants",
    "autres passifs non courants": "autres_passifs_non_courants",
    "total des passifs non courants": "total_passifs_non_courants",
    "fournisseurs et comptes rattaches": "fournisseurs_comptes_rattaches",
    "autres passifs courants": "autres_passifs_courants",
    "concours bancaires": "dettes_financieres_courantes",
    "total des passifs courants": "total_passifs_courants",
    "total des capitaux propres et des passifs": "total_capitaux_propres_et_passifs",
    "flux de tresorerie provenant de l exploitation": "flux_tresorerie_exploitation",
    "flux de tresorerie lies a l exploitation": "flux_tresorerie_exploitation",
    "tresorerie a la cloture de l exercice": "tresorerie_cloture",
    "part des minoritaires": "interets_minoritaires_resultat",
}

CONTAINS: tuple[tuple[str, str], ...] = (
    ("variation de stock", "variation_stocks"),
    ("var de stock", "variation_stocks"),
    ("distribution des dividendes", "dividendes_verses"),
    ("acquisition d immo financi", "acquisitions_financieres"),
    ("acquisition d immob financi", "acquisitions_financieres"),
    ("acquisition des immob", "acquisitions_immobilisations"),
    ("acquisition d immo", "acquisitions_immobilisations"),
    ("cession d immo", "cessions_immobilisations"),
    ("emprunts et credit", "variation_nette_emprunts"),
    ("augmentation de capital", "augmentation_capital"),
    ("dot aux amortissements", "dotations_amortissements_provisions"),
)

SECTION_HEADERS: set[str] = {
    "produits d exploitation",
    "charges d exploitation",
    "actifs",
    "actifs non courants",
    "actifs courants",
    "passifs",
    "passifs non courants",
    "passifs courants",
    "capitaux propres",
    "ajustements pour",
    "variation de",
    "variation des",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("\ufffd", "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    for char in "'’`´":
        text = text.replace(char, " ")
    text = "".join(
        char if (char.isalnum() or char.isspace()) else " " for char in text
    )
    return " ".join(text.split())


_EXACT_NORMALIZED = {normalize(label): key for label, key in EXACT.items()}
_CONTAINS_NORMALIZED = tuple((normalize(fragment), key) for fragment, key in CONTAINS)
_SECTIONS_NORMALIZED = {normalize(label) for label in SECTION_HEADERS}


def canonical_label(key: str) -> str:
    return CANONICAL.get(key, key)


def note_to_key(note: str) -> str | None:
    return NOTE_MAP.get(note)


def map_label(label: str, note: str = "") -> tuple[str | None, float]:
    normalized = normalize(label)
    if not normalized:
        return None, 0.0
    if normalized == "part des minoritaires":
        key = (
            "interets_minoritaires_bilan"
            if note
            else "interets_minoritaires_resultat"
        )
        return key, 1.0
    if normalized in _EXACT_NORMALIZED:
        return _EXACT_NORMALIZED[normalized], 1.0
    if normalized.startswith("flux de tresorerie") and "exploitation" in normalized:
        return "flux_tresorerie_exploitation", 0.9
    for fragment, key in _CONTAINS_NORMALIZED:
        if fragment in normalized:
            return key, 0.9

    best_key: str | None = None
    best_score = 0.0
    for candidate, key in _EXACT_NORMALIZED.items():
        score = SequenceMatcher(None, normalized, candidate).ratio()
        if score > best_score:
            best_key, best_score = key, score
    if best_key is not None and best_score >= 0.86:
        return best_key, round(best_score, 2)
    return None, 0.0


def is_section_header(label: str) -> bool:
    normalized = normalize(label)
    if normalized in _SECTIONS_NORMALIZED:
        return True
    return normalized.startswith("flux de tresorerie")
