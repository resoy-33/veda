import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  ListChecks,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { api } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { StatusBadge } from "../components/StatusBadge.jsx";
import { formatPeriod } from "../lib/format.js";
import { VERIFICATION_LABELS } from "../lib/ratios.js";

const ALLOWED_ROLES = ["broker", "verifier", "admin"];

function issuerName(issuer) {
  return issuer === "SAH" ? "SAH Lilas" : issuer;
}

export function Verification() {
  const { user } = useAuth();
  const allowed = ALLOWED_ROLES.includes(user?.role);
  const [filings, setFilings] = useState([]);
  const [jobs, setJobs] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
        const data = await api.listFilings();
        if (!active) {
          return;
        }
        setFilings(
          [...(data.items || [])]
            .filter((filing) => filing.token_id)
            .sort((left, right) => right.period.localeCompare(left.period))
        );
      } catch (err) {
        if (active) {
          setError(err.message || "Impossible de charger la file de vérification.");
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

  const summary = useMemo(() => {
    const results = Object.values(jobs);
    const done = results.filter((job) => job.state === "done");
    return {
      checked: done.length,
      passed: done.filter((job) => job.result?.verified).length,
      failed: done.filter((job) => job.result && !job.result.verified).length,
      running: results.filter((job) => job.state === "running").length,
    };
  }, [jobs]);

  async function handleVerify(filing) {
    setJobs((current) => ({
      ...current,
      [filing.id]: { state: "running" },
    }));
    try {
      const result = await api.verifyFiling(filing.id);
      setJobs((current) => ({
        ...current,
        [filing.id]: { state: "done", result },
      }));
    } catch (err) {
      setJobs((current) => ({
        ...current,
        [filing.id]: {
          state: "error",
          error: err.message || "La vérification a échoué.",
        },
      }));
    }
  }

  if (!allowed) {
    return (
      <div className="stack-lg">
        <header className="page-head">
          <div>
            <span className="page-kicker">
              <ShieldCheck size={15} />
              Audit & conformité
            </span>
            <h1 className="page-title">Vérification</h1>
          </div>
        </header>
        <div className="inline-message">
          Cette file de contrôle est réservée aux rôles analyste, auditeur et
          administrateur.
        </div>
      </div>
    );
  }

  return (
    <div className="stack-lg">
      <header className="page-head">
        <div>
          <span className="page-kicker">
            <ShieldCheck size={15} />
            Audit & conformité
          </span>
          <h1 className="page-title">Vérification</h1>
          <p className="page-sub">
            Reconstruisez chaque dépôt depuis Hedera : topic HCS, chaîne de
            hachage, métadonnée HFS et credential NFT.
          </p>
        </div>
      </header>

      <section className="metric-grid" aria-label="Indicateurs de vérification">
        <article className="metric-card">
          <span className="metric-icon metric-icon--blue">
            <ListChecks size={18} />
          </span>
          <div>
            <span className="metric-label">File de contrôle</span>
            <strong>{loading ? "…" : filings.length} dossiers</strong>
            <span className="metric-note">Dépôts scellés vérifiables</span>
          </div>
        </article>
        <article className="metric-card">
          <span className="metric-icon metric-icon--emerald">
            <CheckCircle2 size={18} />
          </span>
          <div>
            <span className="metric-label">Contrôles exécutés</span>
            <strong>{summary.checked}</strong>
            <span className="metric-note">
              {summary.passed} conformes · {summary.failed} anomalie
              {summary.failed > 1 ? "s" : ""}
            </span>
          </div>
        </article>
        <article className="metric-card">
          <span className="metric-icon metric-icon--slate">
            <ShieldCheck size={18} />
          </span>
          <div>
            <span className="metric-label">En cours</span>
            <strong>{summary.running}</strong>
            <span className="metric-note">Lecture du Mirror Node</span>
          </div>
        </article>
      </section>

      <section className="card panel">
        <div className="card-head registry-list-head">
          <div>
            <span className="page-kicker">
              <ListChecks size={15} />
              File de vérification
            </span>
            <h2 className="section-title">Dépôts scellés</h2>
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
          <div className="filing-skeleton" aria-label="Chargement de la file">
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
            <ShieldCheck size={26} />
            <strong>Aucun dépôt scellé</strong>
            <span>Les dossiers scellés apparaîtront ici pour contrôle.</span>
          </div>
        ) : (
          <div className="verify-queue">
            {filings.map((filing) => {
              const job = jobs[filing.id];
              const checks = job?.result?.checks || [];
              const passed = checks.filter((check) => check.status === "pass").length;
              const firstFailure = checks.find((check) => check.status !== "pass");
              return (
                <article className="verify-row" key={filing.id}>
                  <span className="filing-year">
                    <strong>{filing.period.slice(0, 4)}</strong>
                    <span>Exercice</span>
                  </span>
                  <div className="verify-main">
                    <strong>{issuerName(filing.issuer)}</strong>
                    <span>
                      {formatPeriod(filing.period)} · NFT {filing.token_id} #
                      {filing.serial}
                    </span>
                    <code>{filing.topic_id}</code>
                  </div>
                  <div className="verify-state">
                    {job?.state === "running" ? (
                      <span className="verify-running">
                        <LoaderCircle className="spin" size={15} />
                        Lecture Hedera
                      </span>
                    ) : job?.state === "done" ? (
                      <span
                        className={`verdict-pill ${
                          job.result?.verified ? "is-pass" : "is-fail"
                        }`}
                      >
                        {passed}/{checks.length || 12}
                      </span>
                    ) : job?.state === "error" ? (
                      <span className="verdict-pill is-fail">Erreur</span>
                    ) : (
                      <StatusBadge status={filing.status} size="sm" />
                    )}
                    {job?.state === "done" && (
                      <span className="verify-detail">
                        {job.result?.verified
                          ? "Toutes les empreintes concordent"
                          : firstFailure
                          ? VERIFICATION_LABELS[firstFailure.check] ||
                            firstFailure.check
                          : "Contrôle incomplet"}
                      </span>
                    )}
                    {job?.state === "error" && (
                      <span className="verify-detail">{job.error}</span>
                    )}
                  </div>
                  <div className="verify-actions">
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => handleVerify(filing)}
                      disabled={job?.state === "running"}
                    >
                      {job?.state === "running" ? (
                        <LoaderCircle className="spin" size={15} />
                      ) : job?.state === "done" ? (
                        <RefreshCw size={15} />
                      ) : (
                        <ShieldCheck size={15} />
                      )}
                      {job?.state === "done" ? "Relancer" : "Vérifier"}
                    </button>
                    <Link className="verify-link" to={`/depots/${filing.id}`}>
                      Dossier
                      <ArrowRight size={15} />
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
