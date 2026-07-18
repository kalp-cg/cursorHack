"use client";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
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
import ListenButton from "@/components/ListenButton";
import VoiceMic from "@/components/VoiceMic";
import CounterfactualPanel from "@/components/CounterfactualPanel";
import ShareCaseBar, { decodeCaseParam } from "@/components/ShareCaseBar";
import { TranslatedText } from "@/components/TranslatedText";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import SensePanel from "@/components/SensePanel";
import DiscriminationCard from "@/components/DiscriminationCard";
import { useApp } from "@/lib/app-context";
import Link from "next/link";

const COMORBIDITY_KEYS = [
  { key: "comorbidityDiabetes", value: "Diabetes" },
  { key: "comorbidityPregnancy", value: "Pregnancy" },
  { key: "comorbidityAmlapitta", value: "Amlapitta" },
  { key: "comorbidityRaktapitta", value: "Raktapitta" },
] as const;

function IntakePanel({ onSubmit }: { onSubmit: (inp: VignetteInput) => void }) {
  const { t } = useApp();
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
      comorbidities: selectedComorbs,
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
        {t("newCase")}
      </h1>
      <p className="text-sm mb-8" style={{ color: "var(--veda-ink-soft)" }}>
        {t("newCaseHint")}
      </p>

      <label className="block text-sm font-medium mb-1" style={{ color: "var(--veda-ink)" }}>
        {t("vignetteLabel")}
      </label>
      <textarea
        value={freeText}
        onChange={(e) => setFreeText(e.target.value)}
        placeholder={t("vignettePlaceholder")}
        rows={3}
        className="w-full rounded-xl px-4 py-3 text-sm mb-3 resize-none outline-none"
        style={{
          background: "var(--veda-shila-deep)",
          border: "1px solid var(--veda-fog)",
          color: "var(--veda-ink)",
          fontFamily: "var(--font-ui)",
        }}
      />
      <div className="mb-6">
        <VoiceMic onTranscript={(text) => setFreeText((prev) => (prev ? `${prev} ${text}` : text))} />
      </div>

      <label className="block text-sm font-medium mb-1" style={{ color: "var(--veda-ink)" }}>
        {t("symptomsLabel")}
      </label>
      <div className="flex gap-2 mb-2">
        <input
          type="text"
          value={symptomInput}
          onChange={(e) => setSymptomInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addSymptom()}
          placeholder={t("placeholder")}
          className="flex-1 rounded-xl px-4 py-2 text-sm outline-none veda-input"
        />
        <PrimaryButton size="sm" onClick={addSymptom}>
          {t("addSymptom")}
        </PrimaryButton>
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

      <label className="block text-sm font-medium mb-2" style={{ color: "var(--veda-ink)" }}>
        {t("comorbiditiesLabel")}
      </label>
      <div className="flex flex-wrap gap-3 mb-8">
        {COMORBIDITY_KEYS.map((c) => {
          const selected = selectedComorbs.includes(c.value);
          return (
            <button
              key={c.value}
              type="button"
              onClick={() =>
                setSelectedComorbs((prev) =>
                  selected ? prev.filter((x) => x !== c.value) : [...prev, c.value]
                )
              }
              className="px-4 py-2 rounded-xl text-sm font-medium min-h-[44px] transition-all"
              style={{
                background: selected ? "var(--veda-kesar)" : "var(--veda-shila-deep)",
                color: selected ? "white" : "var(--veda-ink)",
                border: `1px solid ${selected ? "var(--veda-kesar)" : "var(--veda-fog)"}`,
              }}
            >
              {t(c.key)}
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
        {running ? t("rankingFormulations") : t("submitCase")}
      </PrimaryButton>
    </div>
  );
}

function ResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t, user, locale, conversationId, setConversationId } = useApp();
  const [response, setResponse] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showIntake, setShowIntake] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<string | null>(null);
  const [followUp, setFollowUp] = useState("");
  const [asking, setAsking] = useState(false);
  const localeBoot = useRef(true);

  useEffect(() => {
    if (searchParams.get("intake") === "true") {
      setShowIntake(true);
      setLoading(false);
      return;
    }

    const caseParam = searchParams.get("case");
    if (caseParam) {
      const decoded = decodeCaseParam(caseParam);
      if (decoded) {
        setLoading(true);
        const payload = { ...decoded, locale: decoded.locale || locale };
        sessionStorage.setItem("vedya_input", JSON.stringify(payload));
        api
          .recommend(payload)
          .then((result) => {
            if (result.conversation_id) setConversationId(result.conversation_id);
            sessionStorage.setItem("vedya_results", JSON.stringify(result));
            setResponse(result);
          })
          .catch(console.error)
          .finally(() => setLoading(false));
        return;
      }
    }

    const stored = sessionStorage.getItem("vedya_results");
    if (stored) {
      const parsed = JSON.parse(stored) as RecommendationResponse;
      setResponse(parsed);
      if (parsed.conversation_id) setConversationId(parsed.conversation_id);
    }
    setLoading(false);
  }, [searchParams, setConversationId]);

  // Re-rank with new locale so explanations switch EN ↔ HI ↔ GU
  useEffect(() => {
    if (localeBoot.current) {
      localeBoot.current = false;
      return;
    }
    if (showIntake) return;
    const raw = sessionStorage.getItem("vedya_input");
    if (!raw) return;
    let cancelled = false;
    (async () => {
      try {
        const inp = JSON.parse(raw) as VignetteInput;
        const payload = { ...inp, locale };
        sessionStorage.setItem("vedya_input", JSON.stringify(payload));
        setLoading(true);
        const result = await api.recommend(payload);
        if (cancelled) return;
        if (result.conversation_id) setConversationId(result.conversation_id);
        sessionStorage.setItem("vedya_results", JSON.stringify(result));
        setResponse(result);
      } catch (e) {
        console.error(e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [locale, showIntake, setConversationId]);

  const handleIntakeSubmit = useCallback(async (inp: VignetteInput) => {
    setLoading(true);
    try {
      const payload = { ...inp, locale };
      const result = await api.recommend(payload);
      if (result.conversation_id) setConversationId(result.conversation_id);
      sessionStorage.setItem("vedya_input", JSON.stringify(payload));
      sessionStorage.setItem("vedya_results", JSON.stringify(result));
      setResponse(result);
      setShowIntake(false);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [locale, setConversationId]);

  async function askFollowUp() {
    if (!followUp.trim()) return;
    setAsking(true);
    try {
      const result = await api.recommend({
        free_text: followUp.trim(),
        symptoms: [],
        rogas: [],
        comorbidities: [],
        top_k: 10,
        locale,
        conversation_id: user
          ? conversationId || response?.conversation_id || undefined
          : undefined,
        follow_up: Boolean(user && (conversationId || response?.conversation_id)),
      });
      if (result.conversation_id) setConversationId(result.conversation_id);
      sessionStorage.setItem("vedya_results", JSON.stringify(result));
      sessionStorage.setItem(
        "vedya_input",
        JSON.stringify({
          free_text: followUp.trim(),
          symptoms: [],
          rogas: [],
          comorbidities: [],
          top_k: 10,
          locale,
          conversation_id: result.conversation_id,
          follow_up: true,
        })
      );
      setResponse(result);
      setFollowUp("");
    } catch (e) {
      console.error(e);
    } finally {
      setAsking(false);
    }
  }

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
          <p style={{ color: "var(--veda-ink-soft)", fontFamily: "var(--font-ui)" }}>{t("rankingFormulations")}</p>
        </div>
      </div>
    );
  }

  if (!response) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen" style={{ background: "var(--veda-shila)" }}>
        <p style={{ color: "var(--veda-ink-soft)" }}>{t("noResults")}</p>
        <PrimaryButton className="mt-4" onClick={() => router.push("/")}>{t("goHome")}</PrimaryButton>
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
            comorbidities={response.results[0]?.safety_violations.length ? [t("constraintsActive")] : []}
            onReset={() => router.push("/")}
          />
        </div>
        {selectedForCompare.length === 2 && (
          <PrimaryButton
            size="sm"
            onClick={() => router.push(`/compare?a=${selectedForCompare[0]}&b=${selectedForCompare[1]}`)}
          >
            {t("compareSelected")} →
          </PrimaryButton>
        )}
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="veda-results-meta mb-5">
          <span className="veda-chip-meta">
            {response.llm_used ? t("modeLlm") : t("modeTemplate")}
          </span>
          <span className="veda-chip-meta">
            {t("corpusBadge")} {response.corpus_version}
          </span>
        </div>

        {/* Resolved terms */}
        {response.resolved_concepts.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {response.resolved_concepts.map((rc) => (
              <TermChip key={rc.concept_id} term={rc.surface_form} canonical={rc.canonical_name} />
            ))}
            {response.unresolved_terms.map((term) => (
              <TermChip key={term} term={term} variant="unresolved" />
            ))}
          </div>
        )}

        <SensePanel items={response.sense_disambiguations || []} />

        {/* 1. Safety panel */}
        {globalAlerts.length > 0 && <SafetyPanel violations={globalAlerts} />}

        {/* 2. Top pick */}
        {topResult && (
          <div
            className="rounded-2xl p-6 mb-4"
            style={{ background: "var(--veda-surface)", border: "1px solid var(--veda-harita-soft)" }}
          >
            <div className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "var(--veda-harita)" }}>
              {t("topRecommendation")}
            </div>
            <div className="text-2xl font-medium mb-1" style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}>
              {topResult.yoga_name}
            </div>
            <div className="text-sm mb-3" style={{ color: "var(--veda-ink-soft)" }}>
              {topResult.kalpana} · {t("fitScore")}: {topResult.score.toFixed(1)}
            </div>

            {(topResult.primary_indications.length > 0 || topResult.secondary_indications.length > 0) && (
              <div className="veda-ind-block mb-4">
                <div className="veda-ind-label">{t("indicationsTitle")}</div>
                {topResult.primary_indications.length > 0 && (
                  <p>
                    <strong>{t("primaryIndications")}:</strong>{" "}
                    {topResult.primary_indications.join(" · ")}
                  </p>
                )}
                {topResult.secondary_indications.length > 0 && (
                  <p>
                    <strong>{t("secondaryIndications")}:</strong>{" "}
                    {topResult.secondary_indications.join(" · ")}
                  </p>
                )}
              </div>
            )}

            {topResult.explanation && (
              <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--veda-ink)" }}>
                {topResult.explanation.summary}
              </p>
            )}
            <div className="mb-4">
              <ListenButton
                yogaName={topResult.yoga_name}
                kalpana={topResult.kalpana || ""}
                summary={topResult.explanation?.summary || ""}
              />
            </div>
            {topResult.rank_features && (
              <div className="mb-4">
                <ScoreBreakdown features={topResult.rank_features} />
              </div>
            )}
            {topResult.references.slice(0, 2).map((r) => (
              <CitationCard key={r.ref_id} reference={r} />
            ))}
            {topResult.differentiation_note && (
              <TranslatedText
                as="p"
                text={topResult.differentiation_note}
                className="mt-3 text-sm italic"
                style={{ color: "var(--veda-ink-soft)" }}
              />
            )}
            <div className="mt-4">
              <PrimaryButton
                size="sm"
                variant="outline"
                onClick={() => router.push(`/detail/${topResult.yoga_id}`)}
              >
                {t("viewDetail")} →
              </PrimaryButton>
            </div>
          </div>
        )}

        {activeResults.length >= 2 && (
          <DiscriminationCard
            a={activeResults[0]}
            b={activeResults[1]}
            onCompare={() =>
              router.push(`/compare?a=${activeResults[0].yoga_id}&b=${activeResults[1].yoga_id}`)
            }
          />
        )}

        <div className="veda-tip mb-6">
          <strong>{t("teachingTip")}</strong>
          <span>{t("teachingTipBody")}</span>
        </div>

        <CounterfactualPanel
          baseline={response}
          onApplied={(next) => {
            setResponse(next);
            if (next.conversation_id) setConversationId(next.conversation_id);
          }}
        />

        {/* 4. Full ranked list */}
        <h3 className="veda-list-title">{t("candidates")}</h3>
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
              {t("learnSynonyms")} →
            </button>
          </div>
        )}

        {/* Follow-up conversation — open to guests for usefulness */}
        <div
          className="mt-8 rounded-2xl p-5"
          style={{ background: "var(--veda-surface)", border: "1px solid var(--veda-fog)" }}
        >
          <h3 className="text-lg font-medium mb-1" style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}>
            {t("followUpTitle")}
          </h3>
          <p className="text-sm mb-3" style={{ color: "var(--veda-ink-soft)" }}>
            {user ? t("followUpHint") : t("followUpOpen")}
          </p>
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <input
                className="veda-input flex-1"
                value={followUp}
                onChange={(e) => setFollowUp(e.target.value)}
                placeholder={t("followUpPlaceholder")}
                onKeyDown={(e) => e.key === "Enter" && askFollowUp()}
              />
              <PrimaryButton onClick={askFollowUp} disabled={asking || !followUp.trim()}>
                {asking ? t("running") : t("askFollowUp")}
              </PrimaryButton>
            </div>
            <VoiceMic onTranscript={(text) => setFollowUp((prev) => (prev ? `${prev} ${text}` : text))} />
            {!user && (
              <Link href="/signup" style={{ color: "var(--veda-harita)", fontSize: "0.85rem" }}>
                {t("signup")} → {t("history")}
              </Link>
            )}
          </div>
        </div>

        <ShareCaseBar response={response} />

        {/* Stats */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          {[
            { label: t("candidates"), value: response.total_candidates },
            { label: t("excluded"), value: response.excluded_count },
            { label: t("warned"), value: response.warned_count },
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
