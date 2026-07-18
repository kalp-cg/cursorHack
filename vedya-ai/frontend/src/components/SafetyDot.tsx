"use client";
import { SafetyViolation } from "@/lib/api";

interface Props {
  violations: SafetyViolation[];
  hardExcluded?: boolean;
}

export default function SafetyDot({ violations, hardExcluded }: Props) {
  if (hardExcluded) {
    return (
      <span
        className="w-2.5 h-2.5 rounded-full inline-block"
        style={{ background: "var(--veda-agni)" }}
        title="Hard excluded — contraindicated"
        aria-label="Contraindicated"
      />
    );
  }
  if (violations.some((v) => v.severity === "WARN")) {
    return (
      <span
        className="w-2.5 h-2.5 rounded-full inline-block"
        style={{ background: "var(--veda-kesar)" }}
        title="Safety warning — use with caution"
        aria-label="Safety warning"
      />
    );
  }
  return (
    <span
      className="w-2.5 h-2.5 rounded-full inline-block"
      style={{ background: "var(--veda-harita)" }}
      title="No safety concerns for current profile"
      aria-label="Safe"
    />
  );
}
