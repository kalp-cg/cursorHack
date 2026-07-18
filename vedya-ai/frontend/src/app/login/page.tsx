"use client";

import { FormEvent, Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import PrimaryButton from "@/components/PrimaryButton";

function safeReturnTo(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return "/";
  return raw;
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t, setSession } = useApp();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const returnTo = safeReturnTo(searchParams.get("returnTo"));

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.login({ email, password });
      setSession(res.access_token, res.user);
      router.push(returnTo);
    } catch {
      setError(t("authError"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="veda-auth-shell">
      <div className="veda-auth-card">
        <h1>{t("loginTitle")}</h1>
        <p className="veda-auth-sub">{t("loginSub")}</p>
        <form onSubmit={onSubmit}>
          <div className="veda-field">
            <label htmlFor="login-email">{t("email")}</label>
            <input
              id="login-email"
              className="veda-input"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="veda-field">
            <label htmlFor="login-password">{t("password")}</label>
            <input
              id="login-password"
              className="veda-input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>
          {error ? <p className="veda-error">{error}</p> : null}
          <PrimaryButton type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? t("pleaseWait") : t("login")}
          </PrimaryButton>
        </form>
        <p className="veda-auth-footer">
          {t("noAccount")}{" "}
          <Link href={`/signup?returnTo=${encodeURIComponent(returnTo)}`}>{t("signup")}</Link>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
