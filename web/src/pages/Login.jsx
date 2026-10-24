import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BadgeCheck,
  Building2,
  Check,
  ChevronRight,
  Eye,
  EyeOff,
  FileText,
  Fingerprint,
  KeyRound,
  LineChart,
  Link2,
  LoaderCircle,
  ScanSearch,
  Settings2,
  ShieldCheck,
} from "lucide-react";
import { api } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { Brand } from "../components/Brand.jsx";
import { DEMO_ACCOUNTS, ROLES, ROLE_TIER } from "../lib/labels.js";

const ROLE_ICONS = {
  issuer: Building2,
  broker: LineChart,
  verifier: ScanSearch,
  admin: Settings2,
};

export function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let active = true;
    api
      .health()
      .then((data) => {
        if (active) {
          setHealth(data);
        }
      })
      .catch(() => {
        if (active) {
          setHealth({ status: "down", db: "error" });
        }
      });
    return () => {
      active = false;
    };
  }, []);

  if (isAuthenticated) {
    return <Navigate to="/depots" replace />;
  }

  const signIn = async (nextEmail, nextPassword) => {
    setError("");
    setLoading(nextEmail);
    try {
      await login(nextEmail, nextPassword);
      const target = location.state?.from?.pathname || "/depots";
      navigate(target, { replace: true });
    } catch (requestError) {
      if (requestError.status === 401) {
        setError("Identifiants incorrects. Vérifiez l’e-mail et le mot de passe.");
      } else if (requestError.code === "network") {
        setError("Le service est injoignable. Réessayez dans un instant.");
      } else {
        setError(requestError.message || "Connexion impossible.");
      }
    } finally {
      setLoading(null);
    }
  };

  const onSubmit = (event) => {
    event.preventDefault();
    if (!email.trim() || !password) {
      setError("Renseignez votre e-mail et votre mot de passe.");
      return;
    }
    signIn(email.trim(), password);
  };

  const healthy = health?.status === "ok" && health?.db === "ok";

  return (
    <div className="login">
      <section className="login-brand">
        <div className="login-brand-inner">
          <div className="login-brand-top">
            <Brand />
            <span className="login-eyebrow">
              <ShieldCheck size={14} />
              Registre financier vérifié
            </span>
          </div>

          <div className="login-hero">
            <h1 className="login-title">
              La confiance,
              <em>preuve à l’appui.</em>
            </h1>
            <p className="login-lead">
              Chaque chiffre tracé jusqu’à la source. Chaque rapport scellé sur
              Hedera, vérifiable par n’importe qui, à n’importe quel moment.
            </p>

            <div className="login-chain" aria-label="Chaîne de confiance">
              <span className="chain-node">
                <FileText size={17} />
                PDF source
              </span>
              <ChevronRight size={15} className="chain-arrow" />
              <span className="chain-node">
                <Link2 size={17} />
                Journal HCS
              </span>
              <ChevronRight size={15} className="chain-arrow" />
              <span className="chain-node">
                <BadgeCheck size={17} />
                Credential NFT
              </span>
            </div>

            <ul className="login-points">
              <li>
                <span className="point-icon">
                  <Fingerprint size={16} />
                </span>
                <span>
                  <strong>Empreinte SHA-256</strong> du document déposé
                </span>
              </li>
              <li>
                <span className="point-icon">
                  <Link2 size={16} />
                </span>
                <span>
                  <strong>Chaîne d’événements</strong> horodatée sur HCS
                </span>
              </li>
              <li>
                <span className="point-icon">
                  <BadgeCheck size={16} />
                </span>
                <span>
                  <strong>Credential NFT</strong> et rapport exportable
                </span>
              </li>
            </ul>
          </div>

          <div className="login-brand-footer">
            <span className="login-network">
              <span className="network-dot" />
              Hedera testnet
            </span>
            <span>Les clés ne quittent jamais le serveur.</span>
          </div>
        </div>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <span className="login-secure">
            <ShieldCheck size={14} />
            Accès sécurisé · JWT
          </span>
          <h2>Bienvenue</h2>
          <p className="login-sub">
            Connectez-vous pour accéder au registre des dépôts vérifiés.
          </p>

          <form className="form-stack" onSubmit={onSubmit} noValidate>
            <label className="field">
              <span className="field-label">Adresse e-mail</span>
              <input
                className="input"
                type="email"
                name="email"
                autoComplete="username"
                placeholder="vous@exemple.tn"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                disabled={Boolean(loading)}
              />
            </label>

            <label className="field">
              <span className="field-label">Mot de passe</span>
              <span className="input-wrap">
                <input
                  className="input"
                  type={showPassword ? "text" : "password"}
                  name="password"
                  autoComplete="current-password"
                  placeholder="Votre mot de passe"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  disabled={Boolean(loading)}
                />
                <button
                  type="button"
                  className="input-action"
                  onClick={() => setShowPassword((value) => !value)}
                  aria-label={
                    showPassword
                      ? "Masquer le mot de passe"
                      : "Afficher le mot de passe"
                  }
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
            </label>

            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={Boolean(loading)}
            >
              {loading ? (
                <>
                  <LoaderCircle size={18} className="spin" />
                  Connexion…
                </>
              ) : (
                <>
                  Se connecter
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <div className="login-demo">
            <div className="demo-head">
              <span className="demo-title">
                <KeyRound size={15} />
                Connexion rapide — démo
              </span>
              <span className="demo-hint">mot de passe : demo1234</span>
            </div>

            <div className="demo-grid">
              {DEMO_ACCOUNTS.map((account) => {
                const Icon = ROLE_ICONS[account.role];
                const role = ROLES[account.role];
                const busy = loading === account.email;
                return (
                  <button
                    key={account.email}
                    type="button"
                    className={`demo-card demo-card--${role.tone}`}
                    onClick={() => signIn(account.email, "demo1234")}
                    disabled={Boolean(loading)}
                  >
                    <span className="demo-icon">
                      {busy ? (
                        <LoaderCircle size={18} className="spin" />
                      ) : (
                        <Icon size={18} />
                      )}
                    </span>
                    <span className="demo-copy">
                      <strong>{role.label}</strong>
                      <small>{ROLE_TIER[account.role]}</small>
                    </span>
                    <ChevronRight size={16} className="demo-arrow" />
                  </button>
                );
              })}
            </div>

            <p className="demo-note">
              <Check size={13} />
              Analyste et auditeur partagent les mêmes droits de vérification.
            </p>
          </div>

          <div className="login-meta">
            <span className={`health${healthy ? " is-ok" : " is-down"}`}>
              <span className="health-dot" />
              {health === null
                ? "Connexion au service…"
                : healthy
                  ? "API et base opérationnelles"
                  : "Service temporairement indisponible"}
            </span>
            <span className="login-version">v{health?.version || "0.4.0"}</span>
          </div>
        </div>
      </section>
    </div>
  );
}
