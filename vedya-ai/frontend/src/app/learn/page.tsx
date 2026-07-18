"use client";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import PrimaryButton from "@/components/PrimaryButton";
import TermChip from "@/components/TermChip";

function LearnContent() {
  const router = useRouter();
  const params = useSearchParams();
  const conceptParam = params.get("concept") || "Jvara";

  const [concept, setConcept] = useState(conceptParam);
  const [input, setInput] = useState(conceptParam);
  const [data, setData] = useState<{ canonical_name: string; type: string; synonyms: string[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchConcept(conceptParam);
  }, [conceptParam]);

  async function fetchConcept(name: string) {
    setLoading(true);
    setError("");
    try {
      const result = await api.synonymMap(name);
      setData(result);
      setConcept(result.canonical_name);
    } catch {
      setError(`'${name}' not found in corpus.`);
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ background: "var(--veda-shila)", minHeight: "100vh", fontFamily: "var(--font-ui)" }}>
      {/* Header */}
      <div className="sticky top-0 z-10 px-6 py-3 flex items-center gap-4" style={{ background: "var(--veda-ink)" }}>
        <button onClick={() => router.back()} className="text-sm" style={{ color: "rgba(247,249,248,0.6)" }}>← Back</button>
        <span className="text-base font-semibold" style={{ fontFamily: "var(--font-display)", color: "#F7F9F8" }}>Learn</span>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-medium mb-2" style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}>
          Synonym & Terminology Map
        </h1>
        <p className="text-sm mb-8" style={{ color: "var(--veda-ink-soft)" }}>
          Explore the multiple names of a disease or symptom across classical Ayurvedic texts and modern equivalents.
        </p>

        {/* Search */}
        <div className="flex gap-2 mb-8">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchConcept(input)}
            placeholder="e.g. Jvara, Fever, Pinasa…"
            className="flex-1 rounded-xl px-4 py-3 text-sm outline-none"
            style={{
              background: "var(--veda-shila-deep)",
              border: "1px solid var(--veda-fog)",
              color: "var(--veda-ink)",
            }}
          />
          <PrimaryButton onClick={() => fetchConcept(input)} disabled={loading}>
            {loading ? "…" : "Look up"}
          </PrimaryButton>
        </div>

        {error && (
          <div className="text-sm p-4 rounded-xl mb-4" style={{ background: "var(--veda-agni-soft)", color: "var(--veda-agni)" }}>
            {error}
          </div>
        )}

        {data && (
          <div className="rounded-2xl p-6" style={{ background: "var(--veda-surface)", border: "1px solid var(--veda-shila-deep)" }}>
            <div className="flex items-center gap-2 mb-4">
              <div className="text-2xl font-medium" style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}>
                {data.canonical_name}
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: "var(--veda-shila-deep)", color: "var(--veda-fog)" }}>
                {data.type}
              </span>
            </div>

            <div className="mb-4">
              <div className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "var(--veda-fog)" }}>
                All synonyms in corpus
              </div>
              <div className="flex flex-wrap gap-2">
                {data.synonyms.filter((s) => s.toLowerCase() !== data.canonical_name.toLowerCase()).slice(0, 30).map((s) => (
                  <button
                    key={s}
                    onClick={() => { setInput(s); fetchConcept(s); }}
                    className="transition-all hover:scale-105"
                  >
                    <TermChip term={s} />
                  </button>
                ))}
              </div>
            </div>

            {/* Teaching point */}
            <div
              className="mt-4 p-4 rounded-xl text-sm"
              style={{ background: "var(--veda-tamra-soft)", borderLeft: "3px solid var(--veda-tamra)" }}
            >
              <div className="font-semibold mb-1" style={{ color: "var(--veda-tamra)" }}>Teaching Point</div>
              <p style={{ color: "var(--veda-ink)" }}>
                <strong>{data.canonical_name}</strong> is the canonical Ayurvedic concept.
                Its {data.synonyms.length - 1} recorded synonyms span Sanskrit ({data.synonyms.filter(s => /[A-Z]/.test(s[0])).slice(0, 3).join(", ")}),
                transliterated forms, and English clinical equivalents.
                Knowing all synonyms enables accurate literature search and formulation retrieval across texts.
              </p>
            </div>
          </div>
        )}

        {/* Quick links */}
        <div className="mt-8">
          <div className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: "var(--veda-fog)" }}>
            Explore key concepts
          </div>
          <div className="flex flex-wrap gap-2">
            {["Jvara", "Kasa", "Pinasa", "Shotha", "Prameha", "Shwasa", "Vrana", "Pandu"].map((c) => (
              <button
                key={c}
                onClick={() => { setInput(c); fetchConcept(c); }}
                className="text-sm px-3 py-1.5 rounded-lg transition-all hover:opacity-80"
                style={{ background: "var(--veda-harita-soft)", color: "var(--veda-harita)", fontFamily: "var(--font-ui)" }}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LearnPage() {
  return (
    <Suspense>
      <LearnContent />
    </Suspense>
  );
}
