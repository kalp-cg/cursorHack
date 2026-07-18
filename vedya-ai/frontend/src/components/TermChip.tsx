"use client";

interface Props {
  term: string;
  canonical?: string;
  onRemove?: () => void;
  variant?: "resolved" | "unresolved";
}

export default function TermChip({ term, canonical, onRemove, variant = "resolved" }: Props) {
  const isUnresolved = variant === "unresolved";
  return (
    <span
      className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium"
      style={{
        background: isUnresolved ? "var(--veda-kesar-soft)" : "var(--veda-harita-soft)",
        color: isUnresolved ? "var(--veda-kesar)" : "var(--veda-harita)",
        border: `1px solid ${isUnresolved ? "var(--veda-kesar)" : "var(--veda-harita)"}`,
        fontFamily: "var(--font-ui)",
      }}
      title={canonical ? `Resolved to: ${canonical}` : undefined}
    >
      {canonical && canonical !== term ? (
        <>
          <span style={{ opacity: 0.7 }}>{term}</span>
          <span style={{ opacity: 0.5 }}>→</span>
          <span>{canonical}</span>
        </>
      ) : (
        term
      )}
      {onRemove && (
        <button
          onClick={onRemove}
          className="ml-1 hover:opacity-70"
          aria-label={`Remove ${term}`}
          style={{ lineHeight: 1 }}
        >
          ×
        </button>
      )}
    </span>
  );
}
