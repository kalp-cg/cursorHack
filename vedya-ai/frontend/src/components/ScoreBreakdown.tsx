"use client";

import type { RankFeatures } from "@/lib/api";
import { useApp } from "@/lib/app-context";

interface Props {
  features: RankFeatures;
  compact?: boolean;
}

const BARS: { key: keyof RankFeatures; labelKey: string; kind: "plus" | "minus" }[] = [
  { key: "primary_indication_match", labelKey: "featPrimary", kind: "plus" },
  { key: "secondary_indication_match", labelKey: "featSecondary", kind: "plus" },
  { key: "property_fit", labelKey: "featProperty", kind: "plus" },
  { key: "citation_bonus", labelKey: "featCitation", kind: "plus" },
  { key: "contraindication_penalty", labelKey: "featContra", kind: "minus" },
  { key: "medium_penalty", labelKey: "featMedium", kind: "minus" },
];

export default function ScoreBreakdown({ features, compact }: Props) {
  const { t } = useApp();
  const maxAbs = Math.max(
    1,
    ...BARS.map((b) => Math.abs(Number(features[b.key]) || 0))
  );

  return (
    <div className={`veda-score${compact ? " is-compact" : ""}`}>
      <div className="veda-score-head">
        <span>{t("scoreBreakdown")}</span>
        <strong className="tabular-nums">{features.total_score.toFixed(1)}</strong>
      </div>
      <ul className="veda-score-list">
        {BARS.map((b) => {
          const raw = Number(features[b.key]) || 0;
          const width = Math.min(100, (Math.abs(raw) / maxAbs) * 100);
          if (compact && Math.abs(raw) < 0.01) return null;
          return (
            <li key={b.key}>
              <span className="veda-score-label">{t(b.labelKey)}</span>
              <div className="veda-score-track" aria-hidden>
                <div
                  className={`veda-score-fill ${b.kind === "minus" ? "is-minus" : "is-plus"}`}
                  style={{ width: `${width}%` }}
                />
              </div>
              <span
                className={`veda-score-val tabular-nums ${b.kind === "minus" ? "is-minus" : ""}`}
              >
                {b.kind === "minus" && raw > 0 ? "−" : ""}
                {Math.abs(raw).toFixed(1)}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="veda-score-note">{t("scoreNote")}</p>
    </div>
  );
}
