"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import PrimaryButton from "@/components/PrimaryButton";

export default function ForgotPasswordPage() {
  const { t } = useApp();
  const [email, setEmail] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [issuedCode, setIssuedCode] = useState<string | null>(null);
  const [step, setStep] = useState<"request" | "reset">("request");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onRequestCode(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const res = await api.forgotPassword(email);
      setMessage(res.emailed ? t("checkEmailHint") : res.message);
      if (res.reset_code) {
        setIssuedCode(res.reset_code);
        setResetCode(res.reset_code);
      } else {
        setIssuedCode(null);
      }
      setStep("reset");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "";
      const detailMatch = msg.match(/"detail"\s*:\s*"([^"]+)"/);
      setError(detailMatch?.[1] || t("forgotError"));
    } finally {
      setLoading(false);
    }
  }

  async function onReset(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const res = await api.resetPassword({
        email,
        reset_code: resetCode,
        new_password: newPassword,
      });
      setMessage(res.message || t("resetSuccess"));
      setIssuedCode(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "";
      const detailMatch = msg.match(/"detail"\s*:\s*"([^"]+)"/);
      setError(detailMatch?.[1] || t("resetError"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="veda-auth-shell">
      <div className="veda-auth-card">
        <h1>{t("forgotTitle")}</h1>
        <p className="veda-auth-sub">{t("forgotSub")}</p>

        {step === "request" ? (
          <form onSubmit={onRequestCode}>
            <div className="veda-field">
              <label htmlFor="forgot-email">{t("email")}</label>
              <input
                id="forgot-email"
                className="veda-input"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            {error ? <p className="veda-error">{error}</p> : null}
            <PrimaryButton type="submit" disabled={loading} style={{ width: "100%" }}>
              {loading ? t("pleaseWait") : t("sendResetCode")}
            </PrimaryButton>
          </form>
        ) : (
          <form onSubmit={onReset}>
            {issuedCode ? (
              <p
                style={{
                  margin: "0 0 1rem",
                  padding: "0.75rem 1rem",
                  borderRadius: "0.75rem",
                  background: "var(--veda-harita-soft)",
                  color: "var(--veda-ink)",
                  fontSize: "0.9rem",
                }}
              >
                {t("resetCodeLabel")}: <strong style={{ letterSpacing: "0.12em" }}>{issuedCode}</strong>
              </p>
            ) : null}
            {message ? (
              <p style={{ margin: "0 0 0.85rem", fontSize: "0.88rem", color: "var(--veda-ink-soft)" }}>
                {message}
              </p>
            ) : null}
            <div className="veda-field">
              <label htmlFor="forgot-email-ro">{t("email")}</label>
              <input
                id="forgot-email-ro"
                className="veda-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="veda-field">
              <label htmlFor="reset-code">{t("resetCode")}</label>
              <input
                id="reset-code"
                className="veda-input"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={resetCode}
                onChange={(e) => setResetCode(e.target.value)}
                required
                minLength={6}
                maxLength={12}
              />
            </div>
            <div className="veda-field">
              <label htmlFor="new-password">{t("newPassword")}</label>
              <input
                id="new-password"
                className="veda-input"
                type="password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                placeholder={t("passwordHint")}
              />
            </div>
            {error ? <p className="veda-error">{error}</p> : null}
            <PrimaryButton type="submit" disabled={loading} style={{ width: "100%" }}>
              {loading ? t("pleaseWait") : t("updatePassword")}
            </PrimaryButton>
          </form>
        )}

        <p className="veda-auth-footer">
          <Link href="/login">{t("backToLogin")}</Link>
        </p>
      </div>
    </div>
  );
}
