"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import PrimaryButton from "@/components/PrimaryButton";

export default function SignupPage() {
  const router = useRouter();
  const { t, setSession, locale } = useApp();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.signup({
        email,
        password,
        display_name: displayName || undefined,
        preferred_locale: locale,
      });
      setSession(res.access_token, res.user);
      router.push("/");
    } catch {
      setError(t("signupError"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="veda-auth-shell">
      <div className="veda-auth-card">
        <h1>{t("signupTitle")}</h1>
        <p className="veda-auth-sub">{t("signupSub")}</p>
        <form onSubmit={onSubmit}>
          <div className="veda-field">
            <label htmlFor="signup-name">{t("displayName")}</label>
            <input
              id="signup-name"
              className="veda-input"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              autoComplete="name"
            />
          </div>
          <div className="veda-field">
            <label htmlFor="signup-email">{t("email")}</label>
            <input
              id="signup-email"
              className="veda-input"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="veda-field">
            <label htmlFor="signup-password">{t("password")}</label>
            <input
              id="signup-password"
              className="veda-input"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              placeholder={t("passwordHint")}
            />
          </div>
          {error ? <p className="veda-error">{error}</p> : null}
          <PrimaryButton type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? t("pleaseWait") : t("createAccount")}
          </PrimaryButton>
        </form>
        <p className="veda-auth-footer">
          {t("haveAccount")} <Link href="/login">{t("login")}</Link>
        </p>
      </div>
    </div>
  );
}
