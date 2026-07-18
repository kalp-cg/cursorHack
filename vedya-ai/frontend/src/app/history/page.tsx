"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, RecommendationResponse } from "@/lib/api";
import { useApp } from "@/lib/app-context";

export default function HistoryPage() {
  const { t, user, setConversationId } = useApp();
  const router = useRouter();
  const [items, setItems] = useState<Array<{ conversation_id: string; title: string; updated_at?: string }>>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }
    api
      .listConversations()
      .then(setItems)
      .catch(() => setError(t("authError")));
  }, [user, router, t]);

  async function openCase(id: string) {
    try {
      const detail = await api.getConversation(id);
      const lastAssistant = [...detail.messages].reverse().find((m) => m.role === "assistant" && m.payload);
      if (lastAssistant?.payload) {
        sessionStorage.setItem("vedya_results", JSON.stringify(lastAssistant.payload as RecommendationResponse));
        setConversationId(id);
        router.push("/results");
      }
    } catch {
      setError(t("authError"));
    }
  }

  return (
    <div className="veda-auth-shell">
      <div className="veda-auth-card" style={{ maxWidth: 560 }}>
        <h1>{t("history")}</h1>
        <p className="veda-auth-sub">{t("followUpHint")}</p>
        {error ? <p className="veda-error">{error}</p> : null}
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: "0.55rem" }}>
          {items.map((c) => (
            <li key={c.conversation_id}>
              <button
                type="button"
                onClick={() => openCase(c.conversation_id)}
                className="veda-link-btn veda-link-btn-ghost"
                style={{ width: "100%", justifyContent: "space-between", padding: "0.85rem 1rem" }}
              >
                <span style={{ textAlign: "left" }}>
                  <strong style={{ display: "block" }}>{c.title || t("newCase")}</strong>
                  <span style={{ fontSize: "0.78rem", color: "var(--veda-ink-soft)" }}>{c.updated_at}</span>
                </span>
                <span style={{ color: "var(--veda-harita)" }}>{t("openCase")}</span>
              </button>
            </li>
          ))}
        </ul>
        {!items.length && !error ? (
          <p style={{ color: "var(--veda-ink-soft)", marginTop: "0.75rem" }}>{t("historyEmpty")}</p>
        ) : null}
        <p className="veda-auth-footer">
          <Link href="/">{t("goHome")}</Link>
        </p>
      </div>
    </div>
  );
}
