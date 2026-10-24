const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const dateTimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export const STATUS_LABELS = {
  submitted: "Déposé",
  extracted: "Extrait",
  validated: "Validé",
  failed: "Échec",
  sealed: "Scellé",
};

export const EVENT_LABELS = {
  filing_submitted: "Dépôt du PDF",
  extracted: "Extraction déterministe",
  validated: "Validation comptable",
  sealed: "Scellement Hedera",
};

export function formatPeriod(value) {
  if (!value) {
    return "—";
  }
  return `Exercice ${String(value).slice(0, 4)}`;
}

export function formatYear(value) {
  return value ? String(value).slice(0, 4) : "—";
}

export function formatDate(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return dateFormatter.format(date);
}

export function formatDateTime(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return dateTimeFormatter.format(date);
}

export function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  return new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Number(value));
}

export function formatMTND(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  return `${formatNumber(Number(value) / 1_000_000, digits)} MTND`;
}

export function formatTND(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  return `${formatNumber(Number(value), digits)} TND`;
}

export function formatRatioValue(code, value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  const number = Number(value);
  if (
    [
      "marge_brute",
      "ebitda",
      "total_dettes",
      "dette_nette",
      "fonds_roulement",
      "bfr_exploitation",
      "tresorerie_nette_gestion",
      "capitaux_investis",
      "free_cash_flow",
      "fcff",
      "capitalisation_boursiere",
      "valeur_entreprise",
    ].includes(code)
  ) {
    return formatMTND(number, 1);
  }
  if (
    code.startsWith("croissance_") ||
    code.startsWith("marge_") ||
    code === "roe" ||
    code === "roe_moyen" ||
    code === "roa" ||
    code === "roa_moyen" ||
    code === "roce" ||
    code.startsWith("dupont_effet") ||
    code === "dettes_actif" ||
    code === "autonomie_financiere" ||
    code === "accruals" ||
    code === "taux_distribution" ||
    code === "rendement_benefice" ||
    code === "capex_sur_ca"
  ) {
    return `${formatNumber(number * 100, 1)} %`;
  }
  if (["dio", "dso", "dpo", "ccc"].includes(code)) {
    return `${formatNumber(number, 1)} j`;
  }
  if (
    ["bpa", "dpa", "vcpa", "cfo_par_action", "fcf_par_action", "valeur_graham"].includes(
      code
    )
  ) {
    return `${formatNumber(number, 2)} TND`;
  }
  return `${formatNumber(number, digits)} x`;
}

export function shortHash(value, size = 8) {
  if (!value) {
    return "—";
  }
  if (value.length <= size * 2 + 1) {
    return value;
  }
  return `${value.slice(0, size)}…${value.slice(-size)}`;
}

export function fileSize(bytes) {
  if (!bytes) {
    return "—";
  }
  if (bytes < 1024 * 1024) {
    return `${formatNumber(bytes / 1024, 0)} Ko`;
  }
  return `${formatNumber(bytes / (1024 * 1024), 1)} Mo`;
}

export function isPercentRatio(code) {
  return (
    code.startsWith("croissance_") ||
    code.startsWith("marge_") ||
    ["roe", "roe_moyen", "roa", "roa_moyen", "roce"].includes(code)
  );
}
