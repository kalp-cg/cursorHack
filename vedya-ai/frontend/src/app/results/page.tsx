"use client";
import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  api,
  RecommendationResponse,
  RecommendedFormulation,
  SafetyViolation,
  VignetteInput,
} from "@/lib/api";
import SafetyPanel from "@/components/SafetyPanel";
import RankRow from "@/components/RankRow";
import CoverageNote from "@/components/CoverageNote";
import CaseChip from "@/components/CaseChip";
import TermChip from "@/components/TermChip";
import PrimaryButton from "@/components/PrimaryButton";
import CitationCard from "@/components/CitationCard";

const COMORBIDITIES = ["Diabetes", "Pregnancy", "Amlapitta (Hyperacidity)", "Raktapitta (Bleeding)"];

function IntakePanel({ onSubmit }: { onSubmit: (inp: VignetteInput) => void }) {
  const [freeText, setFreeText] = useState("");
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [symptomInput, setSymptomInput] = useState("");
  const [selectedComorbs, setSelectedComorbs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);

  function addSymptom() {
    const s = symptomInput.trim();
    if (s && !symptoms.includes(s)) setSymptoms((prev) => [...prev, s]);
    setSymptomInput("");
  }

  async function handleSubmit() {
    setRunning(true);
    await onSubmit({
      free_text: freeText || undefined,
      symptoms,
      rogas: [],
      comorbidities: selectedComorbs.map((c) => c.split(" ")[0]),
      top_k: 10,
    });
    setRunning(false);
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12" style={{ fontFamily: "var(--font-ui)" }}>
      <h1
        className="text-3xl font-medium mb-2"
        style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}
      >
        New Case
      </h1>
      <p className="text-sm mb-8" style={{ color: "var(--veda-ink-soft)" }}>
        Enter symptoms or a clinical vignette to rank suitable formulations.
      </p>

      {/* Free text */}
      <label className="block text-sm font-medium mb-1" style={{ color: "var(--veda-ink)" }}>
        Clinical vignette (free text)
      </label>
      <textarea
        value={freeText}
        onChange={(e) => setFreeText(e.target.value)}
        placeholder="e.g. Patient with fever, cough, and runny nose for 3 days. No known comorbidities."
        rows={3}
        className="w-full rounded-xl px-4 py-3 text-sm mb-6 resize-none outline-none"
        style={{
          background: "var(--veda-shila-deep)",
          border: "1px solid var(--veda-fog)",
          color: "var(--veda-ink)",
          fontFamily: "var(--font-ui)",
        }}
      />

      {/* Symptom tags */}
      <label className="block text-sm font-medium mb-1" style={{ color: "var(--veda-ink)" }}>
        Symptoms / Rogas
      </label>
      <div className="flex gap-2 mb-2">
        <input
          type="text"
          value={symptomInput}
          onChange={(e) => setSymptomInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addSymptom()}
          placeholder="e.g. Jvara, Cough, Pinasa…"
          className="flex-1 rounded-xl px-4 py-2 text-sm outline-none"
          style={{
            background: "var(--veda-shila-deep)",
            border: "1px solid var(--veda-fog)",
            color: "var(--veda-ink)",
          }}
        />
        <button
          onClick={addSymptom}
          className="px-4 py-2 rounded-xl text-sm font-medium"
          style={{ background: "var(--veda-harita)", color: "white" }}
        >
          Add
        </button>
      </div>
      <div className="flex flex-wrap gap-2 mb-6">
        {symptoms.map((s) => (
          <TermChip
            key={s}
            term={s}
            onRemove={() => setSymptoms((prev) => prev.filter((x) => x !== s))}
          />
        ))}
      </div>

      {/* Comorbidities */}
      <label className="block text-sm font-medium mb-2" style={{ color: "var(--veda-ink)" }}>
        Comorbidities
      </label>
      <div className="flex flex-wrap gap-3 mb-8">
        {COMORBIDITIES.map((c) => {
          const selected = selectedComorbs.includes(c);
          return (
            <button
              key={c}
              onClick={() =>
                setSelectedComorbs((prev) =>
                  selected ? prev.filter((x) => x !== c) : [...prev, c]
                )
              }
              className="px-4 py-2 rounded-xl text-sm font-medium min-h-[44px] transition-all"
              style={{
                background: selected ? "var(--veda-kesar)" : "var(--veda-shila-deep)",
                color: selected ? "white" : "var(--veda-ink)",
                border: `1px solid ${selected ? "var(--veda-kesar)" : "var(--veda-fog)"}`,
              }}
            >
              {c}
            </button>
          );
        })}
      </div>

      <PrimaryButton
        size="lg"
        onClick={handleSubmit}
        disabled={running || (!freeText.trim() && symptoms.length === 0)}
        className="w-full"
      >
        {running ? "Ranking formulations…" : "Rank Formulations"}
      </PrimaryButton>
    </div>
  );
}

function ResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [response, setResponse] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showIntake, setShowIntake] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<string | null>(null);

  useEffect(() => {
    if (searchParams.get("intake") === "true") {
      setShowIntake(true);
      setLoading(false);
      return;
    }
    const stored = sessionStorage.getItem("vedya_results");
    if (stored) {
      setResponse(JSON.parse(stored));
    }
    setLoading(false);
  }, [searchParams]);

  const handleIntakeSubmit = useCallback(async (inp: VignetteInput) => {
    setLoading(true);
    try {
      const result = await api.recommend(inp);
      sessionStorage.setItem("vedya_results", JSON.stringify(result));
      setResponse(result);
      setShowIntake(false);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  function toggleCompare(yogaId: string) {
    setSelectedForCompare((prev) => {
      if (prev.includes(yogaId)) return prev.filter((id) => id !== yogaId);
      if (prev.length >= 2) return [prev[1], yogaId];
      return [...prev, yogaId];
    });
  }

  if (showIntake) {
    return <IntakePanel onSubmit={handleIntakeSubmit} />;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: "var(--veda-shila)" }}>
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin mx-auto mb-3" style={{ borderColor: "var(--veda-harita)" }} />
          <p style={{ color: "var(--veda-ink-soft)", fontFamily: "var(--font-ui)" }}>Ranking formulations…</p>
        </div>
      </div>
    );
  }

  if (!response) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen" style={{ background: "var(--veda-shila)" }}>
        <p style={{ color: "var(--veda-ink-soft)" }}>No results yet.</p>
        <PrimaryButton className="mt-4" onClick={() => router.push("/")}>Go Home</PrimaryButton>
      </div>
    );
  }

  const activeResults = response.results.filter((r) => !r.hard_excluded);
  const topResult = activeResults[0];
  const globalAlerts: SafetyViolation[] = response.safety_alerts;

  return (
    <div style={{ background: "var(--veda-shila)", minHeight: "100vh", fontFamily: "var(--font-ui)" }}>
      {/* Sticky top bar */}
      <div
        className="sticky top-0 z-20 px-6 py-3 flex items-center gap-4 flex-wrap"
        style={{ background: "var(--veda-ink)", borderBottom: "1px solid rgba(255,255,255,0.1)" }}
      >
        <button onClick={() => router.push("/")} className="text-sm" style={{ color: "rgba(247,249,248,0.6)" }}>← VedyaAI</button>
        <div className="flex-1">
          <CaseChip
            summary={response.vignette_summary}
            comorbidities={response.results[0]?.safety_violations.length ? ["Constraints active"] : []}
            onReset={() => router.push("/")}
          />
        </div>
        {selectedForCompare.length === 2 && (
          <PrimaryButton
            size="sm"
            onClick={() => router.push(`/compare?a=${selectedForCompare[0]}&b=${selectedForCompare[1]}`)}
          >
            Compare Selected →
          </PrimaryButton>
        )}
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Resolved terms */}
        {response.resolved_concepts.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {response.resolved_concepts.map((rc) => (
              <TermChip key={rc.concept_id} term={rc.surface_form} canonical={rc.canonical_name} />
            ))}
            {response.unresolved_terms.map((t) => (
              <TermChip key={t} term={t} variant="unresolved" />
            ))}
          </div>
        )}

        {/* 1. Safety panel */}
        {globalAlerts.length > 0 && <SafetyPanel violations={globalAlerts} />}

        {/* 2. Top pick */}
        {topResult && (
          <div
            className="rounded-2xl p-6 mb-4"
            style={{ background: "var(--veda-surface)", border: "1px solid var(--veda-harita-soft)" }}
          >
            <div className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "var(--veda-harita)" }}>
              Top Recommendation
            </div>
            <div className="text-2xl font-medium mb-1" style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}>
              {topResult.yoga_name}
            </div>
            <div className="text-sm mb-3" style={{ color: "var(--veda-ink-soft)" }}>
              {topResult.kalpana} · Fit Score: {topResult.score.toFixed(1)}
            </div>
            {topResult.explanation && (
              <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--veda-ink)" }}>
                {topResult.explanation.summary}
              </p>
            )}
            {topResult.references.slice(0, 1).map((r) => (
              <CitationCard key={r.ref_id} reference={r} />
            ))}
            {topResult.differentiation_note && (
              <p className="mt-3 text-sm italic" style={{ color: "var(--veda-ink-soft)" }}>
                {topResult.differentiation_note}
              </p>
            )}
          </div>
        )}

        {/* 3. Compare teaser */}
        {activeResults.length >= 2 && (
          <div
            className="rounded-xl p-4 mb-6 flex items-center justify-between"
            style={{ background: "var(--veda-harita-soft)", border: "1px solid var(--veda-harita)" }}
          >
            <span className="text-sm font-medium" style={{ color: "var(--veda-harita)" }}>
              Why {activeResults[0]?.yoga_name} over {activeResults[1]?.yoga_name}?
            </span>
            <PrimaryButton
              size="sm"
              onClick={() =>
                router.push(`/compare?a=${activeResults[0].yoga_id}&b=${activeResults[1].yoga_id}`)
              }
            >
              Compare →
            </PrimaryButton>
          </div>
        )}

        {/* 4. Full ranked list */}
        <div className="space-y-2">
          {response.results.map((r, idx) => (
            <RankRow
              key={r.yoga_id}
              formulation={r}
              index={idx}
              selected={selectedDetail === r.yoga_id}
              onSelect={() => {
                if (r.hard_excluded) return;
                router.push(`/detail/${r.yoga_id}`);
              }}
              compareSelected={selectedForCompare.includes(r.yoga_id)}
              onCompareToggle={() => toggleCompare(r.yoga_id)}
            />
          ))}
        </div>

        {/* 5. Coverage note */}
        {response.coverage_note && (
          <div className="mt-4">
            <CoverageNote note={response.coverage_note} />
          </div>
        )}

        {/* Learn drawer link */}
        {response.resolved_concepts.length > 0 && (
          <div className="mt-6 text-center">
            <button
              onClick={() => router.push(`/learn?concept=${response.resolved_concepts[0]?.canonical_name}`)}
              className="text-sm underline"
              style={{ color: "var(--veda-tamra)" }}
            >
              Learn synonyms & terminology →
            </button>
          </div>
        )}

        {/* Stats */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          {[
            { label: "Candidates", value: response.total_candidates },
            { label: "Excluded", value: response.excluded_count },
            { label: "Warned", value: response.warned_count },
          ].map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl py-3"
              style={{ background: "var(--veda-surface)", border: "1px solid var(--veda-shila-deep)" }}
            >
              <div
                className="text-2xl font-bold tabular-nums"
                style={{ color: "var(--veda-ink)", fontFamily: "var(--font-ui)" }}
              >
                {stat.value}
              </div>
              <div className="text-xs mt-1" style={{ color: "var(--veda-ink-soft)" }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense>
      <ResultsContent />
    </Suspense>
  );
}
