import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  ChevronRight,
  Landmark,
  ListChecks,
  Menu,
  ServerCog,
  ShieldCheck,
  UploadCloud,
  X,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext.jsx";
import { displayName, roleLabel } from "../lib/labels.js";
import { AccountMenu } from "./AccountMenu.jsx";
import { Avatar } from "./Avatar.jsx";
import { Brand } from "./Brand.jsx";
import { ThemeControl } from "./ThemeControl.jsx";

const TITLES = {
  "/depots": "Dépôts",
  "/verification": "Vérification",
  "/operations": "Système",
  "/compte": "Mon compte",
};

export function Layout() {
  const { user } = useAuth();
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    setNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!navOpen) {
      return undefined;
    }
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [navOpen]);

  const title =
    location.pathname === "/depots/nouveau"
      ? "Nouveau dépôt"
      : location.pathname.startsWith("/depots/")
      ? "Dossier de dépôt"
      : TITLES[location.pathname] || "Veda";
  const canDeposit = ["issuer", "admin"].includes(user?.role);
  const canVerify = ["broker", "verifier", "admin"].includes(user?.role);
  const isAdmin = user?.role === "admin";

  return (
    <div className="app-shell">
      {navOpen && (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Fermer le menu"
          onClick={() => setNavOpen(false)}
        />
      )}

      <aside className={`sidebar${navOpen ? " is-open" : ""}`}>
        <div className="sidebar-head">
          <Brand to="/depots" />
          <button
            type="button"
            className="icon-btn sidebar-close"
            aria-label="Fermer le menu"
            onClick={() => setNavOpen(false)}
          >
            <X size={18} />
          </button>
        </div>

        <NavLink to="/compte" className="sidebar-user">
          <Avatar user={user} size="sm" />
          <span className="sidebar-user-copy">
            <strong>{displayName(user)}</strong>
            <span>{roleLabel(user?.role)}</span>
          </span>
          <ChevronRight size={16} />
        </NavLink>

        <nav className="nav" aria-label="Navigation principale">
          <span className="nav-label">Registre</span>
          <NavLink
            to="/depots"
            end
            className={({ isActive }) =>
              `nav-link${isActive ? " is-active" : ""}`
            }
          >
            <Landmark size={18} strokeWidth={1.9} />
            <span>Dépôts</span>
          </NavLink>
          {canDeposit && (
            <NavLink
              to="/depots/nouveau"
              className={({ isActive }) =>
                `nav-link${isActive ? " is-active" : ""}`
              }
            >
              <UploadCloud size={18} strokeWidth={1.9} />
              <span>Nouveau dépôt</span>
            </NavLink>
          )}
          {canVerify && (
            <NavLink
              to="/verification"
              className={({ isActive }) =>
                `nav-link${isActive ? " is-active" : ""}`
              }
            >
              <ListChecks size={18} strokeWidth={1.9} />
              <span>Vérification</span>
            </NavLink>
          )}
          {isAdmin && (
            <NavLink
              to="/operations"
              className={({ isActive }) =>
                `nav-link${isActive ? " is-active" : ""}`
              }
            >
              <ServerCog size={18} strokeWidth={1.9} />
              <span>Système</span>
            </NavLink>
          )}
        </nav>

        <div className="sidebar-spacer" />

        <div className="sidebar-proof">
          <span className="proof-title">
            <ShieldCheck size={16} />
            Preuve ancrée
          </span>
          <span className="proof-row">
            <span className="proof-dot" />
            Journal HCS immuable
          </span>
          <span className="proof-row">
            <span className="proof-dot" />
            Credential NFT vérifiable
          </span>
          <span className="proof-row">
            <span className="proof-dot" />
            Métadonnées HFS
          </span>
        </div>

        <div className="sidebar-footer">
          <ThemeControl compact />
          <span className="sidebar-version">Hedera testnet · v0.4.0</span>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="icon-btn menu-toggle"
              aria-label="Ouvrir le menu"
              onClick={() => setNavOpen(true)}
            >
              <Menu size={20} />
            </button>
            <span className="topbar-title">{title}</span>
          </div>
          <div className="topbar-right">
            <span className="network-pill">
              <span className="network-dot" />
              Hedera testnet
            </span>
            <AccountMenu />
          </div>
        </header>

        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
