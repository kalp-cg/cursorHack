"use client";
import { SafetyViolation } from "@/lib/api";
import { useApp } from "@/lib/app-context";

interface Props {
  violations: SafetyViolation[];
}

export default function SafetyPanel({ violations }: Props) {
  const { t } = useApp();
  if (!violations.length) return null;

  const hardViolations = violations.filter((v) => v.severity === "HARD_EXCLUDE");
  const warnViolations = violations.filter((v) => v.severity === "WARN");

  return (
    <div
      className="rounded-2xl p-4 mb-4"
      style={{ background: "var(--veda-agni-soft)", border: "1px solid var(--veda-agni)" }}
      role="alert"
      aria-live="polite"
    >
      {hardViolations.length > 0 && (
        <div className="mb-3">
          <div
            className="flex items-center gap-2 font-semibold text-sm mb-2"
            style={{ color: "var(--veda-agni)" }}
          >
            <span aria-hidden>⊗</span>
            <span>{t("safetyExcluded")}</span>
          </div>
          {hardViolations.map((v) => (
            <div key={v.rule_id} className="text-sm pl-5 mb-1" style={{ color: "var(--veda-ink)" }}>
              {v.message}
              {v.classical_basis && (
                <span className="block text-xs mt-0.5" style={{ color: "var(--veda-ink-soft)" }}>
                  {v.classical_basis}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {warnViolations.length > 0 && (
        <div>
          <div
            className="flex items-center gap-2 font-semibold text-sm mb-2"
            style={{ color: "var(--veda-kesar)" }}
          >
            <span aria-hidden>⚠</span>
            <span>{t("safetyWarned")}</span>
          </div>
          {warnViolations.map((v) => (
            <div key={v.rule_id} className="text-sm pl-5 mb-1" style={{ color: "var(--veda-ink)" }}>
              {v.message}
              {v.classical_basis && (
                <span className="block text-xs mt-0.5" style={{ color: "var(--veda-ink-soft)" }}>
                  {v.classical_basis}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
