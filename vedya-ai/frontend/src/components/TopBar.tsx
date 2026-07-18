"use client";

import Link from "next/link";
import { useApp } from "@/lib/app-context";
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function TopBar() {
  const { t, user, logout } = useApp();

  return (
    <header className="veda-topbar">
      <div className="veda-topbar-left">
        <Link href="/" className="veda-topbar-brand">
          {t("brand")}
        </Link>
        <nav className="veda-topbar-nav" aria-label="Primary">
          <Link href="/#try-cases" className="veda-nav-link">
            {t("navTry")}
          </Link>
          <Link href="/learn?concept=Jvara" className="veda-nav-link">
            {t("navLearn")}
          </Link>
          <Link href="/ask" className="veda-nav-link">
            {t("navAsk")}
          </Link>
        </nav>
      </div>

      <div className="veda-topbar-actions">
        <LanguageSwitcher />

        {user ? (
          <>
            {user.role === "admin" && (
              <Link href="/admin" className="veda-link-btn veda-link-btn-primary">
                {t("navAdmin")}
              </Link>
            )}
            <Link href="/history" className="veda-nav-link">
              {t("history")}
            </Link>
            <span className="veda-topbar-user">{user.display_name || user.email}</span>
            <button type="button" className="veda-nav-link" onClick={logout}>
              {t("logout")}
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="veda-nav-link">
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
