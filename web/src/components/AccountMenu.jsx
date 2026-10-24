import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowUpRight,
  ChevronDown,
  LogOut,
  Settings2,
  UserRound,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext.jsx";
import { displayName, roleLabel } from "../lib/labels.js";
import { Avatar } from "./Avatar.jsx";
import { ThemeControl } from "./ThemeControl.jsx";

export function AccountMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const onPointer = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    const onKey = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const handleLogout = () => {
    setOpen(false);
    logout();
    navigate("/login", { replace: true });
  };

  if (!user) {
    return null;
  }

  return (
    <div className="account-wrap" ref={rootRef}>
      <button
        type="button"
        className={`account-button${open ? " is-open" : ""}`}
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <Avatar user={user} size="sm" />
        <span className="account-copy">
          <strong>{displayName(user)}</strong>
          <span>{user.email}</span>
        </span>
        <ChevronDown size={16} className="account-chevron" />
      </button>

      {open && (
        <div className="account-menu" aria-label="Menu du compte">
          <div className="account-menu-head">
            <Avatar user={user} size="lg" />
            <div>
              <strong>{displayName(user)}</strong>
              <span>{user.email}</span>
              <span className={`role-pill role-pill--${user.role}`}>
                {roleLabel(user.role)}
              </span>
            </div>
          </div>

          <div className="menu-sep" />

          <Link
            to="/compte"
            className="menu-item"
            onClick={() => setOpen(false)}
          >
            <UserRound size={17} />
            <span>Mon compte</span>
            <ArrowUpRight size={15} className="menu-item-end" />
          </Link>
          <Link
            to="/compte#apparence"
            className="menu-item"
            onClick={() => setOpen(false)}
          >
            <Settings2 size={17} />
            <span>Préférences</span>
          </Link>

          <div className="menu-sep" />

          <div className="menu-theme">
            <span className="menu-theme-label">Apparence</span>
            <ThemeControl compact />
          </div>

          <div className="menu-sep" />

          <button
            type="button"
            className="menu-item is-danger"
            onClick={handleLogout}
          >
            <LogOut size={17} />
            <span>Déconnexion</span>
          </button>
        </div>
      )}
    </div>
  );
}
