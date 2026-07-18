"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, PresetVignette } from "@/lib/api";
import PrimaryButton from "@/components/PrimaryButton";
import VoiceMic from "@/components/VoiceMic";
import ListenButton from "@/components/ListenButton";
import { useApp } from "@/lib/app-context";

function PresetCard({
  preset,
  onRun,
  loading,
  openLabel,
  runningLabel,
}: {
  preset: PresetVignette;
  onRun: () => void;
  loading: boolean;
  openLabel: string;
  runningLabel: string;
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
  const { t, locale, setConversationId } = useApp();
  const [presets, setPresets] = useState<PresetVignette[]>([]);
  const [loadingPreset, setLoadingPreset] = useState<string | null>(null);
  const [freeText, setFreeText] = useState("");
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.getPresets().then(setPresets).catch(console.error);
  }, []);

  async function runPreset(presetId: string) {
    setLoadingPreset(presetId);
    try {
      const result = await api.runPreset(presetId);
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
      console.error(e);
    } finally {
      setLoadingPreset(null);
    }
  }

  async function runFreeText() {
    if (!freeText.trim()) return;
    setRunning(true);
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
      console.error(e);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="veda-page">
      <section className="veda-hero">
        <div className="veda-hero-texture" aria-hidden />
        <div className="veda-hero-inner">
          <h1 className="veda-brand">{t("brand")}</h1>
          <p className="veda-tagline">{t("tagline")}</p>
          <p className="veda-lede">{t("lede")}</p>

          <div className="veda-search-row">
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

          <div className="veda-hero-voice">
            <VoiceMic onTranscript={(text) => setFreeText((prev) => (prev ? `${prev} ${text}` : text))} />
          </div>

          <p className="veda-hint">{t("orPreset")}</p>
        </div>
      </section>

      <section className="veda-section">
        <h2 className="veda-section-title">{t("demoVignettes")}</h2>

        {presets.length === 0 ? (
          <div className="veda-preset-grid">
            {[1, 2, 3].map((i) => (
              <div key={i} className="veda-skeleton" />
            ))}
          </div>
        ) : (
          <div className="veda-preset-grid">
            {presets.map((p) => (
              <PresetCard
                key={p.id}
                preset={p}
                onRun={() => runPreset(p.id)}
                loading={loadingPreset === p.id}
                openLabel={t("openPreset")}
                runningLabel={t("running")}
              />
            ))}
          </div>
        )}

        <div className="veda-center">
          <PrimaryButton
            variant="outline"
            size="lg"
            onClick={() => router.push("/results?intake=true")}
          >
            {t("newCase")}
          </PrimaryButton>
        </div>
      </section>
    </div>
  );
}
