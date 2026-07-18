"use client";
import { ReferenceCard } from "@/lib/api";

interface Props {
  reference: ReferenceCard;
}

export default function CitationCard({ reference }: Props) {
  const locus = [reference.sthana, reference.chapter, reference.verse_id]
    .filter(Boolean)
    .join(" › ");

  return (
    <div
      className="rounded-xl p-3 text-sm"
      style={{
        background: "var(--veda-tamra-soft)",
        borderLeft: "3px solid var(--veda-tamra)",
        fontFamily: "var(--font-ui)",
      }}
    >
      <div className="font-semibold" style={{ color: "var(--veda-tamra)" }}>
        {reference.work}
      </div>
      {locus && (
        <div className="text-xs mt-0.5" style={{ color: "var(--veda-ink-soft)" }}>
          {locus}
        </div>
      )}
      {reference.excerpt_text && (
        <div
          className="mt-2 text-xs italic leading-relaxed"
          style={{ color: "var(--veda-ink-soft)" }}
        >
          &ldquo;{reference.excerpt_text.slice(0, 200)}
          {reference.excerpt_text.length > 200 ? "…" : ""}&rdquo;
        </div>
      )}
    </div>
  );
}
