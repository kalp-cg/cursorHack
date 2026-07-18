"use client";
import { useMemo, useState } from "react";
import {
  api,
  RecommendationResponse,
  RecommendedFormulation,
  VignetteInput,
} from "@/lib/api";
import PrimaryButton from "./PrimaryButton";
import { useApp } from "@/lib/app-context";

const CF_OPTIONS = [
  { id: "Diabetes", labelKey: "cfDiabetes" as const, value: "Diabetes" },
  { id: "Pregnancy", labelKey: "cfPregnancy" as const, value: "Pregnancy" },
  { id: "Amlapitta", labelKey: "cfAmlapitta" as const, value: "Amlapitta" },
  { id: "Raktapitta", labelKey: "cfRaktapitta" as const, value: "Raktapitta" },
];

type Props = {
  baseline: RecommendationResponse;
  onApplied?: (next: RecommendationResponse) => void;
};

function topActive(res: RecommendationResponse): RecommendedFormulation | undefined {
  return res.results.find((r) => !r.hard_excluded) || res.results[0];
}

function loadBaseInput(baseline: RecommendationResponse): VignetteInput {
  try {
    const raw = sessionStorage.getItem("vedya_input");
    if (raw) return JSON.parse(raw) as VignetteInput;
  } catch {
    /* ignore */
  }
  return {
    free_text: baseline.vignette_summary,
    symptoms: [],
    rogas: [],
    comorbidities: [],
    top_k: 10,
  };
}

export default function CounterfactualPanel({ baseline, onApplied }: Props) {
  const { t, locale } = useApp();
  const [selected, setSelected] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [alt, setAlt] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState("");

  const baseTop = useMemo(() => topActive(baseline), [baseline]);

  function toggle(id: string) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function runWhatIf() {
    setRunning(true);
    setError("");
    try {
      const base = loadBaseInput(baseline);
      const mergedComorbs = Array.from(
        new Set([...(base.comorbidities || []), ...selected])
      );
      const result = await api.recommend({
        ...base,
        comorbidities: mergedComorbs,
        locale,
        top_k: base.top_k || 10,
        // Fresh counterfactual run — do not append to conversation thread
        conversation_id: undefined,
        follow_up: false,
      });
      setAlt(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("cfError"));
    } finally {
      setRunning(false);
    }
  }

  function applyAsCase() {
    if (!alt) return;
    sessionStorage.setItem("vedya_results", JSON.stringify(alt));
    const base = loadBaseInput(baseline);
    sessionStorage.setItem(
      "vedya_input",
      JSON.stringify({
        ...base,
        comorbidities: Array.from(new Set([...(base.comorbidities || []), ...selected])),
      })
    );
    onApplied?.(alt);
  }

  const altTop = alt ? topActive(alt) : undefined;
  const scoreDelta =
    baseTop && altTop ? altTop.score - baseTop.score : null;
  const flipped =
    baseTop && altTop ? baseTop.yoga_id !== altTop.yoga_id : false;
  const safetyFlip =
    (baseline.excluded_count || 0) !== (alt?.excluded_count || 0) ||
    (baseline.warned_count || 0) !== (alt?.warned_count || 0);

  return (
    <section className="veda-cf-panel" aria-label={t("cfTitle")}>
      <h3 className="veda-cf-title">{t("cfTitle")}</h3>
      <p className="veda-cf-hint">{t("cfHint")}</p>

      <div className="veda-cf-toggles">
        {CF_OPTIONS.map((opt) => {
          const on = selected.includes(opt.value);
          return (
            <button
              key={opt.id}
              type="button"
              className={`veda-cf-toggle ${on ? "is-on" : ""}`}
              aria-pressed={on}
              onClick={() => toggle(opt.value)}
            >
              {t(opt.labelKey)}
            </button>
          );
        })}
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <PrimaryButton size="sm" onClick={runWhatIf} disabled={running || selected.length === 0}>
          {running ? t("cfRunning") : t("cfRun")}
        </PrimaryButton>
        {alt && (
          <PrimaryButton size="sm" variant="outline" onClick={applyAsCase}>
            {t("cfApply")}
          </PrimaryButton>
        )}
      </div>

      {error && (
        <p style={{ color: "var(--veda-agni)", fontSize: "0.8rem", margin: "0 0 0.5rem" }}>
          {t("cfError")}
        </p>
      )}

      {alt && baseTop && altTop && (
        <div className="veda-cf-delta">
          <div className="veda-cf-card">
            <div className="veda-cf-card-label">{t("cfBaseline")}</div>
            <div className="veda-cf-card-name">{baseTop.yoga_name}</div>
            <div className="veda-cf-card-meta">
              {t("fitScore")}: {baseTop.score.toFixed(1)} · {t("excluded")}: {baseline.excluded_count}
            </div>
          </div>
          <div className="veda-cf-card" style={flipped ? { borderColor: "var(--veda-kesar)" } : undefined}>
            <div className="veda-cf-card-label">{t("cfAlternate")}</div>
            <div className="veda-cf-card-name">{altTop.yoga_name}</div>
            <div className="veda-cf-card-meta">
              {t("fitScore")}: {altTop.score.toFixed(1)}
              {scoreDelta !== null && (
                <>
                  {" "}
                  ({scoreDelta >= 0 ? "+" : ""}
                  {scoreDelta.toFixed(1)})
                </>
              )}
              {" · "}
              {t("excluded")}: {alt.excluded_count}
            </div>
            {(flipped || safetyFlip) && (
              <div
                style={{
                  marginTop: "0.45rem",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  color: "var(--veda-kesar)",
                }}
              >
                {flipped ? t("cfRankFlip") : t("cfSafetyFlip")}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
