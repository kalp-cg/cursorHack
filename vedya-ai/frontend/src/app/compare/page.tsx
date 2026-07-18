"use client";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, CompareResult } from "@/lib/api";
import CompareTable from "@/components/CompareTable";
import PrimaryButton from "@/components/PrimaryButton";
import ListenButton from "@/components/ListenButton";
import ErrorBanner from "@/components/ErrorBanner";
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
      setError(t("selectTwoCompare"));
      setLoading(false);
      return;
    }
    let vignette: {
      free_text?: string;
      symptoms?: string[];
      rogas?: string[];
      comorbidities?: string[];
      locale?: string;
    } = { locale };
    try {
      const raw = sessionStorage.getItem("vedya_input");
      if (raw) vignette = { ...JSON.parse(raw), locale };
    } catch {
      /* ignore */
    }
    setLoading(true);
    setError("");
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
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <div>
            <PrimaryButton size="sm" variant="outline" onClick={() => router.push("/results")}>
              ← {t("backToResults")}
            </PrimaryButton>
            <h1
              className="text-2xl font-medium mt-4"
              style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}
            >
              {t("compareTitle")}
            </h1>
            {result?.winner_reason && (
              <p className="text-sm mt-1" style={{ color: "var(--veda-harita)" }}>
                {t("preferredForCase")}: {winnerName}
              </p>
            )}
          </div>
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
          <ErrorBanner message={error} onDismiss={() => setError("")} dismissLabel={t("dismiss")} />
        )}

        {result && !loading && <CompareTable result={result} />}
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
