import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  Building2,
  CalendarRange,
  CheckCircle2,
  FileText,
  Landmark,
  Plus,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { api } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { StatusBadge } from "../components/StatusBadge.jsx";
import { formatDate, formatMTND, formatPeriod, shortHash } from "../lib/format.js";
import { roleLabel } from "../lib/labels.js";

const ROLE_HOME = {
  issuer: {
    kicker: "Espace émetteur",
    icon: UploadCloud,
    title: "Le prochain exercice commence ici.",
    text: "Déposez le PDF, laissez l’extraction vérifier les comptes, puis scellez la preuve sur Hedera.",
    action: { to: "/depots/nouveau", label: "Déposer un état financier" },
  },
  broker: {
    kicker: "Desk marchés",
    icon: BarChart3,
    title: "Cinq exercices, une seule source de vérité.",
    text: "Comparez les états financiers, téléchargez le rapport vérifié et contrôlez la preuve on-chain.",
    actionLabel: "Ouvrir le dernier dépôt",
  },
  verifier: {
    kicker: "Audit & conformité",
    icon: ShieldCheck,
    title: "Chaque chiffre possède une empreinte.",
    text: "Inspectez la chaîne HCS, le credential NFT et les métadonnées HFS sans dépendre de la base de données.",
    actionLabel: "Vérifier le dernier dépôt",
  },
  admin: {
    kicker: "Opérations",
    icon: Landmark,
    title: "Le registre, sous contrôle.",
    text: "Supervisez les dépôts, accompagnez les émetteurs et contrôlez l’intégrité de la chaîne.",
    action: { to: "/depots/nouveau", label: "Déposer un état financier" },
  },
};

function displayIssuer(issuer) {
  return issuer === "SAH" ? "SAH Lilas" : issuer;
}

export function Deposits() {
  const { user } = useAuth();
  const [filings, setFilings] = useState([]);
  const [details, setDetails] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await api.listFilings();
        if (!active) {
          return;
        }
        const items = [...(data.items || [])].sort((left, right) =>
          right.period.localeCompare(left.period)
        );
        setFilings(items);
        const results = await Promise.allSettled(
          items
            .filter((item) => item.status !== "failed")
            .map((item) => api.getFiling(item.id))
        );
        if (!active) {
          return;
        }
        const next = {};
        results.forEach((result) => {
          if (result.status === "fulfilled") {
            next[result.value.id] = result.value;
          }
        });
        setDetails(next);
      } catch (err) {
        if (active) {
          setError(err.message || "Impossible de charger le registre.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  const latest = filings[0] || null;
  const sealed = filings.filter((filing) => filing.status === "sealed");
  const years = [...new Set(filings.map((filing) => filing.period.slice(0, 4)))];
  const ratioCount = Object.values(details).reduce(
    (total, filing) =>
      total + filing.ratios.filter((ratio) => ratio.value !== null).length,
    0
  );
  const roleHome = ROLE_HOME[user?.role] || ROLE_HOME.broker;
  const RoleIcon = roleHome.icon;

  const chartData = useMemo(() => {
    return filings
      .filter((filing) => filing.status !== "failed")
      .map((filing) => {
        const detail = details[filing.id];
        const revenue = detail?.values?.find(
          (value) => value.line_item === "chiffre_affaires"
        );
        const netIncome = detail?.values?.find(
          (value) => value.line_item === "resultat_net_part_groupe"
        );
        return {
          id: filing.id,
          year: filing.period.slice(0, 4),
          status: filing.status,
          revenue: revenue?.value ?? null,
          netIncome: netIncome?.value ?? null,
        };
      })
      .sort((left, right) => left.year.localeCompare(right.year));
  }, [filings, details]);

  const chartMax = Math.max(
    ...chartData.map((item) => Math.abs(item.revenue || 0)),
    1
  );

  const action = roleHome.action || (latest ? { to: `/depots/${latest.id}`, label: roleHome.actionLabel } : null);

  return (
    <div className="stack-lg">
      <header className="page-head">
        <div>
          <span className="page-kicker">
            <Landmark size={15} />
            Registre vérifié · {roleLabel(user?.role)}
          </span>
          <h1 className="page-title">Dépôts</h1>
          <p className="page-sub">
            Les états financiers déposés, extraits, validés et scellés sur Hedera.
          </p>
        </div>
        {action && (
          <Link className="btn btn-primary" to={action.to}>
            {user?.role === "issuer" || user?.role === "admin" ? (
              <Plus size={17} />
            ) : (
              <ShieldCheck size={17} />
            )}
            {action.label}
          </Link>
        )}
      </header>

      <section className="registry-hero">
        <div className="registry-hero-copy">
          <span className="registry-kicker">
            <RoleIcon size={15} />
            {roleHome.kicker}
          </span>
          <h2>{roleHome.title}</h2>
          <p>{roleHome.text}</p>
          <div className="registry-hero-meta">
            <span>
              <Building2 size={15} />
              SAH Lilas
            </span>
            <span>
              <CalendarRange size={15} />
              {years.length > 0
                ? `${years[years.length - 1]}–${years[0]}`
                : "Aucun exercice"}
            </span>
            <span>
              <FileText size={15} />
              {filings.length} dépôt{filings.length > 1 ? "s" : ""}
            </span>
          </div>
        </div>
        <div className="registry-seal">
          <span className="registry-seal-icon">
            <BadgeCheck size={26} />
          </span>
          <div>
            <strong>{sealed.length} dépôts scellés</strong>
            <span>
              {latest
                ? `Dernier exercice : ${formatPeriod(latest.period)}`
                : "En attente du premier dépôt"}
            </span>
          </div>
          <span className="registry-seal-pill">
            <span className="network-dot" />
            Hedera testnet
          </span>
        </div>
      </section>

      <section className="metric-grid" aria-label="Indicateurs du registre">
        <article className="metric-card">
          <span className="metric-icon metric-icon--emerald">
            <CalendarRange size={18} />
          </span>
          <div>
            <span className="metric-label">Couverture</span>
            <strong>{years.length} exercices</strong>
            <span className="metric-note">
              {years.length > 0
                ? `${years[years.length - 1]} à ${years[0]}`
                : "Aucune période"}
            </span>
          </div>
        </article>
        <article className="metric-card">
          <span className="metric-icon metric-icon--blue">
            <ShieldCheck size={18} />
          </span>
          <div>
            <span className="metric-label">Preuves scellées</span>
            <strong>{sealed.length} / {filings.length || 0}</strong>
            <span className="metric-note">Credential NFT par exercice</span>
          </div>
        </article>
        <article className="metric-card">
          <span className="metric-icon metric-icon--amber">
            <CheckCircle2 size={18} />
          </span>
          <div>
            <span className="metric-label">Ratios calculés</span>
            <strong>{loading ? "…" : ratioCount}</strong>
            <span className="metric-note">Déterministes, sans IA</span>
          </div>
        </article>
        <article className="metric-card">
          <span className="metric-icon metric-icon--slate">
            <FileText size={18} />
          </span>
          <div>
            <span className="metric-label">Contrôles par dépôt</span>
            <strong>12</strong>
            <span className="metric-note">Chaîne, hash, NFT et HFS</span>
          </div>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="card panel chart-panel">
          <div className="card-head">
            <div>
              <span className="page-kicker">
                <BarChart3 size={15} />
                Trajectoire
              </span>
              <h2 className="section-title">Chiffre d’affaires</h2>
            </div>
            <span className="tag">MTND</span>
          </div>
          {loading ? (
            <div className="chart-skeleton" aria-hidden="true">
              {[62, 74, 68, 82, 91].map((height, index) => (
                <span key={index} style={{ height: `${height}%` }} />
              ))}
            </div>
          ) : chartData.length > 0 ? (
            <div className="bar-chart" role="img" aria-label="Chiffre d’affaires par exercice">
              {chartData.map((item) => {
                const height = item.revenue
                  ? Math.max(8, (Math.abs(item.revenue) / chartMax) * 100)
                  : 4;
                return (
                  <Link
                    to={`/depots/${item.id}`}
                    className="bar-column"
                    key={item.id}
                    title={
                      item.revenue
                        ? `${item.year} · ${formatMTND(item.revenue)}`
                        : `${item.year} · non disponible`
                    }
                  >
                    <span className="bar-value">
                      {item.revenue ? formatMTND(item.revenue) : "—"}
                    </span>
                    <span className="bar-track">
                      <span
                        className={`bar-fill${item.status === "sealed" ? " is-sealed" : ""}`}
                        style={{ height: `${height}%` }}
                      />
                    </span>
                    <span className="bar-year">{item.year}</span>
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              <BarChart3 size={24} />
              <strong>Aucune donnée financière</strong>
              <span>Le graphique apparaîtra après le premier dépôt extrait.</span>
            </div>
          )}
        </article>

        <article className="card panel last-seal">
          <div className="card-head">
            <div>
              <span className="page-kicker">
                <Sparkles size={15} />
                Dernière preuve
              </span>
              <h2 className="section-title">
                {latest ? formatPeriod(latest.period) : "Aucun dépôt"}
              </h2>
            </div>
            {latest && <StatusBadge status={latest.status} />}
          </div>
          {latest ? (
            <div className="proof-list">
              <div className="proof-list-row">
                <span>Émetteur</span>
                <strong>{displayIssuer(latest.issuer)}</strong>
              </div>
              <div className="proof-list-row">
                <span>Événements HCS</span>
                <code>{details[latest.id]?.timeline_count ?? "—"}</code>
              </div>
              <div className="proof-list-row">
                <span>Credential NFT</span>
                <code>
                  {latest.token_id
                    ? `${latest.token_id} · #${latest.serial}`
                    : "Non scellé"}
                </code>
              </div>
              <div className="proof-list-row">
                <span>Empreinte PDF</span>
                <code>{shortHash(latest.doc_sha256, 6)}</code>
              </div>
              <div className="proof-list-row">
                <span>Déposé le</span>
                <strong>{formatDate(latest.created_at)}</strong>
              </div>
              <Link className="btn btn-ghost btn-block" to={`/depots/${latest.id}`}>
                Ouvrir le dossier
                <ArrowRight size={16} />
              </Link>
            </div>
          ) : (
            <div className="empty-state">
              <FileText size={24} />
              <strong>Le registre est vide</strong>
              <span>Déposez un premier état financier pour créer une preuve.</span>
            </div>
          )}
        </article>
      </section>

      <section className="card panel registry-list">
        <div className="card-head registry-list-head">
          <div>
            <span className="page-kicker">
              <Landmark size={15} />
              Registre
            </span>
            <h2 className="section-title">Exercices déposés</h2>
          </div>
          <span className="muted registry-count">
            {filings.length} dossier{filings.length > 1 ? "s" : ""}
          </span>
        </div>

        {error && (
          <div className="inline-message is-error" role="alert">
            {error}
          </div>
        )}

        {loading ? (
          <div className="filing-skeleton" aria-label="Chargement du registre">
            {[1, 2, 3].map((item) => (
              <div className="filing-skeleton-row" key={item}>
                <span />
                <span />
                <span />
              </div>
            ))}
          </div>
        ) : filings.length === 0 ? (
          <div className="empty-state">
            <Landmark size={26} />
            <strong>Aucun dépôt</strong>
            <span>Les états financiers déposés apparaîtront ici.</span>
          </div>
        ) : (
          <div className="filing-list">
            {filings.map((filing) => {
              const detail = details[filing.id];
              const revenue = detail?.values?.find(
                (value) => value.line_item === "chiffre_affaires"
              )?.value;
              const netIncome = detail?.values?.find(
                (value) => value.line_item === "resultat_net_part_groupe"
              )?.value;
              return (
                <Link
                  to={`/depots/${filing.id}`}
                  className="filing-row"
                  key={filing.id}
                >
                  <span className="filing-year">
                    <strong>{filing.period.slice(0, 4)}</strong>
                    <span>Exercice</span>
                  </span>
                  <span className="filing-issuer">
                    <span className="filing-issuer-icon">
                      <Building2 size={17} />
                    </span>
                    <span>
                      <strong>{displayIssuer(filing.issuer)}</strong>
                      <span>
                        {filing.sector === "industrial"
                          ? "Industrie"
                          : filing.sector}
                        {" · "}
                        {detail?.consolidation === "individuel"
                          ? "Individuel"
                          : detail?.consolidation || "États financiers"}
                      </span>
                    </span>
                  </span>
                  <span className="filing-metrics">
                    <span>
                      <span className="filing-metric-label">CA</span>
                      <strong>{formatMTND(revenue)}</strong>
                    </span>
                    <span>
                      <span className="filing-metric-label">Résultat net</span>
                      <strong>{formatMTND(netIncome)}</strong>
                    </span>
                  </span>
                  <span className="filing-proof">
                    <StatusBadge status={filing.status} size="sm" />
                    <code>
                      {filing.token_id
                        ? `#${filing.serial} · ${filing.token_id}`
                        : shortHash(filing.doc_sha256, 5)}
                    </code>
                  </span>
                  <span className="filing-open">
                    <ArrowRight size={17} />
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
