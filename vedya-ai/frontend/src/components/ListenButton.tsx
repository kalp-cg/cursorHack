"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useApp } from "@/lib/app-context";

type Props = {
  yogaName: string;
  summary?: string;
  kalpana?: string;
  winnerReason?: string;
  /** Speak raw text via /voice/tts instead of listen-recommendation script */
  rawText?: string;
  size?: "sm" | "md";
  className?: string;
};

export default function ListenButton({
  yogaName,
  summary = "",
  kalpana = "",
  winnerReason,
  rawText,
  size = "sm",
  className = "",
}: Props) {
  const { t, locale } = useApp();
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);

  useEffect(() => {
    api
      .voiceStatus()
      .then((s) => setConfigured(s.configured))
      .catch(() => setConfigured(false));
    return () => {
      stopAudio();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function stopAudio() {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    setPlaying(false);
  }

  async function handleClick() {
    if (playing) {
      stopAudio();
      return;
    }
    if (!configured) return;
    setLoading(true);
    setError("");
    try {
      const blob = rawText
        ? await api.voiceTts(rawText, locale)
        : await api.voiceListenRecommendation({
            yogaName,
            summary,
            kalpana,
            winnerReason,
            locale,
          });
      stopAudio();
      const url = URL.createObjectURL(blob);
      urlRef.current = url;
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        setPlaying(false);
        if (urlRef.current) {
          URL.revokeObjectURL(urlRef.current);
          urlRef.current = null;
        }
      };
      await audio.play();
      setPlaying(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("voiceError"));
    } finally {
      setLoading(false);
    }
  }

  if (configured === false) {
    return (
      <span className={`veda-voice-hint ${className}`} title={t("voiceUnavailable")}>
        {t("voiceOff")}
      </span>
    );
  }

  const pad = size === "sm" ? "0.4rem 0.85rem" : "0.55rem 1.1rem";
  const fontSize = size === "sm" ? "0.8rem" : "0.9rem";

  return (
    <div className={className} style={{ display: "inline-flex", flexDirection: "column", gap: "0.25rem" }}>
      <button
        type="button"
        className="veda-listen-btn"
        onClick={handleClick}
        disabled={loading || configured === null}
        aria-pressed={playing}
        style={{ padding: pad, fontSize }}
      >
        {loading ? t("voiceLoading") : playing ? t("voiceStop") : t("listen")}
      </button>
      {error && (
        <span style={{ fontSize: "0.7rem", color: "var(--veda-agni)" }}>{t("voiceError")}</span>
      )}
    </div>
  );
}
