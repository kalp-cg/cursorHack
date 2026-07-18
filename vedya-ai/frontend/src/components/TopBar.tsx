"use client";

import Link from "next/link";
import { useApp } from "@/lib/app-context";
import { LOCALES, Locale } from "@/lib/i18n";

export default function TopBar() {
  const { locale, setLocale, t, user, logout } = useApp();

  return (
    <header className="veda-topbar">
      <Link href="/" className="veda-topbar-brand">
        {t("brand")}
      </Link>

      <div className="veda-topbar-actions">
        <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", color: "var(--veda-ink-soft)" }}>
          <span className="sr-only" style={{ position: "absolute", width: 1, height: 1, overflow: "hidden" }}>
            {t("language")}
          </span>
          <select
            className="veda-select"
            value={locale}
            onChange={(e) => setLocale(e.target.value as Locale)}
            aria-label={t("language")}
          >
            {LOCALES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </label>

        {user ? (
          <>
            <Link href="/history" className="veda-link-btn veda-link-btn-ghost">
              {t("history")}
            </Link>
            <span style={{ color: "var(--veda-ink-soft)", fontSize: "0.82rem", maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user.display_name || user.email}
            </span>
            <button type="button" className="veda-link-btn veda-link-btn-ghost" onClick={logout}>
              {t("logout")}
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="veda-link-btn veda-link-btn-ghost">
              {t("login")}
            </Link>
            <Link href="/signup" className="veda-link-btn veda-link-btn-primary">
              {t("signup")}
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
