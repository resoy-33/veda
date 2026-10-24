import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  BarChart3,
  Building2,
  CalendarRange,
  CheckCircle2,
  CircleDollarSign,
  Download,
  FileCheck2,
  FileSpreadsheet,
  FileText,
  Fingerprint,
  Hash,
  Landmark,
  Link2,
  LoaderCircle,
  LockKeyhole,
  ScanLine,
  ShieldCheck,
  TrendingUp,
  Wallet,
  XCircle,
} from "lucide-react";
import { api } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { StatusBadge } from "../components/StatusBadge.jsx";
import {
  EVENT_LABELS,
  fileSize,
  formatDate,
  formatDateTime,
  formatMTND,
  formatNumber,
  formatPeriod,
  formatRatioValue,
  formatTND,
  shortHash,
} from "../lib/format.js";
import { roleLabel } from "../lib/labels.js";
import {
  CHECK_LABELS,
  VERIFICATION_LABELS,
  groupRatios,
  groupValues,
} from "../lib/ratios.js";

const TABS = [
  { id: "synthese", label: "Synthèse", icon: BarChart3 },
  { id: "extraction", label: "Extraction", icon: ScanLine },
  { id: "comptes", label: "Comptes extraits", icon: FileText },
  { id: "ratios", label: "Ratios", icon: TrendingUp },
  { id: "rapport", label: "Rapport XLSX", icon: FileSpreadsheet },
  { id: "preuve", label: "Preuve on-chain", icon: ShieldCheck },
];

const EVENT_ICONS = {
  filing_submitted: FileText,
  extracted: ScanLine,
  validated: FileCheck2,
  sealed: LockKeyhole,
};

const HIGHLIGHT_RATIOS = [
  { code: "marge_nette", label: "Marge nette" },
  { code: "roe", label: "ROE" },
  { code: "gearing", label: "Gearing" },
  { code: "dette_nette_ebitda", label: "Dette nette / EBITDA" },
  { code: "liquidite_generale", label: "Liquidité générale" },
  { code: "cfo_sur_ebitda", label: "CFO / EBITDA" },
];

function displayIssuer(issuer) {
  return issuer === "SAH" ? "SAH Lilas" : issuer;
}

function confidenceTone(value) {
  if (value >= 0.95) {
    return "is-high";
  }
  if (value >= 0.85) {
    return "is-mid";
  }
  return "is-low";
}

function eventDetail(event) {
  const payload = event.payload || {};
  if (event.event === "extracted") {
    return `${payload.line_count ?? "—"} lignes · ${payload.model || "déterministe"}`;
  }
  if (event.event === "validated") {
    return `Verdict ${payload.verdict === "pass" ? "conforme" : "non conforme"} · ${
      payload.checks?.length ?? 0
    } contrôles`;
  }
  if (event.event === "sealed") {
    const credential = payload.credential || payload;
    return `NFT ${credential.token_id || "—"} · serial ${
      credential.serial ?? "—"
    }`;
  }
  const size = payload.size ?? payload.byte_length;
  return size ? fileSize(size) : "PDF source horodaté";
}

function reportCell(value) {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "number") {
    return new Intl.NumberFormat("fr-FR", {
      maximumFractionDigits: 3,
    }).format(value);
  }
  return String(value);
}

export function FilingDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [filing, setFiling] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("synthese");
  const [verifying, setVerifying] = useState(false);
  const [verification, setVerification] = useState(null);
  const [verifyError, setVerifyError] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [reportHash, setReportHash] = useState("");
  const [reportPreview, setReportPreview] = useState(null);
  const [reportSheet, setReportSheet] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      setVerification(null);
      setVerifyError("");
      setReportHash("");
      setReportPreview(null);
      setReportSheet("");
      setPreviewError("");
      setPreviewLoading(false);
      try {
        const [detail, events] = await Promise.all([
          api.getFiling(id),
          api.getTimeline(id),
        ]);
        if (active) {
          setFiling(detail);
          setTimeline(events);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Impossible de charger ce dépôt.");
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
  }, [id]);

  const valueMap = useMemo(() => {
    const map = new Map();
    (filing?.values || []).forEach((value) => map.set(value.line_item, value));
    return map;
  }, [filing]);

  const ratioMap = useMemo(() => {
    const map = new Map();
    (filing?.ratios || []).forEach((ratio) => map.set(ratio.code, ratio));
    return map;
  }, [filing]);

  const events = timeline?.events || [];
  const extractedEvent = events.find((event) => event.event === "extracted");
  const validatedEvent = events.find((event) => event.event === "validated");
  const sealedEvent = events.find((event) => event.event === "sealed");
  const sealedCredential = sealedEvent?.payload?.credential || {};
  const validationChecks = validatedEvent?.payload?.checks || [];
  const validationVerdict = validatedEvent?.payload?.verdict;
  const canVerify = ["broker", "verifier", "admin"].includes(user?.role);

  async function handleVerify() {
    setVerifying(true);
    setVerifyError("");
    setTab("preuve");
    try {
      const result = await api.verifyFiling(id);
      setVerification(result);
      const refreshed = await api.getTimeline(id);
      setTimeline(refreshed);
    } catch (err) {
      setVerifyError(err.message || "La vérification Hedera a échoué.");
    } finally {
      setVerifying(false);
    }
  }

  async function handleDownload() {
    setDownloading(true);
    setReportHash("");
    try {
      const response = await api.downloadReport(id);
      const blob = await response.blob();
      const disposition = response.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="?([^";]+)"?/);
      const filename = match?.[1] || `rapport-${filing.period.slice(0, 4)}.xlsx`;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setReportHash(response.headers.get("x-report-sha256") || "");
    } catch (err) {
      setVerifyError(err.message || "Le rapport n’est pas disponible.");
    } finally {
      setDownloading(false);
    }
  }

  async function handleReportPreview() {
    setPreviewLoading(true);
    setPreviewError("");
    try {
      const result = await api.getReportPreview(id);
      setReportPreview(result);
      setReportSheet(result.sheets?.[0]?.name || "");
    } catch (err) {
      setPreviewError(err.message || "L’aperçu du rapport est indisponible.");
    } finally {
      setPreviewLoading(false);
    }
  }

  function handleTab(next) {
    setTab(next);
    if (next === "rapport" && !reportPreview && !previewLoading) {
      handleReportPreview();
    }
  }

  if (loading) {
    return (
      <div className="stack-lg">
        <div className="detail-skeleton">
          <span />
          <span />
          <span />
        </div>
      </div>
    );
  }

  if (error || !filing) {
    return (
      <div className="stack-lg">
        <Link className="back-link" to="/depots">
          <ArrowLeft size={16} />
          Retour au registre
        </Link>
        <section className="card empty-state detail-empty">
          <AlertTriangle size={28} />
          <strong>Dépôt introuvable</strong>
          <span>{error || "Ce dossier n’existe pas ou n’est plus accessible."}</span>
          <Link className="btn btn-ghost" to="/depots">
            Revenir aux dépôts
          </Link>
        </section>
      </div>
    );
  }

  const kpis = [
    {
      label: "Chiffre d’affaires",
      value: valueMap.get("chiffre_affaires")?.value,
      icon: CircleDollarSign,
      tone: "emerald",
      note: "Produits de l’exercice",
      format: formatMTND,
    },
    {
      label: "EBITDA",
      value: ratioMap.get("ebitda")?.value,
      icon: BarChart3,
      tone: "blue",
      note: "Résultat opérationnel avant amortissements",
      format: formatMTND,
    },
    {
      label: "Résultat net",
      value: valueMap.get("resultat_net_part_groupe")?.value,
      icon: TrendingUp,
      tone: "amber",
      note: "Part du groupe",
      format: formatMTND,
    },
    {
      label: "Free cash flow",
      value: ratioMap.get("free_cash_flow")?.value,
      icon: Wallet,
      tone: "slate",
      note: "CFO moins investissements",
      format: formatMTND,
    },
  ];

  const ratioGroups = groupRatios(filing.ratios || []);
  const valueGroups = groupValues(filing.values || []);
  const passedChecks = validationChecks.filter(
    (check) => check.status === "pass"
  ).length;
  const verificationChecks = verification?.checks || [];
  const verificationPassed = verificationChecks.filter(
    (check) => check.status === "pass"
  ).length;
  const pageCount = filing.values?.length
    ? Math.max(...filing.values.map((value) => value.page))
    : 0;
  const reportSheetData =
    reportPreview?.sheets?.find((sheet) => sheet.name === reportSheet) ||
    reportPreview?.sheets?.[0];

  return (
    <div className="stack-lg">
      <div className="detail-top">
        <Link className="back-link" to="/depots">
          <ArrowLeft size={16} />
          Registre des dépôts
        </Link>
        <span className="detail-role">
          <ShieldCheck size={14} />
          {roleLabel(user?.role)}
        </span>
      </div>

      <header className="detail-head">
        <div className="detail-title">
          <span className="page-kicker">
            <Landmark size={15} />
            Dossier de preuve · {formatPeriod(filing.period)}
          </span>
          <div className="detail-title-row">
            <h1>{displayIssuer(filing.issuer)}</h1>
            <StatusBadge status={filing.status} size="lg" />
          </div>
          <p className="page-sub">
            {formatPeriod(filing.period)} ·{" "}
            {filing.consolidation === "individuel"
              ? "états individuels"
              : filing.consolidation}{" "}
            · {filing.sector === "industrial" ? "industrie" : filing.sector} ·{" "}
            {filing.unit}
          </p>
        </div>
        <div className="detail-actions">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={handleDownload}
            disabled={downloading}
          >
            {downloading ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <Download size={16} />
            )}
            Rapport XLSX
          </button>
          {canVerify && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleVerify}
              disabled={verifying || !filing.token_id}
            >
              {verifying ? (
                <LoaderCircle className="spin" size={16} />
              ) : (
                <ShieldCheck size={16} />
              )}
              Vérifier sur Hedera
            </button>
          )}
        </div>
      </header>

      {reportHash && (
        <div className="inline-message is-success" role="status">
          Rapport téléchargé · SHA-256 {shortHash(reportHash, 12)}
        </div>
      )}
      {verifyError && (
        <div className="inline-message is-error" role="alert">
          {verifyError}
        </div>
      )}

      <section className="metric-grid detail-metrics" aria-label="Indicateurs clés">
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <article className="metric-card" key={kpi.label}>
              <span className={`metric-icon metric-icon--${kpi.tone}`}>
                <Icon size={18} />
              </span>
              <div>
                <span className="metric-label">{kpi.label}</span>
                <strong>{kpi.format(kpi.value)}</strong>
                <span className="metric-note">{kpi.note}</span>
              </div>
            </article>
          );
        })}
      </section>

      <nav className="detail-tabs" role="tablist" aria-label="Sections du dépôt">
        {TABS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              type="button"
              role="tab"
              key={item.id}
              aria-selected={tab === item.id}
              aria-controls={`panel-${item.id}`}
              className={`detail-tab${tab === item.id ? " is-active" : ""}`}
              onClick={() => handleTab(item.id)}
            >
              <Icon size={16} />
              {item.label}
            </button>
          );
        })}
      </nav>

      {tab === "synthese" && (
        <div
          className="detail-panel"
          id="panel-synthese"
          role="tabpanel"
          aria-label="Synthèse"
        >
          <div className="detail-grid">
            <section className="card panel">
              <div className="card-head">
                <div>
                  <span className="page-kicker">
                    <FileText size={15} />
                    Identité
                  </span>
                  <h2 className="section-title">Fiche du dépôt</h2>
                </div>
              </div>
              <div className="detail-list">
                <div>
                  <span>Émetteur</span>
                  <strong>{displayIssuer(filing.issuer)}</strong>
                </div>
                <div>
                  <span>Exercice</span>
                  <strong>{formatPeriod(filing.period)}</strong>
                </div>
                <div>
                  <span>Périmètre</span>
                  <strong>
                    {filing.consolidation === "individuel"
                      ? "Individuel"
                      : filing.consolidation}
                  </strong>
                </div>
                <div>
                  <span>Secteur</span>
                  <strong>{filing.sector}</strong>
                </div>
                <div>
                  <span>Unité</span>
                  <strong>{filing.unit}</strong>
                </div>
                <div>
                  <span>Déposé le</span>
                  <strong>{formatDate(filing.created_at)}</strong>
                </div>
                <div>
                  <span>Lignes extraites</span>
                  <strong>{formatNumber(filing.values.length, 0)}</strong>
                </div>
                <div>
                  <span>Ratios calculés</span>
                  <strong>
                    {formatNumber(
                      filing.ratios.filter((ratio) => ratio.value !== null).length,
                      0
                    )}
                  </strong>
                </div>
              </div>
            </section>

            <section className="card panel">
              <div className="card-head">
                <div>
                  <span className="page-kicker">
                    <CheckCircle2 size={15} />
                    Contrôles déterministes
                  </span>
                  <h2 className="section-title">Validation comptable</h2>
                </div>
                <span
                  className={`verdict-pill ${
                    validationVerdict === "pass" ? "is-pass" : "is-fail"
                  }`}
                >
                  {validationVerdict === "pass" ? "Conforme" : "À revoir"}
                </span>
              </div>
              <div className="check-list">
                {validationChecks.map((check) => (
                  <div className="check-row" key={check.id}>
                    {check.status === "pass" ? (
                      <CheckCircle2 className="check-icon is-pass" size={17} />
                    ) : (
                      <XCircle className="check-icon is-fail" size={17} />
                    )}
                    <div>
                      <strong>{CHECK_LABELS[check.id] || check.id}</strong>
                      <span>{check.detail}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="check-foot">
                <span>
                  <BadgeCheck size={16} />
                  {passedChecks} / {validationChecks.length || 7} contrôles passés
                </span>
                <span className="tag">Sans IA</span>
              </div>
            </section>
          </div>

          <section className="card panel">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <TrendingUp size={15} />
                  Lecture rapide
                </span>
                <h2 className="section-title">Ratios clés</h2>
              </div>
              <span className="tag">{filing.ratios[0]?.formula_version ? `Formules v${filing.ratios[0].formula_version}` : "Déterministe"}</span>
            </div>
            <div className="highlight-grid">
              {HIGHLIGHT_RATIOS.map((item) => {
                const ratio = ratioMap.get(item.code);
                return (
                  <div className="highlight-card" key={item.code}>
                    <span>{ratio?.name || item.label}</span>
                    <strong>{formatRatioValue(item.code, ratio?.value)}</strong>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="card panel">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <Fingerprint size={15} />
                  Empreintes
                </span>
                <h2 className="section-title">Chaîne de confiance</h2>
              </div>
            </div>
            <div className="hash-grid">
              <div className="hash-card">
                <span>PDF source</span>
                <code>{filing.doc_sha256}</code>
              </div>
              <div className="hash-card">
                <span>Extraction</span>
                <code>{extractedEvent?.payload?.extraction_sha256 || "—"}</code>
              </div>
              <div className="hash-card">
                <span>Ratios</span>
                <code>{validatedEvent?.payload?.ratios_sha256 || "—"}</code>
              </div>
              <div className="hash-card">
                <span>Rapport XLSX</span>
                <code>{sealedEvent?.payload?.report_sha256 || reportHash || "—"}</code>
              </div>
            </div>
          </section>
        </div>
      )}

      {tab === "extraction" && (
        <div
          className="detail-panel"
          id="panel-extraction"
          role="tabpanel"
          aria-label="Extraction"
        >
          <section className="card panel">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <ScanLine size={15} />
                  Pipeline déterministe
                </span>
                <h2 className="section-title">Du PDF au credential</h2>
              </div>
              <span className="tag">{events.length} événements</span>
            </div>
            {events.length === 0 ? (
              <div className="empty-state">
                <ScanLine size={24} />
                <strong>Aucun événement</strong>
                <span>Le pipeline n’a pas encore démarré pour ce dépôt.</span>
              </div>
            ) : (
              <div className="pipeline-list">
                {events.map((event, index) => {
                  const Icon = EVENT_ICONS[event.event] || FileText;
                  return (
                    <article className="pipeline-item" key={`${event.sequence}-${event.event}`}>
                      <span className="pipeline-marker">
                        <Icon size={18} />
                      </span>
                      <div className="pipeline-copy">
                        <div className="pipeline-head">
                          <strong>{EVENT_LABELS[event.event] || event.event}</strong>
                          <span>#{event.sequence}</span>
                        </div>
                        <span className="pipeline-detail">{eventDetail(event)}</span>
                        <div className="pipeline-meta">
                          <span>{formatDateTime(event.ts)}</span>
                          <code>{event.actor}</code>
                          <span>{event.role}</span>
                        </div>
                        <div className="pipeline-hashes">
                          <span>prev</span>
                          <code title={event.prev_hash}>{shortHash(event.prev_hash, 8)}</code>
                          <ArrowRight size={12} />
                          <code title={event.hash}>{shortHash(event.hash, 8)}</code>
                        </div>
                      </div>
                      <span className="pipeline-index">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                    </article>
                  );
                })}
              </div>
            )}
          </section>

          <section className="card panel">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <Fingerprint size={15} />
                  Empreintes
                </span>
                <h2 className="section-title">Chaîne de confiance</h2>
              </div>
            </div>
            <div className="hash-grid">
              <div className="hash-card">
                <span>PDF source</span>
                <code>{filing.doc_sha256}</code>
              </div>
              <div className="hash-card">
                <span>Extraction</span>
                <code>{extractedEvent?.payload?.extraction_sha256 || "—"}</code>
              </div>
              <div className="hash-card">
                <span>Ratios</span>
                <code>{validatedEvent?.payload?.ratios_sha256 || "—"}</code>
              </div>
              <div className="hash-card">
                <span>Rapport XLSX</span>
                <code>{sealedEvent?.payload?.report_sha256 || reportHash || "—"}</code>
              </div>
            </div>
            <div className="detail-list detail-list--compact">
              <div>
                <span>Méthode d’extraction</span>
                <strong>{extractedEvent?.payload?.model || "deterministic:pymupdf"}</strong>
              </div>
              <div>
                <span>Postes extraits</span>
                <strong>{formatNumber(filing.values?.length || 0, 0)}</strong>
              </div>
              <div>
                <span>Pages parcourues</span>
                <strong>{formatNumber(pageCount, 0)}</strong>
              </div>
              <div>
                <span>Ratios calculés</span>
                <strong>
                  {formatNumber(
                    filing.ratios.filter((ratio) => ratio.value !== null).length,
                    0
                  )}{" "}
                  / {formatNumber(filing.ratios.length, 0)}
                </strong>
              </div>
              <div>
                <span>Contrôles comptables</span>
                <strong>
                  {passedChecks} / {validationChecks.length}
                </strong>
              </div>
            </div>
          </section>

          <section className="card panel">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <FileCheck2 size={15} />
                  Validation
                </span>
                <h2 className="section-title">Contrôles déterministes</h2>
              </div>
              <span
                className={`verdict-pill ${
                  validationVerdict === "pass" ? "is-pass" : "is-fail"
                }`}
              >
                {validationVerdict === "pass" ? "Conforme" : "Écart"}
              </span>
            </div>
            <div className="check-list">
              {validationChecks.map((check) => (
                <div className="check-row" key={check.id}>
                  {check.status === "pass" ? (
                    <CheckCircle2 className="check-icon is-pass" size={17} />
                  ) : (
                    <AlertTriangle className="check-icon is-fail" size={17} />
                  )}
                  <div>
                    <strong>{CHECK_LABELS[check.id] || check.id}</strong>
                    <span>{check.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="card panel">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <Hash size={15} />
                  Données ancrées
                </span>
                <h2 className="section-title">Payloads HCS</h2>
              </div>
            </div>
            <p className="verification-copy">
              Contenu exact de chaque message publié dans le topic HCS.
            </p>
            <div className="payload-list">
              {events.map((event) => (
                <details className="payload-item" key={`payload-${event.sequence}-${event.event}`}>
                  <summary>
                    <span>
                      #{event.sequence} · {EVENT_LABELS[event.event] || event.event}
                    </span>
                    <code>{shortHash(event.hash, 8)}</code>
                  </summary>
                  <pre>{JSON.stringify(event.payload, null, 2)}</pre>
                </details>
              ))}
            </div>
          </section>
        </div>
      )}

      {tab === "comptes" && (
        <div
          className="detail-panel"
          id="panel-comptes"
          role="tabpanel"
          aria-label="Comptes extraits"
        >
          {valueGroups.length === 0 ? (
            <section className="card empty-state">
              <FileText size={26} />
              <strong>Aucune valeur extraite</strong>
              <span>Le PDF n’a pas encore été traité par l’extracteur.</span>
            </section>
          ) : (
            valueGroups.map((group) => (
              <section className="card panel" key={group.id}>
                <div className="card-head">
                  <div>
                    <span className="page-kicker">
                      <FileText size={15} />
                      {group.title}
                    </span>
                    <h2 className="section-title">{group.description}</h2>
                  </div>
                  <span className="tag">{group.items.length} postes</span>
                </div>
                <div className="value-table-wrap">
                  <table className="value-table">
                    <thead>
                      <tr>
                        <th>Poste</th>
                        <th>Valeur</th>
                        <th>Page</th>
                        <th>Confiance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {group.items.map((item) => (
                        <tr key={item.line_item}>
                          <td>
                            <strong>{item.label_raw}</strong>
                            <code>{item.line_item}</code>
                            {item.snippet && (
                              <span className="value-snippet" title={item.snippet}>
                                {item.snippet}
                              </span>
                            )}
                          </td>
                          <td className="value-number">{formatTND(item.value, 0)}</td>
                          <td>
                            <span className="page-pill">p. {item.page}</span>
                          </td>
                          <td>
                            <span
                              className={`confidence-pill ${confidenceTone(
                                item.confidence
                              )}`}
                              title={item.snippet}
                            >
                              {formatNumber(item.confidence * 100, 0)} %
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            ))
          )}
        </div>
      )}

      {tab === "ratios" && (
        <div
          className="detail-panel ratios-panel"
          id="panel-ratios"
          role="tabpanel"
          aria-label="Ratios"
        >
          <div className="ratio-intro">
            <span className="ratio-intro-icon">
              <TrendingUp size={20} />
            </span>
            <div>
              <strong>{filing.ratios.filter((ratio) => ratio.value !== null).length} ratios calculés</strong>
              <span>
                Formules déterministes appliquées aux postes extraits. Les ratios
                sans donnée source sont masqués.
              </span>
            </div>
          </div>
          {ratioGroups.map((group) => (
            <section className="card panel" key={group.id}>
              <div className="card-head">
                <div>
                  <span className="page-kicker">
                    <Hash size={15} />
                    {group.title}
                  </span>
                  <h2 className="section-title">{group.description}</h2>
                </div>
                <span className="tag">{group.items.length} ratios</span>
              </div>
              <div className="ratio-grid">
                {group.items.map((ratio) => (
                  <div className="ratio-card" key={ratio.code}>
                    <span>{ratio.name}</span>
                    <strong>{formatRatioValue(ratio.code, ratio.value)}</strong>
                    <code>{ratio.code}</code>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {tab === "rapport" && (
        <div
          className="detail-panel"
          id="panel-rapport"
          role="tabpanel"
          aria-label="Rapport XLSX"
        >
          <section className="card panel report-card">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <FileSpreadsheet size={15} />
                  Livrable vérifié
                </span>
                <h2 className="section-title">
                  {reportPreview?.filename || "Rapport XLSX"}
                </h2>
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleDownload}
                disabled={downloading}
              >
                {downloading ? (
                  <LoaderCircle className="spin" size={16} />
                ) : (
                  <Download size={16} />
                )}
                Télécharger le classeur
              </button>
            </div>
            <div className="report-meta">
              <div>
                <span>Feuilles</span>
                <strong>{reportPreview?.sheets?.length ?? 4}</strong>
              </div>
              <div>
                <span>Taille</span>
                <strong>{reportPreview ? fileSize(reportPreview.size) : "—"}</strong>
              </div>
              <div>
                <span>SHA-256</span>
                <code>{reportPreview?.sha256 || reportHash || "—"}</code>
              </div>
            </div>
            <p className="verification-copy">
              Aperçu du classeur réellement généré et ancré : synthèse, 45 postes,
              ratios et contrôles. Le fichier téléchargé est identique à celui
              dont l’empreinte est publiée dans le message scellé.
            </p>
            {reportHash && reportPreview && reportHash !== reportPreview.sha256 && (
              <div className="inline-message is-error">
                L’empreinte du fichier téléchargé diffère de l’aperçu.
              </div>
            )}
          </section>

          {previewLoading ? (
            <section className="card panel">
              <div className="filing-skeleton" aria-label="Chargement de l’aperçu">
                {[1, 2, 3].map((item) => (
                  <div className="filing-skeleton-row" key={item}>
                    <span />
                    <span />
                    <span />
                  </div>
                ))}
              </div>
            </section>
          ) : previewError ? (
            <section className="card panel">
              <div className="inline-message is-error" role="alert">
                {previewError}
              </div>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={handleReportPreview}
              >
                <LoaderCircle size={16} />
                Réessayer
              </button>
            </section>
          ) : reportPreview && reportSheetData ? (
            <section className="card panel report-preview">
              <div className="report-sheet-tabs" role="tablist" aria-label="Feuilles du classeur">
                {reportPreview.sheets.map((sheet) => (
                  <button
                    type="button"
                    key={sheet.name}
                    role="tab"
                    aria-selected={reportSheetData.name === sheet.name}
                    className={`report-sheet-tab${
                      reportSheetData.name === sheet.name ? " is-active" : ""
                    }`}
                    onClick={() => setReportSheet(sheet.name)}
                  >
                    {sheet.name}
                    <span>{Math.max(sheet.rows.length - 1, 0)}</span>
                  </button>
                ))}
              </div>
              <div className="value-table-wrap report-table-wrap">
                <table className="report-table">
                  <tbody>
                    {reportSheetData.rows.map((row, rowIndex) => (
                      <tr key={`${reportSheetData.name}-${rowIndex}`}>
                        {row.map((cell, cellIndex) =>
                          rowIndex === 0 ? (
                            <th key={cellIndex}>{reportCell(cell)}</th>
                          ) : (
                            <td key={cellIndex}>{reportCell(cell)}</td>
                          )
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {reportSheetData.truncated && (
                <span className="report-truncated">
                  Aperçu limité aux 300 premières lignes. Le fichier complet est
                  disponible au téléchargement.
                </span>
              )}
            </section>
          ) : null}
        </div>
      )}

      {tab === "preuve" && (
        <div
          className="detail-panel"
          id="panel-preuve"
          role="tabpanel"
          aria-label="Preuve on-chain"
        >
          <div className="proof-layout">
            <section className="card panel verification-panel">
              <div className="card-head">
                <div>
                  <span className="page-kicker">
                    <ShieldCheck size={15} />
                    Vérification indépendante
                  </span>
                  <h2 className="section-title">Reconstruire depuis Hedera</h2>
                </div>
                {verification && (
                  <span
                    className={`verdict-pill ${
                      verification.verified ? "is-pass" : "is-fail"
                    }`}
                  >
                    {verification.verified ? "Vérifié" : "Échec"}
                  </span>
                )}
              </div>
              <p className="verification-copy">
                La vérification relit le topic HCS, recalcule la chaîne de
                hachage, lit la métadonnée du NFT et compare les empreintes du
                PDF, de l’extraction et du rapport. La base de données n’est pas
                utilisée comme source de vérité.
              </p>

              {!canVerify ? (
                <div className="inline-message">
                  Votre rôle {roleLabel(user?.role)} ne permet pas de lancer la
                  vérification. Les preuves restent consultables ci-dessous.
                </div>
              ) : (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleVerify}
                  disabled={verifying || !filing.token_id}
                >
                  {verifying ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <ShieldCheck size={16} />
                  )}
                  {verification ? "Relancer la vérification" : "Lancer les 12 contrôles"}
                </button>
              )}

              {verification && (
                <>
                  <div className="verification-summary">
                    <div>
                      <span>Contrôles passés</span>
                      <strong>
                        {verificationPassed} / {verificationChecks.length}
                      </strong>
                    </div>
                    <div>
                      <span>Messages HCS</span>
                      <strong>{verification.evidence?.message_count ?? "—"}</strong>
                    </div>
                    <div>
                      <span>Metadata HFS</span>
                      <code>{verification.evidence?.metadata_file_id || "—"}</code>
                    </div>
                  </div>
                  <div className="verification-grid">
                    {verificationChecks.map((check) => (
                      <div className="verification-item" key={check.check}>
                        {check.status === "pass" ? (
                          <CheckCircle2 className="check-icon is-pass" size={17} />
                        ) : (
                          <XCircle className="check-icon is-fail" size={17} />
                        )}
                        <div>
                          <strong>
                            {VERIFICATION_LABELS[check.check] || check.check}
                          </strong>
                          <span>{check.detail}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </section>

            <section className="card panel credential-panel">
              <div className="card-head">
                <div>
                  <span className="page-kicker">
                    <BadgeCheck size={15} />
                    Credential
                  </span>
                  <h2 className="section-title">NFT de dépôt</h2>
                </div>
              </div>
              <div className="credential-seal">
                <span className="credential-seal-icon">
                  <LockKeyhole size={24} />
                </span>
                <div>
                  <span>Token</span>
                  <code>{filing.token_id || "Non scellé"}</code>
                  <span>Serial</span>
                  <strong>{filing.serial ?? "—"}</strong>
                </div>
              </div>
              <div className="detail-list detail-list--compact">
                <div>
                  <span>Metadata file</span>
                  <code>{sealedCredential.metadata_file_id || "—"}</code>
                </div>
                <div>
                  <span>Événement scellé</span>
                  <code>#{sealedEvent?.sequence ?? "—"}</code>
                </div>
                <div>
                  <span>Horodatage consensus</span>
                  <strong>
                    {sealedEvent?.ts
                      ? formatDateTime(sealedEvent.ts)
                      : "En attente"}
                  </strong>
                </div>
                <div>
                  <span>Réseau</span>
                  <strong>Hedera testnet</strong>
                </div>
              </div>
            </section>
          </div>

          <section className="card panel">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <Link2 size={15} />
                  Journal HCS
                </span>
                <h2 className="section-title">Cycle de vie du dépôt</h2>
              </div>
              <span className="tag">{events.length} événements</span>
            </div>
            <div className="timeline">
              {events.map((event) => {
                const Icon = EVENT_ICONS[event.event] || FileText;
                return (
                  <div className="timeline-item" key={`${event.sequence}-${event.event}`}>
                    <span className="timeline-marker">
                      <Icon size={17} />
                    </span>
                    <div className="timeline-body">
                      <div className="timeline-head">
                        <strong>{EVENT_LABELS[event.event] || event.event}</strong>
                        <span className="timeline-seq">#{event.sequence}</span>
                      </div>
                      <span className="timeline-detail">{eventDetail(event)}</span>
                      <div className="timeline-meta">
                        <span>{formatDateTime(event.ts)}</span>
                        <code>{event.actor}</code>
                        <span>{event.role}</span>
                      </div>
                      <div className="timeline-hash">
                        <code>{shortHash(event.prev_hash, 6)}</code>
                        <ArrowRight size={12} />
                        <code>{shortHash(event.hash, 6)}</code>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="card panel">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <Building2 size={15} />
                  Identifiants Hedera
                </span>
                <h2 className="section-title">Objets ancrés</h2>
              </div>
            </div>
            <div className="hedera-grid">
              <div className="hedera-card">
                <span className="hedera-icon"><Link2 size={18} /></span>
                <div>
                  <span>Topic HCS</span>
                  <code>{filing.topic_id || "—"}</code>
                </div>
              </div>
              <div className="hedera-card">
                <span className="hedera-icon"><BadgeCheck size={18} /></span>
                <div>
                  <span>Token NFT</span>
                  <code>{filing.token_id || "—"}</code>
                </div>
              </div>
              <div className="hedera-card">
                <span className="hedera-icon"><Hash size={18} /></span>
                <div>
                  <span>Serial</span>
                  <code>{filing.serial ?? "—"}</code>
                </div>
              </div>
              <div className="hedera-card">
                <span className="hedera-icon"><CalendarRange size={18} /></span>
                <div>
                  <span>Déposé le</span>
                  <strong>{formatDate(filing.created_at)}</strong>
                </div>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
