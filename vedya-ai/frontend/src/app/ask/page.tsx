"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useApp } from "@/lib/app-context";
import { api, AskResponse } from "@/lib/api";

interface ChatTurn {
  question: string;
  response?: AskResponse;
  error?: string;
}

const SUGGESTIONS = [
  "What is the treatment for fever with cough?",
  "Which formulations help in common cold (Pinasa)?",
  "mane tav ane khansi chhe",
  "તાવ અને ઉધરસ માટે કયો યોગ યોગ્ય છે?",
];

function citation(p: AskResponse["passages"][number]): string {
  const bits = [p.work];
  if (p.sthana) bits.push(p.sthana);
  if (p.chapter) bits.push(`Ch. ${String(p.chapter).replace(/^chapter\s*/i, "")}`);
  if (p.verse_id) bits.push(`v. ${p.verse_id}`);
  return bits.join(", ");
}

export default function AskPage() {
  const { t, locale } = useApp();
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [voiceReady, setVoiceReady] = useState(false);
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    api.voiceStatus().then((s) => setVoiceReady(s.configured)).catch(() => setVoiceReady(false));
  }, []);

  const speak = async (idx: number, text: string) => {
    if (speakingIdx !== null) {
      audioRef.current?.pause();
      setSpeakingIdx(null);
      return;
    }
    try {
      setSpeakingIdx(idx);
      const blob = await api.voiceTts(text, locale);
      const audio = new Audio(URL.createObjectURL(blob));
      audioRef.current = audio;
      audio.onended = () => setSpeakingIdx(null);
      await audio.play();
    } catch {
      setSpeakingIdx(null);
    }
  };

  const submit = async (question: string) => {
    const q = question.trim();
    if (!q || loading) return;
    setInput("");
    setLoading(true);
    setTurns((prev) => [...prev, { question: q }]);
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    try {
      const res = await api.ask(q, locale);
      setTurns((prev) =>
        prev.map((turn, i) => (i === prev.length - 1 ? { ...turn, response: res } : turn))
      );
    } catch (err) {
      setTurns((prev) =>
        prev.map((turn, i) =>
          i === prev.length - 1
            ? { ...turn, error: err instanceof Error ? err.message : "Request failed" }
            : turn
        )
      );
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  return (
    <div className="veda-page">
      <main className="veda-ask">
        <header className="veda-ask-head">
          <h1>{t("askTitle")}</h1>
          <p>{t("askSub")}</p>
        </header>

        {turns.length === 0 && (
          <section className="veda-ask-empty">
            <p className="veda-ask-hint">{t("askEmptyHint")}</p>
            <div className="veda-ask-suggestions">
              <span className="veda-ask-try">{t("askTryOne")}:</span>
              {SUGGESTIONS.map((s) => (
                <button key={s} type="button" className="veda-ask-chip" onClick={() => submit(s)}>
                  {s}
                </button>
              ))}
            </div>
          </section>
        )}

        <section className="veda-ask-thread" aria-live="polite">
          {turns.map((turn, idx) => (
            <article key={idx} className="veda-ask-turn">
              <div className="veda-ask-q">{turn.question}</div>

              {!turn.response && !turn.error && (
                <div className="veda-ask-a veda-ask-loading">{t("askThinking")}</div>
              )}

              {turn.error && <div className="veda-ask-a veda-ask-error">{turn.error}</div>}

              {turn.response && (
                <div className="veda-ask-a">
                  {turn.response.transliterations && turn.response.transliterations.length > 0 && (
                    <div className="veda-ask-translit">
                      {turn.response.transliterations.map((tr) => (
                        <span key={tr.from} className="veda-ask-translit-chip">
                          {tr.from} → {tr.to}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="veda-ask-answer">
                    {(turn.response.answer_lines ?? turn.response.answer.split("\n")).map(
                      (line, i) => (
                        <p key={i}>{line}</p>
                      )
                    )}
                  </div>

                  {turn.response.concepts.length > 0 && (
                    <div className="veda-ask-block">
                      <h3>{t("askConcepts")}</h3>
                      <div className="veda-ask-concepts">
                        {turn.response.concepts.map((c) => (
                          <span key={c.canonical_name} className="veda-ask-concept">
                            <strong>{c.canonical_name}</strong>
                            {c.surface_form.toLowerCase() !== c.canonical_name.toLowerCase() && (
                              <em>
                                {" "}
                                ({t("askAskedAs")} “{c.surface_form}”)
                              </em>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {turn.response.formulations.length > 0 && (
                    <div className="veda-ask-block">
                      <h3>{t("askFormulations")}</h3>
                      <ul className="veda-ask-formulations">
                        {turn.response.formulations.map((f) => (
                          <li key={f.yoga_id}>
                            <div>
                              <strong>{f.name}</strong>
                              {f.kalpana && <span className="veda-ask-kalpana"> · {f.kalpana}</span>}
                              <div className="veda-ask-indicated">
                                {t("askIndicatedFor")}: {f.matched_conditions.join(", ")}
                              </div>
                            </div>
                            <Link href={`/detail/${f.yoga_id}`} className="veda-link-btn">
                              {t("askViewDetail")}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {turn.response.passages.length > 0 && (
                    <div className="veda-ask-block">
                      <h3>{t("askSources")}</h3>
                      <ol className="veda-ask-passages">
                        {turn.response.passages.slice(0, 6).map((p) => (
                          <li key={p.ref_id}>
                            <blockquote>{p.excerpt}</blockquote>
                            <cite>{citation(p)}</cite>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}

                  <footer className="veda-ask-foot">
                    {voiceReady && (
                      <button
                        type="button"
                        className="veda-ask-listen"
                        onClick={() =>
                          speak(
                            idx,
                            (turn.response!.answer_lines ?? [turn.response!.answer]).join(" ")
                          )
                        }
                      >
                        {speakingIdx === idx ? t("askStopListen") : t("askListen")}
                      </button>
                    )}
                    <span className="veda-ask-grounded">{t("askGrounded")}</span>
                    <span className="veda-ask-disclaimer">{turn.response.disclaimer}</span>
                  </footer>
                </div>
              )}
            </article>
          ))}
          <div ref={bottomRef} />
        </section>

        <form
          className="veda-ask-inputrow"
          onSubmit={(e) => {
            e.preventDefault();
            submit(input);
          }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t("askPlaceholder")}
            maxLength={500}
            aria-label={t("askTitle")}
          />
          <button type="submit" className="veda-btn veda-btn-primary" disabled={loading || !input.trim()}>
            {loading ? t("askThinking") : t("askSend")}
          </button>
        </form>
      </main>
    </div>
  );
}
