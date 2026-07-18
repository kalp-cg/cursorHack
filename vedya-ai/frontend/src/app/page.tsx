"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, PresetVignette } from "@/lib/api";
import PrimaryButton from "@/components/PrimaryButton";
import VoiceMic from "@/components/VoiceMic";
import ListenButton from "@/components/ListenButton";
import ErrorBanner from "@/components/ErrorBanner";
import { useApp } from "@/lib/app-context";

const PRESET_META: Record<string, { badgeKey: string; order: number }> = {
  pinasa_urti: { badgeKey: "wow1Badge", order: 0 },
  inflammatory_shotha: { badgeKey: "wow2Badge", order: 1 },
  diabetic_respiratory: { badgeKey: "wow3Badge", order: 2 },
};

function PresetCard({
  preset,
  onRun,
  loading,
  openLabel,
  runningLabel,
  badge,
}: {
  preset: PresetVignette;
  onRun: () => void;
  loading: boolean;
  openLabel: string;
  runningLabel: string;
  badge?: string;
}) {
  const caseText = [
    preset.label,
    preset.description,
    preset.vignette.free_text || (preset.vignette.symptoms || []).join(", "),
  ]
    .filter(Boolean)
    .join(". ");

  return (
    <article
      className="veda-preset-card"
      onClick={!loading ? onRun : undefined}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if ((e.key === "Enter" || e.key === " ") && !loading) onRun();
      }}
    >
      {badge && <span className="veda-wow-badge">{badge}</span>}
      <h3 className="veda-preset-label">{preset.label}</h3>
      <p className="veda-preset-desc">{preset.description}</p>
      <div className="veda-preset-actions" onClick={(e) => e.stopPropagation()}>
        <PrimaryButton
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onRun();
          }}
          disabled={loading}
        >
          {loading ? runningLabel : openLabel}
        </PrimaryButton>
        <ListenButton rawText={caseText} yogaName={preset.label} size="sm" />
      </div>
    </article>
  );
}

export default function HomePage() {
  const router = useRouter();
  const { t, locale, setConversationId, user } = useApp();
  const [presets, setPresets] = useState<PresetVignette[]>([]);
  const [loadingPreset, setLoadingPreset] = useState<string | null>(null);
  const [freeText, setFreeText] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getPresets(locale)
      .then(setPresets)
      .catch(() => setError(t("loadPresetsError")));
  }, [locale, t]);

  const sortedPresets = [...presets].sort((a, b) => {
    const oa = PRESET_META[a.id]?.order ?? 99;
    const ob = PRESET_META[b.id]?.order ?? 99;
    return oa - ob;
  });

  async function runPreset(presetId: string) {
    setLoadingPreset(presetId);
    setError("");
    try {
      const result = await api.runPreset(presetId, locale);
      if (result.conversation_id) setConversationId(result.conversation_id);
      const preset = presets.find((p) => p.id === presetId);
      if (preset?.vignette) {
        sessionStorage.setItem(
          "vedya_input",
          JSON.stringify({ ...preset.vignette, locale })
        );
      }
      sessionStorage.setItem("vedya_results", JSON.stringify(result));
      router.push("/results");
    } catch (e) {
      setError(e instanceof Error ? e.message : t("rankError"));
    } finally {
      setLoadingPreset(null);
    }
  }

  async function runFreeText() {
    if (!freeText.trim()) return;
    setRunning(true);
    setError("");
    try {
      const result = await api.recommend({
        free_text: freeText,
        symptoms: [],
        rogas: [],
        comorbidities: [],
        top_k: 10,
        locale,
      });
      if (result.conversation_id) setConversationId(result.conversation_id);
      sessionStorage.setItem(
        "vedya_input",
        JSON.stringify({
          free_text: freeText,
          symptoms: [],
          rogas: [],
          comorbidities: [],
          top_k: 10,
          locale,
        })
      );
      sessionStorage.setItem("vedya_results", JSON.stringify(result));
      router.push("/results");
    } catch (e) {
      setError(e instanceof Error ? e.message : t("rankError"));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="veda-page">
      {/* 1. Arrive — brand + problem-aware promise */}
      <section className="veda-hero">
        <div className="veda-hero-texture" aria-hidden />
        <div className="veda-hero-inner">
          <h1 className="veda-brand">{t("brand")}</h1>
          <p className="veda-tagline">{t("tagline")}</p>
          <p className="veda-lede">{t("lede")}</p>

          <div className="veda-hero-ctas">
            <PrimaryButton
              size="lg"
              onClick={() => runPreset("pinasa_urti")}
              disabled={loadingPreset === "pinasa_urti"}
            >
              {loadingPreset === "pinasa_urti" ? t("running") : t("heroCta")}
            </PrimaryButton>
            <PrimaryButton
              variant="outline"
              size="lg"
              className="veda-btn-on-dark"
              onClick={() => router.push("/results?intake=true")}
            >
              {t("newCase")}
            </PrimaryButton>
          </div>
          <p className="veda-hero-secondary-hint">{t("newCaseWhy")}</p>

          {error && (
            <div className="veda-hero-error">
              <ErrorBanner
                message={error}
                onDismiss={() => setError("")}
                dismissLabel={t("dismiss")}
                retryLabel={t("retry")}
              />
            </div>
          )}

          <div className="veda-search-row veda-search-row-hero">
            <input
              type="text"
              className="veda-input"
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              placeholder={t("placeholder")}
              onKeyDown={(e) => e.key === "Enter" && runFreeText()}
              aria-label={t("clinicalVignetteAria")}
            />
            <PrimaryButton onClick={runFreeText} disabled={running || !freeText.trim()}>
              {running ? t("ranking") : t("rank")}
            </PrimaryButton>
          </div>
          <p className="veda-hero-secondary-hint">{t("freeTextSecondary")}</p>

          <div className="veda-hero-voice">
            <VoiceMic onTranscript={(text) => setFreeText((prev) => (prev ? `${prev} ${text}` : text))} />
          </div>
        </div>
      </section>

      {/* 2. Understand the problem */}
      <section className="veda-section veda-problem">
        <h2 className="veda-section-title">{t("problemTitle")}</h2>
        <p className="veda-problem-body">{t("problemBody")}</p>
        <p className="veda-problem-punch">{t("problemPunch")}</p>
        <div className="veda-twin-strip" aria-hidden>
          <div className="veda-twin">
            <strong>{t("twinPunarnavadi")}</strong>
            <span>{t("twinShothaTags")}</span>
          </div>
          <span className="veda-twin-vs">{t("twinVs")}</span>
          <div className="veda-twin">
            <strong>{t("twinVyaghryadi")}</strong>
            <span>{t("twinPinasaTags")}</span>
          </div>
        </div>
      </section>

      {/* 3. How it works */}
      <section className="veda-section veda-how">
        <h2 className="veda-section-title">{t("howTitle")}</h2>
        <ol className="veda-how-grid">
          {[
            ["how1Title", "how1Body"],
            ["how2Title", "how2Body"],
            ["how3Title", "how3Body"],
            ["how4Title", "how4Body"],
          ].map(([titleKey, bodyKey], i) => (
            <li key={titleKey} className="veda-how-card">
              <span className="veda-how-num">{i + 1}</span>
              <h3>{t(titleKey)}</h3>
              <p>{t(bodyKey)}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* 4. Try teaching cases */}
      <section className="veda-section" id="try-cases">
        <h2 className="veda-section-title">{t("demoVignettes")}</h2>
        <p className="veda-section-sub">{t("orPreset")}</p>

        {sortedPresets.length === 0 ? (
          <div className="veda-preset-grid">
            {[1, 2, 3].map((i) => (
              <div key={i} className="veda-skeleton" />
            ))}
          </div>
        ) : (
          <div className="veda-preset-grid">
            {sortedPresets.map((p) => (
              <PresetCard
                key={p.id}
                preset={p}
                onRun={() => runPreset(p.id)}
                loading={loadingPreset === p.id}
                openLabel={t("openPreset")}
                runningLabel={t("running")}
                badge={
                  PRESET_META[p.id] ? t(PRESET_META[p.id].badgeKey) : undefined
                }
              />
            ))}
          </div>
        )}
      </section>

      {/* 5. Trust + return */}
      <section className="veda-section veda-trust">
        <h2 className="veda-section-title">{t("trustTitle")}</h2>
        <ul className="veda-trust-list">
          <li>{t("trust1")}</li>
          <li>{t("trust2")}</li>
          <li>{t("trust3")}</li>
        </ul>
        <div className="veda-trust-actions">
          <Link href="/learn?concept=Jvara" className="veda-link-btn veda-link-btn-ghost">
            {t("navLearn")} — Jvara
          </Link>
          {user ? (
            <Link href="/history" className="veda-link-btn veda-link-btn-primary">
              {t("history")}
            </Link>
          ) : (
            <Link href="/signup" className="veda-link-btn veda-link-btn-primary">
              {t("signup")}
            </Link>
          )}
        </div>
      </section>
    </div>
  );
}
