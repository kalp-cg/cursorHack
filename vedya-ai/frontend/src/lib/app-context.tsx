"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Locale, t as translate } from "@/lib/i18n";

const TOKEN_KEY = "vedya_token";
const USER_KEY = "vedya_user";
const LOCALE_KEY = "vedya_locale";
const CONV_KEY = "vedya_conversation_id";

export interface AuthUser {
  user_id: string;
  email: string;
  display_name?: string | null;
  preferred_locale: string;
  role?: string;
}

interface AppState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Record<string, string>) => string;
  token: string | null;
  user: AuthUser | null;
  setSession: (token: string, user: AuthUser) => void;
  logout: () => void;
  conversationId: string | null;
  setConversationId: (id: string | null) => void;
}

const AppCtx = createContext<AppState | null>(null);

function applyDocumentLocale(next: Locale) {
  if (typeof document === "undefined") return;
  document.documentElement.lang = next === "gu" ? "gu" : "en";
  document.documentElement.dataset.locale = next;
  document.body.classList.remove("locale-en", "locale-gu");
  document.body.classList.add(`locale-${next}`);
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [conversationId, setConversationIdState] = useState<string | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(LOCALE_KEY);
      const loc: Locale = stored === "gu" ? "gu" : "en";
      setLocaleState(loc);
      applyDocumentLocale(loc);
      if (stored && stored !== loc) localStorage.setItem(LOCALE_KEY, loc);
      const tok = localStorage.getItem(TOKEN_KEY);
      const usr = localStorage.getItem(USER_KEY);
      if (tok && usr) {
        setToken(tok);
        setUser(JSON.parse(usr));
      }
      setConversationIdState(sessionStorage.getItem(CONV_KEY));
    } catch {
      /* ignore */
    }
  }, []);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    localStorage.setItem(LOCALE_KEY, next);
    applyDocumentLocale(next);
  }, []);

  const setSession = useCallback(
    (tok: string, usr: AuthUser) => {
      setToken(tok);
      setUser(usr);
      localStorage.setItem(TOKEN_KEY, tok);
      localStorage.setItem(USER_KEY, JSON.stringify(usr));
      if (usr.preferred_locale === "en" || usr.preferred_locale === "gu") {
        setLocale(usr.preferred_locale);
      }
    },
    [setLocale]
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(CONV_KEY);
    setConversationIdState(null);
  }, []);

  const setConversationId = useCallback((id: string | null) => {
    setConversationIdState(id);
    if (id) sessionStorage.setItem(CONV_KEY, id);
    else sessionStorage.removeItem(CONV_KEY);
  }, []);

  // Stable across auth/conversation updates — putting `t` in effect deps used to
  // re-fire recommend/presets whenever conversationId changed (infinite loop).
  const t = useCallback(
    (key: string, vars?: Record<string, string>) => translate(locale, key, vars),
    [locale]
  );

  const value = useMemo<AppState>(
    () => ({
      locale,
      setLocale,
      t,
      token,
      user,
      setSession,
      logout,
      conversationId,
      setConversationId,
    }),
    [locale, setLocale, t, token, user, setSession, logout, conversationId, setConversationId]
  );

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp() {
  const ctx = useContext(AppCtx);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}
