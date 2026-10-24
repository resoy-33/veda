import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  CheckCircle2,
  FileCheck2,
  FileText,
  Fingerprint,
  LoaderCircle,
  LockKeyhole,
  RefreshCw,
  ScanLine,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";
import { api } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { CHECK_LABELS } from "../lib/ratios.js";
import { fileSize, formatNumber, formatPeriod, shortHash } from "../lib/format.js";

const PERIODS = [
  { value: "2025-12-31", label: "Exercice 2025" },
  { value: "2024-12-31", label: "Exercice 2024" },
  { value: "2023-12-31", label: "Exercice 2023" },
  { value: "2022-12-31", label: "Exercice 2022" },
  { value: "2021-12-31", label: "Exercice 2021" },
];

const STEPS = [
  {
    id: "submitted",
    label: "Dépôt du PDF",
    text: "Le document est haché et son empreinte est ancrée dans un topic HCS.",
    icon: FileText,
  },
  {
    id: "extracted",
    label: "Extraction & validation",
    text: "Les 45 postes sont extraits, les ratios calculés et les 7 contrôles exécutés.",
    icon: ScanLine,
  },
  {
    id: "sealed",
    label: "Scellement du credential",
    text: "Le rapport et les empreintes sont publiés sur HFS puis scellés dans un NFT.",
    icon: LockKeyhole,
  },
];

export function NewDeposit() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [formKey, setFormKey] = useState(0);
  const [meta, setMeta] = useState({
    issuer: "SAH",
    period: "2025-12-31",
    sector: "industrial",
    unit: "TND",
    consolidation: "individuel",
  });
  const [step, setStep] = useState("idle");
  const [busy, setBusy] = useState("");
  const [filingId, setFilingId] = useState("");
  const [extraction, setExtraction] = useState(null);
  const [seal, setSeal] = useState(null);
  const [error, setError] = useState("");

  const allowed = ["issuer", "admin"].includes(user?.role);
  const locked = Boolean(filingId);
  const currentIndex = useMemo(() => {
    if (step === "sealed") {
      return 3;
    }
    if (step === "extracted" || step === "failed") {
      return 2;
    }
    if (step === "submitted") {
      return 1;
    }
    return 0;
  }, [step]);

  function selectFile(candidate) {
    setError("");
    if (!candidate) {
      return;
    }
    if (!candidate.name.toLowerCase().endsWith(".pdf")) {
      setError("Seuls les fichiers PDF sont acceptés.");
      return;
    }
    if (candidate.size > 25 * 1024 * 1024) {
      setError("Le fichier dépasse la limite de 25 Mo.");
      return;
    }
    setFile(candidate);
  }

  function reset() {
    setFile(null);
    setStep("idle");
    setBusy("");
    setFilingId("");
    setExtraction(null);
    setSeal(null);
    setError("");
    setFormKey((value) => value + 1);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) {
      setError("Sélectionnez le PDF des états financiers.");
      return;
    }
    setBusy("submit");
    setError("");
    try {
      const result = await api.submitFiling(file, meta);
      setFilingId(result.filing_id);
      setStep("submitted");
    } catch (err) {
      setError(err.message || "Le dépôt a échoué.");
    } finally {
      setBusy("");
    }
  }

  async function handleExtract() {
    setBusy("extract");
    setError("");
    try {
      const result = await api.extractFiling(filingId, file);
      setExtraction(result);
      setStep(result.verdict === "pass" ? "extracted" : "failed");
    } catch (err) {
      setError(err.message || "L’extraction a échoué.");
    } finally {
      setBusy("");
    }
  }

  async function handleSeal() {
    setBusy("seal");
    setError("");
    try {
      const result = await api.sealFiling(filingId);
      setSeal(result);
      setStep("sealed");
    } catch (err) {
      setError(err.message || "Le scellement a échoué.");
    } finally {
      setBusy("");
    }
  }

  if (!allowed) {
    return (
      <div className="stack-lg">
        <Link className="back-link" to="/depots">
          <ArrowLeft size={16} />
          Retour au registre
        </Link>
        <section className="card empty-state detail-empty">
          <LockKeyhole size={28} />
          <strong>Accès réservé à l’émetteur</strong>
          <span>
            Seul le rôle émetteur, ou un administrateur, peut déposer un état
            financier.
          </span>
          <Link className="btn btn-ghost" to="/depots">
            Consulter le registre
          </Link>
        </section>
      </div>
    );
  }

  return (
    <div className="stack-lg">
      <div className="detail-top">
        <Link className="back-link" to="/depots">
          <ArrowLeft size={16} />
          Registre des dépôts
        </Link>
        <span className="detail-role">
          <ShieldCheck size={14} />
          Espace émetteur
        </span>
      </div>

      <header className="page-head">
        <div>
          <span className="page-kicker">
            <UploadCloud size={15} />
            Nouveau dépôt
          </span>
          <h1 className="page-title">Sceller un exercice</h1>
          <p className="page-sub">
            Déposez le PDF, contrôlez l’extraction, puis publiez la preuve sur
            Hedera. Chaque action est irréversible.
          </p>
        </div>
      </header>

      <section className="deposit-layout">
        <div className="stack-lg">
          <form className="card panel deposit-form" onSubmit={handleSubmit}>
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <FileText size={15} />
                  Étape 01 · Document
                </span>
                <h2 className="section-title">États financiers annuels</h2>
              </div>
              <span className="tag">PDF · 25 Mo max</span>
            </div>

            <label
              className={`dropzone${dragging ? " is-dragging" : ""}${
                file ? " has-file" : ""
              }${locked ? " is-locked" : ""}`}
              onDragOver={(event) => {
                event.preventDefault();
                if (!locked) {
                  setDragging(true);
                }
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                if (!locked) {
                  selectFile(event.dataTransfer.files?.[0]);
                }
              }}
            >
              <input
                key={formKey}
                type="file"
                accept="application/pdf,.pdf"
                disabled={locked}
                onChange={(event) => selectFile(event.target.files?.[0])}
              />
              {file ? (
                <>
                  <span className="dropzone-icon is-ready">
                    <FileCheck2 size={24} />
                  </span>
                  <span className="dropzone-copy">
                    <strong>{file.name}</strong>
                    <span>
                      {fileSize(file.size)} · PDF prêt pour le dépôt
                    </span>
                  </span>
                  {!locked && (
                    <span className="dropzone-remove" aria-hidden="true">
                      <X size={15} />
                    </span>
                  )}
                </>
              ) : (
                <>
                  <span className="dropzone-icon">
                    <UploadCloud size={26} />
                  </span>
                  <span className="dropzone-copy">
                    <strong>Glissez le PDF ici</strong>
                    <span>ou cliquez pour sélectionner un fichier</span>
                  </span>
                </>
              )}
            </label>

            <div className="form-row">
              <label className="field">
                <span className="field-label">Émetteur</span>
                <input
                  className="input"
                  value={meta.issuer}
                  readOnly={locked}
                  onChange={(event) =>
                    setMeta((current) => ({
                      ...current,
                      issuer: event.target.value,
                    }))
                  }
                  required
                />
              </label>
              <label className="field">
                <span className="field-label">Exercice</span>
                <select
                  className="input"
                  value={meta.period}
                  disabled={locked}
                  onChange={(event) =>
                    setMeta((current) => ({
                      ...current,
                      period: event.target.value,
                    }))
                  }
                >
                  {PERIODS.map((period) => (
                    <option value={period.value} key={period.value}>
                      {period.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="form-row form-row--three">
              <label className="field">
                <span className="field-label">Secteur</span>
                <select
                  className="input"
                  value={meta.sector}
                  disabled={locked}
                  onChange={(event) =>
                    setMeta((current) => ({
                      ...current,
                      sector: event.target.value,
                    }))
                  }
                >
                  <option value="industrial">Industrie</option>
                  <option value="services">Services</option>
                  <option value="financial">Finance</option>
                  <option value="energy">Énergie</option>
                </select>
              </label>
              <label className="field">
                <span className="field-label">Unité</span>
                <select
                  className="input"
                  value={meta.unit}
                  disabled={locked}
                  onChange={(event) =>
                    setMeta((current) => ({
                      ...current,
                      unit: event.target.value,
                    }))
                  }
                >
                  <option value="TND">TND</option>
                  <option value="EUR">EUR</option>
                  <option value="USD">USD</option>
                </select>
              </label>
              <label className="field">
                <span className="field-label">Périmètre</span>
                <select
                  className="input"
                  value={meta.consolidation}
                  disabled={locked}
                  onChange={(event) =>
                    setMeta((current) => ({
                      ...current,
                      consolidation: event.target.value,
                    }))
                  }
                >
                  <option value="individuel">Individuel</option>
                  <option value="consolide">Consolidé</option>
                </select>
              </label>
            </div>

            <p className="form-note">
              Le PDF doit contenir les états financiers annuels de l’émetteur.
              L’extracteur est calibré sur les états LILAS en français.
            </p>

            {error && (
              <div className="inline-message is-error" role="alert">
                {error}
              </div>
            )}

            <div className="form-actions">
              {!locked ? (
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!file || Boolean(busy)}
                >
                  {busy === "submit" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <ArrowRight size={16} />
                  )}
                  Déposer et ancrer le PDF
                </button>
              ) : (
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={reset}
                  disabled={Boolean(busy)}
                >
                  <RefreshCw size={16} />
                  Recommencer
                </button>
              )}
            </div>
          </form>

          <section className="card panel deposit-steps">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <Sparkles size={15} />
                  Cycle de preuve
                </span>
                <h2 className="section-title">Trois étapes, quatre événements</h2>
              </div>
            </div>
            <div className="step-list">
              {STEPS.map((item, index) => {
                const Icon = item.icon;
                const state =
                  currentIndex > index
                    ? "is-done"
                    : currentIndex === index
                    ? step === "failed" && index === 1
                      ? "is-failed"
                      : "is-active"
                    : "is-todo";
                return (
                  <div className={`step-row ${state}`} key={item.id}>
                    <span className="step-index">
                      {state === "is-done" ? (
                        <CheckCircle2 size={18} />
                      ) : (
                        <Icon size={18} />
                      )}
                    </span>
                    <div>
                      <strong>{item.label}</strong>
                      <span>{item.text}</span>
                    </div>
                    <span className="step-state">
                      {state === "is-done"
                        ? "Terminé"
                        : state === "is-active"
                        ? "En cours"
                        : state === "is-failed"
                        ? "Échec"
                        : "En attente"}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>
        </div>

        <aside className="stack-lg">
          <section className="card panel deposit-action">
            <div className="card-head">
              <div>
                <span className="page-kicker">
                  <Fingerprint size={15} />
                  Prochaine action
                </span>
                <h2 className="section-title">
                  {step === "idle" && "Déposer le document"}
                  {step === "submitted" && "Extraire les comptes"}
                  {step === "extracted" && "Sceller la preuve"}
                  {step === "failed" && "Validation échouée"}
                  {step === "sealed" && "Dépôt scellé"}
                </h2>
              </div>
            </div>

            {step === "idle" && (
              <p className="deposit-action-copy">
                Sélectionnez le PDF et vérifiez les métadonnées. Le dépôt crée le
                topic HCS et ancre l’empreinte du document.
              </p>
            )}

            {step === "submitted" && (
              <>
                <p className="deposit-action-copy">
                  Le PDF est ancré. Lancez l’extraction déterministe des 45 postes
                  et les contrôles comptables.
                </p>
                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  onClick={handleExtract}
                  disabled={Boolean(busy)}
                >
                  {busy === "extract" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <ScanLine size={16} />
                  )}
                  Extraire et valider
                </button>
                <div className="mini-proof">
                  <span>Filing ID</span>
                  <code>{filingId}</code>
                </div>
              </>
            )}

            {step === "extracted" && (
              <>
                <p className="deposit-action-copy">
                  Les comptes sont conformes. Le scellement publie la métadonnée
                  HFS, mint le NFT et écrit l’événement final.
                </p>
                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  onClick={handleSeal}
                  disabled={Boolean(busy)}
                >
                  {busy === "seal" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <LockKeyhole size={16} />
                  )}
                  Sceller sur Hedera
                </button>
                <div className="mini-proof">
                  <span>Extraction</span>
                  <code>{shortHash(extraction?.extraction_sha256, 10)}</code>
                </div>
              </>
            )}

            {step === "failed" && (
              <>
                <div className="failed-note">
                  <AlertTriangle size={18} />
                  <span>
                    Les contrôles comptables n’ont pas tous réussi. Le dépôt ne
                    peut pas être scellé.
                  </span>
                </div>
                <button
                  type="button"
                  className="btn btn-ghost btn-block"
                  onClick={reset}
                >
                  <RefreshCw size={16} />
                  Recommencer avec un autre PDF
                </button>
              </>
            )}

            {step === "sealed" && seal && (
              <>
                <div className="sealed-note">
                  <BadgeCheck size={22} />
                  <div>
                    <strong>Preuve publiée</strong>
                    <span>
                      Exercice {meta.period.slice(0, 4)} · NFT serial{" "}
                      {seal.serial}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  onClick={() => navigate(`/depots/${seal.filing_id}`)}
                >
                  Voir le dossier scellé
                  <ArrowRight size={16} />
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-block"
                  onClick={reset}
                >
                  <RefreshCw size={16} />
                  Déposer un autre exercice
                </button>
              </>
            )}

            {busy && (
              <div className="busy-note" role="status">
                <LoaderCircle className="spin" size={15} />
                {busy === "submit" && "Ancrage du document sur Hedera…"}
                {busy === "extract" && "Extraction et contrôles en cours…"}
                {busy === "seal" && "Publication HFS et mint du NFT…"}
              </div>
            )}
          </section>

          {extraction && (
            <section className="card panel">
              <div className="card-head">
                <div>
                  <span className="page-kicker">
                    <FileCheck2 size={15} />
                    Résultat d’extraction
                  </span>
                  <h2 className="section-title">
                    {extraction.verdict === "pass" ? "Comptes conformes" : "À corriger"}
                  </h2>
                </div>
                <span
                  className={`verdict-pill ${
                    extraction.verdict === "pass" ? "is-pass" : "is-fail"
                  }`}
                >
                  {extraction.verdict === "pass" ? "Conforme" : "Échec"}
                </span>
              </div>
              <div className="extraction-summary">
                <div>
                  <span>Postes extraits</span>
                  <strong>{formatNumber(extraction.line_count, 0)}</strong>
                </div>
                <div>
                  <span>Contrôles</span>
                  <strong>
                    {extraction.checks.filter((check) => check.status === "pass").length}
                    {" / "}
                    {extraction.checks.length}
                  </strong>
                </div>
              </div>
              <div className="check-list check-list--compact">
                {extraction.checks.map((check) => (
                  <div className="check-row" key={check.id}>
                    {check.status === "pass" ? (
                      <CheckCircle2 className="check-icon is-pass" size={16} />
                    ) : (
                      <AlertTriangle className="check-icon is-fail" size={16} />
                    )}
                    <div>
                      <strong>{CHECK_LABELS[check.id] || check.id}</strong>
                      <span>{check.detail}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {step === "sealed" && seal && (
            <section className="card panel">
              <div className="card-head">
                <div>
                  <span className="page-kicker">
                    <BadgeCheck size={15} />
                    Preuve créée
                  </span>
                  <h2 className="section-title">{formatPeriod(meta.period)}</h2>
                </div>
              </div>
              <div className="detail-list detail-list--compact">
                <div>
                  <span>Token NFT</span>
                  <code>{seal.token_id}</code>
                </div>
                <div>
                  <span>Serial</span>
                  <strong>{seal.serial}</strong>
                </div>
                <div>
                  <span>Metadata HFS</span>
                  <code>{seal.metadata_file_id}</code>
                </div>
                <div>
                  <span>Séquence HCS</span>
                  <code>#{seal.hcs_sequence}</code>
                </div>
                <div>
                  <span>Rapport SHA-256</span>
                  <code>{shortHash(seal.report_sha256, 10)}</code>
                </div>
              </div>
            </section>
          )}
        </aside>
      </section>
    </div>
  );
}
