"""French label normalization and mapping to canonical line items."""
from __future__ import annotations

from app.extraction.registry import (
    canonical_label,
    is_section_header,
    map_label,
    normalize,
    note_to_key,
)

MISSING = "\ufffd"


def test_normalize_drops_lost_letters():
    assert normalize(f"R{MISSING}sultat") == "rsultat"
    assert normalize("Résultat") == "resultat"


def test_normalize_apostrophes_and_punctuation():
    assert normalize("Chiffre d'affaires") == "chiffre d affaires"
    assert normalize("Immob. Corp &incorp") == "immob corp incorp"


def test_exact_revenus():
    assert map_label("Revenus")[0] == "chiffre_affaires"


def test_fuzzy_accented_result():
    key, confidence = map_label(f"R{MISSING}sultat d'exploitation")
    assert key == "resultat_exploitation"
    assert confidence >= 0.9


def test_fuzzy_tresorerie_cloture():
    label = f"Tr{MISSING}sorerie {MISSING} la cl{MISSING}ture de l'exercice"
    assert map_label(label)[0] == "tresorerie_cloture"


def test_fuzzy_impot():
    label = f"Imp{MISSING}t sur les soci{MISSING}t{MISSING}s"
    assert map_label(label)[0] == "impot_sur_benefices"


def test_minorities_depend_on_note_context():
    assert map_label("Part des minoritaires", "III.10")[0] == "interets_minoritaires_bilan"
    assert map_label("Part des minoritaires")[0] == "interets_minoritaires_resultat"


def test_acquisitions_and_cessions():
    assert (
        map_label(f"D{MISSING}caissement pour acquisition des immob. Corp &incorp")[0]
        == "acquisitions_immobilisations"
    )
    assert (
        map_label("Encaissement sur cession d'immob corp et incorp")[0]
        == "cessions_immobilisations"
    )
    assert (
        map_label(f"D{MISSING}caissement provenant de l'acquisition d'immob financi{MISSING}res")[0]
        == "acquisitions_financieres"
    )


def test_variation_stocks_variants():
    assert map_label("Variation de stock de produits finis et encours")[0] == "variation_stocks"
    assert map_label("Var de stock de produits finis et encours")[0] == "variation_stocks"


def test_other_gains_and_losses_share_key():
    assert map_label("Autres gains ordinaires")[0] == "autres_gains_pertes"
    assert map_label("Autres pertes ordinaires")[0] == "autres_gains_pertes"


def test_section_headers():
    assert is_section_header("Actifs courants")
    assert is_section_header("Charges d'exploitation")
    assert is_section_header("Flux de trésorerie liés à l'exploitation")
    assert not is_section_header("Résultat d'exploitation")


def test_note_map():
    assert note_to_key("III.2") == "immobilisations_corporelles"
    assert note_to_key("IV.2") is None


def test_canonical_label():
    assert "Chiffre d'affaires" in canonical_label("chiffre_affaires")
