"use client";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, CompareResult } from "@/lib/api";
import CompareTable from "@/components/CompareTable";
import PrimaryButton from "@/components/PrimaryButton";
import ListenButton from "@/components/ListenButton";
import { useApp } from "@/lib/app-context";

function CompareContent() {
  const router = useRouter();
  const { t, locale } = useApp();
  const params = useSearchParams();
  const yogaAId = params.get("a") || "";
  const yogaBId = params.get("b") || "";

  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!yogaAId || !yogaBId) {
      setError(t("noResults"));
      setLoading(false);
      return;
    }
    let vignette: { free_text?: string; symptoms?: string[]; rogas?: string[]; comorbidities?: string[]; locale?: string } = { locale };
    try {
      const raw = sessionStorage.getItem("vedya_input");
      if (raw) vignette = { ...JSON.parse(raw), locale };
    } catch {
      /* ignore */
    }
    api
      .compare(yogaAId, yogaBId, vignette)
      .then(setResult)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [yogaAId, yogaBId, locale, t]);

  const winnerName =
    result?.winner_yoga_id === result?.yoga_a.yoga_id
      ? result?.yoga_a.yoga_name
      : result?.winner_yoga_id === result?.yoga_b.yoga_id
        ? result?.yoga_b.yoga_name
        : result?.yoga_a.yoga_name;

  return (
    <div style={{ background: "var(--veda-shila)", minHeight: "100vh" }}>
      <div
        className="sticky top-0 z-10 px-6 py-3 flex items-center gap-4"
        style={{ background: "var(--veda-ink)" }}
      >
        <button onClick={() => router.back()} className="text-sm" style={{ color: "rgba(247,249,248,0.6)" }}>
          ← Results
        </button>
        <span
          className="text-base font-semibold"
          style={{ fontFamily: "var(--font-display)", color: "#F7F9F8" }}
        >
          {t("compare")}
        </span>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <h1
            className="text-2xl font-medium"
            style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}
          >
            Formulation Comparison
          </h1>
          {result && (
            <ListenButton
              yogaName={winnerName || result.yoga_a.yoga_name}
              summary={result.discrimination_explanation?.summary || ""}
              winnerReason={result.winner_reason || t("speakWhy")}
            />
          )}
        </div>

        {loading && (
          <div className="flex justify-center py-16">
            <div
              className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin"
              style={{ borderColor: "var(--veda-harita)" }}
            />
          </div>
        )}

        {error && (
          <div
            className="text-sm p-4 rounded-xl"
            style={{ background: "var(--veda-agni-soft)", color: "var(--veda-agni)" }}
          >
            {error}
          </div>
        )}

        {result && !loading && <CompareTable result={result} />}

        <div className="mt-8 flex gap-4">
          <PrimaryButton variant="outline" onClick={() => router.back()}>
            ← Back to Results
          </PrimaryButton>
        </div>
      </div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense>
      <CompareContent />
    </Suspense>
  );
}
