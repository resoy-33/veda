export const ROLES = {
  issuer: {
    label: "Émetteur",
    short: "Émetteur",
    description: "Dépose et scelle les états financiers",
    tone: "emerald",
  },
  broker: {
    label: "Analyste",
    short: "Analyste",
    description: "Consulte et vérifie le registre",
    tone: "blue",
  },
  verifier: {
    label: "Auditeur",
    short: "Auditeur",
    description: "Contrôle les preuves on-chain",
    tone: "amber",
  },
  admin: {
    label: "Administrateur",
    short: "Admin",
    description: "Administre le registre et les modèles",
    tone: "slate",
  },
};

export const DEMO_ACCOUNTS = [
  {
    email: "issuer@lilas.tn",
    role: "issuer",
    name: "Direction financière LILAS",
  },
  {
    email: "broker@veda.tn",
    role: "broker",
    name: "Desk marchés Veda",
  },
  {
    email: "verifier@veda.tn",
    role: "verifier",
    name: "Audit & conformité Veda",
  },
  {
    email: "admin@veda.tn",
    role: "admin",
    name: "Administrateur Veda",
  },
];

export const ROLE_TIER = {
  issuer: "Production",
  broker: "Lecture & vérification",
  verifier: "Lecture & vérification",
  admin: "Opérations",
};

export function roleLabel(role) {
  return ROLES[role]?.label || role;
}

export function initials(name, email = "") {
  const source = (name || email.split("@")[0] || "V").trim();
  const words = source.split(/[\s._-]+/).filter(Boolean);
  if (words.length === 0) {
    return "V";
  }
  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }
  return `${words[0][0]}${words[words.length - 1][0]}`.toUpperCase();
}

export function displayName(user) {
  return user?.display_name || user?.email?.split("@")[0] || "Utilisateur";
}
