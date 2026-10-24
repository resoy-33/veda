import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  Database,
  LoaderCircle,
  RefreshCw,
  ServerCog,
  ShieldCheck,
} from "lucide-react";
import { api } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { StatusBadge } from "../components/StatusBadge.jsx";
import { formatDate, formatPeriod } from "../lib/format.js";

function issuerName(issuer) {
  return issuer === "SAH" ? "SAH Lilas" : issuer;
}

export function Operations() {
  const { user } = useAuth();
  const allowed = user?.role === "admin";
  const [health, setHealth] = useState(null);
  const [filings, setFilings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rebuilding, setRebuilding] = useState(false);
  const [rebuildResult, setRebuildResult] = useState(null);
  const [rebuildError, setRebuildError] = useState("");

  useEffect(() => {
    if (!allowed) {
      setLoading(false);
      return undefined;
    }
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [healthData, filingData] = await Promise.all([
          api.health(),
          api.listFilings(),
        ]);
        if (!active) {
          return;
        }
        setHealth(healthData);
        setFilings(
          [...(filingData.items || [])].sort((left, right) =>
            right.period.localeCompare(left.period)
          )
        );
      } catch (err) {
        if (active) {
          setError(err.message || "Impossible de charger l’état du système.");
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
  }, [allowed]);

  const counts = useMemo(() => {
    return {
      sealed: filings.filter((filing) => filing.status === "sealed").length,
      topics: filings.filter((filing) => filing.topic_id).length,
      latest: filings[0] || null,
    };
  }, [filings]);

  async function handleRebuild() {
    setRebuilding(true);
    setRebuildError("");
    setRebuildResult(null);
    try {
      const result = await api.rebuildCache();
      setRebuildResult(result);
      const refreshed = await api.listFilings();
      setFilings(
        [...(refreshed.items || [])].sort((left, right) =>
          right.period.localeCompare(left.period)
        )
      );
    } catch (err) {
      setRebuildError(err.message || "La reconstruction du cache a échoué.");
    } finally {
      setRebuilding(false);
    }
  }

  if (!allowed) {
    return (
      <div className="stack-lg">
        <header className="page-head">
          <div>
            <span className="page-kicker">
              <ServerCog size={15} />
              Opérations
            </span>
            <h1 className="page-title">Système</h1>
          </div>
        </header>
        <div className="inline-message">
          L’espace d’exploitation est réservé au rôle administrateur.
        </div>
      </div>
    );
  }

  return (
    <div className="stack-lg">
      <header className="page-head">
        <div>
          <span className="page-kicker">
            <ServerCog size={15} />
            Opérations
          </span>
          <h1 className="page-title">Système</h1>
          <p className="page-sub">
            Supervision du registre, de la base cache et de la reconstruction
            depuis la chaîne Hedera.
          </p>
        </div>
      </header>

      <section className="metric-grid" aria-label="État du système">
        <article className="metric-card">
          <span className="metric-icon metric-icon--emerald">
            <CheckCircle2 size={18} />
          </span>
          <div>
            <span className="metric-label">Service API</span>
            <strong>{loading ? "…" : health?.status === "ok" ? "En ligne" : "Indisponible"}</strong>
            <span className="metric-note">Version {health?.version || "—"}</span>
          </div>
        </article>
        <article className="metric-card">
          <span className="metric-icon metric-icon--blue">
            <Database size={18} />
          </span>
          <div>
            <span className="metric-label">Base cache</span>
            <strong>{loading ? "…" : health?.db ? "Connectée" : "Hors ligne"}</strong>
            <span className="metric-note">Reconstructible depuis HCS</span>
          </div>
        </article>
        <article className="metric-card">
          <span className="metric-icon metric-icon--amber">
            <ShieldCheck size={18} />
          </span>
          <div>
            <span className="metric-label">Dossiers ancrés</span>
            <strong>{counts.sealed} / {filings.length}</strong>
            <span className="metric-note">{counts.topics} topics HCS</span>
          </div>
        </article>
        <article className="metric-card">
          <span className="metric-icon metric-icon--slate">
            <ServerCog size={18} />
          </span>
          <div>
            <span className="metric-label">Dernier dépôt</span>
            <strong>
              {counts.latest ? formatPeriod(counts.latest.period) : "Aucun"}
            </strong>
            <span className="metric-note">
              {counts.latest ? formatDate(counts.latest.created_at) : "Registre vide"}
            </span>
          </div>
        </article>
      </section>

      <section className="ops-grid">
        <article className="card panel">
          <div className="card-head">
            <div>
              <span className="page-kicker">
                <RefreshCw size={15} />
                Maintenance
              </span>
              <h2 className="section-title">Reconstruire le cache</h2>
            </div>
          </div>
          <p className="verification-copy">
            Relit les topics HCS, les fichiers HFS et les credentials NFT, puis
            régénère la base locale. La chaîne reste l’unique source de vérité.
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleRebuild}
            disabled={rebuilding}
          >
            {rebuilding ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <RefreshCw size={16} />
            )}
            {rebuilding ? "Reconstruction en cours…" : "Lancer la reconstruction"}
          </button>
          {rebuildError && (
            <div className="inline-message is-error" role="alert">
              {rebuildError}
            </div>
          )}
          {rebuildResult && (
            <div className="ops-result">
              <span className="verdict-pill is-pass">Cache reconstruit</span>
              <span>
                {rebuildResult.filings} dossier
                {rebuildResult.filings > 1 ? "s" : ""} · {rebuildResult.events}{" "}
                événement{rebuildResult.events > 1 ? "s" : ""}
              </span>
            </div>
          )}
        </article>

        <article className="card panel">
          <div className="card-head">
            <div>
              <span className="page-kicker">
                <ShieldCheck size={15} />
                Réseau
              </span>
              <h2 className="section-title">Hedera testnet</h2>
            </div>
            <span className="network-pill">
              <span className="network-dot" />
              Connecté
            </span>
          </div>
          <div className="proof-list">
            <div className="proof-list-row">
              <span>Réseau</span>
              <strong>Hedera testnet</strong>
            </div>
            <div className="proof-list-row">
              <span>Journal</span>
              <strong>HCS par dépôt</strong>
            </div>
            <div className="proof-list-row">
              <span>Métadonnées</span>
              <strong>HFS immuable</strong>
            </div>
            <div className="proof-list-row">
              <span>Credential</span>
              <strong>NFT par exercice</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="card panel">
        <div className="card-head registry-list-head">
          <div>
            <span className="page-kicker">
              <ServerCog size={15} />
              Inventaire
            </span>
            <h2 className="section-title">Dossiers et preuves</h2>
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
          <div className="filing-skeleton" aria-label="Chargement de l’inventaire">
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
            <ServerCog size={26} />
            <strong>Aucun dossier</strong>
            <span>Les dépôts ancrés apparaîtront dans cet inventaire.</span>
          </div>
        ) : (
          <div className="value-table-wrap">
            <table className="value-table ops-table">
              <thead>
                <tr>
                  <th>Exercice</th>
                  <th>Émetteur</th>
                  <th>Statut</th>
                  <th>Topic HCS</th>
                  <th>Credential NFT</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filings.map((filing) => (
                  <tr key={filing.id}>
                    <td>
                      <strong>{filing.period.slice(0, 4)}</strong>
                    </td>
                    <td>{issuerName(filing.issuer)}</td>
                    <td>
                      <StatusBadge status={filing.status} size="sm" />
                    </td>
                    <td>
                      <code>{filing.topic_id || "—"}</code>
                    </td>
                    <td>
                      <code>
                        {filing.token_id
                          ? `${filing.token_id} #${filing.serial}`
                          : "—"}
                      </code>
                    </td>
                    <td>
                      <Link className="verify-link" to={`/depots/${filing.id}`}>
                        Dossier
                        <ArrowRight size={14} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
