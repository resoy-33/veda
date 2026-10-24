import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";
import { api, setAccessToken } from "../api/client.js";

const STORAGE_KEY = "veda.session";
const AuthContext = createContext(null);

function readSession() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    if (!parsed?.token || !parsed?.user || parsed.expiresAt <= Date.now()) {
      sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function persist(session) {
  try {
    if (session) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    return;
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(readSession);
  const navigate = useNavigate();

  useLayoutEffect(() => {
    setAccessToken(session?.token);
  }, [session]);

  const login = useCallback(async (email, password) => {
    const data = await api.login(email, password);
    const next = {
      token: data.access_token,
      user: data.user,
      expiresAt: Date.now() + data.expires_in * 1000,
    };
    setAccessToken(next.token);
    persist(next);
    setSession(next);
    return next.user;
  }, []);

  const logout = useCallback(() => {
    setAccessToken(null);
    persist(null);
    setSession(null);
  }, []);

  const updateUser = useCallback((user) => {
    setSession((current) => {
      if (!current) {
        return current;
      }
      const next = { ...current, user };
      persist(next);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!session) {
      return undefined;
    }
    const remaining = session.expiresAt - Date.now();
    if (remaining <= 0) {
      logout();
      return undefined;
    }
    const timer = window.setTimeout(() => {
      logout();
      navigate("/login", { replace: true });
    }, remaining);
    return () => window.clearTimeout(timer);
  }, [session, logout, navigate]);

  useEffect(() => {
    const onUnauthorized = () => {
      logout();
      navigate("/login", { replace: true });
    };
    window.addEventListener("veda:unauthorized", onUnauthorized);
    return () =>
      window.removeEventListener("veda:unauthorized", onUnauthorized);
  }, [logout, navigate]);

  const value = useMemo(
    () => ({
      user: session?.user || null,
      token: session?.token || null,
      isAuthenticated: Boolean(session),
      login,
      logout,
      updateUser,
    }),
    [session, login, logout, updateUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
