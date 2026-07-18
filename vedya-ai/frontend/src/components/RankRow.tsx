"use client";
import { RecommendedFormulation } from "@/lib/api";
import SafetyDot from "./SafetyDot";
import { useApp } from "@/lib/app-context";

interface Props {
  formulation: RecommendedFormulation;
  onSelect?: () => void;
  selected?: boolean;
  compareSelected?: boolean;
  onCompareToggle?: () => void;
  index: number;
}

export default function RankRow({
  formulation,
  onSelect,
  selected,
  compareSelected,
  onCompareToggle,
  index,
}: Props) {
  const { t } = useApp();
  const { yoga_name, kalpana, score, safety_violations, rank_features, hard_excluded } = formulation;

  const maxScore = 10;
  const barWidth = Math.min((score / maxScore) * 100, 100);

  return (
    <div
      className="flex items-start gap-4 p-4 rounded-xl cursor-pointer transition-all duration-150"
      style={{
        background: selected ? "var(--veda-harita-soft)" : "var(--veda-surface)",
        border: selected
          ? "1px solid var(--veda-harita)"
          : hard_excluded
          ? "1px solid var(--veda-agni)"
          : "1px solid transparent",
        opacity: hard_excluded ? 0.55 : 1,
        fontFamily: "var(--font-ui)",
      }}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      aria-label={`Select ${yoga_name}`}
      onKeyDown={(e) => e.key === "Enter" && onSelect?.()}
    >
      {/* Rank number */}
      <div
        className="flex-none w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
        style={{
          background: hard_excluded ? "var(--veda-agni-soft)" : "var(--veda-shila-deep)",
          color: hard_excluded ? "var(--veda-agni)" : "var(--veda-ink-soft)",
        }}
      >
        {hard_excluded ? "—" : formulation.rank}
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className="font-semibold text-base truncate"
            style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}
          >
            {yoga_name}
          </span>
          {kalpana && (
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ background: "var(--veda-shila-deep)", color: "var(--veda-ink-soft)" }}
            >
              {kalpana}
            </span>
          )}
          <SafetyDot violations={safety_violations} hardExcluded={hard_excluded} />
        </div>

        {/* Score bar */}
        {!hard_excluded && (
          <div className="mt-2 flex items-center gap-2">
            <div
              className="flex-1 h-1.5 rounded-full overflow-hidden"
              style={{ background: "var(--veda-shila-deep)" }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${barWidth}%`,
                  background: "var(--veda-harita)",
                }}
              />
            </div>
            <span className="text-xs font-medium tabular-nums" style={{ color: "var(--veda-harita)" }}>
              {score.toFixed(1)}
            </span>
          </div>
        )}

        {/* Primary indications */}
        {formulation.primary_indications.length > 0 && (
          <div className="mt-1 text-xs" style={{ color: "var(--veda-ink-soft)" }}>
            {formulation.primary_indications.slice(0, 4).join(" · ")}
          </div>
        )}

        {hard_excluded && (
          <div className="text-xs mt-1 font-medium" style={{ color: "var(--veda-agni)" }}>
            {t("excludedNote")}
          </div>
        )}
      </div>

      {/* Compare toggle */}
      {!hard_excluded && onCompareToggle && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onCompareToggle();
          }}
          className="flex-none text-xs px-3 py-1.5 rounded-lg border transition-all"
          style={{
            background: compareSelected ? "var(--veda-harita)" : "transparent",
            borderColor: compareSelected ? "var(--veda-harita)" : "var(--veda-fog)",
            color: compareSelected ? "white" : "var(--veda-ink-soft)",
            fontFamily: "var(--font-ui)",
          }}
          aria-label={compareSelected ? t("compareSelected") : t("compare")}
        >
          {compareSelected ? `✓ ${t("compare")}` : t("compare")}
        </button>
      )}
    </div>
  );
}
