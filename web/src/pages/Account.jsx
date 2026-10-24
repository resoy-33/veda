import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import {
  BadgeCheck,
  Check,
  KeyRound,
  LoaderCircle,
  MonitorSmartphone,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { api } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { Avatar } from "../components/Avatar.jsx";
import { ThemeControl } from "../components/ThemeControl.jsx";
import { displayName, roleLabel } from "../lib/labels.js";

export function Account() {
  const { user, updateUser } = useAuth();
  const location = useLocation();
  const [name, setName] = useState(user?.display_name || "");
  const [nameState, setNameState] = useState({ status: "idle", message: "" });
  const [passwords, setPasswords] = useState({
    current: "",
    next: "",
    confirm: "",
  });
  const [passwordState, setPasswordState] = useState({
    status: "idle",
    message: "",
  });

  useEffect(() => {
    setName(user?.display_name || "");
  }, [user?.display_name]);

  useEffect(() => {
    if (!location.hash) {
      return;
    }
    const target = document.getElementById(location.hash.slice(1));
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [location.hash]);

  const onProfileSubmit = async (event) => {
    event.preventDefault();
    const clean = name.trim();
    if (!clean) {
      setNameState({ status: "error", message: "Le nom ne peut pas être vide." });
      return;
    }
    setNameState({ status: "loading", message: "" });
    try {
      const updated = await api.updateProfile(clean);
      updateUser(updated);
      setName(updated.display_name || clean);
      setNameState({ status: "success", message: "Nom affiché mis à jour." });
    } catch (requestError) {
      setNameState({
        status: "error",
        message: requestError.message || "Mise à jour impossible.",
      });
    }
  };

  const onPasswordSubmit = async (event) => {
    event.preventDefault();
    if (passwords.next.length < 8) {
      setPasswordState({
        status: "error",
        message: "Le nouveau mot de passe doit contenir au moins 8 caractères.",
      });
      return;
    }
    if (passwords.next !== passwords.confirm) {
      setPasswordState({
        status: "error",
        message: "La confirmation ne correspond pas au nouveau mot de passe.",
      });
      return;
    }
    setPasswordState({ status: "loading", message: "" });
    try {
      await api.changePassword(passwords.current, passwords.next);
      setPasswords({ current: "", next: "", confirm: "" });
      setPasswordState({
        status: "success",
        message: "Mot de passe mis à jour.",
      });
    } catch (requestError) {
      setPasswordState({
        status: "error",
        message: requestError.message || "Modification impossible.",
      });
    }
  };

  return (
    <div className="stack-lg">
      <header className="page-head">
        <div>
          <span className="page-kicker">
            <UserRound size={15} />
            Identité & sécurité
          </span>
          <h1 className="page-title">Mon compte</h1>
          <p className="page-sub">
            Gérez votre identité affichée et vos accès au registre.
          </p>
        </div>
      </header>

      <div className="account-grid">
        <section className="card identity-card">
          <Avatar user={user} size="xl" />
          <h2>{displayName(user)}</h2>
          <p className="identity-email">{user?.email}</p>
          <span className={`role-pill role-pill--${user?.role}`}>
            {roleLabel(user?.role)}
          </span>
          <div className="detail-list">
            <div>
              <span>Compte Hedera</span>
              <code>{user?.hedera_account_id}</code>
            </div>
            <div>
              <span>Réseau</span>
              <strong>Hedera testnet</strong>
            </div>
            <div>
              <span>Authentification</span>
              <strong>JWT · 1 heure</strong>
            </div>
          </div>
          <span className="identity-foot">
            <ShieldCheck size={14} />
            Les clés Hedera restent côté serveur
          </span>
        </section>

        <div className="account-forms">
          <section className="card form-card">
            <div className="card-head">
              <div>
                <h2 className="section-title">Identité affichée</h2>
                <p className="muted">
                  Ce nom apparaît dans la navigation et les menus.
                </p>
              </div>
              <UserRound size={19} className="card-head-icon" />
            </div>
            <form className="form-stack" onSubmit={onProfileSubmit}>
              <label className="field">
                <span className="field-label">Nom affiché</span>
                <input
                  className="input"
                  value={name}
                  maxLength={80}
                  onChange={(event) => setName(event.target.value)}
                  disabled={nameState.status === "loading"}
                />
              </label>
              <label className="field">
                <span className="field-label">Adresse e-mail</span>
                <input
                  className="input"
                  value={user?.email || ""}
                  readOnly
                  aria-readonly="true"
                />
              </label>
              <div className="form-actions">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={nameState.status === "loading"}
                >
                  {nameState.status === "loading" ? (
                    <LoaderCircle size={17} className="spin" />
                  ) : (
                    <Check size={17} />
                  )}
                  Enregistrer
                </button>
                {nameState.message && (
                  <span
                    className={`inline-message is-${nameState.status}`}
                    role={nameState.status === "error" ? "alert" : "status"}
                  >
                    {nameState.message}
                  </span>
                )}
              </div>
            </form>
          </section>

          <section className="card form-card">
            <div className="card-head">
              <div>
                <h2 className="section-title">Mot de passe</h2>
                <p className="muted">
                  Utilisez au moins 8 caractères. Les sessions existantes
                  restent actives.
                </p>
              </div>
              <KeyRound size={19} className="card-head-icon" />
            </div>
            <form className="form-stack" onSubmit={onPasswordSubmit}>
              <label className="field">
                <span className="field-label">Mot de passe actuel</span>
                <input
                  className="input"
                  type="password"
                  autoComplete="current-password"
                  value={passwords.current}
                  onChange={(event) =>
                    setPasswords((current) => ({
                      ...current,
                      current: event.target.value,
                    }))
                  }
                  disabled={passwordState.status === "loading"}
                />
              </label>
              <div className="form-row">
                <label className="field">
                  <span className="field-label">Nouveau mot de passe</span>
                  <input
                    className="input"
                    type="password"
                    autoComplete="new-password"
                    value={passwords.next}
                    onChange={(event) =>
                      setPasswords((current) => ({
                        ...current,
                        next: event.target.value,
                      }))
                    }
                    disabled={passwordState.status === "loading"}
                  />
                </label>
                <label className="field">
                  <span className="field-label">Confirmation</span>
                  <input
                    className="input"
                    type="password"
                    autoComplete="new-password"
                    value={passwords.confirm}
                    onChange={(event) =>
                      setPasswords((current) => ({
                        ...current,
                        confirm: event.target.value,
                      }))
                    }
                    disabled={passwordState.status === "loading"}
                  />
                </label>
              </div>
              <div className="form-actions">
                <button
                  type="submit"
                  className="btn btn-ghost"
                  disabled={passwordState.status === "loading"}
                >
                  {passwordState.status === "loading" ? (
                    <LoaderCircle size={17} className="spin" />
                  ) : (
                    <KeyRound size={17} />
                  )}
                  Modifier le mot de passe
                </button>
                {passwordState.message && (
                  <span
                    className={`inline-message is-${passwordState.status}`}
                    role={passwordState.status === "error" ? "alert" : "status"}
                  >
                    {passwordState.message}
                  </span>
                )}
              </div>
            </form>
          </section>
        </div>
      </div>

      <section className="card form-card" id="apparence">
        <div className="card-head">
          <div>
            <h2 className="section-title">Apparence</h2>
            <p className="muted">
              Choisissez le thème de l’interface. Le mode système suit les
              préférences de votre appareil.
            </p>
          </div>
          <MonitorSmartphone size={19} className="card-head-icon" />
        </div>
        <ThemeControl />
      </section>

      <p className="account-note">
        <BadgeCheck size={15} />
        Compte de démonstration Veda — les identifiants sont publics.
      </p>
    </div>
  );
}
