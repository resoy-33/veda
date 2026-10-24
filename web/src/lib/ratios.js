export const RATIO_GROUPS = [
  {
    id: "rentabilite",
    title: "Rentabilité",
    description: "Marges, rendement des capitaux et décomposition DuPont.",
    codes: [
      "marge_brute",
      "ebitda",
      "marge_brute_pct",
      "marge_ebitda",
      "marge_exploitation",
      "marge_avant_impot",
      "marge_nette",
      "marge_fcf",
      "roe",
      "roe_moyen",
      "roa",
      "roa_moyen",
      "roce",
      "dupont_effet_impot",
      "dupont_effet_financier",
      "dupont_marge_exploitation",
      "dupont_rotation_actif",
      "dupont_levier_financier",
    ],
  },
  {
    id: "croissance",
    title: "Croissance",
    description: "Évolution annuelle par rapport à l’exercice précédent.",
    codes: [
      "croissance_ca",
      "croissance_ebitda",
      "croissance_ebit",
      "croissance_resultat_net",
      "croissance_bpa",
      "croissance_cfo",
      "croissance_dpa",
      "croissance_total_actif",
    ],
  },
  {
    id: "structure",
    title: "Structure financière",
    description: "Endettement, autonomie et couverture des intérêts.",
    codes: [
      "total_dettes",
      "dette_nette",
      "capitaux_investis",
      "gearing",
      "dette_sur_fonds_propres",
      "dette_nette_ebitda",
      "autonomie_financiere",
      "dettes_actif",
      "couverture_interets_ebit",
      "couverture_interets_ebitda",
      "couverture_interets_ebitda_capex",
      "cfo_dette_brute",
    ],
  },
  {
    id: "liquidite",
    title: "Liquidité & cycle",
    description: "Capacité à honorer le court terme et rotation du besoin en fonds de roulement.",
    codes: [
      "fonds_roulement",
      "bfr_exploitation",
      "tresorerie_nette_gestion",
      "liquidite_generale",
      "liquidite_reduite",
      "liquidite_reduite_stricte",
      "liquidite_immediate",
      "liquidite_immediate_elargie",
      "couverture_cfo_passifs_courants",
      "dio",
      "dso",
      "dpo",
      "ccc",
      "rotation_stocks",
      "rotation_creances",
      "rotation_dettes",
    ],
  },
  {
    id: "cash",
    title: "Cash & investissement",
    description: "Conversion du résultat en trésorerie et effort d’investissement.",
    codes: [
      "free_cash_flow",
      "fcff",
      "cfo_sur_ebitda",
      "cfo_sur_resultat_net",
      "fcf_sur_resultat_net",
      "capex_sur_ca",
      "capex_sur_da",
      "accruals",
    ],
  },
  {
    id: "couts",
    title: "Structure des coûts",
    description: "Poids des principaux postes dans le chiffre d’affaires.",
    codes: [
      "cout_ventes_ca",
      "charges_personnel_ca",
      "autres_charges_ca",
      "dotations_ca",
    ],
  },
  {
    id: "marche",
    title: "Action & marché",
    description: "Indicateurs par action et valorisation boursière.",
    codes: [
      "bpa",
      "dpa",
      "vcpa",
      "cfo_par_action",
      "fcf_par_action",
      "taux_distribution",
      "per",
      "rendement_benefice",
      "pb",
      "ps",
      "p_cfo",
      "p_fcf",
      "capitalisation_boursiere",
      "valeur_entreprise",
      "valeur_graham",
    ],
  },
];

export function groupRatios(ratios) {
  const byCode = new Map(ratios.map((ratio) => [ratio.code, ratio]));
  return RATIO_GROUPS.map((group) => ({
    ...group,
    items: group.codes
      .map((code) => byCode.get(code))
      .filter((ratio) => ratio && ratio.value !== null && ratio.value !== undefined),
  })).filter(
    (group) =>
      group.items.length > 0 &&
      (group.id !== "marche" || Boolean(byCode.get("capitalisation_boursiere")?.value))
  );
}

export const VALUE_SECTIONS = [
  {
    id: "resultat",
    title: "Compte de résultat",
    description: "Produits, charges et résultat de l’exercice.",
    keys: [
      "chiffre_affaires",
      "autres_produits_exploitation",
      "variation_stocks",
      "cout_des_ventes",
      "charges_personnel",
      "autres_charges_exploitation",
      "dotations_amortissements_provisions",
      "resultat_exploitation",
      "charges_interets",
      "autres_produits_financiers",
      "produits_placements",
      "quote_part_resultat_mee",
      "autres_gains_pertes",
      "resultat_avant_impot",
      "impot_sur_benefices",
      "autres_impots",
      "interets_minoritaires_resultat",
      "resultat_net_part_groupe",
      "elements_non_recurrents",
    ],
  },
  {
    id: "bilan",
    title: "Bilan",
    description: "Actif, capitaux propres et passif à la clôture.",
    keys: [
      "immobilisations_incorporelles",
      "ecarts_acquisition",
      "immobilisations_corporelles",
      "immobilisations_financieres",
      "titres_mise_en_equivalence",
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
      "reserves_resultats_reportes",
      "interets_minoritaires_bilan",
      "emprunts_dettes_financieres_non_courants",
      "autres_passifs_non_courants",
      "total_passifs_non_courants",
      "fournisseurs_comptes_rattaches",
      "dettes_financieres_courantes",
      "autres_passifs_courants",
      "total_passifs_courants",
      "total_capitaux_propres_et_passifs",
    ],
  },
  {
    id: "flux",
    title: "Flux de trésorerie",
    description: "Flux d’exploitation, investissement et financement.",
    keys: [
      "flux_tresorerie_exploitation",
      "acquisitions_immobilisations",
      "cessions_immobilisations",
      "acquisitions_financieres",
      "dividendes_verses",
      "variation_nette_emprunts",
      "augmentation_capital",
      "tresorerie_cloture",
    ],
  },
];

export function groupValues(values) {
  const byKey = new Map(values.map((item) => [item.line_item, item]));
  return VALUE_SECTIONS.map((section) => ({
    ...section,
    items: section.keys
      .map((key) => byKey.get(key))
      .filter(Boolean),
  })).filter((section) => section.items.length > 0);
}

export const VERIFICATION_LABELS = {
  messages_present: "Messages présents",
  event_count: "Nombre d’événements",
  hash_chain: "Chaîne de hachage",
  event_order: "Ordre des événements",
  filing_consistency: "Cohérence du dépôt",
  validation_verdict: "Verdict de validation",
  sealed_event: "Événement de scellement",
  nft_metadata: "Métadonnée NFT",
  file_read: "Fichier HFS lisible",
  doc_hash_match: "Empreinte du PDF",
  extraction_hash_match: "Empreinte d’extraction",
  report_hash_match: "Empreinte du rapport",
  topic_match: "Topic HCS",
  mirror_read: "Lecture du mirror",
};

export const CHECK_LABELS = {
  actif_egal_passif: "Actif = passif",
  somme_actif: "Somme de l’actif",
  somme_passif: "Somme du passif",
  ebit_recalcule: "EBIT recalculé",
  ebt_recalcule: "Résultat avant impôt recalculé",
  resultat_net_recalcule: "Résultat net recalculé",
  coherence_tresorerie: "Cohérence de trésorerie",
};
