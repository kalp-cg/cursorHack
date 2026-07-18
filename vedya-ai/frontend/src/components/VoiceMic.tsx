"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useApp } from "@/lib/app-context";

type Props = {
  onTranscript: (text: string) => void;
  className?: string;
};

export default function VoiceMic({ onTranscript, className = "" }: Props) {
  const { t, locale } = useApp();
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState("");
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    api
      .voiceStatus()
      .then((s) => setConfigured(s.configured))
      .catch(() => setConfigured(false));
  }, []);

  async function startRecording() {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType: mime });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((tr) => tr.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setTranscribing(true);
        try {
          const result = await api.voiceStt(blob, locale);
          if (result.text) onTranscript(result.text);
          else setError(t("voiceEmpty"));
        } catch {
          setError(t("voiceError"));
        } finally {
          setTranscribing(false);
        }
      };
      mediaRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      setError(t("micDenied"));
    }
  }

  function stopRecording() {
    const rec = mediaRef.current;
    if (rec && rec.state !== "inactive") {
      rec.stop();
    }
    setRecording(false);
  }

  function handleClick() {
    if (recording) stopRecording();
    else void startRecording();
  }

  if (configured === false) {
    return (
      <div className={`veda-mic-wrap ${className}`}>
        <button
          type="button"
          className="veda-mic-btn is-disabled"
          disabled
          title={t("voiceNeedsKey")}
        >
          <span className="veda-mic-dot" aria-hidden />
          <span>{t("voiceOff")}</span>
        </button>
        <span className="veda-mic-hint">{t("voiceNeedsKey")}</span>
      </div>
    );
  }

  return (
    <div className={`veda-mic-wrap ${className}`}>
      <button
        type="button"
        className={`veda-mic-btn ${recording ? "is-recording" : ""}`}
        onClick={handleClick}
        disabled={transcribing || configured === null}
        aria-pressed={recording}
        title={recording ? t("stopRecording") : t("speakVignette")}
      >
        <span className="veda-mic-dot" aria-hidden />
        <span>
          {transcribing
            ? t("transcribing")
            : recording
              ? t("stopRecording")
              : t("speakVignette")}
        </span>
      </button>
      {error && <span className="veda-mic-error">{error}</span>}
    </div>
  );
}
